import random

class CheckersStartingPosition:
    def __init__(self, board_size=8, num_kings_per_side=3):
        """ Initializes a checkers board configuration where the board is split into
        two equal halves, and each player (Moscow and Kyiv) starts with their kings on their own side. """
        self.board_size = board_size
        self.num_kings_per_side = num_kings_per_side
        self.board = [[None for _ in range(board_size)] for _ in range(board_size)]
        self._generate_position()

    def _is_white_square(self, row, col):
        # Define white squares where (row + col) is even
        return (row + col) % 2 == 0

    def _generate_position(self):
        midpoint = self.board_size // 2

        # Moscow side: Top half (rows 0 to midpoint-1)
        moscow_valid_squares = [
            (r, c) for r in range(0, midpoint) for c in range(self.board_size)
            if self._is_white_square(r, c)
        ]
        
        # Kyiv side: Bottom half (rows midpoint to board_size-1)
        kyiv_valid_squares = [
            (r, c) for r in range(midpoint, self.board_size) for c in range(self.board_size)
            if self._is_white_square(r, c)
        ]

        if len(moscow_valid_squares) < self.num_kings_per_side or len(kyiv_valid_squares) < self.num_kings_per_side:
            raise ValueError("Not enough white squares on one or both sides to place the kings.")

        # Randomly choose positions for Moscow and Kyiv kings on their own sides
        moscow_positions = random.sample(moscow_valid_squares, self.num_kings_per_side)
        kyiv_positions = random.sample(kyiv_valid_squares, self.num_kings_per_side)

        for r, c in moscow_positions:
            self.board[r][c] = "M_King"
        for r, c in kyiv_positions:
            self.board[r][c] = "K_King"

    def display_board(self):
        """Displays the text-based grid representation of the board."""
        print("   " + " ".join([str(i) for i in range(self.board_size)]))
        print("  +" + "-" * (self.board_size * 2 - 1) + "+")
        for r in range(self.board_size):
            row_str = []
            for c in range(self.board_size):
                piece = self.board[r][c]
                if piece == "M_King":
                    row_str.append("M")
                elif piece == "K_King":
                    row_str.append("K")
                else:
                    # Visual indicator for white vs black empty squares
                    row_str.append("." if self._is_white_square(r, c) else " ")
            print(f"{r} |" + "|".join(row_str) + "|")
        print("  +" + "-" * (self.board_size * 2 - 1) + "+")

# Instantiate and display the starting position
position = CheckersStartingPosition(board_size=8, num_kings_per_side=4)
position.display_board()
