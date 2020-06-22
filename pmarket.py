import xml.etree.ElementTree as ET
import requests

api_token = 'kwgn93rerntytt8e5zy5zf84'
api_url_base = 'https://api.zoopla.co.uk/api/v1/'
parameters = {'api_key': api_token}


url = api_url_base + 'property_listings'
parameters['area'] = 'Leamington Spa'

# response = requests.get(url=url, params=parameters)
# print(response.text)
tree = ET.parse('response_dump.xml')
root = tree.getroot()
# root = ET.fromstring(response.text)
for listing in root.iter("listing"):
    for child in listing.iter("agent_address"):
        print(child.text)
