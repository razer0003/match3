#!/usr/bin/env python3
"""
Test script to verify Match 3 game functionality
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from board import Board, TileColor, MatchType
    print("✓ Board module imported successfully")
    
    # Test board creation
    board = Board(8, 9, 60)
    board.generate_initial_board()
    print("✓ Board created and initialized")
    
    # Test match detection
    matches = board.find_all_matches()
    print(f"✓ Match detection works - found {len(matches)} initial matches")
    
    # Test tile access
    tile = board.get_tile(0, 0)
    if tile:
        print(f"✓ Tile access works - tile color: {tile.color.name}")
    
    # Test possible moves
    has_moves = board.has_possible_moves()
    print(f"✓ Move detection works - has possible moves: {has_moves}")
    
    print("\n=== Board Test Complete ===")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error during testing: {e}")
    sys.exit(1)

try:
    from animations import FallAnimation, SwapAnimation, PulseAnimation
    print("✓ Animation module imported successfully")
    
    # Test animation creation
    fall_anim = FallAnimation(0, 100, 1.0)
    print("✓ Fall animation created")
    
    swap_anim = SwapAnimation((0, 0), (60, 0), 0.5)
    print("✓ Swap animation created")
    
    pulse_anim = PulseAnimation(1.0)
    print("✓ Pulse animation created")
    
    print("\n=== Animation Test Complete ===")
    
except ImportError as e:
    print(f"✗ Animation import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Animation error during testing: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! The game should run correctly.")
print("To start the game, run: python match3_game.py")