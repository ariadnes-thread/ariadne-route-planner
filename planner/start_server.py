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

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

logger = logging.getLogger(__name__)


class RoutePlanner(planner_pb2_grpc.RoutePlannerServicer):

    def PlanRoute(self, jsonrequest, context):
        req = json.loads(jsonrequest.jsonData)
        logger.info('Received PlanRoute() call. Data: %s', req)

        try:
            # Parse required params
            # Convert origins and dests to lists of tuples
            origins = [(o['latitude'], o['longitude'])
                       for o in req.pop('origins')]
            dests = [(d['latitude'], d['longitude'])
                     for d in req.pop('dests')]
            noptions = req.pop('noptions')

            # Neither origins nor dests can be empty
            if not (origins and dests):
                raise ValueError('Origins or dests cannot be empty')

            # Make routes
            with connPool.getconn() as conn:
                if 'desired_dist' not in req:
                    router = Point2PointRouter(conn)

                else:
                    router = OrienteeringRouter(conn)

                routes = router.make_route(origins, dests, noptions, **req)

            connPool.putconn(conn)

            # # Convert RouteResults into objects that can be serialized by
            # # json.dumps. NamedTuples are serialized as tuples, which is not
            # # what we want.
            # routeobjs = [
            #     {
            #         'json': json.loads(r.route),
            #         'score': r.score,
            #         'length': r.length
            #     } for r in routes]
            # jsonreply_obj = {'routes': routeobjs}

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
