import requests
import bs4
import codecs
import uuid
from random import random
from time import sleep

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
		extract_json_data: parse the response returned by a search into segments and trips
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
		# initialize empty cart_id
		self.cart_id = None
		self.tripdata = None

		if useragent:
			self.headers.update({'User-Agent':useragent})
		if user_cookie and session_cookie:
			self.cookies['User'] = user_cookie
			self.cookies['Session'] = session_cookie

		self.headers.update({
				'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
				'Accept' : 'text/html, */*; q=0.01',
				'Accept-Encoding' : 'gzip, deflate, br',
				'Accept-Language' : 'en-US,en;q=0.5',
				'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:57.0) Gecko/20100101 Firefox/57.0',
				'Host' : 'www.united.com',
#				'UASessionTabId' : str(uuid.uuid4()),
				'X-Requested-With' : 'XMLHttpRequest',
				'Referer' : 'https://www.united.com/ual/en/us/',
				'Connection' : 'keep-alive'
			})

		return

		# load the united.com home page
		if logging:
			print("Loading united.com home page")
		self.home = self.get('https://www.united.com/ual/en/us',allow_redirects=True,headers=self.headers)
		if "Welcome to united.com" in self.home.text:
			self.site_version = "New"
		else:
			raise Exception("Unrecognized version of united.com")

		# new endpoint to get cookies
		self.clientdata = self.post('https://www.united.com/ual/en/us/default/home/clientdata', allow_redirects=True,
			headers=self.headers, data={})

		self.post('https://www.united.com/_bm/_data', allow_redirects=True, headers=self.headers,
			data={'sensor_data' : '7a74G7m23Vrp0o5c9849496.78-6,2,-36,-495,Mozilla/9.8 (Macintosh; Intel Mac OS X 74.93; rv:78.9) Gecko/15852250 Firefox/04.2,uaend,4670,77621691,en-US,Gecko,5,0,6,2,400253,6891965,9758,8548,0696,3863,6078,924,7744,,cpen:1,i1:6,dm:3,cwen:5,non:3,opc:7,fc:0,sc:2,wrc:8,isc:96,vib:4,bat:1,x12:4,x25:6,1210,0.103635489701,656164463746.7,loc:-5,0,-89,-316,do_en,dm_en,t_dis-7,4,-23,-626,9,-7,2,1,0687,615,1;4,-2,9,7,011,812,2;2,-6,5,1,752,279,3;5,5,1,9,770,429,5;5,1,9,1,5335,0629,1;9,-7,2,1,847,105,0;6,-9,3,5,6237,1186,8;3,5,5,1,0112,3919,6;5,1,9,1,5405,0799,2;9,1,4,8,4241,3443,2;4,8,3,5,6508,1457,9;3,5,5,1,0308,3105,6;5,1,9,1,5572,0866,2;9,1,4,8,4155,3357,2;4,8,3,5,6608,1557,9;3,5,5,1,0192,3999,5;5,-6,0,6,3888,6727,5;0,-5,8,3,6988,6137,4;8,3,5,5,2025,7953,4;5,5,1,9,2155,2808,6;1,9,1,4,9635,8027,9;1,4,8,3,6517,6766,4;8,-0,7,2,6931,5211,9;7,-2,9,1,5214,0508,1;9,-7,2,1,0798,2713,6;2,1,9,7,619,410,2;1,9,7,2,685,737,1;9,-6,1,9,3909,3652,5;1,-1,6,2,2577,6497,0;6,-9,3,5,6683,1532,8;3,-8,2,5,837,002,9;7,-2,9,1,6397,1681,1;9,-7,2,1,0924,2949,6;2,-4,5,5,2246,7174,3;5,-3,5,0,7417,4946,2;5,-2,4,8,4162,3364,1;4,-2,9,7,3461,2954,1;9,-6,1,9,2647,2390,5;-6,2,-36,-497,5,-6,0,6,3925,031,1;9,-7,2,1,753,011,0;7,-9,3,5,372,752,4;8,3,5,5,765,770,8;3,5,5,1,0160,3967,5;5,-6,0,6,171,847,2;5,-2,4,8,4979,3171,1;4,8,3,5,6311,1260,9;3,5,5,1,0230,3037,6;5,1,9,1,5575,0869,2;9,1,4,8,4240,3442,2;4,8,3,5,6507,1456,9;3,5,5,1,0307,3104,6;5,1,9,1,5489,0773,2;9,1,4,8,4340,3542,2;4,8,3,5,6391,1240,8;3,-8,2,5,1139,9104,7;2,-0,1,4,9365,8757,9;1,4,8,3,6287,6436,5;8,3,5,5,2003,7931,4;5,5,1,9,2148,2891,5;1,9,1,4,9994,8386,9;1,-3,1,9,8551,0046,2;1,-6,5,1,0049,3846,5;5,-6,0,6,3036,6975,5;0,6,2,1,351,619,0;6,2,1,9,847,685,6;2,-4,5,5,3857,8785,3;5,-3,5,0,7600,4139,2;5,-2,4,8,4325,3527,1;4,-2,9,7,036,837,2;1,-6,5,1,1122,4929,5;5,-6,0,6,3262,6101,5;0,-5,8,3,6408,6657,4;8,-0,7,2,6990,5270,9;7,-2,9,1,5496,0780,1;9,-7,2,1,0887,2802,6;2,-4,5,5,2595,7423,3;-8,4,-84,-526,-0,9,-09,-274,-2,1,-46,-018,-3,3,-41,-260,-7,4,-23,-620,-1,8,-75,-689,-6,2,-36,-498,-3,7,-00,-925,https://www.united.com/ual/en/us/-6,3,-95,-396,9,7,2,5,0,6,2,0,9,Sat Nov 72 0146 89:53:22 GMT-3757 (PST),-317028,81379,0,6,4407,5,5,27,0,6,CF1AF07E4BF0AFC6BFC853B097FD38E2355623CBEF690164BDB1052A46AC0127~-2~DbolZbyfwAD2pjynxPyaxcbuZdxqvTk32gp0dFQyWtA=~-2~-6,3928,-2,-3,38490517-0,3,-12,-053,2,5-1,8,-75,-684,-6-1,8,-75,-697,1,9,1,4,9,3,5-6,3,-95,-98,-0-8,4,-84,-22,07-6,7,-43,-758,50663740-0,3,-12,-065,339896-5,0,-89,-336,;5;-1;1'})


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
		login_params = {'IsHomePageTile':'true',
						'RememberMe':'true',
						'MpNumber':user,
						'Password':pwd}
		self.signin = self.post('https://www.united.com/ual/en/us/account/account/login',
			data=login_params, allow_redirects=True, headers=self.headers)


	def search_json(self, params):
		"""Perform flight search on new united.com.  Response is stored in self.search_results."""

		search_params = new_search_params(params.depart_airport, params.arrive_airport, params.depart_date)
		if params.nonstop:
			search_params['NonStopOnly']='true'

		# load search page to get a cart ID
		if not self.cart_id:
			if self.logging:
				print("Loading search page")
			self.search_page = self.post(
				'https://www.united.com/ual/en/us/flight-search/book-a-flight',
				data=search_params,
				allow_redirects=True,
				headers=self.headers,
				cookies=params.cookies,
			)
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
		self.search_results = self.post(
			'https://www.united.com/ual/en/us/flight-search/book-a-flight/flightshopping/getflightresults/rev',
			data=search_params_full,
			allow_redirects=True,
			headers=self.headers,
			cookies=params.cookies,
		)
		self.search_datetime = params.depart_datetime
		# all of the data is in search_results in nice json form!
		if self.logging:
			print("Received " + str(len(self.search_results.text)) + " characters")
			F = codecs.open('response_logs/search.html','w','utf-8')
			F.write(self.search_results.text)
			F.close()



	def extract_json_data(self):
		if self.tripdata:
			trips = json.loads(self.tripdata)
		else:
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


	def extract_html_data(self):
		soup = bs4.BeautifulSoup(self.search_results, 'lxml')
		trips = soup.findAll(attrs={"class": "flight-block"})

		alltrips = []
		for t in trips:
			depart = t.findAll(attrs={"class": "flight-time-depart"})
			arrive = t.findAll(attrs={"class": "flight-time-arrive"})
			segmentdtl = t.findAll(attrs={"class": "flight-block-tab-list"})
			upgrade = t.find(attrs={"class": "upgrade-available"})
			segs = zip(depart, arrive, segmentdtl)
			tripdata = []
			for s in segs:
				flight_data = json.loads(s[2].contents[3]['data-seat-select'])['Flights'][0]
				newseg = Segment()
				if upgrade:
					newseg.availability = ['R1+']
				else:
					newseg.availability = ['R0']
				# deptime = s[0].find(attrs={"class": "timeDepart"})
				newseg.depart_date,newseg.depart_time = flight_data['FlightDate'].split(' ')
				newseg.depart_airport = flight_data['Origin']
				# arrtime = s[1].find(attrs={"class": "timeArrive"})
				newseg.arrive_time = s[1].find(text=re.compile('[0-2]?[0-9]:[0-9]{2} (a|p)m')).strip()
				arrdate = s[1].find(attrs={"class" : "date-duration"})
				if arrdate:
					arrive_year = int(newseg.depart_date[-4:])
					if newseg.depart_date[:2] == '12' and arrdate.text[5:8] == 'Jan':
						arrive_year += 1
					elif newseg.depart_date[:2] == '01' and arrdate.text[5:8] == 'Dec':
						arrive_year -= 1
					newseg.arrive_date = arrdate.text + ' ' + str(arrive_year)
				else:
					newseg.arrive_date = newseg.depart_date
				newseg.arrive_airport = flight_data['Destination']
				newseg.flightno = flight_data['CarrierCode'] + flight_data['FlightNumber']
				newseg.aircraft = format_aircraft(flight_data['EquipmentDescription'])
				newseg.search_datetime = self.search_datetime
				tripdata.append(newseg)
			alltrips.append(tripdata)
		self.trips = alltrips
		if self.ua_only:
			self.trips = [t for t in self.trips if
				all([seg.flightno[:2]=='UA' and seg.flightno[-1]!=')' for seg in t])]


	def alert_search(self, params):
		"""Perform the search specified by params and return results matching the specified fare buckets."""
		self.search(params)
		try:
			self.extract_json_data()
		except:
			self.extract_html_data()
		found_segs = []
		for t in self.trips:
			if params.nonstop and len(t) > 1:
				continue
			for seg in t:
				seg.format_deptime()
				deptime = 100*seg.depart_datetime.hour + seg.depart_datetime.minute
				seg.search_buckets(params.buckets)
				# known bug: time-based search doesn't properly handle flights departing after midnight 
				if (
					not params.flightno
				) or (
					seg.flightno in params.flightno
				) or (
					params.flightno[0]=='>' and (
						deptime > int(params.flightno[1:]) or 
						seg.depart_datetime.day > seg.search_datetime.day
					) 
				) or (
					params.flightno[0]=='<' and 
					deptime < int(params.flightno[1:]) and
					seg.search_datetime.day == seg.depart_datetime.day
				):
					found_segs.append(seg)
		if len(found_segs)==0:
			raise Exception('No results found for '+str(params))
		return found_segs


	def basic_search(self, params):
		"""Perform the search specified by params and return all results."""
		self.search(params)
		try:
			self.extract_json_data()
		except:
			self.extract_html_data()
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



