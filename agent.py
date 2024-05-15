from pubsub import pub
from .config import SOLVER_TOPIC, AGENT_RESPONSED
from abc import ABC, ABCMeta, abstractmethod


class Agent(ABC):
    __metaclass__ = ABCMeta

    def __init__(self, id, policy=None) -> None:
        self.id = id
        self.policy = policy
        self.is_alive = True
        pub.subscribe(self._do, SOLVER_TOPIC)

    def execute(self, **kwargs):
        self._do(self.id, kwargs)

    @abstractmethod
    def terminate(self):
        pass

    def _do(
        self, id, kwargs
    ):  # **kwargs is not allowed here, PyPubsub doesn't support it as callback
        if id != self.id:
            return
        if self.policy is None:
            raise ValueError(f"The policy of agent {self.id} hasn't set yet.")
        if not self.is_alive:
            raise RuntimeError(f"The current agent{self.id} is unavailable.")
        ret = self.policy(**kwargs)
        pub.sendMessage(AGENT_RESPONSED, id=self.id, ret=ret)
