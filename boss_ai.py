"""
Advanced AI system for Match 3 Boss Board
Configurable difficulty with strategic thinking and lookahead capabilities
"""

import random
import copy
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
from board import Board, TileColor, Match, MatchType
from special_tiles import SpecialTileType

class AIDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    NIGHTMARE = "nightmare"

class AIConfig:
    """Configuration for AI behavior and difficulty"""
    
    def __init__(self, difficulty: AIDifficulty = AIDifficulty.MEDIUM):
        self.difficulty = difficulty
        
        # Base configuration based on difficulty
        if difficulty == AIDifficulty.EASY:
            self.move_delay = 0.5  # Reduced for normal game speed
            self.thinking_depth = 2  # How many moves to look ahead
            self.special_tile_awareness = 0.3  # How much to prioritize special tiles
            self.combo_planning = 0.2  # How much to plan combos
            self.mistake_chance = 0.15  # Chance to make suboptimal moves
            self.reaction_speed = 0.8  # Speed of reacting to cascades
        elif difficulty == AIDifficulty.MEDIUM:
            self.move_delay = 0.3  # Reduced for normal game speed
            self.thinking_depth = 3  # Restored - using background threading now
            self.special_tile_awareness = 1.2  # Increased to prioritize special tiles more
            self.combo_planning = 0.5
            self.mistake_chance = 0.08
            self.reaction_speed = 0.6
        elif difficulty == AIDifficulty.HARD:
            self.move_delay = 0.2  # Reduced for normal game speed
            self.thinking_depth = 4  # Restored - using background threading now
            self.special_tile_awareness = 0.8
            self.combo_planning = 0.7
            self.mistake_chance = 0.03
            self.reaction_speed = 0.4
        else:  # NIGHTMARE
            self.move_delay = 0.1  # Reduced for normal game speed
            self.thinking_depth = 5  # Restored - using background threading now
            self.special_tile_awareness = 0.95
            self.combo_planning = 0.9
            self.mistake_chance = 0.01
            self.reaction_speed = 0.2
    
    def customize(self, **kwargs):
        """Allow custom configuration of AI parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Move:
    """Represents a possible move on the board"""
    
    def __init__(self, pos1: Tuple[int, int], pos2: Tuple[int, int], score: float = 0.0):
        self.pos1 = pos1  # First tile position
        self.pos2 = pos2  # Second tile position (adjacent)
        self.score = score  # Evaluated score for this move
        self.immediate_matches = []  # Matches created immediately
        self.special_tiles_created = []  # Special tiles this move creates
        self.combo_potential = 0.0  # Potential for future combos
        self.cascade_score = 0.0  # Expected cascade score
    
    def __str__(self):
        return f"Move {self.pos1} -> {self.pos2} (Score: {self.score:.2f})"

class BoardAnalyzer:
    """Analyzes board state and evaluates moves"""
    
    def __init__(self, board: Board, config: AIConfig):
        self.board = board
        self.config = config
    
    def get_all_possible_moves(self) -> List[Move]:
        """Get all valid moves on the board"""
        moves = []
        
        for row in range(self.board.height):
            for col in range(self.board.width):
                # Check right neighbor
                if col < self.board.width - 1:
                    move = Move((row, col), (row, col + 1))
                    if self.is_valid_move(move):
                        moves.append(move)
                
                # Check down neighbor
                if row < self.board.height - 1:
                    move = Move((row, col), (row + 1, col))
                    if self.is_valid_move(move):
                        moves.append(move)
        
        return moves
    
    def is_valid_move(self, move: Move) -> bool:
        """Check if a move would create matches or activate special tiles"""
        # Check if either position has a special tile (special tiles can always be activated)
        tile1 = self.board.get_tile(*move.pos1)
        tile2 = self.board.get_tile(*move.pos2)
        
        if (tile1 and tile1.is_special()) or (tile2 and tile2.is_special()):
            return True  # Special tiles can always be activated by swapping
        
        # Simulate the swap for regular matches
        board_copy = self.create_board_copy()
        self.simulate_swap(board_copy, move.pos1, move.pos2)
        
        # Check if this creates any matches
        matches1 = self.find_matches_at_position(board_copy, move.pos1)
        matches2 = self.find_matches_at_position(board_copy, move.pos2)
        
        return len(matches1) > 0 or len(matches2) > 0
    
    def create_board_copy(self) -> Board:
        """Create a deep copy of the board for simulation"""
        return copy.deepcopy(self.board)
    
    def simulate_swap(self, board: Board, pos1: Tuple[int, int], pos2: Tuple[int, int]):
        """Simulate swapping two tiles on a board copy"""
        tile1 = board.get_tile(*pos1)
        tile2 = board.get_tile(*pos2)
        
        board.grid[pos1[0]][pos1[1]] = tile2
        board.grid[pos2[0]][pos2[1]] = tile1
    
    def find_matches_at_position(self, board: Board, pos: Tuple[int, int]) -> List[Match]:
        """Find all matches involving a specific position"""
        # Simplified match finding - in practice would use board's match detection
        matches = []
        row, col = pos
        tile = board.get_tile(row, col)
        
        if not tile or tile.color == TileColor.EMPTY:
            return matches
        
        # Check horizontal matches
        horizontal_matches = self.find_horizontal_matches(board, pos)
        if horizontal_matches:
            matches.extend(horizontal_matches)
        
        # Check vertical matches
        vertical_matches = self.find_vertical_matches(board, pos)
        if vertical_matches:
            matches.extend(vertical_matches)
        
        return matches
    
    def find_horizontal_matches(self, board: Board, pos: Tuple[int, int]) -> List[Match]:
        """Find horizontal matches at position"""
        matches = []
        row, col = pos
        tile = board.get_tile(row, col)
        
        if not tile:
            return matches
        
        # Count consecutive tiles of same color to the left and right
        left_count = 0
        right_count = 0
        
        # Count left
        for c in range(col - 1, -1, -1):
            left_tile = board.get_tile(row, c)
            if left_tile and left_tile.color == tile.color:
                left_count += 1
            else:
                break
        
        # Count right
        for c in range(col + 1, board.width):
            right_tile = board.get_tile(row, c)
            if right_tile and right_tile.color == tile.color:
                right_count += 1
            else:
                break
        
        total_length = left_count + 1 + right_count
        
        if total_length >= 3:
            # Create match object
            start_col = col - left_count
            end_col = col + right_count
            positions = [(row, c) for c in range(start_col, end_col + 1)]
            
            match_type = MatchType.THREE
            if total_length == 4:
                match_type = MatchType.FOUR
            elif total_length >= 5:
                match_type = MatchType.FIVE
            
            match = Match(positions, match_type)
            matches.append(match)
        
        return matches
    
    def find_vertical_matches(self, board: Board, pos: Tuple[int, int]) -> List[Match]:
        """Find vertical matches at position"""
        matches = []
        row, col = pos
        tile = board.get_tile(row, col)
        
        if not tile:
            return matches
        
        # Count consecutive tiles of same color above and below
        up_count = 0
        down_count = 0
        
        # Count up
        for r in range(row - 1, -1, -1):
            up_tile = board.get_tile(r, col)
            if up_tile and up_tile.color == tile.color:
                up_count += 1
            else:
                break
        
        # Count down
        for r in range(row + 1, board.height):
            down_tile = board.get_tile(r, col)
            if down_tile and down_tile.color == tile.color:
                down_count += 1
            else:
                break
        
        total_length = up_count + 1 + down_count
        
        if total_length >= 3:
            # Create match object
            start_row = row - up_count
            end_row = row + down_count
            positions = [(r, col) for r in range(start_row, end_row + 1)]
            
            match_type = MatchType.THREE
            if total_length == 4:
                match_type = MatchType.FOUR
            elif total_length >= 5:
                match_type = MatchType.FIVE
            
            match = Match(positions, match_type)
            matches.append(match)
        
        return matches

class MoveEvaluator:
    """Evaluates and scores moves based on various factors"""
    
    def __init__(self, config: AIConfig):
        self.config = config
    
    def evaluate_move(self, board: Board, move: Move) -> float:
        """Evaluate a move and return its score"""
        board_copy = copy.deepcopy(board)
        analyzer = BoardAnalyzer(board_copy, self.config)
        
        # Simulate the move
        analyzer.simulate_swap(board_copy, move.pos1, move.pos2)
        
        score = 0.0
        
        # Base score for immediate matches
        immediate_score = self.score_immediate_matches(board_copy, move)
        score += immediate_score
        
        # Bonus for special tile creation
        special_score = self.score_special_tile_creation(board_copy, move)
        score += special_score * self.config.special_tile_awareness
        
        # High bonus for activating existing special tiles (use original board state)
        activation_score = self.score_special_tile_activation(board, move)
        score += activation_score * self.config.special_tile_awareness * 2.0  # Double weight for using existing special tiles
        
        # Bonus for combo potential
        combo_score = self.score_combo_potential(board_copy, move)
        score += combo_score * self.config.combo_planning
        
        # Cascade potential
        cascade_score = self.estimate_cascade_potential(board_copy, move)
        score += cascade_score
        
        move.score = score
        return score
    
    def score_immediate_matches(self, board: Board, move: Move) -> float:
        """Score immediate matches created by the move"""
        analyzer = BoardAnalyzer(board, self.config)
        
        matches1 = analyzer.find_matches_at_position(board, move.pos1)
        matches2 = analyzer.find_matches_at_position(board, move.pos2)
        
        all_matches = matches1 + matches2
        move.immediate_matches = all_matches
        
        score = 0.0
        for match in all_matches:
            # Base score based on match length
            length = len(match.positions)
            if length == 3:
                score += 100
            elif length == 4:
                score += 300  # Creates special tile
            elif length >= 5:
                score += 500  # Creates more powerful special tile
            
            # Bonus for match type
            if match.match_type == MatchType.SQUARE:
                score += 400
            elif match.match_type == MatchType.T_SHAPE:
                score += 600
        
        return score
    
    def score_special_tile_creation(self, board: Board, move: Move) -> float:
        """Score potential special tile creation"""
        score = 0.0
        
        for match in move.immediate_matches:
            length = len(match.positions)
            
            if length == 4:
                # Creates rocket or lightning
                score += 200
                move.special_tiles_created.append(SpecialTileType.ROCKET_HORIZONTAL)
            elif length >= 5:
                # Creates board wipe
                score += 400
                move.special_tiles_created.append(SpecialTileType.BOARD_WIPE)
            elif match.match_type == MatchType.SQUARE:
                # Creates bomb
                score += 300
                move.special_tiles_created.append(SpecialTileType.BOMB)
            elif match.match_type == MatchType.T_SHAPE:
                # Creates lightning
                score += 350
                move.special_tiles_created.append(SpecialTileType.LIGHTNING)
        
        return score
    
    def score_special_tile_activation(self, board: Board, move: Move) -> float:
        """Score moves that activate existing special tiles"""
        score = 0.0
        
        # Check if either tile in the move is special
        tile1 = board.get_tile(*move.pos1)
        tile2 = board.get_tile(*move.pos2)
        
        for tile in [tile1, tile2]:
            if tile and tile.is_special():
                special_type = tile.special_tile.tile_type
                
                # High scores for activating powerful special tiles
                if special_type == SpecialTileType.BOARD_WIPE:
                    score += 500  # Highest priority
                elif special_type == SpecialTileType.LIGHTNING:
                    score += 400
                elif special_type == SpecialTileType.BOMB:
                    score += 350
                elif special_type in [SpecialTileType.ROCKET_HORIZONTAL, SpecialTileType.ROCKET_VERTICAL]:
                    score += 300
                else:
                    score += 250  # Default for other special tiles
        
        return score
    
    def score_combo_potential(self, board: Board, move: Move) -> float:
        """Score potential for future combos with existing special tiles"""
        score = 0.0
        
        # Look for existing special tiles on the board
        special_tiles = self.find_special_tiles(board)
        
        for special_pos, special_tile in special_tiles:
            # Check if this move creates opportunities to use the special tile
            distance = self.calculate_distance(move.pos1, special_pos)
            
            if distance <= 3:  # Within reasonable combo range
                # Bonus based on special tile type and proximity
                if special_tile.tile_type == SpecialTileType.ROCKET_HORIZONTAL:
                    score += 150 / (distance + 1)
                elif special_tile.tile_type == SpecialTileType.BOMB:
                    score += 200 / (distance + 1)
                elif special_tile.tile_type == SpecialTileType.LIGHTNING:
                    score += 250 / (distance + 1)
                elif special_tile.tile_type == SpecialTileType.BOARD_WIPE:
                    score += 300 / (distance + 1)
        
        move.combo_potential = score
        return score
    
    def estimate_cascade_potential(self, board: Board, move: Move) -> float:
        """Estimate potential cascade score from falling tiles"""
        # Simplified cascade estimation
        score = 0.0
        
        # Count empty spaces that will be created
        empty_count = 0
        for match in move.immediate_matches:
            empty_count += len(match.positions)
        
        # Estimate cascade multiplier based on board state
        cascade_multiplier = min(empty_count * 50, 300)
        score += cascade_multiplier
        
        move.cascade_score = score
        return score
    
    def find_special_tiles(self, board: Board) -> List[Tuple[Tuple[int, int], Any]]:
        """Find all special tiles on the board"""
        special_tiles = []
        
        for row in range(board.height):
            for col in range(board.width):
                tile = board.get_tile(row, col)
                if tile and tile.special_tile:
                    special_tiles.append(((row, col), tile.special_tile))
        
        return special_tiles
    
    def calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

class Match3AI:
    """Main AI controller for the boss board with background computation"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.last_move_time = 0
        self.current_board = None
        self.thinking = False
        self.best_move = None
        self.evaluator = MoveEvaluator(config)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.current_future = None
        self.move_ready = False
    
    def set_board(self, board: Board):
        """Set the board this AI should analyze"""
        self.current_board = board
    
    def should_make_move(self) -> bool:
        """Check if AI should make a move based on timing"""
        current_time = time.time()
        return (current_time - self.last_move_time) >= self.config.move_delay
    
    def get_best_move(self) -> Optional[Move]:
        """Get the best move using minimax-like analysis"""
        if not self.current_board:
            return None
        
        analyzer = BoardAnalyzer(self.current_board, self.config)
        possible_moves = analyzer.get_all_possible_moves()
        
        if not possible_moves:
            return None
        
        # Evaluate all moves
        for move in possible_moves:
            self.evaluator.evaluate_move(self.current_board, move)
        
        # Apply lookahead if configured
        if self.config.thinking_depth > 1:
            possible_moves = self.apply_lookahead(possible_moves)
        
        # Sort by score and apply mistake chance
        possible_moves.sort(key=lambda m: m.score, reverse=True)
        
        # Apply mistake chance for realistic AI behavior
        if random.random() < self.config.mistake_chance and len(possible_moves) > 1:
            # Sometimes pick 2nd or 3rd best move
            choice_index = min(random.randint(1, 3), len(possible_moves) - 1)
            return possible_moves[choice_index]
        
        return possible_moves[0] if possible_moves else None
    
    def apply_lookahead(self, moves: List[Move]) -> List[Move]:
        """Apply multi-move lookahead analysis"""
        for move in moves[:10]:  # Only analyze top moves for performance
            lookahead_score = self.calculate_lookahead_score(move, self.config.thinking_depth - 1)
            move.score += lookahead_score * 0.3  # Weight future moves less than immediate
        
        return moves
    
    def calculate_lookahead_score(self, move: Move, depth: int) -> float:
        """Calculate score for moves that could follow this one"""
        if depth <= 0:
            return 0.0
        
        # Simulate the move
        board_copy = copy.deepcopy(self.current_board)
        analyzer = BoardAnalyzer(board_copy, self.config)
        analyzer.simulate_swap(board_copy, move.pos1, move.pos2)
        
        # Get possible follow-up moves
        follow_up_moves = analyzer.get_all_possible_moves()
        
        if not follow_up_moves:
            return 0.0
        
        # Evaluate best follow-up move
        best_follow_up_score = 0.0
        for follow_up in follow_up_moves[:5]:  # Limit for performance
            score = self.evaluator.evaluate_move(board_copy, follow_up)
            if depth > 1:
                score += self.calculate_lookahead_score(follow_up, depth - 1) * 0.5
            best_follow_up_score = max(best_follow_up_score, score)
        
        return best_follow_up_score
    
    def start_thinking(self):
        """Start background computation for the next move"""
        if not self.current_board or self.thinking or not self.should_make_move():
            return
            
        self.thinking = True
        self.move_ready = False
        self.current_future = self.executor.submit(self._compute_move)
    
    def _compute_move(self) -> Optional[Move]:
        """Background computation of the best move"""
        try:
            return self.get_best_move()
        except Exception as e:
            print(f"AI computation error: {e}")
            return None
    
    def get_computed_move(self) -> Optional[Move]:
        """Get the computed move if ready, non-blocking"""
        if not self.thinking or not self.current_future:
            return None
            
        if self.current_future.done():
            try:
                move = self.current_future.result()
                self.thinking = False
                self.move_ready = True
                self.last_move_time = time.time()
                return move
            except Exception as e:
                print(f"Error getting AI move: {e}")
                self.thinking = False
                return None
        
        return None
    
    def is_thinking(self) -> bool:
        """Check if AI is currently computing a move"""
        return self.thinking
    
    def make_move(self) -> Optional[Move]:
        """Execute the AI's chosen move (legacy method for compatibility)"""
        if not self.thinking:
            self.start_thinking()
            
        return self.get_computed_move()