import pygame
import random
import sys
import os
from typing import List, Tuple, Optional, Set
import math
from board import Board, Tile, TileColor, Match, MatchType
from animations import FallAnimation, SwapAnimation, PulseAnimation, ParticleEffect
from special_tiles import SpecialTile, SpecialTileType
from arcade_particles import PixelParticleSystem

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
        
        # Level configuration - first level takes up half the screen
        self.current_level = 1
        self.configure_level(self.current_level)
        
        # Initialize board and sprite manager
        self.board = Board(self.board_width, self.board_height, self.tile_size)
        self.sprite_manager = SpriteManager()
        self.sprite_manager.load_tile_sprites()
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
        # Convert screen coordinates to board coordinates
        board_x = pos[0] - self.board_x
        board_y = pos[1] - self.board_y
        
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
        ]
        
        # Get current special tile type
        current_type = special_types[self.debug_special_type]
        
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
    
    def clear_row_cascade(self, row_index):
        """Clear a single row in the cascade"""
        if row_index < len(self.rocket_lightning_rows):
            row = self.rocket_lightning_rows[row_index]
            
            # Clear entire row (no particles, just instant removal)
            for col in range(self.board.width):
                self.board.set_tile(row, col, None)
            
            print(f"Cleared row {row}")
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
                    affected_positions, activated_tiles = self.board.activate_special_tile(*pos)
                    
                    # Create particle effects for all activated special tiles
                    for tile_row, tile_col, special_tile in activated_tiles:
                        self.create_special_effect_particles((tile_row, tile_col), special_tile)
                    
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
        
        # Clear next row every 0.1 seconds
        if self.rocket_lightning_timer >= 0.1:
            self.rocket_lightning_row_index += 1
            
            if self.rocket_lightning_row_index < len(self.rocket_lightning_rows):
                # Clear the next row
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
                return
            
            # Activate the combo tile immediately
            affected_positions, activated_tiles = self.board.activate_special_tile(*combo_pos)
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
                affected_positions, activated_tiles = self.board.activate_special_tile(*pos1)
                if affected_positions:
                    # Create particle effects for all activated special tiles
                    for tile_row, tile_col, special_tile in activated_tiles:
                        self.create_special_effect_particles((tile_row, tile_col), special_tile)
                    self.score += tile1.special_tile.get_score_bonus()
                    special_activated = True
            
            if tile2 and tile2.is_special():
                affected_positions, activated_tiles = self.board.activate_special_tile(*pos2)
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
        # Add score and create particle effects
        for match in matches:
            # Calculate score with combo multiplier
            match_score = match.score * self.combo_multiplier
            self.score += match_score
            
            # Skip basic particle effects for normal tiles - only use pixel particles for special tiles
            
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
    
    def create_special_effect_particles(self, pos, special_tile):
        """Create particle effects for special tile activation"""
        screen_pos = self.get_tile_screen_pos(pos)
        visual_data = special_tile.get_visual_representation()
        effect_color = visual_data.get('effect_color', (255, 255, 255))
        
        # Check if it's a bomb and create pixel explosion effect
        if special_tile.tile_type == SpecialTileType.BOMB:
            # Create pixel art explosion for regular bombs (not in combos)
            center_x = screen_pos[0] + self.tile_size // 2
            center_y = screen_pos[1] + self.tile_size // 2
            self.pixel_particles.create_bomb_explosion(center_x, center_y)
        
        # Check if it's a rocket and create rocket trail effect
        elif special_tile.tile_type in [SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.ROCKET_VERTICAL]:
            # Get board bounds for clipping
            board_bounds = self._get_board_bounds()
            
            if special_tile.tile_type == SpecialTileType.ROCKET_HORIZONTAL:
                # For horizontal rockets, use row center and middle of board for Y
                row, col = pos
                center_x = screen_pos[0] + self.tile_size // 2
                # Center the horizontal rocket on the exact middle of the row
                center_y = self.board_y + (row * self.tile_size) + (self.tile_size // 2)
                self.pixel_particles.create_rocket_trail(center_x, center_y, 'horizontal', board_bounds)
            else:
                # For vertical rockets, use column center and middle of board for X
                row, col = pos
                # Center the vertical rocket on the exact middle of the column
                center_x = self.board_x + (col * self.tile_size) + (self.tile_size // 2)
                center_y = screen_pos[1] + self.tile_size // 2
                self.pixel_particles.create_rocket_trail(center_x, center_y, 'vertical', board_bounds)
        
        # Check if it's a simple cross (rocket combo) and create cross trail effect
        elif special_tile.tile_type == SpecialTileType.SIMPLE_CROSS:
            # Create cross pattern (both horizontal and vertical) - properly centered
            board_bounds = self._get_board_bounds()
            row, col = pos
            # Use same centering logic as individual rockets
            center_x = self.board_x + (col * self.tile_size) + (self.tile_size // 2)
            center_y = self.board_y + (row * self.tile_size) + (self.tile_size // 2)
            self.pixel_particles.create_rocket_trail(center_x, center_y, 'cross', board_bounds)
        
        # Check if it's a lightning and create lightning arc effect
        elif special_tile.tile_type == SpecialTileType.LIGHTNING:
            # Create dramatic lightning arc effect
            center_x = screen_pos[0] + self.tile_size // 2
            center_y = screen_pos[1] + self.tile_size // 2
            self.pixel_particles.create_lightning_arc(center_x, center_y)
        
        # Skip old particle effects - pixel particles are much more dramatic
    
    def _get_board_bounds(self):
        """Get the board rendering bounds for particle clipping"""
        # Calculate the actual board area bounds
        left = self.board_x
        top = self.board_y
        right = self.board_x + (self.board.width * self.tile_size)
        bottom = self.board_y + (self.board.height * self.tile_size)
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
            return  # Don't process other animations while rocket lightning is active
        
        # Update swap animations
        for swap_anim in self.swap_animations[:]:
            if swap_anim.update(dt):
                # Animation completed
                self.swap_animations.remove(swap_anim)
                
                if not hasattr(swap_anim, 'is_reversal'):
                    # Check for matches (not for reversals)
                    self.complete_swap_animation(swap_anim)
        
        # Update fall animations
        completed_fall_animations = []
        for fall_anim in self.fall_animations[:]:
            if fall_anim.update(dt):
                # Animation completed - ensure tile is properly placed on board
                if hasattr(fall_anim, 'tile') and hasattr(fall_anim, 'to_row') and hasattr(fall_anim, 'col'):
                    self.board.set_tile(fall_anim.to_row, fall_anim.col, fall_anim.tile)
                
                # Add a small delay before removing to prevent flashing
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
        
        # Update pixel particle system
        self.pixel_particles.update(dt)
    
    def draw(self):
        """Draw the entire game"""
        self.screen.fill(BACKGROUND_COLOR)
        
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
        
        # Draw UI elements (outside the clipped area)
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
            # Use the original tiles stored in the animation (before any swap)
            tile1 = getattr(swap_anim, 'original_tile1', self.board.get_tile(*swap_anim.tile_pos1))
            tile2 = getattr(swap_anim, 'original_tile2', self.board.get_tile(*swap_anim.tile_pos2))
            
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
        
        # Check if this position is affected by falling tiles in the same column
        return self.is_column_affected_by_falling(col, row)
    
    def is_column_affected_by_falling(self, col, max_row=None):
        """Check if a column (or specific row in column) is affected by falling tiles"""
        for fall_anim in self.fall_animations:
            if fall_anim.col == col:
                if max_row is None:
                    return True
                # Check if the falling tile will affect this row
                # If a tile is falling to a position at or below this row, this position is affected
                if fall_anim.to_row >= max_row:
                    return True
        return False
    
    def draw_tile_at_position(self, tile_row, tile_col, draw_row, draw_col):
        """Draw a tile at a specific board position"""
        # Calculate tile position with spacing
        spacing = 2  # Small gap between tiles
        x = self.board_x + draw_col * self.tile_size + spacing
        y = self.board_y + draw_row * self.tile_size + spacing
        
        # Draw tile background with smaller size for spacing
        tile_size_with_spacing = self.tile_size - (spacing * 2)
        tile_rect = pygame.Rect(x, y, tile_size_with_spacing, tile_size_with_spacing)
        
        # Get tile color
        tile = self.board.get_tile(tile_row, tile_col)
        if tile:
            # Check if it's a special tile
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
                    
                    # Create font for symbol - make it bigger and bolder
                    font_size = max(tile_size_with_spacing // 2, 24)  # Bigger font
                    font = pygame.font.Font(None, font_size)
                    symbol_surface = font.render(symbol, True, symbol_color)
                    
                    # Center the symbol
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
                    # Fallback to colored rectangle
                    color = tile.color.value
                    self.draw_rounded_rect(self.screen, color, tile_rect, 8)
        else:
            # Don't render anything for empty tiles during rocket lightning cascade
            if not self.rocket_lightning_active:
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
        
        # Draw pixel particle effects
        self.pixel_particles.draw(self.screen)
        
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
        ]
        
        return special_types[self.debug_special_type].name

if __name__ == "__main__":
    game = Match3Game()
    game.run()