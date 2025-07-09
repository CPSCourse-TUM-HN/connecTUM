# code from https://roboticsproject.readthedocs.io/en/latest/ConnectFourAlgorithm.html
import argparse
import json
import os

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
no_motors = False

camera_process = None

def play_game(shared_dict, bot_first, play_in_terminal):
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
    turn = 0 if not bot_first else 1  # 0: Player, 1: Bot
    play_alg = {
        'easy': easy_play,
        'medium': medium_play,
        'hard': hard_play,
        'impossible': lambda board: optimal_play(board, lookup_table),
    }
    mode = 'impossible'
    winner = param.EMPTY

    # Wait for camera to start producing data
    print("Waiting for camera to initialize...")
    while not play_in_terminal and ('grid_ready' not in shared_dict or not shared_dict['grid_ready']):
        #print(shared_dict.get("grid_ready", "not there"))
        if shared_dict["camera_error"] is not None:
            print("Error during camera initialization. Exit program.")
            exit(1)
        pass

    print("Camera ready, game starting!")

    # HARDWARE INITIALIZATION
    send_integer(4)
    send_integer(7)
    send_integer(100)

    while not game_over:
        board.pretty_print_board()

        if turn == 0 and ('current_grid' in shared_dict or play_in_terminal):
            valid_move = False
            while not valid_move:
                if play_in_terminal:
                    col = get_input()
                    if 0 <= col < param.COLUMN_COUNT and board.is_valid_location(col):
                        valid_move = True
                    else:
                        print("Invalid column. Try again.")
                    continue

                # Wait for new grid data from camera
                new_grid = None
                while not play_in_terminal and new_grid is None:
                    if shared_dict["camera_error"] is not None:
                        shared_dict["game_over"] = True # Force the camera to destroy itself
                        camera_process.join()
                        print("An error has occured with the camera.\nIf the issue has been fixed, you can restart the camera by pressing 'c', if not you can quit this program with 'q'.")

                        i = None
                        while i not in ["q", "c"]:
                            i = input("Please enter 'c' or 'q':")
                            shared_dict["camera_error"] = None
                            continue

                        if camera is not None and i == "c":
                            shared_dict["game_over"] = False
                            camera_process.start()
                        elif i == "q":
                            print("Camera has not been fixed. Exit program.")
                            exit(1)

                    if 'current_grid' in shared_dict:
                        new_grid = shared_dict['current_grid'].copy()

                col = board.get_valid_state(new_grid)
                if col is not None:
                    valid_move = True
                    shared_dict['last_player_move'] = col  # Store the move
            game_over = board.play_turn(col, param.PLAYER_PIECE)
            if game_over:
                winner = param.PLAYER_PIECE
        else:
            col = play_alg[mode](board)
            game_over = board.play_turn(col, param.BOT_PIECE)
            send_integer(col)
            send_integer(200)
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


def get_input():
    col = None

    while col is None:
        try:
            col = int(input("Player 1 Make your Selection (0-6): "))
        except ValueError:
            print("Please enter a valid integer between 0 and 6.")

    return col

def camera_processing(config_file, grid, shared_dict):
    camera = Camera(config_file)
    camera.start_image_processing(grid, shared_dict)

def send_integer(number):
    if no_motors:
        return

    try:
        with serial.Serial(serial_port, baud_rate, timeout=timeout_sec) as ser:
            time.sleep(2)
            ser.write((str(number)).encode('utf-8'))
    except serial.SerialException as e:
        print(f"Serial error: {e}")


if __name__ == "__main__":
    # Args parser
    parser = argparse.ArgumentParser()
    parser.add_argument("CONFIG_FILE", type=str, nargs="?", help="Path to a configuration file for the camera")
    parser.add_argument("-b", "--bot-first", help="Make the bot play the first move", action="store_true")
    parser.add_argument("-t", help="Play a game only in the terminal (equivalent to: --no-camera --no-motors)", action="store_true")
    parser.add_argument("--no-camera", help="Play a game using the terminal instead of the camera", action="store_true")
    parser.add_argument("--no-motors", help="Play a game without moving the motors", action="store_true")
    args = parser.parse_args()

    if not args.no_motors and not args.t:
        import serial
        import time
    else:
        no_motors = True
        print("No motors")

    # Create the camera grid
    grid = Grid(30, 0.3)

    if not args.no_camera and not args.t:
        if args.CONFIG_FILE is None:
            parser.error("The following arguments is required: CONFIG_FILE")
        manager = Manager()

        shared_dict = manager.dict()
        shared_dict['game_over'] = False
        shared_dict['grid_ready'] = False
        shared_dict["camera_error"] = None

        camera = Camera(args.CONFIG_FILE)
        camera_process = mp.Process(target=camera_processing, args=(args.CONFIG_FILE, grid, shared_dict))
        camera_process.start()

        play_game(shared_dict, args.bot_first, False)
        camera.destroy()
        camera_process.join()
        exit(0)
    else:
        print("Terminal mode")
        play_game({}, args.bot_first, True)
        exit(0)
