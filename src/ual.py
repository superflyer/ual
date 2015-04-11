#!/usr/bin/env python

import requests
import bs4
import re
import codecs
import sys
import smtplib
import os
import argparse
from copy import deepcopy
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
remapped_classes = {'1':'HN'}
min_avail = 'FJY'
award_buckets = 'OIRX'
#bucket_regex = re.compile(', '.join([c+'[0-9]' for c in Yclasses]))
bucket_regex = re.compile(', '.join(['[A-Z][0-9]']*10))

aircraft_types = ['Boeing','Airbus','Canadair','Embraer','Avro']
airline_codes = ['UA','LH']

stdout = codecs.getwriter('utf-8')(sys.stdout)
stderr = codecs.getwriter('utf-8')(sys.stderr)

#set time zone
os.environ['TZ'] = 'US/Pacific'

def configure(config_file='ual.config'):
	"""import user-configured parameters
	the config file needs to have the following variables, in format <var>:<value>
		ual_user = MileagePlus Number
		ual_pwd = MileagePlus PIN or Password
		spoofUA = Useragent to send requests with
		alert_recipient = recipient of alert emails
		gmail_user = username of gmail account sending alerts
		gmail_pwd = password of gmail account sending alerts
		sms_alerts = email address that receives text messages
	"""
	F = open(config_file)
	config = {}
	for line in F:
		p = line.strip().split(':')
		config[p[0]] = p[1]
	F.close()
	return config

def get_airport(tdtime):
	tddate = tdtime.parent.findNextSibling('div')
	tdairport = tddate.findNextSibling('div')
	return tddate.text,tdairport.text

def format_airport(airport):
	return airport_pattern.match(airport).group(1)

def format_aircraft(aircraft):
	if not aircraft:
		return ''
	elif aircraft[:6] == 'Boeing':
		boeing = re.match('Boeing (7[0-9])[0-9]-([0-9]).*',aircraft)
		if boeing:
			return boeing.group(1)+boeing.group(2)
	elif aircraft[:6] == 'Airbus':
		airbus = re.match('Airbus A([0-9]{2})([0-9])(-([0-9])00)?.*',aircraft)
		if airbus:
			if airbus.group(3):
				return airbus.group(1)+airbus.group(4)
			else:
				return airbus.group(1)+airbus.group(2)
	elif aircraft[:8] == 'Canadair':
		canadair = re.match('Canadair Regional Jet ([0-9])00.*',aircraft)
		if canadair:
			return 'CR'+canadair.group(1)
	elif aircraft[:7] == 'Embraer':
		embraer = re.match('Embraer ERJ-1([0-9]{2})',aircraft)
		if embraer:
			return 'E'+embraer.group(1)
	return aircraft

def long_search_def(start_date,end_date,depart_airport,arrive_airport,buckets='',flightno='',filename='alerts/long_search_defs.txt'):
	alert_defs = []
	cur_datetime = parser.parse(start_date)
	F = open(filename,'aw')
	while cur_datetime <= parser.parse(end_date):
		depart_date = cur_datetime.strftime('%m/%d/%y')
		F.write('\t'.join([depart_date,depart_airport,arrive_airport,'',buckets])+'\n')
		cur_datetime += timedelta(1)
	F.close()
	return 1


def send_email(subject,message,config):
	if config['output_file']:
		F = open(config['output_file'],'a')
		F.write(message)
		F.write('\n')
		F.close()
	else:
		msg = MIMEText(message)
		msg['From'] = config['alert_sender']
		msg["To"] = config['alert_recipient']
		msg["Subject"] = subject
		s = smtplib.SMTP_SSL('smtp.gmail.com',465)
		s.login(config['gmail_user'],config['gmail_pwd'])
		s.sendmail(config['alert_sender'], [config['alert_recipient']], msg.as_string())
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
	def format_depairport(self):
		return format_airport(self.depart_airport)
	def format_arrairport(self):
		return format_airport(self.arrive_airport)
	def bucket_repr(self):
		if self.search_query:
			return ' '.join([(remapped_classes[b] if b in remapped_classes else b)+str(self.search_results[b])+(str(self.search_results[b+'N']) if b in Nclasses else '') for b in self.search_query])
		elif self.search_query=='':
			return 'NA'
		else:
			return self.availability.strip()
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
			self.bucket_repr()]
		return ' '.join(output_params)

	def search_buckets(self,buckets):
		results = {}
		self.search_query = ''
		for b in buckets.upper():
			if b in remapped_classes:
				inv = re.match('.*'+remapped_classes[b]+'([0-9]).*',self.availability)
			else:
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
		subject = config['email_subject'] if config['email_subject'] else 'Results for '+str(alert_def)
		message = 'Query: '+str(alert_def)+'\nResults: '+self.condensed_repr()
		e = send_email(subject,message,config)
		return e


