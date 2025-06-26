# Game Configuration File

# Grid settings
GRID_SIZE = 9
INITIAL_FOOD_PERCENTAGE = 0.25  # 25% of cells start with food

# Agent settings
NUM_AGENTS = 5
INITIAL_ENERGY = 20
INITIAL_INVENTORY = {'red': 1, 'green': 1}

# Agent consumption rates (energy gained from eating)
AGENT_CONFIGS = {
    "Agent1": {'red': 50, 'green': 0},     # Red specialist
    "Agent2": {'red': 20, 'green': 30},    # Green preference
    "Agent3": {'red': 30, 'green': 20},    # Red preference
    "Agent4": {'red': 25, 'green': 25},    # Balanced
    "Agent5": {'red': 0, 'green': 50},     # Green specialist
}

# Game mechanics
ENERGY_LOSS_PER_TURN = 1
REPLENISH_INTERVAL = 20  # Steps between food replenishment
REPLENISH_RED_COUNT = 5
REPLENISH_GREEN_COUNT = 5

# Simulation settings
TOTAL_STEPS = 200
FPS = 2  # Frames per second for visualization
PAUSE_ON_START = False

# Display settings
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 540
CELL_SIZE = 60
MARGIN = 2

# Colors (RGB)
COLORS = {
    'WHITE': (255, 255, 255),
    'GRID': (240, 240, 240),
    'RED_FOOD': (220, 20, 60),
    'GREEN_FOOD': (34, 139, 34),
    'AGENTS': [
        (30, 144, 255),   # Blue
        (255, 140, 0),    # Orange
        (128, 0, 128),    # Purple
        (0, 128, 128),    # Teal
        (199, 21, 133),   # Pink
    ]
}

# Logging settings
LOG_STATS_INTERVAL = 10  # Save statistics every N steps
ENABLE_DEBUG_OUTPUT = True
LOG_LLM_CALLS = True

# LLM settings
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 50
LLM_RETRY_ATTEMPTS = 2

# Fallback behavior settings
CRITICAL_ENERGY_THRESHOLD = 5  # Energy level to trigger emergency eating
LOW_ENERGY_THRESHOLD = 10     # Energy level to prioritize eating
EXPLORATION_PROBABILITY = 0.3  # Chance to explore when no immediate goals