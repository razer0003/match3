# Match 3 Game

A complete Match 3 tile-matching game built with Python and Pygame featuring smooth animations, multiple match types, and engaging gameplay.

## Features

- **Multiple Match Types**: 3-match, 4-match, 5-match, square match, corner match, and T-match patterns
- **Smooth Animations**: Falling tiles, swapping animations, and particle effects
- **Smart Tile Generation**: New tiles fall randomly from the top
- **Auto-Shuffle**: Board automatically shuffles when no valid moves are available
- **Combo System**: Score multiplier increases with consecutive matches
- **Responsive Design**: Game board scales based on level configuration
- **Five Tile Colors**: Red, Green, Blue, Yellow, and Orange tiles

## Game Mechanics

### Match Types and Scoring
- **3-Match**: 100 points × combo multiplier
- **4-Match**: 400 points × combo multiplier  
- **5-Match**: 1000 points × combo multiplier
- **Square Match**: 800 points × combo multiplier (2×2 square of same color)
- **Corner Match**: 600 points × combo multiplier (L-shaped pattern)
- **T-Match**: 800 points × combo multiplier (T-shaped pattern)

### Gameplay
1. Click on a tile to select it (highlighted with white border)
2. Click on an adjacent tile to swap them
3. Valid swaps create matches that are automatically cleared
4. Invalid swaps revert back to original positions
5. New tiles fall from the top to fill empty spaces
6. Chain reactions increase your combo multiplier
7. Board shuffles automatically when no moves are available

## Level Configuration

- **Level 1**: Takes up approximately half of the 1080p screen space
- Board size: 8×9 tiles
- Tile size: 60 pixels
- Centered on screen for optimal visibility

## Installation and Running

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup
1. Clone or download the game files to your local machine
2. Navigate to the game directory in your terminal/command prompt
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Game
Execute the main game file:
```
python match3_game.py
```

## Controls
- **Mouse Click**: Select and swap tiles
- **ESC/Close Window**: Exit the game

## File Structure
```
match3/
├── match3_game.py      # Main game loop and logic
├── board.py            # Board management and match detection
├── animations.py       # Animation system for smooth visuals
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Technical Details

### Architecture
- **Object-Oriented Design**: Modular classes for game components
- **Animation System**: Smooth interpolation for all movements
- **Match Detection**: Comprehensive pattern recognition for all match types
- **State Management**: Clean separation of game logic and visual representation

### Performance
- Optimized for 60 FPS gameplay
- Efficient match detection algorithms
- Minimal memory footprint
- Responsive input handling

## Customization

The game is designed to be easily customizable:

- **Add new levels**: Modify the `configure_level()` method in `match3_game.py`
- **Change colors**: Update the `TileColor` enum in `board.py`
- **Adjust animations**: Modify timing and easing functions in `animations.py`
- **Scoring system**: Update match scores in the `Match` class

## Future Enhancements

Potential additions to consider:
- Power-up tiles and special effects
- Multiple levels with different board sizes
- Sound effects and background music
- High score tracking and persistence
- Tournament mode with time limits
- Online multiplayer capabilities

Enjoy playing this Match 3 game!