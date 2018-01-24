#!/usr/bin/env python
import bs4
import codecs
from datetime import datetime
import re
import requests
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
from time import sleep
from ual_session import *
from ual_functions import *

# redefine stdout/stderr to handle utf-8
stdout = codecs.getwriter('utf-8')(sys.stdout)
stderr = codecs.getwriter('utf-8')(sys.stderr)

# javascript for searches
inject_js = """RESULTS = [];
        (function(JSON) {
          var oldParse = JSON.parse;

          JSON.parse = function(data, reviver) {
            var result = oldParse(data, reviver);

            if (result && result['data'] && result['data']['Trips'] && result['data']['Trips'][0] && result['data']['Trips'][0]['Flights']) {
              console.log('Found something with trips!');
              console.log(result['data']['Trips'][0]['Flights']);
              RESULTS = RESULTS.concat(result['data']['Trips'][0]['Flights']);
            }

            return result;
          };
        }(JSON));"""

fetch_js = "return JSON.stringify(RESULTS);"


class ual_browser(webdriver.Chrome):
	def __init__(self, search_type=None, headless=True, ua_only=False, logging=False, debug=False):

		# set options and initialize
		if logging:
			stdout.write("Initializing headless Chrome\n")
			headless=False
		chrome_options = Options()
		if headless:
			chrome_options.add_argument("--headless")
			chrome_options.add_argument("--window-size=1920x1080")
		webdriver.Chrome.__init__(self, chrome_options=chrome_options)
		#webdriver.Firefox.__init__(self)
		self.ua_only = ua_only
		self.logging = logging
		self.last_login_time = datetime.min
		self.debug = debug
		self.search_type = search_type

		if self.logging:
			stdout.write("Loading united.com booking page.\n")
		self.get_startpage()


	def get_startpage(self, wait=True):
		self.delete_all_cookies()
		self.get('https://www.united.com/ual/en/us/flight-search/book-a-flight')
		self.first_page = True
		self.last_refresh_time = datetime.now()
		if wait:
			self.wait_for_load(
				'//*[@id="btn-search"]',
				text='Book',
				logfile='searchpage.html',
			)

		# self.get_search_page()
		# self.get_homepage()
		# self.login(user, pwd)
		# self.answer_questions()


	def wait_for_load(self, xpath, text=None, wait_time_seconds=20, logfile=None,
			denied_xpath = '/html/body/h1'
	):
		loaded = WebDriverWait(self, wait_time_seconds).until(
		    EC.presence_of_element_located((By.XPATH, xpath + ' | ' + denied_xpath))
		)
		if text:
			loaded = EC.text_to_be_present_in_element(
			    	(By.XPATH, xpath),
			    	text,
			)
		if 'Access Denied' in self.page_source:
			raise AuthorizationError(self.current_url)
		if not loaded:
			stderr.write("Timeout waiting for response\n")
		if self.logging and logfile:
			stdout.write(
				"Received " + str(len(self.page_source)) + " characters.\n"
			)
			F = codecs.open('response_logs/' + logfile, 'w', 'utf-8')
			F.write(self.page_source)
			F.close()


	def replace_text(self, field, new_text):
		field.clear()
		field.send_keys(new_text)


	def get_homepage(self, reload=False):
		if self.logging:
			stdout.write("Loading united.com homepage.\n")
		self.get('https://www.united.com/web/en-US')
		self.homepage=True

		signin_tile = self.find_elements_by_xpath('//*[@id="tile-signin"]/a')[0]
		signin_tile.click()

		self.wait_for_load(
			'//*[@id="frm-login"]/div[2]/a',
			"Forgot your MileagePlus number?",
			logfile='homepage.html',
		)


	def login(self, user, pwd):
		if self.logging:
			stdout.write("Logging in to united.com.\n")
		username = self.find_element_by_id("MpNumber")
		password = self.find_element_by_id("Password")
		username.send_keys(user)
		password.send_keys(pwd)
		loginButton = self.find_element_by_id("btnSignIn")
		loginButton.click()
		self.last_login_time = datetime.now()

		self.wait_for_load(
			'//*[@id="QuestionsList_0__AnswerKey"]',
			logfile='login.html',
		)


	def answer_questions(self):
		'''answer the security questions using the first element from each list'''
		if self.logging:
			stdout.write("Answering security questions.\n")
		for i in [0,1]:
			q = self.find_element_by_id('QuestionsList_' + str(i) + '__AnswerKey')
			a = sorted(q.text.split('\n'))[0]
			q.send_keys(a)
		remember = self.find_element_by_id("IsRememberDevice_True")
		remember.click()
		nextButton = self.find_element_by_id("btnNext")
		nextButton.click()

		self.wait_for_load(
			'//*[@id="main-content"]/div[2]/h1',
			"Welcome to united.com",
			logfile="questions.html",
		)


	def convert_cookies(self):
		jar = requests.cookies.RequestsCookieJar()
		for c in self.get_cookies():
			jar.set(
				c['name'],
				c['value'],
				domain=c['domain'],
				path=c['path'],
				secure=c['secure'],
				rest={'HttpOnly' : c['httpOnly']},
				expires=(None if "expiry" not in c.keys() else c['expiry'])
			)
		return(jar)


