from .maze import *
import networkx as nx
import numpy as np
from .cleaner import *
from pubsub import pub
from ..config import SOLVER_TOPIC, AGENT_RESPONSED, MAZE_UPDATED


class CleanMazeEnv:
    def __init__(self, w, h, n_agents, maze_generator=None) -> None:
        self.w, self.h = w, h
        self.n_agents = n_agents
        self.maze_gen = maze_generator if maze_generator else GrowingTree()
        required_keys = ["wall", "cell", "visited"] + [
            f"agent{i+1}" for i in range(n_agents)
        ]
        symbol_map = self.maze_gen.symbol_map
        if symbol_map is None:
            symbol_map = {"wall": -2, "visited": -1, "cell": 0}
            for i in range(1, n_agents + 1):
                symbol_map[f"agent{i}"] = i
            self.maze_gen.symbol_map = symbol_map
        else:
            if not all(key in symbol_map for key in required_keys):
                raise ValueError(
                    f"symbol_map must contain the keys: {', '.join(required_keys)}"
                )
            if len(set(symbol_map.values())) != len(symbol_map.values()):
                raise ValueError("All values in symbol_map must be unique")
        self.symbol_map = symbol_map
        self.agents = None
        self.reset(True)
        pub.subscribe(self._update_maze, AGENT_RESPONSED)

    def _update_maze(self, id, ret):
        new_pos = self.agents[id - 1].position
        symbol_map = self.symbol_map
        if new_pos is None:
            if self.agents[id - 1].is_alive:
                raise RuntimeError(
                    f"The agent{id} is alive but goes to a None position"
                )
        else:
            if self.maze[*new_pos] == symbol_map["wall"]:
                raise RuntimeError(
                    f"The agent{id} is located at {new_pos} and hits the wall."
                )
            if self.maze[*new_pos] not in [symbol_map["visited"], symbol_map["cell"]]:
                raise RuntimeError(
                    f"The agent{id} and agent{self.maze[*new_pos]} collide at {new_pos}"
                )
            self.maze[*new_pos] = symbol_map[f"agent{id}"]
        if ret is not None:
            self.maze[*ret] = symbol_map["visited"]
        pub.sendMessage(MAZE_UPDATED)

    def reset(self, regenerate=False):
        if regenerate:
            self.cache_maze = self.maze_gen(self.w, self.h)
        policy = None
        if self.agents is not None:
            policy = self.agents[0].policy
            for agent in self.agents:
                self.dispatch(agent.id, Action.Take)
        self.maze = self.cache_maze.copy()
        self.agents = [Cleaner(i + 1, policy) for i in range(self.n_agents)]

    def dispatch(self, id, action: Action, **kwargs):
        pub.sendMessage(SOLVER_TOPIC, id=id, kwargs={"action": action, **kwargs})

    def to_graph(self):
        g = nx.Graph()
        if self.maze is None:
            return g

        visited = np.zeros_like(self.maze, dtype=bool)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        n_row, n_col = self.maze.shape
        symbol_map = self.symbol_map

        def dfs(x, y):
            visited[x, y] = True
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < n_row
                    and 0 <= ny < n_col
                    and self.maze[nx, ny]
                    in [
                        symbol_map["cell"],
                        symbol_map["visited"],
                    ]
                    and not visited[nx, ny]
                ):
                    g.add_node(
                        (nx, ny), visited=self.maze[x, y] == symbol_map["visited"]
                    )
                    g.add_edge((x, y), (nx, ny))
                    dfs(nx, ny)

        for r in range(n_row):
            for c in range(n_col):
                if (
                    self.maze[r, c]
                    in [
                        symbol_map["cell"],
                        symbol_map["visited"],
                    ]
                    and not visited[r, c]
                ):
                    g.add_node((r, c), visited=self.maze[r, c] == symbol_map["visited"])
                    dfs(r, c)

        return g
