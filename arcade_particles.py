"""
Arcade particle effects for Match 3 game with pixel art theme
"""
import arcade
import pygame
import math
import random
from typing import Tuple, List

class PixelArcadeParticleSystem:
    """Wrapper to use Arcade particles in a Pygame context with pixel art styling"""
    
    def __init__(self, screen_width: int, screen_height: int):
        # Create a minimal arcade window context for particle systems
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.emitters = []
        
    def create_bomb_explosion(self, x: float, y: float) -> None:
        """Create a pixel art themed bomb explosion"""
        
        # Create the main explosion emitter
        emitter = arcade.Emitter(
            center_xy=(x, y),
            emit_controller=arcade.EmitBurst(particle_count=30),
            particle_factory=lambda emitter: arcade.LifespanParticle(
                filename_or_texture=self._create_pixel_texture("explosion", (255, 200, 0)),
                change_xy=(
                    random.uniform(-150, 150),  # Horizontal velocity
                    random.uniform(-150, 150)   # Vertical velocity
                ),
                lifetime=random.uniform(0.5, 1.2),
                scale=random.uniform(0.5, 2.0)
            )
        )
        self.emitters.append(emitter)
        
        # Create secondary spark particles
        spark_emitter = arcade.Emitter(
            center_xy=(x, y),
            emit_controller=arcade.EmitBurst(particle_count=20),
            particle_factory=lambda emitter: arcade.LifespanParticle(
                filename_or_texture=self._create_pixel_texture("spark", (255, 100, 0)),
                change_xy=(
                    random.uniform(-200, 200),
                    random.uniform(-200, 200)
                ),
                lifetime=random.uniform(0.3, 0.8),
                scale=random.uniform(0.3, 1.0)
            )
        )
        self.emitters.append(spark_emitter)
        
        # Create smoke particles
        smoke_emitter = arcade.Emitter(
            center_xy=(x, y),
            emit_controller=arcade.EmitBurst(particle_count=15),
            particle_factory=lambda emitter: arcade.LifespanParticle(
                filename_or_texture=self._create_pixel_texture("smoke", (100, 100, 100)),
                change_xy=(
                    random.uniform(-50, 50),
                    random.uniform(-100, -20)  # Smoke rises
                ),
                lifetime=random.uniform(1.0, 2.0),
                scale=random.uniform(1.0, 3.0)
            )
        )
        self.emitters.append(smoke_emitter)
    
    def _create_pixel_texture(self, particle_type: str, color: Tuple[int, int, int]) -> arcade.Texture:
        """Create pixel art styled textures for particles"""
        
        if particle_type == "explosion":
            # Create a pixelated explosion particle (diamond shape)
            size = 8
            pixels = []
            for y in range(size):
                row = []
                for x in range(size):
                    # Diamond/circle pattern
                    center = size // 2
                    distance = abs(x - center) + abs(y - center)
                    if distance <= center:
                        # Create gradient effect
                        alpha = max(0, 255 - (distance * 60))
                        row.append((*color, alpha))
                    else:
                        row.append((0, 0, 0, 0))  # Transparent
                pixels.append(row)
                
        elif particle_type == "spark":
            # Create small bright spark (cross shape)
            size = 4
            pixels = []
            for y in range(size):
                row = []
                for x in range(size):
                    center = size // 2
                    if (x == center) or (y == center):
                        row.append((*color, 255))
                    else:
                        row.append((0, 0, 0, 0))
                pixels.append(row)
                
        elif particle_type == "smoke":
            # Create pixelated smoke cloud
            size = 6
            pixels = []
            for y in range(size):
                row = []
                for x in range(size):
                    # Random smoke pattern
                    if random.random() > 0.3:
                        alpha = random.randint(100, 200)
                        row.append((*color, alpha))
                    else:
                        row.append((0, 0, 0, 0))
                pixels.append(row)
        
        # Convert to arcade texture
        return self._pixels_to_texture(pixels, size)
    
    def _pixels_to_texture(self, pixels: List[List[Tuple[int, int, int, int]]], size: int) -> arcade.Texture:
        """Convert pixel array to arcade texture"""
        # Create a pygame surface from pixels
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        for y, row in enumerate(pixels):
            for x, pixel in enumerate(row):
                if len(pixel) == 4 and pixel[3] > 0:  # Has alpha and not transparent
                    surface.set_at((x, y), pixel)
        
        # Scale up for pixel art effect (4x)
        scaled_size = size * 4
        scaled_surface = pygame.transform.scale(surface, (scaled_size, scaled_size))
        
        # Convert pygame surface to arcade texture
        # We'll need to save as temporary image and load it
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        pygame.image.save(scaled_surface, temp_file.name)
        texture = arcade.load_texture(temp_file.name)
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return texture
    
    def update(self, dt: float):
        """Update all particle emitters"""
        for emitter in self.emitters[:]:
            emitter.update()
            
            # Remove finished emitters
            if len(emitter.get_particles()) == 0 and emitter.can_reap():
                self.emitters.remove(emitter)
    
    def render_to_pygame(self, pygame_screen: pygame.Surface):
        """Render particles to pygame surface"""
        # This is a simplified approach - we'll convert arcade particles to pygame rendering
        for emitter in self.emitters:
            particles = emitter.get_particles()
            for particle in particles:
                # Get particle position and properties
                x, y = particle.center_x, particle.center_y
                
                # Convert arcade coordinates to pygame coordinates (flip Y)
                pygame_y = pygame_screen.get_height() - y
                
                # Determine particle color based on texture or use default
                if hasattr(particle, 'texture') and particle.texture:
                    # For now, use colored circles as simplified rendering
                    if "explosion" in str(particle.texture):
                        color = (255, 200, 0)
                    elif "spark" in str(particle.texture):
                        color = (255, 100, 0)
                    else:  # smoke
                        color = (100, 100, 100)
                else:
                    color = (255, 255, 255)
                
                # Calculate size and alpha based on particle properties
                size = max(1, int(particle.scale * 4))  # Scale for pixel art
                alpha = int(255 * particle.alpha) if hasattr(particle, 'alpha') else 255
                
                # Create surface with alpha for the particle
                if size > 0 and alpha > 0:
                    particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, (*color, alpha), (size, size), size)
                    pygame_screen.blit(particle_surf, (int(x - size), int(pygame_y - size)))
    
    def is_finished(self) -> bool:
        """Check if all effects are finished"""
        return len(self.emitters) == 0


# Simplified pixel particle system that works better with Pygame
class PixelParticleSystem:
    """Pure pygame pixel art particle system"""
    
    def __init__(self):
        self.effects = []
    
    def create_bomb_explosion(self, x: float, y: float):
        """Create pixel art bomb explosion"""
        effect = PixelExplosionEffect(x, y)
        self.effects.append(effect)
    
    def create_rocket_trail(self, start_x: float, start_y: float, direction: str, board_bounds: Tuple[int, int, int, int]):
        """Create rocket trail effect
        Args:
            start_x, start_y: Starting position
            direction: 'horizontal', 'vertical', or 'cross'
            board_bounds: (left, top, right, bottom) bounds of the game board
        """
        if direction == 'horizontal':
            effect = RocketTrailEffect(start_x, start_y, 'horizontal', board_bounds)
            self.effects.append(effect)
        elif direction == 'vertical':
            effect = RocketTrailEffect(start_x, start_y, 'vertical', board_bounds)
            self.effects.append(effect)
        elif direction == 'cross':
            # Create both horizontal and vertical trails for cross pattern
            h_effect = RocketTrailEffect(start_x, start_y, 'horizontal', board_bounds)
            v_effect = RocketTrailEffect(start_x, start_y, 'vertical', board_bounds)
            self.effects.append(h_effect)
            self.effects.append(v_effect)
    
    def create_bomb_rocket_trail(self, start_x: float, start_y: float, board_bounds: Tuple[int, int, int, int]):
        """Create large bomb-colored rocket trail in cross pattern (3-wide)"""
        # Create three horizontal trails (3-wide effect)
        for offset in [-1, 0, 1]:
            adjusted_y = start_y + (offset * 32)  # Assuming 32px tile size for spacing
            h_effect = BombRocketTrailEffect(start_x, adjusted_y, 'horizontal', board_bounds)
            self.effects.append(h_effect)
        
        # Create three vertical trails (3-wide effect)
        for offset in [-1, 0, 1]:
            adjusted_x = start_x + (offset * 32)  # Assuming 32px tile size for spacing
            v_effect = BombRocketTrailEffect(adjusted_x, start_y, 'vertical', board_bounds)
            self.effects.append(v_effect)
    
    def create_lightning_arc(self, x: float, y: float):
        """Create dramatic lightning arc effect"""
        effect = LightningArcEffect(x, y)
        self.effects.append(effect)
    
    def create_board_wipe_arcs(self, start_x: float, start_y: float, target_positions: List[Tuple[float, float]], target_color):
        """Create board wipe arcing lines effect"""
        effect = BoardWipeArcEffect(start_x, start_y, target_positions, target_color)
        self.effects.append(effect)
    
    def create_row_lightning_arc(self, row: int, direction: str, board_bounds: Tuple[int, int, int, int]):
        """Create lightning arc that blasts across an entire row"""
        effect = RowLightningArcEffect(row, direction, board_bounds)
        self.effects.append(effect)
    
    def create_nuclear_megabomb(self, x: float, y: float):
        """Create nuclear-style megabomb explosion with shockwave, smoke, and massive explosion"""
        effect = NuclearMegabombEffect(x, y)
        self.effects.append(effect)
    
    def create_black_hole_lightning_explosion(self, x: float, y: float):
        """Create massive lightning explosion from black hole center"""
        effect = BlackHoleLightningExplosion(x, y)
        self.effects.append(effect)
    
    def update(self, dt: float):
        """Update all effects"""
        for effect in self.effects[:]:
            effect.update(dt)
            if effect.is_finished():
                self.effects.remove(effect)
    
    def draw(self, screen: pygame.Surface):
        """Draw all effects"""
        for effect in self.effects:
            effect.draw(screen)
    
    def is_finished(self) -> bool:
        """Check if all effects are finished"""
        return len(self.effects) == 0


