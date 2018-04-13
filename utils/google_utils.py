"""
Functions for getting attributes about points of interest.
Extracts data from POI locations (elevation, safety, etc.)

Uses: Google Place Search

Uses the python-google-places wrapper:
https://github.com/slimkrazy/python-google-places
"""

from googleplaces import GooglePlaces, types, lang
from configparser import ConfigParser
from uszipcode import ZipcodeSearchEngine
import json

config = ConfigParser()
config.read('./config.ini')
GOOGLE_API_KEY = config.get('auth', 'GOOGLE_API_KEY')
google_places = GooglePlaces(GOOGLE_API_KEY)

def zipcode_to_latlong(zipcode):
	search = ZipcodeSearchEngine()
	loc_data = search.byzipcode(zipcode)
	return loc_data.Latitude, loc_data.Longitude

def save_to_json(data, file_name='output.txt'):
	with open(file_name, 'w') as outfile:
		json.dump(data, outfile)

def get_pois(lat_lng, radius=15, types=[types.TYPE_FOOD]):
	"""
	location: must be given in latitutde-longitude
	radius: distance in meters within which to return plae results
	types: What type of point of interest (examples: TYPE_FOOD)
	"""
	query_result = google_places.nearby_search(lat_lng=lat_lng, radius=radius, types=types)

	if query_result.has_attributions:
		return query_result.html_attributions

	return None

def get_pois_features(place_id):
	"""
	Gets safety, elevation, other attributes for a given point of interest
	"""
	query_result = google_places.get_place(place_id)

	return query_result

def get_pois_reviews():
	"""
	Gets ratings for a point of interest, returns json
	"""
	query_result = google_places.get_place(place_id)

	return query_result.rating

