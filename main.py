# code from https://roboticsproject.readthedocs.io/en/latest/ConnectFourAlgorithm.html
import math
import random
import numpy as np

from connect4 import Position, Solver

ROW_COUNT = 6
COLUMN_COUNT = 7
WINDOW_LENGTH = 4
PLAYER_PIECE = -1
BOT_PIECE = 1
EMPTY = 0



def create_board():
    board = np.zeros((ROW_COUNT, COLUMN_COUNT))
    return board

def pretty_print_board(board):
    flipped_board = np.flipud(board)

    print("\033[0;37;41m 0 \033[0;37;41m 1 \033[0;37;41m 2 \033[0;37;41m 3 \033[0;37;41m 4 \033[0;37;41m 5 \033[0;37;41m 6 \033[0m")
    for i in flipped_board:
        row_str = ""

        for j in i:
            if j == BOT_PIECE:
                #print(yellow)
                row_str +="\033[0;37;43m 1 "
            elif j ==PLAYER_PIECE:
                row_str +="\033[0;37;44m 2 "
            else:
                #print black
                row_str +="\033[0;37;45m   "

        print(row_str+"\033[0m")
    print("\033[0;37;41m 0 \033[0;37;41m 1 \033[0;37;41m 2 \033[0;37;41m 3 \033[0;37;41m 4 \033[0;37;41m 5 \033[0;37;41m 6 \033[0m")

def get_valid_locations(board):
    valid_locations = []
    for col in range(COLUMN_COUNT):
        if is_valid_location(board, col):
            valid_locations.append(col)
    return valid_locations

def is_valid_location(board, col):
    return board[ROW_COUNT - 1][col] == 0

