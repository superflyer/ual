#!/usr/bin/env python
import bs4
import codecs
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
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
	def __init__(self, user, pwd, headless=True, ua_only=False, logging=False):

		# set options and initialize
		chrome_options = Options()
		if headless:
			chrome_options.add_argument("--headless")
			chrome_options.add_argument("--window-size=1920x1080")
		webdriver.Chrome.__init__(self, chrome_options=chrome_options)
		self.ua_only = ua_only
		self.logging=logging

		# log in
		self.get_homepage()
		self.login(user, pwd)
		self.answer_questions()


	def wait_for_load(self, xpath, text=None, wait_time_seconds=10, logfile=None):
		loaded = WebDriverWait(self, wait_time_seconds).until(
		    EC.text_to_be_present_in_element(
		    	(By.XPATH, xpath),
		    	text
		    ) if text else
		    EC.presence_of_element_located((By.XPATH, xpath))
		)
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

		self.wait_for_load(
			'//*[@id="main-content"]/div[2]/div/h1',
			"We don't recognize this device",
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
		self.ua_only = browser.ua_only
		self.browser = browser


	def __enter__(self):
		return self


	def __exit__(self, type, value, traceback):
		if not self.debug:
			self.browser.quit()


	def search(self, params):
		b = self.browser
		if b.logging:
			stdout.write("Searching for " + str(params) + "\n")
		self.search_datetime = params.depart_datetime

		Origin = b.find_element_by_id("Origin")
		Destination = b.find_element_by_id("Destination")
		DepartDate = b.find_element_by_id("DepartDate")
		if b.homepage:
			OneWay = b.find_element_by_id("SearchTypeMain_oneWay")
			OneWay.click()
			if params.nonstop:
				Nonstop = b.find_element_by_id("NonStopOnly")
				Nonstop.click()

		b.replace_text(DepartDate, params.depart_date)
		b.replace_text(Origin, params.depart_airport)
		b.replace_text(Destination, params.arrive_airport + Keys.ENTER)
		b.execute_script(inject_js);
		if params.nonstop:
			b.wait_for_load(
				'//*[@id="flight-result-list-revised"]',
				logfile='search_results.html',
			)
		else:
			b.wait_for_load(
				'//*[@id="FWSolutionSetId"]',
				logfile='search_results.html',
			)

		self.tripdata = b.execute_script(fetch_js)
		b.homepage=False # only the first query is on the homepage

		# we get "access denied" after 3 requests made in this way,
		# so we're reloading the home page each time to start over.
		# this is very slow.
		b.get('https://www.united.com/web/en-US')
		b.homepage=True


if __name__ == "__main__":
	b = ual_browser(sys.argv[1], sys.argv[2], headless=False, logging=True)
	data = ['5/22/18','SFO','AUS','','FX','True']
	params = alert_params(*data)
	S = ual_selenium_session(b)
	S.search(params)
	S.extract_json_data()
	print(S.trips)

	data2 = ['1/22/18','LHR','SFO','','OIR','True']
	S.search(alert_params(*data2))
	S.extract_json_data()
	print(S.trips)

