"""
Level Select Screen for Match 3 game
Simple temporary UI for choosing levels
"""

import pygame
from typing import Optional
from levels import get_available_levels, get_level_config

class LevelSelectScreen:
    """Temporary level select screen"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_level = None
        self.running = True
        self.levels = get_available_levels()
        self.current_selection = 0  # Index of currently highlighted level
        
        # Initialize fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 72)
        self.level_font = pygame.font.Font(None, 48)
        self.instruction_font = pygame.font.Font(None, 32)
        
        # Colors
        self.bg_color = (20, 20, 40)
        self.title_color = (255, 255, 255)
        self.level_normal_color = (200, 200, 200)
        self.level_selected_color = (255, 255, 0)
        self.instruction_color = (150, 150, 150)
        
    def handle_events(self, events):
        """Handle input events"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.current_selection = (self.current_selection - 1) % len(self.levels)
                elif event.key == pygame.K_DOWN:
                    self.current_selection = (self.current_selection + 1) % len(self.levels)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.selected_level = self.levels[self.current_selection]
                    self.running = False
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check if clicked on a level
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    level_y_start = self.screen_height // 2 - 50
                    for i, level in enumerate(self.levels):
                        level_rect_y = level_y_start + i * 80
                        if level_rect_y <= mouse_y <= level_rect_y + 60:
                            self.selected_level = level
                            self.running = False
                            break
    
    def draw(self, screen):
        """Draw the level select screen"""
        # Clear screen
        screen.fill(self.bg_color)
        
        # Draw title
        title_surface = self.title_font.render("SELECT LEVEL", True, self.title_color)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 150))
        screen.blit(title_surface, title_rect)
        
        # Draw level options
        level_y_start = self.screen_height // 2 - 50
        for i, level in enumerate(self.levels):
            config = get_level_config(level)
            
            # Determine color based on selection
            color = self.level_selected_color if i == self.current_selection else self.level_normal_color
            
            # Draw level info
            level_text = f"{config.name} ({config.width}x{config.height})"
            level_surface = self.level_font.render(level_text, True, color)
            level_rect = level_surface.get_rect(center=(self.screen_width // 2, level_y_start + i * 80))
            screen.blit(level_surface, level_rect)
            
            # Draw selection indicator
            if i == self.current_selection:
                pygame.draw.rect(screen, self.level_selected_color, 
                               (level_rect.left - 20, level_rect.top - 5, 
                                level_rect.width + 40, level_rect.height + 10), 2)
        
        # Draw instructions
        instructions = [
            "Use UP/DOWN arrows or mouse to select",
            "Press ENTER/SPACE or click to choose level",
            "Press ESC to exit"
        ]
        
        instruction_y = self.screen_height - 120
        for instruction in instructions:
            instruction_surface = self.instruction_font.render(instruction, True, self.instruction_color)
            instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y))
            screen.blit(instruction_surface, instruction_rect)
            instruction_y += 30
    
    def get_selected_level(self) -> Optional[int]:
        """Get the selected level, or None if cancelled"""
        return self.selected_level