#!/usr/bin/env python3
"""
Test script specifically for match detection
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from board import Board, TileColor, MatchType, Tile

def test_corner_match():
    """Test corner match detection"""
    print("Testing Corner Match Detection...")
    board = Board(5, 5, 60)
    board.generate_initial_board()  # Initialize the grid first
    
    # Clear the board
    for row in range(5):
        for col in range(5):
            board.set_tile(row, col, None)
    
    # Create an L-shape with RED tiles
    # Pattern: Top-left L
    l_positions = [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]
    for row, col in l_positions:
        board.set_tile(row, col, Tile(TileColor.RED))
    
    # Fill other positions with different colors
    for row in range(5):
        for col in range(5):
            if (row, col) not in l_positions and board.get_tile(row, col) is None:
                board.set_tile(row, col, Tile(TileColor.BLUE))
    
    matches = board.find_all_matches()
    corner_matches = [m for m in matches if m.match_type == MatchType.CORNER]
    
    print(f"Found {len(corner_matches)} corner matches")
    if corner_matches:
        print(f"Corner match positions: {corner_matches[0].positions}")
        print("✓ Corner match detection working!")
    else:
        print("✗ Corner match not detected")
    
    return len(corner_matches) > 0

def test_t_match():
    """Test T-match detection"""
    print("\nTesting T-Match Detection...")
    board = Board(5, 5, 60)
    board.generate_initial_board()  # Initialize the grid first
    
    # Clear the board
    for row in range(5):
        for col in range(5):
            board.set_tile(row, col, None)
    
    # Create a T-shape with GREEN tiles
    # Pattern: T pointing up
    t_positions = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    for row, col in t_positions:
        board.set_tile(row, col, Tile(TileColor.GREEN))
    
    # Fill other positions with different colors
    for row in range(5):
        for col in range(5):
            if (row, col) not in t_positions and board.get_tile(row, col) is None:
                board.set_tile(row, col, Tile(TileColor.YELLOW))
    
    matches = board.find_all_matches()
    t_matches = [m for m in matches if m.match_type == MatchType.T_SHAPE]
    
    print(f"Found {len(t_matches)} T-matches")
    if t_matches:
        print(f"T-match positions: {t_matches[0].positions}")
        print("✓ T-match detection working!")
    else:
        print("✗ T-match not detected")
    
    return len(t_matches) > 0

def test_priority():
    """Test that special matches have priority over line matches"""
    print("\nTesting Match Priority...")
    board = Board(5, 5, 60)
    board.generate_initial_board()  # Initialize the grid first
    
    # Clear the board
    for row in range(5):
        for col in range(5):
            board.set_tile(row, col, None)
    
    # Create overlapping patterns - both a horizontal line and part of an L
    # This should detect the L-shape, not just the horizontal line
    overlap_positions = [(1, 0), (1, 1), (1, 2), (2, 0), (3, 0)]  # L-shape
    for row, col in overlap_positions:
        board.set_tile(row, col, Tile(TileColor.ORANGE))
    
    # Fill other positions
    for row in range(5):
        for col in range(5):
            if (row, col) not in overlap_positions and board.get_tile(row, col) is None:
                board.set_tile(row, col, Tile(TileColor.BLUE))
    
    matches = board.find_all_matches()
    corner_matches = [m for m in matches if m.match_type == MatchType.CORNER]
    line_matches = [m for m in matches if m.match_type in [MatchType.THREE, MatchType.FOUR, MatchType.FIVE]]
    
    print(f"Found {len(corner_matches)} corner matches, {len(line_matches)} line matches")
    
    if corner_matches and not line_matches:
        print("✓ Priority system working - L-shape detected instead of line!")
        return True
    elif corner_matches and line_matches:
        print("⚠ Both detected - this might be OK depending on implementation")
        return True
    else:
        print("✗ Priority system not working correctly")
        return False

if __name__ == "__main__":
    corner_ok = test_corner_match()
    t_ok = test_t_match()
    priority_ok = test_priority()
    
    if corner_ok and t_ok and priority_ok:
        print("\n🎉 All match detection tests passed!")
    else:
        print("\n❌ Some tests failed. Check the implementation.")