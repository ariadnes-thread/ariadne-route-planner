import logging
from routers.base_router import *
import utils.poi_types as poi_types
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
            return (p[0] - f1[0]) ** 2 + (p[1] - f1[1]) ** 2 + (p[0] - f2[0]) ** 2 + (p[1] - f2[1]) ** 2

        gmaps_results.sort(key=lambda g: ellipse_distance_sq(origin_latlon, dest_latlon, g.latlon))
        gmaps_results = gmaps_results[:3]
        logger.info('POIs: {}'.format(gmaps_results))

        # Sort the POIs by their scalar projection on the line from the origin
        # to the destination. This approximates the optimal order to visit them
        def scalar_proj(o, a, d):
            """Compute scalar projection of OA onto OD"""
            oa = (a[0] - o[0], a[1] - o[1])
            od = (d[0] - o[0], d[1] - o[1])
            dot_product = oa[0] * od[0] + oa[1] * od[1]
            magnitude_od = math.hypot(od[0], od[1])
            return dot_product / magnitude_od
        # print('Before sorting:')
        # for gmaps_result in gmaps_results:
        #     print(gmaps_result, 'proj=', scalar_proj(origin_latlon, gmaps_result.latlon, dest_latlon))
        gmaps_results.sort(key=lambda g: scalar_proj(origin_latlon, g.latlon, dest_latlon))
        logger.info('After sorting: {}'.format(gmaps_results))

        # Map origins, dests, and POIs to actual vertices
        origin = orientrouter.nearest_vertex(self.conn, origin_latlon)
        dest = orientrouter.nearest_vertex(self.conn, dest_latlon)
        pois = [orientrouter.nearest_vertex(self.conn, g.latlon) for g in gmaps_results]

        # Make route
        edges_sql = orientrouter.make_edges_sql(self.conn, edge_prefs, bbox=bbox)
        nodes = [origin] + pois + [dest]
        with self.conn.cursor() as cur:
            cur.execute('''
            WITH dijkstra AS (
                SELECT * FROM pgr_dijkstraVia(%s, %s, U_turn_on_edge:=FALSE)
            )
            SELECT
              ST_AsGeoJSON(ST_MakeLine(
                CASE WHEN node = source THEN the_geom ELSE ST_Reverse(the_geom) END
              )) AS geojson,
              array_agg(ARRAY[length_m, elevation, nPoints]) AS elevationData, SUM(length_m) AS length
                FROM (
                    SELECT node, source, ways.the_geom, length_m, wvp.elevation, 
                        SUM(ST_NumPoints(ways.the_geom) - 1) OVER (ORDER BY seq) AS nPoints
                    FROM dijkstra JOIN ways ON dijkstra.edge = ways.gid
                    JOIN ways_vertices_pgr wvp ON dijkstra.node = wvp.id) subq;
            ''', (edges_sql, nodes))
            geojson, elevationData, length = cur.fetchone()

            # # Compute length of each leg
            # cur.execute('''
            # SELECT SUM(cost)
            # FROM dijkstra
            # GROUP BY path_id
            # ORDER BY path_id;
            # ''', ())
            # lengths_of_legs = cur.fetchall()
            # # length_of_legs is a list of 1-tuples. Convert to list of floats
            # lengths_of_legs = [l[0] for l in lengths_of_legs]
            #
            #
            # logger.info('Lengths of legs: {}'.format(lengths_of_legs))

        # Old Compute POIResult objects
        # poiresults = [PoiResult(g.latlon, g.name, g.type, l)
        #               for g, l in zip(gmaps_results, lengths_of_legs)]
        # Compute POIResult objects
        poiresults = [PoiResult(g.latlon, g.name, g.type, -1)
                      for g in gmaps_results]
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
        poi_types.TYPE_ART_GALLERY: 2
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
