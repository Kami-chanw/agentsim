from sklearn.cluster import SpectralClustering
from .maze import GrowingTree
import networkx as nx
import numpy as np
from .solve import search
from ..agent import AgentCrashed
from pubsub import pub
from ..config import SOLVER_TOPIC, AGENT_RESPONSED, ENV_UPDATED, register
from ..simenv import SimEnv


class MazeCleanEnv(SimEnv):
    def __init__(
        self,
        w,
        h,
        n_agents,
        n_subgraphs=None,
        maze_generator=None,
        method="search",
        **kwargs,
    ) -> None:
        """
        Initialize the MazeCleanEnv environment.

        Parameters:
            `w` (int):
                The width of the maze.
            `h` (int):
                The height of the maze.
            `n_agents` (int):
                The number of agents in the maze.
            `n_subgraphs` (int, optional):
                The number of subgraphs to partition the maze into. Defaults to the number of agents.
            `maze_generator` (callable, optional):
                A callable object to generate the maze. Defaults to GrowingTree.
            `method` (str, optional):
                The method used to clean the maze. Supported methods are "IPPO" and "search". Defaults to "search".
            **kwParameters: Additional parameters for initializing the method.

        Raises:
            ValueError: If the symbol map provided by the maze generator is invalid.
        """
        super().__init__()

        self.w, self.h = w, h
        self.maze_gen = maze_generator if maze_generator else GrowingTree()
        symbol_map = self.maze_gen.symbol_map
        if symbol_map is None:
            symbol_map = {
                "wall": -2,
                "visited": -1,
                "cell": 0,
            }
        else:
            required_keys = ["wall", "cell", "visited"]
            if not all(key in symbol_map for key in required_keys):
                raise ValueError(
                    f"symbol_map must contain the keys: {', '.join(required_keys)}"
                )
            if len(set(symbol_map.values())) != len(symbol_map.values()):
                raise ValueError("All values in symbol_map must be unique")
        self.maze_gen.symbol_map = self.symbol_map = symbol_map
        self.digit_symbol_map = {
            v: k for k, v in self.symbol_map.items()
        }  # reset_maze need this attr
        self.cached_maze = None

        self.n_agents = n_agents
        self.n_subgraphs = n_subgraphs if n_subgraphs else n_agents
        self._core = register.maze_solver_registry[method](**kwargs)
        self.reset(True)
        self.symbol_map = {
            **self.maze_gen.symbol_map,
            **{f"agent{agent.id}": i + 1 for i, agent in enumerate(self.agents)},
        }
        self.digit_symbol_map = {v: k for k, v in self.symbol_map.items()}

    def update(self, id, ret):
        new_pos, old_pos = ret
        symbol_map = self.symbol_map
        if new_pos is not None:
            if self.maze[*new_pos] == symbol_map["wall"]:
                raise AgentCrashed(id, f"it hits the wall at {new_pos}.")
            if self.maze[*new_pos] not in [
                symbol_map["visited"],
                symbol_map["cell"],
                symbol_map[f"agent{id}"],
            ]:
                raise AgentCrashed(
                    [id, self.maze[*new_pos]], f"they collide at {new_pos}"
                )
            self.maze[*new_pos] = symbol_map[f"agent{id}"]
            self._graph.nodes[new_pos]["value"] = f"agent{id}"
        if old_pos is not None:
            self.maze[*old_pos] = symbol_map["visited"]
            self._graph.nodes[old_pos]["value"] = "visited"

    def reset(self, regenerate=False):
        """
        Reset the maze environment.

        Parameters:
            regenerate (bool, optional): Whether to regenerate the maze. Defaults to False.

        Resets the maze to its initial state. If regenerate is True or if the cached maze is None,
        a new maze is generated. The maze graph is also updated.
        """
        if regenerate or self.cached_maze is None:
            self.cached_maze = self.maze_gen(self.w, self.h)
        self.maze = self.cached_maze.copy()
        self.maze_graph = self._to_graph()

    @property
    def maze_graph(self):
        return self._graph

    @maze_graph.setter
    def maze_graph(self, graph):
        self._graph = graph
        self._subgraphs = (
            self._spectral_partition(graph, self.n_agents)
            if self.n_subgraphs > 1
            else graph
        )
        self.agents = self._core.get_agents(self.n_agents)

        indeces = [
            i * (self.n_agents // self.n_subgraphs) for i in range(self.n_subgraphs)
        ] + [self.n_agents]
        self._solvers = [
            self._core.solver(g, self.agents[indeces[i] : indeces[i + 1]])
            for i, g in enumerate(self._subgraphs)
        ]

    def step(self):
        is_working = False
        for solver in self._solvers:
            try:
                msgs = next(solver)
            except StopIteration:
                pass
            else:
                is_working = True
                for msg in msgs:
                    id, action = msg.pop("id"), msg.pop("action")
                    pub.sendMessage(SOLVER_TOPIC, id=id, action=action, kwargs=msg)
        return is_working

    def _spectral_partition(self, graph, num):
        adjacency_matrix = nx.to_numpy_array(graph)
        sc = SpectralClustering(
            n_clusters=num,
            affinity="precomputed",
            n_init=100,
            assign_labels="discretize",
        )
        sc.fit(adjacency_matrix)

        return [
            graph.subgraph(
                [node for node, label in zip(graph.nodes(), sc.labels_) if label == i]
            )
            for i in range(num)
        ]

    def _to_graph(self):
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
                    g.add_node((nx, ny), value=self.digit_symbol_map[self.maze[nx, ny]])
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
                    g.add_node((r, c), value=self.digit_symbol_map[self.maze[r, c]])
                    dfs(r, c)

        return g