class PixelExplosionEffect:
    """Dramatic pixel art explosion effect with layered burst"""
    
    def __init__(self, x: float, y: float):
        self.particles = []
        self.duration = 2.8
        self.elapsed = 0.0
        
        # CORE EXPLOSION - MASSIVE bright yellow center burst
        for i in range(20):
            angle = (i / 20) * math.pi * 2  # Even distribution in circle
            speed = random.uniform(120, 200)
            
            particle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(1.8, 2.5),
                'max_life': random.uniform(1.8, 2.5),
                'color': (255, 255, 150),  # Brighter pale yellow core
                'size': random.randint(35, 50),  # MASSIVE core pieces
                'type': 'core'
            }
            self.particles.append(particle)
        
        # MAIN EXPLOSION RING - HUGE Orange/yellow burst
        for i in range(50):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(200, 400)
            
            particle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(1.4, 2.2),
                'max_life': random.uniform(1.4, 2.2),
                'color': random.choice([
                    (255, 255, 100),   # Ultra bright yellow
                    (255, 240, 50),    # Golden yellow  
                    (255, 200, 20),    # Bright orange
                    (255, 150, 0),     # Deep orange
                ]),
                'size': random.randint(20, 35),  # MUCH bigger explosion pieces
                'type': 'explosion'
            }
            self.particles.append(particle)
        
        # OUTER EXPLOSION - MASSIVE Red-orange outer ring
        for i in range(40):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(300, 550)
            
            particle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(1.2, 1.8),
                'max_life': random.uniform(1.2, 1.8),
                'color': random.choice([
                    (255, 160, 0),     # Bright orange-red
                    (255, 140, 20),    # Red-orange
                    (255, 120, 10),    # Dark orange
                    (220, 100, 5),     # Brown-orange
                ]),
                'size': random.randint(18, 28),  # MUCH bigger outer pieces
                'type': 'outer'
            }
            self.particles.append(particle)
        
        # BRIGHT SPARKS - LIGHTNING FAST white-hot particles
        for i in range(45):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(400, 700)
            
            particle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.6, 1.2),
                'max_life': random.uniform(0.6, 1.2),
                'color': random.choice([
                    (255, 255, 255),   # Pure white
                    (255, 255, 230),   # Warm white
                    (255, 250, 180),   # Pale yellow-white
                ]),
                'size': random.randint(8, 15),  # MUCH bigger sparks
                'type': 'spark'
            }
            self.particles.append(particle)
        
        # DEBRIS CHUNKS - HUGE flying pieces
        for i in range(35):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(180, 320)
            
            particle = {
                'x': x + random.uniform(-25, 25),
                'y': y + random.uniform(-20, 20),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(1.8, 2.8),
                'max_life': random.uniform(1.8, 2.8),
                'color': random.choice([
                    (120, 70, 35),     # Lighter brown
                    (90, 50, 25),      # Dark brown
                    (140, 80, 40),     # Medium brown
                    (70, 40, 20),      # Very dark
                ]),
                'size': random.randint(10, 18),  # MUCH bigger debris
                'type': 'debris'
            }
            self.particles.append(particle)
        
        # SMOKE PLUMES - MASSIVE billowing gray clouds
        for i in range(30):
            angle = random.uniform(-math.pi/2.5, math.pi + math.pi/2.5)
            speed = random.uniform(100, 200)
            
            particle = {
                'x': x + random.uniform(-50, 50),
                'y': y + random.uniform(-25, 25),
                'vx': math.cos(angle) * speed * 0.7,
                'vy': math.sin(angle) * speed - 70,
                'life': random.uniform(2.5, 4.0),
                'max_life': random.uniform(2.5, 4.0),
                'color': random.choice([
                    (150, 150, 150),   # Light gray
                    (130, 130, 130),   # Medium gray
                    (110, 110, 110),   # Dark gray
                    (90, 90, 90),      # Darker gray
                ]),
                'size': random.randint(20, 40),  # MASSIVE smoke clouds
                'type': 'smoke'
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update explosion particles with dramatic layered physics"""
        self.elapsed += dt
        
        for particle in self.particles[:]:
            # Update position
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            # Physics based on explosion layer
            if particle['type'] == 'core':
                # Core pieces - slow, heavy, dramatic
                particle['vy'] += 180 * dt  # Medium gravity
                particle['vx'] *= 0.98      # Air resistance
                
            elif particle['type'] in ['explosion', 'outer']:
                # Main explosion - medium speed, gravity
                particle['vy'] += 220 * dt  # Gravity
                particle['vx'] *= 0.99      # Slight air resistance
                
            elif particle['type'] == 'spark':
                # Sparks - fast, light, quick fade
                particle['vy'] += 150 * dt  # Light gravity
                particle['vx'] *= 0.995     # Minimal air resistance
                
            elif particle['type'] == 'debris':
                # Debris - heavy, tumbling
                particle['vy'] += 320 * dt  # Heavy gravity
                particle['vx'] *= 0.97      # More air resistance
                
            else:  # smoke
                # Smoke - rises up, spreads out
                particle['vy'] += 60 * dt   # Light gravity
                particle['vx'] *= 0.94      # Heavy air resistance
                particle['vy'] -= 50 * dt   # Strong upward buoyancy
                
            # Update life
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw explosion particles with dramatic layered effect"""
        for particle in self.particles:
            life_ratio = particle['life'] / particle['max_life']
            
            # Calculate alpha and size based on life
            alpha = int(255 * life_ratio)
            size = max(2, int(particle['size'] * life_ratio))
            
            if size > 0 and alpha > 30:
                x, y = int(particle['x']), int(particle['y'])
                
                # Draw different particle types with appropriate effects
                if particle['type'] == 'core':
                    # Draw large bright core pieces with glow
                    self._draw_large_square(screen, x, y, size, particle['color'], alpha)
                    
                elif particle['type'] in ['explosion', 'outer']:
                    # Draw main explosion pieces
                    self._draw_pixel_square(screen, x, y, size, particle['color'], alpha)
                    
                elif particle['type'] == 'spark':
                    # Draw bright sparks with cross pattern
                    self._draw_pixel_cross(screen, x, y, size, particle['color'], alpha)
                    
                elif particle['type'] == 'debris':
                    # Draw irregular debris chunks
                    self._draw_debris_rect(screen, x, y, size, particle['color'], alpha)
                    
                else:  # smoke
                    # Draw large billowing smoke
                    self._draw_large_smoke(screen, x, y, size, particle['color'], alpha)
    
    def _draw_pixel_square(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw a pixelated square with clean edges"""
        # Snap to pixel grid for crisp pixel art
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)  # Ensure even sizes
        
        # Create surface with alpha
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
    
    def _draw_pixel_cross(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw a pixelated cross/plus shape"""
        # Snap to pixel grid
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)
        
        # Draw horizontal bar
        h_surf = pygame.Surface((pixel_size * 2, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - pixel_size, pixel_y - pixel_size // 2))
        
        # Draw vertical bar
        v_surf = pygame.Surface((pixel_size, pixel_size * 2))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size))
    
    def _draw_pixel_rect(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw a small pixelated rectangle"""
        # Snap to pixel grid
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)
        
        # Make rectangles slightly irregular
        w = pixel_size
        h = max(2, pixel_size // 2)
        
        surf = pygame.Surface((w, h))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - w // 2, pixel_y - h // 2))
    
    def _draw_large_square(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw a large explosion core piece with dramatic glow"""
        # Snap to pixel grid but allow larger sizes
        pixel_x = (x // 4) * 4
        pixel_y = (y // 4) * 4
        pixel_size = max(12, (size // 4) * 4)
        
        # Draw outer glow first (larger, dimmer)
        if alpha > 80:
            outer_glow_size = pixel_size + 8
            outer_glow_surf = pygame.Surface((outer_glow_size, outer_glow_size))
            outer_glow_color = (min(255, color[0] + 20), min(255, color[1] + 20), color[2] // 2)
            outer_glow_surf.fill(outer_glow_color)
            outer_glow_surf.set_alpha(alpha // 4)
            screen.blit(outer_glow_surf, (pixel_x - outer_glow_size // 2, pixel_y - outer_glow_size // 2))
        
        # Draw inner glow (medium brightness)
        if alpha > 100:
            inner_glow_size = pixel_size + 4
            inner_glow_surf = pygame.Surface((inner_glow_size, inner_glow_size))
            inner_glow_color = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 20))
            inner_glow_surf.fill(inner_glow_color)
            inner_glow_surf.set_alpha(alpha // 2)
            screen.blit(inner_glow_surf, (pixel_x - inner_glow_size // 2, pixel_y - inner_glow_size // 2))
        
        # Draw main bright core
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
    
    def _draw_debris_rect(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw irregular debris chunks with rotation effect"""
        # Snap to pixel grid
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(3, (size // 2) * 2)
        
        # Draw main chunk
        w = pixel_size
        h = max(2, pixel_size * 2 // 3)  # Rectangular chunks
        
        surf = pygame.Surface((w, h))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - w // 2, pixel_y - h // 2))
        
        # Add some smaller fragments nearby
        if alpha > 80 and random.random() > 0.7:  # 30% chance for fragments
            frag_size = max(1, pixel_size // 3)
            frag_surf = pygame.Surface((frag_size, frag_size))
            frag_surf.fill(color)
            frag_surf.set_alpha(alpha // 2)
            offset_x = random.randint(-pixel_size, pixel_size)
            offset_y = random.randint(-pixel_size, pixel_size)
            screen.blit(frag_surf, (pixel_x + offset_x, pixel_y + offset_y))
    
    def _draw_large_smoke(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw large billowing smoke clouds"""
        # Snap to larger pixel grid for chunky smoke
        pixel_x = (x // 4) * 4
        pixel_y = (y // 4) * 4  
        pixel_size = max(6, (size // 3) * 3)
        
        # Draw main smoke cloud
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha // 3)  # Very transparent smoke
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
        
        # Add some wispy edges
        if alpha > 60:
            for i in range(3):  # 3 wispy bits
                wisp_x = pixel_x + random.randint(-pixel_size//2, pixel_size//2)
                wisp_y = pixel_y + random.randint(-pixel_size//2, pixel_size//2)
                wisp_size = max(2, pixel_size // 3)
                wisp_surf = pygame.Surface((wisp_size, wisp_size))
                wisp_surf.fill(color)
                wisp_surf.set_alpha(alpha // 5)  # Even more transparent
                screen.blit(wisp_surf, (wisp_x - wisp_size // 2, wisp_y - wisp_size // 2))
    
    def _draw_fuzzy_square(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw a fuzzy square for smoke with some transparency variation"""
        # Snap to pixel grid
        pixel_x = (x // 2) * 2  
        pixel_y = (y // 2) * 2
        pixel_size = max(4, (size // 2) * 2)
        
        # Draw main square with reduced alpha for smoke effect
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha // 2)  # Smoke is more transparent
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
    
    def is_finished(self) -> bool:
        """Check if explosion is finished"""
        return len(self.particles) == 0 and self.elapsed > self.duration


class RocketTrailEffect:
    """Pixel art rocket trail that zips across the screen"""
    
    def __init__(self, start_x: float, start_y: float, direction: str, board_bounds: Tuple[int, int, int, int]):
        self.start_x = start_x
        self.start_y = start_y
        self.direction = direction  # 'horizontal' or 'vertical'
        self.board_bounds = board_bounds  # (left, top, right, bottom)
        self.particles = []
        self.duration = 0.8
        self.elapsed = 0.0
        
        # Create the main rocket projectile
        if direction == 'horizontal':
            # Create two rockets going left and right
            self._create_horizontal_rockets()
        else:  # vertical
            # Create two rockets going up and down
            self._create_vertical_rockets()
    
    def _create_horizontal_rockets(self):
        """Create rockets that zip horizontally across the row"""
        left, top, right, bottom = self.board_bounds
        
        # Rocket going left
        rocket_left = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': -1200,  # SUPER FAST leftward
            'vy': 0,
            'life': 1.0,
            'max_life': 1.0,
            'color': (50, 150, 255),  # Electric blue rocket
            'size': 16,
            'type': 'rocket',
            'trail_timer': 0.0,
            'bounds_left': left,
            'bounds_right': right
        }
        
        # Rocket going right
        rocket_right = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': 1200,  # SUPER FAST rightward
            'vy': 0,
            'life': 1.0,
            'max_life': 1.0,
            'color': (50, 150, 255),  # Electric blue rocket
            'size': 16,
            'type': 'rocket',
            'trail_timer': 0.0,
            'bounds_left': left,
            'bounds_right': right
        }
        
        self.particles.append(rocket_left)
        self.particles.append(rocket_right)
    
    def _create_vertical_rockets(self):
        """Create rockets that zip vertically across the column"""
        left, top, right, bottom = self.board_bounds
        
        # Rocket going up
        rocket_up = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': 0,
            'vy': -1200,  # SUPER FAST upward
            'life': 1.0,
            'max_life': 1.0,
            'color': (50, 150, 255),  # Electric blue rocket
            'size': 16,
            'type': 'rocket',
            'trail_timer': 0.0,
            'bounds_top': top,
            'bounds_bottom': bottom
        }
        
        # Rocket going down
        rocket_down = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': 0,
            'vy': 1200,  # SUPER FAST downward
            'life': 1.0,
            'max_life': 1.0,
            'color': (50, 150, 255),  # Electric blue rocket
            'size': 16,
            'type': 'rocket',
            'trail_timer': 0.0,
            'bounds_top': top,
            'bounds_bottom': bottom
        }
        
        self.particles.append(rocket_up)
        self.particles.append(rocket_down)
    
    def update(self, dt: float):
        """Update rocket trail effect"""
        self.elapsed += dt
        
        for particle in self.particles[:]:
            # Update rocket position
            old_x, old_y = particle['x'], particle['y']
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            # Check if rocket has moved out of bounds
            if particle['type'] == 'rocket':  # Only check bounds for main rockets
                if self.direction == 'horizontal':
                    if (particle['vx'] < 0 and particle['x'] < particle['bounds_left']) or \
                       (particle['vx'] > 0 and particle['x'] > particle['bounds_right']):
                        # Rocket is out of bounds, mark for removal
                        particle['life'] = 0
                else:  # vertical
                    if (particle['vy'] < 0 and particle['y'] < particle['bounds_top']) or \
                       (particle['vy'] > 0 and particle['y'] > particle['bounds_bottom']):
                        # Rocket is out of bounds, mark for removal
                        particle['life'] = 0
            
            # Create sparkly trail particles as rocket moves (only for main rockets)
            if particle['type'] == 'rocket' and particle['life'] > 0:
                particle['trail_timer'] += dt
                if particle['trail_timer'] >= 0.008:  # Every 8ms create MORE trail
                    particle['trail_timer'] = 0.0
                    
                    # Create MASSIVE trail sparks behind the rocket
                    for i in range(8):
                        trail_particle = {
                            'x': old_x + random.uniform(-12, 12),
                            'y': old_y + random.uniform(-12, 12),
                            'vx': random.uniform(-80, 80),
                            'vy': random.uniform(-80, 80),
                            'life': random.uniform(0.4, 0.8),
                            'max_life': random.uniform(0.4, 0.8),
                            'color': random.choice([
                                (255, 255, 255),   # White spark
                                (220, 240, 255),   # Light blue
                                (180, 220, 255),   # Blue
                                (140, 200, 255),   # Deeper blue
                                (100, 180, 255),   # Electric blue
                                (255, 255, 200),   # Golden spark
                            ]),
                            'size': random.randint(4, 8),
                            'type': 'trail'
                        }
                        self.particles.append(trail_particle)
            
            # Update particle life
            if particle['type'] == 'trail':
                particle['life'] -= dt
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw rocket trail particles"""
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            x, y = int(particle['x']), int(particle['y'])
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio)
            size = max(1, int(particle['size'] * life_ratio))
            
            if particle['type'] == 'rocket':
                # Draw main rocket as bright elongated shape
                self._draw_rocket(screen, x, y, size, particle['color'], alpha, particle['vx'], particle['vy'])
            else:  # trail
                # Draw sparkly trail
                self._draw_trail_spark(screen, x, y, size, particle['color'], alpha)
    
    def _draw_rocket(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int, vx: float, vy: float):
        """Draw the main rocket projectile with MASSIVE glow"""
        # Snap to pixel grid
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(6, (size // 2) * 2)
        
        # Make rocket MUCH more elongated in direction of movement
        if abs(vx) > abs(vy):  # Moving horizontally
            w = pixel_size * 4  # Much longer
            h = pixel_size
        else:  # Moving vertically
            w = pixel_size
            h = pixel_size * 4  # Much longer
        
        # Draw MASSIVE bright glow first (outermost)
        if alpha > 100:
            mega_glow_w = w + 16
            mega_glow_h = h + 16
            mega_glow_surf = pygame.Surface((mega_glow_w, mega_glow_h))
            mega_glow_color = (100, 180, 255)
            mega_glow_surf.fill(mega_glow_color)
            mega_glow_surf.set_alpha(alpha // 8)
            screen.blit(mega_glow_surf, (pixel_x - mega_glow_w // 2, pixel_y - mega_glow_h // 2))
        
        # Draw medium glow
        if alpha > 120:
            glow_w = w + 8
            glow_h = h + 8
            glow_surf = pygame.Surface((glow_w, glow_h))
            glow_color = (150, 200, 255)
            glow_surf.fill(glow_color)
            glow_surf.set_alpha(alpha // 4)
            screen.blit(glow_surf, (pixel_x - glow_w // 2, pixel_y - glow_h // 2))
        
        # Draw bright rocket core
        surf = pygame.Surface((w, h))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - w // 2, pixel_y - h // 2))
        
        # Draw ultra-bright inner core
        inner_w = max(2, w // 2)
        inner_h = max(2, h // 2)
        inner_surf = pygame.Surface((inner_w, inner_h))
        inner_surf.fill((255, 255, 255))  # Pure white core
        inner_surf.set_alpha(alpha)
        screen.blit(inner_surf, (pixel_x - inner_w // 2, pixel_y - inner_h // 2))
    
    def _draw_trail_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw MASSIVE sparkly trail particles"""
        # Snap to pixel grid
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(3, (size // 2) * 2)
        
        # Draw LARGE cross pattern for massive sparkly effect
        # Horizontal bar - much bigger
        h_surf = pygame.Surface((pixel_size * 3, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - pixel_size // 2))
        
        # Vertical bar - much bigger
        v_surf = pygame.Surface((pixel_size, pixel_size * 3))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 3) // 2))
        
        # Add glow around spark if bright enough
        if alpha > 150:
            # Glow horizontal bar
            glow_h_surf = pygame.Surface((pixel_size * 4, pixel_size + 2))
            glow_color = (min(255, color[0] + 40), min(255, color[1] + 40), 255)
            glow_h_surf.fill(glow_color)
            glow_h_surf.set_alpha(alpha // 3)
            screen.blit(glow_h_surf, (pixel_x - (pixel_size * 4) // 2, pixel_y - (pixel_size + 2) // 2))
            
            # Glow vertical bar
            glow_v_surf = pygame.Surface((pixel_size + 2, pixel_size * 4))
            glow_v_surf.fill(glow_color)
            glow_v_surf.set_alpha(alpha // 3)
            screen.blit(glow_v_surf, (pixel_x - (pixel_size + 2) // 2, pixel_y - (pixel_size * 4) // 2))
    
    def is_finished(self) -> bool:
        """Check if rocket trail is finished"""
        return len(self.particles) == 0 or self.elapsed > self.duration


class BombRocketTrailEffect:
    """Large bomb-colored rocket trail for bomb+rocket combo (3-wide cross pattern)"""
    
    def __init__(self, start_x: float, start_y: float, direction: str, board_bounds: Tuple[int, int, int, int]):
        self.start_x = start_x
        self.start_y = start_y
        self.direction = direction  # 'horizontal' or 'vertical'
        self.board_bounds = board_bounds  # (left, top, right, bottom)
        self.particles = []
        self.duration = 0.8
        self.elapsed = 0.0
        
        # Create the main rocket projectile
        if direction == 'horizontal':
            # Create two rockets going left and right
            self._create_horizontal_bomb_rockets()
        else:  # vertical
            # Create two rockets going up and down
            self._create_vertical_bomb_rockets()
    
    def _create_horizontal_bomb_rockets(self):
        """Create large bomb-colored rockets that zip horizontally"""
        left, top, right, bottom = self.board_bounds
        
        # Rocket going left - BOMB COLORS
        rocket_left = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': -1200,  # SUPER FAST leftward
            'vy': 0,
            'life': 1.0,
            'max_life': 1.0,
            'color': (255, 100, 50),  # Bomb orange/red
            'size': 32,  # MUCH LARGER for 3-wide effect
            'type': 'bomb_rocket',
            'trail_timer': 0.0,
            'bounds_left': left,
            'bounds_right': right
        }
        
        # Rocket going right - BOMB COLORS
        rocket_right = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': 1200,  # SUPER FAST rightward
            'vy': 0,
            'life': 1.0,
            'max_life': 1.0,
            'color': (255, 100, 50),  # Bomb orange/red
            'size': 32,  # MUCH LARGER for 3-wide effect
            'type': 'bomb_rocket',
            'trail_timer': 0.0,
            'bounds_left': left,
            'bounds_right': right
        }
        
        self.particles.append(rocket_left)
        self.particles.append(rocket_right)
    
    def _create_vertical_bomb_rockets(self):
        """Create large bomb-colored rockets that zip vertically"""
        left, top, right, bottom = self.board_bounds
        
        # Rocket going up - BOMB COLORS
        rocket_up = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': 0,
            'vy': -1200,  # SUPER FAST upward
            'life': 1.0,
            'max_life': 1.0,
            'color': (255, 100, 50),  # Bomb orange/red
            'size': 32,  # MUCH LARGER for 3-wide effect
            'type': 'bomb_rocket',
            'trail_timer': 0.0,
            'bounds_top': top,
            'bounds_bottom': bottom
        }
        
        # Rocket going down - BOMB COLORS
        rocket_down = {
            'x': self.start_x,
            'y': self.start_y,
            'vx': 0,
            'vy': 1200,  # SUPER FAST downward
            'life': 1.0,
            'max_life': 1.0,
            'color': (255, 100, 50),  # Bomb orange/red
            'size': 32,  # MUCH LARGER for 3-wide effect
            'type': 'bomb_rocket',
            'trail_timer': 0.0,
            'bounds_top': top,
            'bounds_bottom': bottom
        }
        
        self.particles.append(rocket_up)
        self.particles.append(rocket_down)
    
    def update(self, dt: float):
        """Update bomb rocket trail effect"""
        self.elapsed += dt
        
        for particle in self.particles[:]:
            # Update rocket position
            old_x, old_y = particle['x'], particle['y']
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            # Check if rocket has moved out of bounds
            if particle['type'] == 'bomb_rocket':  # Only check bounds for main rockets
                if self.direction == 'horizontal':
                    if (particle['vx'] < 0 and particle['x'] < particle['bounds_left']) or \
                       (particle['vx'] > 0 and particle['x'] > particle['bounds_right']):
                        # Rocket is out of bounds, mark for removal
                        particle['life'] = 0
                else:  # vertical
                    if (particle['vy'] < 0 and particle['y'] < particle['bounds_top']) or \
                       (particle['vy'] > 0 and particle['y'] > particle['bounds_bottom']):
                        # Rocket is out of bounds, mark for removal
                        particle['life'] = 0
            
            # Create MASSIVE bomb-colored trail particles as rocket moves
            if particle['type'] == 'bomb_rocket' and particle['life'] > 0:
                particle['trail_timer'] += dt
                if particle['trail_timer'] >= 0.006:  # Even more frequent trail for bomb effect
                    particle['trail_timer'] = 0.0
                    
                    # Create HUGE trail sparks with bomb explosion colors
                    for i in range(12):  # More trail particles
                        trail_particle = {
                            'x': old_x + random.uniform(-20, 20),  # Wider spread
                            'y': old_y + random.uniform(-20, 20),
                            'vx': random.uniform(-120, 120),
                            'vy': random.uniform(-120, 120),
                            'life': random.uniform(0.5, 1.0),  # Longer lasting
                            'max_life': random.uniform(0.5, 1.0),
                            'color': random.choice([
                                (255, 80, 0),      # Bright orange
                                (255, 120, 30),    # Orange-red
                                (255, 160, 50),    # Yellow-orange
                                (255, 200, 80),    # Golden yellow
                                (255, 60, 60),     # Red
                                (200, 40, 40),     # Dark red
                                (100, 20, 20),     # Very dark red
                                (50, 50, 50),      # Dark smoke
                            ]),
                            'size': random.randint(6, 12),  # MUCH bigger trail particles
                            'type': 'bomb_trail'
                        }
                        self.particles.append(trail_particle)
            
            # Update particle life
            if particle['type'] == 'bomb_trail':
                particle['life'] -= dt
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw bomb rocket trail particles"""
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            x, y = int(particle['x']), int(particle['y'])
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio)
            size = max(1, int(particle['size'] * life_ratio))
            
            if particle['type'] == 'bomb_rocket':
                # Draw main bomb rocket as HUGE elongated shape
                self._draw_bomb_rocket(screen, x, y, size, particle['color'], alpha, particle['vx'], particle['vy'])
            else:  # bomb_trail
                # Draw large bomb-colored trail
                self._draw_bomb_trail_spark(screen, x, y, size, particle['color'], alpha)
    
    def _draw_bomb_rocket(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int, vx: float, vy: float):
        """Draw the main bomb rocket projectile - HUGE with bomb colors"""
        # Snap to pixel grid but use larger grid for more pixelated look
        pixel_grid = 4
        pixel_x = (x // pixel_grid) * pixel_grid
        pixel_y = (y // pixel_grid) * pixel_grid
        pixel_size = max(8, (size // 4) * 4)  # Larger base size
        
        # Make rocket MASSIVE and elongated in direction of movement
        if abs(vx) > abs(vy):  # Moving horizontally
            w = pixel_size * 6  # MUCH MUCH longer
            h = pixel_size * 2  # Wider too
        else:  # Moving vertically
            w = pixel_size * 2  # Wider
            h = pixel_size * 6  # MUCH MUCH longer
        
        # Draw ENORMOUS bright glow first (outermost)
        if alpha > 80:
            mega_glow_w = w + 32
            mega_glow_h = h + 32
            mega_glow_surf = pygame.Surface((mega_glow_w, mega_glow_h))
            mega_glow_color = (150, 50, 0)  # Dark orange glow
            mega_glow_surf.fill(mega_glow_color)
            mega_glow_surf.set_alpha(alpha // 6)
            screen.blit(mega_glow_surf, (pixel_x - mega_glow_w // 2, pixel_y - mega_glow_h // 2))
        
        # Draw medium glow
        if alpha > 100:
            glow_w = w + 16
            glow_h = h + 16
            glow_surf = pygame.Surface((glow_w, glow_h))
            glow_color = (255, 80, 20)  # Bright orange glow
            glow_surf.fill(glow_color)
            glow_surf.set_alpha(alpha // 3)
            screen.blit(glow_surf, (pixel_x - glow_w // 2, pixel_y - glow_h // 2))
        
        # Draw bright rocket core
        surf = pygame.Surface((w, h))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - w // 2, pixel_y - h // 2))
        
        # Draw ultra-bright inner core
        inner_w = max(4, w // 3)
        inner_h = max(4, h // 3)
        inner_surf = pygame.Surface((inner_w, inner_h))
        inner_surf.fill((255, 255, 180))  # Hot yellow-white core
        inner_surf.set_alpha(alpha)
        screen.blit(inner_surf, (pixel_x - inner_w // 2, pixel_y - inner_h // 2))
    
    def _draw_bomb_trail_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw HUGE bomb-colored trail particles"""
        # Snap to pixel grid
        pixel_grid = 4
        pixel_x = (x // pixel_grid) * pixel_grid
        pixel_y = (y // pixel_grid) * pixel_grid
        pixel_size = max(4, (size // 2) * 2)
        
        # Draw HUGE cross pattern for massive bomb trail effect
        # Horizontal bar - enormous
        h_surf = pygame.Surface((pixel_size * 4, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 4) // 2, pixel_y - pixel_size // 2))
        
        # Vertical bar - enormous
        v_surf = pygame.Surface((pixel_size, pixel_size * 4))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 4) // 2))
        
        # Add bomb-colored glow around spark if bright enough
        if alpha > 120:
            # Glow horizontal bar
            glow_h_surf = pygame.Surface((pixel_size * 6, pixel_size + 4))
            glow_color = (min(255, color[0] + 60), min(255, color[1] + 40), 0)  # Bomb glow
            glow_h_surf.fill(glow_color)
            glow_h_surf.set_alpha(alpha // 4)
            screen.blit(glow_h_surf, (pixel_x - (pixel_size * 6) // 2, pixel_y - (pixel_size + 4) // 2))
            
            # Glow vertical bar
            glow_v_surf = pygame.Surface((pixel_size + 4, pixel_size * 6))
            glow_v_surf.fill(glow_color)
            glow_v_surf.set_alpha(alpha // 4)
            screen.blit(glow_v_surf, (pixel_x - (pixel_size + 4) // 2, pixel_y - (pixel_size * 6) // 2))
    
    def is_finished(self) -> bool:
        """Check if bomb rocket trail is finished"""
        return len(self.particles) == 0 or self.elapsed > self.duration


class LightningArcEffect:
    """Dramatic pixel art lightning arc effect with three sequential arcs"""
    
    def __init__(self, x: float, y: float):
        self.center_x = x
        self.center_y = y
        self.particles = []
        self.duration = 0.8
        self.elapsed = 0.0
        
        # Lightning will create three sequential arcs - faster timing
        self.arc_stages = [
            {'delay': 0.0, 'created': False},    # First small arc
            {'delay': 0.08, 'created': False},   # Second medium arc  
            {'delay': 0.16, 'created': False},   # Third large arc
        ]
        
    def _create_lightning_arc(self, arc_size: int):
        """Create a single lightning arc with the specified size multiplier"""
        base_radius = 60
        radius = base_radius * arc_size
        
        # Create the main lightning bolt branches - reduced count
        num_branches = 4 + (arc_size * 2)  # Fewer branches for cleaner look
        
        for branch in range(num_branches):
            # Each branch extends outward from center
            base_angle = (branch / num_branches) * math.pi * 2
            
            # Create zigzag lightning pattern along this branch
            branch_length = radius + random.uniform(-15, 15)
            segments = 8 + (arc_size * 2)  # Fewer segments for cleaner arcs
            
            prev_x, prev_y = self.center_x, self.center_y
            
            for segment in range(segments):
                # Calculate progress along the branch (0 to 1)
                progress = segment / segments
                
                # Base position along the branch
                base_x = self.center_x + math.cos(base_angle) * (progress * branch_length)
                base_y = self.center_y + math.sin(base_angle) * (progress * branch_length)
                
                # Add zigzag variation
                zigzag_amount = 25 * arc_size * (1 - progress)  # Less zigzag towards the end
                zigzag_x = base_x + random.uniform(-zigzag_amount, zigzag_amount)
                zigzag_y = base_y + random.uniform(-zigzag_amount, zigzag_amount)
                
                # Create lightning segment particle
                particle = {
                    'x': zigzag_x,
                    'y': zigzag_y,
                    'prev_x': prev_x,
                    'prev_y': prev_y,
                    'life': random.uniform(0.25, 0.5),
                    'max_life': random.uniform(0.25, 0.5),
                    'color': random.choice([
                        (255, 255, 255),   # Pure white
                        (200, 200, 255),   # Light blue-white
                        (150, 150, 255),   # Blue-white
                        (255, 255, 200),   # Warm white
                    ]),
                    'size': random.randint(3, 6) + arc_size,
                    'type': 'lightning_bolt',
                    'intensity': random.uniform(0.7, 1.0)
                }
                self.particles.append(particle)
                
                prev_x, prev_y = zigzag_x, zigzag_y
        
        # Create electrical sparks around the lightning - reduced count
        spark_count = 12 + (arc_size * 8)
        for i in range(spark_count):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(20, radius * 1.2)
            
            spark_x = self.center_x + math.cos(angle) * distance
            spark_y = self.center_y + math.sin(angle) * distance
            
            particle = {
                'x': spark_x,
                'y': spark_y,
                'vx': random.uniform(-150, 150),
                'vy': random.uniform(-150, 150),
                'life': random.uniform(0.15, 0.4),
                'max_life': random.uniform(0.15, 0.4),
                'color': random.choice([
                    (255, 255, 255),   # White spark
                    (180, 180, 255),   # Light blue
                    (150, 200, 255),   # Electric blue
                    (255, 255, 180),   # Warm spark
                ]),
                'size': random.randint(2, 4) + arc_size,
                'type': 'electric_spark',
                'intensity': random.uniform(0.5, 1.0)
            }
            self.particles.append(particle)
        
        # Create central flash explosion - reduced count
        flash_count = 8 + (arc_size * 4)
        for i in range(flash_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            
            particle = {
                'x': self.center_x,
                'y': self.center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.2, 0.4),
                'max_life': random.uniform(0.2, 0.4),
                'color': (255, 255, 255),  # Pure white flash
                'size': random.randint(4, 8) + (arc_size * 2),
                'type': 'flash',
                'intensity': 1.0
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update lightning arc effect with sequential arc creation"""
        self.elapsed += dt
        
        # Check if we need to create any new arcs
        for i, stage in enumerate(self.arc_stages):
            if not stage['created'] and self.elapsed >= stage['delay']:
                stage['created'] = True
                self._create_lightning_arc(i + 1)  # Arc sizes 1, 2, 3
        
        # Update all particles
        for particle in self.particles[:]:
            if particle['type'] == 'lightning_bolt':
                # Lightning bolts just fade, don't move
                particle['life'] -= dt
            
            elif particle['type'] == 'electric_spark':
                # Electric sparks move and fade
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.95  # Air resistance
                particle['vy'] *= 0.95
                particle['life'] -= dt
            
            elif particle['type'] == 'flash':
                # Flash particles expand outward
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.90  # Slow down as they expand
                particle['vy'] *= 0.90
                particle['life'] -= dt
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw lightning arc with dramatic electrical effects"""
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            x, y = int(particle['x']), int(particle['y'])
            life_ratio = particle['life'] / particle['max_life']
            intensity = particle['intensity']
            base_alpha = int(255 * life_ratio * intensity)
            size = max(1, int(particle['size'] * life_ratio))
            
            if particle['type'] == 'lightning_bolt':
                # Draw lightning bolt segments with connection lines
                self._draw_lightning_segment(screen, x, y, size, particle['color'], base_alpha, particle)
                
            elif particle['type'] == 'electric_spark':
                # Draw electric sparks as bright crosses
                self._draw_electric_spark(screen, x, y, size, particle['color'], base_alpha)
                
            elif particle['type'] == 'flash':
                # Draw flash as bright square with glow
                self._draw_flash(screen, x, y, size, particle['color'], base_alpha)
    
    def _draw_lightning_segment(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int, particle):
        """Draw a lightning bolt segment with connection to previous segment"""
        # Draw connection line to previous segment
        if 'prev_x' in particle and 'prev_y' in particle:
            prev_x, prev_y = int(particle['prev_x']), int(particle['prev_y'])
            
            # Draw thick lightning line
            self._draw_lightning_line(screen, prev_x, prev_y, x, y, size, color, alpha)
        
        # Draw the main lightning node
        self._draw_pixel_square(screen, x, y, size + 2, color, alpha)
        
        # Draw bright core
        self._draw_pixel_square(screen, x, y, max(1, size // 2), (255, 255, 255), alpha)
    
    def _draw_lightning_line(self, screen: pygame.Surface, x1: int, y1: int, x2: int, y2: int, thickness: int, color: Tuple[int, int, int], alpha: int):
        """Draw a thick pixelated lightning line between two points"""
        # Calculate direction and distance
        dx = x2 - x1
        dy = y2 - y1
        distance = max(1, int(math.sqrt(dx * dx + dy * dy)))
        
        if distance == 0:
            return
        
        # Draw line as series of squares
        for i in range(distance):
            progress = i / distance
            line_x = int(x1 + dx * progress)
            line_y = int(y1 + dy * progress)
            
            self._draw_pixel_square(screen, line_x, line_y, thickness, color, alpha)
    
    def _draw_electric_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw electric sparks as bright crosses with glow"""
        # Draw large cross pattern
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)
        
        # Horizontal bar
        h_surf = pygame.Surface((pixel_size * 3, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - pixel_size // 2))
        
        # Vertical bar
        v_surf = pygame.Surface((pixel_size, pixel_size * 3))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 3) // 2))
        
        # Add glow if bright enough
        if alpha > 150:
            glow_size = pixel_size + 2
            # Glow horizontal
            glow_h_surf = pygame.Surface((pixel_size * 4, glow_size))
            glow_h_surf.fill((200, 200, 255))
            glow_h_surf.set_alpha(alpha // 4)
            screen.blit(glow_h_surf, (pixel_x - (pixel_size * 4) // 2, pixel_y - glow_size // 2))
            
            # Glow vertical
            glow_v_surf = pygame.Surface((glow_size, pixel_size * 4))
            glow_v_surf.fill((200, 200, 255))
            glow_v_surf.set_alpha(alpha // 4)
            screen.blit(glow_v_surf, (pixel_x - glow_size // 2, pixel_y - (pixel_size * 4) // 2))
    
    def _draw_flash(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw bright flash particles"""
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)
        
        # Draw main flash square
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
        
        # Add bright glow around flash
        if alpha > 100:
            glow_size = pixel_size + 4
            glow_surf = pygame.Surface((glow_size, glow_size))
            glow_surf.fill((220, 220, 255))
            glow_surf.set_alpha(alpha // 3)
            screen.blit(glow_surf, (pixel_x - glow_size // 2, pixel_y - glow_size // 2))
    
    def _draw_pixel_square(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw a pixelated square"""
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)
        
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
    
    def is_finished(self) -> bool:
        """Check if lightning arc is finished"""
        return len(self.particles) == 0 and self.elapsed > self.duration


class RowLightningArcEffect:
    """Lightning arc that blasts across an entire row for rocket+lightning combo"""
    
    def __init__(self, row: int, direction: str, board_bounds: Tuple[int, int, int, int]):
        self.row = row
        self.direction = direction  # 'left_to_right' or 'right_to_left'
        self.board_bounds = board_bounds  # (left, top, right, bottom)
        self.particles = []
        self.duration = 0.25  # Slightly longer for more dramatic effect
        self.elapsed = 0.0
        
        # Calculate row position
        left, top, right, bottom = board_bounds
        tile_height = (bottom - top) // 10  # Assuming 10 rows
        self.row_y = top + (row * tile_height) + (tile_height // 2)
        
        # Create the lightning arc
        self._create_row_lightning()
    
    def _create_row_lightning(self):
        """Create lightning arc that blasts across the entire row"""
        left, top, right, bottom = self.board_bounds
        
        if self.direction == 'left_to_right':
            start_x, end_x = left - 20, right + 20
        else:  # right_to_left
            start_x, end_x = right + 20, left - 20
        
        # Create multiple lightning bolts for more intensity
        for bolt_num in range(3):  # 3 parallel lightning bolts
            segments = 20  # More segments for smoother lightning
            bolt_offset_y = (bolt_num - 1) * 4  # Spread bolts vertically
            
            for i in range(segments + 1):
                progress = i / segments
                
                # Base position along the row
                base_x = start_x + (end_x - start_x) * progress
                base_y = self.row_y + bolt_offset_y
                
                # Add dramatic lightning zigzag
                zigzag_intensity = 20 if bolt_num == 0 else 15  # Main bolt has bigger zigzag
                zigzag_offset_x = random.uniform(-zigzag_intensity, zigzag_intensity) if i > 0 and i < segments else 0
                zigzag_offset_y = random.uniform(-12, 12)
                
                lightning_x = base_x + zigzag_offset_x
                lightning_y = base_y + zigzag_offset_y
                
                # Create lightning segment
                if i > 0:
                    # Main bolt is thicker and brighter
                    thickness = random.randint(3, 6) if bolt_num == 0 else random.randint(2, 4)
                    intensity = random.uniform(0.9, 1.0) if bolt_num == 0 else random.uniform(0.6, 0.8)
                    
                    lightning_particle = {
                        'x': prev_x,
                        'y': prev_y,
                        'next_x': lightning_x,
                        'next_y': lightning_y,
                        'life': random.uniform(0.15, 0.25),  # Slightly longer life
                        'max_life': random.uniform(0.15, 0.25),
                        'color': random.choice([
                            (255, 255, 255),  # Pure white (more common)
                            (220, 240, 255),  # Bright electric blue
                            (180, 220, 255),  # Electric blue
                            (255, 240, 200),  # Electric yellow-white
                        ]),
                        'thickness': thickness,
                        'type': 'row_lightning',
                        'intensity': intensity,
                        'bolt_id': bolt_num
                    }
                    self.particles.append(lightning_particle)
                
                prev_x, prev_y = lightning_x, lightning_y
        
        # Create more dramatic electrical sparks along the row
        spark_count = 35  # More sparks for intensity
        for i in range(spark_count):
            spark_x = random.uniform(left - 10, right + 10)  # Extend beyond row
            spark_y = self.row_y + random.uniform(-18, 18)  # Wider spread
            
            # Bigger sparks with more varied movement
            velocity_scale = random.uniform(1.2, 2.0)
            electric_spark = {
                'x': spark_x,
                'y': spark_y,
                'vx': random.uniform(-120, 120) * velocity_scale,
                'vy': random.uniform(-60, 60) * velocity_scale,
                'life': random.uniform(0.08, 0.20),  # Longer lasting sparks
                'max_life': random.uniform(0.08, 0.20),
                'color': random.choice([
                    (255, 255, 255),  # Pure white
                    (220, 240, 255),  # Bright electric blue
                    (255, 255, 180),  # Electric yellow
                    (200, 255, 200),  # Electric green
                    (255, 200, 255),  # Electric magenta
                ]),
                'size': random.randint(4, 8),  # Bigger sparks
                'type': 'row_spark',
                'intensity': random.uniform(0.8, 1.0)  # Higher intensity
            }
            self.particles.append(electric_spark)
        
        # Create dramatic flash effects across the entire row
        flash_count = 12  # More flash points
        for i in range(flash_count):
            flash_x = left + (right - left) * (i / (flash_count - 1))
            flash_y = self.row_y + random.uniform(-8, 8)
            
            # Main bright flash
            flash_particle = {
                'x': flash_x,
                'y': flash_y,
                'vx': 0,
                'vy': 0,
                'life': 0.12,  # Longer flash duration
                'max_life': 0.12,
                'color': (255, 255, 255),  # Pure white flash
                'size': random.randint(12, 18),  # Bigger flash
                'type': 'row_flash',
                'intensity': 1.0
            }
            self.particles.append(flash_particle)
            
            # Add ring of smaller flashes around main flash for dramatic effect
            for ring_angle in range(0, 360, 60):  # 6 points around each flash
                import math
                ring_radius = random.uniform(8, 15)
                ring_x = flash_x + math.cos(math.radians(ring_angle)) * ring_radius
                ring_y = flash_y + math.sin(math.radians(ring_angle)) * ring_radius
                
                ring_flash = {
                    'x': ring_x,
                    'y': ring_y,
                    'vx': math.cos(math.radians(ring_angle)) * 20,  # Slight outward movement
                    'vy': math.sin(math.radians(ring_angle)) * 20,
                    'life': 0.10,
                    'max_life': 0.10,
                    'color': random.choice([
                        (255, 255, 200),  # Yellow-white
                        (200, 255, 255),  # Cyan-white
                        (255, 200, 255),  # Magenta-white
                    ]),
                    'size': random.randint(6, 10),
                    'type': 'row_flash',
                    'intensity': 0.8
                }
                self.particles.append(ring_flash)
    
    def update(self, dt: float):
        """Update row lightning arc effect"""
        self.elapsed += dt
        
        for particle in self.particles[:]:
            if particle['type'] == 'row_lightning':
                # Lightning segments just fade
                particle['life'] -= dt
            
            elif particle['type'] == 'row_spark':
                # Sparks move and fade
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.92  # Air resistance
                particle['vy'] *= 0.92
                particle['life'] -= dt
            
            elif particle['type'] == 'row_flash':
                # Flash particles just fade quickly
                particle['life'] -= dt
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw row lightning arc particles"""
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio * particle['intensity'])
            
            if particle['type'] == 'row_lightning':
                # Draw lightning bolt segment
                self._draw_row_lightning_segment(screen, particle, alpha)
            
            elif particle['type'] == 'row_spark':
                # Draw electric spark
                x, y = int(particle['x']), int(particle['y'])
                size = max(1, int(particle['size'] * life_ratio))
                self._draw_row_spark(screen, x, y, size, particle['color'], alpha)
            
            elif particle['type'] == 'row_flash':
                # Draw bright flash
                x, y = int(particle['x']), int(particle['y'])
                size = max(2, int(particle['size'] * life_ratio))
                self._draw_row_flash(screen, x, y, size, particle['color'], alpha)
    
    def _draw_row_lightning_segment(self, screen: pygame.Surface, particle, alpha: int):
        """Draw a row lightning segment"""
        x1, y1 = int(particle['x']), int(particle['y'])
        x2, y2 = int(particle['next_x']), int(particle['next_y'])
        color = particle['color']
        thickness = particle['thickness']
        
        # Draw thick lightning line
        self._draw_thick_lightning_line(screen, x1, y1, x2, y2, thickness, color, alpha)
    
    def _draw_thick_lightning_line(self, screen: pygame.Surface, x1: int, y1: int, x2: int, y2: int, thickness: int, color: Tuple[int, int, int], alpha: int):
        """Draw a thick pixelated lightning line"""
        dx = x2 - x1
        dy = y2 - y1
        length = max(1, int(math.sqrt(dx * dx + dy * dy)))
        
        if length == 0:
            return
        
        # Draw line as series of thick pixels
        steps = max(1, length // 2)
        for i in range(steps + 1):
            progress = i / steps if steps > 0 else 0
            line_x = int(x1 + dx * progress)
            line_y = int(y1 + dy * progress)
            
            # Snap to pixel grid
            pixel_x = (line_x // 2) * 2
            pixel_y = (line_y // 2) * 2
            pixel_size = thickness * 2
            
            surf = pygame.Surface((pixel_size, pixel_size))
            surf.fill(color)
            surf.set_alpha(alpha)
            screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
    
    def _draw_row_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw row spark as bright cross"""
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(2, (size // 2) * 2)
        
        # Horizontal bar
        h_surf = pygame.Surface((pixel_size * 3, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - pixel_size // 2))
        
        # Vertical bar
        v_surf = pygame.Surface((pixel_size, pixel_size * 3))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 3) // 2))
    
    def _draw_row_flash(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw bright row flash"""
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(4, (size // 2) * 2)
        
        # Main flash
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
        
        # Glow around flash
        if alpha > 100:
            glow_size = pixel_size + 6
            glow_surf = pygame.Surface((glow_size, glow_size))
            glow_surf.fill((220, 220, 255))  # Light blue glow
            glow_surf.set_alpha(alpha // 3)
            screen.blit(glow_surf, (pixel_x - glow_size // 2, pixel_y - glow_size // 2))
    
    def is_finished(self) -> bool:
        """Check if row lightning arc is finished"""
        return len(self.particles) == 0 and self.elapsed > self.duration


class BoardWipeArcEffect:
    """Arcing lines effect for board wipe that connect center to all target tiles"""
    
    def __init__(self, start_x: float, start_y: float, target_positions: List[Tuple[float, float]], target_color):
        self.start_x = start_x
        self.start_y = start_y
        self.target_positions = target_positions
        self.target_color = target_color
        self.particles = []
        self.duration = 0.5  # Quick sequential effect
        self.elapsed = 0.0
        
        # Convert color to RGB values
        if hasattr(target_color, 'value'):
            self.arc_color = target_color.value  # Get RGB tuple from TileColor
        else:
            self.arc_color = (255, 100, 100)  # Fallback red
        
        # Sequential arc stages like lightning
        self.arc_stages = [
            {'delay': 0.0, 'created': False, 'reach': 0.3},    # First short arc (30% to targets)
            {'delay': 0.08, 'created': False, 'reach': 0.7},   # Second medium arc (70% to targets)
            {'delay': 0.16, 'created': False, 'reach': 1.0},   # Third full arc (100% to targets)
        ]
    
    def _create_sequential_arcs(self, stage_reach: float):
        """Create arcs for a specific stage that reach a percentage of the way to targets"""
        for target_x, target_y in self.target_positions:
            # Calculate arc path
            dx = target_x - self.start_x
            dy = target_y - self.start_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < 10:  # Skip very close targets
                continue
            
            # Calculate the actual end point for this stage
            stage_end_x = self.start_x + dx * stage_reach
            stage_end_y = self.start_y + dy * stage_reach
            
            # Arc height based on distance and stage (shorter arcs for earlier stages)
            base_arc_height = min(60, distance * 0.2)
            arc_height = base_arc_height * stage_reach
            
            # Calculate arc peak (perpendicular to the line)
            mid_x = (self.start_x + stage_end_x) / 2
            mid_y = (self.start_y + stage_end_y) / 2
            
            # Perpendicular direction for arc
            perp_x = -dy / distance
            perp_y = dx / distance
            
            # Arc peak position
            arc_peak_x = mid_x + perp_x * arc_height
            arc_peak_y = mid_y + perp_y * arc_height
            
            # Create arc segments (like lightning bolts) - MORE CHAOTIC
            segments = max(12, int(distance * stage_reach / 18))  # More segments for chaos
            for i in range(segments + 1):
                t = i / segments if segments > 0 else 0
                t_inv = 1 - t
                
                # Quadratic bezier curve
                arc_x = (t_inv * t_inv * self.start_x + 
                        2 * t_inv * t * arc_peak_x + 
                        t * t * stage_end_x)
                arc_y = (t_inv * t_inv * self.start_y + 
                        2 * t_inv * t * arc_peak_y + 
                        t * t * stage_end_y)
                
                # Add MUCH MORE chaotic zigzag variation
                zigzag_amount = 18 * stage_reach + random.uniform(0, 15)  # More chaos
                zigzag_x = arc_x + random.uniform(-zigzag_amount, zigzag_amount)
                zigzag_y = arc_y + random.uniform(-zigzag_amount, zigzag_amount)
                
                # Add random branching for extreme chaos
                if random.random() < 0.25 and i > 2:  # 25% chance of branch after segment 2
                    branch_angle = random.uniform(0, math.pi * 2)
                    branch_length = random.uniform(20, 45)
                    branch_x = zigzag_x + math.cos(branch_angle) * branch_length
                    branch_y = zigzag_y + math.sin(branch_angle) * branch_length
                    
                    # Create branch segment (more transparent)
                    branch_particle = {
                        'x': zigzag_x,
                        'y': zigzag_y,
                        'next_x': branch_x,
                        'next_y': branch_y,
                        'life': random.uniform(0.1, 0.2),  # Shorter life
                        'max_life': random.uniform(0.1, 0.2),
                        'color': self.arc_color,
                        'type': 'arc_segment',
                        'intensity': random.uniform(0.3, 0.5),  # Much more transparent
                        'thickness': 1  # Thinner branches
                    }
                    self.particles.append(branch_particle)
                
                # Store previous position for line drawing
                if i > 0:
                    prev_particle = {
                        'x': prev_x,
                        'y': prev_y,
                        'next_x': zigzag_x,
                        'next_y': zigzag_y,
                        'life': random.uniform(0.15, 0.25),
                        'max_life': random.uniform(0.15, 0.25),
                        'color': self.arc_color,
                        'type': 'arc_segment',
                        'intensity': random.uniform(0.5, 0.7),  # More transparent
                        'thickness': 1 + int(stage_reach)  # Thinner main arcs
                    }
                    self.particles.append(prev_particle)
                
                prev_x, prev_y = zigzag_x, zigzag_y
            
            # Create MORE electrical sparks around the endpoint (flashier)
            spark_count = 8 + int(stage_reach * 10)
            for i in range(spark_count):
                angle = random.uniform(0, math.pi * 2)
                spark_distance = random.uniform(15, 50) * stage_reach
                
                spark_x = stage_end_x + math.cos(angle) * spark_distance
                spark_y = stage_end_y + math.sin(angle) * spark_distance
                
                sparkle = {
                    'x': spark_x,
                    'y': spark_y,
                    'vx': random.uniform(-60, 60),  # Faster movement
                    'vy': random.uniform(-60, 60),
                    'life': random.uniform(0.15, 0.3),  # Longer life
                    'max_life': random.uniform(0.15, 0.3),
                    'color': self.arc_color,
                    'size': random.randint(2, 6),  # Bigger sparkles
                    'type': 'arc_sparkle',
                    'intensity': random.uniform(0.4, 0.8)  # More transparent
                }
                self.particles.append(sparkle)
            
            # ADD FLASHY ENERGY BURSTS for extra flair
            burst_count = 4 + int(stage_reach * 3)
            for i in range(burst_count):
                burst_angle = random.uniform(0, math.pi * 2)
                burst_distance = random.uniform(8, 25)
                burst_x = stage_end_x + math.cos(burst_angle) * burst_distance
                burst_y = stage_end_y + math.sin(burst_angle) * burst_distance
                
                # Create energy burst with radiating particles
                for j in range(6):
                    sub_angle = burst_angle + random.uniform(-1.0, 1.0)
                    sub_speed = random.uniform(30, 60)
                    
                    energy_particle = {
                        'x': burst_x,
                        'y': burst_y,
                        'vx': math.cos(sub_angle) * sub_speed,
                        'vy': math.sin(sub_angle) * sub_speed,
                        'life': random.uniform(0.1, 0.25),
                        'max_life': random.uniform(0.1, 0.25),
                        'color': (255, 255, 150) if random.random() < 0.4 else self.arc_color,
                        'size': random.randint(1, 4),
                        'type': 'energy_burst',
                        'intensity': random.uniform(0.6, 1.0)
                    }
                    self.particles.append(energy_particle)
            
            # ADD CRACKLING EFFECT along the arc path
            crackle_segments = segments // 3  # Every third segment
            for i in range(crackle_segments):
                # Pick random point along the arc
                t = random.uniform(0.2, 0.8)  # Not at the ends
                t_inv = 1 - t
                
                crackle_x = (t_inv * t_inv * self.start_x + 
                           2 * t_inv * t * arc_peak_x + 
                           t * t * stage_end_x)
                crackle_y = (t_inv * t_inv * self.start_y + 
                           2 * t_inv * t * arc_peak_y + 
                           t * t * stage_end_y)
                
                # Create small crackling sparks around this point
                for j in range(3):
                    crackle_angle = random.uniform(0, math.pi * 2)
                    crackle_dist = random.uniform(5, 15)
                    
                    crackle_particle = {
                        'x': crackle_x + math.cos(crackle_angle) * crackle_dist,
                        'y': crackle_y + math.sin(crackle_angle) * crackle_dist,
                        'vx': math.cos(crackle_angle) * random.uniform(10, 25),
                        'vy': math.sin(crackle_angle) * random.uniform(10, 25),
                        'life': random.uniform(0.05, 0.15),
                        'max_life': random.uniform(0.05, 0.15),
                        'color': (255, 255, 255),  # White crackling
                        'size': random.randint(1, 2),
                        'type': 'crackle_spark',
                        'intensity': random.uniform(0.7, 1.0)
                    }
                    self.particles.append(crackle_particle)
    
    def update(self, dt: float):
        """Update board wipe arc effect with sequential arc creation"""
        self.elapsed += dt
        
        # Check if we need to create any new arc stages
        for i, stage in enumerate(self.arc_stages):
            if not stage['created'] and self.elapsed >= stage['delay']:
                stage['created'] = True
                self._create_sequential_arcs(stage['reach'])
        
        # Update all particles
        for particle in self.particles[:]:
            # Update based on particle type
            if particle['type'] == 'arc_segment':
                # Arc segments just fade
                particle['life'] -= dt
            
            elif particle['type'] == 'arc_sparkle':
                # Sparkles move and fade
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.95
                particle['vy'] *= 0.95
                particle['life'] -= dt
                
            elif particle['type'] == 'energy_burst':
                # Energy bursts move and fade quickly
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.92  # Faster deceleration
                particle['vy'] *= 0.92
                particle['life'] -= dt
                
            elif particle['type'] == 'crackle_spark':
                # Crackle sparks move erratically and fade fast
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.88  # Even faster deceleration
                particle['vy'] *= 0.88
                # Add some random jitter for crackling effect
                particle['vx'] += random.uniform(-5, 5)
                particle['vy'] += random.uniform(-5, 5)
                particle['life'] -= dt
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw board wipe arcing lines"""
        for particle in self.particles:
            # Skip particles that haven't appeared yet
            if 'delay' in particle and particle['delay'] > 0:
                continue
                
            if particle['life'] <= 0:
                continue
            
            life_ratio = particle['life'] / particle['max_life']
            intensity = particle['intensity']
            alpha = int(255 * life_ratio * intensity)
            
            if particle['type'] == 'arc_segment':
                # Draw arc segment as line between two points
                self._draw_arc_segment_line(screen, particle, alpha)
            
            elif particle['type'] == 'arc_sparkle':
                # Draw sparkles as small crosses
                x, y = int(particle['x']), int(particle['y'])
                size = max(1, int(particle['size'] * life_ratio))
                self._draw_arc_sparkle(screen, x, y, size, particle['color'], alpha)
                
            elif particle['type'] == 'energy_burst':
                # Draw energy bursts as bright stars
                x, y = int(particle['x']), int(particle['y'])
                size = max(1, int(particle['size'] * life_ratio))
                self._draw_energy_burst(screen, x, y, size, particle['color'], alpha)
                
            elif particle['type'] == 'crackle_spark':
                # Draw crackle sparks as tiny bright dots
                x, y = int(particle['x']), int(particle['y'])
                size = max(1, int(particle['size'] * life_ratio))
                self._draw_crackle_spark(screen, x, y, size, particle['color'], alpha)
    
    def _draw_arc_segment_line(self, screen: pygame.Surface, particle, alpha: int):
        """Draw an arc segment as a line between two points (like lightning)"""
        x1, y1 = int(particle['x']), int(particle['y'])
        x2, y2 = int(particle['next_x']), int(particle['next_y'])
        color = particle['color']
        thickness = particle['thickness']
        
        # Draw thick line segment
        self._draw_thick_line(screen, x1, y1, x2, y2, thickness, color, alpha)
    
    def _draw_thick_line(self, screen: pygame.Surface, x1: int, y1: int, x2: int, y2: int, thickness: int, color: Tuple[int, int, int], alpha: int):
        """Draw a thick pixelated line with better pixel alignment"""
        # Calculate line direction and length
        dx = x2 - x1
        dy = y2 - y1
        length = max(1, int(math.sqrt(dx * dx + dy * dy)))
        
        if length == 0:
            return
        
        # Draw line as series of thick pixels with better pixel grid alignment
        pixel_grid = 3  # Smaller pixel grid for thinner lines
        steps = max(1, length // 2)  # More steps for smoother lines
        
        for i in range(steps + 1):
            progress = i / steps if steps > 0 else 0
            line_x = int(x1 + dx * progress)
            line_y = int(y1 + dy * progress)
            
            # Snap to smaller pixel grid for thinner look
            pixel_x = (line_x // pixel_grid) * pixel_grid
            pixel_y = (line_y // pixel_grid) * pixel_grid
            pixel_size = max(pixel_grid, thickness * 2)  # Less multiplication for thinner lines
            
            surf = pygame.Surface((pixel_size, pixel_size))
            surf.fill(color)
            surf.set_alpha(alpha)
            screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
    
    def _draw_traveling_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw the traveling spark as a bright star"""
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        pixel_size = max(3, (size // 2) * 2)
        
        # Draw main cross
        # Horizontal bar
        h_surf = pygame.Surface((pixel_size * 3, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - pixel_size // 2))
        
        # Vertical bar
        v_surf = pygame.Surface((pixel_size, pixel_size * 3))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 3) // 2))
        
        # Add glow
        if alpha > 150:
            glow_size = pixel_size + 2
            # Glow horizontal
            glow_h_surf = pygame.Surface((pixel_size * 4, glow_size))
            glow_h_surf.fill((255, 255, 255))
            glow_h_surf.set_alpha(alpha // 2)
            screen.blit(glow_h_surf, (pixel_x - (pixel_size * 4) // 2, pixel_y - glow_size // 2))
            
            # Glow vertical
            glow_v_surf = pygame.Surface((glow_size, pixel_size * 4))
            glow_v_surf.fill((255, 255, 255))
            glow_v_surf.set_alpha(alpha // 2)
            screen.blit(glow_v_surf, (pixel_x - glow_size // 2, pixel_y - (pixel_size * 4) // 2))
    
    def _draw_arc_sparkle(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw arc sparkles as small crosses with better pixelation"""
        pixel_grid = 4  # Larger pixel grid for more pixelated look
        pixel_x = (x // pixel_grid) * pixel_grid
        pixel_y = (y // pixel_grid) * pixel_grid
        pixel_size = max(pixel_grid, (size // 2) * pixel_grid)
        
        # Horizontal bar
        h_surf = pygame.Surface((pixel_size * 2, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - pixel_size, pixel_y - pixel_size // 2))
        
        # Vertical bar
        v_surf = pygame.Surface((pixel_size, pixel_size * 2))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size))
        
    def _draw_energy_burst(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw energy bursts as bright pixelated stars"""
        pixel_grid = 4
        pixel_x = (x // pixel_grid) * pixel_grid
        pixel_y = (y // pixel_grid) * pixel_grid
        pixel_size = max(pixel_grid, (size // 2) * pixel_grid)
        
        # Main cross
        h_surf = pygame.Surface((pixel_size * 3, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - pixel_size // 2))
        
        v_surf = pygame.Surface((pixel_size, pixel_size * 3))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 3) // 2))
        
        # Diagonal arms for star effect
        if size >= 3:
            # Top-right diagonal
            d1_surf = pygame.Surface((pixel_size * 2, pixel_size))
            d1_surf.fill(color)
            d1_surf.set_alpha(alpha)
            screen.blit(d1_surf, (pixel_x + pixel_size // 2, pixel_y - pixel_size * 2))


class NuclearMegabombEffect:
    """Nuclear-style megabomb explosion with shockwave, smoke, and massive explosion"""
    
    def __init__(self, x: float, y: float):
        self.particles = []
        self.duration = 2.0  # Much faster dramatic effect
        self.elapsed = 0.0
        self.center_x = x
        self.center_y = y
        
        # Phase tracking
        self.shockwave_phase = True
        self.smoke_phase = False
        self.explosion_phase = False
        
        # Create initial shockwave
        self._create_initial_shockwave()
        
    def _create_initial_shockwave(self):
        """Create fast white shockwave ring that expands far"""
        # Create multiple concentric shockwave rings for circular effect
        for ring in range(3):  # 3 rings for thick circular shockwave
            for angle in range(0, 360, 3):  # Dense circle of particles
                angle_rad = math.radians(angle)
                
                # Staggered timing for wave effect
                delay_factor = ring * 0.05
                speed = 800 - (ring * 100)  # Outer rings faster
                
                particle = {
                    'x': self.center_x,
                    'y': self.center_y,
                    'vx': math.cos(angle_rad) * speed,  # VERY fast expansion
                    'vy': math.sin(angle_rad) * speed,
                    'life': 0.2 - delay_factor,  # Very quick shockwave
                    'max_life': 0.2 - delay_factor,
                    'color': (255, 255, 255) if ring == 0 else (255, 255, 200),
                    'size': random.randint(4, 8),
                    'type': 'shockwave'
                }
                self.particles.append(particle)
    
    def _create_smoke_expansion(self):
        """Create black smoke expanding to 8x8 tile radius (256px)"""
        # Dense smoke clouds expanding to 8x8 radius
        for angle in range(0, 360, 6):  # 60 smoke clouds for density
            angle_rad = math.radians(angle)
            
            # Fast expanding smoke to reach 8x8 area
            speed = random.uniform(200, 300)  # Fast enough to reach 256px radius
            particle = {
                'x': self.center_x + random.uniform(-32, 32),
                'y': self.center_y + random.uniform(-32, 32),
                'vx': math.cos(angle_rad) * speed,
                'vy': math.sin(angle_rad) * speed,
                'life': random.uniform(0.6, 0.8),  # Shorter life for faster effect
                'max_life': random.uniform(0.6, 0.8),
                'color': random.choice([
                    (20, 20, 20),   # Very dark gray
                    (10, 10, 10),   # Almost black
                    (30, 30, 30),   # Dark gray
                    (0, 0, 0),      # Pure black
                    (40, 30, 20),   # Dark brown smoke
                ]),
                'size': random.randint(25, 40),  # Much larger smoke clouds
                'type': 'smoke'
            }
            self.particles.append(particle)
            
        # Fill in the middle with additional dense smoke
        for _ in range(80):  # More particles for density
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, 128)  # Fill center to 4-tile radius
            
            particle = {
                'x': self.center_x + math.cos(angle) * distance,
                'y': self.center_y + math.sin(angle) * distance,
                'vx': math.cos(angle) * random.uniform(150, 250),
                'vy': math.sin(angle) * random.uniform(150, 250),
                'life': random.uniform(0.5, 0.7),
                'max_life': random.uniform(0.5, 0.7),
                'color': random.choice([
                    (15, 15, 15), (25, 25, 25), (5, 5, 5), (35, 25, 15)
                ]),
                'size': random.randint(20, 35),
                'type': 'smoke'
            }
            self.particles.append(particle)
    
    def _create_massive_explosion(self):
        """Create the final massive explosion covering 8x8 tile area"""
        # ULTRA-MASSIVE CORE EXPLOSION - 8x8 tiles (256px radius)
        for i in range(50):  # Many more core particles
            angle = (i / 50) * math.pi * 2
            speed = random.uniform(300, 450)  # Much faster to reach 8x8 area
            
            particle = {
                'x': self.center_x,
                'y': self.center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(1.0, 1.5),  # Faster effect
                'max_life': random.uniform(1.0, 1.5),
                'color': (255, 255, 150),  # Bright yellow core
                'size': random.randint(60, 80),  # MASSIVE core pieces
                'type': 'mega_core'
            }
            self.particles.append(particle)
        
        # SECONDARY EXPLOSION RING - Fills 6x6 area
        for i in range(80):  # More particles
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(200, 350)  # Faster expansion
            
            particle = {
                'x': self.center_x,
                'y': self.center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.8, 1.2),
                'max_life': random.uniform(0.8, 1.2),
                'color': random.choice([
                    (255, 180, 0),   # Bright orange
                    (255, 120, 0),   # Dark orange  
                    (255, 200, 100), # Light orange
                    (255, 255, 0),   # Yellow
                    (255, 80, 0),    # Red-orange
                ]),
                'size': random.randint(40, 60),  # Much larger particles
                'type': 'mega_secondary'
            }
            self.particles.append(particle)
        
        # OUTER DEBRIS FIELD - Fills full 8x8 area
        for i in range(120):  # Even more particles
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 300)  # Fast expansion to edges
            
            particle = {
                'x': self.center_x,
                'y': self.center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.7, 1.0),
                'max_life': random.uniform(0.7, 1.0),
                'color': random.choice([
                    (255, 0, 0),     # Bright red
                    (200, 0, 0),     # Dark red
                    (255, 100, 0),   # Orange-red
                    (150, 50, 0),    # Brown-red
                    (255, 50, 50),   # Light red
                    (180, 80, 0),    # Burnt orange
                ]),
                'size': random.randint(20, 35),  # Larger debris
                'type': 'mega_debris'
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update nuclear megabomb effect with phase transitions"""
        self.elapsed += dt
        
        # Phase transitions - Much faster timing!
        if self.elapsed >= 0.15 and self.shockwave_phase:  # Faster shockwave
            self.shockwave_phase = False
            self.smoke_phase = True
            self._create_smoke_expansion()
            
        if self.elapsed >= 0.25 and self.smoke_phase:  # Explosion right after smoke starts
            self.smoke_phase = False
            self.explosion_phase = True
            self._create_massive_explosion()
        
        # Update all particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            # Apply different physics per type
            if particle['type'] == 'shockwave':
                # Shockwave maintains speed
                pass
            elif particle['type'] == 'smoke':
                # Smoke slows down and rises slightly
                particle['vx'] *= 0.95
                particle['vy'] *= 0.95
                particle['vy'] -= 20 * dt  # Slight upward drift
            else:
                # Explosion particles slow down
                particle['vx'] *= 0.92
                particle['vy'] *= 0.92
            
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw nuclear megabomb particles"""
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio)
            
            x, y = int(particle['x']), int(particle['y'])
            size = max(1, int(particle['size'] * life_ratio))
            color = particle['color']
            
            # Draw different types with different styles
            if particle['type'] == 'shockwave':
                self._draw_shockwave_particle(screen, x, y, size, color, alpha)
            elif particle['type'] == 'smoke':
                self._draw_smoke_particle(screen, x, y, size, color, alpha)
            else:
                self._draw_explosion_particle(screen, x, y, size, color, alpha)
    
    def _draw_shockwave_particle(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw bright shockwave particle as larger connected shape"""
        pixel_size = max(4, size)  # Much larger shockwave particles
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        
        # Draw as larger connected square for better circle visibility
        surf = pygame.Surface((pixel_size * 3, pixel_size * 3))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - (pixel_size * 3) // 2))
    
    def _draw_smoke_particle(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw large smoke cloud"""
        pixel_size = max(6, size // 2)  # Much larger smoke clouds
        pixel_x = (x // 4) * 4
        pixel_y = (y // 4) * 4
        
        # Draw as much larger chunky cloud
        surf = pygame.Surface((pixel_size * 4, pixel_size * 4))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size * 2, pixel_y - pixel_size * 2))
    
    def _draw_explosion_particle(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw massive explosion particle"""
        pixel_size = max(8, size // 3)  # Much larger explosion particles
        pixel_x = (x // 6) * 6
        pixel_y = (y // 6) * 6
        
        # Draw as huge explosion chunks
        surf = pygame.Surface((pixel_size * 6, pixel_size * 6))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size * 3, pixel_y - pixel_size * 3))
    
    def is_finished(self) -> bool:
        """Check if effect is finished"""
        return len(self.particles) == 0 and self.elapsed > 4.0


class BlackHoleLightningExplosion:
    """Massive lightning explosion from black hole center - board wipe effect"""
    
    def __init__(self, x: float, y: float):
        self.particles = []
        self.duration = 2.0  # 2 second explosion
        self.elapsed = 0.0
        self.center_x = x
        self.center_y = y
        
        # Create initial massive lightning explosion
        self._create_lightning_explosion()
    
    def _create_lightning_explosion(self):
        """Create massive lightning explosion covering entire board"""
        # GIANT LIGHTNING BOLTS radiating outward
        for angle in range(0, 360, 5):  # 72 lightning bolts
            angle_rad = math.radians(angle)
            
            # Create multiple segments per bolt for smoother lightning
            segments = 25
            for segment in range(segments):
                progress = segment / segments
                distance = progress * 400  # Reach far across board
                
                # Lightning zigzag
                zigzag = math.sin(progress * 20) * 20  # More zigzag
                
                x = self.center_x + math.cos(angle_rad) * distance
                y = self.center_y + math.sin(angle_rad) * distance
                
                # Add zigzag perpendicular to main direction
                perp_angle = angle_rad + math.pi / 2
                x += math.cos(perp_angle) * zigzag
                y += math.sin(perp_angle) * zigzag
                
                particle = {
                    'x': x,
                    'y': y,
                    'life': random.uniform(0.5, 1.0),
                    'max_life': random.uniform(0.5, 1.0),
                    'color': random.choice([
                        (255, 255, 255),  # Pure white
                        (200, 200, 255),  # Electric blue
                        (255, 255, 200),  # Electric yellow
                        (180, 220, 255),  # Light blue
                    ]),
                    'size': random.randint(8, 15),  # Large lightning
                    'type': 'lightning_bolt',
                    'intensity': random.uniform(0.8, 1.0)
                }
                self.particles.append(particle)
        
        # MASSIVE ELECTRIC SPARKS filling the explosion area
        for i in range(300):  # Many sparks
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(50, 350)
            
            x = self.center_x + math.cos(angle) * distance
            y = self.center_y + math.sin(angle) * distance
            
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-200, 200),
                'vy': random.uniform(-200, 200),
                'life': random.uniform(0.3, 0.8),
                'max_life': random.uniform(0.3, 0.8),
                'color': random.choice([
                    (255, 255, 255),  # White
                    (220, 240, 255),  # Light electric blue
                    (255, 255, 180),  # Electric yellow
                    (200, 255, 200),  # Electric green
                    (255, 200, 255),  # Electric magenta
                ]),
                'size': random.randint(6, 12),
                'type': 'electric_spark',
                'intensity': random.uniform(0.7, 1.0)
            }
            self.particles.append(particle)
        
        # BRIGHT FLASH at center
        for i in range(20):
            particle = {
                'x': self.center_x + random.uniform(-30, 30),
                'y': self.center_y + random.uniform(-30, 30),
                'vx': 0,
                'vy': 0,
                'life': random.uniform(0.3, 0.6),
                'max_life': random.uniform(0.3, 0.6),
                'color': (255, 255, 255),  # Pure white flash
                'size': random.randint(20, 30),
                'type': 'center_flash',
                'intensity': 1.0
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update black hole lightning explosion"""
        self.elapsed += dt
        
        for particle in self.particles[:]:
            if particle['type'] == 'lightning_bolt':
                # Lightning bolts just fade
                particle['life'] -= dt
                
            elif particle['type'] == 'electric_spark':
                # Sparks move and fade
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vx'] *= 0.95  # Slight slowdown
                particle['vy'] *= 0.95
                particle['life'] -= dt
                
            elif particle['type'] == 'center_flash':
                # Flash particles just fade
                particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw black hole lightning explosion"""
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio * particle['intensity'])
            
            x, y = int(particle['x']), int(particle['y'])
            size = max(1, int(particle['size'] * life_ratio))
            color = particle['color']
            
            if particle['type'] == 'lightning_bolt':
                self._draw_lightning_segment(screen, x, y, size, color, alpha)
            elif particle['type'] == 'electric_spark':
                self._draw_electric_spark(screen, x, y, size, color, alpha)
            elif particle['type'] == 'center_flash':
                self._draw_center_flash(screen, x, y, size, color, alpha)
    
    def _draw_lightning_segment(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw lightning segment as bright thick line"""
        pixel_size = max(3, size // 2)
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        
        surf = pygame.Surface((pixel_size * 2, pixel_size * 2))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size, pixel_y - pixel_size))
    
    def _draw_electric_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw electric spark as bright cross"""
        pixel_size = max(2, size // 3)
        pixel_x = (x // 2) * 2
        pixel_y = (y // 2) * 2
        
        # Horizontal bar
        h_surf = pygame.Surface((pixel_size * 3, pixel_size))
        h_surf.fill(color)
        h_surf.set_alpha(alpha)
        screen.blit(h_surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - pixel_size // 2))
        
        # Vertical bar
        v_surf = pygame.Surface((pixel_size, pixel_size * 3))
        v_surf.fill(color)
        v_surf.set_alpha(alpha)
        screen.blit(v_surf, (pixel_x - pixel_size // 2, pixel_y - (pixel_size * 3) // 2))
    
    def _draw_center_flash(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw bright center flash"""
        pixel_size = max(4, size // 3)
        pixel_x = (x // 3) * 3
        pixel_y = (y // 3) * 3
        
        surf = pygame.Surface((pixel_size * 3, pixel_size * 3))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - (pixel_size * 3) // 2, pixel_y - (pixel_size * 3) // 2))
    
    def is_finished(self) -> bool:
        """Check if explosion is finished"""
        return len(self.particles) == 0 and self.elapsed > 2.0
    
    def _draw_crackle_spark(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int], alpha: int):
        """Draw crackle sparks as tiny bright pixelated dots"""
        pixel_grid = 4
        pixel_x = (x // pixel_grid) * pixel_grid
        pixel_y = (y // pixel_grid) * pixel_grid
        pixel_size = max(pixel_grid, size * pixel_grid)
        
        # Main dot
        surf = pygame.Surface((pixel_size, pixel_size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, (pixel_x - pixel_size // 2, pixel_y - pixel_size // 2))
        
        # Add small cross pattern for crackling effect
        if size >= 2:
            # Tiny horizontal
            h_surf = pygame.Surface((pixel_size * 2, pixel_grid))
            h_surf.fill(color)
            h_surf.set_alpha(alpha // 2)
            screen.blit(h_surf, (pixel_x - pixel_size, pixel_y - pixel_grid // 2))
            
            # Tiny vertical  
            v_surf = pygame.Surface((pixel_grid, pixel_size * 2))
            v_surf.fill(color)
            v_surf.set_alpha(alpha // 2)
            screen.blit(v_surf, (pixel_x - pixel_grid // 2, pixel_y - pixel_size))
    
    def is_finished(self) -> bool:
        """Check if board wipe arc effect is finished"""
        return len(self.particles) == 0 and self.elapsed > self.duration