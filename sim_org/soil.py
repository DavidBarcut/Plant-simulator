# soil.py
import pygame
import random
import math
from config import ROWS, COLS, CELL_SIZE, SCREEN_SIZE
from weather import sun, current_season, SEASONS

SOILPH = 7.0

# Soil types and horizons
SOIL_TYPES = {
    'sandy': {
    'color': (210, 190, 150),  
    'moisture_retention': 0.2,
    'airation': 1.0,
    'nutrients': {'nitrogen': 5, 'phosphorus': 5, 'potassium': 5},
    'horizons': {
        'O': {
            'Name': 'Humus Layer',
            'description': 'Very thin organic layer due to rapid decomposition and erosion.',
            'composition': 'Sparse decomposed organic matter',
            'depth': 0.02,  
            'moisture': 0.05,
            'nutrients': {'nitrogen': 5, 'phosphorus': 2, 'potassium': 2},
            'color': (139, 69, 19),
            'resistance': 1
        },
        'A': {
            'Name': 'Topsoil',
            'description': 'Light-colored topsoil dominated by sand with minimal organic matter.',
            'composition': 'Mostly mineral particles with some organic input',
            'depth': 0.15,
            'moisture': 0.05,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 5},
            'color': (210, 180, 140),
            'resistance': 2
        },
        'E': {
            'Name': 'Eluvial Horizon',
            'description': 'A leached horizon where soluble minerals and nutrients are washed downward.',
            'composition': 'Primarily sand with very little organic content',
            'depth': 0.10,
            'moisture': 0.03,
            'nutrients': {'nitrogen': 0, 'phosphorus': 3, 'potassium': 3},
            'color': (222, 184, 135),
            'resistance': 2
        },
        'B': {
            'Name': 'Subsoil',
            'description': 'Weakly developed subsoil with minor accumulation of minerals from leaching.',
            'composition': 'Mostly sand with trace amounts of accumulated clay and iron',
            'depth': 0.30,
            'moisture': 0.15,  
            'nutrients': {'nitrogen': 5, 'phosphorus': 3, 'potassium': 3},
            'color': (200, 170, 140),
            'resistance': 2
        },
        'C': {
            'Name': 'Parent Material',
            'description': 'Loose, unconsolidated material composed of weathered rock fragments.',
            'composition': 'Coarse particles and weathered rock',
            'depth': 0.30,
            'moisture': 0.04,
            'nutrients': {'nitrogen': 0, 'phosphorus': 2, 'potassium': 2},
            'color': (160, 82, 45),
            'resistance': 2
        },
        'R': {
            'Name': 'Bedrock',
            'description': 'Underlying bedrock, which may be relatively shallow in sandy regions.',
            'composition': 'Solid rock',
            'depth': 0.10,
            'moisture': 0.2,
            'nutrients': {'nitrogen': 5, 'phosphorus': 5, 'potassium': 5},
            'color': (105, 105, 105),
            'resistance': 6
        }
    }
},

