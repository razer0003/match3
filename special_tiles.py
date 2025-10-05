import random
from enum import Enum
from typing import List, Tuple, Optional, Set
from abc import ABC, abstractmethod

class SpecialTileType(Enum):
    """Types of special tiles"""
    ROCKET_HORIZONTAL = "rocket_horizontal"
    ROCKET_VERTICAL = "rocket_vertical"
    BOARD_WIPE = "board_wipe"
    BOMB = "bomb"
    LIGHTNING = "lightning"
    # Combo tiles
    BOMB_ROCKET = "bomb_rocket"
    BOMB_BOARDWIPE = "bomb_boardwipe"
    MEGA_BOMB = "mega_bomb"
    ENERGIZED_BOMB = "energized_bomb"
    # Rocket combo tiles
    ROCKET_BOARDWIPE = "rocket_boardwipe"
    ROCKET_LIGHTNING = "rocket_lightning"
    SIMPLE_CROSS = "simple_cross"  # For rocket+rocket combinations
    LIGHTNING_CROSS = "lightning_cross"  # For lightning+lightning combinations
    REALITY_BREAK = "reality_break"  # For boardwipe+boardwipe combinations

class SpecialTile(ABC):
    """Base class for all special tiles"""
    
    def __init__(self, tile_type: SpecialTileType, color=None):
        self.tile_type = tile_type
        self.color = color  # Some special tiles might retain the color of the match
        self.is_special = True
    
    @abstractmethod
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions that will be affected when this special tile is activated"""
        pass
    
    @abstractmethod
    def get_visual_representation(self) -> dict:
        """Get visual data for rendering this special tile"""
        pass
    
    def can_be_swapped(self) -> bool:
        """Whether this special tile can be swapped with regular tiles"""
        return True
    
    def get_score_bonus(self) -> int:
        """Score bonus for creating this special tile"""
        return 500

class RocketTile(SpecialTile):
    """Rocket that clears an entire row or column"""
    
    def __init__(self, is_horizontal: bool = True, color=None):
        tile_type = SpecialTileType.ROCKET_HORIZONTAL if is_horizontal else SpecialTileType.ROCKET_VERTICAL
        super().__init__(tile_type, color)
        self.is_horizontal = is_horizontal
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions in the rocket's path"""
        row, col = activation_pos
        positions = []
        
        if self.is_horizontal:
            # Clear entire row
            for c in range(board.width):
                positions.append((row, c))
        else:
            # Clear entire column
            for r in range(board.height):
                positions.append((r, col))
        
        return positions
    
    def get_visual_representation(self) -> dict:
        """Visual data for the rocket"""
        if self.is_horizontal:
            return {
                'sprite_type': 'rocket',
                'symbol': 'R',
                'color': (255, 255, 255),
                'background_color': (255, 69, 0),  # Red-orange for horizontal rocket
                'effect_color': (255, 140, 0)
            }
        else:
            return {
                'sprite_type': 'rocket',
                'symbol': 'R',
                'color': (255, 255, 255),
                'background_color': (30, 144, 255),  # Dodger blue for vertical rocket
                'effect_color': (0, 191, 255)
            }

class BoardWipeTile(SpecialTile):
    """Board wipe that clears all tiles of a specific color"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.BOARD_WIPE, color)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions with the same color as the target"""
        row, col = activation_pos
        target_tile = board.get_tile(row, col)
        
        if not target_tile or target_tile.is_empty():
            return []
        
        positions = []
        target_color = target_tile.color
        
        # Find all tiles with the same color
        for r in range(board.height):
            for c in range(board.width):
                tile = board.get_tile(r, c)
                if tile and not tile.is_empty() and tile.color == target_color:
                    positions.append((r, c))
        
        return positions
    
    def get_visual_representation(self) -> dict:
        """Visual data for the board wipe"""
        return {
            'sprite_type': 'boardwipe',
            'symbol': 'W',
            'color': (255, 255, 255),
            'background_color': (128, 0, 128),  # Purple for board wipe
            'effect_color': (255, 0, 255)  # Magenta effect
        }
    
    def get_score_bonus(self) -> int:
        return 2000

class BombTile(SpecialTile):
    """Bomb that explodes in a 5x5 radius"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.BOMB, color)
        self.radius = 2  # 5x5 area (2 tiles in each direction)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions in the bomb's explosion radius"""
        row, col = activation_pos
        positions = []
        
        for r in range(max(0, row - self.radius), min(board.height, row + self.radius + 1)):
            for c in range(max(0, col - self.radius), min(board.width, col + self.radius + 1)):
                positions.append((r, c))
        
        return positions
    
    def get_visual_representation(self) -> dict:
        """Visual data for the bomb"""
        return {
            'sprite_type': 'bomb',
            'symbol': 'B',
            'color': (255, 255, 255),
            'background_color': (64, 64, 64),  # Dark gray for bomb
            'effect_color': (255, 69, 0)  # Orange-red explosion effect
        }
    
    def get_score_bonus(self) -> int:
        return 1000

