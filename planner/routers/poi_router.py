import logging
from routers.orienteering_router import nearest_vertex, make_edges_sql, get_pois_from_gmaps, get_route_geojson
from routers.base_router import *
import utils.poi_types as poi_types
import math

__all__ = ['PoiRouter']

logger = logging.getLogger(__name__)

def return_n_midpoints(coord1, coord2, N=5):
    """Return N points equally spaced between two lat/lon coordinates."""
    points = []
    cur_x = coord1[0]
    cur_y = coord1[1]

    sign_x = 1
    sign_y = 1
    if max(coord1[0], coord2[0]) == coord2[0]:
        sign_x = -1
    if max(coord1[1], coord2[1]) == coord2[1]:
        sign_y = -1

    step_lat = (coord1[0] - coord2[0]) / N
    step_lon = (coord1[1] - coord2[1]) / N

    for x in range(0, N):
        cur_x += step_lat*sign_x
        cur_y += step_lon*sign_y
        points.append((cur_x, cur_y))

    return points


class PoiRouter(BaseRouter):
    """
    Router that finds nearby POIs and performs Dijkstra's
    """

    def __init__(self, conn):
        self.conn = conn

    def make_route(self, origin_latlon: Tuple[float, float], dest_latlon: Tuple[float, float], **kwargs):
        """
        Make routes based on visiting points of interest

        Expected Keyword Arguments:
        - poi_prefs: Dict[str, float] - Map of poi types to their relative
          weights. The keys are a subset of what's in poi_types.py.
        - edge_profs: Dict[str, float] - Map of edge types to their weights.
            Keys are a subset of ['green', 'popularity']
        - num_pois: Number of pois desired along route, default is 5
        :param origin_latlon: (lat, lon) of origin
        :param dest_latlon: (lat, lon) of dest.
        :return: Resulting route
        """

        # Parse kwargs
        poi_prefs = kwargs.pop('poi_prefs')
        edge_prefs = kwargs.pop('edge_prefs')
        num_pois = kwargs.pop('num_pois', 5)
        bbox = kwargs.pop('bbox', None)
        # Get points of interest
        points_between = return_n_midpoints(origin_latlon, dest_latlon, num_pois)
        closest_pois = []
        for p in points_between:
            # Search radius parameter should be smaller than the space in between two points
            search_radius = math.sqrt(((origin_latlon[0] - dest_latlon[0]) / num_pois)**2 +
                                 ((origin_latlon[1] - dest_latlon[1]) / num_pois)**2)*111111
            try:
                pois = get_pois_from_gmaps(p, search_radius, poi_prefs)
                if len(pois) > 0:
                    for p in pois:
                        # Checking that all POIs added are unique
                        if p not in closest_pois:
                            closest_pois.append(pois[0])
                            break
            except:
                logger.info('Failed to find nearby POIs for point %s', p)

        # Map origins, dests, and POIs to actual vertices
        origin = nearest_vertex(self.conn, origin_latlon)
        dest = nearest_vertex(self.conn, dest_latlon)
        poi_nodes = {
            nearest_vertex(self.conn, poi.latlon): poi
            for poi in closest_pois
        }
        logger.info('Origin %s, dest %s', origin, dest)
        logger.info('POIs: %s', poi_nodes.keys())

        # Compute edges_sql based on edge preferences
        edges_sql = make_edges_sql(self.conn, edge_prefs, bbox=bbox)

        # TODO: edgediscounting

        # Find path from Dijkstra's
        # Compute pairwise distances between origins, dests, and POIs
        path, elevationData = get_route_geojson(
            self.conn, edges_sql, [origin] + list(poi_nodes.keys()) + [dest])
        logger.info('Best path: %s', path)
        # TODO: replace 0 values with score and length (respectively)
        return RouteResult(
            path,
            0, 0,
            elevationData,
            pois=closest_pois
        )


def main():
    origin = (34.140003, -118.122775)  # Avery
    dest = (34.147672, -118.144328)  # Pasadena city hall
    poi_prefs = {
        poi_types.TYPE_PARK: 2,
        poi_types.TYPE_ATM: 3,
        poi_types.TYPE_CAFE: 3
    }
    edge_prefs = {
         'popularity': 1,
         'green': 5
    }
    router = PoiRouter(db_conn.connPool.getconn())
    print(router.make_route(origin, dest, poi_prefs=poi_prefs, edge_prefs=edge_prefs, num_pois=5))


if __name__ == '__main__':
    import db_conn

    main()
