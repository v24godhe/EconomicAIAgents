import os
import sys
import csv
import json
import random
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from config import (
    NUM_AGENTS,
    GRID_SIZE,
    TOTAL_STEPS,
    REPLENISH_INTERVAL,
    REPLENISH_RED_COUNT,
    REPLENISH_GREEN_COUNT,
    AGENT_BASE_CONFIGS,
    CONSUMPTION_RATES,
    STUDY_RUNS_PER_RATE
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

def run_simulation_with_consumption_rate(consumption_rate, num_runs=None):
    """Run multiple simulations with the given consumption rate and return average survival rate"""
    if num_runs is None:
        num_runs = STUDY_RUNS_PER_RATE
        
    survival_rates = []
    
    for run in range(num_runs):
        print(f"  Running simulation {run + 1}/{num_runs} with consumption rate {consumption_rate}")
        
        # Update agent configs with new consumption rate
        import config
        config.CONSUMPTION_RATE = consumption_rate
        config.AGENT_CONFIGS = {
            agent: {
                'red': int(rates['red'] * consumption_rate),
                'green': int(rates['green'] * consumption_rate)
            }
            for agent, rates in AGENT_BASE_CONFIGS.items()
        }
        
        # Create environment and agents
        env = Environment()
        positions = generate_unique_positions(NUM_AGENTS, GRID_SIZE)
        agents = [
            Agent(f"Agent{i+1}", start_pos=positions[i])
            for i in range(NUM_AGENTS)
        ]
        
        # Run simulation
        for step in range(1, TOTAL_STEPS + 1):
            for agent in agents:
                if agent.alive:
                    agent.decide_and_act(env, all_agents=agents)
            
            # Replenish food periodically
            if step % REPLENISH_INTERVAL == 0:
                env.fixed_replenish(
                    red_count=REPLENISH_RED_COUNT,
                    green_count=REPLENISH_GREEN_COUNT
                )
        
        # Calculate survival rate
        survivors = sum(1 for agent in agents if agent.alive)
        survival_rate = survivors / NUM_AGENTS
        survival_rates.append(survival_rate)
        
        print(f"    Survival rate: {survival_rate:.2%} ({survivors}/{NUM_AGENTS})")
    
    avg_survival_rate = np.mean(survival_rates)
    std_survival_rate = np.std(survival_rates)
    
    return avg_survival_rate, std_survival_rate

def main():
    # Use consumption rates from config
    consumption_rates = CONSUMPTION_RATES
    results = []
    
    print("Starting consumption rate study...")
    print(f"Testing consumption rates: {consumption_rates}")
    print(f"Runs per rate: {STUDY_RUNS_PER_RATE}")
    
    for rate in consumption_rates:
        print(f"\nTesting consumption rate: {rate}")
        avg_survival, std_survival = run_simulation_with_consumption_rate(rate)
        results.append({
            'consumption_rate': rate,
            'avg_survival_rate': avg_survival,
            'std_survival_rate': std_survival
        })
        print(f"Average survival rate: {avg_survival:.2%} ± {std_survival:.2%}")
    
    # Save results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"consumption_rate_study_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    # Create visualization
    create_survival_rate_graph(results, timestamp)
    
    # Find optimum consumption rate
    find_optimum_rate(results)

def create_survival_rate_graph(results, timestamp):
    """Create a graph showing survival rate vs consumption rate"""
    rates = [r['consumption_rate'] for r in results]
    survival_rates = [r['avg_survival_rate'] for r in results]
    std_rates = [r['std_survival_rate'] for r in results]
    
    plt.figure(figsize=(12, 8))
    plt.errorbar(rates, survival_rates, yerr=std_rates, marker='o', linewidth=2, markersize=8)
    plt.xlabel('Consumption Rate Multiplier', fontsize=12)
    plt.ylabel('Average Survival Rate', fontsize=12)
    plt.title('Agent Survival Rate vs Consumption Rate', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1)
    
    # Add percentage labels on y-axis
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
    
    # Highlight the optimum point
    max_survival_idx = np.argmax(survival_rates)
    optimum_rate = rates[max_survival_idx]
    optimum_survival = survival_rates[max_survival_idx]
    
    plt.scatter(optimum_rate, optimum_survival, color='red', s=100, zorder=5)
    plt.annotate(f'Optimum: {optimum_rate}\n({optimum_survival:.1%})', 
                xy=(optimum_rate, optimum_survival), 
                xytext=(optimum_rate + 0.2, optimum_survival + 0.1),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red')
    
    plt.tight_layout()
    
    # Save the graph
    graph_file = f"survival_rate_graph_{timestamp}.png"
    plt.savefig(graph_file, dpi=300, bbox_inches='tight')
    print(f"Graph saved to {graph_file}")
    plt.show()

def find_optimum_rate(results):
    """Find and display the optimum consumption rate"""
    max_survival_result = max(results, key=lambda x: x['avg_survival_rate'])
    
    print(f"\n=== OPTIMUM CONSUMPTION RATE ===")
    print(f"Rate: {max_survival_result['consumption_rate']}")
    print(f"Survival Rate: {max_survival_result['avg_survival_rate']:.2%} ± {max_survival_result['std_survival_rate']:.2%}")
    
    # Show what this means for each agent
    print(f"\nAgent consumption rates at optimum ({max_survival_result['consumption_rate']}):")
    for agent, base_rates in AGENT_BASE_CONFIGS.items():
        red_rate = int(base_rates['red'] * max_survival_result['consumption_rate'])
        green_rate = int(base_rates['green'] * max_survival_result['consumption_rate'])
        print(f"  {agent}: Red={red_rate}, Green={green_rate}")

if __name__ == "__main__":
    main