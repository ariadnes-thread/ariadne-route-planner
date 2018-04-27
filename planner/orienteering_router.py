from collections import namedtuple
import json
from pprint import pprint
from typing import *

import googlemaps
import db_conn
import psycopg2
import geopy.distance


class OrienteeringRouter:
    GmapsResult = namedtuple('GmapsResult', ['name', 'latlon', 'rating'])

    def __init__(self, gmaps_api_key: str, conn):
        """
        Create an orienteering router.
        :param gmaps_api_key: Google Maps API key.
        :param conn: psycopg2 database connection.
        """
        self.gmapsclient = googlemaps.Client(gmaps_api_key)
        self.conn = conn
        self.cur = conn.cursor()

    def get_parks_from_gmaps(self, location: Tuple[float, float],
                             radius: float) -> List[GmapsResult]:
        """
        Get POIs from Google Maps.

        Get POIs from Google Maps Places API Nearby Search. It only uses a
        single API request, and only returns up to 20 places.
        :param location: (lat, lon) pair.
        :param radius: Search radius in meters.
        :return: List of results.
        """
        res = self.gmapsclient.places_nearby(
            location=(34.145265, -118.130473), # lat, lon
            radius=5000, # meters
            type='park'
        )

        output = []
        for result in res['results']:
            try:
                output.append(self.GmapsResult(
                    name=result['name'],
                    latlon=(result['geometry']['location']['lat'],
                            result['geometry']['location']['lng']),
                    rating=result['rating']
                ))
            except KeyError:
                # Skip POIs that are missing one of the fields
                pass

        return output


    def nearest_vertex(self, latlon: Tuple[float, float]) -> int:
        """
        Return nearest vertex to a (lat, lon) pair.
        :param latlon: (lat, lon) tuple.
        :return: vertex ID.
        """
        # Careful!!! PostGIS ST_Point is (lon, lat)!
        self.cur.execute('''
        SELECT * FROM ways_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326)
        LIMIT 1;
        ''', (latlon[1], latlon[0]))
        result = self.cur.fetchone()
        return result[0]


def midpoint(coord1, coord2):
    """Return midpoint of two lat/lon coordinates."""
    return (coord1[0] + coord2[0]) / 2, (coord1[1] + coord2[1]) / 2

if __name__ == '__main__':
    origin = (34.140003, -118.122775)  # Caltech
    dest = (34.140707, -118.132212)  # Lake Ave
    length_m = 6000  # Maximum length of path in meters

    # # *only valid for Pasadena area*
    # # Used an online calculator to get m/deg at Pasadena's latitude
    # m_per_deg_latitude = 110924.90
    # m_per_deg_longitude = 92232.91
    # m_per_deg = (m_per_deg_latitude + m_per_deg_longitude) / 2
    # length_deg = length_m / m_per_deg

    with open('config.json') as f:
        config = json.load(f)
    conn = db_conn.connPool.getconn()
    router = OrienteeringRouter(config['gmapsApiKey'], conn)

    # Get points of interest
    center = midpoint(origin, dest)
    print('CENTER:', center)
    parks = router.get_parks_from_gmaps(center, length_m / 2)
    # print(len(parks), parks)

    # Filter POIs that are too far away
    parks = [
        park for park in parks
        if geopy.distance.geodesic(origin, park.latlon).meters
           + geopy.distance.geodesic(park.latlon, dest).meters <= length_m
    ]
    # print(len(parks), parks)

    # Map POIs to actual vertices
    park_nodes = {
        router.nearest_vertex(park.latlon): park
        for park in parks
    }
    pprint(park_nodes)
