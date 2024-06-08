from pubsub import pub
from .config import AGENT_RESPONSED
from abc import ABC, ABCMeta, abstractmethod


class SimEnv(ABC):
    __metaclass__ = ABCMeta

    def __init__(self) -> None:
        pub.subscribe(self.update, AGENT_RESPONSED)

    @abstractmethod
    def update(self, id, ret):
        """
            Update environment base on `ret` which is returned by a specific agent whose id is `id`.
        """
