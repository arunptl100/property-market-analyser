import xml.etree.ElementTree as ET
from collections import defaultdict
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
import csv
from math import cos, asin, sqrt, pi

# False = Use a raw xml dump for testing purposes
# True  = Use live api requests
live = False
# False = Code ran once
# True = Code ran every interval
repeat = False
# Zoopla API details
api_token = 'kwgn93rerntytt8e5zy5zf84'
api_url_base = 'https://api.zoopla.co.uk/api/v1/'
parameters = {'api_key': api_token}
url = api_url_base + 'property_listings'


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
                self.attributes[child.tag] = child.text
        # compute the properties score based on preferences
        # self.get_stations_near_property(1)
        for pref in preferences:
            if pref == 'num_bedrooms':
                # formula: |-Actual-Preference|
                self.score += abs(-int(self.attributes['num_bedrooms'])-int(preferences['num_bedrooms']))
            elif pref == 'num_bathrooms':
                self.score += abs(-int(self.attributes['num_bathrooms'])-int(preferences['num_bathrooms']))
            elif pref == 'budget':
                # formula: -((price - budget)/100000)
                self.score += -(((int(self.attributes['price'])) - int(preferences['budget']))/100000)
            elif pref == 'property_type':
                # if the type of property matches the preferered type then add
                # 10 to the score
                if self.attributes['property_type'] == preferences['property_type']:
                    self.score += 10
            # update score based on stations nearby the property
        self.get_stations_near_property(preferences)

    # function returning the distance between 2 latitude longitude points
    # in miles
    # src: https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
    def compute_distance(self, lat1, lon1, lat2, lon2):
        p = pi/180
        a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
        return (12742 * asin(sqrt(a)))*0.621371

    # Functin returning a list of stations within
    # a set distance from the property
    # Uses the dataset in resources/Stops.csv
    # https://data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/national-public-transport-access-nodes-naptan
    def get_stations_near_property(self, preferences):
        stations_in_range = []
        p_lon = self.attributes['longitude']
        p_lat = self.attributes['latitude']
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
                    dist = self.compute_distance(float(p_lat), float(p_lon), float(s_lat), float(s_lon))
                    if dist <= float(preferences['dist_to_station']):
                        stations_in_range.append(row[4])
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
        self.sort_properties()
        print("==========================================================")
        for property in self.properties:
            property.print()
            print("==========================================================")

    # prints a summary of a property sourced from zoopla
    # the keys used a specific to zoopla API responses
    def print_summary_zoopla(self):
        self.sort_properties()
        print("==========================================================")
        for property in self.properties:
            print("Address : " + property.attributes['agent_address'])
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

    # sorts the property list based on the score of properties
    def sort_properties(self):
        self.properties.sort(key=lambda x: x.score)


executions = 0
interval = 1


def run():
    global executions
    parameters['area'] = 'Leamington Spa'
    parameters['page_size'] = '100'

    preferences = defaultdict(str)
    preferences['num_bedrooms'] = 4
    preferences['num_bathrooms'] = 2
    preferences['budget'] = 500000
    preferences['property_type'] = 'Detached house'
    preferences['dist_to_station'] = 1

    if live:
        response = requests.get(url=url, params=parameters)
        root = ET.fromstring(response.text)
    else:
        tree = ET.parse('response_dump.xml')
        root = tree.getroot()

    props = properties(preferences)
    for listing in root.iter("listing"):
        props.add_property_xml(listing)
    props.print_summary_zoopla()
    executions += 1
    if repeat:
        print("Checked ", executions, " times")
        print("Checking again in ", interval, " hour(s)\n\n\n")

try:
    run()
    if repeat:
        scheduler = BlockingScheduler()
        # seconds hours
        scheduler.add_job(run, 'interval', hours=1)
        # call run every interval
        scheduler.start()
except KeyboardInterrupt:
    # cleans up the console output on ctrl-c
    # by suppressing the exceptions output
    quit()

# test = property()
# print(test.compute_distance(52.2844903882, -1.5362099942, 52.304604, -1.528168))

# TODO:
#  - notification if best score so far is bested
#  - scrape data from savills etc for more data sources
