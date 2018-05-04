from pygeocoder import Geocoder
from uszipcode import ZipcodeSearchEngine
from geopy.geocoders import Nominatim

def zipcode_to_latlong(zipcode):
	"""
	Takes in zipcode and returns the corresponding latitude and longitude
	:param zipcode: String or Int of zipcode (either work)
	:return: Latutude, longitude
	"""

	# TODO: this works for some zip codes but not all
	# (pasadena doesn't work, but LA does). Fix to make it work
	# for everything
	search = ZipcodeSearchEngine()
	loc_data = search.by_zipcode(zipcode)
	return loc_data['Latitude'], loc_data['Longitude']

def latlong_to_zipcode(lat, lon):
	"""
	Takes in zipcode and returns the corresponding latitude and longitude
	:param lat: Latitude
	:param lon: Longitude
	:return: zipcode
	"""
	results = Geocoder.reverse_geocode(lat, lon)
	return results[0].postal_code

def address_to_latlong(address):
	"""
	Takes in latitude and longitude and convert to address
	:param address: Takes in address as string (ex: "175 5th Avenue NYC")
	:return: Latitude, longitude
	"""

	geolocator = Nominatim()
	location = geolocator.geocode(address)
	return location.latitude, location.longitude

def latlong_to_address(lat, lon):
	"""
	Takes in latitude and longitude and convert to address
	:param lat: Latitude
	:param lon: Longitude
	:return: address
	"""

	geolocator = Nominatim()
	location = geolocator.reverse(str(lat) + ", " + str(lon))
	return location.address

#zipcode_to_latlong(91110)
#latlong_to_address(52.509669, 13.376294)
#print(address_to_latlong("1320 San Pasqual St Pasadena"))
latlong_to_zipcode(52.509669, 13.376294)
