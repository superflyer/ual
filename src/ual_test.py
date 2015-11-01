from ual import *

def test(num_tests=1):
	config = configure('../ual.config')
	S = ual_session(config['ual_user'],config['ual_pwd'],useragent=config['spoofUA'],logging=True)
	Plist = [['2/22/16','OGG','SFO',True],
			 ['2/22/16','SFO','FRA',True],
			 ['2/22/16','SFO','YUL',False],
			 ['5/22/16','IAD','DXB',False],
			 ['2/22/16','ORD','SFO',True],
			 ['2/22/16','SFO','SIN',False],
			 ['3/22/16','EWR','BOM',False],
			 ['3/22/16','EWR','BOM',True]]
	for i in range(min(num_tests,len(Plist))):
		P = alert_params(Plist[i][0],Plist[i][1],Plist[i][2],nonstop=Plist[i][3])
		S.search(P,logging=True)
		S.extract_data()
		F = codecs.open('searches/data'+Plist[i][1]+Plist[i][2]+str(i),'w','utf-8')
		F.write(S.trips)
		F.close()
	#X = S.basic_search(P)
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

if __name__ == '__main__':
	pass
	T = test_parsing('searches/SFOFRA1.json')