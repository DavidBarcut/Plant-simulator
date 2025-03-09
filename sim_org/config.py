# config.py

import pygame
import os
import math

# Pygame initialization and screen configuration
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

# Screen and cell configuration
SCREEN_SIZE = (1200, 900)
CELL_SIZE = 3
COLS = SCREEN_SIZE[0] // CELL_SIZE
ROWS = SCREEN_SIZE[1] // CELL_SIZE
SOIL_ROWS = ROWS // 2

# Colors
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
BLUE = (135, 206, 235)
BLACK = (0, 0, 0)
WATER = (0, 0, 139)

# Simulation parameters
TIME_SCALE = 600 / 2

# Other constants and weight factors for growth, etc.
W_geo = 1.0      
W_hydro = 3.0    
W_chemo = 1.5    
W_thermo = 0.5   
w_PH = 1.0
w_air = 1.0

# Geotropism weights by direction
GEOTROPISM_WEIGHTS = {
    'up': 0.5,
    'left': 0.9,
    'right': 0.9,
    'down': 0.9,  
    'down-left': 0.8,
    'down-right': 0.8
}


