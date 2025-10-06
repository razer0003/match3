import pygame
import random
import sys
import os
import time
from typing import List, Tuple, Optional, Set
import math
from board import Board, Tile, TileColor, Match, MatchType
from animations import FallAnimation, SwapAnimation, PulseAnimation, ParticleEffect, PopAnimation, PopParticle, SpawnAnimation
from special_tiles import SpecialTile, SpecialTileType
from arcade_particles import PixelParticleSystem
from levels import get_level_config, LevelConfig
from level_select import LevelSelectScreen
from boss_ai import Match3AI, AIConfig, AIDifficulty

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

class SpriteManager:
    """Manages loading and caching of tile sprites"""
    
    def __init__(self):
        self.tile_sprites = {}
        self.sprites_path = os.path.join(os.path.dirname(__file__), "sprites", "tiles")
        self.load_tile_sprites()
    
    def load_tile_sprites(self):
        """Load all tile sprites from the sprites/tiles directory"""
        sprite_files = {
            TileColor.RED: "redtile.png",
            TileColor.GREEN: "greentile.png", 
            TileColor.BLUE: "bluetile.png",
            TileColor.YELLOW: "yellowtile.png",
            TileColor.ORANGE: "orangetile.png"
        }
        
        # Load regular tile sprites
        for color, filename in sprite_files.items():
            filepath = os.path.join(self.sprites_path, filename)
            if os.path.exists(filepath):
                try:
                    sprite = pygame.image.load(filepath).convert_alpha()
                    self.tile_sprites[color] = sprite
                    print(f"✓ Loaded sprite for {color.name}: {filename}")
                except pygame.error as e:
                    print(f"✗ Failed to load {filename}: {e}")
                    # Fallback to solid color
                    self.tile_sprites[color] = None
            else:
                print(f"✗ Sprite file not found: {filepath}")
                self.tile_sprites[color] = None
        
        # Load special tile sprites
        special_sprites = {
            'rocket': 'rockettile.png',
            'bomb': 'bombtile.png',
            'lightning': 'lightningtile.png',
            'boardwipe': 'boardwipetile.png'
        }
        
        for special_type, filename in special_sprites.items():
            filepath = os.path.join(self.sprites_path, filename)
            if os.path.exists(filepath):
                try:
                    sprite = pygame.image.load(filepath).convert_alpha()
                    self.tile_sprites[special_type] = sprite
                    print(f"✓ Loaded special sprite for {special_type}: {filename}")
                except pygame.error as e:
                    print(f"✗ Failed to load {filename}: {e}")
                    self.tile_sprites[special_type] = None
            else:
                print(f"✗ Special sprite file not found: {filepath}")
                self.tile_sprites[special_type] = None
        
        # Load border sprite
        border_filepath = os.path.join(self.sprites_path, "border.png")
        if os.path.exists(border_filepath):
            try:
                self.border_sprite = pygame.image.load(border_filepath).convert_alpha()
                print(f"✓ Loaded border sprite: border.png")
            except pygame.error as e:
                print(f"✗ Failed to load border.png: {e}")
                self.border_sprite = None
        else:
            print(f"✗ Border sprite file not found: {border_filepath}")
            self.border_sprite = None
    
    def get_tile_sprite(self, color: TileColor, tile_size: int):
        """Get a scaled sprite for the given color and size"""
        if color not in self.tile_sprites or self.tile_sprites[color] is None:
            return None
        
        sprite = self.tile_sprites[color]
        # Scale sprite to be 5 pixels bigger than tile size for normal color tiles
        sprite_size = tile_size + 5
        # Tiles are now 16x16, so calculate scaling factor appropriately
        scale_factor = sprite_size / 16  # 16x16 is the new base size
        # Use nearest neighbor scaling to preserve pixel art crisp look
        return pygame.transform.scale_by(sprite, scale_factor)
    
    def has_sprite(self, color: TileColor) -> bool:
        """Check if we have a sprite for this color"""
        return color in self.tile_sprites and self.tile_sprites[color] is not None
    
    def get_special_sprite(self, special_type: str, tile_size: int):
        """Get a scaled sprite for special tiles"""
        if special_type not in self.tile_sprites or self.tile_sprites[special_type] is None:
            return None
        
        sprite = self.tile_sprites[special_type]
        # Assume special tiles are also 16x16, scale to fit tile size using nearest neighbor scaling
        scale_factor = tile_size / 16  # 16x16 is the base size for special tiles too
        return pygame.transform.scale_by(sprite, scale_factor)
    
    def has_special_sprite(self, special_type: str) -> bool:
        """Check if we have a sprite for this special type"""
        return special_type in self.tile_sprites and self.tile_sprites[special_type] is not None
    
    def get_border_sprite(self, width: int, height: int):
        """Get a scaled border sprite"""
        if not hasattr(self, 'border_sprite') or self.border_sprite is None:
            return None
        # For borders, we can use regular scaling since it's decorative
        return pygame.transform.scale(self.border_sprite, (width, height))
    
    def has_border_sprite(self) -> bool:
        """Check if we have a border sprite"""
        return hasattr(self, 'border_sprite') and self.border_sprite is not None

