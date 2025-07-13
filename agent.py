from llm import get_agent_action
from config import AGENT_MEMORY_SIZE, USE_MULTIMODAL
from pygame_visualization import render_grid_for_agent, surface_to_base64
import json

class Agent:
    def __init__(self, name, start_pos=(4, 4)):
        self.name = name
        self.position = start_pos
        self.inventory = {'red': 1, 'green': 1}
        self.energy = 20
        self.alive = True
        self.consumption_rates = self.get_consumption_rates()
        self.actions_taken = []  # Track history for debugging
        self.memory = []  # Store recent memories for LLM context
        self.step_count = 0
        self.movement_history = []  # Individual movement history like Project 2

    def get_agent_type(self):
        """Determine agent type based on consumption rates"""
        if self.consumption_rates['red'] > self.consumption_rates['green']:
            return 'red'
        elif self.consumption_rates['green'] > self.consumption_rates['red']:
            return 'green'
        else:
            return 'balanced'
    
    @property
    def type(self):
        """Property to get agent type"""
        return self.get_agent_type()

    def get_consumption_rates(self):
        if self.name == "Agent1":
            return {'red': 50, 'green': 0}
        elif self.name == "Agent2":
            return {'red': 20, 'green': 30}
        elif self.name == "Agent3":
            return {'red': 30, 'green': 20}
        elif self.name == "Agent4":
            return {'red': 25, 'green': 25}
        else:
            return {'red': 0, 'green': 50}

    def add_memory(self, observation, action_taken, result):
        """Add a structured memory entry and maintain memory limit"""
        memory_entry = (
            f"Step {self.step_count}: "
            f"Action: {action_taken} | "
            f"Observation: {observation} | "
            f"Outcome: {result} | "
            f"Energy: {self.energy} | "
            f"Inventory: {self.inventory}"
        )
        self.memory.append(memory_entry)
        # Keep only last N memories
        if len(self.memory) > AGENT_MEMORY_SIZE:
            self.memory = self.memory[-AGENT_MEMORY_SIZE:]

    def update_movement_history(self, cell_content, action_taken):
        """Update individual movement history like Project 2"""
        history_entry = {
            "step": self.step_count,
            "position": self.position,
            "cell_content": cell_content if cell_content else "empty",
            "action_taken": action_taken
        }
        
        self.movement_history.append(history_entry)
        
        # Keep only last 3 movements
        if len(self.movement_history) > 3:
            self.movement_history.pop(0)
        
        # Save to individual file like Project 2
        self.save_movement_history_to_file()

    def save_movement_history_to_file(self):
        """Save movement history to individual agent file"""
        filename = f"movement_history_{self.name}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.movement_history, f, indent=4)
    
    def get_current_observation(self, environment, all_agents):
        """Generate current observation for memory"""
        x, y = self.position
        cell_content = environment.get_cell_content(x, y)
        
        # Count nearby food and agents
        nearby_red = 0
        nearby_green = 0
        nearby_agents = 0
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < environment.size and 0 <= ny < environment.size:
                    if environment.get_cell_content(nx, ny) == 'red':
                        nearby_red += 1
                    elif environment.get_cell_content(nx, ny) == 'green':
                        nearby_green += 1
        
        for agent in all_agents:
            if agent.alive and agent.name != self.name:
                ax, ay = agent.position
                if abs(ax - x) <= 1 and abs(ay - y) <= 1:
                    nearby_agents += 1
        
        cell_desc = cell_content if cell_content else "empty"
        return f"at {self.position}, cell has {cell_desc}, nearby: {nearby_red}R {nearby_green}G {nearby_agents}A, energy: {self.energy}"

    def decide_and_act(self, environment, trade_manager=None, all_agents=[]):
        if not self.alive:
            return "inactive"

        self.step_count += 1
        current_observation = self.get_current_observation(environment, all_agents)
        
        self.energy -= 1
        if self.energy <= 0:
            self.alive = False
            return "ran out of energy"

        x, y = self.position
        cell = environment.get_cell_content(x, y)
        occupied_positions = {a.position for a in all_agents if a.alive and a.name != self.name}

        # Generate visual input for multimodal model
        grid_image_base64 = None
        if USE_MULTIMODAL:
            try:
                import pygame
                pygame.init()  # Ensure pygame is initialized
                grid_surface = render_grid_for_agent(environment, self, all_agents)
                grid_image_base64 = surface_to_base64(grid_surface)
            except Exception as e:
                print(f"Failed to generate visual input for {self.name}: {e}")

        retry_message = None
        for attempt in range(2):
            action = get_agent_action(
                agent_name=self.name,
                position=self.position,
                inventory=self.inventory,
                cell_content=cell,
                energy=self.energy,
                consumption_rate=self.consumption_rates,
                memory=self.memory,
                grid_image_base64=grid_image_base64,
                retry_message=retry_message
            )

            # Defensive: Ensure action is always a string
            if not action:
                action = "do nothing"

            # Track actions for debugging
            self.actions_taken.append(action)

            action_result = None
            if action.startswith("move"):
                direction = action.split()[1]
                moved = self.move(direction, environment.size, occupied_positions)
                if moved:
                    action_result = f"moved {direction} (energy: {self.energy})"
                    self.add_memory(current_observation, action, "successful move")
                    self.update_movement_history(cell, action_result)
                    return action_result
                else:
                    retry_message = f"your move {direction} was blocked"
                    action_result = "move blocked"

            elif action == "collect":
                result = self.collect(environment)
                action_result = result
                self.add_memory(current_observation, action, result)
                self.update_movement_history(cell, result)
                return result

            elif action == "eat red" and self.inventory['red'] > 0:
                self.inventory['red'] -= 1
                self.energy += self.consumption_rates['red']
                action_result = f"ate red (+{self.consumption_rates['red']} energy)"
                self.add_memory(current_observation, action, f"gained {self.consumption_rates['red']} energy")
                self.update_movement_history(cell, action_result)
                return action_result

            elif action == "eat green" and self.inventory['green'] > 0:
                self.inventory['green'] -= 1
                self.energy += self.consumption_rates['green']
                action_result = f"ate green (+{self.consumption_rates['green']} energy)"
                self.add_memory(current_observation, action, f"gained {self.consumption_rates['green']} energy")
                self.update_movement_history(cell, action_result)
                return action_result

            elif action == "do nothing":
                action_result = "did nothing"
                self.add_memory(current_observation, action, "no action taken")
                self.update_movement_history(cell, action_result)
                return action_result
            
            # Handle trade actions if trade_manager is provided
            elif action.startswith("trade") and trade_manager:
                action_result = self.handle_trade(action, trade_manager, all_agents)
                self.add_memory(current_observation, action, action_result)
                self.update_movement_history(cell, action_result)
                return action_result

            else:
                retry_message = f"action '{action}' not possible"
                action_result = "invalid action"

        # If we get here, both attempts failed
        self.add_memory(current_observation, "failed attempts", "no valid action found")
        self.update_movement_history(cell, "failed to act")
        return "failed to act"

    def handle_trade(self, action, trade_manager, all_agents):
        """Handle trading actions (placeholder for future implementation)"""
        # This could be expanded to handle complex trading logic
        return "trading not implemented"

    def can_collect(self, food_type):
        return food_type in ['red', 'green']

    def move(self, direction, grid_size, occupied_positions):
        x, y = self.position
        new_pos = self.position

        if direction == 'up':
            new_pos = (max(0, x - 1), y)
        elif direction == 'down':
            new_pos = (min(grid_size - 1, x + 1), y)
        elif direction == 'left':
            new_pos = (x, max(0, y - 1))
        elif direction == 'right':
            new_pos = (x, min(grid_size - 1, y + 1))

        if new_pos not in occupied_positions and new_pos != self.position:
            self.position = new_pos
            return True
        return False

    def collect(self, environment):
        x, y = self.position
        item = environment.get_cell_content(x, y)
        if item and self.can_collect(item):
            self.inventory[item] += 1
            environment.clear_cell(x, y)
            return f"collected {item}"
        return "nothing to collect"

    def status(self):
        print(f"{self.name} ({self.type}) at {self.position} | Inventory: {self.inventory} | Energy: {self.energy} | Alive: {self.alive}")
    
    def get_status_dict(self):
        """Return agent status as dictionary for logging/debugging"""
        return {
            'name': self.name,
            'type': self.type,
            'position': self.position,
            'inventory': self.inventory,
            'energy': self.energy,
            'alive': self.alive,
            'last_actions': self.actions_taken[-5:] if self.actions_taken else [],
            'recent_memories': self.memory[-3:] if self.memory else []
        }