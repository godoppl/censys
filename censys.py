#!/usr/bin/env python

import os
import sys
import json
import requests

API_URL = "https://www.censys.io/api/v1"
argv = ['http', 'ftp', 'ssh'] # the accepted protocols to search for
results = ""
protocol = ""

try:
	UID = os.environ['censys_UID'] # Hidden in environment variable
	SECRET =  os.environ['censys_SECRET'] # Hidden in environment variable
except:
	print "Please export censys_UID and censys_SECRET to environment"
	sys.exit(1)



def helptext():				# just print the help text and quit
	print "\nPlease provide type of protocol to search for like this:"
	argv_ = len(argv)
	for i in range(0,len(argv)):
		if i == len(argv)-1:
			print "or"
		print sys.argv[0], argv[i]
	sys.exit(1)


def arg_parse():			# parse the arguments given and return error if no/false args
	global protocol
	try:
		if sys.argv[1] in argv:
			protocol = sys.argv[1]		# set global variable protocol to first argument
		else:
			do_nothing()
	except:
		helptext()


def search():				# query the database for the first 100 results of the selected protocol
	query = 'location.province:More AND location.country_code:NO AND tags:' + protocol
	page = 1
	query_ = '{"query":"' + query + '", "page":' + str(page) + ', "fields":["ip", "tags"]}'
	json_q = json.loads(query_) 
	res = requests.post(API_URL + "/search/ipv4", json=json_q, auth=(UID, SECRET))
	if res.status_code != 200:
		print "error occurred: %s" % res.json()["error"]
		sys.exit(1)
	results = res.json()['results']
	#for x in range(0,len(results)):
	for x in range(0,10):	
		get_content(results[x]['ip'])	# get the content for the frist [x] ip's

  
def get_content(ip_addr): # get the content associated with the ip
		global protocol
		res = requests.get(API_URL +  "/view/ipv4/" + ip_addr, auth=(UID, SECRET))
		if res.status_code != 200:
			print "error occurred: %s" % res.json()["error"]
			sys.exit(1)
		if protocol == 'http':
			get_http(res)
		if protocol == 'ftp':
			get_ftp(res)
		if protocol == 'ssh':
			get_ssh(res)


def get_http(res_):
	try:
		print res_.json()['ip'], ':', res_.json()['80']['http']['get']['title']
		print res_.json()['80']['http']['get']['body'][100]
	except:
		print 'NO TITLE'


def get_ftp(res_):
	try:
		print res_.json()['ip'], ':', res_.json()['21']['ftp']['banner']['banner']
	except:
		print 'NO TITLE'


def get_ssh(res_):
	try:
		print res_.json()['ip'], ':', res_.json()['22']['ssh']['banner']['raw_banner']
	except:
		print 'NO TITLE'

arg_parse() # parse the commandline arguments
search() # execute the search and output module