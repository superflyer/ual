import requests
import bs4
import codecs
import uuid

from ual_functions import *
from ual_params import *

class ual_session(requests.Session):
	"""Class to hold a session with united.com.

	Methods:
		__init__: loads the website and logs in the user
		login: log in to the site
		search: conduct a flight search
		alert_search: search and extract data for a given alert query, return results matching the specified buckets
		basic_search: search and extract data for a given query, return all results
		long_search: perform alert search over a range of dates -- DEPRECATED
		extract_data, extract_data_old, extract_data_new: parse the response returned by a search into segments and trips
	"""

	def __init__(self, user=None, pwd=None, ua_only=False, logging=False, useragent=None,
					user_cookie=None, session_cookie=None, search_type=None):
		""" Initialize session and attempt to log in user.
		user: united.com Username
		pwd: united.com password
		ua_only: search for united flights only
		logging: log query results in external files
		useragent: useragent to spoof for queries
		search_type: None, Upgrade, or Award (developed for when Expert Mode is broken)

		"""
		requests.Session.__init__(self)
		self.logging = logging
		self.search_type = search_type
		self.ua_only = ua_only
		if useragent:
			self.headers.update({'User-Agent':useragent})
		if user_cookie and session_cookie:
			self.cookies['User'] = user_cookie
			self.cookies['Session'] = session_cookie
		self.headers.update({
				'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
				'Accept' : 'text/html, */*; q=0.01',
				'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4',
				'Origin' : 'https://www.united.com',
				'UASessionTabId' : str(uuid.uuid4()),
				'X-Requested-With' : 'XMLHttpRequest',
				'Referer' : 'https://www.united.com/ual/en/us/'
			})



		# load the united.com home page
		if logging:
			print("Loading united.com home page")
		self.home = self.get('https://www.united.com/ual/en/us',allow_redirects=True,headers=self.headers)
		if "Welcome to united.com" in self.home.text:
			self.site_version = "New"
		else:
			raise Exception("Unrecognized version of united.com")

		# initialize empty cart_id
		self.cart_id = None

		if user:
			# attempt to log in the user
			if logging:
				print("Logging in to united.com")
			self.login(user, pwd)

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
				F = codecs.open('response_logs/signin.html','w','utf-8')
				F.write(self.signin.text)
				F.close()
			if failed:
				raise Exception(self.login_error)
			else:
				self.user = user
				self.last_login_time = datetime.now()


	def login(self,user,pwd):
		""" User login on new united.com."""
		failed = False
		login_params = {'IsHomePageTile':'True',
						'RememberMe':'true',
						'MpNumber':user,
						'Password':pwd}
		self.signin = self.post('https://www.united.com/ual/en/us/account/account/login',
			data=login_params,allow_redirects=True)


	def search(self, params):
		"""Perform flight search on new united.com.  Response is stored in self.search_results."""

		search_params = new_search_params(params.depart_airport, params.arrive_airport, params.depart_date)
		if params.nonstop:
			search_params['NonStopOnly']='true'

		# load search page to get a cart ID
		if not self.cart_id:
			if self.logging:
				print("Loading search page")
			self.search_page = self.post('https://www.united.com/ual/en/us/flight-search/book-a-flight',
				data=search_params,allow_redirects=True,headers=self.headers)
			if self.logging:
				print("Received " + str(len(self.search_page.text)) + " characters")
				F = codecs.open('response_logs/search_page.html','w','utf-8')
				F.write(self.search_page.text)
				F.close()

			# extract cart ID from search page
			soup = bs4.BeautifulSoup(self.search_page.text,'lxml')
			cart_id_input = soup.findAll(attrs={"name":"CartId"})
			self.cart_id = cart_id_input[0]['value']
			if self.logging:
				print("Cart ID: " + self.cart_id)

		# get search results
		# this post is to a json endpoint, the params are returned json-encoded
		search_params_full = new_search_params_full(params.depart_airport, params.arrive_airport,
									params.depart_datetime, self.cart_id, nonstop=params.nonstop,
									search_type = self.search_type)
		if self.logging:
			print("Loading search results")
		self.headers.update({'Content-Type':'application/json'})
		self.search_results = self.post('https://www.united.com/ual/en/us/flight-search/book-a-flight/flightshopping/getflightresults/rev',
			data=search_params_full,
			allow_redirects=True, headers=self.headers)
		self.search_datetime = params.depart_datetime
		# all of the data is in search_results in nice json form!
		if self.logging:
			print("Received " + str(len(self.search_results.text)) + " characters")
			F = codecs.open('response_logs/search.html','w','utf-8')
			F.write(self.search_results.text)
			F.close()



	def extract_data(self):
		results = json.loads(self.search_results.text)
		trips = results['data']['Trips'][0]['Flights']

		alltrips = []
		for t in trips:
			tripdata = []
			seg = t
			while seg:
				newseg = Segment()
				newseg.depart_airport = seg['Origin']
				newseg.arrive_airport = seg['Destination']
				newseg.aircraft = seg['EquipmentDisclosures']['EquipmentType']
				newseg.flightno = seg['MarketingCarrier']+seg['FlightNumber']
				if seg['BookingClassAvailList']:
					# was: len(tripdata) == 0 or newseg.flightno != tripdata[-1].flightno
					newseg.availability = seg['BookingClassAvailList']
				else:
					# no availability appears for second leg of '1-stop' flights
					#   -- purposely ignoring this edge case for now
					# parse classes from "Products"
					found_classes = []
					for p in seg['Products']:
						if ('SURP' in p['ProductType'] or 'DISP' in p['ProductType']) and \
								p['BookingCode']:
							found_classes.append(p['BookingCode'] + str(1))
						elif p['BookingCode'] and p['BookingCount'] > 0:
							found_classes.append(p['BookingCode'] + str(p['BookingCount']))
					newseg.availability = found_classes
				if seg['OperatingCarrier'] != seg['MarketingCarrier']:
					newseg.flightno += ' (' + seg['OperatingCarrier'] + ')'
				newseg.depart_date, newseg.depart_time = seg['DepartDateTime'].split(' ')
				newseg.arrive_date, newseg.arrive_time = seg['DestinationDateTime'].split(' ')
				newseg.search_datetime = self.search_datetime
				tripdata.append(newseg)
				connections = seg['Connections']
				if connections:
					seg = connections[0]
				else:
					seg = None
			alltrips.append(tripdata)

		self.trips = alltrips
		if self.ua_only:
			self.trips = [t for t in self.trips if
				all([seg.flightno[:2]=='UA' and seg.flightno[-1]!=')' for seg in t])]


	def alert_search(self,params):
		"""Perform the search specified by params and return results matching the specified fare buckets."""
		self.search(params)
		self.extract_data()
		found_segs = []
		for t in self.trips:
			if params.nonstop and len(t) > 1:
				continue
			for seg in t:
				seg.search_buckets(params.buckets)
				if not params.flightno or seg.flightno in params.flightno:
					found_segs.append(seg)
		if len(found_segs)==0:
			failed = self.search(params)
			raise Exception('No results found for '+str(params))
		return found_segs


	def basic_search(self,params):
		"""Perform the search specified by params and return all results."""
		self.search(params)
		self.extract_data()
		# the following is for logging only
		for trip in self.trips:
			for seg in trip:
				if params.buckets:
					seg.search_buckets(params.buckets)
				try:
					print(seg.condensed_repr())
				except:
					print(seg)
			print('---')
		return self.trips


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
				if not buckets or sum(seg.search_results.values()) > 0:
					print(seg.condensed_repr())
					found_segs.append(seg)
			cur_datetime += timedelta(1)
		return found_segs
