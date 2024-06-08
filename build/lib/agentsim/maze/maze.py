import numpy as np
from random import randrange, shuffle, choice


class GrowingTree:
    def __init__(self, symbol_map=None, backtrack_ratio=1.0):
        self.backtrack_ratio = backtrack_ratio
        self.symbol_map = symbol_map

    def __call__(self, h, w):
        assert self.symbol_map is not None
        H, W = 2 * h + 1, 2 * w + 1
        grid = np.full((H, W), self.symbol_map["wall"], dtype=int)
        start_pos = (randrange(1, H, 2), randrange(1, W, 2))
        grid[start_pos] = self.symbol_map["cell"]
        active = [start_pos]

        def find_neighbors(r, c, symbol):
            neighbors = []
            directions = [(r - 2, c), (r + 2, c), (r, c - 2), (r, c + 2)]
            for dr, dc in directions:
                if 0 < dr < H - 1 and 0 < dc < W - 1 and grid[dr, dc] == symbol:
                    neighbors.append((dr, dc))
            shuffle(neighbors)
            return neighbors

        while active:
            current = (
                active[-1]
                if np.random.rand() < self.backtrack_ratio
                else choice(active)
            )
            neighbors = find_neighbors(*current, self.symbol_map["wall"])
            if neighbors:
                next_cell = choice(neighbors)
                active.append(next_cell)
                grid[next_cell] = self.symbol_map["cell"]
                grid[
                    (current[0] + next_cell[0]) // 2, (current[1] + next_cell[1]) // 2
                ] = self.symbol_map["cell"]
            else:
                active.remove(current)
        return grid


class Kruskal:
    def __init__(self, symbol_map=None):
        self.symbol_map = symbol_map

    def __call__(self, h, w):
        assert self.symbol_map is not None
        H, W = 2 * h + 1, 2 * w + 1
        grid = np.full((H, W), self.symbol_map["wall"], dtype=np.int8)

        parent = {}
        rank = {}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            root1 = find(x)
            root2 = find(y)
            if root1 != root2:
                if rank[root1] > rank[root2]:
                    parent[root2] = root1
                elif rank[root1] < rank[root2]:
                    parent[root1] = root2
                else:
                    parent[root2] = root1
                    rank[root1] += 1

        for row in range(1, H, 2):
            for col in range(1, W, 2):
                cell = (row, col)
                parent[cell] = cell
                rank[cell] = 0
                grid[row, col] = self.symbol_map["cell"]

        edges = []
        for row in range(1, H, 2):
            for col in range(1, W, 2):
                if row < H - 2:
                    edges.append(((row, col), (row + 2, col)))
                if col < W - 2:
                    edges.append(((row, col), (row, col + 2)))

        shuffle(edges)

        while edges:
            (cell1, cell2) = edges.pop()
            if find(cell1) != find(cell2):
                union(cell1, cell2)
                grid[(cell1[0] + cell2[0]) // 2, (cell1[1] + cell2[1]) // 2] = (
                    self.symbol_map["cell"]
                )

        return grid


class RecursiveDivision:
    VERTICAL = 0
    HORIZONTAL = 1

    def __init__(self, symbol_map=None):
        self.symbol_map = symbol_map

    def __call__(self, h, w):
        assert self.symbol_map is not None
        H, W = 2 * h + 1, 2 * w + 1
        grid = np.full((H, W), self.symbol_map["cell"], dtype=np.int8)
        grid[0, :] = grid[-1, :] = self.symbol_map["wall"]
        grid[:, 0] = grid[:, -1] = self.symbol_map["wall"]

        def divide(min_y, max_y, min_x, max_x):
            height = max_y - min_y + 1
            width = max_x - min_x + 1

            if height <= 1 or width <= 1:
                return

            if width < height:
                cut_direction = self.HORIZONTAL
            elif width > height:
                cut_direction = self.VERTICAL
            else:
                if width == 2:
                    return
                cut_direction = randrange(2)

            cut_length = (height, width)[(cut_direction + 1) % 2]
            if cut_length < 3:
                return

            cut_pos = randrange(1, cut_length, 2)
            door_pos = randrange(0, (height, width)[cut_direction], 2)

            if cut_direction == self.VERTICAL:
                for row in range(min_y, max_y + 1):
                    grid[row, min_x + cut_pos] = self.symbol_map["wall"]
                grid[min_y + door_pos, min_x + cut_pos] = self.symbol_map["cell"]

                divide(min_y, max_y, min_x, min_x + cut_pos - 1)
                divide(min_y, max_y, min_x + cut_pos + 1, max_x)
            else:
                for col in range(min_x, max_x + 1):
                    grid[min_y + cut_pos, col] = self.symbol_map["wall"]
                grid[min_y + cut_pos, min_x + door_pos] = self.symbol_map["cell"]

                divide(min_y, min_y + cut_pos - 1, min_x, max_x)
                divide(min_y + cut_pos + 1, max_y, min_x, max_x)

        divide(1, H - 2, 1, W - 2)
        return grid
