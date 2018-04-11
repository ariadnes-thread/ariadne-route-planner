from concurrent import futures
import time
import json

import grpc

import planner_pb2
import planner_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class RoutePlanner(planner_pb2_grpc.RoutePlannerServicer):

    def PlanRoute(self, request, context):
        data = {
            'route': [
                {'latitude': 34.140930, 'longitude': -118.129366},
                {'latitude': 34.140947, 'longitude': -118.128010},
                {'latitude': 34.140388, 'longitude': -118.128002},
                {'latitude': 34.139434, 'longitude': -118.122862},
            ]
        }

        json_data = json.dumps(data, separators=(',', ':'))
        return planner_pb2.JsonReply(jsonData=json_data)


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
    serve()
