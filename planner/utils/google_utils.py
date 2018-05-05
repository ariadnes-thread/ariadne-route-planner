"""
Functions for getting attributes about points of interest.
Extracts data from POI locations (elevation, safety, etc.)

Uses: Google Place Search

Uses the python-google-places wrapper:
https://github.com/slimkrazy/python-google-places
"""

from googleplaces import GooglePlaces, types
import json


def save_to_json(data, file_name='output.txt'):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile)


class GoogleHelper:
    """
    Helper class for accessing the google API
    """

    def __init__(self, gmaps_api_key=None):
        if gmaps_api_key is None:
            from config import config
            gmaps_api_key = config["gmapsApiKey"]

        self.google_places = GooglePlaces(gmaps_api_key)

    def get_pois(self, lat_lng, radius, type_list):
        """
        location: must be given in latitutde-longitude
        radius: distance in meters within which to return plae results
        types: What type of point of interest (examples: TYPE_FOOD)
        return: List of GooglePlacesSearchResults.
        """
        results = []
        for t in type_list:
            res = self.google_places.nearby_search(
                lat_lng=lat_lng, type=t, radius=radius)
            results.extend(res.places)

        # if query_result.has_attributions:
        #     return query_result.html_attributions

        return results

    def get_pois_features(self, place_id: str):
        """
        Gets safety, elevation, other attributes for a given point of interest
        """
        query_result = self.google_places.get_place(place_id)

        return query_result

    def get_pois_reviews(self, place_id):
        """
        Gets ratings for a point of interest, returns json
        """
        query_result = self.google_places.get_place(place_id)

        return query_result.rating
