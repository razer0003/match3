import pygame
import random
import sys
from typing import List, Tuple, Optional, Set
import math
from board import Board, Tile, TileColor, Match, MatchType
from animations import FallAnimation, SwapAnimation, PulseAnimation, ParticleEffect

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FPS = 60

# Background and UI colors
BACKGROUND_COLOR = (30, 30, 30)
GRID_COLOR = (100, 100, 100)
SELECTED_COLOR = (255, 255, 255)
MATCH_HIGHLIGHT_COLOR = (255, 255, 0, 128)  # Yellow with transparency

class Match3Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Match 3 Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.selected_tile = None
        self.animating = False
        self.score = 0
        self.combo_multiplier = 1
        
        # Animation systems
        self.fall_animations = []
        self.swap_animations = []
        self.pulse_animations = []
        self.particle_effects = []
        
        # Level configuration - first level takes up half the screen
        self.current_level = 1
        self.configure_level(self.current_level)
        
        # Initialize board
        self.board = Board(self.board_width, self.board_height, self.tile_size)
        self.board.generate_initial_board()
        
        # Calculate board position to center it
        total_board_width = self.board_width * self.tile_size
        total_board_height = self.board_height * self.tile_size
        self.board_x = (WINDOW_WIDTH - total_board_width) // 2
        self.board_y = (WINDOW_HEIGHT - total_board_height) // 2
        
        # Font for UI
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
    
    def configure_level(self, level):
        """Configure level-specific parameters"""
        if level == 1:
            # First level takes up half the 1080p size
            self.tile_size = 60
            self.board_width = 8
            self.board_height = 9  # Fits nicely in half screen height
        # Add more level configurations here as needed
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()
    
    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)
    
    def handle_mouse_click(self, pos):
        """Handle mouse clicks for tile selection and swapping"""
        # Convert screen coordinates to board coordinates
        board_x = pos[0] - self.board_x
        board_y = pos[1] - self.board_y
        
        if 0 <= board_x < self.board_width * self.tile_size and 0 <= board_y < self.board_height * self.tile_size:
            col = board_x // self.tile_size
            row = board_y // self.tile_size
            
            # Check if this tile is currently animating (falling or swapping)
            if self.is_tile_animating(row, col):
                return
            
            if self.selected_tile is None:
                # Select the first tile (only if it's not animating)
                self.selected_tile = (row, col)
            else:
                # Check if selected tile is still valid (not animating)
                if self.is_tile_animating(*self.selected_tile):
                    self.selected_tile = (row, col)  # Select new tile instead
                    return
                
                # Try to swap with the selected tile
                if self.are_adjacent(self.selected_tile, (row, col)):
                    # Check if either tile involved in the swap is animating
                    if not (self.is_tile_animating(*self.selected_tile) or self.is_tile_animating(row, col)):
                        self.start_swap_animation(self.selected_tile, (row, col))
                self.selected_tile = None
    
    def are_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent (horizontally or vertically)"""
        row1, col1 = pos1
        row2, col2 = pos2
        return (abs(row1 - row2) == 1 and col1 == col2) or (abs(col1 - col2) == 1 and row1 == row2)
    
    def start_swap_animation(self, pos1, pos2):
        """Start swap animation between two tiles"""
        self.animating = True
        
        # Get screen positions
        screen_pos1 = self.get_tile_screen_pos(pos1)
        screen_pos2 = self.get_tile_screen_pos(pos2)
        
        # Create swap animation
        swap_anim = SwapAnimation(screen_pos1, screen_pos2, 0.3)
        swap_anim.tile_pos1 = pos1
        swap_anim.tile_pos2 = pos2
        self.swap_animations.append(swap_anim)
        
        # Perform the actual swap on the board
        self.board.swap_tiles(pos1, pos2)
    
    def get_tile_screen_pos(self, board_pos):
        """Convert board position to screen position"""
        row, col = board_pos
        x = self.board_x + col * self.tile_size + self.tile_size // 2
        y = self.board_y + row * self.tile_size + self.tile_size // 2
        return (x, y)
    
    def complete_swap_animation(self, swap_anim):
        """Complete a swap animation and check for matches"""
        pos1, pos2 = swap_anim.tile_pos1, swap_anim.tile_pos2
        
        # Check for matches
        matches = self.board.find_all_matches()
        
        if matches:
            # Valid move - process matches
            self.process_matches(matches)
        else:
            # Invalid move - swap back
            self.board.swap_tiles(pos1, pos2)
            # Create reverse swap animation
            screen_pos1 = self.get_tile_screen_pos(pos1)
            screen_pos2 = self.get_tile_screen_pos(pos2)
            reverse_swap = SwapAnimation(screen_pos2, screen_pos1, 0.2)
            reverse_swap.tile_pos1 = pos1
            reverse_swap.tile_pos2 = pos2
            reverse_swap.is_reversal = True
            self.swap_animations.append(reverse_swap)
    
    def process_matches(self, matches):
        """Process all matches found on the board"""
        # Add score and create particle effects
        for match in matches:
            # Calculate score with combo multiplier
            match_score = match.score * self.combo_multiplier
            self.score += match_score
            
            # Create particle effects for matched tiles
            for row, col in match.positions:
                screen_pos = self.get_tile_screen_pos((row, col))
                tile = self.board.get_tile(row, col)
                if tile:
                    effect = ParticleEffect(screen_pos[0], screen_pos[1], tile.color.value)
                    self.particle_effects.append(effect)
            
            # Clear the match
            self.board.clear_matches(match)
        
        # Increase combo multiplier
        self.combo_multiplier += 1
        
        # Start falling animation
        self.start_fall_animation()
    
    def start_fall_animation(self):
        """Start falling animation for tiles after matches are cleared"""
        # Apply gravity to determine new positions
        fall_data = self.board.apply_gravity_with_animation_data()
        
        # Create fall animations for existing tiles
        for col, tiles_to_fall in fall_data.items():
            for tile_data in tiles_to_fall:
                start_y = self.board_y + tile_data['from_row'] * self.tile_size
                end_y = self.board_y + tile_data['to_row'] * self.tile_size
                
                if start_y != end_y:
                    # Calculate duration based on fall distance for more natural feel
                    fall_distance = end_y - start_y
                    base_duration = 0.3
                    distance_factor = fall_distance / (self.tile_size * 3)  # Normalize by 3 tile heights
                    duration = base_duration + distance_factor * 0.3
                    
                    fall_anim = FallAnimation(start_y, end_y, duration)
                    fall_anim.col = col
                    fall_anim.to_row = tile_data['to_row']
                    fall_anim.tile = tile_data['tile']
                    fall_anim.is_existing_tile = True
                    self.fall_animations.append(fall_anim)
        
        # Fill empty spaces with new tiles (they'll fall from above)
        self.board.fill_empty_spaces_with_fall_data()
        
        # Create fall animations for new tiles (with slight delay)
        self.create_new_tile_animations()
    
    def create_new_tile_animations(self):
        """Create fall animations for newly spawned tiles"""
        for col in range(self.board_width):
            # Find all newly spawned tiles in this column from top to bottom
            new_tiles = []
            for row in range(self.board_height):
                tile = self.board.get_tile(row, col)
                if tile and hasattr(tile, 'newly_spawned') and tile.newly_spawned:
                    new_tiles.append((row, tile))
                    # Remove the newly_spawned flag
                    delattr(tile, 'newly_spawned')
            
            # Create animations for new tiles, stacking them properly above the board
            for i, (row, tile) in enumerate(new_tiles):
                # Stack new tiles above the board in reverse order
                # The tile that will end up at the topmost empty position should start highest
                stack_position = len(new_tiles) - i
                start_y = self.board_y - stack_position * self.tile_size
                end_y = self.board_y + row * self.tile_size
                
                # Calculate fall duration based on distance (makes it feel more natural)
                fall_distance = end_y - start_y
                fall_duration = 0.3 + (fall_distance / (self.board_height * self.tile_size)) * 0.8
                
                fall_anim = FallAnimation(start_y, end_y, fall_duration)
                fall_anim.col = col
                fall_anim.to_row = row
                fall_anim.tile = tile
                fall_anim.is_new_tile = True
                self.fall_animations.append(fall_anim)
    
    def complete_fall_animation(self):
        """Complete falling animation and check for new matches"""
        # Check for new matches
        new_matches = self.board.find_all_matches()
        if new_matches:
            # Continue the chain
            self.process_matches(new_matches)
        else:
            # Chain is complete, reset combo multiplier
            self.combo_multiplier = 1
            
            # Check if there are possible moves
            if not self.board.has_possible_moves():
                # No more moves available, shuffle the board
                self.board.shuffle()
            
            # Animation complete
            self.animating = False
    
    def update(self, dt):
        """Update game state"""
        # Update swap animations
        for swap_anim in self.swap_animations[:]:
            if swap_anim.update(dt):
                # Animation completed
                self.swap_animations.remove(swap_anim)
                
                if hasattr(swap_anim, 'is_reversal'):
                    # Reversal complete, stop animating
                    self.animating = False
                else:
                    # Check for matches
                    self.complete_swap_animation(swap_anim)
        
        # Update fall animations
        for fall_anim in self.fall_animations[:]:
            if fall_anim.update(dt):
                # Animation completed
                self.fall_animations.remove(fall_anim)
        
        # Check if all fall animations are complete
        if not self.fall_animations and len([a for a in self.swap_animations if not hasattr(a, 'is_reversal')]) == 0:
            if self.animating:
                self.complete_fall_animation()
        
        # Update pulse animations
        for pulse_anim in self.pulse_animations[:]:
            if pulse_anim.update(dt):
                self.pulse_animations.remove(pulse_anim)
        
        # Update particle effects
        for effect in self.particle_effects[:]:
            effect.update(dt)
            if effect.is_finished():
                self.particle_effects.remove(effect)
    
    def draw(self):
        """Draw the entire game"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw the board
        self.draw_board()
        
        # Draw UI elements
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_board(self):
        """Draw the game board and tiles"""
        # Draw static tiles (not involved in animations)
        for row in range(self.board_height):
            for col in range(self.board_width):
                # Skip tiles that are currently animating
                if self.is_tile_animating(row, col):
                    continue
                
                self.draw_tile_at_position(row, col, row, col)
        
        # Draw falling tiles
        for fall_anim in self.fall_animations:
            # Calculate current position
            current_row = (fall_anim.current_y - self.board_y) / self.tile_size
            self.draw_animated_tile(fall_anim.tile, fall_anim.col, current_row)
        
        # Draw swapping tiles
        for swap_anim in self.swap_animations:
            tile1 = self.board.get_tile(*swap_anim.tile_pos1)
            tile2 = self.board.get_tile(*swap_anim.tile_pos2)
            
            if tile1:
                self.draw_animated_tile_at_screen_pos(tile1, swap_anim.current_pos1)
            if tile2:
                self.draw_animated_tile_at_screen_pos(tile2, swap_anim.current_pos2)
    
    def is_tile_animating(self, row, col):
        """Check if a tile is currently involved in any animation"""
        # Check if involved in swap animation
        for swap_anim in self.swap_animations:
            if (row, col) in [swap_anim.tile_pos1, swap_anim.tile_pos2]:
                return True
        
        # Check if involved in fall animation
        for fall_anim in self.fall_animations:
            if fall_anim.col == col and fall_anim.to_row == row:
                return True
        
        return False
    
    def draw_tile_at_position(self, tile_row, tile_col, draw_row, draw_col):
        """Draw a tile at a specific board position"""
        # Calculate tile position
        x = self.board_x + draw_col * self.tile_size
        y = self.board_y + draw_row * self.tile_size
        
        # Draw tile background
        tile_rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
        
        # Get tile color
        tile = self.board.get_tile(tile_row, tile_col)
        if tile:
            color = tile.color.value
        else:
            color = TileColor.EMPTY.value
        
        # Draw tile with rounded corners for better look
        self.draw_rounded_rect(self.screen, color, tile_rect, 8)
        pygame.draw.rect(self.screen, GRID_COLOR, tile_rect, 2)
        
        # Highlight selected tile
        if self.selected_tile == (tile_row, tile_col):
            pygame.draw.rect(self.screen, SELECTED_COLOR, tile_rect, 4)
    
    def draw_animated_tile(self, tile, col, row_float):
        """Draw a tile at a floating-point row position"""
        x = self.board_x + col * self.tile_size
        y = self.board_y + row_float * self.tile_size
        
        tile_rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
        
        if tile:
            color = tile.color.value
            self.draw_rounded_rect(self.screen, color, tile_rect, 8)
            pygame.draw.rect(self.screen, GRID_COLOR, tile_rect, 2)
    
    def draw_animated_tile_at_screen_pos(self, tile, screen_pos):
        """Draw a tile at a specific screen position"""
        x, y = screen_pos
        x -= self.tile_size // 2
        y -= self.tile_size // 2
        
        tile_rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
        
        if tile:
            color = tile.color.value
            self.draw_rounded_rect(self.screen, color, tile_rect, 8)
            pygame.draw.rect(self.screen, GRID_COLOR, tile_rect, 2)
    
    def draw_rounded_rect(self, surface, color, rect, radius):
        """Draw a rounded rectangle"""
        # Simple implementation - draw rectangle with rounded corners
        pygame.draw.rect(surface, color, rect)
        # Could add actual rounded corner implementation here for better visuals
    
    def draw_ui(self):
        """Draw UI elements like score, level info, etc."""
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        # Draw level
        level_text = self.font.render(f"Level: {self.current_level}", True, (255, 255, 255))
        self.screen.blit(level_text, (20, 60))
        
        # Draw combo multiplier if active
        if self.combo_multiplier > 1:
            combo_text = self.font.render(f"Combo x{self.combo_multiplier}!", True, (255, 255, 0))
            self.screen.blit(combo_text, (20, 100))
        
        # Draw particle effects
        for effect in self.particle_effects:
            effect.draw(self.screen)
        
        # Draw instructions
        if not self.animating and self.selected_tile is None:
            instruction_text = self.font.render("Click tiles to select and swap adjacent ones", True, (200, 200, 200))
            text_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
            self.screen.blit(instruction_text, text_rect)

if __name__ == "__main__":
    game = Match3Game()
    game.run()