import pyglet
from pyglet.window import key


class WindowBase(pyglet.window.Window):
    def __init__(self, env, solve_interval=0.1, run_on_show=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = env

        pyglet.gl.glClearColor(0.96, 0.96, 0.96, 1)
        self._batch = pyglet.graphics.Batch()
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self.pause = not run_on_show

        def update(dt):
            if not self.pause and any(agent.is_alive for agent in self.env.agents):
                if self.env.step():
                    self._update_batch()
                else:
                    pyglet.clock.unschedule(update)

        pyglet.clock.schedule_interval(update, solve_interval)

    def _init_batch(self):
        """
        Initialize elements used to draw. Most of the elements should be initialized in this method.
        """
        raise NotImplementedError("This method should be implemented by derived class")

    def _update_batch(self):
        """
        Update elements in batch. This method will be called periodically after environment updated.
        """
        raise NotImplementedError("This method should be implemented by derived class")

    def _draw_batch(self):
        """
        Draw elements in batch. If the derived class has other batches to draw, it can override this method to decide the order of rendering.
        """
        self._batch.draw()

    def on_draw(self):
        self.clear()
        self._draw_batch()

    def on_close(self):
        for agent in self.env.agents:
            agent.terminate()
        super().on_close()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.pause = not self.pause
        elif symbol == key.ESCAPE:
            self.close()
