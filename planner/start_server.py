import logging
from concurrent import futures
import time
import json
import grpc


import planner_pb2
import planner_pb2_grpc

from db_conn import connPool
from routers.base_router import RouteEncoder
from routers.orienteering_router import OrienteeringRouter
from routers.point2point_router import Point2PointRouter
from routers.dist_edge_prefs_router import DistEdgePrefsRouter

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

logger = logging.getLogger(__name__)


class RoutePlanner(planner_pb2_grpc.RoutePlannerServicer):

    def PlanRoute(self, jsonrequest, context):
        req = json.loads(jsonrequest.jsonData)
        logger.info('Received PlanRoute() call. Data: %s', req)

        try:
            # Convert origin and dest to tuples
            origin = req.pop('origin')
            origin = (origin['latitude'], origin['longitude'])
            dest = req.pop('dest')
            dest = (dest['latitude'], dest['longitude'])

            # Make routes
            conn = connPool.getconn()
            try:
                with conn:
                    if 'desired_dist' not in req:
                        # If POIs not provided
                        if 'poi_prefs' not in req or req['poi_prefs'] == {}:
                            router = Point2PointRouter(conn)
                        else:
                            router = Point2PointRouter(conn) # TODO: change, once the POI's-on-the-way router is added
                    else:
                        if 'poi_prefs' not in req or req['poi_prefs'] == {}:
                            router = DistEdgePrefsRouter(conn)
                        else:
                            router = OrienteeringRouter(conn)

                    routes = router.make_route(origin, dest, **req)
            finally:
                connPool.putconn(conn)

            # jsonData is not the JS object, but its string
            jsonData = RouteEncoder().encode({'routes': routes})

            return planner_pb2.JsonReply(jsonData=jsonData)

        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(e)
            return planner_pb2.JsonReply()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    planner_pb2_grpc.add_RoutePlannerServicer_to_server(RoutePlanner(), server)
    server.add_insecure_port('[::]:1235')
    logger.info('Starting server')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    serve()
