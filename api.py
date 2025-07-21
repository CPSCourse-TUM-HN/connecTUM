from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Optional, List
from game_board import Board
import modules.board_param as param
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from fastapi.responses import JSONResponse
from connect4_alg import Position, Solver

from camera_grid import Grid
from camera import Camera
import argparse

import multiprocessing as mp
from multiprocessing import Manager

import cv2
import asyncio

import os

print(f"[API] PID: {os.getpid()}")

app = FastAPI()

# Allow CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game state (for demo; in production, use sessions or DB)
game_board = None
winner = None
turn = 0  # 0: Player, 1: Bot
reset_required = False
last_board_state = None
selected_difficulty = 'impossible'
selected_debug = False
selected_training_mode = False
lookup_table = dict()

shared_dict = {}
game_process = None
camera_process = None

class MoveRequest(BaseModel):
    column: int

class BoardResponse(BaseModel):
    board: List[List[int]]
    winner: Optional[int]
    turn: int
    valid_moves: List[int]
    scores: Optional[List[float]] = None

class StartGameRequest(BaseModel):
    difficulty: str  # 'easy', 'medium', 'hard', 'impossible'
    who_starts: str  # 'player' or 'bot'
    debug: bool = False
    training_mode: bool = False
    no_motors: bool = False
    no_camera: bool = False

class StatusResponse(BaseModel):
    board: List[List[int]]
    winner: Optional[int]
    turn: int
    valid_moves: List[int]
    game_over: bool
    reset_required: bool
    message: Optional[str]

class MagazineStatusResponse(BaseModel):
    magazine1_full: bool
    magazine2_full: bool
    # Add other magazine fields as needed

class OptionUpdate(BaseModel):
    label: str
    value: bool

class StartCameraRequest(BaseModel):
    file_path: str

# Add logging for unhandled exceptions
def log_exception(request, exc):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

app.add_exception_handler(Exception, log_exception)

@app.post("/start", response_model=BoardResponse)
def start_game_with_options(req: StartGameRequest):
    global game_board, winner, turn, selected_difficulty, reset_required, selected_debug, lookup_table, selected_training_mode, last_start_req

    # Store the request for potential auto-restart
    last_start_req = req

    # Check magazine status before starting game
    magazine1_full = check_magazine_1_status()
    magazine2_full = check_magazine_2_status()

    # Only allow game start if both magazines are full (full=True)
    if not magazine1_full or not magazine2_full:
        magazines_status = []
        if not magazine1_full:
            magazines_status.append("Magazine 1 is empty")
        if not magazine2_full:
            magazines_status.append("Magazine 2 is empty")
        error_message = f"Cannot start game: {', '.join(magazines_status)}. Please fill the magazines before starting."
        raise HTTPException(status_code=400, detail=error_message)

    game_board = Board()
    winner = None
    selected_difficulty = req.difficulty
    selected_debug = req.debug
    selected_training_mode = req.training_mode
    turn = 0 if req.who_starts == 'player' else 1
    reset_required = False
    # Load lookup table for impossible mode
    if selected_difficulty == 'impossible' or selected_training_mode:
        try:
            with open('lookup_table.json', 'r') as file:
                lookup_table = json.load(file)
        except Exception:
            lookup_table = dict()
    return BoardResponse(
        board=game_board.board_array.tolist(),
        winner=winner,
        turn=turn,
        valid_moves=game_board.get_valid_locations(),
        scores=None
    )

