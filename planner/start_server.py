from concurrent import futures
import time
import json
import grpc

import planner_pb2
import planner_pb2_grpc
from orienteering_router import OrienteeringRouter

from db_conn import connPool

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class RoutePlanner(planner_pb2_grpc.RoutePlannerServicer):

    def PlanRoute(self, request, context):
        data = {}
        constraints = json.loads(request.jsonData)

        print('Received PlanRoute() call. Constraints:')
        print(constraints)

        # Lat/lng of origin
        origin = constraints.get('origin')
        destination = constraints.get('destination')
        length = constraints.get('length')
        if origin is not None and destination is not None:
            orig_lat = float(origin.get('latitude'))
            orig_lng = float(origin.get('longitude'))
            dest_lat = float(destination.get('latitude'))
            dest_lng = float(destination.get('longitude'))
            conn = connPool.getconn()

            # TODO: Get length from frontend
            if length is None:
                length = 6000  # Maximum length of path in meters
            length = int(length)
            with open('config.json') as f:
                config = json.load(f)
            router = OrienteeringRouter(config['gmapsApiKey'], conn)
            route_geometry = json.loads(router.make_route((orig_lat, orig_lng), (dest_lat, dest_lng), length)[0])

            # Old algo
            # cur = conn.cursor()
            # cur.execute('SELECT * FROM pathFromNearestKnownPoints(%s,%s,%s,%s)', (orig_lng, orig_lat, dest_lng, dest_lat))
            # linestring, length = cur.fetchone()
            # route_geometry = json.loads(linestring)

            connPool.putconn(conn)
            data['route'] = route_geometry
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
