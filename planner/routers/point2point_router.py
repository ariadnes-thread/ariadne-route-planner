import itertools
import json
import math

from routers.base_router import BaseRouter, RouteResult


def distance(coord1, coord2):
    return math.hypot(coord1[0] - coord2[0], coord1[1] - coord2[1])


def orient_linestring(origin, dest, linestring):
    """Reverse linestring if it is backwards. Return correctly oriented
    linestring."""
    linestring = json.loads(linestring)
    if distance(tuple(reversed(dest)), linestring['coordinates'][0]) \
            < distance(tuple(reversed(origin)), linestring['coordinates'][0]):
        linestring['coordinates'].reverse()
    return json.dumps(linestring)


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

            # HACK: reverse linestring if it is backwards.
            linestring = orient_linestring(origin, dest, linestring)

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
