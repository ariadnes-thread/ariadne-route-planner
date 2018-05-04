"""
Functions for getting attributes about points of interest.
Extracts data from POI locations (elevation, safety, etc.)

Uses: Google Place Search

Uses the python-google-places wrapper:
https://github.com/slimkrazy/python-google-places
"""

from googleplaces import GooglePlaces, types
from configparser import ConfigParser
import psycopg2
import json

class GoogleHelper:
	"""
	Helper class for accessing the google API
	"""
	def __init__(self, gmaps_api_key=None):
		if gmaps_api_key is None:
			config = ConfigParser()
			with open('config.json') as f:
			    config = json.load(f)
			gmaps_api_key = config["gmapsApiKey"]

		self.google_places = GooglePlaces(config["gmapsApiKey"])


	def save_to_json(self, data, file_name='output.txt'):
		with open(file_name, 'w') as outfile:
			json.dump(data, outfile)


	def get_pois(self, lat_lng, radius=15, type_list=[types.TYPE_PARK]):
		"""
		location: must be given in latitutde-longitude
		radius: distance in meters within which to return plae results
		types: What type of point of interest (examples: TYPE_FOOD)
		"""
		query_result = self.google_places.nearby_search(lat_lng=lat_lng, types=type_list, radius=2000)
		
		if query_result.has_attributions:
			return query_result.html_attributions

		return query_result

	def get_pois_features(self, place_id: str):
		"""
		Gets safety, elevation, other attributes for a given point of interest
		"""
		query_result = self.google_places.get_place(place_id)

		return query_result

	def get_pois_reviews(self):
		"""
		Gets ratings for a point of interest, returns json
		"""
		query_result = self.google_places.get_place(place_id)

		return query_result.rating
