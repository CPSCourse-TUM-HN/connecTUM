# code from https://roboticsproject.readthedocs.io/en/latest/ConnectFourAlgorithm.html
import itertools
import json
import os
import random
import numpy as np
import multiprocessing as mp
from multiprocessing import Manager

from connect4 import Position, Solver
import grid_fix
from camera import Camera

ROW_COUNT = 6
COLUMN_COUNT = 7
WINDOW_LENGTH = 4
PLAYER_PIECE = -1
BOT_PIECE = 1
EMPTY = 0

grid = None

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

def is_valid_board(board):
    # For each column, check that there are no empty cells below a filled cell
    for col in range(COLUMN_COUNT):
        found_empty = False
        for row in range(ROW_COUNT):
            if board[row][col] == 0:
                found_empty = True
            elif found_empty:
                # Found a token above an empty cell, invalid board
                return False
    return True


# TODO add more error / cheating & interim state handling
def get_valid_state(old_board, new_board):
    # First, check if the new board is valid
    if not is_valid_board(new_board):
        return None

    # The new board must have exactly one more token than the old board
    old_count = np.count_nonzero(old_board)
    new_count = np.count_nonzero(new_board)
    if new_count != old_count + 1:
        return None

    # Find the difference between the boards
    diff = new_board - old_board
    changed_positions = np.argwhere(diff != 0)

    # There must be exactly one changed position
    if changed_positions.shape[0] != 1:
        return None

    row, col = changed_positions[0]
    # The change must be on top of the stack (all rows below must be non-empty in new_board)
    if row > 0 and new_board[row-1][col] == 0:
        return None

    return int(col)

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
    col, _ = minimax(board, 4, -9999999, 9999999, True)
    return col

def hard_play(board):
    col, _ = minimax(board, 6, -9999999, 9999999, True)
    return col

def optimal_play(board, saved_moves=None):
    """
    :param saved_moves:
        Dictionary of board to scores
    :param board:
        Ensure that BOT_PIECE = 1 and PLAYER_PIECE = -1
        Currently only supports WINDOW_LENGTH = 4
    :return:
        Optimal column to play
    """
    if saved_moves is None:
        saved_moves = {}

    if np.sum(board != 0) < 0: # If less than <n> moves have been played, resort to hard_play to ease search tree
        return hard_play(board)
    else:
        key = board2key(board)
        if key in saved_moves:
            scores = saved_moves[key]
        # Can deduce scores from res for horizontally flipped config due to symmetry
        elif ((flipped_key := board2key(board[:, ::-1])) in saved_moves):
            scores = saved_moves[flipped_key]
        else:
            position = Position(board)
            solver = Solver()
            scores = solver.analyze(position, False)
            saved_moves[key] = scores
            # # Can also deduce scores for horizontally flipped configuration due to symmetry
            # flipped_key = board2key(board[:, ::-1])
            # if not flipped_key in saved_moves:
            #     saved_moves[flipped_key] = scores[::-1]
        print(scores) # TODO For debugging, remove later
        col = scores.index(max(scores))
        return col

def board2key(board):
    return "".join(map(str, board.flatten()))