@app.post("/move", response_model=BoardResponse)
def make_move(move: MoveRequest):
    global game_board, winner, turn, selected_difficulty, selected_debug, lookup_table, selected_training_mode, last_start_req, paused_on_empty

    # Check magazine status FIRST before any other checks
    magazine1_full = check_magazine_1_status()
    magazine2_full = check_magazine_2_status()

    # Pause game if magazines are empty
    if not magazine1_full or not magazine2_full:
        paused_on_empty = True
        magazines_status = []
        if not magazine1_full:
            magazines_status.append("Magazine 1 is empty")
        if not magazine2_full:
            magazines_status.append("Magazine 2 is empty")
        error_message = f"Cannot make move: {', '.join(magazines_status)}. Please fill the magazines before continuing."
        raise HTTPException(status_code=400, detail=error_message)


    # Then check game state
    if not hasattr(game_board, 'play_turn'):
        raise HTTPException(status_code=500, detail="Board object missing play_turn method.")
    if winner is not None:
        raise HTTPException(status_code=400, detail="Game is over.")
    if move.column not in game_board.get_valid_locations():
        raise HTTPException(status_code=400, detail="Invalid move.")

    # Player move (either human or algorithm in debug mode)
    if selected_debug:
        col = get_bot_move(game_board, selected_difficulty)
        game_over = game_board.play_turn(col, param.PLAYER_PIECE)
    else:
        game_over = game_board.play_turn(move.column, param.PLAYER_PIECE)
    scores = None
    if selected_training_mode and not game_over:
        try:
            board_arr = game_board.board_array
            key = "".join(map(str, board_arr.flatten()))
            flipped_key = "".join(map(str, board_arr[:, ::-1].flatten()))
            if key in lookup_table:
                scores = lookup_table[key]
            elif flipped_key in lookup_table:
                scores = lookup_table[flipped_key][::-1]
            else:
                # Compute scores using Solver if not found in lookup_table
                position = Position(board_arr)
                solver = Solver()
                scores = solver.analyze(position, False)
        except Exception as e:
            scores = None
    if game_over:
        winner = param.PLAYER_PIECE
    else:
        turn ^= 1
        # Bot move (always algorithm)
        if not game_over:
            col = get_bot_move(game_board, selected_difficulty)
            game_over = game_board.play_turn(col, param.BOT_PIECE)
            if game_over:
                winner = param.BOT_PIECE
            turn ^= 1
    return BoardResponse(
        board=game_board.board_array.tolist(),
        winner=winner,
        turn=turn,
        valid_moves=game_board.get_valid_locations(),
        scores=scores
    )

@app.get("/state", response_model=BoardResponse)
def get_state():
    global game_board, winner, turn
    if game_board is None:
        raise HTTPException(status_code=400, detail="Game not started.")
    return BoardResponse(
        board=game_board.board_array.tolist(),
        winner=winner,
        turn=turn,
        valid_moves=game_board.get_valid_locations()
    )

@app.post("/reset", response_model=BoardResponse)
def reset_game():
    # Use the same logic as start_game_with_options, but with default values
    req = StartGameRequest(difficulty='impossible', who_starts='player')
    return start_game_with_options(req)

@app.get("/status", response_model=StatusResponse)
def get_status():
    global game_board, winner, turn, reset_required
    if game_board is None:
        raise HTTPException(status_code=400, detail="Game not started.")
    # Simulate camera-based reset detection (replace with real logic)
    # For now, if board is empty, consider reset detected
    is_empty = all(cell == 0 for row in game_board.board_array.tolist() for cell in row)
    if reset_required and is_empty:
        reset_required = False
    message = None
    if winner is not None:
        message = "Game over! Winner: {}. Please clean the board.".format(
            "Player" if winner == 1 else "Bot")
        reset_required = True
    elif reset_required:
        message = "Please clean the board to start a new game."
    return StatusResponse(
        board=game_board.board_array.tolist(),
        winner=winner,
        turn=turn,
        valid_moves=game_board.get_valid_locations(),
        game_over=winner is not None,
        reset_required=reset_required,
        message=message
    )

@app.get("/magazine-status", response_model=MagazineStatusResponse)
def check_if_magazine_empty():
    """
    Check the status of both magazines.
    Returns True if magazine is full, False if empty.

    TODO: Implement actual hardware/sensor logic here
    """
    # Placeholder logic - replace with actual implementation
    # This could involve checking sensors, camera detection, etc.

    # For now, simulate some logic (replace with real implementation)
    import random

    # Example: Check magazine 1 (red coins)
    magazine1_full = check_magazine_1_status()

    # Example: Check magazine 2 (yellow coins)
    magazine2_full = check_magazine_2_status()

    return MagazineStatusResponse(
        magazine1_full=magazine1_full,
        magazine2_full=magazine2_full
    )

