import itertools
from pprint import pprint
from typing import *

from routers.base_router import RouteResult


class Point2PointRouter:
    def __init__(self, conn):
        self.conn = conn

    def make_route(self, origins, dests) -> List[RouteResult]:
        """
        :param origins: (lat, lon) pairs.
        :param dests: (lat, lon) pairs.
        :return:
        """
        output = []
        with self.conn.cursor() as cur:
            for origin, dest in itertools.product(origins, dests):
                cur.execute(
                    'SELECT * FROM pathFromNearestKnownPoints(%s,%s,%s,%s)',
                    (*origin[::-1], *dest[::-1]))
                linestring, length = cur.fetchone()
                output.append(RouteResult(
                    route=linestring,
                    score=0,
                    length=length
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
    pprint(router.make_route(origins, dests))


if __name__ == '__main__':
    import db_conn

    main()
