import requests
import bs4
import codecs

from ual_functions import *
from ual_params import *

class ual_session(requests.Session):
	"""Class to hold a session with united.com.

	Methods:
		__init__: loads the website and logs in the user
		login_old, login_new: log in to old and new versions of the site
		search, search_old, search_new: conduct a flight search
		alert_search: search and extract data for a given alert query, return results matching the specified buckets
		basic_search: search and extract data for a given query, return all results
		long_search: perform alert search over a range of dates
		extract_data, extract_data_old, extract_data_new: parse the response returned by a search into segments and trips
	"""

	def __init__(self,user=None,pwd=None,logging=False,useragent=None):
		""" Initialize session and attempt to log in user."""
		requests.Session.__init__(self)
		if useragent:
			self.headers.update({'User-Agent':useragent})

		# load the united.com home page and figure out whether it's the new site or the old site
		if logging:
			print("Loading united.com home page")
		self.home = self.get('https://www.united.com',allow_redirects=True,headers=self.headers)
		if "Find a Reservation by Confirmation Number" in self.home.text:
			self.site_version = "Old"
		elif "Welcome to the new united.com" in self.home.text:
			self.site_version = "New"
		else:
			raise Exception("Unrecognized version of united.com")
		if logging:
			print(self.site_version + " united.com detected.")

		if user:
			# attempt to log in the user
			if logging:
				print("Logging in to united.com")
			if self.site_version == "Old":
				self.login_old(user, pwd, logging)
			elif self.site_version == "New":
				self.login_new(user, pwd, logging)

			# look for login errors
			# the following could be put in a loop for retries, not necessary at the moment.
			failed = False
			if 'does not match our records' in self.signin.text:
				failed = True
				self.login_error = "Username or password mismatch."
			elif user not in self.signin.text:
				failed = True
				self.login_error = "Username not on landing page."
			if logging or failed:
				F = codecs.open('signin.html','w','utf-8')
				F.write(self.signin.text)
				F.close()
			if failed:
				raise Exception(self.login_error)
			else:
				self.user = user
				self.last_login_time = datetime.now()


	def login_old(self,user,pwd,logging=False):
		""" User login on old united.com."""
		login_params = set_login_params(self.cookies['SID'])
		login_params['ctl00$ContentInfo$accountsummary$OpNum1$txtOPNum'] = user
		login_params['ctl00$ContentInfo$accountsummary$OpPin1$txtOPPin'] = pwd
		self.signin = self.post('https://www.united.com/web/en-US/default.aspx',data=login_params,allow_redirects=True)


	def login_new(self,user,pwd,logging=False):
		""" User login on new united.com."""
		failed = False
		login_params = {'IsHomePageTile':'True',
						'RememberMe':'true',
						'MpNumber':user,
						'Password':pwd}
		self.signin = self.post('https://www.united.com/ual/en/us/account/account/login',
			data=login_params,allow_redirects=True)


	def search(self,params,logging=False):
		if self.site_version == "Old":
			return self.search_old(params,logging)
		elif self.site_version == "New":
			return self.search_new(params,logging)
		if logging:
			print("Received " + str(len(self.search_results.text)) + " characters")
			F = codecs.open('search.html','w','utf-8')
			F.write(self.search_results.text)
			F.close()


	def search_old(self,params,logging=False):
		"""Perform flight search on old united.com.  Response is stored in self.search_results."""
		search_params = set_search_params(self.cookies['SID'])
		search_params['ctl00$ContentInfo$Booking1$Origin$txtOrigin']=params.depart_airport
		search_params['ctl00$ContentInfo$Booking1$Destination$txtDestination']=params.arrive_airport
		search_params['ctl00$ContentInfo$Booking1$DepDateTime$Depdate$txtDptDate']=params.depart_date
		if params.nonstop:
			search_params['ctl00$ContentInfo$Booking1$Direct$chkFltOpt']='on'
		self.search_results = self.post('https://www.united.com/web/en-US/default.aspx',data=search_params,allow_redirects=True,headers=self.headers)


	def search_new(self,params,logging=False):
		"""Perform flight search on new united.com.  Response is stored in self.search_results."""

		search_params = new_search_params(params.depart_airport, params.arrive_airport, params.depart_date)
		if params.nonstop:
			search_params['NonStopOnly']='true'

		# load search page to get a cart ID
		if logging:
			print("Loading search page")
		self.search_page = self.post('https://www.united.com/ual/en/us/flight-search/book-a-flight',
			data=search_params,allow_redirects=True,headers=self.headers)
		if logging:
			print("Received " + str(len(self.search_page.text)) + " characters")
			F = codecs.open('search_page.html','w','utf-8')
			F.write(self.search_page.text)
			F.close()

		# extract cart ID from search page
		soup = bs4.BeautifulSoup(self.search_page.text,'lxml')
		cart_id_input = soup.findAll(attrs={"name":"CartId"})
		cart_id = cart_id_input[0]['value']
		print(cart_id)

		# get search results
		# this post is to a json endpoint, the params are returned json-encoded
		search_params_full = new_search_params_full(params.depart_airport, params.arrive_airport, 
													params.depart_datetime, cart_id, nonstop=params.nonstop)	
		if logging:
			print("Loading search results")
		self.headers.update({'Content-Type':'application/json'})
		self.search_results = self.post('https://www.united.com/ual/en/us/flight-search/book-a-flight/flightshopping/getflightresults/rev',
			data=search_params_full,
			allow_redirects=True,headers=self.headers)
		# all of the data is in search_results in nice json form!


	def extract_data(self):
		if self.site_version == "Old":
			return self.extract_data_old()
		elif self.site_version == "New":
			return self.extract_data_new()


	def extract_data_old(self):
		soup = bs4.BeautifulSoup(self.search_results.text,'lxml')
		trips = soup.findAll(attrs={"class": "tdSegmentBlock"})

		alltrips = []
		for t in trips:
			depart = t.findAll(attrs={"class": "tdDepart"})
			arrive = t.findAll(attrs={"class": "tdArrive"})
			segmentdtl = t.findAll(attrs={"class": "tdSegmentDtl"})
			segs = zip(depart,arrive,segmentdtl)
			tripdata = []
			for s in segs:
				newseg = Segment()
				buckets = s[2].find(text=bucket_regex)
				if buckets:
					newseg.availability = buckets
				deptime = s[0].find(attrs={"class": "timeDepart"})
				newseg.depart_time = deptime.text
				newseg.depart_date,newseg.depart_airport = get_airport(deptime)
				arrtime = s[1].find(attrs={"class": "timeArrive"})
				newseg.arrive_time = arrtime.text
				newseg.arrive_date,newseg.arrive_airport = get_airport(arrtime)
				newseg.flightno = s[2].find(text=re.compile('('+'|'.join(airline_codes)+')[0-9]+'))
				newseg.aircraft = s[2].find(text=re.compile('('+'|'.join(aircraft_types)+')'))
				tripdata.append(newseg)
			alltrips.append(tripdata)
		return alltrips


	def extract_data_new(self):
		return None


	def alert_search(self,params):
		"""Perform the search specified by params and return results matching the specified fare buckets."""
		self.search(params)
		trips = self.extract_data()
		found_segs = []
		for t in trips:
			if params.nonstop and len(t) > 1:
				continue
			for seg in t:
				seg.search_buckets(params.buckets)
				if not params.flightno or seg.flightno in params.flightno:
					found_segs.append(seg)
		if len(found_segs)==0:
			failed = self.search(params,logging=True)
			raise Exception('No results found for '+str(params))
		return found_segs


	def basic_search(self,params):
		"""Perform the search specified by params and return all results."""
		self.search(params)
		data = self.extract_data()
		# the following is for logging only
		for trip in data:
			for seg in trip:
				if params.buckets:
					seg.search_buckets(params.buckets)
				try:
					print(seg.condensed_repr())
				except:
					print(seg)
			print('---')
		return data


	def long_search(self,start_date,end_date,depart_airport,arrive_airport,buckets=None,flightno=None):
		found_segs = []
		cur_datetime = parser.parse(start_date)
		while cur_datetime <= parser.parse(end_date):
			depart_date = cur_datetime.strftime('%m/%d/%y')
			params = alert_params(depart_date,depart_airport,arrive_airport,buckets=buckets,flightno=None,nonstop=True)
			try:
				search_results = self.alert_search(params)
			except Exception as e:
				print e
				continue
			for seg in search_results:
				if sum(seg.search_results.values()) > 0:
					print(seg.condensed_repr())
					found_segs.append(seg)
			cur_datetime += timedelta(1)
		return found_segs
