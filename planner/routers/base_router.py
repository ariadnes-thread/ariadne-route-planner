import abc


class BaseRouter(abc.ABC):

    @abc.abstractmethod
    def make_route(self, origin, destination, *args, **kwargs):
        raise NotImplementedError