'clay': {
    'color': (178, 34, 34),  
    'moisture_retention': 3.0, 
    'airation': 0.3,         
    'nutrients': {'nitrogen': 70, 'phosphorus': 50, 'potassium': 40},  
    'horizons': {
        'O': {
            'name': 'Humus Layer',
            'description': 'A thinner organic layer with limited decomposition due to high moisture.',
            'composition': 'Decomposed organic matter mixed with clay particles',
            'depth': 0.08,  
            'moisture': 3.5,  
            'nutrients': {'nitrogen': 20, 'phosphorus': 15, 'potassium': 10},
            'color': (0, 69, 19),
            'resistance': 2  
        },
        'A': {
            'name': 'Topsoil',
            'description': 'Dense, clay-rich topsoil with high water retention.',
            'composition': 'Mixture of clay, silt, and organic matter',
            'depth': 0.18,  
            'moisture': 4.0, 
            'nutrients': {'nitrogen': 30, 'phosphorus': 20, 'potassium': 15},
            'color': (178, 34, 34),
            'resistance': 4 
        },
        'E': {
            'name': 'Eluvial Horizon',
            'description': 'A minimal horizon with reduced leaching due to low permeability.',
            'composition': 'A sparse mix of sand and silt',
            'depth': 0.05,  
            'moisture': 1.5,  
            'nutrients': {'nitrogen': 25, 'phosphorus': 15, 'potassium': 10},
            'color': (222, 184, 135),
            'resistance': 3
        },
        'B': {
            'name': 'Subsoil',
            'description': 'A subsoil layer with accumulated clay and iron oxides.',
            'composition': 'Concentrated clay, iron, and aluminum compounds',
            'depth': 0.25,
            'moisture': 1.8,  
            'nutrients': {'nitrogen': 40, 'phosphorus': 30, 'potassium': 20},
            'color': (184, 134, 11),
            'resistance': 5 
        },
        'C': {
            'name': 'Weathered Parent Material',
            'description': 'Weathered parent material with clay mineral content.',
            'composition': 'Partially weathered rock with clay components',
            'depth': 0.25,
            'moisture': 0.6,
            'nutrients': {'nitrogen': 35, 'phosphorus': 25, 'potassium': 20},
            'color': (160, 82, 45),
            'resistance': 5
        },
        'R': {
            'name': 'Bedrock',
            'description': 'Underlying bedrock, largely unaffected by soil processes.',
            'composition': 'Solid rock',
            'depth': 0.05,
            'moisture': 0,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 5},
            'color': (105, 105, 105),
            'resistance': 6
        }
    }
},

    'silt': {
    'color': (215, 190, 160),  
    'moisture_retention': 1.1,  
    'airation': 0.7,        
    'nutrients': {'nitrogen': 65, 'phosphorus': 45, 'potassium': 35},
    'horizons': {
        'O': {
            'name': 'Humus Layer',
            'description': 'A thin layer of decomposing organic matter that slowly integrates into the soil.',
            'composition': 'Decomposed organic material',
            'depth': 0.08,  
            'moisture': 0.4,
            'nutrients': {'nitrogen': 12, 'phosphorus': 8, 'potassium': 8},
            'color': (139, 69, 19),
            'resistance': 1
        },
        'A': {
            'name': 'Top Soil',
            'description': 'A well-developed, dark topsoil rich in both organic matter and mineral nutrients.',
            'composition': 'A balanced mix of silt particles and organic inputs',
            'depth': 0.25,  
            'moisture': 0.65,
            'nutrients': {'nitrogen': 30, 'phosphorus': 25, 'potassium': 20},
            'color': (205, 170, 130),
            'resistance': 2
        },
        'E': {
            'name': 'Eluvial Horizon',
            'description': 'A subtle, thin horizon where slight leaching of minerals occurs.',
            'composition': 'Primarily silt with minimal organic residue',
            'depth': 0.03, 
            'moisture': 0.35,
            'nutrients': {'nitrogen': 18, 'phosphorus': 13, 'potassium': 9},
            'color': (222, 184, 135),
            'resistance': 3
        },
        'B': {
            'name': 'Subsoil',
            'description': 'A compact subsoil where minerals and iron oxides accumulate.',
            'composition': 'Concentrated silt with minor clay and iron oxide enrichment',
            'depth': 0.30,
            'moisture': 0.65,
            'nutrients': {'nitrogen': 32, 'phosphorus': 22, 'potassium': 18},
            'color': (180, 130, 15),
            'resistance': 4
        },
        'C': {
            'name': 'Weathered Parent Material',
            'description': 'Weathered parent material containing partially decomposed silt and rock fragments.',
            'composition': 'Weathered rock fragments mixed with silt',
            'depth': 0.30,
            'moisture': 0.55,
            'nutrients': {'nitrogen': 28, 'phosphorus': 18, 'potassium': 13},
            'color': (160, 82, 45),
            'resistance': 5
        },
        'R': {
            'name': 'Bedrock',
            'description': 'Underlying bedrock, occasionally overlain by weathered silt deposits.',
            'composition': 'Solid rock',
            'depth': 0.05,
            'moisture': 0.3,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 5},
            'color': (105, 105, 105),
            'resistance': 6
        }
    }
},
    'peat': {
    'color': (153, 101, 21),  
    'moisture_retention': 3.5,  
    'airation': 0.5,         
    'nutrients': {'nitrogen': 30, 'phosphorus': 15, 'potassium': 10},  
    'horizons': {
        'O': {
            'Name': 'Humus Layer',
            'description': 'A thick, fibrous layer of partially decomposed plant material typical of peat bogs.',
            'composition': 'Partially decomposed plant material',
            'depth': 0.30,
            'moisture': 0.9,
            'nutrients': {'nitrogen': 15, 'phosphorus': 8, 'potassium': 5},
            'color': (139, 69, 19),
            'resistance': 1
        },
        'A': {
            'name': 'Topsoil',
            'description': 'A thin transitional layer where a small amount of mineral material mixes with the organic peat.',
            'composition': 'Limited mineral particles and organic matter',
            'depth': 0.05,
            'moisture': 0.8,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 5},
            'color': (170, 130, 90),
            'resistance': 2
        },
        'E': {
            'name': 'Eluvial Horizon',
            'description': 'A minimal leached layer due to the overwhelming organic content and low mineral input.',
            'composition': 'Sparse mineral residue',
            'depth': 0.02,
            'moisture': 0.7,
            'nutrients': {'nitrogen': 5, 'phosphorus': 3, 'potassium': 2},
            'color': (200, 180, 150),
            'resistance': 2
        },
        'B': {
            'name': 'Subsoil',
            'description': 'A thin mineral transition layer marking the start of underlying mineral matter.',
            'composition': 'Accumulated mineral particles with minor organic influence',
            'depth': 0.10,
            'moisture': 0.6,
            'nutrients': {'nitrogen': 8, 'phosphorus': 4, 'potassium': 4},
            'color': (180, 140, 110),
            'resistance': 3
        },
        'C': {
            'name': 'Parent Material',
            'description': 'Weathered parent material beneath the peat deposit.',
            'composition': 'Weathered rock fragments',
            'depth': 0.15,
            'moisture': 0.4,
            'nutrients': {'nitrogen': 5, 'phosphorus': 2, 'potassium': 2},
            'color': (160, 100, 70),
            'resistance': 4
        },
        'R': {
            'name': 'Bedrock',
            'description': 'Underlying bedrock.',
            'composition': 'Solid rock',
            'depth': 0.05,
            'moisture': 0.5,
            'nutrients': {'nitrogen': 0, 'phosphorus': 0, 'potassium': 0},
            'color': (105, 105, 105),
            'resistance': 6
        }
    }
},
    'chalk': {
    'color': (245, 245, 220),  
    'moisture_retention': 0.3,  
    'airation': 0.8,          
    'nutrients': {'nitrogen': 20, 'phosphorus': 10, 'potassium': 5}, 
    'horizons': {
        'O': {
            'name': 'Humus Layer',
            'description': 'Very thin organic layer, often nearly absent due to rapid decomposition.',
            'composition': 'Sparse decomposed organic matter',
            'depth': 0.01,  
            'moisture': 2.1,
            'nutrients': {'nitrogen': 5, 'phosphorus': 3, 'potassium': 3},
            'color': (139, 69, 19),
            'resistance': 1
        },
        'A': {
            'name': 'Topsoil',
            'description': 'Light-colored, chalky topsoil with minimal organic matter and rapid drainage.',
            'composition': 'Mix of mineral particles with very little organic input',
            'depth': 0.10, 
            'moisture': 1.2,
            'nutrients': {'nitrogen': 15, 'phosphorus': 8, 'potassium': 5},
            'color': (230, 220, 200),
            'resistance': 2
        },
        'E': {
            'name': 'Eluvial Horizon',
            'description': 'A thin, leached horizon where soluble materials are washed out.',
            'composition': 'Primarily mineral particles with negligible organic residue',
            'depth': 0.05,
            'moisture': 1.0,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 3},
            'color': (235, 225, 210),
            'resistance': 2
        },
        'B': {
            'name': 'Subsoil',
            'description': 'Subsoil showing slight accumulation of leached minerals and calcium carbonate.',
            'composition': 'Accumulated minerals with traces of clay and carbonate precipitates',
            'depth': 0.20,  
            'moisture': 0.3,
            'nutrients': {'nitrogen': 15, 'phosphorus': 10, 'potassium': 5},
            'color': (230, 230, 210),
            'resistance': 3
        },
        'C': {
            'name': 'Parent Material',
            'description': 'Weathered parent material comprised of fragmented chalk and limestone.',
            'composition': 'Weathered chalk and limestone fragments',
            'depth': 0.30,
            'moisture': 0.3,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 3},
            'color': (245, 245, 220),
            'resistance': 4
        },
        'R': {
            'name': 'Bedrock',
            'description': 'Underlying solid chalk or limestone bedrock.',
            'composition': 'Consolidated chalk or limestone',
            'depth': 0.10,
            'moisture': 0.2,
            'nutrients': {'nitrogen': 0, 'phosphorus': 0, 'potassium': 0},
            'color': (240, 240, 230),
            'resistance': 6
        }
    }
},

    'loam': {
    'color': (120, 70, 40), 
    'moisture_retention': 1.0, 
    'airation': 0.8,  
    'nutrients': {'nitrogen': 75, 'phosphorus': 55, 'potassium': 45},
    'horizons': {
        'O': {
            'Name': 'Humus Layer',
            'description': 'A rich organic layer full of decomposed plant material and humus.',
            'composition': 'Decomposed organic matter',
            'depth': 0.10,
            'moisture': 2.5,  
            'nutrients': {'nitrogen': 20, 'phosphorus': 15, 'potassium': 10},
            'color': (90, 50, 20),  
            'resistance': 1 
        },
        'A': {
            'Name': 'Topsoil',
            'description': 'Dark, nutrient-rich topsoil with a balanced mix of sand, silt, and clay.',
            'composition': 'Mixture of mineral particles and organic matter',
            'depth': 0.20,
            'moisture': 2.0,  
            'nutrients': {'nitrogen': 35, 'phosphorus': 25, 'potassium': 20},
            'color': (120, 70, 40), 
            'resistance': 2  
        },
        'E': {
            'Name': 'Eluvial Horizon',
            'description': 'A subtle, leached horizon with diminished organic content; often very thin or absent.',
            'composition': 'Primarily mineral particles with minimal organic matter',
            'depth': 0.05,  
            'moisture': 1.5,
            'nutrients': {'nitrogen': 25, 'phosphorus': 15, 'potassium': 10},
            'color': (200, 170, 140), 
            'resistance': 3
        },
        'B': {
            'Name': 'Subsoil',
            'description': 'Subsoil zone where clay and minerals accumulate, less fertile than the A horizon.',
            'composition': 'Accumulated clay, iron, and other minerals',
            'depth': 0.30,
            'moisture': 1.2,  
            'nutrients': {'nitrogen': 40, 'phosphorus': 30, 'potassium': 25},
            'color': (160, 100, 60), 
            'resistance': 4
        },
        'C': {
            'Name': 'Parent Material',
            'description': 'Weathered parent material that is less altered by soil processes.',
            'composition': 'Partially weathered rock fragments',
            'depth': 0.25,
            'moisture': 0.6,
            'nutrients': {'nitrogen': 35, 'phosphorus': 25, 'potassium': 20},
            'color': (140, 90, 50),
            'resistance': 5
        },
        'R': {
            'Name': 'Bedrock',
            'description': 'Underlying solid rock that influences soil formation.',
            'composition': 'Intact bedrock',
            'depth': 0.05,
            'moisture': 0,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 5},
            'color': (105, 105, 105),
            'resistance': 6
        }
    }
},
    'brown_earth': {
    'color': (165, 42, 42), 
    'moisture_retention': 1, 
    'airation': 0.8,  
    'nutrients': {'nitrogen': 75, 'phosphorus': 55, 'potassium': 45},
    'horizons': {
        'O': {
            'description': 'A rich organic layer abundant in decomposed plant material and humus.',
            'composition': 'Decomposed organic matter',
            'depth': 0.10,
            'moisture': 2.5, 
            'nutrients': {'nitrogen': 25, 'phosphorus': 20, 'potassium': 15},
            'color': (139, 69, 19),
            'resistance': 1 
        },
        'A': {
            'description': 'Dark, nutrient-rich topsoil formed by a mix of organic matter and mineral particles.',
            'composition': 'A mix of mineral particles and organic matter',
            'depth': 0.20,
            'moisture': 2.5,
            'nutrients': {'nitrogen': 35, 'phosphorus': 25, 'potassium': 20},
            'color': (130, 65, 40),  
            'resistance': 2
        },
        'E': {
            'description': 'A subtle, lightly leached zone with reduced organic content.',
            'composition': 'Primarily mineral particles',
            'depth': 0.05, 
            'moisture': 0.4,
            'nutrients': {'nitrogen': 30, 'phosphorus': 20, 'potassium': 15},
            'color': (222, 184, 135),
            'resistance': 3
        },
        'B': {
            'description': 'A subsoil zone enriched with accumulated clay, iron, and minerals from above.',
            'composition': 'Accumulated clay, iron, and other minerals',
            'depth': 0.30,
            'moisture': 1.5, 
            'nutrients': {'nitrogen': 40, 'phosphorus': 30, 'potassium': 20},
            'color': (160, 100, 50), 
            'resistance': 4
        },
        'C': {
            'description': 'Weathered parent material that is less altered by soil processes.',
            'composition': 'Partially weathered rock fragments',
            'depth': 0.25,
            'moisture': 1.0,
            'nutrients': {'nitrogen': 35, 'phosphorus': 25, 'potassium': 20},
            'color': (160, 82, 45),
            'resistance': 5
        },
        'R': {
            'description': 'Underlying solid rock that influences soil formation.',
            'composition': 'Solid rock',
            'depth': 0.05,
            'moisture': 0.3,
            'nutrients': {'nitrogen': 10, 'phosphorus': 5, 'potassium': 5},
            'color': (105, 105, 105),
            'resistance': 6
        }
    }
}
}


