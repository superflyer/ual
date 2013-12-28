#!/usr/bin/env python

import requests
import bs4
import re
import codecs
import sys
import smtplib
import os
from datetime import *
from dateutil import parser
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from ual_params import *


#constants
airport_pattern = re.compile('.*\(([A-Z]{3}).*\).*')
Fclasses = ['F','FN','A','ON','O']
Jclasses = ['J','JN','C','D','Z','ZN','P','PN','R','RN','IN','I']
Yclasses = ['Y','YN','B','M','E','U','H','HN','Q','V','W','S','T','L','K','G','N','XN','X']
Nclasses = ['R','I','X']  # removing ON since this is C->F upgrade
min_avail = 'FJY'
award_buckets = 'OIRX'

aircraft_types = ['Boeing','Airbus','Canadair','Embraer','Avro']
airline_codes = ['UA','LH']

ual_user = 'NP904725'
ual_pwd = '4321'
spoofUA = 'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.66 Safari/537.36'

alert_recipient = 'dfreeman@cs.stanford.edu'
alert_sender = 'superflyer02@gmail.com'
gmail_user = 'superflyer02'
gmail_pwd = 'enderwiggin1234'

stdout = codecs.getwriter('utf-8')(sys.stdout)
stderr = codecs.getwriter('utf-8')(sys.stderr)

#set time zone
os.environ['TZ'] = 'US/Pacific'

def get_airport(tdtime):
	tddate = tdtime.parent.findNextSibling('div')
	tdairport = tddate.findNextSibling('div')
	return tddate.text,tdairport.text

def format_airport(airport):
	return airport_pattern.match(airport).group(1)

def format_aircraft(aircraft):
	if aircraft[:6] == 'Boeing':
		boeing = re.match('Boeing (7[0-9])[0-9]-([0-9]).*',aircraft)
		if boeing:
			return boeing.group(1)+boeing.group(2)
		else:
			return aircraft
	elif aircraft[:6] == 'Airbus':
		airbus = re.match('Airbus A([0-9]{2})([0-9])(-([0-9])00)?.*',aircraft)
		if airbus:
			if airbus.group(3):
				return airbus.group(1)+airbus.group(4)
			else:
				return airbus.group(1)+airbus.group(2)
		else:
			return aircraft
	elif aircraft[:8] == 'Canadair':
		canadair = re.match('Canadair Regional Jet ([0-9])00.*',aircraft)
		if canadair:
			return 'CR'+canadair.group(1)
		else:
			return aircraft
	else:
		return aircraft

def long_search_def(start_date,end_date,depart_airport,arrive_airport,buckets='',flightno='',filename='long_search_defs.txt'):
	alert_defs = []
	cur_datetime = parser.parse(start_date)
	F = open(filename,'aw')
	while cur_datetime <= parser.parse(end_date):
		depart_date = cur_datetime.strftime('%m/%d/%y')
		F.write('\t'.join([depart_date,depart_airport,arrive_airport,'',buckets])+'\n')
		cur_datetime += timedelta(1)
	F.close()
	return 1


def send_email(subject,message,recipient=alert_recipient):
	msg = MIMEText(message)
	msg['From'] = alert_sender
	msg["To"] = alert_recipient
	msg["Subject"] = subject
	s = smtplib.SMTP_SSL('smtp.gmail.com',465)
	s.login(gmail_user,gmail_pwd)
	s.sendmail(alert_sender, [alert_recipient], msg.as_string())
	return 1



class Segment(object):
	def __init__(self):
		self.depart_airport = None
		self.depart_time = None
		self.depart_date = None
		self.arrive_airport = None
		self.arrive_time = None
		self.arrive_date = None
		self.aircraft = None
		self.availability = 'NA'
		self.flightno = None
		self.search_results = None
		self.search_query = None
	def __repr__(self):
		paramlist=[self.flightno,self.depart_date,self.depart_airport,self.depart_time,
		self.arrive_airport,self.arrive_time,self.aircraft,self.availability.strip()]
		return(' '.join(paramlist))
	def __str__(self):
		return self.__repr__()
	def format_deptime(self):
		self.depart_datetime = parser.parse(self.depart_date+' '+self.depart_time)
