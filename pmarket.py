import xml.etree.ElementTree as ET
from collections import defaultdict
import requests
from apscheduler.schedulers.blocking import BlockingScheduler


# False = Use a raw xml dump for testing purposes
# True  = Use live api requests
live = False

# Zoopla API details
api_token = 'kwgn93rerntytt8e5zy5zf84'
api_url_base = 'https://api.zoopla.co.uk/api/v1/'
parameters = {'api_key': api_token}
url = api_url_base + 'property_listings'


class property:
    def __init__(self):
        # store attributes of a property in a dictionary
        self.attributes = defaultdict(str)
        self.score = 0

    def parse_xml(self, listing, preferences):
        # parse an property given in XML
        for child in listing:
            self.attributes[child.tag] = child.text
        # compute the properties score based on preferences
        for pref in preferences:
            if pref == 'num_bedrooms':
                # formula: |-Actual-Preference|
                self.score += abs(-int(self.attributes['num_bedrooms'])-int(preferences['num_bedrooms']))
            elif pref == 'num_bathrooms':
                self.score += abs(-int(self.attributes['num_bathrooms'])-int(preferences['num_bathrooms']))
            elif pref == 'budget':
                # formula: -((price - budget)/100000)
                self.score += -(((int(self.attributes['price'])) - int(preferences['budget']))/100000)

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
    def __init__(self):
        self.properties = []
        self.preferences = defaultdict(str)

    def add_preference(self, tag, pref):
        self.preferences[tag] = pref

    # adds a property to the list given an xml iter
    def add_property_xml(self, xml_iter, preferences):
        prop = property()
        prop.parse_xml(xml_iter, preferences)
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
            print("Longitude : " + property.attributes['longitude'])
            print("Latitude : " + property.attributes['latitude'])
            print("Bedrooms : " + property.attributes['num_bedrooms'])
            print("Bathrooms : " + property.attributes['num_bathrooms'])
            print("Price : " + "£{:,.2f}".format(float(property.attributes['price'])))
            print("Score : " + str(property.score))
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
    preferences['budget'] = 600000

    if live:
        response = requests.get(url=url, params=parameters)
        root = ET.fromstring(response.text)
    else:
        tree = ET.parse('response_dump.xml')
        root = tree.getroot()

    props = properties()
    for listing in root.iter("listing"):
        props.add_property_xml(listing, preferences)
    props.print_summary_zoopla()
    executions += 1
    print("Checked ", executions, " times")
    print("Checking again in ", interval, " hours\n\n\n")


run()
scheduler = BlockingScheduler()
# seconds hours
scheduler.add_job(run, 'interval', hours=1)
try:
    scheduler.start()
except KeyboardInterrupt:
    quit()
# whitespace