current_soil_type = 'loam'


def print_moisture_grid(grid):
    print("Moisture Grid:")
    for j, row in enumerate(grid):
        row_values = [f"{cell['moisture']:.1f}" for cell in row]
        print(f"Row {j}: {', '.join(row_values)}")

def initialize_soil_grid(soil_type):
    """Initialize the soil grid based on soil type and its horizons."""
    horizons = SOIL_TYPES[soil_type]['horizons']
    grid = []
    current_row = 0

    for horizon, properties in horizons.items():
        depth = int(ROWS * properties['depth'])
        horizon_nutrients = properties.get('nutrients', {})
        for _ in range(depth):
            if current_row >= ROWS:
                break
            row_cells = []
            for col in range(COLS):
                base_moisture = properties['moisture']
                # Reduce variation: change noise from std dev 2 to 0.5 for a more lax moisture variation.
                moisture = max(0, base_moisture + random.gauss(0, 0.5))
                nitrogen = max(0, horizon_nutrients.get('nitrogen', 0) + random.gauss(0, 2))
                phosphorus = max(0, horizon_nutrients.get('phosphorus', 0) + random.gauss(0, 2))
                potassium = max(0, horizon_nutrients.get('potassium', 0) + random.gauss(0, 2))
                cell = {
                    'moisture': moisture,
                    'nutrients': {
                        'nitrogen': nitrogen,
                        'phosphorus': phosphorus,
                        'potassium': potassium
                    },
                    'base_temperature': 15, 
                    'temperature': 15  
                }
                row_cells.append(cell)
            grid.append(row_cells)
            current_row += 1

    while len(grid) < ROWS:
        row_cells = [{'moisture': 0,
                      'nutrients': {'nitrogen': 0, 'phosphorus': 0, 'potassium': 0},
                      'base_temperature': 15,
                      'temperature': 15} for _ in range(COLS)]
        grid.append(row_cells)
    print_moisture_grid(grid)
    return grid

