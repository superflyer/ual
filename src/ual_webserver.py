#!/usr/bin/env python

import argparse
import sys

from bottle import route, run, template, Bottle
from bottle import get, post, request
from bottle import static_file
from datetime import datetime, timedelta
from dateutil import parser
from re import search
from selenium.common.exceptions import UnexpectedAlertPresentException
from time import localtime, strftime

from ual import *
from ual_functions import format_aircraft

app = Bottle()

# web page defs
@app.route('/hello/:name')
def index(name='World'):
	print(name)
	return template('<b>Hello {{name}}</b>!', name=name)


#@app.route('/include/images/enhanced-mobile/<filename>')
@app.route('/static/<filename>')
def server_static(filename):
	return static_file(filename, root='static')


@app.route('/ual')
def query_form():
	if request.query.refine:
		q = request.query
		params = alert_params(q.depart_date,q.depart_airport,q.arrive_airport,
			q.buckets,nonstop=q.nonstop,award=q.award)
		print(params)
	else:
		params = None
	return template("templates/query", today=datetime.today(), params=params)


@app.route('/searchresults', method='POST')
def query_submit():
	global S
	global ual_search_type

	if not S:
		config = configure(args.c)
		S = open_session(config, search_type=search_type, logging=args.d, debug=args.d)

	depart_airport = request.forms.get('departAirport')
	arrive_airport = request.forms.get('arriveAirport')
	depart_month = request.forms.get('departMonth')
	depart_day = request.forms.get('departDay')
	depart_year = request.forms.get('departYear')
	class_codeO = request.forms.get('classCodeO')
	class_codeI = request.forms.get('classCodeI')
	class_codeR = request.forms.get('classCodeR')
	class_codeX = request.forms.get('classCodeX')
	other = request.forms.get('otherCheck')
	other_codes = request.forms.get('otherClassCodes')
	all_classes = request.forms.get('allClasses')
	nonstop = request.forms.get('nonstop')
	award = request.forms.get('award')

	# add the correct year to the departure date
	if int(depart_month) > date.today().month or \
		int(depart_month) == date.today().month and int(depart_day) >= date.today().day:
		depart_year = str(date.today().year)
	else:
		depart_year = str(date.today().year + 1)
	depart_date = '/'.join([depart_month, depart_day, depart_year])

	# parse date and check it's not too far out
	try:
		if parser.parse(depart_date) > datetime.today() + timedelta(days=max_days_out):
			return template("templates/error",err='Depart date is more than %s days in the future.' % max_days_out)
	except ValueError as e:
		return template("templates/error",err='Error parsing date: '+str(e))

	buckets = ''
	if not all_classes:
		for b in [class_codeO,class_codeI,class_codeR,class_codeX]:
			if b:
				buckets += b
		if other:
			buckets += other_codes

	print(depart_airport, arrive_airport, depart_month, depart_day, depart_year,
		buckets, other_codes, all_classes, nonstop, award)

	flightno = None

	params = alert_params(depart_date,depart_airport,arrive_airport,flightno,
		buckets,nonstop=nonstop,award=award)

	# last session timed out
	if S.browser.last_refresh_time < datetime.now() - timedelta(minutes=30):
		S.browser.get_startpage()

	# do the search
	try:
		result = S.basic_search(params)
	except UnexpectedAlertPresentException as e:
		stderr.write('Received alert: ' + str(e) + '\n')
		Alert(S.browser).accept()
		sleep(5)
		result = []

	# can't be sure that nonstop flag works
	if params.nonstop:
		result = [t for t in result if len(t)==1]
	sorted_result = sorted(result, key=lambda x: (len(x), x[0].depart_datetime))

	#logging
	sys.stdout.write(strftime("%Y-%m-%d %H:%M:%S", localtime())+'\n')
	sys.stdout.flush()

	# need to pass this function to the results template
	params.timedelta = timedelta

	try:
		S.browser.get_startpage(wait=False)
	except UnexpectedAlertPresentException as e:
		stderr.write('Received alert: ' + str(e) + '\n')
		Alert(S.browser).accept()
		sleep(5)

	return template("templates/results", params=params, data=sorted_result)


if __name__=='__main__':

	argparser = argparse.ArgumentParser(
		description='Web app to search united.com for flight availability.')
	argparser.add_argument("-l", action="store_true",
		help="run on localhost")
	argparser.add_argument("-d", action="store_true",
		help="run in debug mode")
	argparser.add_argument('-c', metavar="config_file", default="ual.config", type=str,
		help="filename containing configuration parameters (default: ual.config)")
	argparser.add_argument('-p', metavar="port", default="80", type=int,
		help="port on which to run web server (default: 80)")

	# search for award or upgrades only
	ual_search_type = argparser.add_mutually_exclusive_group()
	ual_search_type.add_argument('--noexpert', action='store_true')

	args = argparser.parse_args()

	# Use when looking for partner awards or when expert mode is broken; hold this in a global variable
	if args.noexpert:
		search_type = 'No-Expert'
	else:
		search_type = None

	debug = args.d

	# global variable to hold session
	config = configure(args.c)
	S = None
	if args.l:
		run(app, host='localhost', port=args.p, reloader=True)
	else:
		run(app, host='0.0.0.0', port=args.p)
