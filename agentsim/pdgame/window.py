import math
import random
from collections import defaultdict
from pyglet import shapes, text
from pyglet.graphics import Batch
from ..window_base import WindowBase


class PDGameWindow(WindowBase):
    def __init__(
        self,
        env,
        solve_interval=0.1,
        run_on_show=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            env, solve_interval, run_on_show, *args, **kwargs, resizable=True
        )

        # Initialize for visualization
        self._line_batch = Batch()
        self._agent_sprites = {}
        self._agent_colors = {}
        self._legend_labels = {}
        self._legend_icons = {}
        self._lines = []
        self._coin_labels = {}
        self._init_batch()

    def _add_agent(self, agent):
        agent_type = agent.type
        if agent_type not in self._agent_colors:
            self._agent_colors[agent_type] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )

        if agent_type not in self._legend_icons:
            self._add_legend(agent_type)

        color = self._agent_colors[agent_type]
        self._agent_sprites[agent.id] = shapes.Circle(
            0, 0, 20, color=color, batch=self._batch
        )

        self._coin_labels[agent.id] = text.Label(
            str(agent.coins),
            font_size=12,
            color=(0, 0, 0, 255),  # Black color
            anchor_x="center",
            anchor_y="center",
            batch=self._batch,
        )

        # Create connection lines
        for other_agent_id, other_sprite in self._agent_sprites.items():
            if other_agent_id != agent.id:
                line = shapes.Line(
                    0,
                    0,
                    0,
                    0,
                    width=1,
                    color=(211, 211, 211),
                    batch=self._line_batch,  # Use line_batch
                )
                self._lines.append((agent.id, other_agent_id, line))

    def _remove_agent(self, agent_id):
        if agent_id in self._agent_sprites:
            self._agent_sprites[agent_id].delete()
            del self._agent_sprites[agent_id]

        if agent_id in self._coin_labels:
            self._coin_labels[agent_id].delete()
            del self._coin_labels[agent_id]

        agent_type = next(
            (agent.type for agent in self.env.agents if agent.id == agent_id), None
        )

        if agent_type and all(
            agent.type != agent_type
            for agent in self.env.agents
            if agent.id != agent_id
        ):
            self._remove_legend(agent_type)

        # Remove lines associated with the agent
        self._lines = [
            line for line in self._lines if line[0] != agent_id and line[1] != agent_id
        ]

    def _add_legend(self, agent_type):
        color = self._agent_colors[agent_type]
        circle_icon = shapes.Circle(0, 0, 10, color=color, batch=self._batch)
        self._legend_icons[agent_type] = circle_icon

        label = text.Label(
            agent_type,
            font_size=12,
            anchor_x="left",
            anchor_y="center",
            color=(0, 0, 0, 255),
            batch=self._batch,
        )
        self._legend_labels[agent_type] = label

    def _remove_legend(self, agent_type):
        if agent_type in self._legend_icons:
            self._legend_icons[agent_type].delete()
            del self._legend_icons[agent_type]

        if agent_type in self._legend_labels:
            self._legend_labels[agent_type].delete()
            del self._legend_labels[agent_type]

    def _init_batch(self):
        for agent in self.env.agents:
            self._add_agent(agent)

    def _update_batch(self):
        # Synchronize agent sprites with env.agents
        current_agent_ids = set(self._agent_sprites.keys())
        env_agent_ids = set(agent.id for agent in self.env.agents)

        # Remove agents that no longer exist
        for agent_id in current_agent_ids - env_agent_ids:
            self._remove_agent(agent_id)

        # Add new agents
        for agent_id in env_agent_ids - current_agent_ids:
            agent = next(agent for agent in self.env.agents if agent.id == agent_id)
            self._add_agent(agent)

        # Remove legends for agent types that no longer exist
        current_agent_types = set(agent.type for agent in self.env.agents)
        legend_agent_types = set(self._legend_labels.keys())

        for agent_type in legend_agent_types - current_agent_types:
            self._remove_legend(agent_type)

        # Add legends for new agent types
        for agent_type in current_agent_types - legend_agent_types:
            self._add_legend(agent_type)

        window_width, window_height = self.get_size()
        x_offset = window_width - 150
        y_offset = window_height - 50
        y_step = 30

        for i, agent_type in enumerate(self._legend_labels):
            icon = self._legend_icons[agent_type]
            label = self._legend_labels[agent_type]
            y_pos = y_offset - i * y_step
            icon.x = x_offset
            icon.y = y_pos
            label.x = x_offset + 20
            label.y = y_pos

        # Update agent positions in a circular layout
        center_x = window_width // 2
        center_y = window_height // 2
        radius = min(window_width, window_height) // 2 - 50

        # Group agents by type
        agent_groups = defaultdict(list)
        for agent in self.env.agents:
            agent_groups[agent.type].append(agent)

        positions = {}
        total_agents = sum(len(agents) for agents in agent_groups.values())
        angle_step = 360 / total_agents

        current_angle = 0
        for agent_type, agents in agent_groups.items():
            for agent in agents:
                sprite = self._agent_sprites[agent.id]
                radians = current_angle * (math.pi / 180)  # Convert degrees to radians
                sprite.x = center_x + radius * math.cos(radians)
                sprite.y = center_y + radius * math.sin(radians)
                positions[agent.id] = (sprite.x, sprite.y)

                # Update coin label positions
                label = self._coin_labels[agent.id]
                label.x = sprite.x + (center_x - sprite.x) * 0.15  # Move towards center
                label.y = sprite.y + (center_y - sprite.y) * 0.15
                label.text = str(agent.coins)

                current_angle += angle_step

        # Update line positions and colors
        for agent_id1, agent_id2, line in self._lines:
            x1, y1 = positions[agent_id1]
            x2, y2 = positions[agent_id2]
            line.x, line.y, line.x2, line.y2 = (x1, y1, x2, y2)

            if (
                agent_id1 in self.env.on_round
                and self.env.on_round[agent_id1] == agent_id2
            ):
                line.color = (255, 255, 0)  # Light yellow
            else:
                line.color = (211, 211, 211)  # Light gray


    def _draw_batch(self):
        self._line_batch.draw()
        self._batch.draw()