soil_properties = {
    'type': 'loam',
    'color': SOIL_TYPES['loam']['color'],
    'moisture_retention': SOIL_TYPES['loam']['moisture_retention'],
    'airation': SOIL_TYPES['loam']['airation'],
    'nutrients': SOIL_TYPES['loam']['nutrients'], 
    'grid': initialize_soil_grid('loam')
}

def update_soil_grid_temperature(soil_grid):
    """
    Updates the 'temperature' field for each cell in the soil grid.
    Temperature is computed based on:
      - The base (seasonal) temperature.
      - Diurnal variation modeled with a cosine function.
      - A depth factor that reduces amplitude with depth.
      - A moisture factor that damps temperature variation in wetter areas.
    """

    # Global (seasonal) base temperature.
    base_temp = SEASONS[current_season]['temperature']

   
    diurnal_amplitude = 10.0  # degrees Celsius

    depth_decay = 5.0  
   
    moisture_decay = 10.0  

  
    phase = sun.angle - math.pi / 2

    for i, row in enumerate(soil_grid):
      
        depth_factor = math.exp(-i / depth_decay)
        for cell in row:
            # Moisture factor: higher moisture dampens the amplitude.
            moisture_factor = math.exp(-cell['moisture'] / moisture_decay)
            effective_amplitude = diurnal_amplitude * depth_factor * moisture_factor
            diurnal_variation = effective_amplitude * math.cos(phase)
            cell['temperature'] = cell['base_temperature'] + diurnal_variation

