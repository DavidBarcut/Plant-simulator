# plants/cactus.py
from .plant import Plant, Root, CELL_SIZE, ROWS, COLS, directions, SHOOT_COLOUR, COTYLEDON_COLOUR, ADULT_LEAF_COLOUR
import pygame
import random
import math
from config import TIME_SCALE
from soil import soil_properties
from weather import sun



class CactusRoot(Root):
        def __init__(self, x, y):
            super().__init__(x, y, target_horizon='B')
            self.max_spread = 2000   # Allow a wider horizontal spread.
            self.tips = [self.Tip(x, y)]

        class Tip(Root.RootTip):
            def grow(self, root_system):
                allowed_depth = root_system.y + root_system.max_depth * CELL_SIZE

                # Check the last segment’s y-position.
                last_segment = self.segments[-1]
                if last_segment['y'] >= allowed_depth:
                    print("Cactus root tip reached maximum allowed depth; skipping further vertical growth.")
                    return

                # Save the number of segments before growth.
                old_segment_count = len(self.segments)

                # Call parent's grow method explicitly.
                Root.RootTip.grow(self, root_system)

                # Validate the newly added segment (if any).
                if len(self.segments) > old_segment_count:
                    new_segment = self.segments[-1]
                    allowed_spread = root_system.max_spread * CELL_SIZE
                    print(f"Cactus new segment at y: {new_segment['y']}, allowed depth: {allowed_depth}")
                    print(f"Cactus new segment x diff: {abs(new_segment['x'] - root_system.x)}, allowed spread: {allowed_spread}")
                    if (new_segment['y'] > allowed_depth or 
                        abs(new_segment['x'] - root_system.x) > allowed_spread):
                        print("Removing cactus root segment: out of allowed bounds.")
                        self.segments.pop()
                        self.occupied_positions.discard((new_segment['x'], new_segment['y']))
                        self.growth_accumulator += 1.0

                # Age all segments.
                for seg in self.segments:
                    seg['age'] += 1



class Cactus(Plant):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.saturation_ratio = 1.5
        # Reuse some of Plant's attributes:
        # self.cotyledon_growth, self.cotyledon_max_growth, etc.
        self.plant = self
        self.roots = CactusRoot(self.x, self.y)
        self.max_height = 80   # Just an example
        self.water_reserve = 0
        self.cladodes = []
        self.cotyledon_max_growth = 10
        self.cotyledon_stop_height = 1

        # Additional flags or counters for each growth stage
        self.cotyledon_withering = 0.0  # 0 -> not withered, 1 -> fully withered
        self.has_produced_shoot = False

    def get_daily_growth(self):
        """Cacti grow more slowly."""
        return 0.2

    def update_health(self, sunlight_factor, nutrient_factor, moisture_factor, growth_increment):
        """
        Cacti handle low moisture better by storing water.
        """
        if moisture_factor > 1.0:
            self.water_reserve += (moisture_factor - 1.0) * 5
            moisture_factor = 1.0
        elif moisture_factor < 0.01 and self.water_reserve > 0:
            self.water_reserve -= 1
            moisture_factor = 0.5

        super().update_health(sunlight_factor, nutrient_factor, moisture_factor, growth_increment)

    def grow(self):
        if self.alive:
            self.roots.grow()


            if self.age >= self.shoot_delay:
                # Let the base class update growth (shoot_height, cotyledon_growth, leaves, stem_segments, etc.)
                super().grow()

                # Calculate a base thickness from the original logic.
            

                # Once cotyledon growth reaches (or exceeds) its maximum, add extra thickness gradually.
                if self.cotyledon_growth >= self.cotyledon_max_growth:
                    self.stem_width = (3 + (self.stem_above_soil // 10)) if self.stem_above_soil > 0 else 1
                    
                else:
                    self.stem_width = (1 + (self.stem_above_soil // 20)) if self.stem_above_soil > 0 else 1


    def draw(self, screen, simulation_running):
        if simulation_running:
            dt = 1
            self.age += dt
            self.grow()
        
    
        # Draw the roots after drawing the above-ground parts.
        self.roots.draw(screen)
        # Only draw above-ground if the plant has passed its shoot delay.
        if self.age >= self.shoot_delay:
            # When the stem breaches the soil, draw a single thick elliptical stem.
            if self.stem_above_soil > 0:
                # Increase thickness faster using excess cotyledon growth if available:
                thickness_multiplier = 2  # adjust as needed
                extra_thickness = 0
                if self.cotyledon_growth > self.cotyledon_max_growth:
                    extra_thickness = int((self.cotyledon_growth - self.cotyledon_max_growth) * thickness_multiplier)
                base_thickness = 10  # baseline stem thickness
                stem_thickness = base_thickness + extra_thickness
                stem_height = self.shoot_height  # current stem height

                # Define a rectangle for the elliptical stem, centered at self.x.
                stem_rect = pygame.Rect(
                    self.x - stem_thickness // 2,
                    self.y - stem_height,
                    stem_thickness,
                    stem_height
                )
                pygame.draw.ellipse(screen, SHOOT_COLOUR, stem_rect)
            else:
                # Before the stem breaches the soil, use the original segmented drawing:
                for i in range(len(self.stem_segments) - 1):
                    start_pos = (self.stem_segments[i]['x'], self.stem_segments[i]['y'])
                    end_pos   = (self.stem_segments[i+1]['x'], self.stem_segments[i+1]['y'])
                    # Compute rectangle that spans from start_pos to end_pos.
                    x = min(start_pos[0], end_pos[0])
                    y = min(start_pos[1], end_pos[1])
                    width = abs(end_pos[0] - start_pos[0])
                    height = abs(end_pos[1] - start_pos[1])
                    rect = (x, y, width, height)
                    pygame.draw.ellipse(screen, SHOOT_COLOUR, rect, int(self.stem_width))
            
            # (Optional) If you want to draw cotyledons or other details when below the soil?
            # Otherwise, when the stem breaches the soil (self.stem_above_soil > 0) we omit them.
            if self.stem_above_soil == 0:
                top_x, top_y = self.x, self.y - self.shoot_height
                cotyledon_offset = 15 + self.stem_width // 2
                if self.cotyledon_sprout_height is not None:
                    cotyledon_y = self.y - min(self.shoot_height, self.cotyledon_sprout_height + self.cotyledon_stop_height)
                else:
                    cotyledon_y = top_y

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
                    pygame.draw.ellipse(screen, COTYLEDON_COLOUR, 
                        (left_segment_end[0] - leaf_width // 2, left_segment_end[1] - leaf_height // 2, leaf_width, leaf_height))
                    pygame.draw.ellipse(screen, COTYLEDON_COLOUR, 
                        (right_segment_end[0] - leaf_width // 2, right_segment_end[1] - leaf_height // 2, leaf_width, leaf_height))
            
            