import re
import smtplib

from copy import deepcopy
from datetime import *
from dateutil import parser
from email.mime.text import MIMEText


#global constants
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

aircraft_types = ['Boeing','Airbus','Canadair','Embraer','Avro','ATR']
airline_codes = ['UA','LH','WP','LX','NH','AC','HA']



def get_airport(tdtime):
	tddate = tdtime.parent.findNextSibling('div')
	tdairport = tddate.findNextSibling('div')
	return tddate.text,tdairport.text

def format_airport(airport):
	m = airport_pattern.match(airport)
	if m:
		return m.group(1)
	else:
		return airport

def format_aircraft(aircraft):
	if len(aircraft) <= 3:
		return aircraft
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
	elif not aircraft:
		return ''
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
	""" Class to hold all information about a single flight segment."""
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
		self.arrive_airport,self.arrive_date,self.arrive_time,self.aircraft,
		self.availability.strip()]
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

	def bucket_repr(self):
		if self.search_query:
			result_list = []
			for b in self.search_query:
				bucketname = remapped_classes[b] if b in remapped_classes else b
				basic_count = self.search_results[b]
				elite_count = self.search_results[b+'N'] if b in Nclasses and self.flightno[:2]=='UA' else ''
				result_list.append(bucketname+str(basic_count)+str(elite_count))
			return ' '.join(result_list)

			# return ' '.join([
			# 	(remapped_classes[b] if b in remapped_classes else b)+
			# 	str(self.search_results[b])+
			# 	(str(self.search_results[b+'N']) if b in Nclasses else '')
			#  for b in self.search_query])

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
			# look for elite availability on UA flights
			if b in Nclasses:
				invN = re.match('.*'+b+'N([0-9]).*',self.availability)
				if invN:
					results[b+'N'] = int(invN.group(1))
		self.search_results = results


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
