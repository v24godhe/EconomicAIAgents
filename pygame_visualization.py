import pygame
import io
import base64
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

def render_grid_for_agent(env, agent, all_agents):
    """Render a small grid image centered on the agent for multimodal LLM"""
    # Create a smaller surface for the agent's view
    view_size = 5  # 5x5 grid around agent
    cell_size = 40  # Smaller cells for LLM processing
    surface_size = view_size * cell_size
    
    surface = pygame.Surface((surface_size, surface_size))
    surface.fill(COLORS['WHITE'])
    
    agent_x, agent_y = agent.position
    
    # Calculate visible area around agent
    start_x = max(0, agent_x - view_size // 2)
    end_x = min(GRID_SIZE, agent_x + view_size // 2 + 1)
    start_y = max(0, agent_y - view_size // 2)
    end_y = min(GRID_SIZE, agent_y + view_size // 2 + 1)
    
    # Draw grid cells
    for i in range(start_x, end_x):
        for j in range(start_y, end_y):
            # Calculate position on the surface
            surf_x = (j - start_y) * cell_size
            surf_y = (i - start_x) * cell_size
            
            rect = pygame.Rect(surf_x, surf_y, cell_size - 2, cell_size - 2)
            pygame.draw.rect(surface, COLORS['GRID'], rect)
            
            # Draw food
            content = env.grid[i][j]
            if content in ['red', 'green']:
                center_x = surf_x + cell_size // 2
                center_y = surf_y + cell_size // 2
                radius = cell_size // 6
                color = COLORS['RED_FOOD'] if content == 'red' else COLORS['GREEN_FOOD']
                pygame.draw.circle(surface, color, (center_x, center_y), radius)
    
    # Draw other agents in view
    for other_agent in all_agents:
        if not other_agent.alive or other_agent.name == agent.name:
            continue
            
        other_x, other_y = other_agent.position
        if start_x <= other_x < end_x and start_y <= other_y < end_y:
            surf_x = (other_y - start_y) * cell_size + cell_size // 2
            surf_y = (other_x - start_x) * cell_size + cell_size // 2
            pygame.draw.circle(surface, (128, 128, 128), (surf_x, surf_y), cell_size // 4)
    
    # Draw current agent (highlighted)
    if start_x <= agent_x < end_x and start_y <= agent_y < end_y:
        surf_x = (agent_y - start_y) * cell_size + cell_size // 2
        surf_y = (agent_x - start_x) * cell_size + cell_size // 2
        pygame.draw.circle(surface, (255, 255, 0), (surf_x, surf_y), cell_size // 3)
        pygame.draw.circle(surface, (0, 0, 0), (surf_x, surf_y), cell_size // 3, 3)
    
    return surface

def surface_to_base64(surface):
    """Convert pygame surface to base64 string for LLM"""
    # Convert surface to string data
    img_str = pygame.image.tostring(surface, 'RGB')
    img_size = surface.get_size()
    
    # Create PIL Image and convert to base64
    try:
        from PIL import Image
        import io
        
        # Convert pygame surface to PIL Image
        img = Image.frombytes('RGB', img_size, img_str)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return img_base64
    except ImportError:
        print("PIL not available for image conversion. Install with: pip install Pillow")
        return None

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