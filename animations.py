import pygame
import math
import random
from typing import Tuple, Optional

class Animation:
    """Base class for animations"""
    
    def __init__(self, duration: float):
        self.duration = duration
        self.elapsed = 0.0
        self.completed = False
    
    def update(self, dt: float) -> bool:
        """Update animation, returns True if completed"""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.completed = True
        return self.completed
    
    def get_progress(self) -> float:
        """Get animation progress (0.0 to 1.0)"""
        return self.elapsed / self.duration if self.duration > 0 else 1.0

class FallAnimation(Animation):
    """Animation for falling tiles"""
    
    def __init__(self, start_y: float, end_y: float, duration: float):
        super().__init__(duration)
        self.start_y = start_y
        self.end_y = end_y
        self.current_y = start_y
    
    def update(self, dt: float) -> bool:
        completed = super().update(dt)
        progress = self.get_progress()
        
        # Clamp progress to prevent overshooting
        progress = min(1.0, max(0.0, progress))
        
        # Use easing function for more natural fall
        eased_progress = self.ease_in_quad(progress)
        self.current_y = self.start_y + (self.end_y - self.start_y) * eased_progress
        
        # Ensure we never overshoot the target position
        if self.start_y < self.end_y:  # Falling down
            self.current_y = min(self.current_y, self.end_y)
        else:  # Falling up (shouldn't happen, but safety)
            self.current_y = max(self.current_y, self.end_y)
        
        return completed
    
    def ease_in_quad(self, t: float) -> float:
        """Quadratic easing function for gentle acceleration"""
        # Simple quadratic easing that can't overshoot
        return t * t

class SwapAnimation(Animation):
    """Animation for swapping tiles"""
    
    def __init__(self, pos1: Tuple[float, float], pos2: Tuple[float, float], duration: float):
        super().__init__(duration)
        self.start_pos1 = pos1
        self.start_pos2 = pos2
        self.current_pos1 = pos1
        self.current_pos2 = pos2
    
    def update(self, dt: float) -> bool:
        # Debug output for boss animations
        if hasattr(self, 'tile_pos1') and getattr(self, 'tile_pos1', None) is not None:
            pass  # No debug output needed
        
        completed = super().update(dt)
        progress = self.get_progress()
        
        # Use smooth easing
        eased_progress = self.ease_in_out_cubic(progress)
        
        # Interpolate positions
        self.current_pos1 = self.lerp_pos(self.start_pos1, self.start_pos2, eased_progress)
        self.current_pos2 = self.lerp_pos(self.start_pos2, self.start_pos1, eased_progress)
        
        if hasattr(self, 'tile_pos1') and getattr(self, 'tile_pos1', None) is not None and completed:
            pass  # Animation completed, no debug needed
        
        return completed
    
    def lerp_pos(self, pos1: Tuple[float, float], pos2: Tuple[float, float], t: float) -> Tuple[float, float]:
        """Linear interpolation between two positions"""
        x1, y1 = pos1
        x2, y2 = pos2
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
    
    def ease_in_out_cubic(self, t: float) -> float:
        """Smooth cubic easing function"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

class PulseAnimation(Animation):
    """Animation for highlighting matches"""
    
    def __init__(self, duration: float, min_scale: float = 0.8, max_scale: float = 1.2):
        super().__init__(duration)
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.current_scale = 1.0
    
    def update(self, dt: float) -> bool:
        completed = super().update(dt)
        progress = self.get_progress()
        
        # Create pulsing effect
        pulse = math.sin(progress * math.pi * 4)  # 4 pulses over duration
        scale_range = self.max_scale - self.min_scale
        self.current_scale = self.min_scale + (scale_range * (pulse + 1) / 2)
        
        return completed

class ParticleEffect:
    """Simple particle effect for match clearing"""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], count: int = 10):
        self.particles = []
        for _ in range(count):
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-150, -50),
                'life': random.uniform(0.5, 1.0),
                'max_life': random.uniform(0.5, 1.0),
                'color': color,
                'size': random.uniform(2, 5)
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update all particles"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += 200 * dt  # Gravity
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw all particles"""
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            size = int(particle['size'] * (particle['life'] / particle['max_life']))
            
            if size > 0:
                # Create a surface with per-pixel alpha
                particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                
                # Use RGB color for drawing, then set alpha on the surface
                rgb_color = particle['color'][:3]  # Extract only RGB components
                pygame.draw.circle(particle_surface, rgb_color, (size, size), size)
                
                # Apply alpha to the entire surface
                particle_surface.set_alpha(alpha)
                screen.blit(particle_surface, (particle['x'] - size, particle['y'] - size))
    
    def is_finished(self) -> bool:
        """Check if all particles are finished"""
        return len(self.particles) == 0

