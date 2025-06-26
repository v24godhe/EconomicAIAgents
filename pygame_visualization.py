import pygame
from config import *

def draw_grid(screen, env, agents, font, sub_font):
    screen.fill(COLORS['GRID'])

    # Draw grid and food
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            rect = pygame.Rect(j * CELL_SIZE, i * CELL_SIZE, CELL_SIZE - MARGIN, CELL_SIZE - MARGIN)
            pygame.draw.rect(screen, COLORS['WHITE'], rect)

            content = env.grid[i][j]
            if content in ['red', 'green']:
                center_x = j * CELL_SIZE + CELL_SIZE // 2
                center_y = i * CELL_SIZE + CELL_SIZE // 2
                radius = CELL_SIZE // 6
                color = COLORS['RED_FOOD'] if content == 'red' else COLORS['GREEN_FOOD']
                pygame.draw.circle(screen, color, (center_x, center_y), radius)

    # Draw agents
    for idx, agent in enumerate(agents):
        if not agent.alive:
            continue
            
        x, y = agent.position
        center_x = y * CELL_SIZE + CELL_SIZE // 2
        center_y = x * CELL_SIZE + CELL_SIZE // 2
        agent_color = COLORS['AGENTS'][idx % len(COLORS['AGENTS'])]

        # Draw agent body
        pygame.draw.circle(screen, agent_color, (center_x, center_y), CELL_SIZE // 4)

        # Draw agent ID
        id_label = font.render(agent.name[-1], True, COLORS['WHITE'])
        screen.blit(id_label, (center_x - 6, center_y - 8))

        # Draw inventory and energy
        inventory_text = f"R{agent.inventory['red']}G{agent.inventory['green']}E{agent.energy}"
        inv_label = sub_font.render(inventory_text, True, (50, 50, 50))
        screen.blit(inv_label, (center_x - 20, center_y + 10))
        
        # Draw energy warning if low
        if agent.energy <= CRITICAL_ENERGY_THRESHOLD:
            # Red border for critical energy
            pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), CELL_SIZE // 4 + 3, 2)
        elif agent.energy <= LOW_ENERGY_THRESHOLD:
            # Yellow border for low energy
            pygame.draw.circle(screen, (255, 255, 0), (center_x, center_y), CELL_SIZE // 4 + 3, 2)

    # Draw grid coordinates (optional)
    if ENABLE_DEBUG_OUTPUT:
        coord_font = pygame.font.SysFont('Arial', 10)
        for i in range(GRID_SIZE):
            # Row numbers
            label = coord_font.render(str(i), True, (100, 100, 100))
            screen.blit(label, (2, i * CELL_SIZE + 2))
            # Column numbers
            label = coord_font.render(str(i), True, (100, 100, 100))
            screen.blit(label, (i * CELL_SIZE + 2, 2))

    pygame.display.flip()

def draw_stats_overlay(screen, env, agents, font):
    """Draw statistics overlay (optional feature)"""
    overlay_height = 100
    overlay = pygame.Surface((SCREEN_WIDTH, overlay_height))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    
    # Food counts
    food_counts = env.count_food()
    text = f"Food: Red={food_counts['red']} Green={food_counts['green']}"
    label = font.render(text, True, COLORS['WHITE'])
    overlay.blit(label, (10, 10))
    
    # Alive agents
    alive_count = sum(1 for agent in agents if agent.alive)
    text = f"Alive: {alive_count}/{len(agents)}"
    label = font.render(text, True, COLORS['WHITE'])
    overlay.blit(label, (10, 30))
    
    # Average energy
    if alive_count > 0:
        avg_energy = sum(agent.energy for agent in agents if agent.alive) / alive_count
        text = f"Avg Energy: {avg_energy:.1f}"
        label = font.render(text, True, COLORS['WHITE'])
        overlay.blit(label, (10, 50))
    
    screen.blit(overlay, (0, SCREEN_HEIGHT - overlay_height))