class Match3Game:
    def __init__(self, level: int = 1):
        # Enable hardware acceleration for better performance
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
        pygame.display.set_caption("Match 3 Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Performance debugging removed
        
        # Game state
        self.selected_tile = None
        self.animating = False
        self.score = 0
        self.combo_multiplier = 1
        
        # Debug mode
        self.debug_mode = False
        self.f3_pressed = False
        self.debug_special_type = 0  # Index for cycling through special tiles
        
        # Animation systems
        self.fall_animations = []
        self.swap_animations = []
        self.pulse_animations = []
        self.particle_effects = []
        self.pixel_particles = PixelParticleSystem()
        self.pop_animations = []
        self.pop_particles = []
        self.spawn_animations = []
        self.pending_matches = None
        
        # Boss board animation systems
        self.boss_fall_animations = []
        self.boss_swap_animations = []
        self.boss_pop_animations = []
        self.boss_pop_particles = []
        self.boss_spawn_animations = []
        self.boss_animating = False
        self.pending_boss_matches = None
        self.boss_move_delay = 0.0  # Delay between boss moves
        self.boss_move_cooldown = 2.0  # 2 seconds between moves
        
        # Boss board combo animation states
        self.boss_bomb_boardwipe_active = False
        self.boss_bomb_boardwipe_positions = []
        self.boss_bomb_boardwipe_timer = 0
        self.boss_bomb_boardwipe_detonation_timer = 0
        self.boss_bomb_boardwipe_detonation_index = 0
        self.boss_rocket_lightning_active = False
        self.boss_rocket_lightning_position = None
        self.boss_rocket_lightning_timer = 0.0
        self.boss_rocket_lightning_phase = None
        self.boss_reality_break_active = False
        self.boss_reality_break_position = None
        self.boss_reality_break_timer = 0.0
        self.boss_reality_break_phase = None
        
        # Bomb boardwipe animation state
        self.bomb_boardwipe_active = False
        self.bomb_boardwipe_positions = []
        self.bomb_boardwipe_timer = 0
        self.bomb_boardwipe_detonation_timer = 0
        self.bomb_boardwipe_detonation_index = 0
        
        # Rocket lightning animation state
        self.rocket_lightning_active = False
        self.rocket_lightning_rows = []
        self.rocket_lightning_timer = 0
        self.rocket_lightning_row_index = 0
        
        # Board wipe animation state
        self.board_wipe_active = False
        self.board_wipe_positions = []
        self.board_wipe_timer = 0.0
        self.board_wipe_delay = 0.2
        
        # Screen shake for dramatic effects
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_shake_timer = 0
        self.screen_offset_x = 0
        self.screen_offset_y = 0
        
        # Black hole (bomb+lightning) animation state
        self.black_hole_active = False
        self.black_hole_center_x = 0
        self.black_hole_center_y = 0
        self.black_hole_timer = 0
        self.black_hole_phase = 'condensing'  # 'condensing' or 'exploding'
        self.original_tile_positions = {}  # Store original positions for animation
        
        # Level configuration
        self.current_level = level
        self.level_config = get_level_config(level)
        self.configure_level()
        
# Performance debugging methods removed
    
    def configure_level(self):
        """Configure game settings based on current level"""
        # Configure level-specific parameters
        self.tile_size = self.level_config.tile_size
        self.board_width = self.level_config.width
        self.board_height = self.level_config.height
        
        # Initialize board and sprite manager
        self.board = Board(self.board_width, self.board_height, self.tile_size)
        self.sprite_manager = SpriteManager()
        self.sprite_manager.load_tile_sprites()
        self.board.generate_initial_board()
        
        # Boss board for dual board levels
        self.boss_board = None
        self.boss_board_x = 0
        self.boss_board_y = 0
        
        # Calculate board positions
        if self.level_config.dual_board:
            # Dual board layout - player on left, boss on right
            total_board_width = self.board_width * self.tile_size
            total_board_height = self.board_height * self.tile_size
            
            # Calculate positions to center both boards with gap to prevent border overlap
            gap_between_boards = 260  # Gap large enough to prevent border overlap (border padding = 120 each side)
            total_dual_width = (total_board_width * 2) + gap_between_boards
            start_x = (WINDOW_WIDTH - total_dual_width) // 2
            
            # Player board on the left side
            self.board_x = start_x
            self.board_y = (WINDOW_HEIGHT - total_board_height) // 2
            
            # Boss board on the right side
            self.boss_board = Board(self.board_width, self.board_height, self.tile_size)
            self.boss_board.generate_initial_board()
            self.boss_board_x = start_x + total_board_width + gap_between_boards
            self.boss_board_y = (WINDOW_HEIGHT - total_board_height) // 2
            
            # Initialize AI for boss board
            ai_config = AIConfig(AIDifficulty.NIGHTMARE)  # Maximum difficulty!
            self.boss_ai = Match3AI(ai_config)
            self.boss_ai.set_board(self.boss_board)
        else:
            # Single board layout - centered
            total_board_width = self.board_width * self.tile_size
            total_board_height = self.board_height * self.tile_size
            self.board_x = (WINDOW_WIDTH - total_board_width) // 2
            self.board_y = (WINDOW_HEIGHT - total_board_height) // 2
            self.boss_ai = None  # No AI for single board mode
        
        # Font for UI
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
    
    def run(self):
        """Main game loop"""
        while self.running:
            frame_start = time.time()
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
            elif event.type == pygame.KEYDOWN:
                self.handle_key_press(event.key)
            elif event.type == pygame.KEYUP:
                self.handle_key_release(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)
    
    def handle_key_press(self, key):
        """Handle key press events"""
        if key == pygame.K_F3:
            self.f3_pressed = True
        elif key == pygame.K_1 and self.f3_pressed:
            # Toggle debug mode with F3+1
            self.debug_mode = not self.debug_mode
            print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        elif key == pygame.K_TAB and self.debug_mode:
            # Cycle through special tile types
            from special_tiles import SpecialTileType
            special_types = [
                SpecialTileType.ROCKET_HORIZONTAL,
                SpecialTileType.ROCKET_VERTICAL,
                SpecialTileType.BOMB,
                SpecialTileType.LIGHTNING,
                SpecialTileType.BOARD_WIPE,
                SpecialTileType.BOMB_ROCKET,
                SpecialTileType.BOMB_BOARDWIPE,
                SpecialTileType.MEGA_BOMB,
                SpecialTileType.ENERGIZED_BOMB,
                SpecialTileType.ROCKET_BOARDWIPE,
                SpecialTileType.ROCKET_LIGHTNING,
                SpecialTileType.SIMPLE_CROSS,
                SpecialTileType.LIGHTNING_CROSS,
            ]
            self.debug_special_type = (self.debug_special_type + 1) % len(special_types)
            current_type = special_types[self.debug_special_type]
            print(f"Selected special tile: {current_type.name}")
    
    def handle_key_release(self, key):
        """Handle key release events"""
        if key == pygame.K_F3:
            self.f3_pressed = False
    
    def handle_mouse_click(self, pos):
        """Handle mouse clicks for tile selection and swapping"""
        # Convert screen coordinates to board coordinates (player board only)
        board_x = pos[0] - self.board_x
        board_y = pos[1] - self.board_y
        
        # In dual board mode, only allow interaction with the player board (left side)
        if self.level_config.dual_board:
            # Check if click is on the boss board (right side) - ignore it
            boss_board_x = pos[0] - self.boss_board_x
            boss_board_y = pos[1] - self.boss_board_y
            if (0 <= boss_board_x < self.board_width * self.tile_size and 
                0 <= boss_board_y < self.board_height * self.tile_size):
                return  # Click was on boss board, ignore
        
        if 0 <= board_x < self.board_width * self.tile_size and 0 <= board_y < self.board_height * self.tile_size:
            col = board_x // self.tile_size
            row = board_y // self.tile_size
            
            # Check if click is actually within the tile (accounting for spacing)
            spacing = 2
            tile_x = col * self.tile_size + spacing
            tile_y = row * self.tile_size + spacing
            tile_size_with_spacing = self.tile_size - (spacing * 2)
            
            # Check if click is within the actual tile area (not in the spacing)
            if not (tile_x <= board_x < tile_x + tile_size_with_spacing and 
                    tile_y <= board_y < tile_y + tile_size_with_spacing):
                return  # Click was in the spacing area, ignore it
            
            # Debug mode: place special tiles
            if self.debug_mode:
                self.place_debug_tile(row, col)
                return
            
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
    
    def place_debug_tile(self, row, col):
        """Place a special tile at the specified position (debug mode only)"""
        from special_tiles import SpecialTileType, create_special_tile
        from board import TileColor, Tile
        
        # Define available special tile types
        special_types = [
            SpecialTileType.ROCKET_HORIZONTAL,
            SpecialTileType.ROCKET_VERTICAL,
            SpecialTileType.BOMB,
            SpecialTileType.LIGHTNING,
            SpecialTileType.BOARD_WIPE,
            SpecialTileType.BOMB_ROCKET,
            SpecialTileType.BOMB_BOARDWIPE,
            SpecialTileType.MEGA_BOMB,
            SpecialTileType.ENERGIZED_BOMB,
            SpecialTileType.ROCKET_BOARDWIPE,
            SpecialTileType.ROCKET_LIGHTNING,
            SpecialTileType.SIMPLE_CROSS,
            SpecialTileType.LIGHTNING_CROSS,
        ]
        
        # Get current special tile type with bounds checking
        if 0 <= self.debug_special_type < len(special_types):
            current_type = special_types[self.debug_special_type]
        else:
            # Reset to first tile if out of bounds
            self.debug_special_type = 0
            current_type = special_types[0]
        
        # Create a special tile
        special_tile = create_special_tile(current_type, color=TileColor.RED)
        
        # Create a new tile with the special type
        new_tile = Tile(TileColor.RED, special_tile)  # Pass special_tile to constructor
        
        # Place the tile on the board
        self.board.set_tile(row, col, new_tile)
        
        print(f"Placed {current_type.name} at ({row}, {col})")
    
    def handle_bomb_boardwipe_combo(self, pos, combo_tile):
        """Handle the bomb + boardwipe combo with special animation"""
        from special_tiles import create_special_tile, SpecialTileType
        from board import Tile, TileColor
        
        # Clear any existing fall animations to prevent stuck falling tiles
        self.fall_animations.clear()
        
        # Get bomb positions before removing combo tile
        bomb_positions = combo_tile.get_bomb_positions(self.board, pos)
        
        # Place bombs at selected positions
        for bomb_pos in bomb_positions:
            bomb_special = create_special_tile(SpecialTileType.BOMB, color=TileColor.ORANGE)
            bomb_tile = Tile(TileColor.ORANGE, special_tile=bomb_special)
            self.board.set_tile(*bomb_pos, bomb_tile)
        
        # Remove the combo tile after placing bombs
        self.board.set_tile(*pos, None)
        
        # Sort positions from top to bottom, left to right for sequential detonation
        bomb_positions.sort(key=lambda pos: (pos[0], pos[1]))
        
        # Set up animation state
        self.bomb_boardwipe_active = True
        self.bomb_boardwipe_positions = bomb_positions
        self.bomb_boardwipe_timer = 0
        self.bomb_boardwipe_detonation_timer = 0
        self.bomb_boardwipe_detonation_index = 0
        
        # Add score for the combo
        self.score += combo_tile.get_score_bonus()
        
        # Immediately start a fall animation to fill gaps
        self.start_fall_animation()
        
        print(f"Placed {len(bomb_positions)} bombs for sequential detonation!")
    
    def handle_rocket_boardwipe_combo(self, pos, combo_tile):
        """Handle the rocket + boardwipe combo with special animation"""
        from special_tiles import create_special_tile, SpecialTileType
        from board import Tile, TileColor
        import random
        
        # Clear any existing fall animations to prevent stuck falling tiles
        self.fall_animations.clear()
        
        # Get rocket positions before removing combo tile
        rocket_positions = combo_tile.get_rocket_positions(self.board, pos)
        
        # Place rockets at selected positions (randomly choose horizontal or vertical)
        for rocket_pos in rocket_positions:
            is_horizontal = random.choice([True, False])
            rocket_type = SpecialTileType.ROCKET_HORIZONTAL if is_horizontal else SpecialTileType.ROCKET_VERTICAL
            rocket_special = create_special_tile(rocket_type, color=TileColor.RED)
            rocket_tile = Tile(TileColor.RED, special_tile=rocket_special)
            self.board.set_tile(*rocket_pos, rocket_tile)
        
        # Remove the combo tile after placing rockets
        self.board.set_tile(*pos, None)
        
        # Sort positions from top to bottom, left to right for sequential detonation
        rocket_positions.sort(key=lambda pos: (pos[0], pos[1]))
        
        # Set up animation state (reuse bomb boardwipe animation system)
        self.bomb_boardwipe_active = True
        self.bomb_boardwipe_positions = rocket_positions
        self.bomb_boardwipe_timer = 0
        self.bomb_boardwipe_detonation_timer = 0
        self.bomb_boardwipe_detonation_index = 0
        
        # Add score for the combo
        self.score += combo_tile.get_score_bonus()
        
        # Immediately start a fall animation to fill gaps
        self.start_fall_animation()
        
        print(f"Placed {len(rocket_positions)} rockets for sequential detonation!")
    
    def handle_rocket_lightning_combo(self, pos, combo_tile):
        """Handle the rocket + lightning combo with cascading row clearing"""
        # Clear any existing fall animations to prevent stuck falling tiles
        self.fall_animations.clear()
        
        # Remove the combo tile
        self.board.set_tile(*pos, None)
        
        # Get rows to clear in cascade order
        cascade_rows = combo_tile.get_cascade_rows(self.board, pos)
        
        # Set up animation state
        self.rocket_lightning_active = True
        self.rocket_lightning_rows = cascade_rows
        self.rocket_lightning_timer = 0
        self.rocket_lightning_row_index = 0
        
        # Add score for the combo
        self.score += combo_tile.get_score_bonus()
        
        # Start with the first row immediately
        self.clear_row_cascade(0)
        
        print(f"Starting rocket lightning cascade clearing {len(cascade_rows)} rows!")
    
    def handle_reality_break_combo(self, pos, combo_tile):
        """Handle the ultimate Reality Break combo - breaks the 4th wall!"""
        # Clear any existing fall animations to prevent interference
        self.fall_animations.clear()
        
        # Remove the combo tile
        self.board.set_tile(*pos, None)
        
        # Set up Reality Break animation state
        self.reality_break_active = True
        self.reality_break_timer = 0
        self.reality_break_phase = 'diagonal_lightning_1'
        self.reality_tiles_consumed = False  # Reset tile consumption flag
        
        # Add massive score for ultimate combo
        self.score += combo_tile.get_score_bonus()
        
        # Start the Reality Break sequence immediately
        self.start_diagonal_lightning_phase_1()
        
        print("REALITY BREAK INITIATED - BREAKING THE 4TH WALL!")
    
    def start_diagonal_lightning_phase_1(self):
        """Phase 1: Red diagonal lightning from top-left to bottom-right"""
        # Create massive diagonal lightning effect (red)
        self.pixel_particles.create_diagonal_lightning(
            start_x=self.board_x,
            start_y=self.board_y,
            end_x=self.board_x + self.board_width * self.tile_size,
            end_y=self.board_y + self.board_height * self.tile_size,
            color=(255, 0, 0),  # Red lightning
            thickness=8
        )
        
        # Clear tiles along the diagonal path for visual effect
        for i in range(min(self.board_height, self.board_width)):
            if i < self.board_height and i < self.board_width:
                self.board.set_tile(i, i, None)
        
        # Massive screen shake for reality breaking
        self.start_screen_shake(25.0, 0.5)  # ULTIMATE SHAKE!
        
        print("Phase 1: Red diagonal lightning breaks reality!")
    
    def clear_row_cascade(self, row_index):
        """Clear a single row in the cascade with lightning arc effect"""
        if row_index < len(self.rocket_lightning_rows):
            row = self.rocket_lightning_rows[row_index]
            
            # Determine direction (alternating left-right pattern)
            direction = 'left_to_right' if row_index % 2 == 0 else 'right_to_left'
            
            # Create lightning arc effect that blasts across the row
            board_bounds = self._get_board_bounds()
            self.pixel_particles.create_row_lightning_arc(row, direction, board_bounds)
            
            # Add dramatic screen shake for each lightning blast
            self.start_screen_shake(8.0, 0.3)  # Strong shake for 0.3 seconds
            
            # Clear entire row
            for col in range(self.board.width):
                self.board.set_tile(row, col, None)
            
            print(f"Cleared row {row} with {direction} lightning arc")
            # Don't start fall animation during cascade - wait until end
    
    def handle_board_wipe_activation(self, pos, board_wipe_tile, target_color):
        """Handle board wipe activation with target color and particles"""
        # Find all positions with the target color
        positions_to_clear = []
        for row in range(self.board.height):
            for col in range(self.board.width):
                tile = self.board.get_tile(row, col)
                if tile and not tile.is_empty() and tile.color == target_color:
                    positions_to_clear.append((row, col))
        
        if positions_to_clear:
            # Remove the board wipe tile itself first
            self.board.set_tile(*pos, None)
            
            # Create board wipe particle effect first
            center_x = self.get_tile_screen_pos(pos)[0] + self.tile_size // 2
            center_y = self.get_tile_screen_pos(pos)[1] + self.tile_size // 2
            
            # Get target positions for arc effect
            target_positions = []
            for target_pos in positions_to_clear:
                target_x = self.get_tile_screen_pos(target_pos)[0] + self.tile_size // 2
                target_y = self.get_tile_screen_pos(target_pos)[1] + self.tile_size // 2
                target_positions.append((target_x, target_y))
            
            # Create board wipe arc effect
            self.pixel_particles.create_board_wipe_arcs(center_x, center_y, target_positions, target_color)
            
            # Add dramatic screen shake for board wipe
            self.start_screen_shake(10.0, 0.6)  # Long shake for board wipe
            
            # Set up delayed clearing (0.4 seconds to let particle animation play longer)
            self.board_wipe_active = True
            self.board_wipe_positions = positions_to_clear
            self.board_wipe_timer = 0.0
            self.board_wipe_delay = 0.4
            
            # Add score
            self.score += board_wipe_tile.get_score_bonus()
            
            print(f"Board wipe targeting {target_color.name} - will clear {len(positions_to_clear)} tiles")
    
    def update_board_wipe_animation(self, dt):
        """Update the board wipe animation with delayed clearing"""
        self.board_wipe_timer += dt
        
        if self.board_wipe_timer >= self.board_wipe_delay:
            # Time to clear the tiles
            for pos in self.board_wipe_positions:
                self.board.set_tile(*pos, None)
            
            # Reset state
            self.board_wipe_active = False
            self.board_wipe_positions = []
            self.board_wipe_timer = 0.0
            
            # Start fall animation to fill gaps
            self.start_fall_animation()
            
            print("Board wipe completed!")
    
    def update_bomb_boardwipe_animation(self, dt):
        """Update the bomb boardwipe animation sequence"""
        self.bomb_boardwipe_timer += dt
        
        # Phase 1: Show bombs for 0.5 seconds
        if self.bomb_boardwipe_timer < 0.5:
            return  # Just show the bombs
        
        # Phase 2: Sequential detonation (0.1 seconds between each bomb)
        self.bomb_boardwipe_detonation_timer += dt
        
        if self.bomb_boardwipe_detonation_timer >= 0.1:  # Detonate every 0.1 seconds
            if self.bomb_boardwipe_detonation_index < len(self.bomb_boardwipe_positions):
                # Detonate the current bomb
                pos = self.bomb_boardwipe_positions[self.bomb_boardwipe_detonation_index]
                tile = self.board.get_tile(*pos)
                
                if tile and tile.is_special():
                    # Activate this bomb
                    result = self.board.activate_special_tile(*pos)
                    if isinstance(result, tuple) and len(result) == 2:
                        affected_positions, activated_tiles = result
                    else:
                        # Handle old return format for compatibility
                        affected_positions = result if result else []
                        activated_tiles = [(pos[0], pos[1], tile.special_tile)] if tile.special_tile else []
                    
                    # Create particle effects for all activated special tiles
                    for tile_row, tile_col, special_tile in activated_tiles:
                        self.create_special_effect_particles((tile_row, tile_col), special_tile)
                    
                    # Add screen shake for each bomb detonation in sequence
                    self.start_screen_shake(8.0, 0.2)  # Quick shakes for each bomb
                    
                    # Start a fall animation after each bomb to keep tiles falling
                    self.start_fall_animation()
                
                self.bomb_boardwipe_detonation_index += 1
                self.bomb_boardwipe_detonation_timer = 0
            else:
                # All bombs detonated, finish the animation
                self.bomb_boardwipe_active = False
                self.bomb_boardwipe_positions = []
                self.bomb_boardwipe_timer = 0
                self.bomb_boardwipe_detonation_timer = 0
                self.bomb_boardwipe_detonation_index = 0
                
                print("Bomb boardwipe sequence completed!")
    
    def update_rocket_lightning_animation(self, dt):
        """Update the rocket lightning cascade animation"""
        self.rocket_lightning_timer += dt
        
        # Clear next row every 0.4 seconds (slightly slower for more drama)
        if self.rocket_lightning_timer >= 0.4:
            self.rocket_lightning_row_index += 1
            
            if self.rocket_lightning_row_index < len(self.rocket_lightning_rows):
                # Clear the next row with lightning arc
                self.clear_row_cascade(self.rocket_lightning_row_index)
                self.rocket_lightning_timer = 0
            else:
                # All rows cleared, finish the animation
                self.rocket_lightning_active = False
                self.rocket_lightning_rows = []
                self.rocket_lightning_timer = 0
                self.rocket_lightning_row_index = 0
                
                # Now start fall animation to fill all the empty spaces
                self.start_fall_animation()
                
                print("Rocket lightning cascade completed!")
    
    def start_black_hole_animation(self, center_x: float, center_y: float):
        """Start black hole animation for bomb+lightning combo"""
        # Clear any existing fall animations to prevent stuck falling tiles
        self.fall_animations.clear()
        
        self.black_hole_active = True
        self.black_hole_center_x = center_x
        self.black_hole_center_y = center_y
        self.black_hole_timer = 0
        self.black_hole_phase = 'condensing'
        
        # Tile positions should already be stored before activation
        if not hasattr(self, 'original_tile_positions') or not self.original_tile_positions:
            print("Warning: No tile positions stored for black hole animation!")
            self.original_tile_positions = {}
        
        print(f"Starting black hole animation at ({center_x}, {center_y}) with {len(self.original_tile_positions)} tiles")
    
    def update_black_hole_animation(self, dt):
        """Update the black hole animation"""
        self.black_hole_timer += dt
        
        if self.black_hole_phase == 'condensing':
            # Phase 1: All tiles shrink and move toward center (1.5 seconds)
            condensing_duration = 1.5
            
            if self.black_hole_timer < condensing_duration:
                progress = self.black_hole_timer / condensing_duration
                
                # Clear the board immediately when condensing starts to hide original tiles
                if self.black_hole_timer < 0.1:  # Only on first frame
                    for row in range(self.board.height):
                        for col in range(self.board.width):
                            self.board.set_tile(row, col, None)
                
                # Update each tile's position to move toward center with easing
                for (row, col), tile_data in self.original_tile_positions.items():
                    # Calculate movement toward center with ease-in effect
                    target_x = self.black_hole_center_x
                    target_y = self.black_hole_center_y
                    
                    # Use quadratic easing for more dramatic effect
                    eased_progress = progress * progress
                    
                    # Lerp from original position to center
                    tile_data['current_x'] = tile_data['original_x'] + (target_x - tile_data['original_x']) * eased_progress
                    tile_data['current_y'] = tile_data['original_y'] + (target_y - tile_data['original_y']) * eased_progress
                    
            else:
                # Condensing complete, start explosion
                self.black_hole_phase = 'exploding'
                self.black_hole_timer = 0
                
                # NOW clear all tiles from the board (board wipe effect)
                for row in range(self.board.height):
                    for col in range(self.board.width):
                        self.board.set_tile(row, col, None)
                
                # Create massive lightning explosion
                self.pixel_particles.create_black_hole_lightning_explosion(
                    self.black_hole_center_x, self.black_hole_center_y
                )
                
                # Add massive screen shake
                self.start_screen_shake(25.0, 1.0)  # Even more intense than nuclear bomb
                
        elif self.black_hole_phase == 'exploding':
            # Phase 2: Lightning explosion plays out (2 seconds)
            explosion_duration = 2.0
            
            if self.black_hole_timer >= explosion_duration:
                # Animation complete
                self.black_hole_active = False
                self.original_tile_positions = {}
                
                # Clear any existing fall animations to prevent duplicates
                self.fall_animations.clear()
                
                # Instead of instantly filling the board, create falling tiles from the top
                # Clear the board first
                for row in range(self.board.height):
                    for col in range(self.board.width):
                        self.board.set_tile(row, col, None)
                
                # Create tiles above the board that will fall down naturally
                self.create_falling_tiles_for_empty_board()
                
                print("Black hole animation completed!")
    
    def update_reality_break_animation(self, dt):
        """Update the Reality Break animation through all phases"""
        self.reality_break_timer += dt
        
        if self.reality_break_phase == 'diagonal_lightning_1':
            # Wait 0.8 seconds then start phase 2 directly (no falling during reality break)
            if self.reality_break_timer >= 0.8:
                self.reality_break_phase = 'diagonal_lightning_2'
                self.reality_break_timer = 0
                self.start_diagonal_lightning_phase_2()
                
        elif self.reality_break_phase == 'diagonal_lightning_2':
            # Wait 0.8 seconds then start black hole phase directly (no falling during reality break)
            if self.reality_break_timer >= 0.8:
                self.reality_break_phase = 'black_hole_expand'
                self.reality_break_timer = 0
                self.start_reality_black_hole_phase()
                
        elif self.reality_break_phase == 'black_hole_expand':
            # Clear remaining tiles partway through black hole expansion (after 1.5 seconds)
            if self.reality_break_timer >= 1.5 and not getattr(self, 'reality_tiles_consumed', False):
                # Clear any remaining tiles that weren't destroyed by lightning
                for row in range(self.board.height):
                    for col in range(self.board.width):
                        self.board.set_tile(row, col, None)
                self.reality_tiles_consumed = True
                print("Black hole consumes remaining tiles!")
            
            # Black hole expands for 3 seconds total, consuming everything
            if self.reality_break_timer >= 3.0:
                self.reality_break_phase = 'singularity_collapse'
                self.reality_break_timer = 0
                self.start_singularity_collapse()
                
        elif self.reality_break_phase == 'singularity_collapse':
            # Singularity collapses in 1.0 second
            if self.reality_break_timer >= 1.0:
                self.reality_break_phase = 'complete'
                self.reality_break_timer = 0
                self.complete_reality_break()
    
    def start_diagonal_lightning_phase_2(self):
        """Phase 2: Black diagonal lightning from top-right to bottom-left"""
        # Create massive diagonal lightning effect (black)
        self.pixel_particles.create_diagonal_lightning(
            start_x=self.board_x + self.board_width * self.tile_size,
            start_y=self.board_y,
            end_x=self.board_x,
            end_y=self.board_y + self.board_height * self.tile_size,
            color=(0, 0, 0),  # Black lightning
            thickness=8
        )
        
        # Clear tiles along the opposite diagonal path for visual effect
        for i in range(min(self.board_height, self.board_width)):
            row = i
            col = (self.board_width - 1) - i
            if 0 <= row < self.board_height and 0 <= col < self.board_width:
                self.board.set_tile(row, col, None)
        
        # Another massive screen shake
        self.start_screen_shake(25.0, 0.5)
        
        print("Phase 2: Black diagonal lightning tears reality further!")
    
    def start_reality_black_hole_phase(self):
        """Phase 3: Massive black hole that consumes everything including UI"""
        # Don't clear the board immediately - let tiles be consumed visually first
        # We'll clear them partway through the black hole expansion
        
        # Set black hole parameters for maximum screen coverage
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        
        # Create the ultimate black hole effect that grows to consume the entire screen
        self.pixel_particles.create_reality_black_hole(center_x, center_y)
        
        # Ultimate screen shake as reality breaks down
        self.start_screen_shake(30.0, 2.0)  # Most intense shake for 2 seconds
        
        print("Phase 3: Reality black hole consumes everything!")
    
    def start_singularity_collapse(self):
        """Phase 4: White singularity collapse"""
        # Create white singularity effect
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        
        self.pixel_particles.create_white_singularity(center_x, center_y)
        
        # Final massive shake as reality collapses
        self.start_screen_shake(35.0, 1.0)
        
        print("Phase 4: White singularity collapses reality!")
    
    def complete_reality_break(self):
        """Complete the Reality Break animation and restore normal gameplay"""
        self.reality_break_active = False
        self.reality_break_phase = None
        
        # Clear all animations and effects
        self.fall_animations.clear()
        
        # Regenerate the board naturally with falling tiles
        self.create_falling_tiles_for_empty_board()
        
        print("REALITY RESTORED - Normal gameplay resumed!")
    
    def update_lightning_cross_animation(self, dt):
        """Update Lightning Cross sequential arc animation"""
        self.lightning_cross_timer += dt
        
        if self.lightning_cross_phase == 'arc_1':
            # Wait 0.6 seconds then start arc 2
            if self.lightning_cross_timer >= 0.6:
                self.lightning_cross_phase = 'arc_2'
                self.lightning_cross_timer = 0
                self.start_lightning_cross_arc_2()
                
        elif self.lightning_cross_phase == 'arc_2':
            # Wait 0.6 seconds then start arc 3
            if self.lightning_cross_timer >= 0.6:
                self.lightning_cross_phase = 'arc_3'
                self.lightning_cross_timer = 0
                self.start_lightning_cross_arc_3()
                
        elif self.lightning_cross_phase == 'arc_3':
            # Wait 0.6 seconds then start arc 4
            if self.lightning_cross_timer >= 0.6:
                self.lightning_cross_phase = 'arc_4'
                self.lightning_cross_timer = 0
                self.start_lightning_cross_arc_4()
                
        elif self.lightning_cross_phase == 'arc_4':
            # Wait 0.6 seconds then complete
            if self.lightning_cross_timer >= 0.6:
                self.lightning_cross_phase = 'complete'
                self.lightning_cross_timer = 0
                self.complete_lightning_cross()
    
    def create_falling_tiles_for_empty_board(self):
        """Create falling tiles to fill an empty board naturally"""
        from board import TileColor, Tile
        import random
        
        # For each column, create enough tiles to fill it
        for col in range(self.board.width):
            for row in range(self.board.height):
                # Choose a random color (same as normal tile generation)
                valid_colors = [TileColor.RED, TileColor.GREEN, TileColor.BLUE, 
                               TileColor.YELLOW, TileColor.ORANGE]
                color = random.choice(valid_colors)
                tile = Tile(color)
                
                # Calculate starting and ending positions
                start_y = self.board_y - (self.board.height - row) * self.tile_size
                end_y = self.board_y + row * self.tile_size
                
                # Calculate fall duration based on distance
                fall_distance = end_y - start_y
                fall_duration = 0.3 + (fall_distance / (self.board_height * self.tile_size)) * 0.8
                
                # Create fall animation using the correct constructor
                fall_anim = FallAnimation(start_y, end_y, fall_duration)
                fall_anim.col = col
                fall_anim.to_row = row
                fall_anim.tile = tile
                fall_anim.is_new_tile = True
                
                self.fall_animations.append(fall_anim)
    
    def start_screen_shake(self, intensity: float, duration: float):
        """Start screen shake effect for dramatic impact"""
        self.screen_shake_intensity = intensity
        self.screen_shake_duration = duration
        self.screen_shake_timer = 0
    
    def update_screen_shake(self, dt):
        """Update screen shake effect"""
        if self.screen_shake_duration > 0:
            self.screen_shake_timer += dt
            
            if self.screen_shake_timer < self.screen_shake_duration:
                # Calculate shake based on remaining time
                progress = 1.0 - (self.screen_shake_timer / self.screen_shake_duration)
                current_intensity = self.screen_shake_intensity * progress
                
                # Random shake offset
                import random
                self.screen_offset_x = random.uniform(-current_intensity, current_intensity)
                self.screen_offset_y = random.uniform(-current_intensity, current_intensity)
            else:
                # Shake finished
                self.screen_shake_duration = 0
                self.screen_offset_x = 0
                self.screen_offset_y = 0
    
    def handle_lightning_cross_combo(self, pos, combo_tile):
        """Handle Lightning Cross combo - sequential lightning arcs across the board"""
        # Clear any existing fall animations to prevent interference
        self.fall_animations.clear()
        
        # Remove the combo tile
        self.board.set_tile(*pos, None)
        
        # Set up Lightning Cross animation state
        self.lightning_cross_active = True
        self.lightning_cross_timer = 0
        self.lightning_cross_phase = 'arc_1'
        self.lightning_cross_arc_count = 0
        
        # Add massive score for lightning cross combo
        self.score += combo_tile.get_score_bonus()
        
        # Start the Lightning Cross sequence immediately
        self.start_lightning_cross_arc_1()
        
        print("LIGHTNING CROSS ACTIVATED - Arcing across the board!")
    
    def start_lightning_cross_arc_1(self):
        """Phase 1: Diagonal lightning from top-left to bottom-right"""
        # Create diagonal lightning effect (yellow/white)
        self.pixel_particles.create_diagonal_lightning(
            start_x=self.board_x,
            start_y=self.board_y,
            end_x=self.board_x + self.board_width * self.tile_size,
            end_y=self.board_y + self.board_height * self.tile_size,
            color=(255, 255, 0),  # Yellow lightning
            thickness=6
        )
        
        # Clear tiles along the diagonal path
        for i in range(min(self.board_height, self.board_width)):
            if i < self.board_height and i < self.board_width:
                self.board.set_tile(i, i, None)
        
        # Screen shake for lightning impact
        self.start_screen_shake(20.0, 0.4)
        
        print("Phase 1: Top-left to bottom-right diagonal lightning!")
    
    def start_lightning_cross_arc_2(self):
        """Phase 2: Vertical lightning from top middle to bottom middle"""
        mid_col = self.board_width // 2
        
        # Create vertical lightning effect (blue/white)
        self.pixel_particles.create_diagonal_lightning(
            start_x=self.board_x + mid_col * self.tile_size + self.tile_size // 2,
            start_y=self.board_y,
            end_x=self.board_x + mid_col * self.tile_size + self.tile_size // 2,
            end_y=self.board_y + self.board_height * self.tile_size,
            color=(100, 200, 255),  # Blue lightning
            thickness=6
        )
        
        # Clear tiles along the vertical column
        for row in range(self.board_height):
            if 0 <= mid_col < self.board_width:
                self.board.set_tile(row, mid_col, None)
        
        # Screen shake for lightning impact
        self.start_screen_shake(20.0, 0.4)
        
        print("Phase 2: Top to bottom vertical lightning!")
    
    def start_lightning_cross_arc_3(self):
        """Phase 3: Diagonal lightning from top-right to bottom-left"""
        # Create diagonal lightning effect (purple/white)
        self.pixel_particles.create_diagonal_lightning(
            start_x=self.board_x + self.board_width * self.tile_size,
            start_y=self.board_y,
            end_x=self.board_x,
            end_y=self.board_y + self.board_height * self.tile_size,
            color=(200, 100, 255),  # Purple lightning
            thickness=6
        )
        
        # Clear tiles along the opposite diagonal
        for i in range(min(self.board_height, self.board_width)):
            row = i
            col = (self.board_width - 1) - i
            if 0 <= row < self.board_height and 0 <= col < self.board_width:
                self.board.set_tile(row, col, None)
        
        # Screen shake for lightning impact
        self.start_screen_shake(20.0, 0.4)
        
        print("Phase 3: Top-right to bottom-left diagonal lightning!")
    
    def start_lightning_cross_arc_4(self):
        """Phase 4: Horizontal lightning from middle left to middle right"""
        mid_row = self.board_height // 2
        
        # Create horizontal lightning effect (red/orange)
        self.pixel_particles.create_diagonal_lightning(
            start_x=self.board_x,
            start_y=self.board_y + mid_row * self.tile_size + self.tile_size // 2,
            end_x=self.board_x + self.board_width * self.tile_size,
            end_y=self.board_y + mid_row * self.tile_size + self.tile_size // 2,
            color=(255, 150, 50),  # Orange lightning
            thickness=6
        )
        
        # Clear tiles along the horizontal row
        for col in range(self.board_width):
            if 0 <= mid_row < self.board_height:
                self.board.set_tile(mid_row, col, None)
        
        # Screen shake for lightning impact
        self.start_screen_shake(20.0, 0.4)
        
        print("Phase 4: Left to right horizontal lightning!")
    
    def complete_lightning_cross(self):
        """Complete the Lightning Cross animation and restore normal gameplay"""
        self.lightning_cross_active = False
        self.lightning_cross_phase = None
        
        # Clear all animations and effects
        self.fall_animations.clear()
        
        # Apply gravity and create falling tiles for the empty spaces
        self.start_fall_animation()
        
        print("Lightning Cross complete - Board refilling!")
    
    def are_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent (horizontally or vertically)"""
        row1, col1 = pos1
        row2, col2 = pos2
        return (abs(row1 - row2) == 1 and col1 == col2) or (abs(col1 - col2) == 1 and row1 == row2)
    
    def start_swap_animation(self, pos1, pos2):
        """Start swap animation between two tiles"""
        # Get screen positions
        screen_pos1 = self.get_tile_screen_pos(pos1)
        screen_pos2 = self.get_tile_screen_pos(pos2)
        
        # Create swap animation
        swap_anim = SwapAnimation(screen_pos1, screen_pos2, 0.3)
        swap_anim.tile_pos1 = pos1
        swap_anim.tile_pos2 = pos2
        # Store the original tiles before swapping
        swap_anim.original_tile1 = self.board.get_tile(*pos1)
        swap_anim.original_tile2 = self.board.get_tile(*pos2)
        self.swap_animations.append(swap_anim)
        
        # DON'T perform the swap yet - wait for animation to complete
    
    def get_tile_screen_pos(self, board_pos):
        """Convert board position to screen position"""
        row, col = board_pos
        x = self.board_x + col * self.tile_size + self.tile_size // 2
        y = self.board_y + row * self.tile_size + self.tile_size // 2
        return (x, y)
    
    def complete_swap_animation(self, swap_anim):
        """Complete a swap animation and check for matches"""
        pos1, pos2 = swap_anim.tile_pos1, swap_anim.tile_pos2
        
        # First, perform the actual swap on the board (unless this is a reversal)
        if not getattr(swap_anim, 'is_reversal', False):
            self.board.swap_tiles(pos1, pos2)
        
        # Check for combo tiles first
        combo_tile = self.board.check_for_combo(pos1, pos2)
        if combo_tile:
            # Create combo tile at one of the positions
            combo_pos = pos1  # Place combo at first position
            new_tile = Tile(TileColor.RED, special_tile=combo_tile)
            self.board.set_tile(*combo_pos, new_tile)
            
            # Remove the other tile
            self.board.set_tile(*pos2, None)
            
            # Check if this combo needs special handling
            if hasattr(combo_tile, 'requires_special_handling') and combo_tile.requires_special_handling:
                from special_tiles import SpecialTileType
                if combo_tile.tile_type == SpecialTileType.BOMB_BOARDWIPE:
                    self.handle_bomb_boardwipe_combo(combo_pos, combo_tile)
                elif combo_tile.tile_type == SpecialTileType.ROCKET_BOARDWIPE:
                    self.handle_rocket_boardwipe_combo(combo_pos, combo_tile)
                elif combo_tile.tile_type == SpecialTileType.ROCKET_LIGHTNING:
                    self.handle_rocket_lightning_combo(combo_pos, combo_tile)
                elif combo_tile.tile_type == SpecialTileType.REALITY_BREAK:
                    self.handle_reality_break_combo(combo_pos, combo_tile)
                return
            
            # Store tile positions BEFORE activation for black hole animation
            from special_tiles import SpecialTileType
            if combo_tile.tile_type == SpecialTileType.ENERGIZED_BOMB:
                # Store all tile positions before they get cleared
                self.original_tile_positions = {}
                for row in range(self.board.height):
                    for col in range(self.board.width):
                        tile = self.board.get_tile(row, col)
                        if tile and not tile.is_empty():
                            screen_pos = self.get_tile_screen_pos((row, col))
                            self.original_tile_positions[(row, col)] = {
                                'original_x': screen_pos[0],
                                'original_y': screen_pos[1],
                                'current_x': screen_pos[0],
                                'current_y': screen_pos[1],
                                'tile': tile
                            }
                print(f"Stored {len(self.original_tile_positions)} tiles for black hole animation")
            
            # Activate the combo tile immediately
            result = self.board.activate_special_tile(*combo_pos)
            if isinstance(result, tuple) and len(result) == 2:
                affected_positions, activated_tiles = result
            else:
                # Handle old return format for compatibility
                print(f"Warning: activate_special_tile returned unexpected format: {result}")
                affected_positions = result if result else []
                activated_tiles = [(combo_pos[0], combo_pos[1], combo_tile)] if combo_tile else []
            
            if affected_positions:
                # Create particle effects for all activated special tiles
                for tile_row, tile_col, special_tile in activated_tiles:
                    self.create_special_effect_particles((tile_row, tile_col), special_tile)
                self.score += combo_tile.get_score_bonus()
                self.start_fall_animation()
                return
        
        # Check if either tile is a special tile that should be activated
        special_activated = False
        
        tile1 = self.board.get_tile(*pos1)
        tile2 = self.board.get_tile(*pos2)
        
        # Handle board wipe special case - need target color from the swapped tile
        from special_tiles import SpecialTileType
        
        if tile1 and tile1.is_special() and tile1.special_tile.tile_type == SpecialTileType.BOARD_WIPE:
            # Board wipe targets the color of the tile it was swapped with
            target_color = tile2.color if tile2 and not tile2.is_empty() else None
            if target_color:
                self.handle_board_wipe_activation(pos1, tile1.special_tile, target_color)
                special_activated = True
        elif tile2 and tile2.is_special() and tile2.special_tile.tile_type == SpecialTileType.BOARD_WIPE:
            # Board wipe targets the color of the tile it was swapped with
            target_color = tile1.color if tile1 and not tile1.is_empty() else None
            if target_color:
                self.handle_board_wipe_activation(pos2, tile2.special_tile, target_color)
                special_activated = True
        else:
            # Handle other special tiles normally
            if tile1 and tile1.is_special():
                result = self.board.activate_special_tile(*pos1)
                if isinstance(result, tuple) and len(result) == 2:
                    affected_positions, activated_tiles = result
                else:
                    # Handle old return format for compatibility
                    affected_positions = result if result else []
                    activated_tiles = [(pos1[0], pos1[1], tile1.special_tile)] if tile1.special_tile else []
                
                if affected_positions:
                    # Create particle effects for all activated special tiles
                    for tile_row, tile_col, special_tile in activated_tiles:
                        self.create_special_effect_particles((tile_row, tile_col), special_tile)
                    self.score += tile1.special_tile.get_score_bonus()
                    special_activated = True
            
            if tile2 and tile2.is_special():
                result = self.board.activate_special_tile(*pos2)
                if isinstance(result, tuple) and len(result) == 2:
                    affected_positions, activated_tiles = result
                else:
                    # Handle old return format for compatibility
                    affected_positions = result if result else []
                    activated_tiles = [(pos2[0], pos2[1], tile2.special_tile)] if tile2.special_tile else []
                
                if affected_positions:
                    # Create particle effects for all activated special tiles
                    for tile_row, tile_col, special_tile in activated_tiles:
                        self.create_special_effect_particles((tile_row, tile_col), special_tile)
                    self.score += tile2.special_tile.get_score_bonus()
                    special_activated = True
        
        if special_activated:
            # Special tile was activated, start falling animation
            self.start_fall_animation()
            return
        
        # Check for regular matches
        matches = self.board.find_all_matches()
        
        if matches:
            # Valid move - process matches
            self.process_matches(matches)
        else:
            # Invalid move - swap back
            # Create reverse swap animation with current positions as starting points
            screen_pos1 = self.get_tile_screen_pos(pos1)
            screen_pos2 = self.get_tile_screen_pos(pos2)
            reverse_swap = SwapAnimation(screen_pos1, screen_pos2, 0.2)
            reverse_swap.tile_pos1 = pos1
            reverse_swap.tile_pos2 = pos2
            reverse_swap.is_reversal = True
            # Store the tiles that need to be shown during reversal (the swapped ones)
            reverse_swap.original_tile1 = self.board.get_tile(*pos1)
            reverse_swap.original_tile2 = self.board.get_tile(*pos2)
            self.swap_animations.append(reverse_swap)
            # Perform the reverse swap on the board
            self.board.swap_tiles(pos1, pos2)
    
    def process_matches(self, matches):
        """Process all matches found on the board"""
        # Create pop animations for matched tiles (but don't clear tiles yet)
        self.create_pop_animations_for_matches(matches)
        
        # Add score and create particle effects
        for match in matches:
            # Calculate score with combo multiplier
            match_score = match.score * self.combo_multiplier
            self.score += match_score
        
        # Store matches to clear after animation completes
        self.pending_matches = matches
        
        # Increase combo multiplier
        self.combo_multiplier += 1
        
        # Don't start falling until pop animations finish
    
    def create_pop_animations_for_matches(self, matches):
        """Create pop animations for matched tiles"""
        for match in matches:
            # Get tile positions and data for animation
            tile_positions = []
            tile_data = []
            match_color = None
            
            for row, col in match.positions:
                tile = self.board.get_tile(row, col)
                if tile and tile.color != TileColor.EMPTY:
                    x = self.board_x + col * self.tile_size
                    y = self.board_y + row * self.tile_size
                    tile_positions.append((row, col, x, y))
                    tile_data.append(tile.copy() if hasattr(tile, 'copy') else tile)  # Store copy of tile
                    if match_color is None:
                        match_color = tile.color
            
            if not tile_positions:
                continue
            
            # Check if this match will create a special tile
            special_tile_pos = self.board.get_special_tile_position(match)
            center_pos = None
            is_special = False
            
            if special_tile_pos:
                is_special = True
                center_row, center_col = special_tile_pos
                center_x = self.board_x + center_col * self.tile_size + self.tile_size // 2
                center_y = self.board_y + center_row * self.tile_size + self.tile_size // 2
                center_pos = (center_x, center_y)
            
            # Create pop animation with tile data
            pop_anim = PopAnimation(tile_positions, tile_data, center_pos)
            self.pop_animations.append(pop_anim)
            
            # Create pop particle at center of match
            if tile_positions:
                if is_special and center_pos:
                    # Special match: white particle at center position
                    pop_particle = PopParticle(center_pos[0], center_pos[1], (255, 255, 255), True)
                else:
                    # Normal match: colored particle at match center
                    avg_x = sum(pos[2] for pos in tile_positions) / len(tile_positions) + self.tile_size // 2
                    avg_y = sum(pos[3] for pos in tile_positions) / len(tile_positions) + self.tile_size // 2
                    
                    # Get color from tile color
                    color = self.get_color_from_tile_color(match_color)
                    pop_particle = PopParticle(avg_x, avg_y, color, False)
                
                self.pop_particles.append(pop_particle)
    
    def get_color_from_tile_color(self, tile_color):
        """Convert TileColor enum to RGB tuple"""
        color_map = {
            TileColor.RED: (255, 100, 100),
            TileColor.GREEN: (100, 255, 100),
            TileColor.BLUE: (100, 100, 255),
            TileColor.YELLOW: (255, 255, 100),
            TileColor.ORANGE: (255, 165, 0)
        }
        return color_map.get(tile_color, (255, 255, 255))
    
    def get_pop_animation_scale(self, row, col):
        """Get the current scale for a tile due to pop animation"""
        for pop_anim in self.pop_animations:
            for i, (tile_row, tile_col, _, _) in enumerate(pop_anim.tile_positions):
                if tile_row == row and tile_col == col:
                    return pop_anim.get_tile_scale(i)
        return 1.0  # No animation, full scale
    
    def get_pop_animation_tile(self, row, col):
        """Get the tile data from pop animation if this tile is animating"""
        for pop_anim in self.pop_animations:
            for i, (tile_row, tile_col, _, _) in enumerate(pop_anim.tile_positions):
                if tile_row == row and tile_col == col:
                    return pop_anim.tile_data[i]
        return None
    
    def get_spawn_animation_scale(self, row, col):
        """Get the current scale for a tile due to spawn animation"""
        for spawn_anim in self.spawn_animations:
            if spawn_anim.row == row and spawn_anim.col == col:
                return spawn_anim.get_scale()
        return 1.0  # No animation, full scale
    
    def create_spawn_animation(self, row, col):
        """Create a spawn animation for a special tile"""
        spawn_anim = SpawnAnimation(row, col)
        self.spawn_animations.append(spawn_anim)
    
    def create_boss_pop_animations_for_matches(self, matches):
        """Create pop animations for boss board matched tiles"""
        for match in matches:
            # Get tile positions and data for animation
            tile_positions = []
            tile_data = []
            match_color = None
            
            for row, col in match.positions:
                tile = self.boss_board.get_tile(row, col)
                if tile and tile.color != TileColor.EMPTY:
                    x = self.boss_board_x + col * self.tile_size
                    y = self.boss_board_y + row * self.tile_size
                    tile_positions.append((row, col, x, y))
                    tile_data.append(tile.copy() if hasattr(tile, 'copy') else tile)  # Store copy of tile
                    if match_color is None:
                        match_color = tile.color
            
            if not tile_positions:
                continue
            
            # Check if this match will create a special tile
            special_tile_pos = self.boss_board.get_special_tile_position(match)
            center_pos = None
            is_special = False
            
            if special_tile_pos:
                is_special = True
                center_row, center_col = special_tile_pos
                center_x = self.boss_board_x + center_col * self.tile_size + self.tile_size // 2
                center_y = self.boss_board_y + center_row * self.tile_size + self.tile_size // 2
                center_pos = (center_x, center_y)
            
            # Create pop animation with tile data
            pop_anim = PopAnimation(tile_positions, tile_data, center_pos)
            self.boss_pop_animations.append(pop_anim)
            
            # Create pop particle at center of match
            if tile_positions:
                if is_special and center_pos:
                    # Special match: white particle at center position
                    pop_particle = PopParticle(center_pos[0], center_pos[1], (255, 255, 255), True)
                else:
                    # Normal match: colored particle at match center
                    avg_x = sum(pos[2] for pos in tile_positions) / len(tile_positions) + self.tile_size // 2
                    avg_y = sum(pos[3] for pos in tile_positions) / len(tile_positions) + self.tile_size // 2
                    
                    # Get color from tile color
                    color = self.get_color_from_tile_color(match_color)
                    pop_particle = PopParticle(avg_x, avg_y, color, False)
                
                self.boss_pop_particles.append(pop_particle)
    
    def get_boss_pop_animation_scale(self, row, col):
        """Get the current scale for a boss tile due to pop animation"""
        for pop_anim in self.boss_pop_animations:
            for i, (tile_row, tile_col, _, _) in enumerate(pop_anim.tile_positions):
                if tile_row == row and tile_col == col:
                    return pop_anim.get_tile_scale(i)
        return 1.0  # No animation, full scale
    
    def get_boss_pop_animation_tile(self, row, col):
        """Get the tile data from boss pop animation if this tile is animating"""
        for pop_anim in self.boss_pop_animations:
            for i, (tile_row, tile_col, _, _) in enumerate(pop_anim.tile_positions):
                if tile_row == row and tile_col == col:
                    return pop_anim.tile_data[i]
        return None
    
    def get_boss_spawn_animation_scale(self, row, col):
        """Get the current scale for a boss tile due to spawn animation"""
        for spawn_anim in self.boss_spawn_animations:
            if spawn_anim.row == row and spawn_anim.col == col:
                return spawn_anim.get_scale()
        return 1.0  # No animation, full scale
    
    def create_boss_spawn_animation(self, row, col):
        """Create a spawn animation for a boss special tile"""
        spawn_anim = SpawnAnimation(row, col)
        self.boss_spawn_animations.append(spawn_anim)
    
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
                    fall_anim.from_row = tile_data['from_row']
                    fall_anim.to_row = tile_data['to_row']
                    fall_anim.tile = tile_data['tile']
                    fall_anim.is_existing_tile = True
                    self.fall_animations.append(fall_anim)
        
        # During Reality Break, don't fill empty spaces with new tiles
        if not hasattr(self, 'reality_break_phase') or self.reality_break_phase is None:
            # Create fall animations for new tiles BEFORE placing them on board
            self.create_new_tile_animations_improved()
            
            # Don't fill board with new tiles - they'll be placed when animations complete
    
    def create_new_tile_animations_improved(self):
        """Create fall animations for new tiles - tiles exist ONLY in animations until completion"""
        import random
        from board import Tile
        
        for col in range(self.board_width):
            # Find empty positions that need new tiles
            empty_positions = []
            for row in range(self.board_height):
                if self.board.get_tile(row, col) is None:
                    empty_positions.append(row)
            
            if not empty_positions:
                continue
                
            # Remove existing tiles from board that will be animated
            existing_tiles = []
            for row in range(self.board_height):
                tile = self.board.get_tile(row, col)
                if tile is not None:
                    existing_tiles.append((row, tile))
                    self.board.set_tile(row, col, None)  # Remove from board during animation
            
            # Create animations for existing tiles falling down
            shift_amount = len(empty_positions)
            for old_row, tile in existing_tiles:
                new_row = old_row + shift_amount
                if new_row < self.board_height:  # Make sure it stays on the board
                    start_y = self.board_y + old_row * self.tile_size
                    end_y = self.board_y + new_row * self.tile_size
                    fall_distance = end_y - start_y
                    fall_duration = 0.3 + (fall_distance / (self.board_height * self.tile_size)) * 0.8
                    
                    fall_anim = FallAnimation(start_y, end_y, fall_duration)
                    fall_anim.col = col
                    fall_anim.from_row = old_row
                    fall_anim.to_row = new_row
                    fall_anim.tile = tile
                    fall_anim.is_new_tile = False
                    self.fall_animations.append(fall_anim)
            
            # Create animations for new tiles, stacking them properly above the board
            for i, row in enumerate(empty_positions):
                # Create a new tile
                color = random.choice(self.board.available_colors)
                tile = Tile(color)
                
                # Stack new tiles above the board in reverse order
                stack_position = len(empty_positions) - i
                start_y = self.board_y - stack_position * self.tile_size
                end_y = self.board_y + row * self.tile_size
                
                # Calculate fall duration based on distance
                fall_distance = end_y - start_y
                fall_duration = 0.3 + (fall_distance / (self.board_height * self.tile_size)) * 0.8
                
                fall_anim = FallAnimation(start_y, end_y, fall_duration)
                fall_anim.col = col
                fall_anim.to_row = row
                fall_anim.tile = tile
                fall_anim.is_new_tile = True
                self.fall_animations.append(fall_anim)

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
        # Re-fill any empty spaces that still exist (fallback safety)
        self.board.fill_empty_spaces()
        
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
    
    def create_special_effect_particles(self, pos, special_tile, boss_board=False):
        """Create particle effects for special tile activation"""
        if boss_board:
            screen_pos = self.get_boss_tile_screen_pos(pos)
        else:
            screen_pos = self.get_tile_screen_pos(pos)
        visual_data = special_tile.get_visual_representation()
        effect_color = visual_data.get('effect_color', (255, 255, 255))
        
        # Check if it's a bomb and create pixel explosion effect
        if special_tile.tile_type == SpecialTileType.BOMB:
            # Create pixel art explosion for regular bombs (not in combos)
            center_x = screen_pos[0] + self.tile_size // 2
            center_y = screen_pos[1] + self.tile_size // 2
            self.pixel_particles.create_bomb_explosion(center_x, center_y)
            # Add dramatic screen shake for bomb explosions
            self.start_screen_shake(12.0, 0.4)  # Strong shake for bombs
        
        # Check if it's a rocket and create rocket trail effect
        elif special_tile.tile_type in [SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.ROCKET_VERTICAL]:
            # Get appropriate board bounds for clipping
            if boss_board:
                board_bounds = self._get_boss_board_bounds()
                board_x, board_y = self.boss_board_x, self.boss_board_y
            else:
                board_bounds = self._get_board_bounds()
                board_x, board_y = self.board_x, self.board_y
            
            if special_tile.tile_type == SpecialTileType.ROCKET_HORIZONTAL:
                # For horizontal rockets, use row center and middle of board for Y
                row, col = pos
                center_x = screen_pos[0] + self.tile_size // 2
                # Center the horizontal rocket on the exact middle of the row
                center_y = board_y + (row * self.tile_size) + (self.tile_size // 2)
                self.pixel_particles.create_rocket_trail(center_x, center_y, 'horizontal', board_bounds)
            else:
                # For vertical rockets, use column center and middle of board for X
                row, col = pos
                # Center the vertical rocket on the exact middle of the column
                center_x = board_x + (col * self.tile_size) + (self.tile_size // 2)
                center_y = screen_pos[1] + self.tile_size // 2
                self.pixel_particles.create_rocket_trail(center_x, center_y, 'vertical', board_bounds)
        
        # Check if it's a simple cross (rocket combo) and create cross trail effect
        elif special_tile.tile_type == SpecialTileType.SIMPLE_CROSS:
            # Create cross pattern (both horizontal and vertical) - properly centered
            if boss_board:
                board_bounds = self._get_boss_board_bounds()
                board_x, board_y = self.boss_board_x, self.boss_board_y
            else:
                board_bounds = self._get_board_bounds()
                board_x, board_y = self.board_x, self.board_y
            
            row, col = pos
            # Use same centering logic as individual rockets
            center_x = board_x + (col * self.tile_size) + (self.tile_size // 2)
            center_y = board_y + (row * self.tile_size) + (self.tile_size // 2)
            self.pixel_particles.create_rocket_trail(center_x, center_y, 'cross', board_bounds)
        
        # Check if it's a lightning cross combo and create sequential lightning arcs
        elif special_tile.tile_type == SpecialTileType.LIGHTNING_CROSS:
            self.handle_lightning_cross_combo(pos, special_tile)
            return  # Special handling, no normal board clearing
        
        # Check if it's a bomb+rocket combo and create large bomb-colored cross trail
        elif special_tile.tile_type == SpecialTileType.BOMB_ROCKET:
            # Create large cross pattern with bomb explosion colors (3-wide cross)
            if boss_board:
                board_bounds = self._get_boss_board_bounds()
                board_x, board_y = self.boss_board_x, self.boss_board_y
            else:
                board_bounds = self._get_board_bounds()
                board_x, board_y = self.board_x, self.board_y
            
            row, col = pos
            # Use same centering logic as individual rockets
            center_x = board_x + (col * self.tile_size) + (self.tile_size // 2)
            center_y = board_y + (row * self.tile_size) + (self.tile_size // 2)
            self.pixel_particles.create_bomb_rocket_trail(center_x, center_y, board_bounds)
            # Add massive screen shake for bomb+rocket combo (most powerful)
            self.start_screen_shake(15.0, 0.5)  # Strongest shake for ultimate combo
        
        # Check if it's a lightning and create lightning arc effect
        elif special_tile.tile_type == SpecialTileType.LIGHTNING:
            # Create dramatic lightning arc effect
            center_x = screen_pos[0] + self.tile_size // 2
            center_y = screen_pos[1] + self.tile_size // 2
            self.pixel_particles.create_lightning_arc(center_x, center_y)
            # Add electric screen shake for lightning bolts
            self.start_screen_shake(6.0, 0.25)  # Medium shake for lightning
        
        # Check if it's a mega bomb (bomb+bomb combo) and create nuclear explosion
        elif special_tile.tile_type == SpecialTileType.MEGA_BOMB:
            # Create nuclear-style megabomb explosion
            center_x = screen_pos[0] + self.tile_size // 2
            center_y = screen_pos[1] + self.tile_size // 2
            self.pixel_particles.create_nuclear_megabomb(center_x, center_y)
            # Add MASSIVE screen shake for nuclear megabomb (most intense)
            self.start_screen_shake(20.0, 0.8)  # ULTIMATE shake for nuclear bomb!
        
        # Check if it's an energized bomb (bomb+lightning combo) and create black hole effect
        elif special_tile.tile_type == SpecialTileType.ENERGIZED_BOMB:
            # Start black hole animation
            center_x = screen_pos[0] + self.tile_size // 2
            center_y = screen_pos[1] + self.tile_size // 2
            self.start_black_hole_animation(center_x, center_y)
        
        # Skip old particle effects - pixel particles are much more dramatic
    
    def _get_board_bounds(self):
        """Get the board rendering bounds for particle clipping"""
        # Calculate the actual board area bounds
        left = self.board_x
        top = self.board_y
        right = self.board_x + (self.board.width * self.tile_size)
        bottom = self.board_y + (self.board.height * self.tile_size)
        return (left, top, right, bottom)
    
    def _get_boss_board_bounds(self):
        """Get the boss board rendering bounds for particle clipping"""
        # Calculate the actual boss board area bounds
        left = self.boss_board_x
        top = self.boss_board_y
        right = self.boss_board_x + (self.boss_board.width * self.tile_size)
        bottom = self.boss_board_y + (self.boss_board.height * self.tile_size)
        return (left, top, right, bottom)
    
    def update(self, dt):
        """Update game state"""
        # Update bomb boardwipe animation
        if self.bomb_boardwipe_active:
            self.update_bomb_boardwipe_animation(dt)
            # Continue with other animations (especially fall animations)
        
        # Update board wipe animation
        if self.board_wipe_active:
            self.update_board_wipe_animation(dt)
        
        # Update rocket lightning animation
        if self.rocket_lightning_active:
            self.update_rocket_lightning_animation(dt)
            # Don't return early - let particle system update
        
        # Update screen shake
        self.update_screen_shake(dt)
        
        # Update boss board combo animations
        if self.boss_bomb_boardwipe_active:
            self.update_boss_bomb_boardwipe_animation(dt)
        
        if self.boss_rocket_lightning_active:
            self.update_boss_rocket_lightning_animation(dt)
        
        if self.boss_reality_break_active:
            self.update_boss_reality_break_animation(dt)
        
        # Update black hole animation
        if self.black_hole_active:
            self.update_black_hole_animation(dt)
        
        # Update reality break animation
        if hasattr(self, 'reality_break_active') and self.reality_break_active:
            self.update_reality_break_animation(dt)
        
        # Update lightning cross animation
        if hasattr(self, 'lightning_cross_active') and self.lightning_cross_active:
            self.update_lightning_cross_animation(dt)
        
        # Update swap animations (skip during special effects)
        if (not self.rocket_lightning_active and not self.black_hole_active and 
            not (hasattr(self, 'reality_break_active') and self.reality_break_active) and
            not (hasattr(self, 'lightning_cross_active') and self.lightning_cross_active)):
            for swap_anim in self.swap_animations[:]:
                if swap_anim.update(dt):
                    # Animation completed
                    self.swap_animations.remove(swap_anim)
                    
                    if not hasattr(swap_anim, 'is_reversal'):
                        # Check for matches (not for reversals)
                        self.complete_swap_animation(swap_anim)
        
        # Update fall animations (skip during rocket lightning and black hole)
        if not self.rocket_lightning_active and not self.black_hole_active:
            completed_fall_animations = []
            for fall_anim in self.fall_animations[:]:
                if fall_anim.update(dt):
                    # For new tiles, only place on board when removing animation
                    # For existing tiles, place immediately but add delay before removal  
                    if hasattr(fall_anim, 'is_new_tile') and fall_anim.is_new_tile:
                        # New tiles - place on board and remove immediately
                        if hasattr(fall_anim, 'tile') and hasattr(fall_anim, 'to_row') and hasattr(fall_anim, 'col'):
                            self.board.set_tile(fall_anim.to_row, fall_anim.col, fall_anim.tile)
                        completed_fall_animations.append(fall_anim)
                        self.fall_animations.remove(fall_anim)
                    else:
                        # Existing tiles - place on board immediately but delay removal
                        if hasattr(fall_anim, 'tile') and hasattr(fall_anim, 'to_row') and hasattr(fall_anim, 'col'):
                            self.board.set_tile(fall_anim.to_row, fall_anim.col, fall_anim.tile)
                        
                        # Add delay before removal
                        if not hasattr(fall_anim, 'completion_delay'):
                            fall_anim.completion_delay = 0.05  # 50ms delay
                            fall_anim.delay_elapsed = 0.0
                        
                        fall_anim.delay_elapsed += dt
                        if fall_anim.delay_elapsed >= fall_anim.completion_delay:
                            completed_fall_animations.append(fall_anim)
                            self.fall_animations.remove(fall_anim)
            
            # Check if all fall animations are complete and we need to check for new matches  
            if completed_fall_animations and not self.fall_animations:
                # All falling is done, check for new matches
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
        
        # Update pop animations
        for pop_anim in self.pop_animations[:]:
            if pop_anim.update(dt):
                self.pop_animations.remove(pop_anim)
        
        # If all pop animations are done and we have pending matches, clear them and start falling
        if not self.pop_animations and hasattr(self, 'pending_matches') and self.pending_matches:
            # Check for special tiles that will be created and trigger spawn animations
            special_tile_positions = []
            for match in self.pending_matches:
                special_tile_pos = self.board.get_special_tile_position(match)
                if special_tile_pos:
                    special_tile_positions.append(special_tile_pos)
            
            # Clear matches (which creates special tiles)
            for match in self.pending_matches:
                self.board.clear_matches(match)
            
            # Create spawn animations for special tiles
            for row, col in special_tile_positions:
                self.create_spawn_animation(row, col)
            
            self.pending_matches = None
            self.start_fall_animation()
        
        # Update pop particles
        for pop_particle in self.pop_particles[:]:
            pop_particle.update(dt)
            if pop_particle.is_finished():
                self.pop_particles.remove(pop_particle)
        
        # Update spawn animations
        for spawn_anim in self.spawn_animations[:]:
            if spawn_anim.update(dt):
                self.spawn_animations.remove(spawn_anim)
        
        # Update boss pop animations
        for pop_anim in self.boss_pop_animations[:]:
            if pop_anim.update(dt):
                self.boss_pop_animations.remove(pop_anim)
        
        # If all boss pop animations are done and we have pending matches, clear them and apply gravity
        if not self.boss_pop_animations and hasattr(self, 'pending_boss_matches') and self.pending_boss_matches:
            # Check for special tiles that will be created and trigger spawn animations
            special_tile_positions = []
            for match in self.pending_boss_matches:
                special_tile_pos = self.boss_board.get_special_tile_position(match)
                if special_tile_pos:
                    special_tile_positions.append(special_tile_pos)
            
            # Clear matches (which creates special tiles)
            for match in self.pending_boss_matches:
                self.boss_board.clear_matches(match)
            
            # Create spawn animations for special tiles
            for row, col in special_tile_positions:
                self.create_boss_spawn_animation(row, col)
            
            self.pending_boss_matches = None
            self.apply_boss_board_gravity()
        
        # Update boss pop particles
        for pop_particle in self.boss_pop_particles[:]:
            pop_particle.update(dt)
            if pop_particle.is_finished():
                self.boss_pop_particles.remove(pop_particle)
        
        # Update boss spawn animations
        for spawn_anim in self.boss_spawn_animations[:]:
            if spawn_anim.update(dt):
                self.boss_spawn_animations.remove(spawn_anim)
        
        # Update pixel particle system
        self.pixel_particles.update(dt)
        
        # Update boss swap animations
        if (not self.rocket_lightning_active and not self.black_hole_active and 
            not (hasattr(self, 'reality_break_active') and self.reality_break_active) and
            not (hasattr(self, 'lightning_cross_active') and self.lightning_cross_active)):
            for swap_anim in self.boss_swap_animations[:]:
                if swap_anim.update(dt):
                    # Animation completed
                    self.boss_swap_animations.remove(swap_anim)
                    self.complete_boss_swap_animation(swap_anim)
        
        # Update boss fall animations (simplified for performance)
        if not self.rocket_lightning_active and not self.black_hole_active:
            completed_count = 0
            for fall_anim in self.boss_fall_animations[:]:
                if fall_anim.update(dt):
                    # Animation completed - ensure tile is properly placed on boss board
                    if hasattr(fall_anim, 'tile') and hasattr(fall_anim, 'to_row') and hasattr(fall_anim, 'col'):
                        self.boss_board.set_tile(fall_anim.to_row, fall_anim.col, fall_anim.tile)
                    
                    self.boss_fall_animations.remove(fall_anim)
                    completed_count += 1
            
            # Check if all boss fall animations are complete
            if completed_count > 0 and not self.boss_fall_animations:
                # All boss falling is done, check for cascade matches
                self.complete_boss_fall_animation()

        # Update boss AI delay timer
        if self.boss_move_delay > 0:
            self.boss_move_delay -= dt
        
        # Update AI for boss board
        if (self.boss_ai and not self.animating and not self.boss_animating and 
            self.boss_move_delay <= 0):
            self.update_boss_ai()
    
    def draw(self):
        """Draw the entire game"""
        # Apply screen shake offset by temporarily adjusting board position
        original_board_x = self.board_x
        original_board_y = self.board_y
        original_boss_board_x = self.boss_board_x
        original_boss_board_y = self.boss_board_y
        
        self.board_x += int(self.screen_offset_x)
        self.board_y += int(self.screen_offset_y)
        self.boss_board_x += int(self.screen_offset_x)
        self.boss_board_y += int(self.screen_offset_y)
        
        self.screen.fill(BACKGROUND_COLOR)
        
        if self.level_config.dual_board:
            # Draw dual board layout
            self.draw_dual_boards()
        else:
            # Draw single board layout
            # Draw the border behind everything if available
            self.draw_border()
            
            # Set up clipping area for the game board
            board_area = pygame.Rect(self.board_x, self.board_y, 
                                    self.board_width * self.tile_size, 
                                    self.board_height * self.tile_size)
            
            # Draw the board with clipping
            old_clip = self.screen.get_clip()
            self.screen.set_clip(board_area)
            self.draw_board()
            self.screen.set_clip(old_clip)
        
        # Draw particle effects (affected by shake)
        self.pixel_particles.draw(self.screen)
        
        # Restore original board positions
        self.board_x = original_board_x
        self.board_y = original_board_y
        self.boss_board_x = original_boss_board_x
        self.boss_board_y = original_boss_board_y
        
        # Draw UI elements (outside the clipped area, not affected by shake)
        self.draw_ui()
        
        # Draw debug overlay if in debug mode
        if self.debug_mode:
            self.draw_debug_overlay()
        
        pygame.display.flip()
    
    def draw_border(self):
        """Draw the border around the game area"""
        if self.sprite_manager.has_border_sprite():
            # Calculate border dimensions (much larger than board area)
            border_padding = 120  # Extra space around the board
            border_width = self.board_width * self.tile_size + (border_padding * 2)
            border_height = self.board_height * self.tile_size + (border_padding * 2)
            
            border_sprite = self.sprite_manager.get_border_sprite(border_width, border_height)
            if border_sprite:
                # Center the border around the board
                border_x = self.board_x - border_padding
                border_y = self.board_y - border_padding
                self.screen.blit(border_sprite, (border_x, border_y))
    
    def draw_board(self):
        """Draw the game board and tiles"""
        # Skip drawing normal tiles during black hole animation
        if not (self.black_hole_active and self.black_hole_phase == 'condensing'):
            # Draw static tiles (not involved in animations)
            for row in range(self.board_height):
                for col in range(self.board_width):
                    # Skip tiles that are currently animating
                    if self.is_tile_animating(row, col):
                        continue
                    
                    self.draw_tile_at_position(row, col, row, col)
        
        # Draw falling tiles (skip during black hole)
        if not self.black_hole_active:
            for fall_anim in self.fall_animations:
                # Calculate current position
                current_row = (fall_anim.current_y - self.board_y) / self.tile_size
                self.draw_animated_tile(fall_anim.tile, fall_anim.col, current_row)
        
        # Draw swapping tiles (skip during black hole)
        if not self.black_hole_active:
            for swap_anim in self.swap_animations:
                # Use the original tiles stored in the animation (before any swap)
                tile1 = getattr(swap_anim, 'original_tile1', self.board.get_tile(*swap_anim.tile_pos1))
                tile2 = getattr(swap_anim, 'original_tile2', self.board.get_tile(*swap_anim.tile_pos2))
                
                if tile1:
                    self.draw_animated_tile_at_screen_pos(tile1, swap_anim.current_pos1)
                if tile2:
                    self.draw_animated_tile_at_screen_pos(tile2, swap_anim.current_pos2)
        
        # Draw black hole condensing tiles
        if self.black_hole_active and self.black_hole_phase == 'condensing':
            for (row, col), tile_data in self.original_tile_positions.items():
                # Calculate scale based on distance to center and animation progress
                distance_to_center = ((tile_data['current_x'] - self.black_hole_center_x) ** 2 + 
                                    (tile_data['current_y'] - self.black_hole_center_y) ** 2) ** 0.5
                max_distance = 300  # Approximate max distance from center
                # Scale based on distance: far away = full size (1.0), close to center = tiny (0.1)
                distance_factor = min(1.0, distance_to_center / max_distance)
                scale = max(0.1, 0.1 + distance_factor * 0.9)  # Scale from 0.1 to 1.0 based on distance
                
                # Draw tile at current animated position with scaling
                self.draw_black_hole_tile(tile_data['tile'], tile_data['current_x'], tile_data['current_y'], scale)
    
    def draw_black_hole_tile(self, tile, center_x, center_y, scale):
        """Draw a tile during black hole condensation with scaling using actual tile sprites"""
        if not tile or tile.is_empty():
            return
            
        # Calculate scaled size
        scaled_size = int(self.tile_size * scale)
        if scaled_size <= 0:
            return
            
        from board import TileColor
            
        # Get the appropriate sprite for this tile
        sprite_surface = None
        
        if tile.is_special():
            # For special tiles, try to get their sprite
            visual_data = tile.special_tile.get_visual_representation()
            sprite_type = visual_data.get('sprite_type')
            if sprite_type and self.sprite_manager.has_special_sprite(sprite_type):
                sprite_surface = self.sprite_manager.get_special_sprite(sprite_type, scaled_size)
        
        # If no special sprite, use regular tile sprite
        if sprite_surface is None:
            # Map tile colors to filenames
            tile_filenames = {
                TileColor.RED: "redtile.png",
                TileColor.GREEN: "greentile.png", 
                TileColor.BLUE: "bluetile.png",
                TileColor.YELLOW: "yellowtile.png",
                TileColor.ORANGE: "orangetile.png"
            }
            
            tile_filename = tile_filenames.get(tile.color)
            if tile_filename:
                # Load and scale the tile image with crisp scaling (no smoothing)
                try:
                    original_sprite = pygame.image.load(f"sprites/tiles/{tile_filename}").convert_alpha()
                    # Use pygame.transform.scale instead of smoothscale for crisp pixels
                    sprite_surface = pygame.transform.scale(original_sprite, (scaled_size, scaled_size))
                except Exception as e:
                    print(f"Failed to load sprite {tile_filename}: {e}")
                    # Fallback to colored rectangle if sprite loading fails
                    sprite_surface = pygame.Surface((scaled_size, scaled_size))
                    sprite_surface.fill(tile.color.value)
            else:
                print(f"No filename mapping found for color: {tile.color}")
                # Fallback to colored rectangle
                sprite_surface = pygame.Surface((scaled_size, scaled_size))
                sprite_surface.fill(tile.color.value)
        
        # Draw the sprite centered at the current position
        if sprite_surface:
            sprite_rect = sprite_surface.get_rect(center=(center_x, center_y))
            self.screen.blit(sprite_surface, sprite_rect)
        else:
            # Ultimate fallback - draw colored rectangle
            print(f"No sprite available for tile {tile.color}, using colored rectangle")
            rect = pygame.Rect(center_x - scaled_size // 2, center_y - scaled_size // 2, scaled_size, scaled_size)
            pygame.draw.rect(self.screen, tile.color.value, rect)
    
    def is_tile_animating(self, row, col):
        """Check if a tile is currently involved in any animation"""
        # During black hole condensing, all tiles are being animated
        if self.black_hole_active and self.black_hole_phase == 'condensing':
            return True
            
        # Check if involved in swap animation
        for swap_anim in self.swap_animations:
            if (row, col) in [swap_anim.tile_pos1, swap_anim.tile_pos2]:
                return True
        
        # Check if this position is affected by falling tiles in the same column
        return self.is_column_affected_by_falling(col, row)
    
    def is_column_affected_by_falling(self, col, max_row=None):
        """Check if a column (or specific row in column) is affected by falling tiles"""
        for fall_anim in self.fall_animations:
            if fall_anim.col == col:
                if max_row is None:
                    return True
                # Check if there's a tile that originally came from this position OR is falling to this position
                # This handles both existing tiles moving and new tiles falling
                if hasattr(fall_anim, 'from_row'):
                    # Existing tile moving from one position to another
                    if fall_anim.from_row == max_row or fall_anim.to_row == max_row:
                        return True
                else:
                    # New tile falling to a position (no from_row)
                    if fall_anim.to_row == max_row:
                        return True
        return False
    
    def draw_tile_at_position(self, tile_row, tile_col, draw_row, draw_col):
        """Draw a tile at a specific board position"""
        # Check for pop animation scaling
        scale = self.get_pop_animation_scale(tile_row, tile_col)
        
        # Also check for spawn animation scaling (spawn takes priority if both exist)
        spawn_scale = self.get_spawn_animation_scale(tile_row, tile_col)
        if spawn_scale != 1.0:
            scale = spawn_scale
        
        # Calculate tile position with spacing
        spacing = 2  # Small gap between tiles
        base_x = self.board_x + draw_col * self.tile_size + spacing
        base_y = self.board_y + draw_row * self.tile_size + spacing
        
        # Apply scaling for pop animation
        tile_size_with_spacing = self.tile_size - (spacing * 2)
        scaled_size = int(tile_size_with_spacing * scale)
        
        # Center the scaled tile
        offset = (tile_size_with_spacing - scaled_size) // 2
        x = base_x + offset
        y = base_y + offset
        
        # Skip drawing if tile is too small (popped)
        if scaled_size < 2:
            return
            
        tile_rect = pygame.Rect(x, y, scaled_size, scaled_size)
        
        # Get tile color - check if it's animating first
        tile = self.get_pop_animation_tile(tile_row, tile_col)
        if tile is None:
            tile = self.board.get_tile(tile_row, tile_col)
        if tile:
            # Check if it's a special tile
            if tile.is_special():
                visual_data = tile.special_tile.get_visual_representation()
                
                # Try to use special tile sprite first, fallback to text rendering
                sprite_type = visual_data.get('sprite_type')
                if sprite_type and self.sprite_manager.has_special_sprite(sprite_type):
                    sprite = self.sprite_manager.get_special_sprite(sprite_type, scaled_size)
                    self.screen.blit(sprite, (x, y))
                    # No border for sprites - they should be self-contained
                else:
                    # Fallback to text rendering
                    bg_color = visual_data.get('background_color', tile.color.value)
                    self.draw_rounded_rect(self.screen, bg_color, tile_rect, 8)
                    
                    # Draw special tile symbol
                    symbol = visual_data.get('symbol', '?')
                    symbol_color = visual_data.get('color', (255, 255, 255))
                    
                    # Create font for symbol - make it bigger and bolder
                    font_size = max(scaled_size // 2, 12)  # Bigger font, scaled
                    font = pygame.font.Font(None, font_size)
                    symbol_surface = font.render(symbol, True, symbol_color)
                    
                    # Center the symbol
                    symbol_rect = symbol_surface.get_rect(center=(x + scaled_size // 2, y + scaled_size // 2))
                    self.screen.blit(symbol_surface, symbol_rect)
                    
                    # Add a glowing border for text-based special tiles only
                    pygame.draw.rect(self.screen, visual_data.get('effect_color', (255, 255, 255)), tile_rect, 3)
            else:
                # Regular tile - try to use sprite first, fallback to color
                sprite = self.sprite_manager.get_tile_sprite(tile.color, scaled_size)
                if sprite:
                    # Sprite is 5 pixels bigger than tile, so center it by offsetting by -2 (scaled)
                    sprite_offset = int(-2 * scale)
                    sprite_x = x + sprite_offset
                    sprite_y = y + sprite_offset
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                else:
                    # Fallback to colored rectangle
                    color = tile.color.value
                    self.draw_rounded_rect(self.screen, color, tile_rect, 8)
        else:
            # Don't render anything for empty tiles during special effects
            if not self.rocket_lightning_active and not getattr(self, 'reality_break_active', False):
                color = TileColor.EMPTY.value
                self.draw_rounded_rect(self.screen, color, tile_rect, 8)
        
        # Highlight selected tile
        if self.selected_tile == (tile_row, tile_col):
            pygame.draw.rect(self.screen, SELECTED_COLOR, tile_rect, 4)
        
        # Dim tiles that are currently animating (can't be selected)
        if self.is_tile_animating(tile_row, tile_col):
            dim_overlay = pygame.Surface((self.tile_size, self.tile_size))
            dim_overlay.set_alpha(100)
            dim_overlay.fill((0, 0, 0))
            self.screen.blit(dim_overlay, (x, y))
    
    def draw_animated_tile(self, tile, col, row_float):
        """Draw a tile at a floating-point row position"""
        spacing = 2  # Small gap between tiles
        x = self.board_x + col * self.tile_size + spacing
        y = self.board_y + row_float * self.tile_size + spacing
        
        tile_size_with_spacing = self.tile_size - (spacing * 2)
        tile_rect = pygame.Rect(x, y, tile_size_with_spacing, tile_size_with_spacing)
        
        if tile:
            if tile.is_special():
                visual_data = tile.special_tile.get_visual_representation()
                
                # Try to use special tile sprite first, fallback to text rendering
                sprite_type = visual_data.get('sprite_type')
                if sprite_type and self.sprite_manager.has_special_sprite(sprite_type):
                    sprite = self.sprite_manager.get_special_sprite(sprite_type, tile_size_with_spacing)
                    self.screen.blit(sprite, (x, y))
                else:
                    # Fallback to text rendering
                    bg_color = visual_data.get('background_color', tile.color.value)
                    self.draw_rounded_rect(self.screen, bg_color, tile_rect, 8)
                    
                    # Draw special tile symbol
                    symbol = visual_data.get('symbol', '?')
                    symbol_color = visual_data.get('color', (255, 255, 255))
                    
                    font_size = max(tile_size_with_spacing // 2, 24)  # Bigger font
                    font = pygame.font.Font(None, font_size)
                    symbol_surface = font.render(symbol, True, symbol_color)
                    
                    symbol_rect = symbol_surface.get_rect(center=(x + tile_size_with_spacing // 2, y + tile_size_with_spacing // 2))
                    self.screen.blit(symbol_surface, symbol_rect)
                    
                    # Add a glowing border for text-based special tiles only
                    pygame.draw.rect(self.screen, visual_data.get('effect_color', (255, 255, 255)), tile_rect, 3)
            else:
                # Regular tile - try to use sprite first, fallback to color
                sprite = self.sprite_manager.get_tile_sprite(tile.color, tile_size_with_spacing)
                if sprite:
                    # Sprite is 5 pixels bigger than tile, so center it by offsetting by -2
                    sprite_x = x - 2
                    sprite_y = y - 2
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                else:
                    color = tile.color.value
                    self.draw_rounded_rect(self.screen, color, tile_rect, 8)
    
    def draw_animated_tile_at_screen_pos(self, tile, screen_pos):
        """Draw a tile at a specific screen position"""
        spacing = 2  # Small gap between tiles
        x, y = screen_pos
        x -= self.tile_size // 2
        y -= self.tile_size // 2
        
        # Apply spacing to animated tiles too
        x += spacing
        y += spacing
        tile_size_with_spacing = self.tile_size - (spacing * 2)
        tile_rect = pygame.Rect(x, y, tile_size_with_spacing, tile_size_with_spacing)
        
        if tile:
            if tile.is_special():
                visual_data = tile.special_tile.get_visual_representation()
                
                # Try to use special tile sprite first, fallback to text rendering
                sprite_type = visual_data.get('sprite_type')
                if sprite_type and self.sprite_manager.has_special_sprite(sprite_type):
                    sprite = self.sprite_manager.get_special_sprite(sprite_type, tile_size_with_spacing)
                    self.screen.blit(sprite, (x, y))
                    # No border for sprites - they should be self-contained
                else:
                    # Fallback to text rendering
                    bg_color = visual_data.get('background_color', tile.color.value)
                    self.draw_rounded_rect(self.screen, bg_color, tile_rect, 8)
                    
                    # Draw special tile symbol
                    symbol = visual_data.get('symbol', '?')
                    symbol_color = visual_data.get('color', (255, 255, 255))
                    
                    font_size = max(tile_size_with_spacing // 2, 24)  # Bigger font
                    font = pygame.font.Font(None, font_size)
                    symbol_surface = font.render(symbol, True, symbol_color)
                    
                    symbol_rect = symbol_surface.get_rect(center=(x + tile_size_with_spacing // 2, y + tile_size_with_spacing // 2))
                    self.screen.blit(symbol_surface, symbol_rect)
                    
                    # Add a glowing border for text-based special tiles only
                    pygame.draw.rect(self.screen, visual_data.get('effect_color', (255, 255, 255)), tile_rect, 3)
            else:
                # Regular tile - try to use sprite first, fallback to color
                sprite = self.sprite_manager.get_tile_sprite(tile.color, tile_size_with_spacing)
                if sprite:
                    # Sprite is 5 pixels bigger than tile, so center it by offsetting by -2
                    sprite_x = x - 2
                    sprite_y = y - 2
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                else:
                    color = tile.color.value
                    self.draw_rounded_rect(self.screen, color, tile_rect, 8)
    
    def draw_rounded_rect(self, surface, color, rect, radius):
        """Draw a rounded rectangle"""
        # Simple implementation - draw rectangle with rounded corners
        pygame.draw.rect(surface, color, rect)
        # Could add actual rounded corner implementation here for better visuals
    
    def draw_dual_borders(self):
        """Draw borders around both boards in dual mode"""
        if self.sprite_manager.has_border_sprite():
            border_padding = 120  # Extra space around each board
            border_width = self.board_width * self.tile_size + (border_padding * 2)
            border_height = self.board_height * self.tile_size + (border_padding * 2)
            
            border_sprite = self.sprite_manager.get_border_sprite(border_width, border_height)
            if border_sprite:
                # Player board border (left)
                player_border_x = self.board_x - border_padding
                player_border_y = self.board_y - border_padding
                self.screen.blit(border_sprite, (player_border_x, player_border_y))
                
                # Boss board border (right)
                boss_border_x = self.boss_board_x - border_padding
                boss_border_y = self.boss_board_y - border_padding
                self.screen.blit(border_sprite, (boss_border_x, boss_border_y))

    def draw_dual_boards(self):
        """Draw both player and boss boards side by side"""
        # Draw borders for both boards
        self.draw_dual_borders()
        
        # Draw player board (left side)
        player_board_area = pygame.Rect(self.board_x, self.board_y, 
                                      self.board_width * self.tile_size, 
                                      self.board_height * self.tile_size)
        
        old_clip = self.screen.get_clip()
        self.screen.set_clip(player_board_area)
        self.draw_board()
        self.screen.set_clip(old_clip)
        
        # Draw boss board (right side)
        if self.boss_board:
            boss_board_area = pygame.Rect(self.boss_board_x, self.boss_board_y, 
                                        self.board_width * self.tile_size, 
                                        self.board_height * self.tile_size)
            
            self.screen.set_clip(boss_board_area)
            self.draw_boss_board()
            self.screen.set_clip(old_clip)
        
        # Draw labels
        player_label = self.font.render("PLAYER", True, (255, 255, 255))
        boss_label = self.font.render("BOSS", True, (255, 100, 100))
        
        # Position labels above the boards
        player_label_x = self.board_x + (self.board_width * self.tile_size - player_label.get_width()) // 2
        boss_label_x = self.boss_board_x + (self.board_width * self.tile_size - boss_label.get_width()) // 2
        label_y = self.board_y - 40
        
        self.screen.blit(player_label, (player_label_x, label_y))
        self.screen.blit(boss_label, (boss_label_x, label_y))
    
    def draw_boss_board(self):
        """Draw the boss board with animations"""
        # Draw static tiles (not involved in animations)
        for row in range(self.boss_board.height):
            for col in range(self.boss_board.width):
                # Skip tiles that are currently animating
                if self.is_boss_tile_animating(row, col):
                    continue
                
                tile = self.boss_board.get_tile(row, col)
                if tile:
                    self.draw_boss_tile_at_position(row, col, tile)
        
        # Draw falling tiles on boss board
        for fall_anim in self.boss_fall_animations:
            # Calculate current position accounting for tile center offset
            current_row = (fall_anim.current_y - self.boss_board_y - self.tile_size // 2) / self.tile_size
            self.draw_boss_animated_tile(fall_anim.tile, fall_anim.col, current_row)
        
        # Draw swapping tiles on boss board
        for swap_anim in self.boss_swap_animations:
            # Always use the original tiles stored in the animation
            tile1 = swap_anim.original_tile1
            tile2 = swap_anim.original_tile2
            
            if tile1:
                self.draw_boss_animated_tile_at_screen_pos(tile1, swap_anim.current_pos1)
            if tile2:
                self.draw_boss_animated_tile_at_screen_pos(tile2, swap_anim.current_pos2)
        
        # Draw AI thinking indicator
        if self.boss_ai and self.boss_ai.is_thinking():
            self.draw_thinking_indicator()
    
    def draw_boss_tile_at_position(self, row, col, tile):
        """Draw a single tile on the boss board"""
        # Check for pop animation scaling
        scale = self.get_boss_pop_animation_scale(row, col)
        
        # Also check for spawn animation scaling (spawn takes priority if both exist)
        spawn_scale = self.get_boss_spawn_animation_scale(row, col)
        if spawn_scale != 1.0:
            scale = spawn_scale
        
        # Get tile data - check if it's animating first
        animation_tile = self.get_boss_pop_animation_tile(row, col)
        if animation_tile is not None:
            tile = animation_tile
        
        # Skip drawing if tile is too small (popped)
        if scale < 0.1:
            return
            
        base_x = self.boss_board_x + col * self.tile_size + self.tile_size // 2
        base_y = self.boss_board_y + row * self.tile_size + self.tile_size // 2
        
        # Apply scaling
        scaled_size = int(self.tile_size * scale)
        
        # Get sprite for the tile
        if tile.special_tile:
            sprite = self.sprite_manager.get_special_sprite(tile.special_tile.get_visual_representation().get('sprite_type', 'lightning'), scaled_size)
        else:
            sprite = self.sprite_manager.get_tile_sprite(tile.color, scaled_size)
        
        if sprite:
            sprite_rect = sprite.get_rect(center=(base_x, base_y))
            self.screen.blit(sprite, sprite_rect)
        else:
            # Fallback to colored rectangle
            tile_rect = pygame.Rect(base_x - scaled_size // 2, base_y - scaled_size // 2, scaled_size, scaled_size)
            pygame.draw.rect(self.screen, tile.color.value, tile_rect)
    
    def is_boss_tile_animating(self, row, col):
        """Check if a boss tile is currently involved in any animation"""
        # Check if involved in swap animation
        for swap_anim in self.boss_swap_animations:
            if (row, col) in [swap_anim.tile_pos1, swap_anim.tile_pos2]:
                return True
        
        # Check if this position is affected by falling tiles in the same column
        return self.is_boss_column_affected_by_falling(col, row)
    
    def is_boss_column_affected_by_falling(self, col, max_row=None):
        """Check if a column in boss board is affected by falling tiles"""
        for fall_anim in self.boss_fall_animations:
            if fall_anim.col == col:
                if max_row is None:
                    return True
                # Check if there's a tile that originally came from this position OR is falling to this position
                if hasattr(fall_anim, 'from_row'):
                    # Existing tile moving from one position to another
                    if fall_anim.from_row == max_row or fall_anim.to_row == max_row:
                        return True
                else:
                    # New tile falling to a position (no from_row)
                    if fall_anim.to_row == max_row:
                        return True
        return False
    
    def draw_boss_animated_tile(self, tile, col, row_float):
        """Draw an animated tile on the boss board at a floating row position"""
        # Calculate tile position
        x = self.boss_board_x + col * self.tile_size + self.tile_size // 2
        y = self.boss_board_y + row_float * self.tile_size + self.tile_size // 2
        
        self.draw_boss_animated_tile_at_screen_pos(tile, (x, y))
    
    def draw_boss_animated_tile_at_screen_pos(self, tile, screen_pos):
        """Draw an animated tile on the boss board at a specific screen position"""
        x, y = screen_pos
        
        # Just draw the tile normally - no special effects or red circles
        if tile.special_tile:
            sprite = self.sprite_manager.get_special_sprite(tile.special_tile.get_visual_representation().get('sprite_type', 'lightning'), self.tile_size)
        else:
            sprite = self.sprite_manager.get_tile_sprite(tile.color, self.tile_size)
            
            if sprite:
                sprite_rect = sprite.get_rect(center=(x, y))
                self.screen.blit(sprite, sprite_rect)
            else:
                # Fallback to normal colored rectangle
                tile_rect = pygame.Rect(x - self.tile_size // 2, y - self.tile_size // 2, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, tile.color.value, tile_rect)
    
    def draw_thinking_indicator(self):
        """Draw an indicator showing that the AI is thinking"""
        # Position above the boss board
        indicator_x = self.boss_board_x + (self.boss_board.width * self.tile_size) // 2
        indicator_y = self.boss_board_y - 40
        
        # Create pulsing effect
        pulse = (pygame.time.get_ticks() / 500) % 1.0  # Pulse every 500ms
        alpha = int(128 + 127 * abs(pulse - 0.5) * 2)  # Pulse between 128-255
        
        # Create thinking text
        thinking_text = self.font.render("AI THINKING...", True, (255, 255, 0))
        thinking_rect = thinking_text.get_rect(center=(indicator_x, indicator_y))
        
        # Draw background with pulsing alpha
        bg_surface = pygame.Surface((thinking_rect.width + 20, thinking_rect.height + 10))
        bg_surface.set_alpha(alpha)
        bg_surface.fill((0, 0, 0))
        bg_rect = bg_surface.get_rect(center=(indicator_x, indicator_y))
        self.screen.blit(bg_surface, bg_rect)
        
        # Draw the text
        self.screen.blit(thinking_text, thinking_rect)
        
        # Draw spinning dots
        dots = "⚈ ⚈ ⚈"
        dots_text = self.font.render(dots, True, (255, 255, 255))
        dots_rect = dots_text.get_rect(center=(indicator_x, indicator_y + 25))
        
        # Rotate the dots
        angle = (pygame.time.get_ticks() / 10) % 360
        rotated_dots = pygame.transform.rotate(dots_text, angle)
        rotated_rect = rotated_dots.get_rect(center=dots_rect.center)
        self.screen.blit(rotated_dots, rotated_rect)
    
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
        
        # Draw pop particles
        for pop_particle in self.pop_particles:
            pop_particle.draw(self.screen)
        
        # Draw boss pop particles
        for pop_particle in self.boss_pop_particles:
            pop_particle.draw(self.screen)
        
        # Draw instructions
        if self.selected_tile is None:
            if self.fall_animations:
                instruction_text = self.font.render("Tiles falling... You can still make matches in unaffected areas!", True, (200, 200, 200))
            else:
                instruction_text = self.font.render("Click tiles to select and swap adjacent ones", True, (200, 200, 200))
            text_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
            self.screen.blit(instruction_text, text_rect)
        
        # Draw special tile legend
        self.draw_special_tile_legend()
    
    def draw_special_tile_legend(self):
        """Draw legend showing what each special tile does"""
        legend_y = 150
        legend_items = [
            ("R (Orange): Horizontal Rocket - Clears entire row", (255, 69, 0)),
            ("R (Blue): Vertical Rocket - Clears entire column", (30, 144, 255)),
            ("B (Gray): Bomb - Explodes 5x5 area", (64, 64, 64)),
            ("L (Dark Blue): Lightning - Arc pattern strike", (25, 25, 112)),
            ("W (Purple): Board Wipe - Clears all of same color", (128, 0, 128))
        ]
        
        small_font = pygame.font.Font(None, 24)
        for i, (text, color) in enumerate(legend_items):
            legend_surface = small_font.render(text, True, (255, 255, 255))
            
            # Draw colored square next to text
            square_size = 20
            square_rect = pygame.Rect(20, legend_y + i * 25, square_size, square_size)
            pygame.draw.rect(self.screen, color, square_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), square_rect, 2)
            
            # Draw text
            self.screen.blit(legend_surface, (50, legend_y + i * 25))
    
    def draw_debug_overlay(self):
        """Draw debug mode overlay"""
        from special_tiles import SpecialTileType
        
        # Create semi-transparent overlay
        debug_surface = pygame.Surface((WINDOW_WIDTH, 120))
        debug_surface.set_alpha(200)
        debug_surface.fill((0, 0, 0))
        self.screen.blit(debug_surface, (0, 0))
        
        # Debug text
        font = pygame.font.Font(None, 24)
        text_lines = [
            "DEBUG MODE ACTIVE",
            f"Current Tile: {self.get_current_debug_tile_name()}",
            "TAB = Cycle tiles | Click = Place tile",
            "F3+1 = Exit debug mode"
        ]
        
        for i, line in enumerate(text_lines):
            color = (255, 255, 0) if i == 0 else (255, 255, 255)
            text_surface = font.render(line, True, color)
            self.screen.blit(text_surface, (10, 10 + i * 25))
    
    def get_current_debug_tile_name(self):
        """Get the name of the currently selected debug tile"""
        from special_tiles import SpecialTileType
        
        special_types = [
            SpecialTileType.ROCKET_HORIZONTAL,
            SpecialTileType.ROCKET_VERTICAL,
            SpecialTileType.BOMB,
            SpecialTileType.LIGHTNING,
            SpecialTileType.BOARD_WIPE,
            SpecialTileType.BOMB_ROCKET,
            SpecialTileType.BOMB_BOARDWIPE,
            SpecialTileType.MEGA_BOMB,
            SpecialTileType.ENERGIZED_BOMB,
            SpecialTileType.ROCKET_BOARDWIPE,
            SpecialTileType.ROCKET_LIGHTNING,
            SpecialTileType.SIMPLE_CROSS,
        ]
        
        # Add bounds checking to prevent crashes
        if 0 <= self.debug_special_type < len(special_types):
            return special_types[self.debug_special_type].name
        else:
            # Reset to first tile if out of bounds
            self.debug_special_type = 0
            return special_types[0].name
    
    def update_boss_ai(self):
        """Update the AI and execute moves for the boss board"""
        if not self.boss_ai or not self.boss_board:
            return
        
        # Update AI computation (frame-based processing)
        if self.boss_ai.is_thinking():
            self.boss_ai.update_computation()
        
        # Start thinking when it's time to make a move and not already thinking
        elif self.boss_ai.should_make_move():
            self.boss_ai.start_thinking()
        
        # Check if a move is ready
        ai_move = self.boss_ai.get_computed_move()
        
        if ai_move:
            # Execute the move on the boss board
            self.execute_boss_move(ai_move)
    
    def execute_boss_move(self, move):
        """Execute an AI move on the boss board with animations"""
        from boss_ai import Move
        
        # Start boss swap animation
        pos1, pos2 = move.pos1, move.pos2
        
        # Get screen positions for boss board
        screen_pos1 = self.get_boss_tile_screen_pos(pos1)
        screen_pos2 = self.get_boss_tile_screen_pos(pos2)
        
        # Create swap animation for boss board
        print(f"Creating boss swap animation: {screen_pos1} -> {screen_pos2}, duration: 0.3s")
        swap_anim = SwapAnimation(screen_pos1, screen_pos2, 0.3)  # Same speed as player animations
        print(f"Animation created: start_pos1={swap_anim.start_pos1}, start_pos2={swap_anim.start_pos2}, duration={swap_anim.duration}")
        
        # Store tile positions and original tiles in the animation
        swap_anim.tile_pos1 = pos1
        swap_anim.tile_pos2 = pos2
        swap_anim.original_tile1 = self.boss_board.get_tile(*pos1)
        swap_anim.original_tile2 = self.boss_board.get_tile(*pos2)
        
        self.boss_swap_animations.append(swap_anim)
        self.boss_animating = True
        
        # Reset move delay for next move
        self.boss_move_delay = self.boss_move_cooldown
    
    def get_boss_tile_screen_pos(self, board_pos):
        """Get screen position for a boss board tile"""
        row, col = board_pos
        x = self.boss_board_x + col * self.tile_size + self.tile_size // 2
        y = self.boss_board_y + row * self.tile_size + self.tile_size // 2
        return (x, y)
    
    def complete_boss_swap_animation(self, swap_anim):
        """Complete a boss board swap animation and process matches"""
        pos1, pos2 = swap_anim.tile_pos1, swap_anim.tile_pos2
        
        # First, perform the actual swap on the boss board
        self.boss_board.swap_tiles(pos1, pos2)
        
        # Check for combo tiles first
        combo_tile = self.boss_board.check_for_combo(pos1, pos2)
        if combo_tile:
            # Create combo tile at one of the positions
            combo_pos = pos1  # Place combo at first position
            from board import Tile
            from board import TileColor
            new_tile = Tile(TileColor.RED, special_tile=combo_tile)
            self.boss_board.set_tile(*combo_pos, new_tile)
            
            # Remove the other tile
            self.boss_board.set_tile(*pos2, None)
            
            # Check if this combo needs special handling
            if hasattr(combo_tile, 'requires_special_handling') and combo_tile.requires_special_handling:
                from special_tiles import SpecialTileType
                print(f"Boss created special combo: {combo_tile.tile_type}")
                if combo_tile.tile_type == SpecialTileType.BOMB_BOARDWIPE:
                    self.handle_boss_bomb_boardwipe_combo(combo_pos, combo_tile)
                elif combo_tile.tile_type == SpecialTileType.ROCKET_BOARDWIPE:
                    self.handle_boss_rocket_boardwipe_combo(combo_pos, combo_tile)
                elif combo_tile.tile_type == SpecialTileType.ROCKET_LIGHTNING:
                    self.handle_boss_rocket_lightning_combo(combo_pos, combo_tile)
                elif combo_tile.tile_type == SpecialTileType.REALITY_BREAK:
                    self.handle_boss_reality_break_combo(combo_pos, combo_tile)
                return
            
            # Activate the combo tile immediately on boss board
            result = self.boss_board.activate_special_tile(*combo_pos)
            if isinstance(result, tuple) and len(result) == 2:
                affected_positions, activated_tiles = result
                # Create particle effects for boss special tiles
                for tile_row, tile_col, special_tile in activated_tiles:
                    self.create_boss_special_effect_particles((tile_row, tile_col), special_tile)
            
            self.apply_boss_board_gravity()
            return
        
        # Check if either tile is a special tile that should be activated
        special_activated = False
        
        tile1 = self.boss_board.get_tile(*pos1)
        tile2 = self.boss_board.get_tile(*pos2)
        
        # Handle board wipe special case
        from special_tiles import SpecialTileType
        
        if tile1 and tile1.is_special() and tile1.special_tile.tile_type == SpecialTileType.BOARD_WIPE:
            # Board wipe targets the color of the tile it was swapped with
            target_color = tile2.color if tile2 and not tile2.is_empty() else None
            if target_color:
                self.handle_boss_board_wipe_activation(pos1, tile1.special_tile, target_color)
                special_activated = True
        elif tile2 and tile2.is_special() and tile2.special_tile.tile_type == SpecialTileType.BOARD_WIPE:
            # Board wipe targets the color of the tile it was swapped with
            target_color = tile1.color if tile1 and not tile1.is_empty() else None
            if target_color:
                self.handle_boss_board_wipe_activation(pos2, tile2.special_tile, target_color)
                special_activated = True
        else:
            # Handle other special tiles normally
            if tile1 and tile1.is_special():
                result = self.boss_board.activate_special_tile(*pos1)
                if isinstance(result, tuple) and len(result) == 2:
                    affected_positions, activated_tiles = result
                    if affected_positions:
                        # Create particle effects for boss special tiles
                        for tile_row, tile_col, special_tile in activated_tiles:
                            self.create_boss_special_effect_particles((tile_row, tile_col), special_tile)
                        special_activated = True
            
            if tile2 and tile2.is_special():
                result = self.boss_board.activate_special_tile(*pos2)
                if isinstance(result, tuple) and len(result) == 2:
                    affected_positions, activated_tiles = result
                    if affected_positions:
                        # Create particle effects for boss special tiles
                        for tile_row, tile_col, special_tile in activated_tiles:
                            self.create_boss_special_effect_particles((tile_row, tile_col), special_tile)
                        special_activated = True
        
        if special_activated:
            # Special tile was activated, apply gravity
            self.apply_boss_board_gravity()
            return
        
        # Check for regular matches
        matches = self.boss_board.find_all_matches()
        if matches:
            self.process_boss_matches(matches)
        else:
            self.boss_animating = False
    
    def process_boss_matches(self, matches):
        """Process matches on the boss board and update AI score"""
        # Create pop animations for boss matched tiles (but don't clear tiles yet)
        self.create_boss_pop_animations_for_matches(matches)
        
        # Store matches to clear after animation completes
        self.pending_boss_matches = matches
        
        # Don't apply gravity until pop animations finish
        
        # Note: Cascades will be checked when fall animations complete
    
    def apply_boss_board_gravity(self):
        """Apply gravity to the boss board with animations"""
        # Apply gravity to determine new positions
        fall_data = self.boss_board.apply_gravity_with_animation_data()
        
        # Create fall animations for existing tiles
        for col, tiles_to_fall in fall_data.items():
            for tile_data in tiles_to_fall:
                start_y = self.get_boss_tile_screen_pos((tile_data['from_row'], col))[1]
                end_y = self.get_boss_tile_screen_pos((tile_data['to_row'], col))[1]
                
                if start_y != end_y:
                    # Calculate duration based on fall distance
                    fall_distance = end_y - start_y
                    base_duration = 0.3
                    distance_factor = fall_distance / (self.tile_size * 3)
                    duration = base_duration + distance_factor * 0.3
                    
                    fall_anim = FallAnimation(start_y, end_y, duration)
                    fall_anim.col = col
                    fall_anim.from_row = tile_data['from_row']
                    fall_anim.to_row = tile_data['to_row']
                    fall_anim.tile = tile_data['tile']
                    fall_anim.is_existing_tile = True
                    self.boss_fall_animations.append(fall_anim)
        
        # Fill empty spaces with new tiles
        self.boss_board.fill_empty_spaces_with_fall_data()
        
        # Create fall animations for new tiles
        self.create_boss_new_tile_animations()
        
        # Set boss_animating to True if we have animations
        if self.boss_fall_animations:
            self.boss_animating = True
    
    def create_boss_new_tile_animations(self):
        """Create fall animations for newly spawned tiles on boss board"""
        for col in range(self.boss_board.width):
            # Find all newly spawned tiles in this column from top to bottom
            new_tiles = []
            for row in range(self.boss_board.height):
                tile = self.boss_board.get_tile(row, col)
                if tile and hasattr(tile, 'newly_spawned') and tile.newly_spawned:
                    new_tiles.append((row, tile))
                    # Remove the newly_spawned flag
                    delattr(tile, 'newly_spawned')
            
            # Create animations for new tiles, stacking them properly above the board
            for i, (row, tile) in enumerate(new_tiles):
                # Stack new tiles above the board in reverse order
                stack_position = len(new_tiles) - i
                boss_board_y = self.get_boss_tile_screen_pos((0, 0))[1] - self.tile_size
                start_y = boss_board_y - stack_position * self.tile_size
                end_y = self.get_boss_tile_screen_pos((row, col))[1]
                
                # Calculate fall duration based on distance
                fall_distance = end_y - start_y
                fall_duration = 0.3 + (fall_distance / (self.boss_board.height * self.tile_size)) * 0.8
                
                fall_anim = FallAnimation(start_y, end_y, fall_duration)
                fall_anim.col = col
                fall_anim.to_row = row
                fall_anim.tile = tile
                fall_anim.is_new_tile = True
                self.boss_fall_animations.append(fall_anim)
    
    def complete_boss_fall_animation(self):
        """Complete boss fall animation and check for cascade matches"""
        # Check for new matches
        cascade_matches = self.boss_board.find_all_matches()
        if cascade_matches:
            # Continue the cascade
            self.process_boss_matches(cascade_matches)
        else:
            # Chain is complete, boss turn is done
            self.boss_animating = False
    
    def create_boss_special_effect_particles(self, position, special_tile):
        """Create particle effects for boss board special tile activation"""
        # Convert boss board position to screen position
        screen_pos = self.get_boss_tile_screen_pos(position)
        
        # Create same particle effects as player board but positioned for boss board
        self.create_special_effect_particles(position, special_tile, boss_board=True)
    
    def handle_boss_board_wipe_activation(self, pos, special_tile, target_color):
        """Handle board wipe activation on boss board"""
        # Start the board wipe animation for boss board
        self.board_wipe_active = True
        self.board_wipe_progress = 0.0
        self.board_wipe_target_color = target_color
        self.board_wipe_boss_board = True  # Flag to indicate this is for boss board
        
        # Remove the board wipe tile
        self.boss_board.set_tile(*pos, None)
        
        # Create explosion particle effect at activation position
        screen_pos = self.get_boss_tile_screen_pos(pos)
        effect = ParticleEffect(screen_pos[0], screen_pos[1], (255, 255, 255), 50)
        self.particle_effects.append(effect)
    
    def handle_boss_rocket_boardwipe_combo(self, pos, combo_tile):
        """Handle the rocket + boardwipe combo on boss board"""
        from special_tiles import create_special_tile, SpecialTileType
        from board import Tile, TileColor
        import random
        
        # Clear any existing boss fall animations
        self.boss_fall_animations.clear()
        
        # Get rocket positions before removing combo tile
        rocket_positions = combo_tile.get_rocket_positions(self.boss_board, pos)
        
        # Place rockets at selected positions (randomly choose horizontal or vertical)
        for rocket_pos in rocket_positions:
            is_horizontal = random.choice([True, False])
            rocket_type = SpecialTileType.ROCKET_HORIZONTAL if is_horizontal else SpecialTileType.ROCKET_VERTICAL
            rocket_special = create_special_tile(rocket_type, color=TileColor.RED)
            rocket_tile = Tile(TileColor.RED, special_tile=rocket_special)
            self.boss_board.set_tile(*rocket_pos, rocket_tile)
        
        # Remove the combo tile after placing rockets
        self.boss_board.set_tile(*pos, None)
        
        # Sort positions from top to bottom, left to right for sequential detonation
        rocket_positions.sort(key=lambda pos: (pos[0], pos[1]))
        
        # Set up animation state for boss board (use separate state variables)
        self.boss_bomb_boardwipe_active = True
        self.boss_bomb_boardwipe_positions = rocket_positions
        self.boss_bomb_boardwipe_timer = 0
        self.boss_bomb_boardwipe_detonation_timer = 0
        self.boss_bomb_boardwipe_detonation_index = 0
        
        # Immediately start a fall animation to fill gaps
        self.apply_boss_board_gravity()
        
        print(f"Boss placed {len(rocket_positions)} rockets for sequential detonation!")
    
    def handle_boss_bomb_boardwipe_combo(self, pos, combo_tile):
        """Handle the bomb + boardwipe combo on boss board"""
        from special_tiles import create_special_tile, SpecialTileType
        from board import Tile, TileColor
        
        # Get bomb positions before removing combo tile
        bomb_positions = combo_tile.get_bomb_positions(self.boss_board, pos)
        
        # Place bombs at selected positions
        for bomb_pos in bomb_positions:
            bomb_special = create_special_tile(SpecialTileType.BOMB, color=TileColor.RED)
            bomb_tile = Tile(TileColor.RED, special_tile=bomb_special)
            self.boss_board.set_tile(*bomb_pos, bomb_tile)
        
        # Remove the combo tile
        self.boss_board.set_tile(*pos, None)
        
        # Set up animation state for boss board
        self.boss_bomb_boardwipe_active = True
        self.boss_bomb_boardwipe_positions = bomb_positions
        self.boss_bomb_boardwipe_timer = 0
        self.boss_bomb_boardwipe_detonation_timer = 0
        self.boss_bomb_boardwipe_detonation_index = 0
        
        self.apply_boss_board_gravity()
        print(f"Boss placed {len(bomb_positions)} bombs for sequential detonation!")
    
    def handle_boss_rocket_lightning_combo(self, pos, combo_tile):
        """Handle the rocket + lightning combo on boss board"""
        # Set up rocket lightning animation for boss board
        self.boss_rocket_lightning_active = True
        self.boss_rocket_lightning_position = pos
        self.boss_rocket_lightning_timer = 0.0
        self.boss_rocket_lightning_phase = 'charging'
        
        print("Boss activated rocket lightning combo!")
    
    def handle_boss_reality_break_combo(self, pos, combo_tile):
        """Handle the reality break combo on boss board"""
        # Set up reality break animation for boss board
        self.boss_reality_break_active = True
        self.boss_reality_break_position = pos
        self.boss_reality_break_timer = 0.0
        self.boss_reality_break_phase = 'charging'
        
        print("Boss activated reality break combo!")
    
    def update_boss_bomb_boardwipe_animation(self, dt):
        """Update boss board bomb/rocket boardwipe animation (sequential detonation)"""
        if not self.boss_bomb_boardwipe_positions:
            self.boss_bomb_boardwipe_active = False
            return
        
        self.boss_bomb_boardwipe_timer += dt
        
        # Wait initial delay before starting detonations
        if self.boss_bomb_boardwipe_timer < 0.5:
            return
        
        self.boss_bomb_boardwipe_detonation_timer += dt
        
        # Detonate next tile every 0.2 seconds
        if (self.boss_bomb_boardwipe_detonation_timer >= 0.2 and 
            self.boss_bomb_boardwipe_detonation_index < len(self.boss_bomb_boardwipe_positions)):
            
            # Get the position to detonate
            pos = self.boss_bomb_boardwipe_positions[self.boss_bomb_boardwipe_detonation_index]
            
            # Activate the special tile at this position on boss board
            tile = self.boss_board.get_tile(*pos)
            if tile and tile.is_special():
                result = self.boss_board.activate_special_tile(*pos)
                if isinstance(result, tuple) and len(result) == 2:
                    affected_positions, activated_tiles = result
                    # Create particle effects for boss special tiles
                    for tile_row, tile_col, special_tile in activated_tiles:
                        self.create_boss_special_effect_particles((tile_row, tile_col), special_tile)
            
            self.boss_bomb_boardwipe_detonation_index += 1
            self.boss_bomb_boardwipe_detonation_timer = 0
            
            # If this was the last detonation, end the animation
            if self.boss_bomb_boardwipe_detonation_index >= len(self.boss_bomb_boardwipe_positions):
                self.boss_bomb_boardwipe_active = False
                self.apply_boss_board_gravity()
    
    def update_boss_rocket_lightning_animation(self, dt):
        """Update boss board rocket lightning combo animation"""
        # For now, just end the animation quickly - can be enhanced later
        self.boss_rocket_lightning_active = False
        print("Boss rocket lightning combo completed!")
        self.apply_boss_board_gravity()
    
    def update_boss_reality_break_animation(self, dt):
        """Update boss board reality break combo animation"""
        # For now, just end the animation quickly - can be enhanced later
        self.boss_reality_break_active = False
        print("Boss reality break combo completed!")
        self.apply_boss_board_gravity()

def run_level_select():
    """Run the level select screen and return selected level"""
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption("Match 3 - Level Select")
    clock = pygame.time.Clock()
    
    level_select = LevelSelectScreen(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    while level_select.running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                level_select.running = False
                return None
        
        level_select.handle_events(events)
        level_select.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return level_select.get_selected_level()

if __name__ == "__main__":
    # Run level select first
    selected_level = run_level_select()
    
    if selected_level is not None:
        # Start game with selected level
        game = Match3Game(selected_level)
        game.run()
    
    pygame.quit()
    sys.exit()