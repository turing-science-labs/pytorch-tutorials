import random
from collections import deque
import networkx as nx

class CheckersGameEngine:
    def __init__(self, board_size=4, num_kings_per_side=3):
        self.board_size = board_size
        self.num_kings_per_side = num_kings_per_side

    def _is_white_square(self, r, c):
        # Define white squares where (row + col) is even
        return (r + c) % 2 == 0

    def get_initial_state(self):
        # Initialize board with Moscow (M) and Kyiv (K) on their own sides
        board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        midpoint = self.board_size // 2
        # Find valid squares in each player's half
        moscow_squares = [(r, c) for r in range(0, midpoint) for c in range(self.board_size) if self._is_white_square(r, c)]
        kyiv_squares = [(r, c) for r in range(midpoint, self.board_size) for c in range(self.board_size) if self._is_white_square(r, c)]
        
        # Place kings for each player on their respective sides
        for i in range(min(self.num_kings_per_side, len(moscow_squares))):
            m_r, m_c = moscow_squares[i]
            board[m_r][m_c] = 'M'
        for i in range(min(self.num_kings_per_side, len(kyiv_squares))):
            k_r, k_c = kyiv_squares[-(i+1)]
            board[k_r][k_c] = 'K'
        return tuple(tuple(row) for row in board)

    def get_valid_moves(self, board, player):
        moves = []
        opponent = 'K' if player == 'M' else 'M'
        # Find all pieces of the current player
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == player:
                    # King can move diagonally in all 4 directions
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dr, dc in directions:
                        # 1. Simple move
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if self._is_white_square(nr, nc) and board[nr][nc] is None:
                                # Generate new board state
                                new_board = [list(row) for row in board]
                                new_board[r][c] = None
                                new_board[nr][nc] = player
                                moves.append(tuple(tuple(row) for row in new_board))
                        # 2. Jump move
                        jr, jc = r + 2*dr, c + 2*dc
                        if 0 <= jr < self.board_size and 0 <= jc < self.board_size:
                            if self._is_white_square(jr, jc) and board[nr][nc] == opponent and board[jr][jc] is None:
                                new_board = [list(row) for row in board]
                                new_board[r][c] = None
                                new_board[nr][nc] = None # Capture opponent
                                new_board[jr][jc] = player
                                moves.append(tuple(tuple(row) for row in new_board))
        return moves

    def build_reachability_graph(self):
        initial_board = self.get_initial_state()
        # State representation: (board_tuple, current_turn)
        start_state = (initial_board, 'M')
        G = nx.DiGraph()
        queue = deque([start_state])
        visited = {start_state}
        while queue:
            curr_state = queue.popleft()
            board, turn = curr_state
            # Identify next player's turn
            next_turn = 'K' if turn == 'M' else 'M'
            # Get transitions
            next_boards = self.get_valid_moves(board, turn)
            for next_board in next_boards:
                # If the opponent is completely wiped out, it is a terminal win state
                opponent_piece_count = sum(row.count(next_turn) for row in next_board)
                if opponent_piece_count == 0:
                    next_state = (next_board, 'GAME_OVER')
                else:
                    next_state = (next_board, next_turn)
                G.add_edge(curr_state, next_state, player=turn)
                if next_state not in visited and next_state[1] != 'GAME_OVER':
                    visited.add(next_state)
                    queue.append(next_state)
        return G

# Instantiate generator with 4x4 board and 3 kings per side
engine = CheckersGameEngine(board_size=4, num_kings_per_side=3)
G = engine.build_reachability_graph()
print(f"Generated State Graph with {G.number_of_nodes()} states and {G.number_of_edges()} transitions.")
