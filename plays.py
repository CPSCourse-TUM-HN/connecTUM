import random

import modules.board_param as param
from connect4_alg import Position, Solver

def board2key(board):
    return "".join(map(str, board.flatten()))

def is_terminal_node(board):
    return board.winning_move(param.PLAYER_PIECE) or board.winning_move(param.BOT_PIECE) or len(board.get_valid_location()) == 0

def minimax(board, depth, alpha, beta, maximisingPlayer):
    valid_locations = board.get_valid_location()

    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if is_terminal:
            # Weight the bot winning really high
            if board.winning_move(param.BOT_PIECE):
                return None, 9999999
            # Weight the human winning really low
            elif board.winning_move(param.PLAYER_PIECE):
                return None, -9999999
            else:  # No more valid moves
                return None, 0
        # Return the bot's score
        else:
            return None, board.score_position(param.BOT_PIECE)

    if maximisingPlayer:
        value = -9999999
        # Randomise column to start
        column = random.choice(valid_locations)
        for col in valid_locations:
            # Create a copy of the board
            b_copy = board.copy()
            # Drop a piece in the temporary board and record score
            b_copy.drop_piece(col, param.BOT_PIECE)
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
            # Create a copy of the board
            b_copy = board.copy()
            # Drop a piece in the temporary board and record score
            b_copy.drop_piece(col, param.PLAYER_PIECE)
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                # Make 'column' the best scoring column we can get
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value

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
        Ensure that param.BOT_PIECE = 1 and param.PLAYER_PIECE = -1
        Currently only supports param.WINDOW_LENGTH = 4
    :return:
        Optimal column to play
    """
    if saved_moves is None:
        saved_moves = {}

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