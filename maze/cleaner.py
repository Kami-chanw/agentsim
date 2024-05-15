from enum import Enum
from ..agent import Agent


class Action(Enum):
    MoveUp, MoveDown, MoveLeft, MoveRight, Place, Take = range(6)


class Cleaner(Agent):
    def __init__(self, id, policy=None) -> None:
        super().__init__(id, policy if policy is not None else self._default_policy)
        self.position = None

    def _default_policy(self, action, **kwargs):
        old_postition = self.position
        if action == Action.MoveUp:
            self.position = (self.position[0] - 1, self.position[1])
        elif action == Action.MoveDown:
            self.position = (self.position[0] + 1, self.position[1])
        elif action == Action.MoveLeft:
            self.position = (self.position[0], self.position[1] - 1)
        elif action == Action.MoveRight:
            self.position = (self.position[0], self.position[1] + 1)
        elif action == Action.Place:
            self.position = kwargs["position"]
        elif action == Action.Take:
            self.position = None
            self.is_alive = False

        return old_postition

    def terminate(self):
        self.policy(Action.Take)