def get_next_open_row(board, col):
    for r in range(ROW_COUNT):
        if board[r][col] == 0:
            return r

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def score_position(board, piece):
    score = 0

    # Score centre column
    centre_array = [int(i) for i in list(board[:, COLUMN_COUNT // 2])]
    centre_count = centre_array.count(piece)
    score += centre_count * (WINDOW_LENGTH - 1)

    # Score horizontal positions
    for r in range(ROW_COUNT):
        row_array = [int(i) for i in list(board[r, :])]
        for c in range(COLUMN_COUNT - WINDOW_LENGTH + 1):
            # Create a horizontal window of 4
            window = row_array[c:c + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Score vertical positions
    for c in range(COLUMN_COUNT):
        col_array = [int(i) for i in list(board[:, c])]
        for r in range(ROW_COUNT - WINDOW_LENGTH + 1):
            # Create a vertical window of 4
            window = col_array[r:r + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Score positive diagonals
    for r in range(ROW_COUNT - WINDOW_LENGTH + 1):
        for c in range(COLUMN_COUNT - WINDOW_LENGTH + 1):
            # Create a positive diagonal window of 4
            window = [board[r + i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    # Score negative diagonals
    for r in range(ROW_COUNT - WINDOW_LENGTH + 1):
        for c in range(COLUMN_COUNT - WINDOW_LENGTH + 1):
            # Create a negative diagonal window of 4
            window = [board[r + WINDOW_LENGTH - 1 - i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score

def evaluate_window(window, piece):
    score = 0
    # Switch scoring based on turn
    opp_piece = PLAYER_PIECE
    if piece == PLAYER_PIECE:
        opp_piece = BOT_PIECE

    # Prioritise a winning move
    # Minimax makes this less important
    if window.count(piece) == WINDOW_LENGTH:
        score += 100
    # Make connecting WINDOW_LENGTH - 1 second priority
    elif WINDOW_LENGTH > 2 and window.count(piece) == WINDOW_LENGTH - 1 and window.count(EMPTY) == 1:
        score += 5
    # Make connecting WINDOW_LENGTH - 2 third priority
    elif WINDOW_LENGTH > 3 and window.count(piece) == WINDOW_LENGTH - 2  and window.count(EMPTY) == 2:
        score += 2
    # Prioritise blocking an opponent's winning move (but not over bot winning)
    # Minimax makes this less important
    if window.count(opp_piece) == WINDOW_LENGTH and window.count(EMPTY) == 1:
        score -= 50

    return score

def winning_move(board, piece):
    # Check valid horizontal locations for win
    for c in range(COLUMN_COUNT - WINDOW_LENGTH + 1):
        for r in range(ROW_COUNT):
            if all(board[r][c + i] == piece for i in range(WINDOW_LENGTH)):
                return True

    # Check valid vertical locations for win
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - WINDOW_LENGTH + 1):
            if all(board[r + i][c] == piece for i in range(WINDOW_LENGTH)):
                return True

    # Check valid positive diagonal locations for win
    for c in range(COLUMN_COUNT - WINDOW_LENGTH + 1):
        for r in range(ROW_COUNT - WINDOW_LENGTH + 1):
            if all(board[r + i][c + i] == piece for i in range(WINDOW_LENGTH)):
                return True

    # check valid negative diagonal locations for win
    for c in range(COLUMN_COUNT - WINDOW_LENGTH + 1):
        for r in range(WINDOW_LENGTH - 1, ROW_COUNT):
            if all(board[r - i][c + i] == piece for i in range(WINDOW_LENGTH)):
                return True

    return False

def is_terminal_node(board):
    return winning_move(board, PLAYER_PIECE) or winning_move(board, BOT_PIECE) or len(get_valid_locations(board)) == 0

def minimax(board, depth, alpha, beta, maximisingPlayer):
    valid_locations = get_valid_locations(board)

    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if is_terminal:
            # Weight the bot winning really high
            if winning_move(board, BOT_PIECE):
                return None, 9999999
            # Weight the human winning really low
            elif winning_move(board, PLAYER_PIECE):
                return None, -9999999
            else:  # No more valid moves
                return None, 0
        # Return the bot's score
        else:
            return None, score_position(board, BOT_PIECE)

    if maximisingPlayer:
        value = -9999999
        # Randomise column to start
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            # Create a copy of the board
            b_copy = board.copy()
            # Drop a piece in the temporary board and record score
            drop_piece(b_copy, row, col, BOT_PIECE)
            new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                # Make 'column' the best scoring column we can get
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value

    else:  # Minimising player
        value = 9999999
        # Randomise column to start
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            # Create a copy of the board
            b_copy = board.copy()
            # Drop a piece in the temporary board and record score
            drop_piece(b_copy, row, col, PLAYER_PIECE)
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                # Make 'column' the best scoring column we can get
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value

def play_turn(board, col, piece):
    if 0 <= col < COLUMN_COUNT and is_valid_location(board, col):
        row = get_next_open_row(board, col)
        drop_piece(board, row, col, piece)
        if winning_move(board, piece):
            pretty_print_board(board)
            print(f"{'PLAYER 1' if piece == PLAYER_PIECE else 'BOT'} WINS!")
            return True  # Game over
    return False  # Game continues

def easy_play(board):
    col, _ = minimax(board, 2, -9999999, 9999999, True)
    return col

def medium_play(board):
    col, _ = minimax(board, 3, -9999999, 9999999, True)
    return col

def hard_play(board):
    col, _ = minimax(board, 4, -9999999, 9999999, True)
    return col

def optimal_play(board):
    """
    :param board:
        Ensure that BOT_PIECE = 1 and PLAYER_PIECE = -1
        Currently only supports WINDOW_LENGTH = 4
    :return:
        Optimal column to play
    """
    if np.sum(board != 0) < 6: # If less than <n> moves have been played, resort to hard_play to ease search tree
        return hard_play(board)
    else:
        position = Position(board)
        solver = Solver()
        scores = solver.analyze(position, False)
        print(scores) # TODO For debugging, remove later
        col = scores.index(max(scores))
        return col

def play_game():
    board = create_board()
    game_over = False
    turn = 0  # 0: Player, 1: Bot
    play_alg = {
        'easy': easy_play,
        'medium': medium_play,
        'hard': hard_play,
        'impossible': optimal_play,
    }
    mode = 'hard'

    while not game_over:
        pretty_print_board(board)
        if turn == 0:
            valid_move = False
            while not valid_move:
                try:
                    col = int(input("Player 1 Make your Selection (0-6): "))
                    if 0 <= col < COLUMN_COUNT and is_valid_location(board, col):
                        valid_move = True
                    else:
                        print("Invalid column. Try again.")
                except ValueError:
                    print("Please enter a valid integer between 0 and 6.")
            game_over = play_turn(board, col, PLAYER_PIECE)
        else:
            col = play_alg[mode](board)
            game_over = play_turn(board, col, BOT_PIECE)
        if len(get_valid_locations(board)) == 0 and not game_over:
            pretty_print_board(board)
            print("Game is a draw!")
            game_over = True
        turn ^= 1  # Switch turns

if __name__ == "__main__":
    play_game()