class LightningTile(SpecialTile):
    """Lightning that strikes in an arc pattern"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.LIGHTNING, color)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions in the lightning arc pattern"""
        row, col = activation_pos
        positions = []
        
        # Lightning arc pattern - creates a zigzag pattern
        # Main strike (vertical line)
        for r in range(board.height):
            positions.append((r, col))
        
        # Arc branches (diagonal patterns)
        for offset in range(1, 3):  # 2 branches on each side
            # Left diagonal branch
            if col - offset >= 0:
                for r in range(max(0, row - offset), min(board.height, row + offset + 1)):
                    positions.append((r, col - offset))
            
            # Right diagonal branch
            if col + offset < board.width:
                for r in range(max(0, row - offset), min(board.height, row + offset + 1)):
                    positions.append((r, col + offset))
        
        # Remove duplicates
        return list(set(positions))
    
    def get_visual_representation(self) -> dict:
        """Visual data for the lightning"""
        return {
            'sprite_type': 'lightning',
            'symbol': 'L',
            'color': (255, 255, 255),
            'background_color': (25, 25, 112),  # Midnight blue for lightning
            'effect_color': (255, 255, 0)  # Bright yellow lightning effect
        }
    
    def get_score_bonus(self) -> int:
        return 800

class TileDeck:
    """Manages which special tiles are created for different match types"""
    
    def __init__(self):
        # Default deck configuration
        self.deck_config = {
            'four_match': [RocketTile],
            'five_match': [BoardWipeTile],
            'corner_match': [BombTile],
            't_match': [BombTile],
            'square_match': [LightningTile]
        }
        
        # Deck building will allow players to customize these mappings
        self.player_deck = self.deck_config.copy()
    
    def get_special_tile_for_match(self, match_type, match_color=None) -> Optional[SpecialTile]:
        """Get the appropriate special tile for a match type"""
        
        # Check by both value and name to handle different enum instances
        if (hasattr(match_type, 'value') and match_type.value == 4) or (hasattr(match_type, 'name') and match_type.name == 'FOUR'):
            # 50/50 chance for horizontal or vertical rocket
            is_horizontal = random.choice([True, False])
            return RocketTile(is_horizontal, match_color)
        
        elif (hasattr(match_type, 'value') and match_type.value == 5) or (hasattr(match_type, 'name') and match_type.name == 'FIVE'):
            return BoardWipeTile(match_color)
        
        elif hasattr(match_type, 'name') and match_type.name == 'CORNER':
            return BombTile(match_color)
        
        elif hasattr(match_type, 'name') and match_type.name == 'T_SHAPE':
            return BombTile(match_color)
        
        elif hasattr(match_type, 'name') and match_type.name == 'SQUARE':
            return LightningTile(match_color)
        
        return None
    
    def set_deck_configuration(self, match_type: str, special_tile_classes: List):
        """Allow players to customize their deck (for future deck building)"""
        self.player_deck[match_type] = special_tile_classes
    
    def get_available_special_tiles(self) -> List:
        """Get all available special tile types for deck building"""
        return [RocketTile, BoardWipeTile, BombTile, LightningTile]

# Factory function for creating special tiles
class BombRocketTile(SpecialTile):
    """Bomb + Rocket combo - destroys 3-wide cross pattern across entire board"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.BOMB_ROCKET, color)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get 3-wide cross pattern extending across entire board"""
        row, col = activation_pos
        positions = []
        
        # Horizontal 3-wide stripe (entire width of board)
        for c in range(board.width):
            for r_offset in [-1, 0, 1]:  # 3 rows tall
                target_row = row + r_offset
                if 0 <= target_row < board.height:
                    positions.append((target_row, c))
        
        # Vertical 3-wide stripe (entire height of board)
        for r in range(board.height):
            for c_offset in [-1, 0, 1]:  # 3 columns wide
                target_col = col + c_offset
                if 0 <= target_col < board.width:
                    positions.append((r, target_col))
        
        # Remove duplicates (center area will overlap)
        return list(set(positions))
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'bomb',  # Use bomb sprite for now
            'symbol': 'BR',
            'color': (255, 255, 255),
            'background_color': (255, 165, 0),  # Orange
            'effect_color': (255, 69, 0)
        }
    
    def get_score_bonus(self) -> int:
        return 2500

