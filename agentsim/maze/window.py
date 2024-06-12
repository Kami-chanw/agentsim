from pyglet import shapes
from pyglet.text import Label
from ..window_base import WindowBase
import colorsys, random


class MazeWindow(WindowBase):
    def __init__(
        self,
        env,
        cmap=None,
        solve_interval=0.1,
        run_on_show=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            env, solve_interval, run_on_show, *args, **kwargs, resizable=True
        )

        # init for visualization
        self.cmap = cmap if cmap is not None else {}
        self.cmap.setdefault("wall", (10, 10, 10))
        self.cmap.setdefault("cell", (170, 175, 175))
        self.cmap.setdefault("visited", (255, 255, 255))
        for i, agent in enumerate(env.agents):
            hue = i / env.n_agents
            saturation = 0.7 + 0.3 * random.random()
            lightness = 0.4 + 0.4 * random.random()
            r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
            self.cmap.setdefault(
                f"agent{agent.id}", (int(r * 255), int(g * 255), int(b * 255))
            )

        self._init_batch()

    def _init_batch(self):
        num_rows, num_cols = self.env.maze.shape

        self._grid = [[] for _ in range(num_rows)]
        for row in range(num_rows):
            for col in range(num_cols):
                self._grid[row].append(shapes.Rectangle(1, 1, 1, 1, batch=self._batch))

        self._label = {
            str(agent.id): Label(
                text=str(agent.id),
                anchor_x="center",
                anchor_y="center",
                color=(17, 19, 19, 255),
                dpi=96,
                batch=self._batch,
            )
            for agent in self.env.agents
        }

    def _update_batch(self):
        num_rows, num_cols = self.env.maze.shape
        cell_size = min(self.width / num_cols, self.height / num_rows)

        offset_x = (self.width - (cell_size * num_cols)) / 2
        offset_y = (self.height - (cell_size * num_rows)) / 2
        # Draw each cell
        for row in range(num_rows):
            for col in range(num_cols):
                cell_type = self.env.digit_symbol_map[self.env.maze[row, col]]
                x = col * cell_size + offset_x
                y = (num_rows - row - 1) * cell_size + offset_y
                if cell_type.startswith("agent"):
                    color = (
                        self.cmap[cell_type]
                        if cell_type in self.cmap
                        else self.cmap["agent"]
                    )
                    agent_id = cell_type.split("agent")[1]
                    self._label[agent_id].x = x + cell_size / 2
                    self._label[agent_id].y = y + cell_size / 2
                    self._label[agent_id].font_size = cell_size // 2
                else:
                    color = self.cmap[cell_type]
                self._grid[row][col].x = x
                self._grid[row][col].y = y
                self._grid[row][col].width = cell_size
                self._grid[row][col].height = cell_size
                self._grid[row][col].color = color
