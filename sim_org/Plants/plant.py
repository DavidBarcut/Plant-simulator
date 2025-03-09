# plant.py
import pygame
import random
import math
from config import CELL_SIZE,SOIL_ROWS, ROWS, COLS, TIME_SCALE, GEOTROPISM_WEIGHTS, w_PH, w_air, W_geo, W_hydro, W_chemo, W_thermo, SCREEN_SIZE


from soil import soil_properties, SOIL_TYPES, SOILPH
from weather import sun, SEASONS, current_season  

SEED_COLOUR = (34, 139, 34)
SHOOT_COLOUR = (50, 205, 50)
COTYLEDON_COLOUR = (50, 205, 50)
ADULT_LEAF_COLOUR = (50, 205, 50)
FLOWER_BULB_COLOUR = (139, 69, 19)
FLOWER_PETAL_COLOUR = (255, 165, 0)
ROOT = (255, 255, 250)

MAX_ROOT_TIPS = 10

class Seed:
    def __init__(self, x, y, seed_type="small"):
        self.x = x
        self.y = y
        self.seed_type = seed_type
        self.time_to_germinate = 0  
        self.germinated = False
        self.plant = None 

        # Seed weight attributes
        self.starting_weight = 0.05
        self.current_weight = self.starting_weight
        self.seed_status = "healthy"
        self.hydration = 0.0  

        # Seed type properties
        if seed_type == "small":
            self.dry_weight = 1.0
        elif seed_type == "large":
            self.dry_weight = 3.0
        else:
            self.dry_weight = 1.0

        self.saturation_ratio = 1.5
        self.water_absorbed = 0.0
        self.size = 3 
        self.initial_uptake_rate = random.uniform(0.1, 0.2) * self.dry_weight

        self.age = 0  
        self.alive = True

        # Gravity simulation
        self.gravity_speed = 5
        self.on_ground = False
        self.ground_level = SOIL_ROWS * CELL_SIZE

        self.temp = SEASONS[current_season]['temperature']
        self.moisture_factor = 0.0

    def apply_gravity(self):
        if not self.on_ground:
            self.y += self.gravity_speed
            if self.y >= self.ground_level:
                self.y = self.ground_level
                self.on_ground = True
               
                self.plant = Plant(self.x, self.y)

    def update_imbibition(self):
        if not self.on_ground:
            return 

        dt = 10
        self.age += TIME_SCALE / sun.day_length

        if not self.germinated:
            self.time_to_germinate += TIME_SCALE / sun.day_length

        self.plant.time_to_germinate = self.time_to_germinate

        grid_x = int(self.x // CELL_SIZE)
        grid_y = int(self.y // CELL_SIZE)
        if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
            local_moisture = soil_properties['grid'][grid_y][grid_x]['moisture']
        else:
            local_moisture = 0

        optimal_soil_moisture = 10.0  
        self.moisture_factor = max(0, min(local_moisture / optimal_soil_moisture, 1))
        self.temp = SEASONS[current_season]['temperature']

        optimal_temp = 20.0
        sigma_temp = 5.0
        temp_factor = math.exp(-((self.temp - optimal_temp) ** 2) / (2 * sigma_temp ** 2))

        self.water_absorbed += self.initial_uptake_rate * dt * self.moisture_factor * temp_factor
        self.hydration = self.water_absorbed / self.dry_weight
        self.current_weight = self.starting_weight + self.water_absorbed

        if self.hydration >= self.saturation_ratio and not self.germinated:
            self.germinated = True

    def draw(self, screen, simulation_running):
        self.apply_gravity()
        pygame.draw.circle(screen, SEED_COLOUR, (int(self.x), int(self.y)), self.size)

        if simulation_running and self.on_ground:
            self.update_imbibition()
            if self.germinated and self.plant:
                self.plant.grow()
                self.plant.draw(screen)

    def get_seed_status(self):
        if self.temp < 5 or self.temp > 35:
            self.alive = False
            return "plant will not germinate"
        elif self.temp < 10:
            return "Too Cold"
        elif self.temp > 30:
            return "Too Hot"
        elif self.moisture_factor < 0.2:
            return "Low Moisture"
        else:
            return "healthy"

    def get_stats(self):
        if not self.germinated:
            status = self.get_seed_status()
            result = {
                "plant_type": "Sunflower",
                "stage": "seed",
                "status": status,
                "time_to_germinate": self.time_to_germinate,
                "health": "dead" if not self.alive else "healthy",
                "weight": self.current_weight,
                "height": 0,
                "root_depth": 0,
                "age": self.age
            }
            if not self.alive:
                result["death_reason"] = status
            return result
        else:
            return self.plant.get_stats()




MAX_ROOT_TIPS = 10

# Standard directional lambdas.
directions = {
    'left':       lambda x, y: {'x': x - CELL_SIZE, 'y': y},
    'right':      lambda x, y: {'x': x + CELL_SIZE, 'y': y},
    'down':       lambda x, y: {'x': x,            'y': y + CELL_SIZE},
    'up':         lambda x, y: {'x': x,            'y': y - CELL_SIZE},
    'down-left':  lambda x, y: {'x': x - CELL_SIZE, 'y': y + CELL_SIZE},
    'down-right': lambda x, y: {'x': x + CELL_SIZE, 'y': y + CELL_SIZE},

    'left-branch':  lambda x, y: {'x': x - 2*CELL_SIZE, 'y': y + int(CELL_SIZE/2)},
    'right-branch': lambda x, y: {'x': x + 2*CELL_SIZE, 'y': y + int(CELL_SIZE/2)}
}

class Root:
    """
    A root system that starts with one main (tap) root tip and can branch into multiple tips.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tips = [self.RootTip(x, y, direction='down')]
    
    def get_horizon_resistance(self, row):
        horizons = SOIL_TYPES[soil_properties['type']]['horizons']
        cumulative_depth = 0
        for horizon, properties in horizons.items():
            depth = int(ROWS * properties['depth'])
            if cumulative_depth <= row < cumulative_depth + depth:
                return properties['resistance']
            cumulative_depth += depth
        return 1 

    def grow(self):
        """
        Grow each active tip in the system.
        """
        for tip in self.tips[:]:
            tip.grow(self)

    def absorb_moisture(self):
        """
        Determine the available moisture for the plant from the soil beneath the roots.
        Here we use the root's location to sample the soil grid.
        """
        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)
        if 0 <= cell_y < len(soil_properties['grid']) and 0 <= cell_x < len(soil_properties['grid'][0]):
            actual_moisture = soil_properties['grid'][cell_y][cell_x]['moisture']
        else:
            actual_moisture = 0

        return actual_moisture

    def absorb_nutrients(self):
        """
        Determine the nutrient factor available to the plant via the roots.
        """
        nutrients = soil_properties['nutrients']
        nutrient_factor = (
            min(nutrients.get('nitrogen', 0) / 100.0, 1.0) +
            min(nutrients.get('phosphorus', 0) / 100.0, 1.0) +
            min(nutrients.get('potassium', 0) / 100.0, 1.0)
        ) / 3.0
        return nutrient_factor

    def draw(self, screen):
        """
        Draw all active tips.
        """
        for tip in self.tips:
            tip.draw(screen)

    class RootTip:
        """
        Represents a single actively growing root tip.
        Each tip has its own chain of segments and can branch off new tips.
        """
        def __init__(self, x, y, direction=None):
            self.segments = [{'x': x, 'y': y, 'age': 0}]
            self.occupied_positions = {(x, y)}
            self.growth_accumulator = 0.0
            self.growth_counter = 0
            self.direction = direction  
            self.max_width = 4
            self.static_segments = []
            self.max_segments = 70
            self.env_scores = {}

    

        def grow(self, root_system):

            
            if len(self.segments) >= self.max_segments:
                return
            
            daily_root_growth = 4
            base_per_tick_growth = (daily_root_growth / sun.day_length) * TIME_SCALE

           
            last_segment = self.segments[-1]
            x, y = last_segment['x'], last_segment['y']
            standard_dirs = ['left', 'right', 'down', 'up', 'down-left', 'down-right']
            optimal_temp = 20.0
            sigma = 10.0

            for dkey in standard_dirs:
                pos = directions[dkey](x, y)
                grid_x = int(pos['x'] // CELL_SIZE)
                grid_y = int(pos['y'] // CELL_SIZE)



                if (0 <= grid_x < COLS and 0 <= grid_y < ROWS and (pos['x'], pos['y']) not in self.occupied_positions):
                    cell = soil_properties['grid'][grid_y][grid_x]
                    moisture = cell['moisture'] 
                    local_temp = cell['temperature']
                    resistance = root_system.get_horizon_resistance(grid_y)

              
                    temp_factor = math.exp(-((local_temp - optimal_temp) ** 2) / (2 * sigma ** 2))
                    nutrient_factor = root_system.absorb_nutrients()  
        

                    score = (
                        (W_hydro * (moisture / resistance)) *
                        (W_thermo * temp_factor) *
                        (W_chemo * nutrient_factor) *
                        (W_geo   * GEOTROPISM_WEIGHTS[dkey])
                    )
                    self.env_scores[dkey] = score


            # --- Choose a Direction ---
            if self.env_scores and random.random() < 0.7:
                chosen_direction = max(self.env_scores, key=self.env_scores.get)
            elif self.env_scores:
                chosen_direction = random.choice(list(self.env_scores.keys()))
            else:
          
                return

            env_factor = self.env_scores.get(chosen_direction, 1.0)
            pH_value = SOILPH
            optimal_pH = 7.0
            pH_sigma = 0.5
            pH_factor = math.exp(-((pH_value - optimal_pH) ** 2) / (2 * pH_sigma ** 2))

            airation_factor = SOIL_TYPES[soil_properties['type']].get('airation', 1.0)
          


            # --- Accumulate Growth ---
            growth_increment = base_per_tick_growth * env_factor
            self.growth_accumulator += growth_increment

           
            threshold = 1.0  
            if self.growth_accumulator >= threshold:
                self.growth_accumulator -= threshold
                new_segment = directions[chosen_direction](x, y)
                new_segment['age'] = 0
                self.segments.append(new_segment)
                self.occupied_positions.add((new_segment['x'], new_segment['y']))
                self.growth_counter += 1

                if self.growth_counter % 5 == 0:
                    self.static_segments.append({
                        'x': new_segment['x'] - CELL_SIZE, 
                        'y': new_segment['y'] + CELL_SIZE
                    })
                    self.static_segments.append({
                        'x': new_segment['x'] + CELL_SIZE, 
                        'y': new_segment['y'] + CELL_SIZE
                    })

                # --- Branching Logic ---
           
                if self.growth_counter % 2 == 0 and random.random() < 0.8:
                    if len(root_system.tips) < MAX_ROOT_TIPS:
                        bx = new_segment['x']
                        by = new_segment['y']
                   
                        branch_dir = random.choice(['left-branch', 'right-branch'])
                        branch_tip = root_system.RootTip(bx, by, direction=branch_dir)
                        root_system.tips.append(branch_tip)

            # --- Age All Segments ---
            for seg in self.segments:
                seg['age'] += 1

        def draw(self, screen):
            for i in range(len(self.segments) - 1):
                start_pos = (self.segments[i]['x'], self.segments[i]['y'])
                end_pos = (self.segments[i + 1]['x'], self.segments[i + 1]['y'])
                width = min(1 + self.segments[i]['age'] // 10, self.max_width)
                pygame.draw.line(screen, ROOT, start_pos, end_pos, width)

            for segment in self.static_segments:
                pygame.draw.line(screen, ROOT, (segment['x'], segment['y']),
                                 (segment['x'] + 1, segment['y'] - 1), 2)
                pygame.draw.line(screen, ROOT, (segment['x'], segment['y']),
                                 (segment['x'] - 1, segment['y'] - 1), 2)



class Plant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shoot_height = 0
        self.max_height = 200
        self.growth_rate = 1
        self.cotyledon_growth = 0
        self.cotyledon_max_growth = 20
        self.cotyledon_stop_height = 10
        self.stem_above_soil = 0  
        self.cotyledon_sprout_height = None
        self.leaves = []  
        self.flower_bulb_growth = 0
        self.flower_bloom_growth = 0
        self.flower_bloom_start_height = 100
        self.roots = Root(self.x, self.y)
        self.stem_segments = [{'x': self.x, 'y': self.y, 'height': 0}]
        self.stem_width = 1
        self.age = 0.0
        self.shoot_delay = 2
        self.time_to_germinate = 5
        self.stage = "seed"
        self.plant_type = "Sunflower"  
        self.resource_status = []
        self.death_reason = ""


     
        self.max_health = 100
        self.health = self.max_health
        self.alive = True

    def get_daily_growth(self):
        """Return the average daily growth (in cm/day) for the current season."""
        switch_growth_height = 32 
        if self.shoot_height < switch_growth_height:
            return 5.0
        elif self.shoot_height < self.flower_bloom_start_height:
            return 10.0
        else:
            return 5.0
        
    def get_horizon_resistance(self, height):
        horizons = SOIL_TYPES[soil_properties['type']]['horizons']
        cumulative_depth = 0
        for horizon, properties in horizons.items():
            depth = int(ROWS * properties['depth'])
            if cumulative_depth <= height < cumulative_depth + depth:
                return properties['resistance']
            cumulative_depth += depth
        return 1 

    def get_sunlight_factor(self):
        """
        Return a sunlight factor based solely on the current season.
        Adjust the values below to calibrate for your simulation.
        """
        season_factors = {
            "spring": 0.9,
            "summer": 1.0,
            "autumn": 0.7,
            "winter": 0.3
        }
      
        return season_factors.get(current_season, 1.0)
        

    def update_health(self, sunlight_factor, nutrient_factor, moisture_factor, temp, pH):
        self.resource_status.clear()

        optimal_pH = 7.0
        max_ph_deviation = 1.5

      
        if temp >= 50:
            self.die("Extreme heat (>50°C)")
            return
        elif temp >= 45:
            self.resource_status.append("Severe heat stress")
            self.health -= 15
        elif temp > 40:
            self.resource_status.append("Heat stress")
            self.health -= 5
        elif temp > 30:
            self.resource_status.append("Mild heat stress growth reduced")

        if temp <= -5:
            self.die("Extreme cold (<-5°C)")
            return
        elif temp <= -2:
            self.resource_status.append("Severe frost")
            self.health -= 15
        elif temp <= 0:
            self.resource_status.append("Frost damage")
            self.health -= 5
        elif temp < 5:
            self.resource_status.append("Cold stress")
            self.health -= 2
        elif temp < 10:
            self.resource_status.append("Mild cold stress plant growth reduced")


        if moisture_factor < 0.2:
            self.resource_status.append("Low moisture")
            self.health -= 5
        elif moisture_factor > 5.0:
            self.resource_status.append("Waterlogging")
            self.health -= 5

        # pH checks
        if pH < optimal_pH - max_ph_deviation:
            self.resource_status.append("Too acidic")
            self.health -= 3
        elif pH > optimal_pH + max_ph_deviation:
            self.resource_status.append("Too alkaline")
            self.health -= 3

        # Recovery under optimal conditions
        if not self.resource_status:
            health_recovery = 2  # Simple fixed recovery per tick
            self.health = min(self.max_health, self.health + health_recovery)

    
        if self.health <= 0:
            self.die("Accumulated stress")

  
        print(f"Resource status: {', '.join(self.resource_status) if self.resource_status else 'Optimal'}, Health: {self.health:.2f}")

    def die(self, reason="Unknown"):
        """Sets plant status to dead with a specific reason."""
        self.alive = False
        self.death_reason = reason
        print(f"Plant died due to: {self.death_reason}.")



    def grow(self):

        # --- Grow the root system regardless of shoot delay ---
        if self.alive:
            self.age += TIME_SCALE / sun.day_length
            self.roots.grow()

            # --- Grow the shoot only after the delay period ---
            if self.age >= self.shoot_delay:
                # print(f"Plant is {self.age:.2f} days old.")
                daily_growth = self.get_daily_growth()  
                base_per_tick_growth = (daily_growth / sun.day_length) * TIME_SCALE

                shoot_above_soil = self.y - self.shoot_height < SOIL_ROWS * CELL_SIZE

                sunlight_factor = self.get_sunlight_factor() if shoot_above_soil else 1.0
                # print(f"Sunlight factor: {sunlight_factor:.2f}")
                resistance = self.get_horizon_resistance(self.shoot_height)

                moisture_factor = self.roots.absorb_moisture()
                nutrient_factor = self.roots.absorb_nutrients()
                growth_increment = 0

                if sunlight_factor < 0.3:
                    self.resource_status.append("Not enough sunlight")
                if moisture_factor < 0.3:
                    self.resource_status.append("Not enough water")
                if nutrient_factor < 0.3:
                    self.resource_status.append("Low nutrients")
                
                # For demonstration, assume if temperature is outside 10-35, we say "too hot/cold"
                local_temp = SEASONS[current_season]['temperature']
                optimal_temp = 20.0
                sigma = 10.0
                temp_factor = math.exp(-((local_temp - optimal_temp) ** 2) / (2 * sigma ** 2))
                

            

                # cell_x = int(self.x // CELL_SIZE)
                # cell_y = int((self.y - int(self.shoot_height)) // CELL_SIZE)
            

                if shoot_above_soil:
                    growth_increment = base_per_tick_growth * sunlight_factor * moisture_factor * nutrient_factor * temp_factor
                else:
                    growth_increment = (base_per_tick_growth * moisture_factor * nutrient_factor * temp_factor) / resistance

                # print(f"Daily growth: {daily_growth:.2f} cm, Growth increment: {growth_increment:.2f} cm")

                self.update_health(sunlight_factor, nutrient_factor, moisture_factor, local_temp, SOILPH)
                if not self.alive:
                    return  
                if self.shoot_height < self.max_height:
                    self.shoot_height += growth_increment
                    # print(f"Plant height: {self.shoot_height:.2f} cm")
                    self.stem_segments.append({
                        'x': self.x,
                        'y': self.y - self.shoot_height,
                        'height': self.shoot_height
                    })

                if self.y - self.shoot_height < SOIL_ROWS * CELL_SIZE:
                    self.stem_above_soil = SOIL_ROWS * CELL_SIZE - (self.y - self.shoot_height)

                if self.stem_above_soil > 0 and self.cotyledon_growth < self.cotyledon_max_growth:
                    self.cotyledon_growth += growth_increment
                    if self.cotyledon_sprout_height is None:
                        self.cotyledon_sprout_height = self.shoot_height

                MIN_STEM_FOR_BRANCHES = 30
                if self.cotyledon_growth >= self.cotyledon_max_growth:  
                
                    if not self.leaves or ((self.shoot_height - self.leaves[-1]['sprout_height']) >= MIN_STEM_FOR_BRANCHES):
                        self.leaves.append({'growth': 0, 'sprout_height': self.shoot_height})
                    

                    for leaf in self.leaves:
                        if leaf['growth'] < self.cotyledon_max_growth:
                            leaf['growth'] += growth_increment

                if self.stem_above_soil >= self.flower_bloom_start_height:
                    if self.flower_bulb_growth < 10:
                        self.flower_bulb_growth += growth_increment
                    elif self.flower_bloom_growth < 20:
                        self.flower_bloom_growth += growth_increment

    def get_root_depth(self):
        """Compute the maximum vertical depth of the root system below the plant's starting y-coordinate."""
        max_depth = 0
        for tip in self.roots.tips:
            for segment in tip.segments:
              
                if segment['y'] > self.y:
                    depth = segment['y'] - self.y
                    if depth > max_depth:
                        max_depth = depth
        return max_depth
    

    def update_stage(self):
       
        if self.shoot_height < 0.001:
            return "seed"
        elif self.shoot_height < 50:
            return "vegetative"
        else:
            return "flowering"

        print(f"Plant stage: {self.stage}")

    def get_stats(self):
        health_ratio = self.health / self.max_health if self.max_health else 0
        if health_ratio > 0.7:
            health_status = "healthy"
        elif health_ratio < 0.3:
            health_status = "dying"
        else:
            health_status = "stable"
        stem_cells = len(self.stem_segments)
        root_cells = sum(len(tip.segments) for tip in self.roots.tips)
        root_depth = self.get_root_depth()
        weight = (stem_cells + root_cells) * 2 / 1000
        self.stage = self.update_stage()
        resource_status_str = ", ".join(self.resource_status) if self.resource_status else "All good"
        stats = {
            "plant_type": self.plant_type,
            "stage": self.stage,
            "resource_status": resource_status_str,
            "time_to_germinate": self.time_to_germinate,
            "health": health_status,
            "weight": weight,
            "height": self.shoot_height,
            "root_depth": root_depth,
            "age": self.age
        }
        if not self.alive:
            stats["death_reason"] = self.death_reason
        return stats




    def draw(self, screen):
       
        if self.age >= self.shoot_delay:
            for i in range(len(self.stem_segments) - 1):
                start_pos = (self.stem_segments[i]['x'], self.stem_segments[i]['y'])
                end_pos = (self.stem_segments[i + 1]['x'], self.stem_segments[i + 1]['y'])
                self.stem_width = 0.5 + self.stem_above_soil // 20 if self.stem_above_soil > 0 else 1
                pygame.draw.line(screen, SHOOT_COLOUR, start_pos, end_pos, int(self.stem_width))

            top_x, top_y = self.x, self.y - self.shoot_height
            cotyledon_offset = 15 + self.stem_width // 2
            if self.cotyledon_sprout_height is not None:
                cotyledon_y = self.y - min(self.shoot_height, self.cotyledon_sprout_height + self.cotyledon_stop_height)
            else:
                cotyledon_y = top_y

         
        self.roots.draw(screen)

        if self.stem_above_soil > 0:
            if self.cotyledon_growth > 0:
                segment_length = min(self.cotyledon_growth, 10)
                left_segment_end = (top_x - cotyledon_offset, cotyledon_y - segment_length)
                right_segment_end = (top_x + cotyledon_offset, cotyledon_y - segment_length)
                pygame.draw.line(screen, COTYLEDON_COLOUR, (top_x, cotyledon_y), left_segment_end, 2)
                pygame.draw.line(screen, COTYLEDON_COLOUR, (top_x, cotyledon_y), right_segment_end, 2)

            if self.cotyledon_growth > 10:
                leaf_growth = min(self.cotyledon_growth - 10, 20)
                leaf_width = 10 + leaf_growth
                leaf_height = 5 + leaf_growth // 2
                pygame.draw.ellipse(screen, COTYLEDON_COLOUR, (left_segment_end[0] - leaf_width // 2, left_segment_end[1] - leaf_height // 2, leaf_width, leaf_height))  # Left cotyledon
                pygame.draw.ellipse(screen, COTYLEDON_COLOUR, (right_segment_end[0] - leaf_width // 2, right_segment_end[1] - leaf_height // 2, leaf_width, leaf_height))  # Right cotyledon

           
            for leaf in self.leaves:
                if leaf['growth'] > 0:
                    leaf_segment_length = min(leaf['growth'], 5)  
                    leaf_segment_width = 2 + leaf['growth'] // 10  
                    leaf_sprout_y = self.y - min(self.shoot_height, leaf['sprout_height'] + self.cotyledon_stop_height * 2)  
                    leaf_offset = cotyledon_offset + leaf['growth'] // 2  
                    left_segment_end = (top_x - leaf_offset, leaf_sprout_y - leaf_segment_length)
                    right_segment_end = (top_x + leaf_offset, leaf_sprout_y - leaf_segment_length)

                    pygame.draw.line(
                        screen, 
                        ADULT_LEAF_COLOUR, 
                        (int(top_x), int(leaf_sprout_y)), 
                        (int(left_segment_end[0]), int(left_segment_end[1])), 
                        int(leaf_segment_width)
                    )
                    pygame.draw.line(
                        screen, 
                        ADULT_LEAF_COLOUR, 
                        (int(top_x), int(leaf_sprout_y)), 
                        (int(right_segment_end[0]), int(right_segment_end[1])), 
                        int(leaf_segment_width)
)
                    if leaf['growth'] > 10:
                        leaf_growth = min(leaf['growth'] - 10, 20)  
                        leaf_width = 40 + leaf_growth
                        leaf_height = 10 + leaf_growth // 2

                        left_leaf_end_y = left_segment_end[1] + leaf_growth // 3
                        right_leaf_end_y = right_segment_end[1] + leaf_growth // 3

                        pygame.draw.ellipse(screen, ADULT_LEAF_COLOUR, (left_segment_end[0] - leaf_width // 2, left_leaf_end_y - leaf_height // 2, leaf_width, leaf_height))
                        pygame.draw.ellipse(screen, ADULT_LEAF_COLOUR, (right_segment_end[0] - leaf_width // 2, right_leaf_end_y - leaf_height // 2, leaf_width, leaf_height))
                    
        if self.flower_bloom_growth > 0:
        
            petal_count = 20  # Number of petals
            petal_growth = min(self.flower_bloom_growth, 40)
            petal_length = 20 + petal_growth  # Length of petals
            petal_width = 6  # Width of petals

            # Coordinates for the flower's center
            center_x, center_y = self.x, self.y - self.shoot_height

            # Draw petals in a radial arrangement
            for i in range(petal_count):
                angle = i * (360 / petal_count)  # Angle for each petal
                radians = math.radians(angle)

                # Calculate the petal's position based on the angle
                petal_tip_x = center_x + math.cos(radians) * petal_length
                petal_tip_y = center_y + math.sin(radians) * petal_length
                petal_base_left_x = center_x + math.cos(radians - math.pi / 12) * (petal_length // 2)
                petal_base_left_y = center_y + math.sin(radians - math.pi / 12) * (petal_length // 2)
                petal_base_right_x = center_x + math.cos(radians + math.pi / 12) * (petal_length // 2)
                petal_base_right_y = center_y + math.sin(radians + math.pi / 12) * (petal_length // 2)

                # Draw each petal as a polygon
                pygame.draw.polygon(
                    screen,
                    FLOWER_PETAL_COLOUR,
                    [
                        (petal_tip_x, petal_tip_y),
                        (petal_base_left_x, petal_base_left_y),
                        (petal_base_right_x, petal_base_right_y),
                    ],
                )

            # Draw the central disk
            flower_disk_radius = 15 + petal_growth // 3
            pygame.draw.circle(
                screen,
                FLOWER_BULB_COLOUR,  # Dark brown or yellow color
                (center_x, center_y),
                flower_disk_radius,
            )

            # Optionally, add texture to the disk (dots to represent seeds)
            seed_count = 50
            for _ in range(seed_count):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, flower_disk_radius * 0.8)
                seed_x = center_x + math.cos(angle) * distance
                seed_y = center_y + math.sin(angle) * distance
                pygame.draw.circle(screen, (139, 69, 19), (int(seed_x), int(seed_y)), 2)  # Brown seed dots


