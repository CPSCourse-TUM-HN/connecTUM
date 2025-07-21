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

motor_controller = None
camera_process = None

def play_game(shared_dict, level, bot_first, play_in_terminal, no_print):
    lookup_table_loc = 'lookup_table_till_move_10.json'

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
    winner = param.EMPTY

    # Wait for camera to start producing data
    if not play_in_terminal:
        print("Waiting for camera to initialize...")
    
    while not play_in_terminal and ('grid_ready' not in shared_dict or not shared_dict['grid_ready']):
        #print(shared_dict.get("grid_ready", "not there"))
        if shared_dict["camera_error"] is not None:
            print("Error during camera initialization. Exit program.")
            exit(1)
        pass

    print("Camera ready or not required, game starting!")

    # HARDWARE INITIALIZATION
    if motor_controller:
        motor_controller.initialize_to_game_state()

    while not game_over:
        valid_move = False

        if not no_print:
            board.pretty_print_board()
        
        if turn == 0 and ('current_grid' in shared_dict or play_in_terminal):
            while not valid_move:
                if play_in_terminal:
                    col = get_input()
                    if 0 <= col < param.COLUMN_COUNT and board.is_valid_location(col):
                        valid_move = True
                    # else:
                    #     print("Invalid column. Try again.")
                    continue

                # Wait for new grid data from camera
                new_grid = None
                while not play_in_terminal and new_grid is None:
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
            col = play_alg[level](board)
            played_pos = -1

            if motor_controller is not None:
                motor_controller.activate_loader(motor_controller.get_loader_index())
                motor_controller.move_stepper_to(col + 1)
                motor_controller.drop_token()

            # Block game if the coin is not properly dropped
            while not valid_move:
                # Wait for new grid data from camera
                new_grid = None
                while not play_in_terminal and new_grid is None:
                    if 'current_grid' in shared_dict:
                        new_grid = shared_dict['current_grid'].copy()
                        played_pos = board.get_valid_state(new_grid)

                if play_in_terminal or played_pos == col:
                    valid_move = True
                    shared_dict["last_bot_move"] = col

            if motor_controller is not None:
                motor_controller.reset_drop_servo()
                motor_controller.move_stepper_to_loader()

            game_over = board.play_turn(col, param.BOT_PIECE)
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

def start_game(shared_dict, args):
    global no_motors, serial

    # Import motor lbrary
    if not args.no_motors and not args.t:
        import MechanicalSystemController as motor_controller_module
        motor_controller = motor_controller_module.MechanicalSystemController()
    else:
        no_motors = True
        print("No motors")

    # Create the camera grid
    grid = Grid(30, 0.3)

    # Camera process
    if not args.no_camera and not args.t:
        if args.CONFIG_FILE is None:
            parser.error("The following arguments is required: CONFIG_FILE")

        shared_dict['game_over'] = False
        shared_dict['grid_ready'] = False
        shared_dict["camera_error"] = None
        shared_dict["camera_options"] = {}

        camera_process = mp.Process(target=camera_processing, args=(args.CONFIG_FILE, grid, shared_dict))
        camera_process.start()

    else:
        print("Terminal mode")

    print(f"Difficulty level: {args.level[0]}")
    play_game(shared_dict, args.level[0], args.bot_first, (args.no_camera or args.t), args.no_print)

    if not args.no_camera and not args.t:
        camera_process.join()


if __name__ == "__main__":
    manager = Manager()
    shared_dict = manager.dict()

    # Args Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("CONFIG_FILE", type=str, nargs="?", help="Path to a configuration file for the camera")
    parser.add_argument("-l", "--level", type=str, nargs=1, default=["impossible"], choices=["easy", "medium", "hard", "impossible"], help="Select the level of difficulty (Default: impossible)")
    parser.add_argument("-b", "--bot-first", help="Make the bot play the first move", action="store_true")
    parser.add_argument("-t", help="Play a game only in the terminal (equivalent to: --no-camera --no-motors)", action="store_true")
    parser.add_argument("--no-camera", help="Play a game using the terminal instead of the camera", action="store_true")
    parser.add_argument("--no-motors", help="Play a game without moving the motors", action="store_true")
    parser.add_argument("--no-print", help="Play a game without printing the board in the terminal", action="store_true")
    
    args = parser.parse_args()

    start_game(shared_dict, args)
    exit(0)