#		return self.depart_datetime.strftime('%m/%d/%y %H:%M')
	def format_arrtime(self):
		self.arrive_datetime = parser.parse(self.arrive_date+' '+self.arrive_time)
		if self.depart_date:
			self.day_offset=''
			if self.depart_datetime.day != self.arrive_datetime.day:
				for offset in ['-1','+1','+2']:
					if self.arrive_datetime.day == (self.depart_datetime+timedelta(days=int(offset))).day:
						self.day_offset = offset
	def condensed_repr(self):
		self.format_deptime()
		self.format_arrtime()
		output_params = [self.depart_datetime.strftime('%m/%d/%y').strip('0'),
			self.flightno,
			format_airport(self.depart_airport),
			self.depart_datetime.strftime('%H:%M'),
			format_airport(self.arrive_airport),
			self.arrive_datetime.strftime('%H:%M')+self.day_offset,
			format_aircraft(self.aircraft),
			' '.join([b+str(self.search_results[b])+(str(self.search_results[b+'N']) if b in Nclasses else '') for b in self.search_query]) if self.search_query else self.availability.strip()]
		return ' '.join(output_params)

	def search_buckets(self,buckets):
		results = {}
		self.search_query = ''
		for b in buckets.upper():
			inv = re.match('.*'+b+'([0-9]).*',self.availability)
			if inv:
				results[b] = int(inv.group(1))
				self.search_query += b
			if b in Nclasses:
				invN = re.match('.*'+b+'N([0-9]).*',self.availability)
				if invN:
					results[b+'N'] = int(invN.group(1))
		self.search_results = results

	def send_alert_email(self,alert_def):
		subject = 'Availability found for alert '+str(alert_def)
		message = 'Query: '+str(alert_def)+'\nResults: '+self.condensed_repr()
		e = send_email(subject,message)
		return e


class alert_params(object):
	def __init__(self,depart_date,depart_airport,arrive_airport,flightno=None,buckets=None,nonstop=False):
		self.depart_airport=depart_airport
		self.arrive_airport=arrive_airport
		self.buckets=buckets.upper() if buckets else None
		self.flightno=flightno
		# need to do some error-checking on dates
		depart_datetime = parser.parse(depart_date)  # assume h:mm = 0:00
		if depart_datetime + timedelta(days=1,minutes=-1) < datetime.today() :
			raise Exception('Depart date is in the past.')
		if depart_datetime > datetime.today() + timedelta(days=331):
			raise Exception('Depart date is more than 331 days in the future.')
		self.depart_date=depart_date
		self.nonstop=nonstop
	def __repr__(self):
		return ' '.join([self.depart_date,
			self.flightno if self.flightno else '',
			self.depart_airport,
			self.arrive_airport,
			self.buckets if self.buckets else '',
			'NS' if self.nonstop else ''])
	def __str__(self):
		return self.__repr__()




