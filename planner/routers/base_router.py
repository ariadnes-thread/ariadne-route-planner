from typing import NamedTuple


class RouteResult(NamedTuple):
    route: str
    score: float
    length: float
