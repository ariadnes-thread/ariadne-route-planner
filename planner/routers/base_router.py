import abc
import json
from typing import *


class RouteResult:
    def __init__(self, geojson: str, score: float, length: float, elevationData):
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

    def __str__(self):
        return str(vars(self))


class RouteEncoder(json.JSONEncoder):
    """JSON encoder that can encode RouteResults."""

    def default(self, o):
        """Tries to return a serializable object for o."""
        if isinstance(o, RouteResult):
            return vars(o)

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
