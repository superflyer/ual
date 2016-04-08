#!/usr/bin/env python
import os
import codecs
import sys
import argparse

from itertools import chain

from ual_session import * 
from ual_mileagerun import *


#redefine stdout/stderr to handle utf-8
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
		try:
			p = line.strip().split(':')
			config[p[0]] = p[1]
		except IndexError:
			# ignore malformed lines
			pass
	F.close()
	return config

def open_session(config, ua_only=False, logging=False, search_type=None):
	# open Session
	try:
		ses = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'],
			ua_only=ua_only, logging=logging, search_type=search_type)
	except Exception as e:
		subject = e.args[0]
		message = 'User: '+config['ual_user']
		send_email(subject,message,config)
		raise
	return ses


def send_aggregate_results(config, results=None, errors=None):
	subject = config['email_subject'] if config['email_subject'] else 'SuperFlyer search'
	if results:
		subject_results = subject + ' results'
		message_results = '\n'.join([seg.condensed_repr() for seg in sorted(results, key=lambda x: x.depart_datetime)])
		e = send_email(subject_results, message_results, config)
	else:
		e = 1
	if errors:
		subject_err = 'Errors in ' + subject
		message_err = '\n'.join([str(a)+': '+str(e) for a,e in errors])
		e1 = send_email(subject_err, message_err, config)
	else: 
		e1 = 0
	return (e, e1)


def run_alerts(config, filename='alerts/alert_defs.txt', aggregate=False, 
	ua_only=False, logging=False, search_type=None):
	"""If no output file is specified then send email to address specified in config.
	   If site_version is specified then the script will repeatedly log in until the specified site version is obtained
	   (up to max_retries times).
	"""

	ses = open_session(config, ua_only=ua_only, logging=logging, search_type=search_type)

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
				# if doing an aggregate search, copy the search definition for each day
				b = a.copy()
				b.depart_date = cur_datetime.strftime('%m/%d/%y')
				b.depart_datetime = cur_datetime
				alert_defs.append(b)
				cur_datetime += timedelta(1)
		except ValueError as e:
			stderr.write('Error parsing alert definition: '+line+ '  (' + str(e) + ')\n')
			continue			
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
			try:
				print(seg.condensed_repr())
			except:
				print(seg)
				stderr.write('Error getting string representation of segment.\n')
				continue
			if seg.search_results and max(seg.search_results.values()) > 0:
				results.append(seg)
				if not aggregate:
					subject = config['email_subject'] if config['email_subject'] else 'Results for '+str(a)
					message = 'Query: '+str(a)+'\nResults: '+seg.condensed_repr()
					send_email(subject,message,config)

	if aggregate:
		e, e1 = send_aggregate_results(config, results, errors)

	return(ses)


def run_mr_search(config, filename='alerts/mr_searches.txt', logging=False, search_type=None):
	"""Performs a mileage run search using parameters specified in the given file."""
	ses = open_session(config, ua_only=True, logging=logging, search_type=search_type)
	mr_searches = parse_mr_file(filename)
	print datetime.today().strftime('%c')
	for m in mr_searches:
		config['email_subject'] = m.name + ' mileage run search'
		results, errors = m.search(ses)
		e, e1 = send_aggregate_results(config, results, errors)
	return(ses)


def ual(logging=False):
	"""quickly load a session for debugging purposes"""
	config = configure('../ual.config')
	S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'],logging=logging)
	return S


if __name__=='__main__':

	argparser = argparse.ArgumentParser(description='Search united.com for flight availability.')

	# delivery methods
	search_type = argparser.add_mutually_exclusive_group()
	search_type.add_argument("-a", action="store_true", help="search on date range and aggregate results")
	search_type.add_argument("-m", action="store_true", help="mileage run search")

	# optional arguments
	argparser.add_argument("-v", action="store_true", help="verbose output with response logging")
	argparser.add_argument("-u", action="store_true", help="search for United-operated flights only")
	argparser.add_argument("-o", metavar="output_file", type=str, help="filename to store results")
	argparser.add_argument('-s', metavar="email_subject", type=str, help="subject to be sent in emails")

	# delivery methods
	recipient = argparser.add_mutually_exclusive_group()
	recipient.add_argument("-t", action="store_true", help="send text message instead of email")
	recipient.add_argument("-e", metavar="email_address", type=str, help="email address to send results to")

	# site version
	version = argparser.add_mutually_exclusive_group()
	version.add_argument('--force_old_site', action='store_true')
	version.add_argument('--force_new_site', action='store_true')

	# search for award or upgrades only
	ual_search_type = argparser.add_mutually_exclusive_group()
	ual_search_type.add_argument('--upgrade', action='store_true')
	ual_search_type.add_argument('--award', action='store_true')

	#positional arguments
	argparser.add_argument('-c', metavar="config_file", default="ual.config", type=str, help="filename containing configuration parameters (default: ual.config)")
	argparser.add_argument('alert_file', nargs='?', type=str, help='file containing alert definitions')	# metavar='file',

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

	# set logging
	if args.v:
		logging=True
	else:
		logging=False

	# set ua-only flag:
	if args.u:
		ua_only=True
	else:
		ua_only=False

	# configure the site version
	if args.force_old_site:
		site_version = "Old"
	elif args.force_new_site:
		site_version = "New"
	else:
		site_version = None

	# Use when looking for partner awards or when expert mode is broken
	if args.upgrade:
		ual_search_type = 'Upgrade'
	elif args.award:
		ual_search_type = 'Award'
	else:
		ual_search_type = None

	# run the alerts
	if args.alert_file:
		if args.a:
			S = run_alerts(config, filename=args.alert_file, aggregate=True,
				ua_only=ua_only, logging=logging, search_type=ual_search_type)
		elif args.m:
			S = run_mr_search(config, filename=args.alert_file, logging=logging, 
				search_type=ual_search_type)
		else:
			S = run_alerts(config, filename=args.alert_file,
				ua_only=ua_only, logging=logging, search_type=ual_search_type)
	else:
		S = run_alerts(config, ua_only=ua_only, logging=logging, search_type=ual_search_type)




