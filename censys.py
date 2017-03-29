#!/usr/bin/env python

import os
import sys
import json
import requests
import configparser2

parser = configparser2.ConfigParser()

API_URL = "https://www.censys.io/api/v1"
invalid_env = False
protocol_array = []
filename = ""
country = ""
province = ""
city = ""
search_text = ""

def helptext():				# just print the help text and quit
    print "usage: %s [-f] [-s] [-h] [-l] [-v] [-w filename] [-n results]\r\n" % sys.argv[0]
    print "protocols: (multiple accepted)"
    print "--ftp (-f)	FTP (port 21)"
    print "--ssh (-s)	SSH (port 22)"
    print "--http (-h)	HTTP (port 80)\r\n"
    print "COMING SOON: " + "--country [Country code] eg. GB, US, NO or similar"
    print "COMING SOON: " + "--province [Province or County] eg. California, Nordland"
    print "COMING SOON: " + "--city [City] eg. London, Oslo, Austin"
    print "COMING SOON: " + "--search [Search query]\r\n"
    print "--list (-l)	Print list of IP's to stdout"
    print "--view (-v)	Print details of services to stdout"
    print "--write (-w) [filename] will write output to file (optional)"
    print "-n [integer] is number of ip's to request details(optional)"

    sys.exit(1)

def search(num_results, view_data, list_ips, protocols, output_file):	# query the database for number of results specified the selected protocol (or all if not specified)
    results = []
    pages = 1
    num_pages = 0
    if num_results >= 100:
        num_pages = (num_results/100)		# TODO Reevaluate this solution, seems overly complicated

    for protocol in protocols:		# For every protocol specified..
        for y in range(1,num_pages+2):		# And the number of results specified..
            if pages >= y:
                result = query(y, protocol)  # Query the server
                pages = result[1]
                results = results + result[0]

        if num_results > len(results):
            num_results = len(results)		# Make sure to keep within the number of results available

        if list_ips:					# If specified, print the ip's to stdout
            for i in range(0,num_results):
                print results[i]['ip']

        print "results returned: %i of type %s" % (num_results, protocol)	# Status information to stdout

        if (output_file is not None or view_data):
            for y in range(0,num_results):  # Retrieve the content for the first [x] results to stdout
                content = get_content(results[y]['ip'], protocol)
                if len(filename) > 0:
                    f.write(content)
                if view_data:
                    print content

        results = [] # Clean up results for this protocol

def query(page, protocol):
    query_string = 'location.province:More AND location.country_code:NO AND tags:' + protocol      # TODO make the query from arguments instead
    json_query = json.loads('{"query":"' + query_string + '", "page":' + str(page) + ', "fields":["ip", "tags"]}')
    res = requests.post(API_URL + "/search/ipv4", json=json_query, auth=(UID, SECRET))
    if res.status_code != 200:
        print "error occurred: %s" % res.json()["error"]
        sys.exit(1)
    # print "This search revealed %s ip addresses" % res.json()['metadata']['count']
    results = res.json()['results']
    pages = res.json()['metadata']['pages']
    return [results, pages]

def get_content(ip, protocol): # get the content associated with the ip and protocol
    details = ""
    res = requests.get(API_URL +  "/view/ipv4/" + ip, auth=(UID, SECRET))
    if res.status_code != 200:
        print "Nothing returned on IP: " + ip
    if protocol == "http":
        try:
            details = str(res.json()['ip']) + "\n" + res.json()['80']['http']['get']['title'] + "\n" + res.json()['80']['http']['get']['body'][300] + "\n"
        except:
            details = ip + ": NO TITLE\n"

    if protocol == "ftp":
        try:
            details = str(res.json()['ip']) + "\n" + res.json()['21']['ftp']['banner']['banner']
        except:
            details = ip + ": NO TITLE\n"

    if protocol == "ssh":
        try:
            details = str(res.json()['ip']) +  "		" + res.json()['22']['ssh']['banner']['raw_banner']
        except:
            details = ip + ": NO TITLE\n"

    return details.encode("utf8")

def read_config():
    try:
        config_file = open('censys.conf', 'r+')
        parser.read_file(config_file)
        # TODO If ['authentication'] does not exist or the uid and secret options are not present, we need to ask for this information
    except Exception as e:
        print(e)

    global UID
    global SECRET
    ## Check for authentication and set variables
    UID = parser['authentication']['uid']
    SECRET = parser['authentication']['secret']
    return parser

def parse_args():
    view_data = False
    list_ips = False
    num_results = 0
    f = None
    for i in range(1,len(sys.argv)):	# Run through all the arguments
        argument = sys.argv[i]
        if argument == '-f' or argument == '--ftp':
            protocol_array.append('ftp')
        elif argument == '-h' or argument == '--http':
            protocol_array.append('http')
        elif argument == '-s' or argument == '--ssh':
            protocol_array.append('ssh')
        # elif argument == '--country':
        #     try:
        #         country = sys.argv[i + 1]
        #         if country[0] == '-': #TODO make an array of accepted country codes and match for correctness
        #             raise Exception("ERROR: Please provide a country code after --country argument\r\n\r\n")
        #     except Exception as e:
        #         print(e)
        #         helptext()
        # elif argument == '--province':
        #     try:
        #         province = sys.argv[i + 1]
        #         if province[0] == '-':
        #             raise Exception("ERROR: Please provide a province after --province argument\r\n\r\n")
        #     except Exception as e:
        #         print(e)
        #         helptext()
        # elif argument == '--city':
        #     try:
        #         city = sys.argv[i + 1]
        #         if city[0] == '-':
        #             raise Exception("ERROR: Please provide a city after --city argument\r\n\r\n")
        #     except Exception as e:
        #         print(e)
        #         helptext()
        # elif argument == '--search':
        #     try:
        #         search_text = sys.argv[i + 1]
        #         if search_text[0] == '-':
        #             raise Exception("ERROR: Bad formatting of search query\r\n\r\n")
        #     except Exception as e:
        #         print(e)
        #         helptext()
        #     finally:
        #         print("Save search query?") # TODO Set up input here, and save query to configuration file
        elif argument == '-l' or '--list':
            list_ips = True
        elif argument == '-v' or argument == '--view':
            view_data = True
        elif argument == '-w' or argument == '--write':
            try:
                filename = sys.argv[i+1]		# Set the filename (must be right after --write (-w) argument)
                if filename[0] == '-':
                    raise Exception("ERROR: Not a filename, probably another flag\r\n\r\n")
                else:
                    print 'Will write output to %s' % filename
                    f = open(filename, 'a')
            except Exception as e:
                print("{}\r\n\r\n".format(e))
                helptext()
        else:							# If the argument is not a flag, maybe it is an integer?
            try:
                if int(argument) == 0:
                    print "You entered 0, will just search and not print any results"
                elif int(argument) in range(1,10000):
                    num_results = int(argument)
                if int(argument) > 10000:
                    raise Exception("ERROR: Please don't try to display more than 10k results...\r\n\r\n")
            except Exception as e:
                print(e)
                helptext()

        if len(protocol_array) == 0:
            print("Please provide at least one protocol to search for\r\n\r\n")
            helptext()
        else:
            search(num_results, view_data, list_ips, protocol_array, f)

config = read_config()

if len(sys.argv) == 1:		# Display help if no arguments
    helptext()
else:
    parse_args()

# search(num_results) # execute the search and output module
