import itertools
from pprint import pprint

from routers.base_router import BaseRouter, RouteResult


class Point2PointRouter(BaseRouter):
    def __init__(self, conn):
        self.conn = conn

    def make_route(self, origin, dest, **kwargs):
        """
        :param origin: (lat, lon) of origin
        :param dest: (lat, lon) of dest.
        :return:
        """

        with self.conn.cursor() as cur:
            if 'bbox' in kwargs:
                bbox = kwargs['bbox']
                cur.execute(
                    'SELECT * FROM pathFromNearestKnownPointsBBOX(%s,%s,%s,%s,%s,%s,%s,%s)',
                    (*reversed(origin), *reversed(dest), bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']))
            else:
                cur.execute(
                    'SELECT * FROM pathFromNearestKnownPoints(%s,%s,%s,%s)',
                    (*reversed(origin), *reversed(dest)))
            linestring, length, elevationData = cur.fetchone()
            return RouteResult(
                geojson=linestring,
                score=0,
                length=length,
                elevationData=elevationData,
                pois=[]
            )


def main():
    origin = (34.140003, -118.122775)  # Avery
    dest = (34.147672, -118.144328)  # Pasadena city hall
    router = Point2PointRouter(db_conn.connPool.getconn())
    print(router.make_route(origin, dest))


if __name__ == '__main__':
    import db_conn

    main()
