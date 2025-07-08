# code from https://roboticsproject.readthedocs.io/en/latest/ConnectFourAlgorithm.html
import json
import os

# import serial
# import time

import multiprocessing as mp
from multiprocessing import Manager

from camera_grid import Grid
from camera import Camera
from game_board import Board
from plays import easy_play, medium_play, hard_play, optimal_play

import modules.board_param as param

# HARDWARE INITIALIZATION
serial_port = '/dev/ttyUSB0'
baud_rate = 9600
timeout_sec = 2

def play_game(shared_dict):
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

    # HARDWARE INITIALIZATION
    send_integer(4)
    send_integer(7)
    send_integer(100)

    while not game_over:
        #current_grid = shared_dict['current_grid'].copy()
        board.pretty_print_board()
        if turn == 0 and 'current_grid' in shared_dict:
            valid_move = False
            while not valid_move:
                # Wait for new grid data from camera
                new_grid = None
                while new_grid is None:
                    if 'current_grid' in shared_dict:
                        new_grid = shared_dict['current_grid'].copy()
                col = board.get_valid_state(new_grid)
                if col is not None:
                    valid_move = True
                    # shared_dict['last_player_move'] = col  # Store the move
            game_over = board.play_turn(col, param.PLAYER_PIECE)
            if game_over:
                winner = param.PLAYER_PIECE
        else:
            col = play_alg[mode](board)
            game_over = board.play_turn(col, param.BOT_PIECE)
            send_integer(col)
            time.sleep(6)
            send_integer(200)
            time.sleep(10)
            send_integer(100)
            if game_over:
                winner = param.BOT_PIECE

        if len(board.get_valid_locations()) == 0 and not game_over:
            board.pretty_print_board()
            print("Game is a draw!")
            game_over = True
            winner = param.EMPTY
        turn ^= 1  # Switch turns
    board.print_final_score(winner)
    shared_dict['game_over'] = True
    # Save learned moves
    with open(lookup_table_loc, 'w') as file:
        json.dump(lookup_table, file, indent=4)

def camera_processing(cam, grid, shared_dict):
    cam.start_image_processing(grid, shared_dict)

def send_integer(number):
    try:
        with serial.Serial(serial_port, baud_rate, timeout=timeout_sec) as ser:
            time.sleep(2)
            ser.write((str(number)).encode('utf-8'))
    except serial.SerialException as e:
        print(f"Serial error: {e}")


if __name__ == "__main__":
    manager = Manager()

    shared_dict = manager.dict()
    shared_dict['game_over'] = False
    shared_dict['grid_ready'] = False

    grid = Grid(30, 0.3)
    camera = Camera()
    camera_process = mp.Process(target=camera_processing, args=(camera, grid, shared_dict))

    camera_process.start()
    play_game(shared_dict)
    camera_process.join()
    
    # train()Details: und nicht wie hier
