from pubsub import pub
from ..config import SOLVER_TOPIC, AGENT_RESPONSED, ENV_UPDATED, register
from ..simenv import SimEnv
from .player import Action


class PDGameEnv(SimEnv):
    def __init__(self, reward_matrix, role_num_dict, n_replace, n_round=10) -> None:
        """
        Initialize the PDGameEnv environment.

        Parameters:
            reward_matrix (list): A 2x2x2 matrix representing the rewards between two players in different policies.
                                  Example: [[[3, 3], [0, 5]], [[5, 0], [1, 1]]]
                                  Where reward_matrix[0][0] represents the rewards when both cooperate,
                                  reward_matrix[0][1] when the first player cooperates and the second defects,
                                  reward_matrix[1][0] when the first player defects and the second cooperates,
                                  and reward_matrix[1][1] when both defect.

            role_num_dict (dict): A dictionary mapping the names of player types to the number of agents of that type.
                                  Example: {"copycat": 2, "defector": 2}
                                  This creates 2 'copycat' agents and 2 'defector' agents.

            n_replace (int): The number of agents to be replaced in the evolution process.
                             Example: 1 means one agent with the lowest coins will be replaced by a new agent of the best type.

            n_round (int, optional): The number of rounds each pair of agents will play in one step. Default is 10.

        Raises:
            ValueError: If the reward matrix size is incorrect.
        """
        super().__init__()
        self.agents = []
        self.agent_id_map = {}
        agent_id = 0
        for name, num in role_num_dict.items():
            for _ in range(num):
                agent = register.player_registry[name](id=agent_id)
                self.agents.append(agent)
                self.agent_id_map[agent_id] = agent
                agent_id += 1

        if (
            len(reward_matrix) != 2
            or len(reward_matrix[0]) != 2
            or len(reward_matrix[0][0]) != 2
        ):
            raise ValueError(
                "Wrong reward matrix size. It should be a 2x2x2 matrix which represents the rewards between two players in different two policies."
            )

        self.reward_matrix = reward_matrix
        self.n_round = n_round
        self.n_replace = n_replace
        self.reset()

    @property
    def n_agents(self):
        return len(self.agents)

    def update(self, id, ret):
        pass

    def step(self):
        pair_index = self._current_round % (
            len(self._matching_pairs) // (self.n_agents // 2)
        )
        round_pairs = self._matching_pairs[
            pair_index * (self.n_agents // 2) : (pair_index + 1) * (self.n_agents // 2)
        ]

        for agent1_id, agent2_id in round_pairs:
            agent1 = self.agent_id_map[agent1_id]
            agent2 = self.agent_id_map[agent2_id]
            self.on_round[agent1_id] = agent2_id
            self.on_round[agent2_id] = agent1_id

            last_action1 = Action.Cooperate
            last_action2 = Action.Cooperate
            last_reward1 = 0
            last_reward2 = 0

            for _ in range(self.n_round):
                action1 = agent1.make_decision(last_action2, last_reward1)
                action2 = agent2.make_decision(last_action1, last_reward2)

                if action1 == Action.Cooperate and action2 == Action.Cooperate:
                    reward1, reward2 = self.reward_matrix[0][0]
                elif action1 == Action.Cooperate and action2 == Action.Defect:
                    reward1, reward2 = self.reward_matrix[0][1]
                elif action1 == Action.Defect and action2 == Action.Cooperate:
                    reward1, reward2 = self.reward_matrix[1][0]
                else:
                    reward1, reward2 = self.reward_matrix[1][1]

                pub.sendMessage(
                    SOLVER_TOPIC,
                    id=agent1_id,
                    action=action1,
                    kwargs={},
                )
                pub.sendMessage(
                    SOLVER_TOPIC,
                    id=agent2_id,
                    action=action2,
                    kwargs={},
                )

                last_action1, last_action2 = action1, action2
                last_reward1, last_reward2 = reward1, reward2

        self._current_round += 1
        if (
            self._current_round > 0
            and self._current_round
            % (len(self._matching_pairs) // (self.n_agents // 2))
            == 0
        ):
            self._evolution()
        return True

    def reset(self):
        self.on_round = {}
        self._current_round = 0
        for agent in self.agents:
            agent.execute(Action.Reset)
        self._matching_pairs = []
        for i in range(self.n_agents):
            for j in range(i + 1, self.n_agents):
                self._matching_pairs.append((self.agents[i].id, self.agents[j].id))

    def _evolution(self):
        sorted_agents = sorted(self.agents, key=lambda x: x.coins)
        best_agent_type = sorted_agents[-1].__class__
        removed_agents = []
        new_agent_ids = []
        for i in range(self.n_replace):
            agent_to_remove = sorted_agents[i]
            removed_agents.append((agent_to_remove.id, agent_to_remove.type))
            agent_to_remove.terminate()
            self.agents.remove(agent_to_remove)
            del self.agent_id_map[agent_to_remove.id]
            if agent_to_remove.id in self.on_round:
                opponent_id = self.on_round.pop(agent_to_remove.id)
                if opponent_id in self.on_round:
                    del self.on_round[opponent_id]

            new_agent_id = max(self.agent_id_map.keys()) + 1
            new_agent = best_agent_type(id=new_agent_id)
            self.agents.append(new_agent)
            new_agent_ids.append(new_agent_id)
            self.agent_id_map[new_agent_id] = new_agent

        self.reset()
        pub.sendMessage(
            ENV_UPDATED,
            removed_agents=removed_agents,
            new_agent_ids=new_agent_ids,
        )
