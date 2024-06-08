from enum import Enum
from ..agent import Agent


class Action(Enum):
    MoveUp, MoveDown, MoveLeft, MoveRight, Place, Take, Reset = range(7)


class Cleaner(Agent):
    def __init__(self, id) -> None:
        super().__init__(id)
        self.position = None
        self.start_posi = None

    def _execute(self, action, **kwargs):
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
            self.position = self.start_posi = kwargs["position"]
        elif action == Action.Take:
            self.position = self.start_posi = None
            self.is_alive = False
        elif action == Action.Reset:
            self.position = self.start_posi
        else:
            raise ValueError(f"Unknown action {action}")

        return self.position, old_postition

    def terminate(self):
        if self.is_alive:
            self.execute(Action.Take)
        super().terminate()

    def make_decision(self, *args, **kwargs):
        pass
