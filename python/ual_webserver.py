#!/usr/bin/env python

from bottle import route, run, template
from bottle import get, post, request
from bottle import static_file
from time import localtime, strftime
from datetime import *
from dateutil import parser
import sys

from ual import *

# global variable to hold session
S = ual_session(ual_user,ual_pwd,useragent=spoofUA)

# web page defs
@route('/hello/:name')
def index(name='World'):
	print(name)
	return template('<b>Hello {{name}}</b>!', name=name)


@route('/include/images/enhanced-mobile/<filename>')
@route('/static/<filename>')
def server_static(filename):
	return static_file(filename, root='static')


@get('/ual') # or @route('/login')
def query_form():
    return template("query", today=datetime.today())

@post('/ual') # or @route('/login', method='POST')
def query_submit():
	global S

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
	if parser.parse(depart_date) + timedelta(days=1,minutes=-1) < datetime.today() :
		depart_date = depart_month + '/' + depart_day + '/' + str(date.today().year+1)
	if parser.parse(depart_date) > datetime.today() + timedelta(days=331):
		return template("error",err='Depart date is in the past or more than 331 days in the future.')

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

	params = alert_params(depart_date,depart_airport,arrive_airport,flightno,buckets,nonstop)
	if len(sys.argv) > 1 and sys.argv[1] == '-t':
		F = open('../international.html')
		raw_data = F.read()
		F.close()
		result = extract_data(raw_data)
	else:
		if S.last_login_time < datetime.now() - timedelta(minutes=30):
			S = ual_session(ual_user,ual_pwd,useragent=spoofUA)
		result = S.basic_search(params)

		
	#logging
	sys.stdout.write(strftime("%Y-%m-%d %H:%M:%S", localtime())+'\n')
	sys.stdout.flush()
	
	return template("results", params=params, data=result)

#run(host='dfreeman-md.linkedin.biz', port=8080)

if __name__=='__main__':
	run(host='localhost', port=8080)