class PopAnimation(Animation):
    """Animation for tiles popping/shrinking when matched"""
    
    def __init__(self, tile_positions: list, tile_data: list, center_pos: Optional[Tuple[float, float]] = None, duration: float = 0.15):
        super().__init__(duration)
        self.tile_positions = tile_positions  # List of (row, col, x, y) positions
        self.tile_data = tile_data  # List of actual tile objects to draw during animation
        self.center_pos = center_pos  # If None, shrink to nothing; if set, shrink to center
        self.scales = [1.0] * len(tile_positions)  # Current scale for each tile
        self.is_special = center_pos is not None
    
    def update(self, dt: float) -> bool:
        completed = super().update(dt)
        progress = self.get_progress()
        
        
        if self.is_special:
            # Special tile creation: shrink toward center position
            for i in range(len(self.scales)):
                # Fast shrink with slight bounce
                self.scales[i] = max(0.0, 1.0 - (progress * 1.2))
        else:
            # Normal match: shrink to nothing with bounce
            bounce_factor = 1.0 + (math.sin(progress * math.pi * 2) * 0.1)
            for i in range(len(self.scales)):
                self.scales[i] = max(0.0, (1.0 - progress) * bounce_factor)
        
        return completed
    
    def get_tile_scale(self, index: int) -> float:
        """Get the current scale for a tile at given index"""
        if index < len(self.scales):
            return self.scales[index]
        return 0.0

class SpawnAnimation(Animation):
    """Animation for special tiles spawning/growing from tiny to normal size"""
    
    def __init__(self, row: int, col: int, duration: float = 0.25):
        super().__init__(duration)
        self.row = row
        self.col = col
        self.scale = 0.0  # Start tiny
    
    def update(self, dt: float) -> bool:
        completed = super().update(dt)
        progress = self.get_progress()
        
        # Elastic easing out for a satisfying "pop in" effect
        if progress < 1.0:
            # Elastic ease-out formula
            c4 = (2 * math.pi) / 3
            self.scale = math.pow(2, -10 * progress) * math.sin((progress * 10 - 0.75) * c4) + 1
            self.scale = max(0.0, min(1.2, self.scale))  # Clamp and allow slight overshoot
        else:
            self.scale = 1.0  # Final size
        
        return completed
    
    def get_scale(self) -> float:
        """Get the current scale for the spawning tile"""
        return self.scale

class PopParticle:
    """Simple pop particle effect"""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], is_special: bool = False):
        self.x = x
        self.y = y
        self.color = color if not is_special else (255, 255, 255)  # White for special
        self.life = 0.3  # Short duration
        self.max_life = 0.3
        self.size = 8 if not is_special else 12
        self.max_size = self.size
        self.particles = []
        
        # Create small particle burst
        particle_count = 6 if not is_special else 10
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.2, 0.4),
                'max_life': random.uniform(0.2, 0.4),
                'size': random.uniform(2, 4)
            })
    
    def update(self, dt: float):
        """Update particle effect"""
        self.life -= dt
        
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vx'] *= 0.95  # Friction
            particle['vy'] *= 0.95
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface):
        """Draw particle effect"""
        if self.life <= 0:
            return
            
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
                
            # Keep original size and full opacity for crisp pixel art look
            size = int(particle['size'])
            
            # Draw solid circle directly on screen - no alpha blending
            pygame.draw.circle(screen, self.color, 
                             (int(particle['x']), int(particle['y'])), size)
    
    def is_finished(self) -> bool:
        """Check if particle effect is done"""
        return self.life <= 0 and len(self.particles) == 0