#!/usr/bin/env python

default_min_connect_time = 60
default_max_connect_time = 720
default_buckets = 'R'

from dateutil import parser
from datetime import datetime, timedelta
from ual_functions import *
import sys


def parse_mr_file(filename):
	"""Read mileage run definitions and create an array of mr_search_params objects.

	mr block format:

	start_date	end_date	buckets*	min_connect_time*	max_connect_time*
	dep	arr	flightno*	optional*
	repeat above for each segment
	separate blocks with one or more * characters

	notes:
	 (*) means optional field
	 depart/arrive airports can be comma-separated
	 "optional" means search can return success even if this segment is not available;
	    availability on this segment will be reported if found.
	 search returns AND of all specified buckets
	"""

	search_strings = []
	cur_search_strings = []
	F = open(filename,'r')
	for line in F:
		if line[0] in '#\n':
			# skip comments and blank lines
			continue
		elif line[0] == '*':
			search_strings.append(cur_search_strings)
			cur_search_strings = []
		else:
			cur_search_strings.append(line.strip())
	F.close()
	if len(cur_search_strings) > 0:
		search_strings.append(cur_search_strings)

	searches = [mr_search_params(x) for x in search_strings]
	return searches


class mr_alert_params(alert_params):
	def __init__(self, depart_date, depart_airport, arrive_airport, flightno=None,
				buckets=default_buckets, nonstop=True, optional=False):
		super(mr_alert_params,self).__init__(depart_date, depart_airport, arrive_airport, flightno,
				buckets, nonstop)
		self.optional = optional
	def __repr__(self):
		return super(mr_alert_params,self).__repr__() + (' Opt' if self.optional else '')


class mr_search_params(object):
	"""Holds parameters for a single mileage run search
	   Parameters are given as an array of strings from the definitions file
	"""

	def __init__(self, text_params):
		"""assign global params and an array of search params"""
		self.strings = '\n'.join(text_params)

		# parse headerline
		headers = text_params[0].split('\t')
		self.name = headers[0]
		try:
			# set start date to the later of tomorrow or the given start date
			self.start_date = max([parser.parse(headers[1]), datetime.today() + timedelta(1)])
			self.end_date = min([parser.parse(headers[2]), 
				datetime.today() + timedelta(max_days_out)])
		except IndexError:
			raise IndexError('Malformed header in params file.')
		self.buckets = headers[3] if len(headers) > 3 else 'R'
		self.days = headers[4] if len(headers) > 4 else '1111111'
		self.min_connect_time = (int)(headers[5]) if len(headers) > 5 else default_min_connect_time
		self.max_connect_time = (int)(headers[6]) if len(headers) > 6 else default_max_connect_time

		# parse each search line
		self.searches = []
		for line in text_params[1:]:	
			text_data = line.split('\t')
			try:
				data = [str(self.start_date), 
						text_data[0], text_data[1], # depart/arrive airport
						text_data[3] if len(text_data) > 3 else None, # flight number
						self.buckets,
						True] # nonstop
			except IndexError:
				print text_data
				raise
			a = alert_params(*data)
			# set optional flag if any character is found in the 5th field
			a.optional = True if len(text_data) > 4 else False
			a.days_offset = (int)(text_data[2]) if len(text_data) > 2 and text_data[2] else 0
			self.searches.append(a)


	def __repr__(self):
		return ' '.join([str(self.start_date), str(self.end_date), self.buckets,
			str(self.min_connect_time), str(self.max_connect_time)]) + ' (' + \
			'; '.join([str(x).strip() for x in self.searches]) + ')'

	def search(self, ses):

		# iterate through search dates
		cur_date = self.start_date
		results = []
		num_required_results = len([x for x in self.searches if not x.optional])
		errors = []
		while cur_date <= self.end_date:
			if self.days[cur_date.weekday()] != '1':
				cur_date += timedelta(1)
				continue
			cur_date_results = []
			required_results_found = 0
			# search each flight and append results
			for a in self.searches:
				tmp_results = []
				b = a.copy()
				b.depart_date = (cur_date + timedelta(b.days_offset)).strftime('%m/%d/%y')
				b.depart_datetime = (cur_date + timedelta(b.days_offset))
				try:
					segs = ses.alert_search(b)
				except Exception as e:
					# report an error and go on to the next day
					errors.append((a,e.args[0]))
					break
				for seg in segs:
					try:
						print(seg.condensed_repr())
					except:
						print(seg)
						sys.stderr.write('Error getting string representation of segment.\n')
						continue
					if seg.search_results and min(seg.search_results.values()) > 0:
						tmp_results.append(seg)
				# if not optional and not found, abort
				if not a.optional and len(tmp_results) == 0:
					break
				if not a.optional and len(tmp_results) > 0:
					required_results_found += 1
				cur_date_results += tmp_results
			# if all results found, add to mr_results
			if required_results_found == num_required_results:
				results += cur_date_results

			cur_date += timedelta(1)

		return results, errors


