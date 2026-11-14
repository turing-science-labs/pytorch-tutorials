import random
from collections import deque
import itertools
import networkx as nx

class CheckersGameEngine:
    def __init__(self, board_size=5, num_kings_per_side=3, num_mines=3):
        self.board_size = board_size
        self.num_kings_per_side = num_kings_per_side
        self.num_mines = num_mines
        self.mines = set()
        self.G = nx.DiGraph()
        self.game_values = {}
        self._place_mines_and_initialize()

    def _is_white_square(self, r, c):
        # Define white squares where (row + col) is even
        return (r + c) % 2 == 0

    def _place_mines_and_initialize(self):
        # Collect all valid playable squares on the board
        all_playable = [(r, c) for r in range(self.board_size) for c in range(self.board_size) if self._is_white_square(r, c)]
        
        # Midpoint division (For 5x5: Top half rows are 0,1. Bottom half rows are 3,4. Row 2 is neutral/middle)
        mid = self.board_size // 2
        
        # Seed for reproducibility
        random.seed(42)
        while True:
            self.mines = set(random.sample(all_playable, min(self.num_mines, len(all_playable) - 2)))
            non_mine_playable = [sq for sq in all_playable if sq not in self.mines]
            
            if not non_mine_playable:
                continue
                
            # Validate connectivity of all playable squares (BFS)
            visited = set()
            queue = deque([non_mine_playable[0]])
            visited.add(non_mine_playable[0])
            
            while queue:
                r, c = queue.popleft()
                for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in non_mine_playable and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        
            if len(visited) != len(non_mine_playable):
                continue # Must be fully connected
                
            # Separate playable squares on each player's starting half
            moscow_start_pool = [sq for sq in non_mine_playable if sq[0] < mid]
            kyiv_start_pool = [sq for sq in non_mine_playable if sq[0] > (mid if self.board_size % 2 != 0 else mid - 1)]
            
            # The total playable starting squares must be even and divided equally between Moscow and Kyiv
            if len(moscow_start_pool) == len(kyiv_start_pool) and len(moscow_start_pool) >= self.num_kings_per_side:
                break

    def get_all_valid_starting_boards(self):
        mid = self.board_size // 2
        all_playable = [(r, c) for r in range(self.board_size) for c in range(self.board_size) 
                        if self._is_white_square(r, c) and (r, c) not in self.mines]
        
        moscow_squares = [sq for sq in all_playable if sq[0] < mid]
        kyiv_squares = [sq for sq in all_playable if sq[0] > (mid if self.board_size % 2 != 0 else mid - 1)]
        
        # Generate all valid placements of 3 kings in Moscow's territory
        moscow_placements = list(itertools.combinations(moscow_squares, self.num_kings_per_side))
        # Generate all valid placements of 3 kings in Kyiv's territory
        kyiv_placements = list(itertools.combinations(kyiv_squares, self.num_kings_per_side))
        
        starting_boards = []
        for m_config in moscow_placements:
            for k_config in kyiv_placements:
                # Build board tuple representation
                board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
                for r, c in m_config:
                    board[r][c] = 'M'
                for r, c in k_config:
                    board[r][c] = 'K'
                starting_boards.append(tuple(tuple(row) for row in board))
        return starting_boards

    def get_valid_moves(self, board, player):
        moves = []
        opponent = 'K' if player == 'M' else 'M'
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == player:
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dr, dc in directions:
                        # 1. Simple move (Destination must not be a mine)
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            if self._is_white_square(nr, nc) and (nr, nc) not in self.mines and board[nr][nc] is None:
                                new_board = [list(row) for row in board]
                                new_board[r][c] = None
                                new_board[nr][nc] = player
                                moves.append(tuple(tuple(row) for row in new_board))
                        # 2. Jump move (Destination and intermediate opponent square must not be mines)
                        jr, jc = r + 2*dr, c + 2*dc
                        if 0 <= jr < self.board_size and 0 <= jc < self.board_size:
                            if (self._is_white_square(jr, jc) and
                                (jr, jc) not in self.mines and
                                (nr, nc) not in self.mines and
                                board[nr][nc] == opponent and
                                board[jr][jc] is None):
                                new_board = [list(row) for row in board]
                                new_board[r][c] = None
                                new_board[nr][nc] = None
                                new_board[jr][jc] = player
                                moves.append(tuple(tuple(row) for row in new_board))
        return moves

    def build_reachability_graph(self):
        starting_boards = self.get_all_valid_starting_boards()
        self.G = nx.DiGraph()
        queue = deque()
        visited = set()
        
        # Add all possible initial starting positions with Moscow to move
        for board in starting_boards:
            start_state = (board, 'M')
            queue.append(start_state)
            visited.add(start_state)
            
        while queue:
            curr_state = queue.popleft()
            board, turn = curr_state
            next_turn = 'K' if turn == 'M' else 'M'
            next_boards = self.get_valid_moves(board, turn)
            for next_board in next_boards:
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
        self.game_values = {}
        out_degrees = {node: self.G.out_degree(node) for node in self.G.nodes()}
        queue = deque()
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

        for node in self.G.nodes():
            if node not in self.game_values:
                self.game_values[node] = 'DRAW'
        return self.game_values

    def query_state_outcome(self, board, turn):
        state = (board, turn)
        return self.game_values.get(state, "State not reachable / found")

    def print_board(self, board):
        mid = self.board_size // 2
        print("  " + " ".join(str(c) for c in range(self.board_size)))
        print(" +" + "-" * (self.board_size * 2 - 1) + "+")
        for r in range(self.board_size):
            # Print a partition line before Kyiv's starting rows
            if r == (mid if self.board_size % 2 == 0 else mid + 1):
                print(" |" + "-" * (self.board_size * 2 - 1) + "| (Kyiv Territory)")
            elif r == mid and self.board_size % 2 != 0:
                print(" |" + "-" * (self.board_size * 2 - 1) + "| (Neutral Zone)")
            elif r == mid and self.board_size % 2 == 0:
                pass

            row_str = []
            for c in range(self.board_size):
                if (r, c) in self.mines:
                    row_str.append("X")
                else:
                    val = board[r][c]
                    if val is None:
                        row_str.append("." if self._is_white_square(r, c) else " ")
                    else:
                        row_str.append(val)

            label = " (Moscow Territory)" if r < mid else ""
            print(f"{r}|{' '.join(row_str)}|{label}")
        print(" +" + "-" * (self.board_size * 2 - 1) + "+")

