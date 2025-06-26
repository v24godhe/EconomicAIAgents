from llm import get_agent_action

class Agent:
    def __init__(self, name, start_pos=(4, 4)):
        self.name = name
        self.position = start_pos
        self.inventory = {'red': 1, 'green': 1}
        self.energy = 20
        self.alive = True
        self.consumption_rates = self.get_consumption_rates()
        self.actions_taken = []  # Track history for debugging

    def get_agent_type(self):
        """Determine agent type based on consumption rates"""
        if self.consumption_rates['red'] > self.consumption_rates['green']:
            return 'red'
        elif self.consumption_rates['green'] > self.consumption_rates['red']:
            return 'green'
        else:
            return 'balanced'

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

    def decide_and_act(self, environment, trade_manager=None, all_agents=[]):
        if not self.alive:
            return "inactive"

        self.energy -= 1
        if self.energy <= 0:
            self.alive = False
            return "ran out of energy"

        x, y = self.position
        cell = environment.get_cell_content(x, y)
        occupied_positions = {a.position for a in all_agents if a.alive and a.name != self.name}

        retry_message = None
        for attempt in range(2):
            action = get_agent_action(
                agent_name=self.name,
                position=self.position,
                inventory=self.inventory,
                cell_content=cell,
                energy=self.energy,
                consumption_rate=self.consumption_rates,
                retry_message=retry_message
            )

            # # Track actions for debugging
            # self.actions_taken.append(action)

            if action.startswith("move"):
                direction = action.split()[1]
                moved = self.move(direction, environment.size, occupied_positions)
                if moved:
                    return f"moved {direction} (energy: {self.energy})"
                else:
                    retry_message = f"your move {direction} was blocked"

            elif action == "collect":
                result = self.collect(environment)
                return result

            elif action == "eat red" and self.inventory['red'] > 0:
                self.inventory['red'] -= 1
                self.energy += self.consumption_rates['red']
                return f"ate red (+{self.consumption_rates['red']} energy)"

            elif action == "eat green" and self.inventory['green'] > 0:
                self.inventory['green'] -= 1
                self.energy += self.consumption_rates['green']
                return f"ate green (+{self.consumption_rates['green']} energy)"

            elif action == "do nothing":
                return "did nothing"
            
            # Handle trade actions if trade_manager is provided
            elif action.startswith("trade") and trade_manager:
                return self.handle_trade(action, trade_manager, all_agents)

            else:
                retry_message = f"action '{action}' not possible"

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
            'last_actions': self.actions_taken[-5:] if self.actions_taken else []
        }