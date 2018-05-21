import heapq
import itertools
import logging
import statistics
import random
from typing import *
from googleplaces import GooglePlacesAttributeError
import utils.poi_types as poi_types
from routers.base_router import BaseRouter, RouteResult

from utils import google_utils as GoogleUtils


__all__ = ['OrienteeringRouter']

logger = logging.getLogger(__name__)


class PathResult(NamedTuple):
    path: List[int]
    score: float
    length: float


class GmapsResult(NamedTuple):
    name: str
    latlon: Tuple[float, float]
    score: float


def get_pois_from_gmaps(loc: Tuple[float, float], radius: float,
                        poi_prefs: Dict[str, float]) -> List[GmapsResult]:
    """
    Get POIs from Google Maps.

    Get POIs from Google Maps Places API Nearby Search. It only uses a
    single API request, and only returns up to 20 places.
    :param loc: (lat, lon) pair.
    :param radius: Search radius in meters.
    :param poi_prefs: Map of poi types to their relative weights.
    :return: List of results.
    """
    output = []
    GoogleHelper = GoogleUtils.GoogleHelper()

    for poitype in poi_prefs:
        # Places for this POI only
        places = GoogleHelper.get_pois({'lat': loc[0], 'lng': loc[1]},
                                       radius=radius, type_list=[poitype])
        for place in places:
            try:
                # Note: some places don't seem to have ratings.
                # These return a GooglePlacesAttributeError as caught below,
                # and are skipped.

                # Convert rating and latlon from Decimal to float.
                # Score POIs by their weight.
                output.append(GmapsResult(
                    name=place.name,
                    latlon=(float(place.geo_location['lat']),
                            float(place.geo_location['lng'])),
                    score=float(place.rating) * poi_prefs[poitype]
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


def make_edges_sql(conn, edge_prefs: Dict[str, float],
                   max_discount: float = 0.7) -> str:
    """
    Make edges_sql query from map of edge preferences. It's suitable for
    use in pgr_dijkstra calls.
    :param conn:
    :param edge_prefs: Map of edge preferences.
    :return: edges_sql string.
    """
    if sum(edge_prefs.values()) == 0:
        # No edge preferences
        return \
            '''
            SELECT
              gid AS id, source, target,
              length_m AS cost,
              length_m * SIGN(reverse_cost) AS reverse_cost
            FROM ways
            '''

    with conn.cursor() as cur:
        # Adjust edge costs by their greenery/popularity values, weighted by
        # preferences
        return cur.mogrify(
            '''
            SELECT
              gid AS id, source, target,
              length_m * multiplier AS cost,
              length_m * SIGN(reverse_cost) * multiplier AS reverse_cost
            FROM ways
              INNER JOIN (
                SELECT
                  gid, 
                  (1 - %s * ((%s * greenery + %s * popularity_highres)) / %s) 
                    AS multiplier
                FROM ways_metadata                  
              ) AS ways_multipliers USING (gid)
            ''',
            (max_discount,
             edge_prefs.get('green', 0),
             edge_prefs.get('popularity', 0),
             sum(edge_prefs.values()))
        ).decode()


def pairwise_shortest_path_costs(conn, edges_sql: str, origins: List[int],
         dests: List[int]) -> Dict[Tuple[int, int], float]:
    """
    Compute distance between each pair of origins and destinations.
    :param conn:
    :param edges_sql: Edges query for pgr_dijkstra.
    :param origins: List of starting vertices.
    :param dests: List of destination vertices.
    :return: Map of (vertex pair) -> distance, in meters.
        Although edges_sql may use adjusted edge costs, this method returns
        the true distances of the paths.
        If no path exists, entries may be missing.
    """
    with conn.cursor() as cur:
        # Execute many-to-many Dijkstra's.
        # Rejoin with 'ways' to get true lengths.
        cur.execute(
            '''
            WITH dijkstra AS (
                SELECT * FROM pgr_dijkstra(%s, %s, %s)
            )
            SELECT start_vid, end_vid, SUM(length_m)
            FROM dijkstra
              INNER JOIN ways ON (dijkstra.edge = ways.gid)
            GROUP BY start_vid, end_vid
            ''',
            (edges_sql, origins, dests))
        results = cur.fetchall()
        return {(start_vid, end_vid): length
                for (start_vid, end_vid, length) in results}


def solve_orienteering(
        poi_score: Dict[int, float], max_distance: float,
        pairdist: Dict[Tuple[int, int], float],
        origins: List[int], dests: List[int], noptions: int,
        power_param: float = 4.0, length_param: int = 4,
        n_total_trials: int = 1000) -> List[PathResult]:
    """
    Return high-scoring paths from any origin to any destination.
    Paths accumulate score by visiting POIs.
    :param poi_score: Score of each POI.
    :param max_distance: Desired maximum distance.
    :param pairdist: Map of distances between each pair of nodes.
        Specifically, all pairs in
        '(o, d) for o in origins + pois for d in pois + dests'
        should be represented. However, missing pairs are allowed; they are
        assumed not to exist.
    :param origins: List of possible origins.
    :param dests: List of possible destinations.
    :param noptions: Return up to this many options. There are a variety
        of reasons this method may return fewer than 'noptions' paths;
        see the comment for make_paths().
    Orienteering algorithm parameters:
    :param power_param: Configures how desirability is calculated.
    :param length_param: Configures how many of the top nodes to keep.
    :param n_total_trials: Number of total random paths to try.
    :return: List of (path, score, length), for each best path.
    """
    def make_path(origin: int, dest: int) -> PathResult:
        """
        Make a path from a specific origin to a specific destination.

        *Assumes* that (origin, dest) in pairdist, that is, origin can
        reach dest.
        :param origin: Origin vertex id.
        :param dest: Destination vertex id.
        :return: (List of nodes, score, distance) of a randomly generated
            path. The list of nodes includes origin and dest.
        """
        assert (origin, dest) in pairdist
        path = [origin]
        score = 0.0
        dist = 0.0
        visited = set()

        # Make a path
        while True:
            # Get feasible nodes, and compute their desirability
            cur = path[-1]
            feas = []
            for v in set(poi_score) - visited:
                try:
                    if dist + pairdist[(cur, v)] + pairdist[(v, dest)] \
                            < max_distance:
                        d = (poi_score[v] / pairdist[(cur, v)]) ** power_param
                        feas.append((d, v))
                except KeyError:
                    # cur cannot reach v, or v cannot reach dest, so no
                    # pairdist
                    pass

            # If no POIs are feasible, go directly to destination
            if feas == []:
                path.append(dest)
                # There are two cases here.
                # If cur is origin, origin can reach dest by this function's
                # precondition.
                # Otherwise, we reason backward. We got to cur from some
                # previous node, and we wouldn't have walked to cur if
                # it can't reach dest.
                # So there is no KeyError here.
                dist += pairdist[(cur, dest)]
                return PathResult(path, score, dist)

            # Choose next node
            feas.sort(reverse=True)  # Sort highest -> lowest desirability
            feas = feas[:length_param]
            feas_d, feas_v = zip(*feas)
            nextnode = random.choices(feas_v, feas_d)[0]

            # Advance to next node
            path.append(nextnode)
            score += poi_score[nextnode]
            dist += pairdist[(cur, nextnode)]
            visited.add(nextnode)

    def make_paths(origin: int, dest: int, ntrials: int
                   ) -> Iterator[PathResult]:
        """
        Make paths from origin to destination. Return unique paths found.

        There are several cases where the function may return zero, only
        one, or very few paths.
        - If origin cannot reach dest, return empty list.
        - If distance from origin to dest > max distance, technically no
          path is valid but we assume the user wanted a short path
          as possible, so return the path directly from origin to dest.
        - Otherwise, return up to the # distinct paths found.
        :param origin: Start of path.
        :param dest: Destination of path.
        :param ntrials: Number of trials to execute.
        :return: Iterator of (path, score, length).
        """
        if (origin, dest) not in pairdist:
            # Origin and dest are not connected. Yield no routes
            return

        if pairdist[origin, dest] > max_distance:
            # Yield only direct origin -> dest path
            yield PathResult([origin, dest], 0, pairdist[origin, dest])
            return

        # Return unique paths
        pathset = set()
        for _ in range(ntrials):
            path, score, length = make_path(origin, dest)
            t = tuple(path)
            if t not in pathset:
                yield PathResult(path, score, length)
                pathset.add(t)

    def make_all_paths() -> Iterator[PathResult]:
        for o, d in itertools.product(origins, dests):
            yield from make_paths(
                o, d, n_total_trials // (len(origins) * len(dests))
            )

    return heapq.nlargest(noptions, make_all_paths(), key=lambda x: x[1])


def get_route_geojson(conn, edges_sql: str, nodes: List[int]):
    """
    Find route through all vertices and return its GeoJSON.
    :param edges_sql: Edges query for pgr_dijkstra.
    :param nodes: List of vertices.
    :return: GeoJSON of path, as a LineString.
    """
    with conn.cursor() as cur:
        cur.execute('''
        WITH dijkstra AS (
            SELECT * FROM pgr_dijkstraVia(%s, %s)
        )
        SELECT
          ST_AsGeoJSON(ST_MakeLine(
            CASE WHEN node = source THEN ways.the_geom ELSE ST_Reverse(ways.the_geom) END
          )) AS geojson,
          array_agg(ARRAY[length_m, wvp.elevation]) as elevationData
        FROM dijkstra
          JOIN ways ON dijkstra.edge = ways.gid
          JOIN ways_vertices_pgr wvp on dijkstra.node = wvp.id;;
        ''', (edges_sql, nodes,))

        return cur.fetchone()


class OrienteeringRouter(BaseRouter):
    """
    Router that makes routes by visiting nice vertices.
    Basically make_route is the only function meant to be used from outside.
    """

    def __init__(self, conn):
        """
        Create an orienteering router.
        :param conn: psycopg2 database connection.
        """
        self.conn = conn

    def make_route(self, origin_latlons: List[Tuple[float, float]],
                   dest_latlons: List[Tuple[float, float]], noptions: int,
                   **kwargs) -> List[RouteResult]:
        """
        Make routes of at most a given length while visitng points of interest.

        Expected keyword arguments:
        - desired_dist: float - Desired distance in meters.
        - poi_prefs: Dict[str, float] - Map of poi types to their relative
          weights. The keys are a subset of what's in poi_types.py.
        - edge_prefs: Dict[str, float] - Map of edge types to their weights.
          The keys are a subset of ['green', 'popularity'].

        :return: List of routes. Each route is a RouteResult, containing
            (GeoJSON, score, total length in meters).
            Score is meant for comparing routes, but doesn't necessarily have
            meaning alone.
        """
        # Parse kwargs
        length_m = kwargs.pop('desired_dist')
        poi_prefs = kwargs.pop('poi_prefs')
        edge_prefs = kwargs.pop('edge_prefs')

        # Compute median point
        # TODO this isn't the center of the smallest circle that covers all the
        # origins/dests...but solving that (the smallest-circle problem) is
        # complicated.
        lats, lons = zip(*(origin_latlons + dest_latlons))
        medlat = statistics.median(lats)
        medlon = statistics.median(lons)
        center = (medlat, medlon)
        logger.info('CENTER: %s', center)

        # Get points of interest
        pois = get_pois_from_gmaps(center, length_m / 2, poi_prefs)

        # Map origins, dests, and POIs to actual vertices
        origins = [nearest_vertex(self.conn, o) for o in origin_latlons]
        dests = [nearest_vertex(self.conn, d) for d in dest_latlons]
        poi_nodes = {
            nearest_vertex(self.conn, poi.latlon): poi
            for poi in pois
        }
        logger.info('ORIGINS: %s, DEST: %s', origins, dests)
        logger.info('POIs: %s', poi_nodes)
        poi_score = {vid: poi_nodes[vid].score for vid in poi_nodes}

        # Compute edges_sql based on edge preferences
        edges_sql = make_edges_sql(self.conn, edge_prefs)

        # Compute pairwise distances between origins, dests, and POIs
        pairdist = pairwise_shortest_path_costs(
            self.conn, edges_sql, origins + list(poi_nodes.keys()),
            list(poi_nodes.keys()) + dests)
        # TODO if a node is not connected, pairdist may silently omit distances
        # Sanity check that dest is actually reachable from origin?
        # Other checks for strongly connected components?

        # Get high-scoring paths from origins to dests
        paths = solve_orienteering(poi_score, length_m, pairdist,
                                   origins, dests, noptions)
        logger.info('BEST PATHS: %s', paths)

        routes = []

        for p in paths:
            geojson, elevationData = get_route_geojson(self.conn, edges_sql, p.path)
            routes.append(RouteResult(
                geojson,
                p.score, p.length,
                elevationData,
                # Hack: this is simple but kludgy
                origins.index(p.path[0]),
                dests.index(p.path[-1])
            ))
        # Get GeoJSON of each path
        return routes


def midpoint(coord1, coord2):
    """Return midpoint of two lat/lon coordinates."""
    return (coord1[0] + coord2[0]) / 2, (coord1[1] + coord2[1]) / 2


def main():
    origins = [(34.140003, -118.122775),  # Avery
               (34.136872, -118.122910),  # Olive walk
               (34.137038, -118.127548),  # Kerchoff?
               ]
    dests = [(34.143209, -118.118393),  # PCC
             (34.147672, -118.144328),  # Pasadena city hall
             ]
    length_m = 4000  # Maximum length of path in meters
    poi_prefs = {
        poi_types.TYPE_PARK: 2,
        poi_types.TYPE_ART_GALLERY: 5
    }
    edge_prefs = {
        'popularity': 1,
        'green': 5
    }
    noptions = 5

    conn = db_conn.connPool.getconn()
    router = OrienteeringRouter(conn)
    routes = router.make_route(
        origins, dests, noptions, desired_dist=length_m, poi_prefs=poi_prefs,
        edge_prefs=edge_prefs)

    # linestringlist = []
    # for r in results:
    #     linestringlist.append(json.loads(r.route))
    # print(json.dumps(
    #     {'type': 'GeometryCollection', 'geometries': linestringlist}
    # ))

    for route in routes:
        print(route)


if __name__ == '__main__':
    import db_conn

    main()