def check_magazine_1_status() -> bool:
    """
    Check if magazine 1 (red coins) is full.
    TODO: Implement actual sensor/hardware logic
    """
    # Placeholder - replace with actual implementation
    # Could involve checking weight sensors, optical sensors, etc.
    return True  # Simulating empty magazine for testing

def check_magazine_2_status() -> bool:
    """
    Check if magazine 2 (yellow coins) is full.
    TODO: Implement actual sensor/hardware logic
    """
    # Placeholder - replace with actual implementation
    # Could involve checking weight sensors, optical sensors, etc.
    return True  # Simulating empty magazine for testing

def get_bot_move(board, difficulty):
    from plays import easy_play, medium_play, hard_play, optimal_play
    if difficulty == 'easy':
        return easy_play(board)
    elif difficulty == 'medium':
        return medium_play(board)
    elif difficulty == 'hard':
        return hard_play(board)
    elif difficulty == 'impossible':
        return optimal_play(board, lookup_table)
    else:
        return easy_play(board)


#** Julien's Part (settings/debug) **#

def run_game(args):
    import main

    manager = Manager()
    shared_dict = manager.dict()
    shared_dict["frame"] = None

    main.start_game(shared_dict, args)

def run_camera(config_file, shared_dict):
    grid = Grid(30, 0.3)
    camera = Camera(config_file)

    camera.start_image_processing(grid, shared_dict)

@app.post("/new_game")
def new_game(option: StartGameRequest):
    args = argparse.Namespace(
        CONFIG_FILE="config/picam.yaml",
        level=['impossible'],
        bot_first=False,
        t=False,
        no_camera=True,
        no_motors=True,
        no_print=False
    )

    game_process = mp.Process(target=run_game, args=(args,))
    game_process.start()

    return {"status": "game started"}

@app.post("/start_camera")
def start_camera(config: StartCameraRequest):
    if config.file_path not in ["config/default.yaml", "config/picam.yaml"]:
        return {"error": "The file path provided is not correct"}
    
    camera_process = mp.Process(target=run_camera, args=(config.file_path, shared_dict))
    camera_process.start()

    return {"status": "camera started"}

@app.get("/kill_camera")
def kill_camera():
    if camera_process is None:
        return JSONResponse({"error": "There is no camera initialized"})
    
    camera_process.join()
    camera_process = None

    return JSONResponse({"status": "Camera successfully killed"})
    
@app.get("/options_list")
def get_options_list():
    if "camera_options" not in shared_dict:
        return JSONResponse({"error": "There is no camera initialized"})
    return JSONResponse(content=dict(shared_dict["camera_options"]))

@app.post("/option")
def update_camera_option(option: OptionUpdate):
    if "camera_options" not in shared_dict:
        return {"error": "There is no camera initialized"}
    
    shared_dict["camera_options"] = {
        **shared_dict["camera_options"],
        option.label: option.value
    }

    return {"status": "ok", "updated": {option.label: option.value}}

@app.websocket("/ws/camera")
async def camera_feed(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Use asyncio.wait_for to handle optional messages while still sending frames
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                # print(f"Received: {data}")
                try:
                    message = json.loads(data)
                    if "carousel_index" in message:
                        # print("User is viewing image index:", message["carousel_index"])
                        shared_dict["carousel_index"] = int(message["carousel_index"])
                except json.JSONDecodeError:
                    print("Invalid JSON:", data)
            
            except asyncio.TimeoutError:
                pass  # No incoming message; continue sending frame

            if shared_dict["frame"] is not None:
                success, jpeg = cv2.imencode(".jpg", shared_dict["frame"])
                
                if success:
                    await websocket.send_bytes(jpeg.tobytes())

            await asyncio.sleep(0.05)  # ~20 FPS
    except Exception as e:
        print("WebSocket closed:", e)
    
