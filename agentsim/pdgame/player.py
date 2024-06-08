from collections import defaultdict
from enum import Enum
from ..agent import Agent
from ..config import register
import numpy as np
import random


class Action(Enum):
    Cooperate, Defect, Reset = range(3)


class Player(Agent):
    def __init__(self, id) -> None:
        super().__init__(id)
        self.reset()

    def _execute(self, action, **kwargs):
        if action == Action.Reset:
            self.reset()
        return self.coins

    def reset(self):
        self.coins = 0

    def make_decision(self, *args, **kwargs):
        opponent_action, last_reward = args
        self.coins += last_reward

    def terminate(self):
        self.reset()


@register.player("copycat")
class Copycat(Player):

    def __init__(self, id) -> None:
        super().__init__(id)

    def reset(self):
        super().reset()
        self._last_opponent_aciton = Action.Cooperate

    def make_decision(self, *args, **kwargs):
        super().make_decision(*args, **kwargs)
        opponent_action, last_reward = args
        ret = self._last_opponent_aciton
        self._last_opponent_aciton = opponent_action
        return ret


@register.player("qlearner")
class QLearner(Player):
    def __init__(self, id, alpha=0.1, gamma=0.9, epsilon=0.1):
        super().__init__(id)
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: np.zeros(len(Action)))
        self.last_state = None
        self.last_action = None

    def reset(self):
        super().reset()
        self.last_state = None
        self.last_action = None

    def make_decision(self, *args, **kwargs):
        super().make_decision(*args, **kwargs)
        opponent_action, last_reward = args
        state = (opponent_action,)
        if random.uniform(0, 1) < self.epsilon:
            action = random.choice(list(Action))
        else:
            action = Action(np.argmax(self.q_table[state]))

        if self.last_state is not None and self.last_action is not None:
            self.update_q_table(self.last_state, self.last_action, last_reward, state)

        self.last_state = state
        self.last_action = action
        return action

    def update_q_table(self, state, action, reward, next_state):
        current_q = self.q_table[state][action.value]
        max_future_q = np.max(self.q_table[next_state])
        new_q = (1 - self.alpha) * current_q + self.alpha * (
            reward + self.gamma * max_future_q
        )
        self.q_table[state][action.value] = new_q


@register.player("cooperator")
class Cooperator(Player):
    def __init__(self, id) -> None:
        super().__init__(id)

    def make_decision(self, *args, **kwargs):
        super().make_decision(*args, **kwargs)
        return Action.Cooperate


@register.player("fraud")
class Fraud(Player):
    def __init__(self, id) -> None:
        super().__init__(id)

    def make_decision(self, *args, **kwargs):
        super().make_decision(*args, **kwargs)
        return Action.Defect


@register.player("grudger")
class Grudger(Player):
    def __init__(self, id) -> None:
        super().__init__(id)

    def reset(self):
        super().reset()
        self._opponent_cheated = False

    def make_decision(self, *args, **kwargs):
        super().make_decision(*args, **kwargs)
        if args == Action.Defect:
            self._opponent_cheated = True
        return Action.Cooperate if not self._opponent_cheated else Action.Defect
