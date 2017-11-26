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

#redefine stdout/stderr to handle utf-8
stdout = codecs.getwriter('utf-8')(sys.stdout)
stderr = codecs.getwriter('utf-8')(sys.stderr)


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


	def wait_for_text(self, xpath, text, wait_time_seconds=10, logfile=None):
		loaded = WebDriverWait(self, wait_time_seconds).until(
		    EC.text_to_be_present_in_element(
		    	(By.XPATH, xpath),
		    	text
		    )
		)
		if not loaded:
			stderr.write("Timeout waiting for response\n")
		if self.logging and logfile:
			stdout.write(
				"Received " + str(len(self.page_source)) + " characters.\n"
			)
			F = codecs.open(logfile, 'w', 'utf-8')
			F.write(self.page_source)
			F.close()


	def replace_text(self, field, new_text):
		field.clear()
		field.send_keys(new_text)


	def get_homepage(self):
		if self.logging:
			stdout.write("Loading united.com homepage.\n")
		self.get('https://www.united.com/web/en-US')
		self.homepage=True

		signin_tile = self.find_elements_by_xpath('//*[@id="tile-signin"]/a')[0]
		signin_tile.click()

		self.wait_for_text(
			'//*[@id="frm-login"]/div[2]/a',
			"Forgot your MileagePlus number?",
			logfile='response_logs/homepage.html',
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

		self.wait_for_text(
			'//*[@id="main-content"]/div[2]/div/h1',
			"We don't recognize this device",
			logfile='response_logs/login.html',
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

		self.wait_for_text(
			'//*[@id="main-content"]/div[2]/h1',
			"Welcome to united.com",
			logfile="response_logs/questions.html",
		)


	def search(self, params):
		if self.logging:
			stdout.write("Searching for " + str(params) + "\n")
		Origin = self.find_element_by_id("Origin")
		Destination = self.find_element_by_id("Destination")
		DepartDate = self.find_element_by_id("DepartDate")
		if self.homepage:
			OneWay = self.find_element_by_id("SearchTypeMain_oneWay")
			OneWay.click()

		self.replace_text(DepartDate, params.depart_date)
		self.replace_text(Origin, params.depart_airport)
		self.replace_text(Destination, params.arrive_airport + Keys.ENTER)

	# wait for this to disappear if you want 1-stop itineraries
	# '//*[@id="fl-stopsresults-loader-partial"]/h2'
	# "Loading flight options with stops"

		self.wait_for_text(
			'//*[@id="flight-details-1"]',
			'',
			logfile='response_logs/search_results.html',
		)
		self.homepage=False


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



if __name__ == "__main__":
	b = ual_browser(sys.argv[1], sys.argv[2], headless=False, logging=True)
	data = ['5/22/18','SFO','AUS','','FX','True']
	params = alert_params(*data)
	b.search(params)
	cookies = b.convert_cookies()
	#cookies = '; '.join(c['name'] + '=' + c['value'] for c in b.get_cookies())
	cart_id = b.find_element_by_id('EditSearchCartId').get_attribute('value')
	tab_id = b.find_element_by_id('UASessionTabId').get_attribute('value')
	S = ual_search_session(cookies, cart_id, tab_id, logging=True)
	S.basic_search(params)
	# b.extract_html_data()
