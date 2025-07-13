from ._mcs import mcs_play
from ._mcts import mcts_play
from connect4_alg import Position, Solver

import modules.board_param as param
from game_board import Board

def board2key(board_arr):
    """
    :param board_arr:
        Numpy array representation of board array
    :return:
        String representation of board array (so that it is a valid key in a JSON)
    """
    return "".join(map(str, board_arr.flatten()))

def is_terminal_node(board: Board):
    return board.winning_move(param.PLAYER_PIECE) or board.winning_move(param.BOT_PIECE) or len(board.get_valid_locations()) == 0

def easy_play(board):
    col = mcs_play(board, 100)
    return col

def medium_play(board):
    col = mcs_play(board, 1000)
    return col

def hard_play(board):
    col = mcts_play(board, 1000, 1.414)
    return col

def optimal_play(board, saved_moves=None):
    """
    :param saved_moves:
        Dictionary of board to scores
    :param board:
        Board object
        Ensure that param.BOT_PIECE = 1 and param.PLAYER_PIECE = -1
        Currently only supports param.WINDOW_LENGTH = 4
    :return:
        Optimal column to play
    """
    if saved_moves is None:
        saved_moves = {}

    board_arr = board.board_array

    key = board2key(board_arr)
    if key in saved_moves:
        scores = saved_moves[key]
    # Can deduce scores from res for horizontally flipped config due to symmetry
    elif ((flipped_key := board2key(board_arr[:, ::-1])) in saved_moves):
        scores = saved_moves[flipped_key]
    else:
        position = Position(board_arr)
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