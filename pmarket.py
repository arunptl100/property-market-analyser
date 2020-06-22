import xml.etree.ElementTree as ET
import requests


# False = Use a raw xml dump for testing purposes
# True  = Use live api requests
live = False

# Zoopla API details
api_token = 'kwgn93rerntytt8e5zy5zf84'
api_url_base = 'https://api.zoopla.co.uk/api/v1/'
parameters = {'api_key': api_token}
url = api_url_base + 'property_listings'


class properties:
    def __init__(self):
        self.properties = []
        self.score = 0

    def addprop(self, xml_iter):
        self.properties.append(xml_iter)

    def print(self):
        print("==========================================================")
        for property in self.properties:
            for child in property:
                if child.tag == "agent_address":
                    print("Address : " + child.text)
                elif child.tag == "latitude":
                    print("Latitude : " + child.text)
                elif child.tag == "longitude":
                    print("Longitude : " + child.text)
                elif child.tag == "price":
                    print("Price : " + "£{:,.2f}".format(float(child.text)))
            print("Score : " + str(self.score))
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
    props.addprop(listing)

props.print()



# whitespace
