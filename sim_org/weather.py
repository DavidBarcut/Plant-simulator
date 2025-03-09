# weather.py

import math
import random
import pygame
from config import SCREEN_SIZE, TIME_SCALE, BLUE
import config



SEASONS = {
    'spring': {
        'day_length': 600,
        'temperature': 15,
        'humidity': 60,
        'light_hours': 12,
        'growth_range': (0.8, 1.0),
        'rain_chance': 0.4 
    },
    'summer': {
        'day_length': 800,
        'temperature': 25,
        'humidity': 50,
        'light_hours': 14,
        'growth_range': (0.3, 0.8),
        'rain_chance': 0.2
    },
    'autumn': {
        'day_length': 600,
        'temperature': 10,
        'humidity': 70,
        'light_hours': 10,
        'growth_range': (0.1, 0.5),
        'rain_chance': 0.3
    },
    'winter': {
        'day_length': 400,
        'temperature': 0,
        'humidity': 80,
        'light_hours': 8,
        'growth_range': (0.0, 0.0),
        'rain_chance': 0.5
    }
}

current_season = 'spring'

class Sun:
    def __init__(self, screen_width, screen_height, day_length):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 30
        self.angle = 0  
        self.day_length = day_length  

    def update(self):

        increment = (2 * math.pi / self.day_length) * (config.TIME_SCALE / 2.0)
        self.angle += increment
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    # def draw(self, screen):
    #     sun_x = (self.screen_width / 2) + (self.screen_width / 2) * math.cos(self.angle)
    #     sun_y = (self.screen_height / 2) - (self.screen_height / 2) * math.sin(self.angle)
    #     pygame.draw.circle(screen, (255, 255, 0), (int(sun_x), int(sun_y)), self.radius)


class Moon:
    def __init__(self, screen_width, screen_height, day_length):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 20
        self.angle = math.pi  # Start opposite the sun
        self.day_length = day_length

    def update(self):
        increment = (2 * math.pi / self.day_length) * (config.TIME_SCALE / 2.0)
        self.angle += increment
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    # def draw(self, screen):
    #     moon_x = (self.screen_width / 2) + (self.screen_width / 2) * math.cos(self.angle)
    #     moon_y = (self.screen_height / 2) - (self.screen_height / 2) * math.sin(self.angle)
    #     pygame.draw.circle(screen, (200, 200, 200), (int(moon_x), int(moon_y)), self.radius)


def simulate_rain(soil_properties, rain_intensity):
    for i, row in enumerate(soil_properties['grid']):
        depth_factor = 1.0 if i < len(soil_properties['grid']) * 0.3 else 0.5
        for cell in row:
           
            cell['moisture'] += (rain_intensity / 200) * (depth_factor/2) * soil_properties.get('moisture_retention', 1)

rain_drops = [] 

def update_and_draw_rain(screen, rain_intensity):
    global rain_drops
    
    new_count = int(rain_intensity * 10)  
    for _ in range(new_count):
        drop = {
            'x': random.randint(0, SCREEN_SIZE[0]),
            'y': random.randint(-50, 0),
            'length': random.randint(10, 15),
            'speed': random.randint(5, 10)
        }
        rain_drops.append(drop)
   
    for drop in rain_drops:
        drop['y'] += drop['speed']
        pygame.draw.line(screen, (173, 216, 230), (drop['x'], drop['y']),
                         (drop['x'], drop['y'] + drop['length']), 1)

    rain_drops = [drop for drop in rain_drops if drop['y'] < SCREEN_SIZE[1]]


def draw_sky(screen):
    season = SEASONS[current_season]
    day_length = season['day_length'] 
    sky_height = SCREEN_SIZE[1] // 2


    current_time = pygame.time.get_ticks() / 1000.0

    normalized_time = (current_time % day_length) / day_length

    light_intensity = 0.5 * (1 + math.cos(2 * math.pi * (normalized_time - 0.5)))

    night_color = (0, 0, 139)      # dark blue for night
    day_color = (135, 206, 235)    # light blue for day

 
    sky_color = (
        int(night_color[0] * (1 - light_intensity) + day_color[0] * light_intensity),
        int(night_color[1] * (1 - light_intensity) + day_color[1] * light_intensity),
        int(night_color[2] * (1 - light_intensity) + day_color[2] * light_intensity)
    )


    pygame.draw.rect(screen, sky_color, pygame.Rect(0, 0, SCREEN_SIZE[0], sky_height))

    for i in range(sky_height):
        blend_t = i / sky_height
        blended_color = (
            int(sky_color[0] * (1 - blend_t) + sky_color[0] * blend_t),
            int(sky_color[1] * (1 - blend_t) + sky_color[1] * blend_t),
            int(sky_color[2] * (1 - blend_t) + sky_color[2] * blend_t)
        )
        pygame.draw.line(screen, blended_color, (0, sky_height - i), (SCREEN_SIZE[0], sky_height - i))

def set_time_of_day(time_value, sun, moon):
    angle = (time_value / 100) * 2 * math.pi
    sun.angle = angle
    moon.angle = angle + math.pi


sun = Sun(SCREEN_SIZE[0], SCREEN_SIZE[1], SEASONS[current_season]['day_length'])
moon = Moon(SCREEN_SIZE[0], SCREEN_SIZE[1], SEASONS[current_season]['day_length'])

def set_season(season):
    global current_season, sun, moon
    current_season = season
    season_properties = SEASONS[season]
    sun = Sun(SCREEN_SIZE[0], SCREEN_SIZE[1], season_properties['day_length'])
    moon = Moon(SCREEN_SIZE[0], SCREEN_SIZE[1], season_properties['day_length'])
 
    print(f'Season set to {season} with properties: {season_properties}')
