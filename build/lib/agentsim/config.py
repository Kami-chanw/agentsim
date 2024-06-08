# agents will subscribe it to execute actions
SOLVER_TOPIC = "sovler.action"

# enviroment will subscribe it to update itself
AGENT_RESPONSED = "agent.action.completed"

# window will subscribe it to update gui
ENV_UPDATED = "env.updated"


class register:
    player_registry = {}
    maze_solver_registry = {}

    @staticmethod
    def player(type_name):
        def decorator(cls):
            register.player_registry[type_name] = cls
            cls.type = type_name
            return cls

        return decorator

    @staticmethod
    def maze_solver(type_name):
        def decorator(cls):
            register.maze_solver_registry[type_name] = cls
            return cls

        return decorator
