#!/usr/bin/env python

import sys
import os.path
#import json
import time
import query
import configparser2

parser = configparser2.ConfigParser()
invalid_env = False

def help():
    # help: Prints the helptext and quits
    print sys.argv[0] + ": Performs IPv4 searches in censys.io database for addresses and protocols"
    print "usage: %s [-f] [-s] [-h] [-d] [--country:] [--province:] [--city:] [--search:] [-w filename] [Integer]\r\n" % sys.argv[0]
    print "protocols: (multiple accepted)"
    print "--ftp (-f)	  FTP (port 21)"
    print "--ssh (-s)	  SSH (port 22)"
    print "--http (-h)	  HTTP (port 80)"
    print "--details (-d) Print details of services to stdout\r\n"

    print "--country:[Country]              eg. England, 'United States of America', Norway or similar"
    print "--province:[Province or County]  eg. California, Nordland"
    print "--city:[City]                    eg. London, Oslo, Austin"
    print "--search:[Search query]          Search for specific string in Banner, Title or Body of default response\r\n"

    print "--write (-w):[filename]          Write details of services to file (optional)"
    print "--write-list (-wl):[filename]    Only write list of IP's (Useful for importing to nmap or msf)"
    print "[Integer]                        Number of ip's to request (optional, default is 100, maximum is 10000)"

    exit()

def read_config():
    # read_config: Read the configuration file, and check if API Credentials are stored. If there are no API
    # Credentials stored, ask for those and store them in the configuration file if user accepts to do so

    if not os.path.isfile('censys.conf'):
        open('censys.conf', 'a').close()
    with open('censys.conf', 'r+') as config_file:
        parser.read_file(config_file)
        config_file.seek(0) # Seek back to start in case of writing to the config file
        try:
            query.auth(parser['authentication']['uid'], parser['authentication']['secret'])  # Initialize the query engine with credentials
        except:
            print "WARNING: No registered API Credentials!\nGet these from: https://censys.io/account"
            UID = raw_input('Please input censys UID: ')
            SECRET = raw_input('Please input censys SECRET: ')
            query.auth(UID, SECRET)  # Initialize the query engine with credentials
            answer = raw_input("Write API Credentials to config? [y/N]")
            if answer == "y":
                parser.add_section('authentication')
                parser['authentication']['UID'] = UID
                parser['authentication']['SECRET'] = SECRET
                parser.write(config_file)

def parse_args():
    num_results = 100
    protocol_array = []
    details = False
    listIP = False
    fileobject = None
    city = None
    province = None
    country = None
    search_text = None
    for i in range(1,len(sys.argv)):	# Run through all the arguments
        argument = sys.argv[i]
        if argument == '-f' or argument == '--ftp':
            protocol_array.append('ftp')
        elif argument == '-h' or argument == '--http':
            protocol_array.append('http')
        elif argument == '-s' or argument == '--ssh':
            protocol_array.append('ssh')
        elif argument[:9] == '--country':
            try:
                arg, country = argument.split(':')
                if country == "":
                    raise Exception("ERROR: Please provide a country code after --country argument\r\n\r\n")
            except Exception as e:
                print(e)
                help()
        elif argument[:10] == '--province':
            try:
                arg, province = argument.split(':')
                if province == "":
                    raise Exception("ERROR: Please provide a province after --province argument\r\n\r\n")
            except Exception as e:
                print(e)
                help()
        elif argument[:6] == '--city':
            try:
                arg, city = argument.split(':')
                if city == "":
                    raise Exception("ERROR: Please provide a city after --city argument\r\n\r\n")
            except Exception as e:
                print(e)
                help()
        elif argument[:8] == '--search':
            try:
                arg, search_text = argument.split(':')
                if search_text == "":
                    raise Exception("ERROR: Bad formatting of search query\r\n\r\n")
            except Exception as e:
                print(e)
                help()
        elif argument == '-d' or argument == '--details':
            details = True
        elif argument[:2] == '-w' or argument[:7] == '--write':
            try:
                arg, filename = argument.split(':')
            except:
                print("No filename given, will use current time as filename")
                arg = argument
                filename = ""
            listIP = (arg == "-wl" or arg == "--write-list")
            if filename == "":
                filename = time.strftime('%d_%b_%H_%M_%S.out')
            fileobject = open(filename, 'a')
        else:
            try:
                if int(argument) == 0:
                    help()
                elif int(argument) in range(1,10000):
                    num_results = int(argument)
                if int(argument) > 10000:
                    print("WARNING: Capping the query to 10k results...\r\n\r\n")
                    num_results = 10000
            except Exception as e:
                print(e)
                help()

    if len(protocol_array) == 0:
        print("ERROR: Please provide at least one protocol to search for\r\n\r\n")
        help()
    else:
        search(num_results, details, listIP, protocol_array, fileobject, city, province, country, search_text) # TODO Does not seem right to call this function from here...

#   search: Build the query from the arguments passed
#   Arguments:
#       num_results (int): The number of results to return
#       view_data (boolean): Print list to std_out?
#       details (boolean): Print details of each item in the list to std_out?
#       protocols (string array): What protocols to search for
#       output_file (file object): What file to write results to
def search(num_results, details, listIP, protocols, output_file, city=None, province=None, country=None, search_text=None):	# query the database for number of results specified the selected protocol (or all if not specified)
    results = []
    pages = 1
    num_pages = 0
    if num_results >= 100:
        num_pages = (num_results/100)		# TODO Reevaluate this solution, seems overly complicated

    # TODO We should return only results that have services responding on all selected protocols
    for y in range(1,num_pages+2):		# And the number of results specified..
        # TODO This should not be done with a for loop.... The query function should handle this instead
        if pages >= y:
            try:
                result = query.query(y, protocols, city, province, country, search_text)  # Query the server
            except Exception as e:
                print(e)
                help()
            pages = result.json()['metadata']['pages']
            results = results + result.json()['results']

    if num_results > len(results):
        num_results = len(results)		# This makes sure to keep within the number of results available

    for i in range(0,num_results):
        ip = results[i]['ip']
        if details or (output_file is not None and not listIP):
            content = query.detail(ip)
        if details:
            print(content)
        else:
            print(ip)
        if output_file is not None:
            if listIP:
                output_file.write(ip + " ")
            else:
                output_file.write(content + "\n")


if len(sys.argv) == 1: # Display help if no arguments
    help()
else:
    read_config() # Read the config file
    parse_args() # Go through the list of arguments and start the search

