from sklearn.cluster import SpectralClustering
import networkx as nx
from ..cleaner import Action


class CentralizedSolver:
    """
    The `CentralizedSolver` implements a centralized collaborative solver. Its algorithmic process is as follows:

    1. Perform spectral decomposition on the graph composed of feasible paths in the maze, resulting in `n_agents` subgraphs.
    2. For each subgraph, arbitrarily select a leaf node `u`, then use breadth-first search (BFS) to find the node `v` that is the furthest from `u`, and set `v` as the starting node.
    3. Start from `v` to traverse the entire graph, preprocessing the height of each node. The height here is defined as the maximum height of all child nodes plus one. Specifically, the height of a leaf node is 0.
    4. Continue traversing the entire graph from `v`. When a node `w` has a degree greater than 2 (indicating multiple branches), prioritize the branch with the smaller height.
    """

    def __init__(self, maze_graph, n_agents, keep_dead_agents=False) -> None:
        self.n_agents = n_agents
        self.subgraphs = self._spectral_partition(maze_graph)
        self.keep_dead_agents = keep_dead_agents

    def solve(self):
        # find start node of each subgraph
        msgs, action_gen = [], []
        for i, g in enumerate(self.subgraphs):
            for node, deg in g.degree():
                if deg == 1:  # bfs from a leaf node to obtain diameter of the tree
                    path_lengths = nx.single_source_shortest_path_length(g, node)
                    start_node = max(path_lengths, key=path_lengths.get)
                    action_gen.append(self._action_gen(g, start_node))
                    msgs.append(
                        self._pack_msg(
                            i + 1,
                            Action.Place,
                            position=start_node,
                        )
                    )
                    break
        yield msgs

        solved = [False] * self.n_agents
        while not all(solved):
            msgs.clear()
            for i, g in enumerate(self.subgraphs):
                if not solved[i]:
                    try:
                        action = next(action_gen[i])
                    except StopIteration:
                        action = Action.Take
                        solved[i] = True
                        if self.keep_dead_agents:
                            continue
                    msgs.append(self._pack_msg(i + 1, action))
            yield msgs

    def _spectral_partition(self, graph):
        n_agents = self.n_agents
        adjacency_matrix = nx.to_numpy_array(graph)
        sc = SpectralClustering(
            n_clusters=n_agents,
            affinity="precomputed",
            n_init=100,
            assign_labels="discretize",
        )
        sc.fit(adjacency_matrix)

        return [
            graph.subgraph(
                [node for node, label in zip(graph.nodes(), sc.labels_) if label == i]
            )
            for i in range(n_agents)
        ]

    def _pack_msg(self, id, action, **kwargs):
        return {"id": id, "action": action, **kwargs}

    def _action_gen(self, g, start_node):
        dir_act_map = {
            (0, 1): Action.MoveRight,
            (1, 0): Action.MoveDown,
            (0, -1): Action.MoveLeft,
            (-1, 0): Action.MoveUp,
        }

        # dfs graph g to get depth of each node
        depths = {}
        stack = [(start_node, None, 0)]
        while stack:
            node, parent, state = stack.pop()
            if state == 0:
                depths[node] = 0
                stack.append((node, parent, 1))
                for nbr in g.neighbors(node):
                    if nbr != parent:
                        stack.append((nbr, node, 0))
            elif state == 1:
                for nbr in g.neighbors(node):
                    if nbr != parent:
                        depths[node] = max(depths[node], depths[nbr] + 1)

        # dfs to generate actions
        visited = set()
        stack = [
            (start_node, iter(sorted(g.neighbors(start_node), key=lambda x: depths[x])))
        ]

        while stack:
            node, nbrs = stack[-1]
            if node not in visited:
                visited.add(node)

            try:
                nbr = next(nbrs)
                if nbr not in visited:
                    yield dir_act_map[tuple(a - b for a, b in zip(nbr, node))]
                    stack.append(
                        (
                            nbr,
                            iter(sorted(g.neighbors(nbr), key=lambda x: depths[x])),
                        )
                    )
            except StopIteration:
                stack.pop()
                if len(visited) == g.number_of_nodes():
                    return
                if stack:
                    parent_node = stack[-1][0]
                    yield dir_act_map[tuple(a - b for a, b in zip(parent_node, node))]
