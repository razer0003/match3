#!/usr/bin/env python3
"""
Debug script for special tile creation
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from board import Board, TileColor, MatchType, Tile
from special_tiles import TileDeck

def test_four_match_creation():
    """Test if 4-matches create special tiles"""
    print("Testing 4-Match Special Tile Creation...")
    board = Board(8, 8, 60)
    board.generate_initial_board()
    
    # Clear the board
    for row in range(8):
        for col in range(8):
            board.set_tile(row, col, None)
    
    # Create a horizontal 4-match
    four_match_positions = [(2, 1), (2, 2), (2, 3), (2, 4)]
    for row, col in four_match_positions:
        board.set_tile(row, col, Tile(TileColor.RED))
    
    # Fill other positions with different colors
    for row in range(8):
        for col in range(8):
            if (row, col) not in four_match_positions and board.get_tile(row, col) is None:
                board.set_tile(row, col, Tile(TileColor.BLUE))
    
    # Find matches
    matches = board.find_all_matches()
    print(f"Found {len(matches)} matches")
    
    for i, match in enumerate(matches):
        print(f"Match {i+1}: Type = {match.match_type}, Positions = {match.positions}")
        
        # Test special tile creation
        deck = TileDeck()
        special_tile = deck.get_special_tile_for_match(match.match_type, TileColor.RED)
        
        if special_tile:
            print(f"  -> Creates special tile: {special_tile.tile_type}")
        else:
            print(f"  -> No special tile created")
    
    return len(matches) > 0

def test_match_types():
    """Test all match types for special tile creation"""
    print("\nTesting All Match Types...")
    deck = TileDeck()
    
    test_cases = [
        (MatchType.THREE, "3-match"),
        (MatchType.FOUR, "4-match"),
        (MatchType.FIVE, "5-match"),
        (MatchType.CORNER, "Corner match"),
        (MatchType.T_SHAPE, "T-match"),
        (MatchType.SQUARE, "Square match")
    ]
    
    for match_type, description in test_cases:
        special_tile = deck.get_special_tile_for_match(match_type, TileColor.RED)
        if special_tile:
            print(f"{description} -> {special_tile.tile_type.name}")
        else:
            print(f"{description} -> No special tile")

if __name__ == "__main__":
    four_match_ok = test_four_match_creation()
    test_match_types()
    
    if four_match_ok:
        print("\n✓ 4-match detection working")
    else:
        print("\n✗ 4-match detection failed")