def update_moisture_gradient(x, y, size):
    x = int(x)
    y = int(y)
    horizons = SOIL_TYPES[soil_properties['type']]['horizons']
    max_distance = size * 2 

    for i in range(-max_distance, max_distance + 1):
        for j in range(-max_distance, max_distance + 1):
            grid_x = x + i
            grid_y = y + j
            if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                distance = math.sqrt(i**2 + j**2)
                if distance <= max_distance:
                   
                    cumulative_depth = 0
                    for horizon, properties in horizons.items():
                        depth = int(ROWS * properties['depth'])
                        if cumulative_depth <= grid_y < cumulative_depth + depth:
                            moisture_retention = properties['moisture']
                            break
                        cumulative_depth += depth

                   
                    moisture_increase = max(0, (size * 2 - distance) * moisture_retention)
                 
                    soil_properties['grid'][grid_y][grid_x]['moisture'] += moisture_increase



def set_soil_type(soil_type):
    """Update global soil_properties and reinitialize the grid."""
    soil_properties['type'] = soil_type
    soil_properties['color'] = SOIL_TYPES[soil_type]['color']
    soil_properties['moisture_retention'] = SOIL_TYPES[soil_type]['moisture_retention']
    soil_properties['airation'] = SOIL_TYPES[soil_type]['airation']
    soil_properties['nutrients'] = SOIL_TYPES[soil_type]['nutrients']
    soil_properties['grid'] = initialize_soil_grid(soil_type)
    print(f'Soil type set to {soil_type}')


def draw_soil_horizons(screen):
    horizons = SOIL_TYPES[soil_properties['type']]['horizons']
    current_row = 0

    for horizon, properties in horizons.items():
        depth = int(ROWS * properties['depth'])
        color = properties['color']
        for _ in range(depth):
            if current_row >= ROWS:
                break
            for col in range(COLS):
                x = col * CELL_SIZE
                y = current_row * CELL_SIZE + SCREEN_SIZE[1] // 2
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)
              
            current_row += 1

   
    while current_row < ROWS:
        for col in range(COLS):
            x = col * CELL_SIZE
            y = current_row * CELL_SIZE + SCREEN_SIZE[1] // 2
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (105, 105, 105), rect)  
         
        current_row += 1
