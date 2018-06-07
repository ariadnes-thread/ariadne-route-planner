import abc
import json
import math
from typing import *


class PoiResult:
    def __init__(self, location: Tuple[float, float], name: str, type: str,
                 length_of_leg: float):
        """
        A POI along a route.
        """
        self.location = location
        self.name = name
        self.type = type
        self.length_of_leg = length_of_leg


class RouteResult:
    def __init__(self, geojson: str, score: float, length: float, elevationData,
                 pois: List[PoiResult]):
        """
        Create a route result.
        :param geojson: GeoJSON of route.
        :param score: Score of route. It doesn't have meaning alone but can be
                      compared with other routes.
        :param length: Meters.
        """
        self.geojson = geojson
        self.score = score
        self.length = length
        self.elevationData = elevationData
        self.pois = pois

    def __str__(self):
        return str(vars(self))


class RouteEncoder(json.JSONEncoder):
    """JSON encoder that can encode RouteResults."""

    def default(self, o):
        """Tries to return a serializable object for o."""
        if isinstance(o, RouteResult):
            return {
                'geojson': json.loads(o.geojson),
                'score': o.score,
                'length': o.length,
                'elevationData': o.elevationData,
                'pois': o.pois
            }

        elif isinstance(o, PoiResult):
            return {
                'location': {'latitude': o.location[0], 'longitude': o.location[1]},
                'name': o.name,
                'type': o.type,
                'length_of_leg': o.length_of_leg
            }

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


class BaseRouter(abc.ABC):

    @abc.abstractmethod
    def make_route(self, origin: Tuple[float, float], dest: Tuple[float, float],
                   **kwargs) -> RouteResult:
        """
        Make a route.
        :param origin: lat/lon of origin.
        :param dest: lat/lon of destination.
        :param kwargs: Additional kwargs
        :return: Resulting route.
        """
        raise NotImplementedError



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

