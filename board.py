import random
from typing import List, Optional, Set, Tuple, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from special_tiles import SpecialTile

class TileColor(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    EMPTY = (50, 50, 50)

class MatchType(Enum):
    THREE = 3
    FOUR = 4
    FIVE = 5
    SQUARE = "square"
    CORNER = "corner"
    T_SHAPE = "t_shape"

class Tile:
    """Represents a single tile in the game"""
    
    def __init__(self, color: TileColor, special_tile=None):
        self.color = color
        self.special_tile = special_tile  # SpecialTile instance if this is a special tile
        self.falling = False
        self.fall_speed = 0
        self.target_row = 0
        self.current_y = 0
    
    def __repr__(self):
        if self.is_special():
            return f"Tile({self.color.name}, Special: {self.special_tile.tile_type.name})"
        return f"Tile({self.color.name})"
    
    def is_empty(self):
        return self.color == TileColor.EMPTY
    
    def is_special(self):
        """Check if this is a special tile"""
        return self.special_tile is not None
    
    def set_falling(self, target_row: int, fall_speed: float = 300):
        """Set tile to falling state"""
        self.falling = True
        self.target_row = target_row
        self.fall_speed = fall_speed

class Match:
    """Represents a match found on the board"""
    
    def __init__(self, positions: List[Tuple[int, int]], match_type: MatchType):
        self.positions = positions
        self.match_type = match_type
        self.score = self.calculate_score()
    
    def calculate_score(self):
        """Calculate score based on match type and length"""
        base_scores = {
            MatchType.THREE: 100,
            MatchType.FOUR: 400,
            MatchType.FIVE: 1000,
            MatchType.SQUARE: 800,
            MatchType.CORNER: 600,
            MatchType.T_SHAPE: 800
        }
        return base_scores.get(self.match_type, 100)

class Board:
    """Manages the game board and tile operations"""
    
    def __init__(self, width: int, height: int, tile_size: int):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.grid: List[List[Optional[Tile]]] = []
        self.base_colors = [TileColor.RED, TileColor.GREEN, TileColor.BLUE, 
                           TileColor.YELLOW, TileColor.ORANGE]
        self.available_colors = self.base_colors.copy()
        self.excluded_colors = set()
        
        # Import here to avoid circular imports
        from special_tiles import TileDeck
        self.tile_deck = TileDeck()
    
    def generate_initial_board(self):
        """Generate initial board ensuring no matches"""
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        for row in range(self.height):
            for col in range(self.width):
                # Get valid colors (avoid creating initial matches)
                valid_colors = self.get_valid_colors_for_position(row, col)
                color = random.choice(valid_colors)
                self.grid[row][col] = Tile(color)
    
    def get_valid_colors_for_position(self, row: int, col: int) -> List[TileColor]:
        """Get colors that don't create matches at given position"""
        valid_colors = self.available_colors.copy()
        
        # Check horizontal matches
        if col >= 2:
            if (self.grid[row][col-1] and self.grid[row][col-2] and 
                self.grid[row][col-1].color == self.grid[row][col-2].color):
                if self.grid[row][col-1].color in valid_colors:
                    valid_colors.remove(self.grid[row][col-1].color)
        
        # Check vertical matches
        if row >= 2:
            if (self.grid[row-1][col] and self.grid[row-2][col] and 
                self.grid[row-1][col].color == self.grid[row-2][col].color):
                if self.grid[row-1][col].color in valid_colors:
                    valid_colors.remove(self.grid[row-1][col].color)
        
        return valid_colors if valid_colors else [random.choice(self.available_colors)]
    
    def set_excluded_colors(self, excluded_colors: Set[TileColor]):
        """Set which colors should be excluded from generation"""
        self.excluded_colors = excluded_colors
        self.available_colors = [color for color in self.base_colors 
                                if color not in self.excluded_colors]
        
        # Ensure we always have at least 3 colors available
        if len(self.available_colors) < 3:
            # Add back some colors if we excluded too many
            for color in self.base_colors:
                if color not in self.excluded_colors:
                    continue
                self.available_colors.append(color)
                if len(self.available_colors) >= 3:
                    break
    
    def get_tile(self, row: int, col: int) -> Optional[Tile]:
        """Get tile at specific position"""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row][col]
        return None
    
    def set_tile(self, row: int, col: int, tile: Optional[Tile]):
        """Set tile at specific position"""
        if 0 <= row < self.height and 0 <= col < self.width:
            self.grid[row][col] = tile
    
    def swap_tiles(self, pos1: Tuple[int, int], pos2: Tuple[int, int]):
        """Swap two tiles on the board"""
        row1, col1 = pos1
        row2, col2 = pos2
        
        if (0 <= row1 < self.height and 0 <= col1 < self.width and
            0 <= row2 < self.height and 0 <= col2 < self.width):
            self.grid[row1][col1], self.grid[row2][col2] = self.grid[row2][col2], self.grid[row1][col1]
    
    def find_all_matches(self) -> List[Match]:
        """Find all matches on the board"""
        matches = []
        processed_positions = set()
        
        # Find special pattern matches FIRST (they have higher priority)
        matches.extend(self.find_corner_matches(processed_positions))
        matches.extend(self.find_t_matches(processed_positions))
        matches.extend(self.find_square_matches(processed_positions))
        
        # Then find horizontal and vertical line matches
        matches.extend(self.find_line_matches(processed_positions))
        
        return matches
    
    def find_line_matches(self, processed_positions: Set[Tuple[int, int]]) -> List[Match]:
        """Find horizontal and vertical line matches"""
        matches = []
        
        # Check horizontal matches
        for row in range(self.height):
            col = 0
            while col < self.width:
                if self.grid[row][col] and not self.grid[row][col].is_empty():
                    color = self.grid[row][col].color
                    match_positions = [(row, col)]
                    
                    # Extend match to the right
                    next_col = col + 1
                    while (next_col < self.width and self.grid[row][next_col] and 
                           self.grid[row][next_col].color == color):
                        match_positions.append((row, next_col))
                        next_col += 1
                    
                    # Create match if 3 or more tiles
                    if len(match_positions) >= 3:
                        # Skip if already processed
                        if not any(pos in processed_positions for pos in match_positions):
                            match_type = self.get_line_match_type(len(match_positions))
                            matches.append(Match(match_positions, match_type))
                            processed_positions.update(match_positions)
                    
                    col = max(col + 1, next_col)
                else:
                    col += 1
        
        # Check vertical matches
        for col in range(self.width):
            row = 0
            while row < self.height:
                if self.grid[row][col] and not self.grid[row][col].is_empty():
                    color = self.grid[row][col].color
                    match_positions = [(row, col)]
                    
                    # Extend match downward
                    next_row = row + 1
                    while (next_row < self.height and self.grid[next_row][col] and 
                           self.grid[next_row][col].color == color):
                        match_positions.append((next_row, col))
                        next_row += 1
                    
                    # Create match if 3 or more tiles
                    if len(match_positions) >= 3:
                        # Skip if already processed
                        if not any(pos in processed_positions for pos in match_positions):
                            match_type = self.get_line_match_type(len(match_positions))
                            matches.append(Match(match_positions, match_type))
                            processed_positions.update(match_positions)
                    
                    row = max(row + 1, next_row)
                else:
                    row += 1
        
        return matches
    
    def get_line_match_type(self, length: int) -> MatchType:
        """Get match type based on line length"""
        if length == 3:
            return MatchType.THREE
        elif length == 4:
            return MatchType.FOUR
        else:
            return MatchType.FIVE
    
    def find_square_matches(self, processed_positions: Set[Tuple[int, int]]) -> List[Match]:
        """Find 2x2 square matches"""
        matches = []
        
        for row in range(self.height - 1):
            for col in range(self.width - 1):
                positions = [(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)]
                
                # Check if all positions have the same color
                tiles = [self.grid[r][c] for r, c in positions]
                if (all(tile and not tile.is_empty() for tile in tiles) and
                    all(tile.color == tiles[0].color for tile in tiles) and
                    not any(pos in processed_positions for pos in positions)):
                    
                    matches.append(Match(positions, MatchType.SQUARE))
                    processed_positions.update(positions)
        
        return matches
    
    def find_corner_matches(self, processed_positions: Set[Tuple[int, int]]) -> List[Match]:
        """Find L-shaped corner matches"""
        matches = []
        
        # Define corner patterns (relative positions) - L-shapes as you specified
        # Pattern: xxx
        #          xoo  
        #          xoo
        corner_patterns = [
            # Top-left corner (xxx pattern at top)
            [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],  # xxx at top, x column down
            # Top-right corner (xxx pattern at top)
            [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],  # xxx at top, x column down right
            # Bottom-left corner (xxx pattern at bottom)
            [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],  # x column down, xxx at bottom
            # Bottom-right corner (xxx pattern at bottom)
            [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2)],  # x column down right, xxx at bottom
        ]
        
        # Check all possible positions on the board
        for row in range(self.height):
            for col in range(self.width):
                for pattern in corner_patterns:
                    positions = [(row + dr, col + dc) for dr, dc in pattern]
                    
                    # Check bounds
                    if all(0 <= r < self.height and 0 <= c < self.width for r, c in positions):
                        tiles = [self.grid[r][c] for r, c in positions]
                        
                        if (all(tile and not tile.is_empty() for tile in tiles) and
                            all(tile.color == tiles[0].color for tile in tiles) and
                            not any(pos in processed_positions for pos in positions)):
                            
                            matches.append(Match(positions, MatchType.CORNER))
                            processed_positions.update(positions)
        
        return matches
    
    def find_t_matches(self, processed_positions: Set[Tuple[int, int]]) -> List[Match]:
        """Find T-shaped matches"""
        matches = []
        
        # Define T patterns (relative positions) - All 4 orientations
        # Pattern: xxx
        #          oxo
        #          oxo
        t_patterns = [
            # T with horizontal top (xxx at top, vertical line down middle)
            [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],  # xxx at top, line down middle
            # T with horizontal bottom (xxx at bottom, vertical line up middle)  
            [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],  # line up middle, xxx at bottom
            # T with vertical left (xxx on left, horizontal line right middle)
            [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],  # xxx on left, line right middle
            # T with vertical right (xxx on right, horizontal line left middle)
            [(0, 2), (1, 0), (1, 1), (1, 2), (2, 2)],  # line left middle, xxx on right
        ]
        
        # Check all possible positions on the board
        for row in range(self.height):
            for col in range(self.width):
                for pattern in t_patterns:
                    positions = [(row + dr, col + dc) for dr, dc in pattern]
                    
                    # Check bounds
                    if all(0 <= r < self.height and 0 <= c < self.width for r, c in positions):
                        tiles = [self.grid[r][c] for r, c in positions]
                        
                        if (all(tile and not tile.is_empty() for tile in tiles) and
                            all(tile.color == tiles[0].color for tile in tiles) and
                            not any(pos in processed_positions for pos in positions)):
                            
                            matches.append(Match(positions, MatchType.T_SHAPE))
                            processed_positions.update(positions)
        
        return matches
    
    def clear_matches(self, match: Match):
        """Clear tiles from a match and potentially create special tiles"""
        # Determine if this match should create a special tile
        special_tile = self.tile_deck.get_special_tile_for_match(match.match_type)
        
        if special_tile:
            # Create special tile at the center of the match
            center_pos = self.get_match_center(match.positions)
            center_row, center_col = center_pos
            
            # Get the color from the matched tiles
            matched_color = None
            for row, col in match.positions:
                tile = self.grid[row][col]
                if tile and not tile.is_empty():
                    matched_color = tile.color
                    break
            
            # Clear matched tiles, but preserve special tiles
            for row, col in match.positions:
                tile = self.grid[row][col]
                if tile and tile.is_special():
                    # Don't clear special tiles - they should only be activated when triggered
                    continue
                self.grid[row][col] = None
            
            # Place the special tile at the center (only if center position is not a special tile)
            center_tile = self.grid[center_row][center_col]
            if not (center_tile and center_tile.is_special()):
                special_tile.color = matched_color
                self.grid[center_row][center_col] = Tile(matched_color, special_tile)
        else:
            # Regular match - clear tiles but preserve special tiles
            for row, col in match.positions:
                tile = self.grid[row][col]
                if tile and tile.is_special():
                    # Don't clear special tiles - they should only be activated when triggered
                    continue
                self.grid[row][col] = None
    
    def get_match_center(self, positions: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Get the center position of a match for placing special tiles"""
        if not positions:
            return (0, 0)
        
        # Calculate the centroid of the match
        avg_row = sum(pos[0] for pos in positions) / len(positions)
        avg_col = sum(pos[1] for pos in positions) / len(positions)
        
        # Find the position closest to the centroid
        center_pos = positions[0]
        min_distance = float('inf')
        
        for pos in positions:
            distance = ((pos[0] - avg_row) ** 2 + (pos[1] - avg_col) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                center_pos = pos
        
        return center_pos
    
    def apply_gravity(self):
        """Apply gravity to make tiles fall down"""
        for col in range(self.width):
            # Collect non-empty tiles from bottom to top
            tiles = []
            for row in range(self.height - 1, -1, -1):
                if self.grid[row][col] is not None:
                    tiles.append(self.grid[row][col])
                self.grid[row][col] = None
            
            # Place tiles from bottom up
            for i, tile in enumerate(tiles):
                self.grid[self.height - 1 - i][col] = tile
    
    def apply_gravity_with_animation_data(self):
        """Apply gravity and return data for animations"""
        fall_data = {}
        
        for col in range(self.width):
            fall_data[col] = []
            
            # Collect non-empty tiles with their current positions
            tiles_with_positions = []
            for row in range(self.height - 1, -1, -1):
                if self.grid[row][col] is not None:
                    tiles_with_positions.append((row, self.grid[row][col]))
                self.grid[row][col] = None
            
            # Place tiles from bottom up and record movements
            for i, (original_row, tile) in enumerate(tiles_with_positions):
                new_row = self.height - 1 - i
                
                if original_row != new_row:
                    fall_data[col].append({
                        'from_row': original_row,
                        'to_row': new_row,
                        'tile': tile
                    })
                
                self.grid[new_row][col] = tile
        
        return fall_data
    
    def fill_empty_spaces(self):
        """Fill empty spaces with new random tiles"""
        for col in range(self.width):
            for row in range(self.height):
                if self.grid[row][col] is None:
                    color = random.choice(self.available_colors)
                    self.grid[row][col] = Tile(color)
    
    def fill_empty_spaces_with_fall_data(self):
        """Fill empty spaces with new random tiles marked for animation"""
        for col in range(self.width):
            for row in range(self.height):
                if self.grid[row][col] is None:
                    color = random.choice(self.available_colors)
                    tile = Tile(color)
                    tile.newly_spawned = True  # Mark for animation
                    self.grid[row][col] = tile
    
    def has_possible_moves(self) -> bool:
        """Check if there are any possible moves on the board"""
        # Try swapping each adjacent pair and check for matches
        for row in range(self.height):
            for col in range(self.width):
                # Check right neighbor
                if col < self.width - 1:
                    self.swap_tiles((row, col), (row, col + 1))
                    if self.find_all_matches():
                        self.swap_tiles((row, col), (row, col + 1))  # Swap back
                        return True
                    self.swap_tiles((row, col), (row, col + 1))  # Swap back
                
                # Check bottom neighbor
                if row < self.height - 1:
                    self.swap_tiles((row, col), (row + 1, col))
                    if self.find_all_matches():
                        self.swap_tiles((row, col), (row + 1, col))  # Swap back
                        return True
                    self.swap_tiles((row, col), (row + 1, col))  # Swap back
        
        return False
    
    def shuffle(self):
        """Shuffle the board when no moves are available"""
        # Collect all tiles
        tiles = []
        for row in range(self.height):
            for col in range(self.width):
                if self.grid[row][col]:
                    tiles.append(self.grid[row][col])
        
        # Shuffle tiles
        random.shuffle(tiles)
        
        # Place shuffled tiles back ensuring no initial matches
        tile_index = 0
        for row in range(self.height):
            for col in range(self.width):
                if tile_index < len(tiles):
                    # Try to place tile without creating immediate matches
                    valid_colors = self.get_valid_colors_for_position(row, col)
                    
                    # Find a tile with valid color
                    placed = False
                    for i in range(tile_index, len(tiles)):
                        if tiles[i].color in valid_colors:
                            # Swap this tile to current position
                            tiles[tile_index], tiles[i] = tiles[i], tiles[tile_index]
                            self.grid[row][col] = tiles[tile_index]
                            tile_index += 1
                            placed = True
                            break
                    
                    if not placed:
                        # If no valid tile found, place any tile
                        self.grid[row][col] = tiles[tile_index]
                        tile_index += 1
                else:
                    self.grid[row][col] = None
    
    def activate_special_tile(self, row: int, col: int) -> tuple:
        """Activate a special tile and return (affected_positions, activated_tiles)"""
        tile = self.get_tile(row, col)
        if not tile or not tile.is_special():
            return [], []
        
        # Track all activated special tiles for particle effects
        activated_tiles = [(row, col, tile.special_tile)]
        
        # Get positions affected by the special tile
        affected_positions = tile.special_tile.get_affected_positions(self, (row, col))
        
        # First, collect special tiles that will be chain-detonated (before clearing)
        chain_reactions = []
        for pos_row, pos_col in affected_positions:
            if 0 <= pos_row < self.height and 0 <= pos_col < self.width:
                # Check if there are other special tiles in the affected area
                affected_tile = self.get_tile(pos_row, pos_col)
                if affected_tile and affected_tile.is_special() and (pos_row, pos_col) != (row, col):
                    # Store the special tile for chain reaction
                    chain_reactions.append((pos_row, pos_col, affected_tile.special_tile))
        
        # Clear the original special tile first
        self.grid[row][col] = None
        
        # Clear all affected positions (except special tiles that will chain)
        for pos_row, pos_col in affected_positions:
            if 0 <= pos_row < self.height and 0 <= pos_col < self.width:
                # Don't clear special tiles yet - they need to detonate first
                affected_tile = self.get_tile(pos_row, pos_col)
                if not (affected_tile and affected_tile.is_special()):
                    self.grid[pos_row][pos_col] = None
        
        # Handle chain reactions - special tiles detonate instead of being destroyed
        all_affected = affected_positions.copy()
        for chain_row, chain_col, special_tile in chain_reactions:
            # Recursively activate the special tile (it will detonate)
            chain_positions, chain_activated = self.activate_special_tile(chain_row, chain_col)
            all_affected.extend(chain_positions)
            activated_tiles.extend(chain_activated)
        
        return list(set(all_affected)), activated_tiles  # Remove duplicates from affected positions
    
    def check_for_special_tile_matches(self, row: int, col: int) -> bool:
        """Check if a position contains a special tile that should be activated"""
        tile = self.get_tile(row, col)
        return tile is not None and tile.is_special()
    
    def check_for_combo(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> Optional['SpecialTile']:
        """Check if swapping two special tiles creates a combo"""
        # Import here to avoid circular imports
        from special_tiles import SpecialTile, SpecialTileType, create_special_tile
        
        tile1 = self.get_tile(*pos1)
        tile2 = self.get_tile(*pos2)
        
        # Both tiles must be special to create a combo
        if not (tile1 and tile1.is_special() and tile2 and tile2.is_special()):
            return None
        
        special1 = tile1.special_tile
        special2 = tile2.special_tile
        
        # Get the types of the special tiles
        type1 = special1.tile_type
        type2 = special2.tile_type
        
        # Check for specific combinations
        combo_map = {
            # Bomb + Rocket combinations
            frozenset([SpecialTileType.BOMB, SpecialTileType.ROCKET_HORIZONTAL]): SpecialTileType.BOMB_ROCKET,
            frozenset([SpecialTileType.BOMB, SpecialTileType.ROCKET_VERTICAL]): SpecialTileType.BOMB_ROCKET,
            
            # Bomb + Board Wipe combination
            frozenset([SpecialTileType.BOMB, SpecialTileType.BOARD_WIPE]): SpecialTileType.BOMB_BOARDWIPE,
            
            # Bomb + Bomb = Mega Bomb
            frozenset([SpecialTileType.BOMB, SpecialTileType.BOMB]): SpecialTileType.MEGA_BOMB,
            
            # Lightning + Bomb = Energized Bomb
            frozenset([SpecialTileType.LIGHTNING, SpecialTileType.BOMB]): SpecialTileType.ENERGIZED_BOMB,
            
            # Lightning + Lightning = Lightning Cross
            frozenset([SpecialTileType.LIGHTNING, SpecialTileType.LIGHTNING]): SpecialTileType.LIGHTNING_CROSS,
            
            # Rocket + Rocket = Simple Cross (1x1 cross)
            frozenset([SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.ROCKET_VERTICAL]): SpecialTileType.SIMPLE_CROSS,
            

            
            # Rocket + Board Wipe combination
            frozenset([SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.BOARD_WIPE]): SpecialTileType.ROCKET_BOARDWIPE,
            frozenset([SpecialTileType.ROCKET_VERTICAL, SpecialTileType.BOARD_WIPE]): SpecialTileType.ROCKET_BOARDWIPE,
            
            # Rocket + Lightning combination
            frozenset([SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.LIGHTNING]): SpecialTileType.ROCKET_LIGHTNING,
            frozenset([SpecialTileType.ROCKET_VERTICAL, SpecialTileType.LIGHTNING]): SpecialTileType.ROCKET_LIGHTNING,
            
            # Boardwipe + Boardwipe = Reality Break
            frozenset([SpecialTileType.BOARD_WIPE, SpecialTileType.BOARD_WIPE]): SpecialTileType.REALITY_BREAK,
        }
        
        # Check for same-type rocket combinations first
        if type1 == type2:
            if type1 in [SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.ROCKET_VERTICAL]:
                # Same-type rockets create simple cross
                color = special1.color if special1.color else special2.color
                return create_special_tile(SpecialTileType.SIMPLE_CROSS, color=color)
        
        # Create a set of the two tile types
        type_set = frozenset([type1, type2])
        
        # Check if this combination exists in our combo map
        combo_type = combo_map.get(type_set)
        if combo_type:
            # Use the color of the first tile
            color = special1.color if special1.color else special2.color
            return create_special_tile(combo_type, color=color)
        
        return None
    
    def get_special_tile_position(self, match: 'Match') -> Optional[Tuple[int, int]]:
        """Get the position where a special tile will be created for a match"""
        from special_tiles import SpecialTileType
        
        # Determine what type of special tile this match would create
        if match.match_type == MatchType.FOUR:
            # 4-match creates rocket at center
            return self.get_match_center(match.positions)
        elif match.match_type == MatchType.FIVE:
            # 5-match creates lightning at center  
            return self.get_match_center(match.positions)
        elif match.match_type in [MatchType.SQUARE, MatchType.CORNER]:
            # Square/corner creates bomb at center
            return self.get_match_center(match.positions)
        elif match.match_type == MatchType.T_SHAPE:
            # T-shape creates board wipe at center
            return self.get_match_center(match.positions)
        
        return None  # No special tile for 3-matches