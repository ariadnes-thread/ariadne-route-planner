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
import psycopg2
import db_conn
import json

config = ConfigParser()
with open('config.json') as f:
    config = json.load(f)
conn = db_conn.connPool.getconn()
google_places = GooglePlaces(config["gmapsApiKey"])

print('\n', config['gmapsApiKey'], '\n')
def zipcode_to_latlong(zipcode):
	search = ZipcodeSearchEngine()
	loc_data = search.byzipcode(zipcode)
	return loc_data.Latitude, loc_data.Longitude

def save_to_json(data, file_name='output.txt'):
	with open(file_name, 'w') as outfile:
		json.dump(data, outfile)


def get_pois(lat_lng, radius=15, type_list=['park']):
	"""
	location: must be given in latitutde-longitude
	radius: distance in meters within which to return plae results
	types: What type of point of interest (examples: TYPE_FOOD)
	"""
	type_dict = {'park': types.TYPE_PARK}

	new_types = []
	for t in type_list:
		new_types.append(type_dict[t])
	query_result = google_places.nearby_search(lat_lng=lat_lng, keyword='park', radius=2000)
	
	if query_result.has_attributions:
		return query_result.html_attributions

	return query_result

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

def save_to_db():
	# Import app config
	config = json.load(open('config.json'))

	# Setup `psycopg` connection, http://initd.org/psycopg/docs/usage.html
	conn = psycopg2.connect(
	    host=config["dbHost"]
	    dbname=config["dbName"],
	    user=config["dbUser"],
	    password=config["dbPass"],
	    port=config["dbPort"]
	)
	cur = conn.cursor()

	# Commit changes to the database (if any) and close connection
	conn.commit()
	cur.close()
	conn.close()

