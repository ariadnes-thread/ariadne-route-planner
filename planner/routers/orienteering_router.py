from collections import namedtuple
from config import config
from pprint import pprint
import random
from typing import *
from googleplaces import GooglePlacesAttributeError
import utils.poi_types as poi_types

import googlemaps
import geopy.distance

from routers.base_router import BaseRouter
from utils import google_utils as GoogleUtils

GmapsResult = namedtuple('GmapsResult', ['name', 'latlon', 'rating'])


def get_pois_from_gmaps(location: Tuple[float, float],
                        radius: float, type_list) -> List[GmapsResult]:
    """
    Get POIs from Google Maps.

    Get POIs from Google Maps Places API Nearby Search. It only uses a
    single API request, and only returns up to 20 places.
    :param location: (lat, lon) pair.
    :param radius: Search radius in meters.
    :param type_list: List of the type of POIS being fetched from gmaps
        (parks, landmarks, coffee shops, etc.)
    :return: List of results.
    """
    GoogleHelper = GoogleUtils.GoogleHelper()
    places = GoogleHelper.get_pois({'lat': location[0], 'lng': location[1]},
                                   radius=radius, type_list=type_list)
    output = []
    for place in places:
        try:
            # Note: some places don't seem to have ratings.
            # These return a GooglePlacesAttributeError as caught below,
            # and are skipped.
            # Convert rating and latlon from Decimal to float.
            output.append(GmapsResult(
                name=place.name,
                latlon=(float(place.geo_location['lat']),
                        float(place.geo_location['lng'])),
                rating=float(place.rating)
            ))
        except GooglePlacesAttributeError:
            # Name, location, or rating wasn't available. Skip it
            pass

    return output


def nearest_vertex(conn, latlon: Tuple[float, float]) -> int:
    """
    Return nearest vertex to a (lat, lon) pair.
    :param latlon: (lat, lon) tuple.
    :return: vertex ID.
    """
    with conn.cursor() as cur:
        # Careful!!! PostGIS ST_Point is (lon, lat)!
        cur.execute('''
        SELECT * FROM ways_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326)
        LIMIT 1;
        ''', (latlon[1], latlon[0]))
        result = cur.fetchone()
        return result[0]


def all_pairs_shortest_path_costs(conn, vids: List[int]) \
        -> Dict[Tuple[int, int], float]:
    """
    Compute distance between each pair of vertices.
    :param vids: List of vertex ids.
    :return: Map of (vertex pair) -> distance.
    """
    with conn.cursor() as cur:
        # Execute many-to-many Dijkstra's. Give edge costs in meters
        cur.execute('''
        SELECT *
        FROM pgr_dijkstraCost(
            'SELECT gid AS id, source, target, length_m AS cost, ' ||
             'length_m * SIGN(reverse_cost) AS reverse_cost FROM ways',
            %s, %s)
        ''', (vids, vids))
        results = cur.fetchall()
        return {(start_vid, end_vid): length
                for (start_vid, end_vid, length) in results}


def solve_orienteering(node_score: Dict[int, float],
                       max_distance: float,
                       pairdist: Dict[Tuple[int, int], float],
                       origin_vid: int, dest_vid: int,
                       power_param: float = 4.0, length_param: int = 4,
                       ntrials: int = 1000) -> List[int]:
    """
    Solve the orienteering problem for a set of nodes.

    There are two kinds of nodes: "points of interest", and the origin and
    destination. Scores are only for points of interest, but distances
    must be for *all* pairs of vertices.
    :param node_score: Weights of all POIs.
    :param max_distance: Desired maximum distance.
    :param pairdist: Map of distances between each pair of nodes, including
        origin, destination, and POIs.
    :param origin_vid: Origin id.
    :param dest_vid: Destination id.
    Orienteering algorithm parameters:
    :param power_param: Configures how desirability is calculated.
    :param length_param: Configures how many of the top nodes to keep.
    :param ntrials: Number of random walks to try.
    :return: List of nodes along the best path, including the origin and
    destination.
    If something crazy happens like the distance from the origin to the
    destination is > max_distance, still return [origin_vid, dest_vid].
    """

    def make_path() -> Optional[Tuple[List[int], float, float]]:
        """
        Make a path from origin to destination.
        This function may fail and return None. Currently the only reason
        it could fail is if (origin_vid, dest_vid) not in pairdist,
        i.e. the origin cannot reach the destination.
        :return: (List of nodes, score, distance).
            The list of nodes includes the origin and destination.
            If something fails, return None.
        """
        path = [origin_vid]
        score = 0
        dist = 0
        visited = set()

        # Make a path
        while True:
            # Get feasible nodes, and compute their desirability
            cur = path[-1]
            feasible_nodes = []
            for v in set(node_score) - visited:
                try:
                    if dist + pairdist[(cur, v)] + pairdist[(v, dest_vid)] \
                            < max_distance:
                        d = (node_score[v] / pairdist[(cur, v)]) ** power_param
                        feasible_nodes.append((d, v))
                except KeyError:
                    # cur cannot reach v, or v cannot reach dest, so no
                    # pairdist
                    pass

            # If no POIs are feasible, go directly to destination
            if not feasible_nodes:
                path.append(dest_vid)
                try:
                    dist += pairdist[(cur, dest_vid)]
                    return path, score, dist
                except KeyError:
                    # cur cannot reach dest.
                    # But we reason backward: how did we get to cur? From
                    # another node prev. But prev wouldn't have chosen cur
                    # if cur couldn't reach dest.
                    # So cur must be the origin, and the origin cannot
                    # reach dest.
                    return None

            # Choose next node
            feasible_nodes.sort(reverse=True)  # Sort highest -> lowest desirability
            feasible_nodes = feasible_nodes[:length_param]
            feas_d, feas_v = zip(*feasible_nodes)
            nextnode = random.choices(feas_v, feas_d)[0]

            # Advance to next node
            path.append(nextnode)
            score += node_score[nextnode]
            dist += pairdist[(cur, nextnode)]
            visited.add(nextnode)

    # TODO what if max_distance < shortest distance from origin to dest?
    bestpath = [origin_vid, dest_vid]
    bestscore = 0
    bestdist = 0

    for trial in range(ntrials):
        res = make_path()
        if res is None:
            continue
        mypath, myscore, mydist = res

        # Better score, or same score but shorter path
        if myscore > bestscore or \
                (myscore == bestscore and mydist < bestdist):
            bestpath = mypath
            bestscore = myscore
            bestdist = mydist
            print('Best path: {}, score={}, dist={}, trial={}'.format(
                bestpath, bestscore, bestdist, trial))

    return bestpath


