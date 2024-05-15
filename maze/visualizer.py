import pyglet
from pyglet.window import key
from pyglet import shapes
import threading
import time


class MazeWindow(pyglet.window.Window):
    def __init__(
        self,
        env,
        solver,
        cmap=None,
        solve_interval=0.1,
        run_on_show=True,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs, resizable=True)
        self.env = env
        self.solver = solver

        # init for visualization
        self.cmap = cmap if cmap is not None else {}
        self.cmap.setdefault("wall", (10, 10, 10))
        self.cmap.setdefault("cell", (170, 215, 81))
        self.cmap.setdefault("visited", (255, 255, 255))
        self.cmap.setdefault("agent", (255, 10, 10))
        self.digit_symbol_map = {v: k for k, v in self.env.maze_gen.symbol_map.items()}

        # init for solver thread
        self.solver_thread = threading.Thread(target=self._solve)
        self.running = run_on_show
        self.pause = not run_on_show
        self.solve_interval = solve_interval

        # init for pyglet
        pyglet.gl.glClearColor(0.96, 0.96, 0.96, 1)
        self.batch = pyglet.graphics.Batch()
        self.key_handler = key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self._init_rect()

    def _solve(self):
        gen = self.solver.solve()
        while self.running and any(agent.is_alive for agent in self.env.agents):
            while self.pause:
                time.sleep(0.1)
            try:
                msgs = next(gen)
            except StopIteration:
                return
            for msg in msgs:
                self.env.dispatch(**msg)
            time.sleep(self.solve_interval)

    def _init_rect(self):
        num_rows, num_cols = self.env.maze.shape

        self.grid = [[] for _ in range(num_rows)]
        for row in range(num_rows):
            for col in range(num_cols):
                self.grid[row].append(shapes.Rectangle(1, 1, 1, 1, batch=self.batch))

    def on_draw(self):
        self.clear()
        self.draw_maze()

    def on_show(self):
        self.solver_thread.start()

    def on_close(self):
        for agent in self.env.agents:
            agent.terminate()
        self.running = False
        super().on_close()

    def draw_maze(self):
        num_rows, num_cols = self.env.maze.shape
        cell_size = min(self.width / num_cols, self.height / num_rows)

        offset_x = (self.width - (cell_size * num_cols)) / 2
        offset_y = (self.height - (cell_size * num_rows)) / 2
        # Draw each cell
        for row in range(num_rows):
            for col in range(num_cols):
                cell_type = self.digit_symbol_map[self.env.maze[row][col]]
                if cell_type.startswith("agent"):
                    color = (
                        self.cmap[cell_type]
                        if cell_type in self.cmap
                        else self.cmap["agent"]
                    )
                else:
                    color = self.cmap[cell_type]
                self.grid[row][col].x = col * cell_size + offset_x
                self.grid[row][col].y = (num_rows - row - 1) * cell_size + offset_y
                self.grid[row][col].width = cell_size
                self.grid[row][col].height = cell_size
                self.grid[row][col].color = color

        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.pause = not self.pause
        elif symbol == key.ESCAPE:
            self.close()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.draw_maze()
