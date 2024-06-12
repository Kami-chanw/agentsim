from agentsim.pdgame import PDGameEnv, PDGameWindow
import pyglet

reward_matrix = [[(2, 2), (-1, 3)], [(3, -1), (0, 0)]]

role_num_dict = {"copycat": 10, "cooperator": 5, "fraud": 5, "grudger": 5}
env = PDGameEnv(reward_matrix, role_num_dict, 5)
wnd = PDGameWindow(env)
pyglet.app.run()
