#!/usr/bin/env python

from bottle import route, run, template, Bottle
from bottle import get, post, request
from bottle import static_file
from time import localtime, strftime
from datetime import *
from dateutil import parser
from re import search
import sys
import argparse

from ual import *

app = Bottle()

# web page defs
@app.route('/hello/:name')
def index(name='World'):
	print(name)
	return template('<b>Hello {{name}}</b>!', name=name)


@app.route('/include/images/enhanced-mobile/<filename>')
@app.route('/static/<filename>')
def server_static(filename):
	return static_file(filename, root='static')


@app.route('/ual')
def query_form():
	if request.query.refine:
		q = request.query
		params = alert_params(q.depart_date,q.depart_airport,q.arrive_airport,q.flightno,q.buckets,nonstop=q.nonstop)
	else:
		params = None
	print(params)
	return template("templates/query", today=datetime.today(), params=params)

@app.route('/searchresults', method='POST')
def query_submit():
	global S
	global site_version, max_retries

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
	airline = request.forms.get('airlineCode')
	flightno = request.forms.get('flightNumber')
	nonstop = request.forms.get('nonstop')

	depart_date = depart_month + '/' + depart_day + '/' + str(date.today().year)
	try:
		if parser.parse(depart_date) + timedelta(days=1,minutes=-1) < datetime.today() :
			depart_date = depart_month + '/' + depart_day + '/' + str(date.today().year+1)
		if parser.parse(depart_date) > datetime.today() + timedelta(days=331):
			return template("templates/error",err='Depart date is in the past or more than 331 days in the future.')
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
		buckets, other_codes, all_classes, airline, flightno, nonstop)

	flightno = airline + flightno

	params = alert_params(depart_date,depart_airport,arrive_airport,flightno,buckets,nonstop=nonstop)
	if args.t: 
		# testing mode
		F = open('ual_test/international.html')
		raw_data = F.read()
		F.close()
		# need to mock up a session
		result = extract_data(raw_data)
		for trip in result:
			for seg in trip:
				seg.format_deptime()
				seg.format_arrtime()
				if params.buckets:
					seg.search_buckets(params.buckets)
	else:
		if S.last_login_time < datetime.now() - timedelta(minutes=30):
			config = configure(args.c)
			for i in range(max_retries):
				S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'])
				if not site_version or S.site_version == site_version:
					break
		result = S.basic_search(params)
		# can't be sure that nonstop flag works
		if params.nonstop:
			result = [t for t in result if len(t)==1]
		sorted_result = sorted(result, key=lambda x: (len(x), x[0].depart_datetime))

		
	#logging
	sys.stdout.write(strftime("%Y-%m-%d %H:%M:%S", localtime())+'\n')
	sys.stdout.flush()
	
	return template("templates/results", params=params, data=sorted_result)

if __name__=='__main__':

	argparser = argparse.ArgumentParser(description='Web app to search united.com for flight availability.')
	argparser.add_argument("-l", action="store_true", help="run on localhost")
	argparser.add_argument("-t", action="store_true", help="run in testing mode")
	argparser.add_argument('-c', metavar="config_file", default="ual.config", type=str, help="filename containing configuration parameters (default: ual.config)")
	argparser.add_argument('-p', metavar="port", default="80", type=int, help="port on which to run web server (default: 80)")

	# site version
	version = argparser.add_mutually_exclusive_group()
	version.add_argument('--force_old_site', action='store_true')
	version.add_argument('--force_new_site', action='store_true')

	args = argparser.parse_args()

	# configure the site version, hold it in a global variable
	if args.force_old_site:
		site_version = "Old"
	elif args.force_new_site:
		site_version = "New"
	else:
		site_version = None

	# global variable to hold session
	max_retries = 10
	if not args.t:
		config = configure(args.c)
		for i in range(max_retries):
			S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'])
			if not site_version or S.site_version == site_version:
				break

	if args.l:
		run(app, host='localhost', port=args.p, reloader=True)
	else:
		run(app, host='0.0.0.0', port=args.p)
