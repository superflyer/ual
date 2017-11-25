#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ual_browser(webdriver.Chrome):
	def __init__(self, user, pwd):
		webdriver.Chrome.__init__(self)
		self.get_homepage()
		self.login(user, pwd)
		self.answer_questions()


	def wait_for_text(self, xpath, text, wait_time_seconds=10):
		loaded = WebDriverWait(self, wait_time_seconds).until(
		    EC.text_to_be_present_in_element(
		    	(By.XPATH, xpath),
		    	text
		    )
		)
		if not loaded:
			self.quit()


	def get_homepage(self):
		self.get('https://www.united.com/web/en-US')

		signin_tile = self.find_elements_by_xpath('//*[@id="tile-signin"]/a')
		signin_tile[0].click()

		self.wait_for_text(
			'//*[@id="frm-login"]/div[2]/a',
			"Forgot your MileagePlus number?"
		)


	def login(self, user, pwd):
		username = self.find_element_by_id("MpNumber")
		password = self.find_element_by_id("Password")
		username.send_keys(user)
		password.send_keys(pwd)
		loginButton = self.find_element_by_id("btnSignIn")
		loginButton.click()

		self.wait_for_text(
			'//*[@id="main-content"]/div[2]/div/h1',
			"We don't recognize this device"
		)

	def answer_questions(self):
		'''answer the security questions using the first element from each list'''
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
			"Welcome to united.com"
		)

