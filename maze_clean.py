from agentsim.maze import MazeWindow, MazeCleanEnv
import pyglet

env = MazeCleanEnv(10, 10, 5)
window = MazeWindow(
    env,
    width=1000,
    height=800,
    caption="Maze Cleaner Simulation",
    solve_interval=0.5,
)

pyglet.app.run()
