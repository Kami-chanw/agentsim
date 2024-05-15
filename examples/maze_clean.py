from maze.env import CleanMazeEnv
from maze.visualizer import MazeWindow
from maze.solve import CentralizedSolver
import pyglet

env = CleanMazeEnv(15, 20, 5)
solver = CentralizedSolver(env.to_graph(), env.n_agents)
window = MazeWindow(
    env, solver, width=1000, height=800, caption="Maze Cleaner Simulation"
)

pyglet.app.run()
