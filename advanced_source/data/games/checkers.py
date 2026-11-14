import random
from collections import deque
import networkx as nx

class CheckersGameEngine:
    def __init__(self, board_size=4, num_kings_per_side=3):
        self.board_size = board_size
        self.num_kings_per_side = num_kings_per_side
        self.G = nx.DiGraph()
        self.game_values = {}

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
        self.G = nx.DiGraph()
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
                self.G.add_edge(curr_state, next_state, player=turn)
                if next_state not in visited and next_state[1] != 'GAME_OVER':
                    visited.add(next_state)
                    queue.append(next_state)
        return self.G

    def analyze_game_states(self):
        """ Performs retrograde analysis on the state space graph G to determine
        if each state is a Win for Moscow (M), a Win for Kyiv (K), or a Draw (D). """
        self.game_values = {}
        out_degrees = {node: self.G.out_degree(node) for node in self.G.nodes()}
        queue = deque()
        # 1. Identify and label terminal (Game Over / No moves) states
        for node in self.G.nodes():
            board, turn = node
            if turn == 'GAME_OVER':
                incoming = list(self.G.in_edges(node, data=True))
                if incoming and incoming[0][2].get('player') == 'M':
                    self.game_values[node] = 'M_WIN'
                else:
                    self.game_values[node] = 'K_WIN'
                queue.append(node)
            elif out_degrees[node] == 0:
                self.game_values[node] = 'K_WIN' if turn == 'M' else 'M_WIN'
                queue.append(node)

        # 2. Backward propagation (Retrograde Analysis)
        while queue:
            curr = queue.popleft()
            curr_val = self.game_values[curr]
            for parent, _, edge_data in self.G.in_edges(curr, data=True):
                if parent in self.game_values:
                    continue
                parent_board, parent_turn = parent
                if (parent_turn == 'M' and curr_val == 'M_WIN') or (parent_turn == 'K' and curr_val == 'K_WIN'):
                    self.game_values[parent] = curr_val
                    queue.append(parent)
                else:
                    out_degrees[parent] -= 1
                    if out_degrees[parent] == 0:
                        self.game_values[parent] = 'K_WIN' if parent_turn == 'M' else 'M_WIN'
                        queue.append(parent)

        # 3. Label remaining states as forced draws
        for node in self.G.nodes():
            if node not in self.game_values:
                self.game_values[node] = 'DRAW'

        return self.game_values

    def query_state_outcome(self, board, turn):
        """ Queries the theoretical game theoretical outcome of a given board state and turn."""
        state = (board, turn)
        return self.game_values.get(state, "State not reachable / found")

    def print_board(self, board):
        """ Helper to pretty-print the board state layout. """
        print("  " + " ".join(str(c) for c in range(self.board_size)))
        print(" +" + "-" * (self.board_size * 2 - 1) + "+")
        for r in range(self.board_size):
            row_str = []
            for c in range(self.board_size):
                val = board[r][c]
                if val is None:
                    row_str.append("." if self._is_white_square(r, c) else " ")
                else:
                    row_str.append(val)
            print(f"{r}|{" ".join(row_str)}|")
        print(" +" + "-" * (self.board_size * 2 - 1) + "+")

engine = CheckersGameEngine(board_size=4, num_kings_per_side=3) # Run pipeline and display outcomes
G = engine.build_reachability_graph()
game_values = engine.analyze_game_states()
outcome_counts = {'M_WIN': 0, 'K_WIN': 0, 'DRAW': 0} # Calculate statistics of outcomes
for val in game_values.values():
    outcome_counts[val] += 1

print(f"Generated State Graph with {G.number_of_nodes()} states and {G.number_of_edges()} transitions.\n")
print("Game Theoretical Analysis Completed:")
for outcome, count in outcome_counts.items():
    print(f" - {outcome}: {count} states ({count/len(G)*100:.2f}%)")

# Evaluate and print initial starting position
initial_board = engine.get_initial_state()
print("\nInitial Starting Board Configuration:")
engine.print_board(initial_board)

outcome = engine.query_state_outcome(initial_board, 'M')
print(f"\nThe initial starting position (Moscow to move) is a guaranteed: {outcome}")
