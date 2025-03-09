# water.py

import random
import math
import pygame
from config import CELL_SIZE, WATER, COLS, ROWS, SCREEN_SIZE
from soil import soil_properties, update_moisture_gradient

class WaterBlock:
    def __init__(self, x, y, size=4):
        self.x = x
        self.y = y
        self.size = size
        grid_x = self.x // CELL_SIZE
        grid_y = (self.y - SCREEN_SIZE[1] // 2) // CELL_SIZE
        update_moisture_gradient(grid_x, grid_y, size)

    def draw(self, screen):
        for i in range(self.size):
            for j in range(self.size):
                pygame.draw.rect(screen, WATER, (self.x + i * CELL_SIZE, self.y + j * CELL_SIZE, CELL_SIZE, CELL_SIZE))
