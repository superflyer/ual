#!/usr/bin/python
import os
import codecs
import sys
import argparse

from datetime import datetime, timedelta
from itertools import chain
from random import random, shuffle
from time import sleep

from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.alert import Alert

from ual_selenium import *
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


def open_session(config, search_type=None, ua_only=False, logging=False, debug=False):
	# search_type parameter is ignored for now
	# open session in selenium and log in
	browser = ual_browser(search_type=search_type, 	headless=not debug,
		ua_only=ua_only, logging=logging, debug=debug)

	# pass the parameters into a requests session
	ses = ual_selenium_session(browser)
	return ses


def send_aggregate_results(config, results=None, errors=None):
	subject = config['email_subject'] if config['email_subject'] else 'SuperFlyer search'
	if results:
		subject_results = subject + ' results'
		message_results = '\n'.join([seg.condensed_repr() for seg in sorted(results, key=lambda x: x.depart_datetime)])
		e = send_email(subject_results, message_results, config)
	else:
		e = 1
	if errors and not config['suppress_errors']:
		subject_err = 'Errors in ' + subject
		message_err = '\n'.join([str(a)+': '+str(e) for a,e in errors])
		e1 = send_email(subject_err, message_err, config)
	else:
		e1 = 0
	return (e, e1)


def run_alerts(config, filename='alerts/alert_defs.txt', aggregate=False,
	ua_only=False, logging=False, search_type=None, debug=False):
	"""If no output file is specified then send email to address specified in config.
	"""

	# read alert defs
	with open(filename,'r') as F:
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

	print datetime.today().strftime('%c')
	results = []
	errors = []
	alert_delay = 1
	# shuffle(alert_defs)
	alert_defs.sort(key=lambda x: x.depart_date)

	#with
	ses = open_session(config, ua_only=ua_only, logging=logging,
		search_type=search_type, debug=debug)
	for a in alert_defs:
		# search for alerts
		try:
			print(a)
			segs = ses.alert_search(a)
			sleep(len(alert_defs)*random() + alert_delay)
			ses.browser.get_startpage()
		except UnexpectedAlertPresentException as e:
			stderr.write('Received alert: ' + str(e.alert_text) + '\n')
			Alert(ses.browser).accept()
			sleep(len(alert_defs)*random() + alert_delay)
			ses.browser.get_startpage()
			if alert_delay < 600:
				alert_delay *= 1.2
				alert_defs.append(a)
			continue
		except Exception as e:
			if aggregate:
				errors.append((a, str(e)))
			else:
				subject = 'Superflyer error'
				message = 'Query: ' + str(a) + '\nException: ' + str(e)
				stderr.write(subject+'\n'+message+'\n')
				if not config['suppress_errors']:
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


def run_mr_search(config, filename='alerts/mr_searches.txt', logging=False,
		search_type=None, debug=False):
	"""Performs a mileage run search using parameters specified in the given file."""
	ses = open_session(config, ua_only=True, logging=logging, search_type=search_type,
		debug=debug)
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
	argparser.add_argument("-d", action="store_true", help="debugging mode")
	argparser.add_argument("--suppress_errors", action="store_true", help="don't send error emails")

	# delivery methods
	recipient = argparser.add_mutually_exclusive_group()
	recipient.add_argument("-t", action="store_true", help="send text message instead of email")
	recipient.add_argument("-e", metavar="email_address", type=str, help="email address to send results to")

	#positional arguments
	argparser.add_argument('-c', metavar="config_file", default="ual.config", type=str, help="filename containing configuration parameters (default: ual.config)")
	argparser.add_argument('alert_file', nargs='?', type=str, help='file containing alert definitions')	# metavar='file',

	args = argparser.parse_args()


	config = configure(args.c)

	# configure to send text mesages
	if args.t: config['alert_recipient'] = config['sms_alerts']

	# configure custom email address
	if args.e: config['alert_recipient'] = args.e

	# configure output file
	config['output_file'] = args.o if args.o else None

	# configure email subject
	config['email_subject'] = args.s if args.s else None

	# suppress errors
	config['suppress_errors'] = args.suppress_errors

	# run the alerts
	alert_file = args.alert_file if args.alert_file else 'alerts/alert_defs.txt'
	if args.m:
		run_mr_search(config, filename=alert_file, logging=logging, debug=debug)
	else:
		run_alerts(config, filename=alert_file, aggregate=args.a,
			ua_only=args.u, logging=args.v, debug=args.d)