# Instantiate generator with 5x5 board, 3 kings per side, and 3 mines
engine = CheckersGameEngine(board_size=5, num_kings_per_side=3, num_mines=3)
G = engine.build_reachability_graph()
game_values = engine.analyze_game_states()

outcome_counts = {'M_WIN': 0, 'K_WIN': 0, 'DRAW': 0}
for val in game_values.values():
    outcome_counts[val] += 1

print(f"Generated expanded State Graph with {G.number_of_nodes()} states and {G.number_of_edges()} transitions.\n")
print("Game Theoretical Analysis Completed for All Reachable Starting Positions:")
for outcome, count in outcome_counts.items():
    print(f" - {outcome}: {count} states ({count/len(G)*100:.2f}%)")

# Find outcome metrics across ONLY the initial starting states
start_boards = engine.get_all_valid_starting_boards()
start_outcomes = {'M_WIN': 0, 'K_WIN': 0, 'DRAW': 0}
for board in start_boards:
    res = engine.query_state_outcome(board, 'M')
    start_outcomes[res] += 1

print(f"\nEvaluation of the {len(start_boards)} possible starting layouts (Moscow moving first):")
for res, count in start_outcomes.items():
    print(f" - {res}: {count} layouts ({count/len(start_boards)*100:.2f}%)")
