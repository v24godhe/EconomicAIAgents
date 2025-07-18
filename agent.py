import json
from llm import get_agent_action
from config import (
    AGENT_CONFIGS,
    ENERGY_LOSS_PER_TURN,
    AGENT_MEMORY_SIZE,
    USE_MULTIMODAL
)
from pygame_visualization import render_grid_for_agent, surface_to_base64

class Agent:
    def __init__(self, name, start_pos=(4, 4)):
        self.name = name
        self.position = start_pos
        # Initialize inventory & energy from config
        from config import INITIAL_INVENTORY, INITIAL_ENERGY
        self.inventory = INITIAL_INVENTORY.copy()
        self.energy = INITIAL_ENERGY
        self.alive = True

        # Load this agent's consumption rates from AGENT_CONFIGS
        self.consumption_rates = AGENT_CONFIGS.get(self.name, {'red': 0, 'green': 0})

        # Histories & counters
        self.actions_taken = []
        self.memory = []
        self.movement_history = []
        self.step_count = 0

    @property
    def type(self):
        """Determine agent 'type' from its highest consumption rate."""
        r, g = self.consumption_rates['red'], self.consumption_rates['green']
        if r > g:
            return 'red'
        elif g > r:
            return 'green'
        else:
            return 'balanced'

    def add_memory(self, observation, action, outcome):
        entry = (
            f"Step {self.step_count}: "
            f"Action: {action} | "
            f"Observation: {observation} | "
            f"Outcome: {outcome} | "
            f"Energy: {self.energy} | "
            f"Inventory: {self.inventory}"
        )
        self.memory.append(entry)
        # keep only last N
        if len(self.memory) > AGENT_MEMORY_SIZE:
            self.memory = self.memory[-AGENT_MEMORY_SIZE:]

    def update_movement_history(self, cell_content, action_taken):
        entry = {
            "step": self.step_count,
            "position": self.position,
            "cell_content": cell_content or "empty",
            "action_taken": action_taken
        }
        self.movement_history.append(entry)
        if len(self.movement_history) > 3:
            self.movement_history.pop(0)
        # save to file
        with open(f"movement_history_{self.name}.txt", "w", encoding="utf-8") as f:
            json.dump(self.movement_history, f, indent=2)

    def get_current_observation(self, environment, all_agents):
        x, y = self.position
        cell = environment.get_cell_content(x, y) or "empty"

        nearby = {'red': 0, 'green': 0, 'agents': 0}
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < environment.size and 0 <= ny < environment.size:
                    c = environment.get_cell_content(nx, ny)
                    if c in nearby:
                        nearby[c] += 1
        for other in all_agents:
            if other.alive and other is not self:
                ox, oy = other.position
                if abs(ox - x) <= 1 and abs(oy - y) <= 1:
                    nearby['agents'] += 1

        return (f"at {self.position}, cell has {cell}, "
                f"nearby {nearby['red']}R {nearby['green']}G {nearby['agents']}A, "
                f"energy {self.energy}")

    def decide_and_act(self, environment, trade_manager=None, all_agents=[]):
        if not self.alive:
            return "inactive"

        self.step_count += 1

        # Lose energy each turn
        self.energy -= ENERGY_LOSS_PER_TURN
        if self.energy <= 0:
            self.alive = False
            return "ran out of energy"

        obs = self.get_current_observation(environment, all_agents)
        x, y = self.position
        cell = environment.get_cell_content(x, y)
        occupied = {a.position for a in all_agents if a.alive and a is not self}

        # Prepare visual if multimodal
        grid_b64 = None
        if USE_MULTIMODAL:
            try:
                import pygame
                pygame.init()
                surf = render_grid_for_agent(environment, self, all_agents)
                grid_b64 = surface_to_base64(surf)
            except Exception:
                grid_b64 = None

        retry = None
        for _ in range(2):
            action = get_agent_action(
                agent_name=self.name,
                position=self.position,
                inventory=self.inventory,
                cell_content=cell,
                energy=self.energy,
                consumption_rate=self.consumption_rates,
                memory=self.memory,
                grid_image_base64=grid_b64,
                retry_message=retry
            ) or "do nothing"

            self.actions_taken.append(action)
            result = None

            if action.startswith("move"):
                direction = action.split()[1]
                new_pos = {
                    'up':    (max(0, x-1), y),
                    'down':  (min(environment.size-1, x+1), y),
                    'left':  (x, max(0, y-1)),
                    'right': (x, min(environment.size-1, y+1))
                }[direction]
                if new_pos not in occupied and new_pos != self.position:
                    self.position = new_pos
                    result = f"moved {direction} (energy: {self.energy})"
                else:
                    retry = f"move {direction} blocked"
                    result = "move blocked"

            elif action == "collect":
                item = environment.get_cell_content(x, y)
                if item and item in self.inventory:
                    self.inventory[item] += 1
                    environment.clear_cell(x, y)
                    result = f"collected {item}"
                else:
                    result = "nothing to collect"

            elif action == "eat red" and self.inventory['red'] > 0:
                self.inventory['red'] -= 1
                gain = self.consumption_rates['red']
                self.energy += gain
                result = f"ate red (+{gain})"

            elif action == "eat green" and self.inventory['green'] > 0:
                self.inventory['green'] -= 1
                gain = self.consumption_rates['green']
                self.energy += gain
                result = f"ate green (+{gain})"

            elif action == "do nothing":
                result = "did nothing"

            else:
                retry = f"action '{action}' invalid"
                result = "failed to act"

            # record memory & movement
            self.add_memory(obs, action, result)
            self.update_movement_history(cell, result)

            return result

        # if both attempts failed
        self.add_memory(obs, "no valid action", "failed both retries")
        self.update_movement_history(cell, "failed to act")
        return "failed to act"

    def status(self):
        print(f"{self.name} ({self.type}) @ {self.position} | "
              f"E={self.energy} | Inv={self.inventory} | Alive={self.alive}")

    def get_status_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'position': self.position,
            'inventory': self.inventory.copy(),
            'energy': self.energy,
            'alive': self.alive,
            'recent_actions': self.actions_taken[-5:],
            'recent_memory': self.memory[-AGENT_MEMORY_SIZE:]
        }