class ual_selenium_session(ual_session):
	def __init__(self, browser):
		ual_session.__init__(self, logging=browser.logging, ua_only=browser.ua_only)
		self.browser = browser
		self.debug = browser.debug
		browser.first_page = True
		self.is_retry = False


	def __enter__(self):
		return self


	def __exit__(self, type, value, traceback):
		if self.debug:
			return
		if isinstance(value, KeyboardInterrupt):
			return
		self.browser.quit()


	def search(self, params):
		b = self.browser
		if b.logging:
			stdout.write("Searching for " + str(params) + "\n")
		self.search_datetime = params.depart_datetime

		if b.first_page:
			Origin = b.find_element_by_id('Trips_0__Origin')
			Destination = b.find_element_by_id('Trips_0__Destination')
			DepartDate = b.find_element_by_id('Trips_0__DepartDate')
	 		OneWay = b.find_elements_by_xpath('//*[@id="search-summary-wrapper"]/fieldset[4]/div/div/div/label[2]')[0]
	 		Award = b.find_elements_by_xpath('//*[@id="award-container"]/div/div/div[2]/label[2]')[0]
			search_btn = b.find_element_by_id('btn-search')
			Nonstop = b.find_element_by_id("Trips_0__NonStop")
			Upgrade = b.find_element_by_id("select-upgrade-type")

			if params.nonstop: Nonstop.click()
			OneWay.click()
			if params.award: Award.click()
			# Upgrade.send_keys('M' + Keys.ENTER)
		else:
			Origin = b.find_element_by_id("Origin")
			Destination = b.find_element_by_id("Destination")
			DepartDate = b.find_element_by_id("DepartDate")
			search_btn = b.find_elements_by_xpath('//*[@id="flightSearch"]/fieldset/div/div[2]/div/div[2]/button')[0]

		b.replace_text(DepartDate, params.depart_date + Keys.TAB)
		b.replace_text(Origin, params.depart_airport + Keys.TAB)
		b.replace_text(Destination, params.arrive_airport + Keys.TAB)
		search_btn.click()
		if b.logging:
			stdout.write('Initiated search\n')

		try:
			b.wait_for_load(
				'//*[@id="fl-results-loader-full"]/h2',
				'Thank you for choosing United',
			)
			b.execute_script(inject_js);
			b.wait_for_load(
				'//*[@id="flight-result-list-revised"]/li[1]/div[2]',
				logfile='search_results.html',
				wait_time_seconds=10,
			)
			b.first_page = False
			stdout.write('Results loaded\n')
		except AuthorizationError:
			if b.first_page:
				raise
			else:
				stderr.write('Access denied, retrying\n')
				b.get_startpage()
				b.first_page = True
				self.search(params)
		except UnexpectedAlertPresentException as e:
			stderr.write('Received alert: ' + str(e) + '\n')
			Alert(b).accept()
			sleep(5)
			if self.is_retry:
				result = []
			else:
				self.is_retry = True
				self.search(params)
		except TimeoutException:
			if 'There are no flights' in b.page_source:
				pass
			else:
				raise


		self.search_results = b.page_source
		self.tripdata = b.execute_script(fetch_js)
		self.is_retry = False


class AuthorizationError(Exception):
    """Exception raised for authorization errors to united.com

    Attributes:
        url -- url of the error
    """
    def __init__(self, url):
    	stderr.write('Access denied to ' + url + '\n')


if __name__ == "__main__":

	b = ual_browser(headless=False, logging=True)
	S = ual_selenium_session(b)
	# data = ['5/22/18','SFO','AUS','','FX',True]
	# params = alert_params(*data)
	# S.search(params)
	# S.extract_html_data()
	# for t in S.trips:
	# 	print t

	data2 = ['1/5/18','LAX','SFO','','OIR',True]
	S.search(alert_params(*data2))
	S.extract_html_data()
	for t in S.trips: print t

