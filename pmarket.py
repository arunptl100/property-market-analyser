import xml.etree.ElementTree as ET
from collections import defaultdict
import requests


# False = Use a raw xml dump for testing purposes
# True  = Use live api requests
live = False

# Zoopla API details
api_token = 'kwgn93rerntytt8e5zy5zf84'
api_url_base = 'https://api.zoopla.co.uk/api/v1/'
parameters = {'api_key': api_token}
url = api_url_base + 'property_listings'


# use property objects storing attributes in a dictionary
# store a list of attributes for a property
# to print all attributes stored for a property
# iterate through attr list , giving key for the dictionary
class property:
    def __init__(self):
        # store attributes of a property in a dictionary
        self.attributes = defaultdict(str)
        # attr_list is a list of attribute names (keys for attributes dictiona)
        self.attr_list = []
        self.score = 0

    def parse_xml(self, listing):
        # parse an property given in XML
        for child in listing:
            self.attr_list.append(child.tag)
            self.attributes[child.tag] = child.text

    def print(self):
        # get every attribute name for the property
        for att in self.attr_list:
            if att == "price":
                print(att + " : " + "£{:,.2f}".format(float(self.attributes[att])))
            else:
                # retrieve the attributes value from the dictionary
                print(att + " : " + self.attributes[att])
        print("Score : " + str(self.score))


class properties:
    def __init__(self):
        self.properties = []

    # adds a property to the list given an xml iter
    def add_property_xml(self, xml_iter):
        prop = property()
        prop.parse_xml(xml_iter)
        self.properties.append(prop)

    # Prints every stored attribute for the property
    def print_all(self):
        print("==========================================================")
        for property in self.properties:
            property.print()
            print("==========================================================")

    # prints a summary of a property sourced from zoopla
    def print_summary_zoopla(self):
        print("==========================================================")
        for property in self.properties:
            print("Address : " + property.attributes['agent_address'])
            print("Longitude : " + property.attributes['longitude'])
            print("Latitude : " + property.attributes['latitude'])
            print("Price : " + "£{:,.2f}".format(float(property.attributes['price'])))
            print("Score : " + str(property.score))
            print("==========================================================")


parameters['area'] = 'Leamington Spa'
parameters['page_size'] = '100'

if live:
    response = requests.get(url=url, params=parameters)
    root = ET.fromstring(response.text)
else:
    tree = ET.parse('response_dump.xml')
    root = tree.getroot()

props = properties()
for listing in root.iter("listing"):
    props.add_property_xml(listing)

props.print_summary_zoopla()



# whitespace
