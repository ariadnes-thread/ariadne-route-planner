from routers.base_router import BaseRouter


class Point2PointRouter(BaseRouter):
    def __init__(self, conn):
        self.conn = conn

    def make_route(self, origin, destination, *args, **kwargs):
        with self.conn.cursor() as cur:
            cur.execute('SELECT * FROM pathFromNearestKnownPoints(%s,%s,%s,%s)',
                        (*origin[::-1], *destination[::-1]))
            linestring, length = cur.fetchone()
            return linestring, length
