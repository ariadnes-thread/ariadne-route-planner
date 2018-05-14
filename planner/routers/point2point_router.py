import itertools
from pprint import pprint

from routers.base_router import BaseRouter, RouteResult


class Point2PointRouter(BaseRouter):
    def __init__(self, conn):
        self.conn = conn

    def make_route(self, origins, dests, noptions, **kwargs):
        """
        :param origins: (lat, lon) pairs.
        :param dests: (lat, lon) pairs.
        :return:
        """
        output = []
        with self.conn.cursor() as cur:
            # First 'noptions' routes in norigins * ndests.
            origin_dest_options = itertools.islice(
                itertools.product(enumerate(origins), enumerate(dests)),
                noptions)

            for (oi, origin), (di, dest) in origin_dest_options:
                cur.execute(
                    'SELECT * FROM pathFromNearestKnownPoints(%s,%s,%s,%s)',
                    (*reversed(origin), *reversed(dest)))
                linestring, length = cur.fetchone()
                output.append(RouteResult(
                    json=linestring,
                    score=0,
                    length=length,
                    origin_idx=oi,
                    dest_idx=di
                ))
        return output


def main():
    origins = [(34.140003, -118.122775),  # Avery
               (34.136872, -118.122910),  # Olive walk
               (34.137038, -118.127548),  # Kerchoff?
               ]
    dests = [(34.143209, -118.118393),  # PCC
             (34.147672, -118.144328),  # Pasadena city hall
             ]
    router = Point2PointRouter(db_conn.connPool.getconn())
    # pprint(router.make_route(origins, dests, 4))
    routes = router.make_route(origins, dests, 4)
    for route in routes:
        print(route)

if __name__ == '__main__':
    import db_conn

    main()
