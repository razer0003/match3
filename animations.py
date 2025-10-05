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
            print(f"SwapAnimation update: dt={dt:.4f}, elapsed={self.elapsed:.4f}, duration={self.duration:.4f}, progress={self.get_progress():.4f}")
        
        completed = super().update(dt)
        progress = self.get_progress()
        
        # Use smooth easing
        eased_progress = self.ease_in_out_cubic(progress)
        
        # Interpolate positions
        self.current_pos1 = self.lerp_pos(self.start_pos1, self.start_pos2, eased_progress)
        self.current_pos2 = self.lerp_pos(self.start_pos2, self.start_pos1, eased_progress)
        
        if hasattr(self, 'tile_pos1') and getattr(self, 'tile_pos1', None) is not None and completed:
            print(f"SwapAnimation COMPLETED: final elapsed={self.elapsed:.4f}, duration={self.duration:.4f}")
        
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