class BombBoardwipeTile(SpecialTile):
    """Bomb + Boardwipe combo - places random bombs then detonates all"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.BOMB_BOARDWIPE, color)
        self.requires_special_handling = True  # Flag for game to handle specially
    
    def get_bomb_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get positions where bombs should be placed"""
        total_tiles = board.width * board.height
        num_bombs = max(1, int(total_tiles * 0.15))  # 15% of board
        
        # Get all non-special tile positions (excluding activation position)
        available_positions = []
        for r in range(board.height):
            for c in range(board.width):
                if (r, c) == activation_pos:
                    continue  # Skip activation position
                tile = board.get_tile(r, c)
                if tile and not tile.is_special():
                    available_positions.append((r, c))
        
        # Randomly select positions for bombs
        if available_positions:
            bomb_positions = random.sample(available_positions, min(num_bombs, len(available_positions)))
            return bomb_positions
        return []
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """This shouldn't be called for bomb-boardwipe, but return activation pos as fallback"""
        return [activation_pos]
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'boardwipe',  # Use boardwipe sprite for now
            'symbol': 'BW',
            'color': (255, 255, 255),
            'background_color': (128, 0, 128),  # Purple
            'effect_color': (255, 0, 255)
        }
    
    def get_score_bonus(self) -> int:
        return 5000

class MegaBombTile(SpecialTile):
    """Mega Bomb - 7x7 explosion radius"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.MEGA_BOMB, color)
        self.radius = 3  # 7x7 area (3 tiles in each direction)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions in 7x7 area"""
        row, col = activation_pos
        positions = []
        
        for r in range(max(0, row - self.radius), min(board.height, row + self.radius + 1)):
            for c in range(max(0, col - self.radius), min(board.width, col + self.radius + 1)):
                positions.append((r, c))
        
        return positions
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'bomb',  # Use bomb sprite for now
            'symbol': 'MB',
            'color': (255, 255, 255),
            'background_color': (139, 0, 0),  # Dark red
            'effect_color': (255, 69, 0)
        }
    
    def get_score_bonus(self) -> int:
        return 3000

class EnergizedBombTile(SpecialTile):
    """Energized Bomb - 10x10 explosion radius"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.ENERGIZED_BOMB, color)
        self.radius = 5  # 10x10 area (5 tiles in each direction)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions in 10x10 area"""
        row, col = activation_pos
        positions = []
        
        for r in range(max(0, row - self.radius), min(board.height, row + self.radius + 1)):
            for c in range(max(0, col - self.radius), min(board.width, col + self.radius + 1)):
                positions.append((r, c))
        
        return positions
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'lightning',  # Use lightning sprite for now
            'symbol': 'EB',
            'color': (255, 255, 255),
            'background_color': (75, 0, 130),  # Indigo
            'effect_color': (255, 255, 0)
        }
    
    def get_score_bonus(self) -> int:
        return 4000

class RocketBoardwipeTile(SpecialTile):
    """Rocket + Boardwipe combo - places random rockets then detonates sequentially"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.ROCKET_BOARDWIPE, color)
        self.requires_special_handling = True  # Flag for game to handle specially
    
    def get_rocket_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get positions where rockets should be placed"""
        total_tiles = board.width * board.height
        num_rockets = max(1, int(total_tiles * 0.15))  # 15% of board
        
        # Get all non-special tile positions (excluding activation position)
        available_positions = []
        for r in range(board.height):
            for c in range(board.width):
                if (r, c) == activation_pos:
                    continue  # Skip activation position
                tile = board.get_tile(r, c)
                if tile and not tile.is_special():
                    available_positions.append((r, c))
        
        # Randomly select positions for rockets
        if available_positions:
            rocket_positions = random.sample(available_positions, min(num_rockets, len(available_positions)))
            return rocket_positions
        return []
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """This shouldn't be called for rocket-boardwipe, but return activation pos as fallback"""
        return [activation_pos]
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'rocket',  # Use rocket sprite for now
            'symbol': 'RW',
            'color': (255, 255, 255),
            'background_color': (255, 20, 147),  # Deep pink
            'effect_color': (255, 105, 180)
        }
    
    def get_score_bonus(self) -> int:
        return 4500

class RocketLightningTile(SpecialTile):
    """Rocket + Lightning combo - clears top row then cascades down"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.ROCKET_LIGHTNING, color)
        self.requires_special_handling = True  # Flag for game to handle specially
    
    def get_cascade_rows(self, board, activation_pos: Tuple[int, int]) -> List[int]:
        """Get rows to clear in cascade order (top to bottom)"""
        return list(range(board.height))  # All rows from 0 to bottom
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """This shouldn't be called for rocket-lightning, but return activation pos as fallback"""
        return [activation_pos]
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'lightning',  # Use lightning sprite for now
            'symbol': 'RL',
            'color': (255, 255, 255),
            'background_color': (255, 215, 0),  # Gold
            'effect_color': (255, 255, 0)
        }
    
    def get_score_bonus(self) -> int:
        return 3500