class alert_params(object):
	def __init__(self,depart_date,depart_airport,arrive_airport,flightno=None,buckets=None,nonstop=False):
		self.depart_airport=depart_airport.upper()
		self.arrive_airport=arrive_airport.upper()
		self.buckets=buckets.upper() if buckets else ''
		self.flightno=flightno
		# need to do some error-checking on dates
		self.depart_datetime = parser.parse(depart_date)  # assume h:mm = 0:00
		if self.depart_datetime + timedelta(days=1,minutes=-1) < datetime.today() :
			raise Exception('Depart date is in the past.')
		if self.depart_datetime > datetime.today() + timedelta(days=331):
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
	def copy(self):
		return(deepcopy(self))
	def other_buckets(self):
		others = re.search('[^'+award_buckets+']+',self.buckets)
		if others:
			return others.group()
		else:
			return ''




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
		results = self.search(params)
		data = extract_data(results)
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


def run_alerts(config,ses=None,filename='alerts/alert_defs.txt',aggregate=False):
	"""If no output file specified then send email to address specified in config.
	"""
	# open Session
	if not ses:
		try:
			ses = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'])
		except Exception as e:
			subject = e.args[0]
			message = 'User: '+config['ual_user']
			send_email(subject,message,config)
			raise
	# read alert defs
	F = open(filename,'r')
	alert_defs = []
	for line in F:
		try:
			data = line.strip().split('\t')
			if len(data) < 3 or data[0][0]=='#': continue
			if aggregate:
				end_date = data.pop(1)
			else:
				end_date = data[0]
			a = alert_params(*data)
			a.nonstop=True
			cur_datetime = parser.parse(data[0])
			while cur_datetime <= parser.parse(end_date):
				b = a.copy()
				b.depart_date = cur_datetime.strftime('%m/%d/%y')
				b.depart_datetime = cur_datetime
				alert_defs.append(b)
				cur_datetime += timedelta(1)
		except:
			stderr.write('Error parsing alert definition: '+line)
			continue
	F.close()

	print datetime.today().strftime('%c')
	results = []
	errors = []
	for a in alert_defs:
		# search for alerts
		try:
			segs = ses.alert_search(a)
		except Exception as e:
			if aggregate:
				errors.append((a,e.args[0]))
			else:
				subject = e.args[0]
				message = 'Query: '+str(a)
				stderr.write(subject+'\n'+message+'\n')
				if config['alert_recipient'] != config['sms_alerts']:
					# don't send error messates via sms
					send_email(subject,message,config)
			continue
		for seg in segs:
			print(seg.condensed_repr())
			if sum(seg.search_results.values()) > 0:
				results.append(seg)
				if not aggregate:
					seg.send_alert_email(a)
	if aggregate:
		if results:
			subject = config['email_subject'] if config['email_subject'] else 'SuperFlyer search results found'
#			message = '\n'.join(sorted([seg.condensed_repr() for seg in results]))
			message = '\n'.join([seg.condensed_repr() for seg in sorted(results, key=lambda x: x.depart_datetime)])
			e = send_email(subject,message,config)
		if errors:
			subject_err = 'Errors in SuperFlyer search'
			message_err = '\n'.join([str(a)+': '+str(e) for a,e in errors])
			e1 = send_email(subject_err,message_err,config)

	return(ses)



def test():
	from itertools import chain
	config = configure()
	S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'])
	P = alert_params('10/30/14','MSP','SFO',None,'X1')
	X = S.basic_search(P)
	return(S,list(chain.from_iterable(X)))

def scratch():
	x = X[0][0]
	print(x.condensed_repr())
	x.search_buckets('JIRYX')
	print(x.condensed_repr())

def ual(logging=False):
	"""quickly load a session for debugging purposes"""
	config = configure('../ual.config')
	S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'],logging=logging)
	return S

if __name__=='__main__':

	argparser = argparse.ArgumentParser(description='Search united.com for flight availability.')
	argparser.add_argument("-a", action="store_true", help="search on date range and aggregate results")
	argparser.add_argument("-o", metavar="output_file", type=str, help="filename to store results")
	argparser.add_argument('alert_file', type=str, help='file containing alert definitions')	# metavar='file',
	argparser.add_argument('-c', metavar="config_file", default="ual.config", type=str, help="filename containing configuration parameters (default: ual.config)")
	argparser.add_argument('-s', metavar="email_subject", type=str, help="subject to be sent in emails")

	recipient = argparser.add_mutually_exclusive_group()
	recipient.add_argument("-t", action="store_true", help="send text message instead of email")
	recipient.add_argument("-e", metavar="email_address", type=str, help="email address to send results to")

	args = argparser.parse_args()


	config = configure(args.c)

	# configure to send text mesages
	if args.t:
		config['alert_recipient'] = config['sms_alerts']
	
	# configure custom email address
	if args.e:
		config['alert_recipient'] = args.e

	# configure output file
	if args.o:
		config['output_file'] = args.o
	else:
		config['output_file'] = None

	# configure email subject
	if args.s:
		config['email_subject'] = args.s
	else:
		config['email_subject'] = None
	if args.alert_file:
		if args.a:
			S = run_alerts(config,ses=None,filename=args.alert_file,aggregate=True)
		else:
			S = run_alerts(config,ses=None,filename=args.alert_file)
	else:
		S = run_alerts(config)




