import networkx as nx
from ..cleaner import Action, Cleaner
from ...config import register

@register.maze_solver("search")
class SearchSolver:
    def __init__(self, **kwargs) -> None:
        pass

    def get_agents(self, n_agents):
        return [Cleaner(i) for i in range(1, n_agents + 1)]


    def solver(self, g, agents):
        if len(agents) != 1:
            raise ValueError(
                "The search algorithm doesn't support multiple agents in a graph."
            )
        for node, deg in g.degree():
            if deg == 1:  # bfs from a leaf node to obtain diameter of the tree
                path_lengths = nx.single_source_shortest_path_length(g, node)
                start_node = max(path_lengths, key=path_lengths.get)
                yield [{"id": agents[0].id, "action": Action.Place, "position": start_node}]
                break

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
            (
                start_node,
                iter(sorted(g.neighbors(start_node), key=lambda x: depths[x])),
            )
        ]

        while stack:
            node, nbrs = stack[-1]
            if node not in visited:
                visited.add(node)

            try:
                nbr = next(nbrs)
                if nbr not in visited:
                    yield [
                        {
                            "id": agents[0].id,
                            "action": dir_act_map[tuple(a - b for a, b in zip(nbr, node))],
                        }
                    ]
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
                    yield [
                        {
                            "id": agents[0].id,
                            "action": dir_act_map[
                                tuple(a - b for a, b in zip(parent_node, node))
                            ],
                        }
                    ]