class SimpleCrossTile(SpecialTile):
    """Simple Cross - 1x1 cross pattern for rocket combinations"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.SIMPLE_CROSS, color)
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions in a simple cross pattern (1x1 wide)"""
        row, col = activation_pos
        positions = []
        
        # Center position
        positions.append((row, col))
        
        # Horizontal line (single width)
        for c in range(board.width):
            if c != col:
                positions.append((row, c))
        
        # Vertical line (single width)  
        for r in range(board.height):
            if r != row:
                positions.append((r, col))
        
        return positions
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'lightning',  # Use lightning sprite for now
            'symbol': 'X',
            'color': (255, 255, 255),
            'background_color': (100, 149, 237),  # Cornflower blue
            'effect_color': (135, 206, 250)
        }
    
    def get_score_bonus(self) -> int:
        return 2000

class LightningCrossTile(SpecialTile):
    """Lightning Cross - Creates cross pattern of lightning arcs across the board"""
    
    def __init__(self):
        super().__init__(SpecialTileType.LIGHTNING_CROSS)
        self.requires_special_handling = True
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all positions affected by the lightning cross (all 4 phases combined)"""
        positions = []
        
        # Phase 1: Top-left to bottom-right diagonal
        for i in range(min(board.height, board.width)):
            if i < board.height and i < board.width:
                positions.append((i, i))
        
        # Phase 2: Top-middle to bottom-middle (vertical)
        center_col = board.width // 2
        for row in range(board.height):
            positions.append((row, center_col))
        
        # Phase 3: Top-right to bottom-left diagonal
        for i in range(min(board.height, board.width)):
            if i < board.height and (board.width - 1 - i) >= 0:
                positions.append((i, board.width - 1 - i))
        
        # Phase 4: Middle-right to middle-left (horizontal)
        center_row = board.height // 2
        for col in range(board.width):
            positions.append((center_row, col))
        
        # Remove duplicates
        return list(set(positions))
    
    def get_visual_representation(self):
        """Return visual representation for lightning cross tile"""
        return {
            'symbol': '⚡',
            'color': (255, 255, 255),  # Bright white
            'background_color': (75, 0, 130),  # Indigo background
            'effect_color': (255, 255, 0)  # Bright yellow effect
        }
    
    def get_score_bonus(self) -> int:
        return 3000  # Higher score for dramatic cross lightning effect

class RealityBreakTile(SpecialTile):
    """Reality Break - Ultimate combo that breaks the 4th wall"""
    
    def __init__(self, color=None):
        super().__init__(SpecialTileType.REALITY_BREAK, color)
        self.requires_special_handling = True
    
    def get_affected_positions(self, board, activation_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reality Break affects the entire board and beyond"""
        positions = []
        # Affect all board positions
        for row in range(board.height):
            for col in range(board.width):
                positions.append((row, col))
        return positions
    
    def get_visual_representation(self) -> dict:
        return {
            'sprite_type': 'boardwipe',  # Use boardwipe sprite but with special effects
            'symbol': '∞',  # Infinity symbol for reality break
            'color': (255, 255, 255),
            'background_color': (0, 0, 0),  # Black background
            'effect_color': (255, 255, 255)  # White effect
        }
    
    def get_score_bonus(self) -> int:
        return 10000  # Massive score bonus for the ultimate combo!

def create_special_tile(tile_type: SpecialTileType, **kwargs) -> SpecialTile:
    """Factory function to create special tiles"""
    if tile_type in [SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.ROCKET_VERTICAL]:
        is_horizontal = tile_type == SpecialTileType.ROCKET_HORIZONTAL
        return RocketTile(is_horizontal, kwargs.get('color'))
    
    elif tile_type == SpecialTileType.BOARD_WIPE:
        return BoardWipeTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.BOMB:
        return BombTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.LIGHTNING:
        return LightningTile(kwargs.get('color'))
    
    # Combo tiles
    elif tile_type == SpecialTileType.BOMB_ROCKET:
        return BombRocketTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.BOMB_BOARDWIPE:
        return BombBoardwipeTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.MEGA_BOMB:
        return MegaBombTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.ENERGIZED_BOMB:
        return EnergizedBombTile(kwargs.get('color'))
    
    # Rocket combo tiles
    elif tile_type == SpecialTileType.ROCKET_BOARDWIPE:
        return RocketBoardwipeTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.ROCKET_LIGHTNING:
        return RocketLightningTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.SIMPLE_CROSS:
        return SimpleCrossTile(kwargs.get('color'))
    
    elif tile_type == SpecialTileType.LIGHTNING_CROSS:
        return LightningCrossTile()
    
    elif tile_type == SpecialTileType.REALITY_BREAK:
        return RealityBreakTile(kwargs.get('color'))
    
    raise ValueError(f"Unknown special tile type: {tile_type}")