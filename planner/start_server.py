import logging
from concurrent import futures
import time
import json
import grpc
from typing import *


import planner_pb2
import planner_pb2_grpc
from routers.base_router import RouteResult
from routers.orienteering_router import OrienteeringRouter

from db_conn import connPool
from routers.point2point_router import Point2PointRouter

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def routeresults_to_json(list: List[RouteResult]) -> str:
    """
    Convert a list of RouteResults to a JSON message ready to send out.
    :param list:
    :return:
    """
    routeobjs = []
    for r in list:
        routeobjs.append({
            'json': json.loads(r.route),
            'score': r.score,
            'length': r.length
        })
    return json.dumps({
        'routes': routeobjs
    })


class RoutePlanner(planner_pb2_grpc.RoutePlannerServicer):

    def PlanRoute(self, request, context):
        req = json.loads(request.jsonData)
        req = req['jsonData']
        print('Received PlanRoute() call. Data:')
        print(req)

        try:
            # Convert origins and dests to lists of tuples
            origins = [(o['latitude'], o['longitude'])
                       for o in req['origins']]
            dests = [(d['latitude'], d['longitude'])
                     for d in req['dests']]

            # Neither can be empty
            if origins == [] or dests == []:
                raise ValueError('Origins or dests cannot be empty')

            with connPool.getconn() as conn:
                if 'desired_dist' not in req:
                    router = Point2PointRouter(conn)
                    routes = router.make_route(origins, dests)

                else:
                    length = req['desired_dist']
                    poi_prefs = req['poi_prefs']
                    edge_prefs = req['edge_prefs']
                    noptions = req['noptions']
                    router = OrienteeringRouter(conn)
                    routes = router.make_route(
                        origins, dests, length, poi_prefs, edge_prefs, noptions)

            connPool.putconn(conn)

            return planner_pb2.JsonReply(jsonData=routeresults_to_json(routes))

        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(e)
            return planner_pb2.JsonReply()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    planner_pb2_grpc.add_RoutePlannerServicer_to_server(RoutePlanner(), server)
    server.add_insecure_port('[::]:1235')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