class ual_session(requests.Session):

	def __init__(self,user=None,pwd=None,logging=False,useragent=None):
		requests.Session.__init__(self)
		if useragent:
			self.headers={'User-Agent':useragent}
		else:
			self.headers={}
		home = self.get('https://www.united.com',allow_redirects=True,headers=self.headers)
		if user:
			login_params = set_login_params(self.cookies['SID'])
			login_params['ctl00$ContentInfo$accountsummary$OpNum1$txtOPNum'] = user
			login_params['ctl00$ContentInfo$accountsummary$OpPin1$txtOPPin'] = pwd
			signin = self.post('https://www.united.com/web/en-US/default.aspx',data=login_params,allow_redirects=True)
			if logging:
				F = codecs.open('signin.html','w','utf-8')
				F.write(signin.text)
				F.close()
			if 'The sign-in information you entered does not match an account in our records.' in signin.text or user not in signin.text:
				raise Exception('Login to united.com failed.')
			else:
				self.user = user
			self.last_login_time = datetime.now()

	def search(self,params,logging=False):
		search_params = set_search_params(self.cookies['SID'])
		search_params['ctl00$ContentInfo$Booking1$Origin$txtOrigin']=params.depart_airport
		search_params['ctl00$ContentInfo$Booking1$Destination$txtDestination']=params.arrive_airport
		search_params['ctl00$ContentInfo$Booking1$DepDateTime$Depdate$txtDptDate']=params.depart_date
		if params.nonstop:
			search_params['ctl00$ContentInfo$Booking1$Direct$chkFltOpt']='on'
		search = self.post('https://www.united.com/web/en-US/default.aspx',data=search_params,allow_redirects=True,headers=self.headers)
		if logging:
			F = codecs.open('search.html','w','utf-8')
			F.write(search.text)
			F.close()
		return search.text

	def alert_search(self,params):
		results = self.search(params)
		trips = extract_data(results)
		found_segs = []
		for t in trips:
			for seg in t:
				seg.search_buckets(params.buckets)
				if not params.flightno or seg.flightno in params.flightno:
					found_segs.append(seg)
		if len(found_segs)==0:
			failed = self.search(params,logging=True)
			raise Exception('No results found for '+str(params))
		return found_segs

	def basic_search(self,params):
		results = self.search(params)
		data = extract_data(results)
		for trip in data:
			for seg in trip:
				if params.buckets:
					seg.search_buckets(params.buckets)
				print(seg.condensed_repr())
			print('---')
		return data

	def long_search(self,start_date,end_date,depart_airport,arrive_airport,buckets=None,flightno=None):
		found_segs = []
		cur_datetime = parser.parse(start_date)
		while cur_datetime <= parser.parse(end_date):
			depart_date = cur_datetime.strftime('%m/%d/%y')
			params = alert_params(depart_date,depart_airport,arrive_airport,buckets=buckets,flightno=None,nonstop=True)
			search_results = self.alert_search(params)
			for seg in search_results:
				if sum(seg.search_results.values()) > 0:
					print(seg.condensed_repr())
					found_segs.append(seg)
			cur_datetime += timedelta(1)
		return found_segs


def extract_data(input_html):
	soup = bs4.BeautifulSoup(input_html)
#	soup = bs4.BeautifulSoup(input_html,'lxml')

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
			buckets = s[2].find(text=re.compile(', '.join([c+'[0-9]' for c in Yclasses])))
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


def run_alerts(ses=None,filename='alert_defs.txt'):
	# open Session
	if not ses:
		try:
			ses = ual_session(ual_user,ual_pwd,useragent=spoofUA)
		except Exception as e:
			subject = e.args[0]
			message = 'User: '+ual_user
			send_email(subject,message)
			raise
	# read alert defs
	F = open(filename,'r')
	alert_defs = []
	for line in F:
		try:
			data = line.strip().split('\t')
			if data[0][0]=='#' or len(data) < 3: continue
			a = alert_params(*data)
			alert_defs.append(a)
		except:
			stderr.write('Error parsing alert definition: '+line)
			continue
	print datetime.today().strftime('%c')
	for a in alert_defs:
		# search for alerts
		try:
			segs = ses.alert_search(a)
		except Exception as e:
			subject = e.args[0]
			message = 'Query: '+str(a)
			stderr.write(subject+'\n'+message+'\n')
			send_email(subject,message)
			continue
		for seg in segs:
			print(seg.condensed_repr())
			if sum(seg.search_results.values()) > 0:
				seg.send_alert_email(a)
	return(ses)




#S,D = basic_search('9/20/14','sfo','fra',min_avail+award_buckets)

def test():
	S = ual_session(ual_user,ual_pwd,useragent=spoofUA)
	X = S.long_search('7/11/14','7/25/14','SFO','JFK','I')
	return(S,X)

def scratch():
	x = X[0][0]
	print(x.condensed_repr())
	x.search_buckets('JIRYX')
	print(x.condensed_repr())

def ual():
	S = ual_session(ual_user,ual_pwd,useragent=spoofUA)
	return S

if __name__=='__main__':
	if sys.argv[1]:
		S = run_alerts(ses=None,filename=sys.argv[1])
	else:
		S = run_alerts()




