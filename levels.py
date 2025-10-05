"""
Level configuration system for Match 3 game
Defines different levels with varying board sizes and parameters
"""

from typing import Dict, Tuple

class LevelConfig:
    """Configuration for a single level"""
    
    def __init__(self, level: int, width: int, height: int, tile_size: int = 60, name: str = "", dual_board: bool = False):
        self.level = level
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.name = name or f"Level {level}"
        self.dual_board = dual_board  # True for VS levels with two boards
    
    def get_board_pixel_size(self) -> Tuple[int, int]:
        """Get total board size in pixels"""
        return (self.width * self.tile_size, self.height * self.tile_size)

# Level definitions
LEVELS = {
    1: LevelConfig(
        level=1,
        width=8,
        height=9,
        tile_size=60,
        name="Level 1 - Classic"
    ),
    2: LevelConfig(
        level=2,
        width=6,
        height=7,  # 2 less than level 1
        tile_size=60,
        name="Level 2 - Compact"
    ),
    3: LevelConfig(
        level=3,
        width=10,
        height=11,  # 2 more than level 1
        tile_size=50,  # Slightly smaller tiles to fit on screen
        name="Level 3 - Mega Board"
    ),
    4: LevelConfig(
        level=4,
        width=7,
        height=8,  # Smaller boards to fit two side by side
        tile_size=45,  # Smaller tiles for dual board layout
        name="Level 4 - VS Boss",
        dual_board=True
    )
}

def get_level_config(level: int) -> LevelConfig:
    """Get configuration for specified level"""
    if level not in LEVELS:
        raise ValueError(f"Level {level} not found. Available levels: {list(LEVELS.keys())}")
    return LEVELS[level]

def get_available_levels() -> list:
    """Get list of all available level numbers"""
    return sorted(LEVELS.keys())