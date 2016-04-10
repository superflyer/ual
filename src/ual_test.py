#!/usr/bin/env python

from ual import *
import json

def test(num_tests=1, search_type=None):
	config = configure('../ual.config')
	results = []
	S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'],logging=True,
		search_type=search_type)
	Plist = [['12/20/16','SFO','EWR',True],
			 ['6/29/16','SFO','NRT',True],
			 ['5/17/16','ORD','MSP',True],
			 ['6/21/16','SFO','MSP',True],
			 ['2/22/16','SFO','FRA',True],
			 ['2/22/16','SFO','YUL',False],
			 ['5/22/16','IAD','DXB',False],
			 ['2/22/16','ORD','SFO',True],
			 ['2/22/16','SFO','SIN',False],
			 ['3/22/16','EWR','BOM',False],
			 ['3/22/16','EWR','BOM',True]]
	for i in range(min(num_tests,len(Plist))):
		P = alert_params(Plist[i][0],Plist[i][1],Plist[i][2],nonstop=Plist[i][3])
		S.search(P)
		S.extract_data()
		F = codecs.open('searches/data'+Plist[i][1]+Plist[i][2]+str(i),'w','utf-8')
		for trip in S.trips:
			for seg in trip:
				F.write(str(seg) + '\n')
		F.close()
		results.append(S.basic_search(P))
	return S

def scratch():
	x = X[0][0]
	print(x.condensed_repr())
	x.search_buckets('JIRYX')
	print(x.condensed_repr())

class foo(object):
	"""docstring for foo"""
	def __init__(self, arg):
		super(foo, self).__init__()
		self.text = arg	

def test_parsing(filename):
	config = configure('../ual.config')
	S = ual_session(config['ual_user'],config['ual_pwd'],logging=True)

	F = open(filename)
	S.search_results = foo(F.read())
	F.close()
	S.extract_data()

	return S.trips

def load_search_results(filename):
	F = open(filename)
	raw_json = F.read()
	F.close()
	data = json.loads(raw_json)
	return data

def mr_test(filename):
	config = configure('ual.config')
	P = parse_mr_file(filename)
	print P
	S = run_mr_search(config, filename)

if __name__ == '__main__':
	# mr_test('alerts/mr_searches.txt')
	X = test(search_type='Upgrade')
	Y = load_search_results('response_logs/search.html')
	# T = test_parsing('searches/SFOFRA1.json')