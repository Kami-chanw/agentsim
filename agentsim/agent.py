from pubsub import pub
from .config import SOLVER_TOPIC, AGENT_RESPONSED
from abc import ABC, ABCMeta, abstractmethod


class AgentCrashed(RuntimeError):
    def __init__(self, agent_ids, reason):
        if isinstance(agent_ids, int):
            agent_ids = [agent_ids]
        super().__init__(
            f"Agent(s) {', '.join(map(str, agent_ids))} crashed because " + reason
        )

        self.agent_ids = agent_ids


class Agent(ABC):
    __metaclass__ = ABCMeta

    def __init__(self, id) -> None:
        self.id = id
        self.is_alive = True
        pub.subscribe(self._do, SOLVER_TOPIC)

    def execute(self, action, **kwargs):  # shouldn't override it
        self._do(self.id, action, kwargs)

    @abstractmethod
    def _execute(self, action, **kwargs):
        """
        Execute an action. This method should change internal status of an agent.
        """

    @abstractmethod
    def make_decision(self, *args, **kwargs):
        """
        Make a decision under the policy of itself with environment observation passing by args or kwargs
        """

    def terminate(self):
        self.is_alive = False

    def _do(
        self, id, action, kwargs
    ):  # **kwargs is not allowed here, PyPubsub doesn't support it as callback
        if id != self.id:
            return
        if not self.is_alive:
            raise RuntimeError(f"The current agent{self.id} is unavailable.")
        ret = self._execute(action, **kwargs)
        pub.sendMessage(AGENT_RESPONSED, id=self.id, ret=ret)
