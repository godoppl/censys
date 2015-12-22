#!/usr/bin/env python

import os
import sys
import json
import requests

API_URL = "https://www.censys.io/api/v1"
ftp = ['-f', '--ftp']  # the accepted protocol arguments
http = ['-h', '--http']
ssh = ['-s', '--ssh']
invalid_env = 0
protocol = []
num_results = 0 # defaults to no results printed (Just query server)
list_ips = 0 # If 1: print the list of IP's
view_data = 0 # If 1: print the data associated with the IP's
filename = ""

def helptext():				# just print the help text and quit
	print "usage: %s [-f] [-s] [-h] [-l] [-w filename] [integer]\n" % sys.argv[0]
	print "protocols: (multiple accepted)"
	print "--ftp (-f)	FTP (port 21)"
	print "--ssh (-s)	SSH (port 22)"
	print "--http (-h)	HTTP (port 80)\n"
	print "--list (-l)	Print list of IP's to stdout"
	print "--write (-w) [filename] will write output to file (optional)"
	print "[integer] is number of ip's to query(optional)"

	sys.exit(1)

def search(num_results_):	# query the database for number of results specified the selected protocol (or all if not specified)
	results = []
	pages = 1
	num_pages = 0
	if num_results_ >= 100:
		num_pages = (num_results_/100)
	for x in range(0,len(protocol)):		# For every protocol specified..
		for y in range(1,num_pages+2):		# And the number of results specified..
			if pages >= y:
				query_ = query(y,protocol[x])  # Query the server
				pages = query_[1]
				results = results + query_[0]

		if num_results_ > len(results):
			num_results_ = len(results)		# Make sure to keep within the number of results available

		if list_ips == 1:					# If specified, print the ip's to stdout
			for i in range(0,num_results_):
				print results[i]['ip']

		print "results returned: %i of type %s" % (num_results_, protocol[x])	# Status information to stdout

		for x in range(0,num_results_):  # Retrieve the content for the first [x] results to stdout
			content = get_content(results[x]['ip'])
			if len(filename) >= 1:
				# put content in file
			if view_data == 1:
				print content
									

		results = [] # Clean up results for this protocol
def query(page, protocol):
	query = 'location.province:More AND location.country_code:NO AND tags:' + protocol
	query_ = '{"query":"' + query + '", "page":' + str(page) + ', "fields":["ip", "tags"]}'
	json_q = json.loads(query_) 
	res = requests.post(API_URL + "/search/ipv4", json=json_q, auth=(UID, SECRET))
	if res.status_code != 200:
		print "error occurred: %s" % res.json()["error"]
		sys.exit(1)
	# print "This search revealed %s ip addresses" % res.json()['metadata']['count']
	results = res.json()['results']
	pages = res.json()['metadata']['pages']
	return [results, pages]

  
def get_content(ip_addr): # get the content associated with the ip # !!!!! Needs to return and not print!
	res = requests.get(API_URL +  "/view/ipv4/" + ip_addr, auth=(UID, SECRET))
	if res.status_code != 200:
		print "error occurred: %s" % res.json()["error"]
		sys.exit(1)
	if protocol == 'http': ## THIS DOES NOT WORK, THIS NEEDS TO BE A FOR LOOP
		content = get_http(res)
	if protocol == 'ftp': ## THIS DOES NOT WORK
		content = get_ftp(res)
	if protocol == 'ssh': ## THIS DOES NOT WORK
		content = get_ssh(res)
		

def get_http(res_): # !!!!! Needs to return and not print
	try:
		print res_.json()['ip'], ':', res_.json()['80']['http']['get']['title']
		print res_.json()['80']['http']['get']['body']
	except:
		print 'NO TITLE'


def get_ftp(res_):# !!!!! Needs to return and not print
	try:
		print res_.json()['ip'], ':', res_.json()['21']['ftp']['banner']['banner']
	except:
		print 'NO TITLE'


def get_ssh(res_):# !!!!! Needs to return and not print
	try:
		print res_.json()['ip'], ':', res_.json()['22']['ssh']['banner']['raw_banner']
	except:
		print 'NO TITLE'



try:
	UID = os.environ['censys_UID'] # Hidden in environment variable
	SECRET =  os.environ['censys_SECRET'] # Hidden in environment variable
except:
	print "Please export censys_UID and censys_SECRET to environment"
	sys.exit(1)


if len(sys.argv) == 1:		# Display help if no arguments 
	helptext()

for i in range(1,len(sys.argv)):	# Run through all the arguments 
	argument = sys.argv[i]
	if argument in ftp:
		protocol.append('ftp')
	elif argument in http:
		protocol.append('http')
	elif argument in ssh:
		protocol.append('ssh')
	elif argument == '-l' or argument == '--list':
		list_ips = 1
	elif argument == '-w' or argument == '--write':
		try:
			filename = sys.argv[i+1]		# Set the filename (must be right after --write (-w) argument)
			if filename[0] == '-':
				raise Exception('Not a filename, probably another flag')
		except:
			invalid_env = 1			
		print 'Will write output to %s' % filename
	else:							# If the argument is not a flag, maybe it is an integer?
		try:
			if int(argument) in range(1,10000):
				num_results = int(argument)
			if int(argument) == 0:
				print "You entered 0, will just search and not print any results"
			if int(argument) > 10000:
				print "Please don't try to display more than 10k results..."
		except:
			invalid_env = 1

if invalid_env == 1 or len(protocol) == 0:	# If something is wrong with the arguments, display helptext
		helptext()

search(num_results) # execute the search and output module
