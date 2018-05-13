import abc
from typing import *


class RouteResult(NamedTuple):
    route: str
    score: float
    length: float


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
