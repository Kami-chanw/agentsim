import pyglet
from pyglet.window import key
import threading
import time
from pubsub import pub
from .config import ENV_UPDATED


class WindowBase(pyglet.window.Window):
    def __init__(self, env, solve_interval=0.1, run_on_show=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = env

        # init for solver thread
        self.work_thread = threading.Thread(target=self._solve)
        self.running = run_on_show
        self.pause = not run_on_show
        self.solve_interval = solve_interval

        # init for pyglet
        pyglet.gl.glClearColor(0.96, 0.96, 0.96, 1)
        self._batch = pyglet.graphics.Batch()
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_handler)

    def _init_batch(self):
        """
        Initialize elements used to draw.
        """

    def _draw_batch(self):
        """
        Update elements in batch.
        """

    def on_draw(self):
        self.clear()
        self._draw_batch()

    def _solve(self):
        while self.running and any(agent.is_alive for agent in self.env.agents):
            while self.pause:
                time.sleep(0.1)
            if not self.env.step():
                return
            time.sleep(self.solve_interval)

    def on_show(self):
        self.work_thread.start()

    def on_close(self):
        for agent in self.env.agents:
            agent.terminate()
        self.running = False
        super().on_close()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.pause = not self.pause
        elif symbol == key.ESCAPE:
            self.close()