def get_route_geojson(conn, nodes: List[int]) -> Tuple[str, float]:
    """
    Find route through all vertices and return its GeoJSON.
    :param nodes: List of vertices.
    :return: (GeoJSON of path, total length of path in meters)
    """
    with conn.cursor() as cur:
        cur.execute('''
        WITH dijkstra AS (
            SELECT *
            FROM pgr_dijkstraVia(
                'SELECT gid AS id, source, target, cost, reverse_cost FROM ways',
                %s)
        )
        SELECT
            ST_AsGeoJSON(ST_MakeLine(CASE WHEN node = source THEN the_geom ELSE ST_Reverse(the_geom) END)) AS geojson, 
            SUM(ways.length_m) AS length
        FROM dijkstra
          JOIN ways ON dijkstra.edge = ways.gid;
        ''', (nodes,))
        return cur.fetchone()


class OrienteeringRouter(BaseRouter):
    """
    Router that makes routes by visiting nice vertices.
    Basically make_route is the only function meant to be used from outside.
    """

    def __init__(self, conn, gmaps_api_key: str):
        """
        Create an orienteering router.
        :param gmaps_api_key: Google Maps API key.
        :param conn: psycopg2 database connection.
        """
        self.gmapsclient = googlemaps.Client(gmaps_api_key)
        self.conn = conn

    def make_route(self, origin, dest, length_m, *args, **kwargs):
        """
        Make a route of at most a given length using orienteering heuristics.
        :param origin: lat/lon pair.
        :param dest: lat/lon pair.
        :param length_m: Desired length in meters.
        :return: (GeoJSON of route, total length of route in meters)
        """
        # Get points of interest
        center = midpoint(origin, dest)
        print('CENTER:', center)
        pois = get_pois_from_gmaps(center, length_m / 2,
                                   [poi_types.TYPE_PARK, poi_types.TYPE_RESTAURANT])

        # Filter POIs that are too far away
        pois = [
            poi for poi in pois
            if geopy.distance.geodesic(origin, poi.latlon).meters +
               geopy.distance.geodesic(poi.latlon, dest).meters <= length_m
        ]

        # Map origin, dest, and POIs to actual vertices
        origin_vid = nearest_vertex(self.conn, origin)
        dest_vid = nearest_vertex(self.conn, dest)
        poi_nodes = {
            nearest_vertex(self.conn, poi.latlon): poi
            for poi in pois
        }
        print('ORIGIN:', origin_vid, '; DEST:', dest_vid)
        pprint(poi_nodes)
        ratings = {vid: poi_nodes[vid].rating for vid in poi_nodes}

        # Solve APSP between origin, dest, and POIs
        all_vids = [origin_vid, dest_vid] + list(poi_nodes.keys())
        pairdist = all_pairs_shortest_path_costs(self.conn, all_vids)
        # TODO if a node is not connected, pairdist may silently omit distances
        # Sanity check that dest is actually reachable from origin?
        # Other checks for strongly connected components?

        # Solve orienteering problem from origin to dest
        bestpath = solve_orienteering(ratings, length_m, pairdist,
                                      origin_vid, dest_vid)

        # Compute the overall route from origin to dest
        return get_route_geojson(self.conn, bestpath)


def midpoint(coord1, coord2):
    """Return midpoint of two lat/lon coordinates."""
    return (coord1[0] + coord2[0]) / 2, (coord1[1] + coord2[1]) / 2


def main():
    origin = (34.140003, -118.122775)  # Caltech
    dest = (34.140707, -118.132212)  # Lake Ave
    length_m = 6000  # Maximum length of path in meters

    conn = db_conn.connPool.getconn()
    router = OrienteeringRouter(config['gmapsApiKey'], conn)
    pprint(router.make_route(origin, dest, length_m))


if __name__ == '__main__':
    import db_conn

    main()
