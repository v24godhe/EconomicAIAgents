import os
import sys
import csv
import random
from config import (
    NUM_AGENTS,
    GRID_SIZE,
    TOTAL_STEPS,
    REPLENISH_INTERVAL,
    REPLENISH_RED_COUNT,
    REPLENISH_GREEN_COUNT
)
from environment import Environment
from agent import Agent

def generate_unique_positions(num_agents: int, grid_size: int):
    positions = set()
    while len(positions) < num_agents:
        positions.add((
            random.randint(0, grid_size - 1),
            random.randint(0, grid_size - 1)
        ))
    return list(positions)

def main():
    # Prepare environment and agents
    env = Environment()
    positions = generate_unique_positions(NUM_AGENTS, GRID_SIZE)
    agents = [
        Agent(f"Agent{i+1}", start_pos=positions[i])
        for i in range(NUM_AGENTS)
    ]

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    energy_log_path = os.path.join("logs", "llm_agent_log.csv")
    action_log_path = os.path.join("logs", "llm_actions_log.csv")

    # Open CSV files and write headers
    with open(energy_log_path, "w", newline="", encoding="utf-8") as elog, \
         open(action_log_path, "w", newline="", encoding="utf-8") as alog:

        energy_writer = csv.writer(elog)
        action_writer = csv.writer(alog)

        energy_writer.writerow(["Step", "Agent", "Energy"])
        action_writer.writerow(["Step", "Agent", "Action"])

        # Main simulation loop
        for step in range(1, TOTAL_STEPS + 1):
            print(f"\n--- Step {step} ---")
            alive_count = sum(1 for a in agents if a.alive)
            print(f"Alive: {alive_count}/{NUM_AGENTS}")

            for agent in agents:
                if agent.alive:
                    action = agent.decide_and_act(env, all_agents=agents)
                else:
                    action = "inactive"

                # Console log
                print(f"{agent.name} @ {agent.position} | E={agent.energy}: {action}")

                # CSV log
                energy_writer.writerow([step, agent.name, agent.energy])
                action_writer.writerow([step, agent.name, action])

            # Replenish food periodically
            if step % REPLENISH_INTERVAL == 0:
                print(f"🔄 Replenishing {REPLENISH_RED_COUNT} red & "
                      f"{REPLENISH_GREEN_COUNT} green")
                env.fixed_replenish(
                    red_count=REPLENISH_RED_COUNT,
                    green_count=REPLENISH_GREEN_COUNT
                )

    print("\nSimulation complete.")
    print(f"Energy log saved to {energy_log_path}")
    print(f"Actions log saved to {action_log_path}")

if __name__ == "__main__":
    main()
