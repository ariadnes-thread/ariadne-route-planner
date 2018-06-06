import logging
from routers.base_router import *
from pprint import pprint


__all__ = ['DistEdgePrefsRouter']

logger = logging.getLogger(__name__)


class PathResult(NamedTuple):
    points: List[int]
    score: float
    length: float


class GmapsResult(NamedTuple):
    name: str
    latlon: Tuple[float, float]
    score: float
    type: str

def get_route_geojson(conn, origin, dest, distance, popularity, greenery):
    """
    Find route through all vertices and return its GeoJSON.
    :param edges_sql: Edges query for pgr_dijkstra.
    :param nodes: List of vertices.
    :return: GeoJSON of path, as a LineString.
    """

    lon1 = origin[1]
    lat1 = origin[0]
    lon2 = dest[1]
    lat2 = dest[0]

    logger.info("Lon1 %s, Lat1 %s, Lon2 %s, Lat2 %s,\n distance %s,\n popularity %s,\n greenery %s",
                lon1, lat1, lon2, lat2, distance, popularity, greenery)
    with conn.cursor() as cur:
        cur.execute('''
            SELECT * FROM 
            pathfromnearestknownpointslength(%s, %s, %s, %s, %s, %s, %s)
            ''', (lon1, lat1, lon2, lat2, distance, popularity, greenery))
        return cur.fetchone()


class DistEdgePrefsRouter(BaseRouter):
    """
    Router that makes routes by taking into account desired distance and edge preferences.
    Basically make_route is the only function meant to be used from outside.
    """

    def __init__(self, conn):
        """
        Create an orienteering router.
        :param conn: psycopg2 database connection.
        """
        self.conn = conn

    def make_route(self, origin_latlon: Tuple[float, float],
                   dest_latlon: Tuple[float, float], **kwargs) -> RouteResult:
        """
        Make routes of at most a given length while visitng points of interest.

        Expected keyword arguments:
        - desired_dist: float - Desired distance in meters.
        - poi_prefs: Dict[str, float] - Map of poi types to their relative
          weights. The keys are a subset of what's in poi_types.py.
        - edge_prefs: Dict[str, float] - Map of edge types to their weights.
          The keys are a subset of ['green', 'popularity'].

        :return: Resulting route.
        """
        # Parse kwargs
        length_m = kwargs.pop('desired_dist')
        edge_prefs = kwargs.pop('edge_prefs')

        geojson, length, elevationData = get_route_geojson(self.conn, origin_latlon, dest_latlon, length_m, edge_prefs.get('green', 0),
             edge_prefs.get('popularity', 0))

        # Hack: make sure linestring is in the correct direction
        geojson = orient_linestring(origin_latlon, dest_latlon, geojson)

        return RouteResult(
            geojson,
            0, length,
            elevationData, []
        )


def midpoint(coord1, coord2):
    """Return midpoint of two lat/lon coordinates."""
    return (coord1[0] + coord2[0]) / 2, (coord1[1] + coord2[1]) / 2


def main():
    origin = (34.140003, -118.122775)  # Avery
    dest = (34.147672, -118.144328)  # Pasadena city hall
    length_m = 5000  # Maximum length of path in meters
    edge_prefs = {
        'popularity': 1,
        'green': 5
    }

    conn = db_conn.connPool.getconn()
    router = DistEdgePrefsRouter(conn)
    route = router.make_route(
        origin, dest, desired_dist=length_m,
        edge_prefs=edge_prefs)

    print(RouteEncoder().encode(route))


if __name__ == '__main__':
    import db_conn
    logging.basicConfig(level=logging.INFO)
    main()
