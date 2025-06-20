import itertools
import json
import os

import modules.board_param as param
from game_board import Board
from plays import easy_play, medium_play, hard_play, optimal_play

def play_turn(board, col, piece, display_board=True):
    if 0 <= col < param.COLUMN_COUNT and board.is_valid_location(col):
        board.drop_piece(col, piece)
        if board.winning_move(piece):
            if display_board:
                board.pretty_print_board()
                print(f"{'PLAYER 1' if piece == param.PLAYER_PIECE else 'BOT'} WINS!")
            return True  # Game over
    return False  # Game continues

def train(n_turns=4):
    print("\033[1;32mStarting...\033[0m")

    lookup_table_loc = 'lookup_table.json'

    if os.path.isfile(lookup_table_loc):
        with open(lookup_table_loc, 'r') as file:
            lookup_table = json.load(file)
            print(f"Loaded lookup table {lookup_table_loc}.")
    else:
        print(f"The file '{lookup_table_loc}' does not exist.")
        lookup_table = dict()

    board = Board()
    game_over = False
    turn = 0  # 0: Random Bot, 1: Optimal Bot
    winner = 0


    if n_turns is None:
        n_turns = param.ROW_COUNT * param.COLUMN_COUNT // 2 + 1
    i = 0
    for player_first in (True, False,):
        move_seqs = (seq for seq in itertools.product(range(param.COLUMN_COUNT), repeat=n_turns))
        for move_seq in move_seqs:
            print(move_seq)
            board = Board()
            board.pretty_print_board()
            for it_col in move_seq:
                if player_first:
                    if not board.is_valid_location(it_col): break # Move onto next move sequence
                    game_over = play_turn(board, it_col, param.PLAYER_PIECE)
                    board.pretty_print_board()
                    if game_over: break

                bot_col = optimal_play(board, lookup_table)
                game_over = play_turn(board, bot_col, param.BOT_PIECE)
                board.pretty_print_board()
                if game_over: break

                if not player_first:
                    if not board.is_valid_location(it_col): break # Move onto next move sequence
                    game_over = play_turn(board, it_col, param.PLAYER_PIECE)
                    board.pretty_print_board()
                    if game_over: break


            with open(lookup_table_loc, 'w') as file:
                json.dump(lookup_table, file, indent=4)
                print(f"\033[1;32mSaved for move sequence {i}\033[0m")
                i += 1