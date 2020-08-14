import xml.etree.ElementTree as ET
from collections import defaultdict

import config
import requests
import csv
import uuid
from math import cos, asin, sqrt, pi

# False = Use a raw xml dump for testing purposes
# True  = Use live api requests
live = True
# False = Code ran once
# True = Code ran every interval
repeat = True
# Zoopla API details
api_token = config.zoopla_api_token
api_url_base = 'https://api.zoopla.co.uk/api/v1/'
parameters = {'api_key': api_token}
url = api_url_base + 'property_listings'

executions = 0
interval = 1
global_prop_list = []
global_stops_list = []

# object storing details of a given station from the stops dataset
class station:
    def __init__(self, long, lat, name):
        self.long = long
        self.lat = lat
        self.name = name

class property:
    def __init__(self):
        # store attributes of a property in a dictionary
        self.attributes = defaultdict(str)
        self.near_stations = []
        self.score = 0

    # parses a property given in xml from Zoopla
    def parse_xml(self, listing, preferences):
        print("*Processing a property*")
        # parse an property given in XML
        for child in listing:
            if child.text is not None:
                # add the attribute and value to the properties attribute dictionary
                self.attributes[child.tag] = child.text
                # compute the properties score based on preferences
                if child.text == 'num_bedrooms':
                    # formula: |-Actual-Preference|
                    self.score += abs(-int(self.attributes['num_bedrooms'])-int(preferences['num_bedrooms']))
                elif child.text == 'num_bathrooms':
                    self.score += abs(-int(self.attributes['num_bathrooms'])-int(preferences['num_bathrooms']))
                elif child.text == 'budget':
                    # formula: -((price - budget)/100000)
                    self.score += -(((int(self.attributes['price'])) - int(preferences['budget']))/100000)
                elif child.text == 'property_type':
                    # if the type of property matches the preferered type then add
                    # 15 to the score
                    if self.attributes['property_type'] == preferences['property_type']:
                        self.score += 30
        # generate a unique ID for this property
        # we are taking properties from different sources, some info may not be
        # present from some sources so dont generate an id based on info from
        # the property
        self.attributes['uid'] = uuid.uuid4()
        # update score based on stations nearby the property
        self.get_stations_near_property(preferences)

    # function returning the distance between 2 latitude longitude points
    # in miles
    # src: https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
    def compute_distance(self, lat1, lon1, lat2, lon2):
        p = pi/180
        a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
        return (12742 * asin(sqrt(a)))*0.621371

    # Function returning a list of stations within
    # a set distance from the property
    # Uses the dataset in resources/Stops.csv
    # https://data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/national-public-transport-access-nodes-naptan
    # this is very slow - optimisation (parallelisation?)
    def get_stations_near_property(self, preferences):
        # first check that we've parsed the stations into memory as a list of
        # station objects
        # parsing is only done once - global_stops_list is a persistant global
        # variable
        if not global_stops_list:
            print("parsing stations...")
            # parse the csv file
            with open('resources/Stops.csv', 'r', encoding='mac_roman') as stops:
                reader = csv.reader(stops)
                iter_reader = iter(reader)
                next(iter_reader)
                for row in iter_reader:
                    # only consider stations that are railway stations
                    if row[31] == "RSE":
                        s_lon = row[29]
                        s_lat = row[30]
                        global_stops_list.append(station(s_lon, s_lat, row[4]))
        stations_in_range = []
        p_lon = self.attributes['longitude']
        p_lat = self.attributes['latitude']
        for stat in global_stops_list:
            dist = self.compute_distance(float(stat.lat), float(stat.long), float(p_lat), float(p_lon))
            if dist <= float(preferences['dist_to_station']):
                stations_in_range.append(stat.name)
                # add 10 to the properties score
                self.score += 10
        # now check for any duplicate stations in the list due to errors in the
        # dataset
        self.near_stations = stations_in_range

    def print(self):
        # get every attribute name for the property
        for att in self.attributes:
            if att == "price":
                print(att + " : " + "£{:,.2f}".format(float(self.attributes[att])))
            else:
                # retrieve the attributes value from the dictionary
                print(att + " : " + self.attributes[att])
        print("Score : " + str(self.score))


class properties:
    def __init__(self, preferences):
        self.properties = []
        self.preferences = preferences

    # adds a property to the list given an xml iter
    def add_property_xml(self, xml_iter):
        prop = property()
        prop.parse_xml(xml_iter, self.preferences)
        self.properties.append(prop)

    # Prints every stored attribute for the property
    def print_all(self):
        self.sort_properties(False)
        print("==========================================================")
        for property in self.properties:
            property.print()
            print("==========================================================")

    # prints a summary of a property sourced from zoopla
    # the keys used a specific to zoopla API responses
    def print_summary_zoopla(self):
        self.sort_properties(False)
        print("==========================================================")
        for property in self.properties:
            print("Address : " + property.attributes['displayable_address'])
            print("Type : " + property.attributes['property_type'])
            print("Longitude : " + property.attributes['longitude'])
            print("Latitude : " + property.attributes['latitude'])
            print("Bedrooms : " + property.attributes['num_bedrooms'])
            print("Bathrooms : " + property.attributes['num_bathrooms'])
            print("Price : " + "£{:,.2f}".format(float(property.attributes['price'])))
            # property.get_stations_near_property(self.preferences)
            print("Stations nearby ", property.near_stations)
            print("Score : " + str(round(property.score, 2)))
            print("==========================================================")

    def get_properties(self):
        self.sort_properties(True)
        # this returns an object containing a dictionary of attributes
        attr_list = []
        for prop in self.properties:
            # make the price pretty
            prop.attributes['price'] = "£{:,.2f}".format(float(prop.attributes['price']))
            # take the first and last part of the address
            addr = prop.attributes['agent_address'].split(",")
            prop.attributes['agent_address'] = addr[0] + ", " + addr[-1]
            # add the score to the attribute dictionary
            prop.attributes['score'] = prop.score
            attr_list.append(prop.attributes)
        return attr_list

    # sorts the property list based on the score of properties
    # returning -1 if the id does not exist
    def sort_properties(self, reverse):
        self.properties.sort(key=lambda x: x.score, reverse=reverse)


# function returning the property object for a given id
def get_property(id):
    for property in global_prop_list:
        if str(property['uid']).strip() == id.strip():
            return property
    return -1

# returns the global property list
# the list is populated with property objects after a call of do_work
def see_results():
    return global_prop_list


def do_work(area, beds, baths, budget, type, dist_train, interval):
    global executions
    print("Beginning a scan")
    parameters['area'] = area
    parameters['page_size'] = '100'

    preferences = defaultdict(str)
    preferences['num_bedrooms'] = beds
    preferences['num_bathrooms'] = baths
    preferences['budget'] = budget
    preferences['property_type'] = type
    preferences['dist_to_station'] = dist_train
    print("Processing the parameters: area: ", area, ", beds: ", beds, ", baths: ", baths, ", budget: ", budget, ", type: ", type, ", dist_train: ", dist_train)
    if live:
        response = requests.get(url=url, params=parameters)
        root = ET.fromstring(response.text)
    else:
        tree = ET.parse('response_dump.xml')
        root = tree.getroot()

    props = properties(preferences)
    for listing in root.iter("listing"):
        props.add_property_xml(listing)
    # props.print_summary_zoopla()

    executions += 1
    global global_prop_list
    global_prop_list = props.get_properties().copy()



# TODO:
#  - notification if best score so far is bested
#  - scrape data from savills etc for more data sources
