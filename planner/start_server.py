from concurrent import futures
import time
import json

import grpc

import planner_pb2
import planner_pb2_grpc

from db_conn import connPool

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class RoutePlanner(planner_pb2_grpc.RoutePlannerServicer):

    def PlanRoute(self, request, context):
        data = {}
        constraints = json.loads(request.jsonData)

        # Lat/lng of origin
        origin = constraints.get('origin')
        destination = constraints.get('destination')
        if origin is not None and destination is not None:
            orig_lat = origin.get('latitude')
            orig_lng = origin.get('longitude')
            dest_lat = destination.get('latitude')
            dest_lng = destination.get('longitude')

            conn = connPool.getconn()
            cur = conn.cursor()
            cur.execute('SELECT * FROM pathFromNearestKnownPoints(%s,%s,%s,%s)', (orig_lng, orig_lat, dest_lng, dest_lat))
            linestring, length = cur.fetchone()
            data['route'] = json.loads(linestring)
            data['length'] = length
            json_data = json.dumps(data, separators=(',', ':'))
            return planner_pb2.JsonReply(jsonData=json_data)
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Invalid origin or destination!')
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
    serve()