def train():
    print("\033[1;32mStarting...\033[0m")


    lookup_table_loc = 'lookup_table.json'

    if os.path.isfile(lookup_table_loc):
        with open(lookup_table_loc, 'r') as file:
            lookup_table = json.load(file)
            print(f"Loaded lookup table {lookup_table_loc}.")
    else:
        print(f"The file '{lookup_table_loc}' does not exist.")
        lookup_table = dict()

    board = create_board()
    game_over = False
    turn = 0  # 0: Random Bot, 1: Optimal Bot
    winner = 0


    n_turns = 4
    i = 0
    for player_first in (True, False,):
        move_seqs = (seq for seq in itertools.product(range(COLUMN_COUNT), repeat=n_turns))
        for move_seq in move_seqs:
            print(move_seq)
            board = create_board()
            pretty_print_board(board)
            for it_col in move_seq:
                if player_first:
                    if not is_valid_location(board, it_col): break # Move onto next move sequence
                    game_over = play_turn(board, it_col, PLAYER_PIECE)
                    pretty_print_board(board)
                    if game_over: break

                bot_col = optimal_play(board, lookup_table)
                game_over = play_turn(board, bot_col, BOT_PIECE)
                pretty_print_board(board)
                if game_over: break

                if not player_first:
                    if not is_valid_location(board, it_col): break # Move onto next move sequence
                    game_over = play_turn(board, it_col, PLAYER_PIECE)
                    pretty_print_board(board)
                    if game_over: break


            with open(lookup_table_loc, 'w') as file:
                json.dump(lookup_table, file, indent=4)
                print(f"\033[1;32mSaved for move sequence {i}\033[0m")
                i += 1


def print_final_score(board, winner):
    score = get_score(board, winner)
    print(f"Final score for your game: {score}")

def get_score(board, winner):
    moves_played = int(np.sum(board != 0))
    max_moves = board.shape[0] * board.shape[1]
    if winner == BOT_PIECE:
        score = moves_played
    else:
        score = max_moves * 2 - moves_played
    return score * 10

def play_game(shared_dict):
    lookup_table_loc = 'lookup_table.json'

    if os.path.isfile(lookup_table_loc):
        with open(lookup_table_loc, 'r') as file:
            lookup_table = json.load(file)
            print(f"Loaded lookup table {lookup_table_loc}.")
    else:
        print(f"The file '{lookup_table_loc}' does not exist.")
        lookup_table = dict()


    global grid
    board = create_board()
    game_over = False
    turn = 0  # 0: Player, 1: Bot
    play_alg = {
        'easy': easy_play,
        'medium': medium_play,
        'hard': hard_play,
        'impossible': lambda board: optimal_play(board, lookup_table),
    }
    mode = 'impossible'
    winner = 0
    # Wait for camera to start producing data
    print("Waiting for camera to initialize...")
    while 'grid_ready' not in shared_dict or not shared_dict['grid_ready']:
        pass
    print("Camera ready, game starting!")
    while not game_over:
        #current_grid = shared_dict['current_grid'].copy()
        pretty_print_board(board)
        if turn == 0 and 'current_grid' in shared_dict:
            valid_move = False
            while not valid_move:
                # Wait for new grid data from camera
                new_grid = None
                while new_grid is None:
                    if 'current_grid' in shared_dict:
                        new_grid = shared_dict['current_grid'].copy()
                col = get_valid_state(board, new_grid)
                if col is not None:
                    valid_move = True
                    shared_dict['last_player_move'] = col  # Store the move
            game_over = play_turn(board, col, PLAYER_PIECE)
            if game_over:
                winner = PLAYER_PIECE
        else:
            col = play_alg[mode](board)
            game_over = play_turn(board, col, BOT_PIECE)
            if game_over:
                winner = BOT_PIECE

        if len(get_valid_locations(board)) == 0 and not game_over:
            pretty_print_board(board)
            print("Game is a draw!")
            game_over = True
            winner = EMPTY
        turn ^= 1  # Switch turns
    print_final_score(board, winner)
    shared_dict['game_over'] = True
    # Save learned moves
    with open(lookup_table_loc, 'w') as file:
        json.dump(lookup_table, file, indent=4)

def camera_processing(grid, shared_dict):
    Camera.start_image_processing(grid, shared_dict)

if __name__ == "__main__":
    # manager = Manager()
    # shared_dict = manager.dict()
    # shared_dict['game_over'] = False
    # shared_dict['grid_ready'] = False
    # grid = grid_fix.Grid(30, 0.3)
    # camera_process = mp.Process(target=camera_processing, args=(grid, shared_dict))
    # camera_process.start()
    # play_game(shared_dict)
    # camera_process.join()
    train()
