import logging
from routers.base_router import *
import poi_types
# Sorta hack: importing from another router
import routers.orienteering_router as orientrouter

from utils import google_utils as GoogleUtils

logger = logging.getLogger(__name__)


class POIsOnWayRouter(BaseRouter):
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

    def make_route(self, origin_latlon: Tuple[float, float],
                   dest_latlon: Tuple[float, float], **kwargs) -> RouteResult:
        """
        Make routes that visits nearby points of interest.
        :return: Resulting route.
        """
        # Parse kwargs
        poi_prefs = kwargs.pop('poi_prefs')
        edge_prefs = kwargs.pop('edge_prefs')
        bbox = kwargs.pop('bbox', None)

        # Get points of interest
        center = orientrouter.midpoint(origin_latlon, dest_latlon)
        # TODO: the radius is some arbitrary large #
        gmaps_results = orientrouter.get_pois_from_gmaps(center, 10000, poi_prefs)

        # Compute nearest POIs to path
        def ellipse_distance_sq(f1, f2, p):
            """dist(f1, p)^2 + dist(f2, p)^2"""
            return (p[0] - f1[0])**2 + (p[1] - f1[1])**2 + (p[0] - f2[0])**2 + (p[1] - f2[1])**2
        gmaps_results.sort(key=lambda g: ellipse_distance_sq(origin_latlon, dest_latlon, g.latlon))
        gmaps_results = gmaps_results[:3]
        print(gmaps_results)
        # TODO: POIs are not in the optimal order to be visited...but oh well

        # Map origins, dests, and POIs to actual vertices
        origin = orientrouter.nearest_vertex(self.conn, origin_latlon)
        dest = orientrouter.nearest_vertex(self.conn, dest_latlon)
        pois = [orientrouter.nearest_vertex(self.conn, g.latlon) for g in gmaps_results]

        # Make route
        edges_sql = orientrouter.make_edges_sql(self.conn, edge_prefs, bbox=bbox)
        nodes = [origin] + pois + [dest]
        with self.conn.cursor() as cur:
            cur.execute('''
            CREATE TEMPORARY TABLE dijkstra AS (
              SELECT * FROM pgr_dijkstraVia(%s, %s)
            );
            ''', (edges_sql, nodes,))

            cur.execute('''
            SELECT
              ST_AsGeoJSON(ST_MakeLine(
                CASE WHEN node = source THEN ways.the_geom ELSE ST_Reverse(ways.the_geom) END
              )) AS geojson,
              array_agg(ARRAY[length_m, wvp.elevation]) AS elevationData,
              SUM(dijkstra.cost)
            FROM dijkstra
              JOIN ways ON dijkstra.edge = ways.gid
              JOIN ways_vertices_pgr wvp ON dijkstra.node = wvp.id;
            ''', ())
            geojson, elevationData, length = cur.fetchone()

            # Compute length of each leg
            cur.execute('''
            SELECT SUM(cost)
            FROM dijkstra 
            GROUP BY path_id
            ORDER BY path_id;
            ''', ())
            lengths_of_legs = cur.fetchall()
            # length_of_legs is a list of 1-tuples. Convert to list of floats
            lengths_of_legs = [l[0] for l in lengths_of_legs]

            # TODO if there's an error above, will this table be dropped?
            cur.execute('DROP TABLE dijkstra;')

            logger.info('Lengths of legs: {}'.format(lengths_of_legs))


        # Compute POIResult objects
        poiresults = [PoiResult(g.latlon, g.name, g.type, l)
                      for g, l in zip(gmaps_results, lengths_of_legs)]
        return RouteResult(
            geojson,
            0, length,
            elevationData,
            pois=poiresults
        )



def main():
    origin = (34.140003, -118.122775)  # Avery
    dest = (34.140771, -118.132323)  # Lake ave
    poi_prefs = {
        poi_types.TYPE_PARK: 2,
        poi_types.TYPE_ART_GALLERY: 3,
    }
    edge_prefs = {
        'popularity': 1,
        'green': 5
    }

    conn = db_conn.connPool.getconn()
    router = POIsOnWayRouter(conn)
    route = router.make_route(origin, dest, poi_prefs=poi_prefs,
                              edge_prefs=edge_prefs)

    print(RouteEncoder().encode(route))


if __name__ == '__main__':
    import db_conn
    logging.basicConfig(level=logging.INFO)
    main()
