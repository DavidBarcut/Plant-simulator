# main.py

import pygame
import math
import random
import threading

from soil import set_soil_type, soil_properties, initialize_soil_grid, SEASONS, draw_soil_horizons, SOIL_TYPES
from Plants.plant import Seed
from water import WaterBlock
from weather import sun, moon, draw_sky, simulate_rain, update_and_draw_rain, set_season, current_season
from config import SCREEN_SIZE, WHITE, CELL_SIZE, ROWS, COLS
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

screen = pygame.Surface(SCREEN_SIZE)
clock = pygame.time.Clock()
screen_lock = threading.Lock()

seeds = []
water_blocks = []
simulation_running = False
rain_intensity = 1.0
raining = False
overlay_mode = None


display_info_mode = False
soil_info_text = ""
soil_info_pos = (0, 0)


info_font = pygame.font.SysFont("Arial", 18)

def get_soil_horizon_info(mouse_y):
   
    soil_top_y = SCREEN_SIZE[1] // 2  
    soil_bottom_y = soil_top_y + (ROWS * CELL_SIZE)
    if mouse_y < soil_top_y or mouse_y > soil_bottom_y:
        return None

    soil_depth = ROWS * CELL_SIZE  
    horizons = SOIL_TYPES[soil_properties['type']]['horizons']
    cumulative_height = 0
    info = None

    for horizon_key, props in horizons.items():
     
        horizon_height = int(ROWS * props['depth'] * CELL_SIZE)
        cumulative_height += horizon_height
        horizon_bottom_y = soil_top_y + cumulative_height
        if mouse_y <= horizon_bottom_y:
     
            horizon_name = props.get('name', props.get('Name', horizon_key))
            description = props.get('description', 'No description')
            composition = props.get('composition', 'N/A')
            moisture = props.get('moisture', 'N/A')
            nutrients = props.get('nutrients', {})
            nitrogen = nutrients.get('nitrogen', 'N/A')
            phosphorus = nutrients.get('phosphorus', 'N/A')
            potassium = nutrients.get('potassium', 'N/A')
            resistance = props.get('resistance', 'N/A')
            airation = props.get('airation', 'N/A')


            info = (
                f"Horizon Key: {horizon_key}\n"
                f"Name: {horizon_name}\n"
                f"Description: {description}\n"
                f"Composition: {composition}\n"
                f"Moisture Scores: {moisture}\n"
                f"Nutrients Scores:\n"
                f"  - Nitrogen: {nitrogen}\n"
                f"  - Phosphorus: {phosphorus}\n"
                f"  - Potassium: {potassium}\n"
                f"Resistance: {resistance}\n"
            )
            if airation != 'N/A':
                info += f"Airation: {airation}\n"
            break

    return info


def wrap_text(text, font, max_width):
    """Wrap text to fit within a given pixel width."""
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + (' ' if current_line else '') + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines



def set_overlay_mode(mode):
    global overlay_mode
    if mode in ["moisture", "nutrients", "combined"]:
        overlay_mode = mode
    else:
        overlay_mode = None
    print("Overlay mode set to", overlay_mode)


def interpolate_color(normalized):
   
    stops = [
        (0.0, (255, 0, 0)),       # Red
        (0.33, (255, 165, 0)),    # Orange
        (0.66, (255, 255, 0)),    # Yellow
        (1.0, (0, 0, 255))        # Blue
    ]
  
    for i in range(len(stops) - 1):
        low_val, low_color = stops[i]
        high_val, high_color = stops[i + 1]
        if normalized <= high_val:
        
            t = (normalized - low_val) / (high_val - low_val)
            r = int(low_color[0] + t * (high_color[0] - low_color[0]))
            g = int(low_color[1] + t * (high_color[1] - low_color[1]))
            b = int(low_color[2] + t * (high_color[2] - low_color[2]))
            return (r, g, b)
    return stops[-1][1]

def draw_overlay_grid(screen, mode):
    overlay_surface = pygame.Surface((COLS * CELL_SIZE, ROWS * CELL_SIZE), pygame.SRCALPHA)
    for row_index, row in enumerate(soil_properties['grid']):
        for col_index, cell in enumerate(row):
            rect = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if mode == "moisture":
                value = cell['moisture']
                max_value = 5.0  
                normalized = min(value, max_value) / max_value
            elif mode == "nutrients":
                nutrients = cell['nutrients']
                total = nutrients['nitrogen'] + nutrients['phosphorus'] + nutrients['potassium']
                max_value = 150  
                normalized = min(total, max_value) / max_value
            elif mode == "combined":
                moisture_value = cell['moisture']
                max_moisture = 5.0
                normalized_moisture = min(moisture_value, max_moisture) / max_moisture
                nutrients = cell['nutrients']
                total = nutrients['nitrogen'] + nutrients['phosphorus'] + nutrients['potassium']
                max_nutrient = 150
                normalized_nutrient = min(total, max_nutrient) / max_nutrient
                normalized = (normalized_moisture + normalized_nutrient) / 2.0
          
            base_color = interpolate_color(normalized)
       
            color = (*base_color, 150)
            pygame.draw.rect(overlay_surface, color, rect)
   
    screen.blit(overlay_surface, (0, SCREEN_SIZE[1] // 2))





def start_simulation():
    global simulation_running
    simulation_running = True

def pause_simulation():
    global simulation_running
    simulation_running = False


def game_loop():
    global display_info_mode, soil_info_text, soil_info_pos
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    display_info_mode = not display_info_mode
            elif event.type == pygame.MOUSEMOTION:
            
                soil_info_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    mouse_x, mouse_y = event.pos
                    seeds.append(Seed(mouse_x, mouse_y))
        

        if display_info_mode:
            # Use the global soil_info_pos updated by the client
            print("Updated soil_info_pos from client:", soil_info_pos)  
            info = get_soil_horizon_info(soil_info_pos[1])
            soil_info_text = info if info else ""
        else:
            soil_info_text = ""



        with screen_lock:
            screen.fill(WHITE)
            if simulation_running:
                sun.update()
                moon.update()


            

            draw_sky(screen)

            if raining:
                simulate_rain(soil_properties, rain_intensity)
                update_and_draw_rain(screen, rain_intensity)

            draw_soil_horizons(screen)
            if overlay_mode is not None:
                draw_overlay_grid(screen, overlay_mode)


            for seed in seeds:
                seed.draw(screen, simulation_running)
            for water_block in water_blocks:
                water_block.draw(screen)

         
         

            # Draw the soil info popup if enabled and text exists
            if display_info_mode and soil_info_text:
              
                lines = soil_info_text.split('\n')
                
      
                line_surfaces = [info_font.render(line, True, (0, 0, 0)) for line in lines]

   
                line_height = info_font.get_linesize()
                popup_width = max(surf.get_width() for surf in line_surfaces) + 10
                popup_height = len(line_surfaces) * line_height + 10

       
                popup_x = soil_info_pos[0] + 12
                popup_y = soil_info_pos[1] - (popup_height + 12)
                

                if popup_y < 0:
                    popup_y = 0

                popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
                pygame.draw.rect(screen, (255,255,255), popup_rect)
                pygame.draw.rect(screen, (0,0,0), popup_rect, 2)

           
                y_offset = popup_y + 5
                for surf in line_surfaces:
                    screen.blit(surf, (popup_x + 5, y_offset))
                    y_offset += line_height





            pygame.display.flip()
            clock.tick(5)


