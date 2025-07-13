import random
# import pygame
import sys
import json
import csv
from datetime import datetime
from environment import Environment
from agent import Agent
from pygame_visualization import draw_grid

def generate_unique_positions(num_agents, grid_size):
    positions = set()
    while len(positions) < num_agents:
        x = random.randint(0, grid_size - 1)
        y = random.randint(0, grid_size - 1)
        positions.add((x, y))
    return list(positions)

def save_game_stats(agents, step, filename="game_stats.json"):
    """Save game statistics for analysis"""
    stats = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        'agents': [agent.get_status_dict() for agent in agents],
        'alive_count': sum(1 for agent in agents if agent.alive)
    }
    
    try:
        with open(filename, 'r') as f:
            all_stats = json.load(f)
    except:
        all_stats = []
    
    all_stats.append(stats)
    
    with open(filename, 'w') as f:
        json.dump(all_stats, f, indent=2)

def main():
    # pygame.init()
    # screen = pygame.display.set_mode((540, 540))
    # pygame.display.set_caption("LLM Agent Simulation")
    # font = pygame.font.SysFont('Arial', 16, bold=True)
    # sub_font = pygame.font.SysFont('Arial', 12)
    # clock = pygame.time.Clock()

    # Game configuration
    REPLENISH_RED = 5
    REPLENISH_GREEN = 5
    REPLENISH_INTERVAL = 20
    FPS = 5  # Frames per second
    
    env = Environment()
    num_agents = 5 
    positions = generate_unique_positions(num_agents, env.size)
    agents = [Agent(f"Agent{i+1}", start_pos=positions[i]) for i in range(num_agents)]

    steps = 0
    total_steps = 50
    running = True
    paused = False

    print("\n=== SIMULATION STARTED ===")
    print(f"Total agents: {num_agents}")
    print(f"Replenishment: {REPLENISH_RED} red, {REPLENISH_GREEN} green every {REPLENISH_INTERVAL} steps")

    # CSV logging setup - real-time logging like Project 2
    with open("llm_agent_log.csv", "w", newline='') as energy_log, \
         open("llm_actions_log.csv", "w", newline='') as action_log:

        energy_writer = csv.writer(energy_log)
        action_writer = csv.writer(action_log)
        
        # Write CSV headers
        energy_writer.writerow(["Step", "Agent", "Energy"])
        action_writer.writerow(["Step", "Agent", "Action"])

        while steps < total_steps and running:
            # Handle events
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         running = False
            #     elif event.type == pygame.KEYDOWN:
            #         if event.key == pygame.K_SPACE:
            #             paused = not paused
            #             print(f"\n{'PAUSED' if paused else 'RESUMED'}")
            #         elif event.key == pygame.K_q:
            #             running = False

            # Count alive agents
            print(f"\n--- Step {steps + 1} ---")
            alive_count = sum(1 for agent in agents if agent.alive)
            print(f"Alive agents: {alive_count}/{num_agents}")
            
            # Agent actions
            for agent in agents:
                if agent.alive:
                    action = agent.decide_and_act(env, all_agents=agents)
                    print(f"{agent.name} at {agent.position} (energy: {agent.energy}): {action}")
                    
                    # Real-time CSV logging - log energy and actions immediately
                    energy_writer.writerow([steps + 1, agent.name, agent.energy])
                    action_writer.writerow([steps + 1, agent.name, action])
                else:
                    # Log dead agents too for complete data
                    energy_writer.writerow([steps + 1, agent.name, 0])
                    action_writer.writerow([steps + 1, agent.name, "inactive"])
            
            # Check for game over
            if alive_count == 0:
                print("\n🎮 GAME OVER - All agents died!")
                running = False

            steps += 1

            # Replenish food at intervals
            if steps % REPLENISH_INTERVAL == 0:
                print(f"\n🔄 Replenishing {REPLENISH_RED} red and {REPLENISH_GREEN} green at step {steps}...")
                env.fixed_replenish(red_count=REPLENISH_RED, green_count=REPLENISH_GREEN)

            # Save JSON statistics every 10 steps (keep existing functionality)
            if steps % 10 == 0:
                save_game_stats(agents, steps)

            # Always update display
            # draw_grid(screen, env, agents, font, sub_font)
            
            # # Show pause indicator
            # if paused:
            #     pause_text = font.render("PAUSED", True, (255, 0, 0))
            #     text_rect = pause_text.get_rect(center=(270, 270))
            #     pygame.draw.rect(screen, (255, 255, 255), text_rect.inflate(20, 10))
            #     screen.blit(pause_text, text_rect)
            #     pygame.display.flip()
            
            # clock.tick(FPS)

    # Final statistics
    print("\n=== SIMULATION COMPLETE ===")
    for agent in agents:
        agent.status()
    
    # Save final stats
    save_game_stats(agents, steps, "final_stats.json")
    
    # pygame.quit()
    print("\nSimulation data saved to:")
    print("- game_stats.json and final_stats.json (existing JSON format)")
    print("- llm_agent_log.csv and llm_actions_log.csv (new real-time CSV format)")

if __name__ == "__main__":
    main()