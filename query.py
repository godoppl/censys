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



def query(page, protocols, city=None, province=None, country=None, search_text=None): #This needs to return all the pages in a array instead, to prevent all these duplicate searches
    #   query: Constructs the query and sends the request to the censys API
    #   Arguments:
    #       page: Number of pages to return (100 results per page)
    #       protocol: the protocol to request (ssh, ftp or http)
    #       city: return results from this city (Optional)
    #       province: return results from this province (Optional)
    #       country: return results from this country (Optional)
    connector = " AND "
    query_string = ""      # TODO make the query from arguments instead
    if UID == "" or SECRET == "":
        raise Exception("ERROR: No UID or SECRET given, can not make request\r\n\r\n")
    if city is not None:
        query_string +=  "location.city:" + city
    if province is not None:
        query_string += connector + "location.province:" + province
    if country is not None:
        query_string += connector + "location.country:" + country
    if search_text is not None:
        query_string += connector + search_text
    for protocol in protocols:
        query_string += connector + "tags: " + protocol
    json_query = json.loads('{"query":"' + query_string + '", "page":' + str(page) + ', "fields":["ip", "tags"]}')
    print "Query is:", query_string
    answer = raw_input("Save search query? [y/N]")  # TODO Set up input here, and save query to configuration file
    if answer == "y":
        with open('censys.conf', 'r+') as config_file:
            try:
                parser = configparser2.ConfigParser()
                parser.read_file(config_file)
                config_file.seek(0) # Seek back to start in case of writing to the config file
                try:
                    saved = parser.options('saved_searches')
                except:
                    parser.add_section('saved_searches')
                    saved = parser.options('saved_searches')
                parser['saved_searches'][str(len(saved))] = query_string
                parser.write(config_file)
            except Exception as e:
                print(e)
    res = requests.post(API_URL + "/search/ipv4", json=json_query, auth=(UID, SECRET))
    if res.status_code != 200:
        print "error occurred: %s" % res.json()["error"]
        sys.exit(1)
    return res



def detail(ip):
    #   detail: Return the details
    #   Arguments:
    #       ip: IPv4 address to get details about
    res = requests.get(API_URL +  "/view/ipv4/" + ip, auth=(UID, SECRET))
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
    return details.encode("utf8")
