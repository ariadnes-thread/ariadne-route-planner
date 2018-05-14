import abc
import json
from typing import *


class RouteResult:
    def __init__(self, json: str, score: float, length: float, origin_idx: int,
                 dest_idx: int):
        """
        Create a route result.
        :param json: GeoJSON of route.
        :param score: Score of route. It doesn't have meaning alone but can be
                      compared with other routes.
        :param length: Meters.
        :param origin_idx: Index of origin in original request.
        :param dest_idx: Same
        """
        self.json = json
        self.score = score
        self.length = length
        self.origin_idx = origin_idx
        self.dest_idx = dest_idx

    def __str__(self):
        return "RouteResult(json='{}...', score={}, length={}, origin_idx={}, dest_idx={}".format(
            self.json[:20], self.score, self.length, self.origin_idx, self.dest_idx)


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
    def make_route(self, origins: List[Tuple[float, float]],
                   dests: List[Tuple[float, float]], noptions: int, **kwargs
                   ) -> List[RouteResult]:
        """
        Make routes.
        :param origins: Possible origins.
        :param dests: Possible destinations.
        :param noptions: # route options to return.
        :param kwargs: Additional kwargs
        :return: List of RouteResults.
        """
        raise NotImplementedError
