from collections import namedtuple
import json
from pprint import pprint
from typing import *

import googlemaps
import db_conn
import psycopg2


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

if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)

    conn = db_conn.connPool.getconn()

    router = OrienteeringRouter(config['gmapsApiKey'], conn)
    parks = router.get_parks_from_gmaps((34.145265, -118.130473), 5000)
    park_nodes = {
        router.nearest_vertex(park.latlon): park
        for park in parks
    }
    pprint(park_nodes)

