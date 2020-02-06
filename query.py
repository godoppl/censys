import json
import requests
import sys
import configparser2

UID = ""
SECRET = ""
API_URL = "https://www.censys.io/api/v1"

def auth(_UID, _SECRET):
    #   auth: Authentication data for censys API access
    #   Arguments:
    #       _UID: API UID
    #
    global UID; UID = _UID
    global SECRET; SECRET = _SECRET

    #  TODO Do a validation of the credentials


def constructor(options):
    # constructor: put the options together into a query string
    #   Arguments:
    #      options: the search options
    #   Returns:
    #       string object with the complete search query

    connector = " AND "
    query_string = ""
    for option in options:
        query_string += option + connector
    return query_string[:-5]

def query(page, options): #This needs to return all the pages in a array instead, to prevent all these duplicate searches
    #   query: Constructs the query and sends the request to the censys API
    #   Arguments:
    #       page: Number of pages to return (100 results per page)
    #       options: the search options
    #   Returns:
    #       res object with the json result 

    query_string = constructor(options)
    if UID == "" or SECRET == "":
        raise Exception("ERROR: No UID or SECRET given, can not make request\r\n\r\n")
    json_query = json.loads('{"query":"' + query_string + '", "page":' + str(page) + ', "fields":["ip", "tags"]}')
    res = requests.post(API_URL + "/search/ipv4", json=json_query, auth=(UID, SECRET))
    if res.status_code != 200:
        print "error occurred: %s" % res.json()["error"]
        sys.exit(1)
    return res



def detail(ip):
    #   detail: Return the details
    #   Arguments:
    #       ip: IPv4 address to get details about
    #   Returns:
    #       multiline string with details (banners, titles) of services

    res = requests.get(API_URL +  "/view/ipv4/" + ip, auth=(UID, SECRET))
    try:
        details = "-"*60 + "\n\t\t" + str(res.json()['ip'])
        if res.status_code == 200:
            try:
                details += "\nHTTP Service Title:  " + res.json()['80']['http']['get']['title'] + "\nBody:\n" + res.json()['80']['http']['get']['body'][:300] + "\n"
            except:
                pass
            try:
                details += "\nFTP Banner:  " + res.json()['21']['ftp']['banner']['banner'] + "\n"
            except:
                pass
            try:
                details += "\nSSH Banner:  " + res.json()['22']['ssh']['banner']['raw_banner'] + "\n"
            except:
                pass
        else:
            details += "\n\t\tERROR: No data returned!"
    except:
        details = "\n\t\tERROR: No data returned!"
        pass
    return details.encode("utf8")

