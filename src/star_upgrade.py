import argparse

from ual import *
#from ual_params import *

def star_upgrade(config,logging=False):
	"""Attempt to upgrade the *A itinerary referenced in config.  
	Config needs to have the following prameters for the reservation to be upgraded:
		upgrade_firstname, upgrade_lastname, upgrade_PNR, upgrade_airline, 
		upgrade_from, upgrade_to, upgrade_date, upgrade_flight, upgrade_class
	(upgrade_class is the current class booked)
	"""
	
	# open a session with united.com
	ses = ual_session(config['ual_user'],config['ual_pwd'],logging=logging,useragent=config['spoofUA'])

	# set post parameters from config
	upgrade_params = set_upgrade_params(ses.cookies['SID'])
	# upgrade_params['hdnAccountNumber'] = 'RV545571'
	# upgrade_params['hdnAccountNumberE'] = 'awFgN51P9moCfB0WlTuolQ%3d%3d'
	# upgrade_params['hdnCustomerId'] = '55803396'
	# upgrade_params['hdnAccountStatus'] = '4'
	# upgrade_params['ctl00$ContentInfo$ucFname1$txtFName'] = 'David'
	# upgrade_params['ctl00$ContentInfo$ucLname1$txtLName'] = 'Freeman'
	# upgrade_params['ctl00$ContentInfo$ucRecordLocator$txtPNR'] = '8N5DOE'
	# upgrade_params['ctl00$ContentInfo$ddlAirlines'] = 'SQ'
	# upgrade_params['ctl00$ContentInfo$ucOrigin1$txtOrigin'] = 'blr'
	# upgrade_params['ctl00$ContentInfo$ucDestination1$txtDestination'] = 'sin'
	# upgrade_params['ctl00$ContentInfo$ucDepartDate1$txtDptDate'] = '10/30/2015'
	# upgrade_params['ctl00$ContentInfo$ucFltnum1$txtFltNum'] = '503'
	# upgrade_params['ctl00$ContentInfo$ddlCabin1'] = 'Economy'
	# upgrade_params['ctl00$ContentInfo$ucEmail$txtEmail'] = 'dfreeman@cs.stanford.edu'

	# X = ses.upgrade(upgrade_params,logging=logging)

	# post the upgrade
	upgrade_page = ses.get('https://www.united.com/web/en-US/apps/reservation/flight/upgrade/sauaAwardUpgrade.aspx')
	upgrade = ses.post('https://www.united.com/web/en-US/apps/reservation/flight/upgrade/sauaAwardUpgrade.aspx',data=upgrade_params,allow_redirects=True,headers=ses.headers)
	print upgrade.status_code
	print upgrade.url
	if logging:
		F = codecs.open('response_logs/upgrade.html','w','utf-8')
		F.write(upgrade.text)
		F.close()
	return upgrade.text


def test():
	X = star_upgrade(config,logging=True)

if __name__=='__main__':

	argparser = argparse.ArgumentParser(description='Apply a Star Alliance upgrade to the itinerary in configs.')

	# optional arguments
	#argparser.add_argument("-a", action="store_true", help="search on date range and aggregate results")

	recipient = argparser.add_mutually_exclusive_group()
	recipient.add_argument("-t", action="store_true", help="send text message instead of email")
	recipient.add_argument("-e", metavar="email_address", type=str, help="email address to send results to")

	#positional arguments
	argparser.add_argument('-c', metavar="config_file", default="ual.config", type=str, help="filename containing configuration parameters (default: ual.config)")

	args = argparser.parse_args()

	config = configure(args.c)

	# configure to send text mesages
	if args.t:
		config['alert_recipient'] = config['sms_alerts']
	
	# configure custom email address
	if args.e:
		config['alert_recipient'] = args.e


