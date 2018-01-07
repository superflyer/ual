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
remapped_classes = {'1':'HN', '2':'PN'}
min_avail = 'FJY'
award_buckets = 'OIRX'
#bucket_regex = re.compile(', '.join([c+'[0-9]' for c in Yclasses]))
bucket_regex = re.compile(', '.join(['[A-Z][0-9]']*10))
max_days_out = 337  #maximum number of days out to search

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


def send_email(subject, message, config):
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
		self.availability = ['NA']
		self.flightno = None
		self.search_results = None
		self.search_query = None
		self.search_datetime = None
	def __repr__(self):
		paramlist=[self.flightno,self.depart_date,self.depart_airport,self.depart_time,
		self.arrive_airport,self.arrive_date,self.arrive_time,self.aircraft,
		' '.join(self.availability)]
		return(' '.join(paramlist))
	def __str__(self):
		return self.__repr__()
	def format_deptime(self):
		self.depart_datetime = parser.parse(self.depart_date+' '+self.depart_time)
		if self.depart_datetime.day == self.search_datetime.day:
			self.depart_offset = ''
		else:
			self.depart_offset = '+' + str((self.depart_datetime - self.search_datetime).days)

#		return self.depart_datetime.strftime('%m/%d/%y %H:%M')

	def format_arrtime(self):
		self.arrive_datetime = parser.parse(self.arrive_date+' '+self.arrive_time)
		if self.depart_date:
			if self.arrive_datetime.day == self.search_datetime.day:
				self.arrive_offset = ''
			elif (self.arrive_datetime - self.search_datetime).days > 0:
				self.arrive_offset = '+' + str((self.arrive_datetime - self.search_datetime).days)
			elif (self.arrive_datetime - self.search_datetime).days < 0:
				self.arrive_offset = str((self.arrive_datetime - self.search_datetime).days)

	def bucket_repr(self):
		if self.search_query:
			result_list = []
			for b in self.search_query:
				bucketname = remapped_classes[b] if b in remapped_classes else b
				basic_count = self.search_results[b]
				try:
					elite_count = self.search_results[b+'N'] if b in Nclasses and self.flightno[:2]=='UA' else ''
				except KeyError:
					elite_count = ''
				result_list.append(bucketname+str(basic_count)+str(elite_count))
			return ' '.join(result_list)

			# return ' '.join([
			# 	(remapped_classes[b] if b in remapped_classes else b)+
			# 	str(self.search_results[b])+
			# 	(str(self.search_results[b+'N']) if b in Nclasses else '')
			#  for b in self.search_query])

#		elif self.search_query=='':
#			return 'NA'
		else:
			return ' '.join(self.availability)

	def condensed_repr(self):
		self.format_deptime()
		self.format_arrtime()
		output_params = [self.search_datetime.strftime('%a'),
			self.search_datetime.strftime('%m/%d/%y').strip('0'),
			self.flightno,
			format_airport(self.depart_airport),
			self.depart_datetime.strftime('%H:%M')+self.depart_offset,
			format_airport(self.arrive_airport),
			self.arrive_datetime.strftime('%H:%M')+self.arrive_offset,
			format_aircraft(self.aircraft),
			self.bucket_repr()]
		return ' '.join(output_params)

	def search_buckets(self,buckets=None):
		self.search_query = ''
		if buckets:
			results = {}
			for b in buckets.upper():
				bucket_code = remapped_classes[b] if b in remapped_classes else b
				found_classes = [c[:-1] for c in self.availability]
				try:
					results[b] = int(self.availability[found_classes.index(bucket_code)][-1])
					if b in Nclasses:  			# look for elite availability on UA flights
						results[b+'N'] = int(self.availability[found_classes.index(bucket_code+'N')][-1])
					self.search_query += b
				except ValueError:
					# no result found
					pass
		else:
			results = {x[:-1] : int(x[-1]) for x in self.availability}
		self.search_results = results


class alert_params(object):
	def __init__(self, depart_date, depart_airport, arrive_airport, flightno=None, buckets=None,
			nonstop=False, award=False, cookies=None):
		self.depart_airport=depart_airport.upper()
		self.arrive_airport=arrive_airport.upper()
		self.buckets=buckets.upper() if buckets else ''
		self.flightno=flightno
		# need to do some error-checking on dates
		self.depart_datetime = parser.parse(depart_date)  # assume h:mm = 0:00
		if self.depart_datetime + timedelta(days=1,minutes=-1) < datetime.today() :
			raise ValueError('Depart date is in the past.')
		if self.depart_datetime > datetime.today() + timedelta(days=max_days_out):
			raise ValueError('Depart date is more than %s days in the future.' % max_days_out)
		self.depart_date=depart_date
		self.nonstop=nonstop
		self.award=award
		self.cookies=cookies
	def __repr__(self):
		return ' '.join([self.depart_date,
			self.flightno if self.flightno else '',
			self.depart_airport,
			self.arrive_airport,
			self.buckets if self.buckets else '',
			'NS' if self.nonstop else '',
			'Award' if self.award else ''])
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
