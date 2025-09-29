import random
from typing import List, Optional, Set, Tuple
from enum import Enum

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
    
    def __init__(self, color: TileColor):
        self.color = color
        self.falling = False
        self.fall_speed = 0
        self.target_row = 0
        self.current_y = 0
    
    def __repr__(self):
        return f"Tile({self.color.name})"
    
    def is_empty(self):
        return self.color == TileColor.EMPTY
    
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
        self.available_colors = [TileColor.RED, TileColor.GREEN, TileColor.BLUE, 
                               TileColor.YELLOW, TileColor.ORANGE]
    
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
        
        # Define corner patterns (relative positions) - More comprehensive L-shapes
        corner_patterns = [
            # 3x3 L-shapes (5 tiles each)
            [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],  # Top-left L
            [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],  # Top-right L
            [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],  # Bottom-left L
            [(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)],  # Bottom-right L
            
            # Smaller L-shapes (4 tiles each)
            [(0, 0), (0, 1), (1, 0), (2, 0)],          # Small top-left L
            [(0, 0), (0, 1), (1, 1), (2, 1)],          # Small top-right L
            [(0, 0), (1, 0), (2, 0), (2, 1)],          # Small bottom-left L
            [(0, 1), (1, 1), (2, 1), (2, 0)],          # Small bottom-right L
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
        t_patterns = [
            # T pointing up
            [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
            # T pointing down
            [(0, 1), (1, 0), (1, 1), (1, 2), (-1, 1)],
            # T pointing left
            [(0, 1), (1, 0), (1, 1), (1, 2), (1, -1)],
            # T pointing right
            [(0, 1), (1, 0), (1, 1), (1, 2), (1, 3)],
            
            # Smaller T patterns (4 tiles)
            [(0, 0), (0, 1), (0, 2), (1, 1)],         # T up
            [(0, 1), (1, 0), (1, 1), (1, 2)],         # T down
            [(0, 0), (1, 0), (2, 0), (1, 1)],         # T right
            [(0, 1), (1, 0), (1, 1), (2, 1)],         # T left
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
        """Clear tiles from a match"""
        for row, col in match.positions:
            self.grid[row][col] = None
    
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