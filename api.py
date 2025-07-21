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
import numpy as np

from camera_grid import Grid
from camera import Camera
import argparse

import multiprocessing as mp
from multiprocessing import Manager

import cv2
import asyncio

import os
import random

from plays import board2key  # Import the actual board2key function

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
debug_mode = True  # New debug mode flag

# Motor controller and camera globals
motor_controller = None
camera_process = None
manager = Manager()
shared_dict = manager.dict()

def camera_processing_target():
    """Camera processing function for multiprocessing"""
    try:
        grid = Grid(30, 0.3)
        camera = Camera("config/picam.yaml")
        camera.start_image_processing(grid, shared_dict)
    except Exception as e:
        print(f"Camera processing error: {e}")
        shared_dict["camera_error"] = str(e)

# Remove motor controller initialization from module level
# Initialize motor controller
def initialize_motor_controller():
    """Initialize motor controller only when needed and not in debug mode"""
    global motor_controller

    if debug_mode:
        print("[DEBUG MODE] Motor controller initialization skipped")
        return None

    if motor_controller is not None:
        return motor_controller

    try:
        import MechanicalSystemController as motor_controller_module
        motor_controller = motor_controller_module.MechanicalSystemController()
        print("Motor controller initialized")
        return motor_controller
    except ImportError as e:
        print(f"Motor controller not available - running in simulation mode: {e}")
        return None
    except Exception as e:
        print(f"Error initializing motor controller: {e}")
        return None

class MoveRequest(BaseModel):
    column: int

class BoardResponse(BaseModel):
    board: List[List[int]]
    winner: Optional[int]
    turn: int
    valid_moves: List[int]
    scores: Optional[List[float]] = None
    final_score: Optional[int] = None
    move_message: Optional[str] = None

class StartGameRequest(BaseModel):
    difficulty: str  # 'easy', 'medium', 'hard', 'impossible'
    who_starts: str  # 'player' or 'bot'
    training_mode: bool = False
    no_motors: bool = False
    no_camera: bool = False
    nickname: Optional[str] = None

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

class LeaderboardEntry(BaseModel):
    nickname: str
    score: int

class SaveScoreRequest(BaseModel):
    nickname: str
    score: int

# Global variables
current_nickname = ""
move_messages = {}

def load_move_messages():
    """Load move evaluation messages from JSON file"""
    global move_messages
    try:
        with open('move_messages.json', 'r') as f:
            move_messages = json.load(f)
        print("Move messages loaded successfully")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load move messages: {e}")
        # Fallback to default messages if file is missing
        move_messages = {
            "bad": ["That move could use some work."],
            "mid": ["An okay move."],
            "good": ["Nice move!"]
        }

# Load move messages on startup
load_move_messages()

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

def compute_score(board_array, winner):
    """Compute the final game score based on winner and moves played"""
    moves_played = int(np.sum(board_array != 0))
    max_moves = board_array.shape[0] * board_array.shape[1]
    if winner == param.BOT_PIECE:
        score = moves_played
    else:
        score = max_moves * 2 - moves_played
    return score * 10

def save_score_to_leaderboard(nickname: str, score: int, difficulty: str):
    """Save score to leaderboard JSON file - only keep highest score per nickname per difficulty"""
    leaderboard_file = "leaderboard.json"

    # Load existing leaderboard
    try:
        with open(leaderboard_file, 'r') as f:
            leaderboard_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard_data = {}

    # Initialize difficulty if it doesn't exist
    if difficulty not in leaderboard_data:
        leaderboard_data[difficulty] = []

    # Find existing entry for this nickname in this difficulty
    existing_entry = None
    for i, entry in enumerate(leaderboard_data[difficulty]):
        if entry["nickname"] == nickname:
            existing_entry = i
            break

    # Update or add score
    if existing_entry is not None:
        # Only update if new score is higher
        if score > leaderboard_data[difficulty][existing_entry]["score"]:
            leaderboard_data[difficulty][existing_entry]["score"] = score
    else:
        # Add new entry
        leaderboard_data[difficulty].append({"nickname": nickname, "score": score})

    # Sort by score (descending)
    leaderboard_data[difficulty].sort(key=lambda x: x["score"], reverse=True)

    # Save back to file
    with open(leaderboard_file, 'w') as f:
        json.dump(leaderboard_data, f, indent=2)

@app.get("/leaderboard")
def get_leaderboard(difficulty: str = "impossible", current_player: str = ""):
    """Get the leaderboard for a specific difficulty with current player's ranking"""
    leaderboard_file = "leaderboard.json"

    try:
        with open(leaderboard_file, 'r') as f:
            leaderboard_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard_data = {}

    # Get leaderboard for specific difficulty
    leaderboard = leaderboard_data.get(difficulty, [])

    # Sort by score (descending)
    leaderboard.sort(key=lambda x: x["score"], reverse=True)

    # Find current player's position
    player_rank = None
    player_entry = None
    for i, entry in enumerate(leaderboard):
        if entry["nickname"] == current_player:
            player_rank = i + 1
            player_entry = entry
            break

    # Get top 10
    top_10 = leaderboard[:10]

    # If current player is not in top 10 but exists, include them
    result = {
        "difficulty": difficulty,
        "top_10": top_10,
        "current_player": None,
        "available_difficulties": ["easy", "medium", "hard", "impossible"]
    }

    if player_entry and player_rank and player_rank > 10:
        result["current_player"] = {
            "rank": player_rank,
            "nickname": player_entry["nickname"],
            "score": player_entry["score"]
        }

    return result

# Add logging for unhandled exceptions
def log_exception(request, exc):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

app.add_exception_handler(Exception, log_exception)

def play_bot_turn_on_board(col):
    """Execute physical robot move for bot turn"""
    if debug_mode:
        print(f"[DEBUG MODE] Bot would move to column {col}")
        return

    # Initialize motor controller when needed
    controller = initialize_motor_controller()
    if controller is None:
        print(f"Simulating bot move to column {col}")
        return

    controller.activate_loader(controller.get_loader_index())
    controller.move_stepper_to(col + 1)
    controller.drop_token()
    controller.move_stepper_to_loader()

def start_camera_processing():
    """Start camera processing for player move detection"""
    global camera_process, shared_dict

    if debug_mode:
        print("[DEBUG MODE] Camera processing bypassed")
        return

    if camera_process is not None:
        return  # Already running

    try:
        shared_dict['game_over'] = False
        shared_dict['grid_ready'] = False
        shared_dict["camera_error"] = None
        shared_dict["camera_options"] = {}
        shared_dict["frame"] = None

        camera_process = mp.Process(target=camera_processing_target)
        camera_process.start()
        print("Camera process started successfully")
    except Exception as e:
        print(f"Failed to start camera process: {e}")
        camera_process = None

def wait_for_player_move():
    """Wait for camera to detect player move and return the column"""
    if debug_mode:
        print("[DEBUG MODE] Player move detection bypassed - use UI instead")
        return None

    if 'current_grid' not in shared_dict:
        return None

    # Wait for new grid data from camera
    timeout_counter = 0
    max_timeout = 300  # 30 seconds timeout (0.1s intervals)

    while timeout_counter < max_timeout:
        if 'current_grid' in shared_dict:
            current_grid = shared_dict['current_grid'].copy()
            col = game_board.get_valid_state(current_grid)
            if col is not None:
                shared_dict['last_player_move'] = col
                return col

        import time
        time.sleep(0.1)
        timeout_counter += 1

    return None  # Timeout

@app.get("/leaderboard")
def get_leaderboard(current_player: str = ""):
    """Get the current leaderboard with current player's ranking"""
    leaderboard_file = "leaderboard.json"

    try:
        with open(leaderboard_file, 'r') as f:
            leaderboard_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        leaderboard_data = {}

    # Sort by score (descending)
    for difficulty in leaderboard_data:
        leaderboard_data[difficulty].sort(key=lambda x: x["score"], reverse=True)

    # Find current player's position
    player_rank = None
    player_entry = None
    for difficulty, entries in leaderboard_data.items():
        for i, entry in enumerate(entries):
            if entry["nickname"] == current_player:
                player_rank = i + 1
                player_entry = entry
                break
        if player_rank is not None:
            break

    # Get top 10 for each difficulty
    top_10_by_difficulty = {difficulty: entries[:10] for difficulty, entries in leaderboard_data.items()}

    # If current player is not in top 10 but exists, include them
    result = {
        "top_10_by_difficulty": top_10_by_difficulty,
        "current_player": None
    }

    if player_entry and player_rank and player_rank > 10:
        result["current_player"] = {
            "rank": player_rank,
            "nickname": player_entry["nickname"],
            "score": player_entry["score"]
        }

    return result

@app.post("/save-score")
def save_score(request: SaveScoreRequest):
    """Save a score to the leaderboard"""
    # Use the current game difficulty
    save_score_to_leaderboard(request.nickname, request.score, selected_difficulty)
    return {"status": "Score saved successfully"}

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

def evaluate_move_quality(board, col, scores):
    """Evaluate the quality of a player's move based on scores"""
    if not scores or col >= len(scores):
        return "mid"  # Default to mid if no scores available

    move_score = scores[col]
    valid_moves = board.get_valid_locations()
    valid_scores = [scores[i] for i in valid_moves if i < len(scores)]

    if not valid_scores:
        return "mid"

    best_score = max(valid_scores)
    worst_score = min(valid_scores)

    # If all moves have the same score, it's mid
    if best_score == worst_score:
        return "mid"

    score_range = best_score - worst_score
    threshold_good = best_score - (score_range * 0.2)  # Top 20%
    threshold_bad = worst_score + (score_range * 0.2)  # Bottom 20%

    if move_score >= threshold_good:
        return "good"
    elif move_score <= threshold_bad:
        return "bad"
    else:
        return "mid"

def get_move_message(quality):
    """Get a random message for the move quality"""
    return random.choice(move_messages.get(quality, ["Move made."]))

@app.post("/start", response_model=BoardResponse)
def start_game_with_options(req: StartGameRequest):
    global game_board, winner, turn, selected_difficulty, reset_required, selected_debug, lookup_table, selected_training_mode, last_start_req, debug_mode, current_nickname

    # Store the request for potential auto-restart
    last_start_req = req

    print(f"Starting game with debug_mode={debug_mode}")

    # Skip magazine check in debug mode
    if not debug_mode:
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

        # Initialize hardware
        controller = initialize_motor_controller()
        if controller:
            controller.initialize_to_game_state()

        # Start camera processing if not in no_camera mode
        if not req.no_camera:
            start_camera_processing()
    else:
        print("[DEBUG MODE] Skipping hardware initialization and camera processing")

    game_board = Board()
    winner = None
    selected_difficulty = req.difficulty
    selected_debug = False # This is now controlled by the global debug_mode flag
    selected_training_mode = req.training_mode
    turn = 0 if req.who_starts == 'player' else 1
    reset_required = False

    try:
        with open('lookup_table_till_move_12.json', 'r') as file:
            lookup_table = json.load(file)
    except Exception:
        lookup_table = dict()

    current_nickname = getattr(req, 'nickname', '')

    return BoardResponse(
        board=game_board.board_array.tolist(),
        winner=winner,
        turn=turn,
        valid_moves=game_board.get_valid_locations(),
        scores=None,
        final_score=None
    )

def _process_player_move(player_col: int):
    """
    Processes a player's move, handles bot's turn, and returns the game state.
    This is the unified logic for both debug and normal gameplay.
    """
    global game_board, winner, turn, selected_difficulty, lookup_table, selected_training_mode, current_nickname

    # Calculate scores for move evaluation (both training and normal mode)
    scores = None
    move_message = None

    # Check if board is empty (no moves played yet)
    board_empty = np.sum(game_board.board_array != 0) == 0

    # Only calculate scores and generate messages if board is not empty
    if not board_empty:
        # Use unified function for score calculation
        scores = get_board_scores(game_board.board_array, lookup_table)

        # Generate move message for non-training mode AND training mode (show funny messages in both)
        if scores:
            quality = evaluate_move_quality(game_board, player_col, scores)
            move_message = get_move_message(quality)

    # Execute player move
    game_over = game_board.play_turn(player_col, param.PLAYER_PIECE)
    final_score = None

    if game_over:
        winner = param.PLAYER_PIECE
        final_score = compute_score(game_board.board_array, winner)
        # Auto-save score with difficulty
        if current_nickname.strip():
            save_score_to_leaderboard(current_nickname.strip(), final_score, selected_difficulty)
    else:
        turn ^= 1
        # Execute bot move
        if not game_over:
            col = get_bot_move(game_board, selected_difficulty)
            play_bot_turn_on_board(col)  # Will log in debug mode or execute physical move
            game_over = game_board.play_turn(col, param.BOT_PIECE)
            if game_over:
                winner = param.BOT_PIECE
                final_score = compute_score(game_board.board_array, winner)
                # Auto-save score with difficulty
                if current_nickname.strip():
                    save_score_to_leaderboard(current_nickname.strip(), final_score, selected_difficulty)
            turn ^= 1

    return BoardResponse(
        board=game_board.board_array.tolist(),
        winner=winner,
        turn=turn,
        valid_moves=game_board.get_valid_locations(),
        scores=scores if selected_training_mode else None,  # Show scores in training mode
        final_score=final_score,
        move_message=move_message
    )

@app.post("/move", response_model=BoardResponse)
def make_move(move: MoveRequest):
    """Make a move (UI-based in debug mode, camera-based otherwise)"""
    global game_board, winner, turn, selected_difficulty, selected_debug, lookup_table, selected_training_mode

    if debug_mode:
        # Debug mode: allow UI-based moves
        return make_debug_move(move)
    else:
        # Production mode: use camera detection
        return wait_for_player_move_endpoint()

def get_board_scores(board_array, lookup_table):
    """
    Unified function to get scores for a board position.
    First checks lookup table, then falls back to computation if needed.
    """
    try:
        # Use the exact same key generation as optimal_play function
        key = board2key(board_array)
        flipped_key = board2key(board_array[:, ::-1])

        # First try direct lookup
        if key in lookup_table:
            return lookup_table[key]

        # Try flipped board lookup
        elif flipped_key in lookup_table:
            return lookup_table[flipped_key][::-1]

        # If not in lookup table, compute using impossible mode algorithm
        else:
            print(f"Board position not found in lookup table, computing with impossible algorithm...")
            position = Position(board_array)
            solver = Solver()
            scores = solver.analyze(position, False)
            return scores

    except Exception as e:
        print(f"Error in get_board_scores: {e}")
        return None

def make_debug_move(move: MoveRequest):
    """Handle UI-based moves in debug mode"""
    global game_board, winner, turn

    if game_board is None:
        raise HTTPException(status_code=400, detail="Game not started. Please start a new game first.")

    if winner is not None:
        raise HTTPException(status_code=400, detail="Game is over.")

    if turn != 0:
        raise HTTPException(status_code=400, detail="It's not the player's turn.")

    col = move.column
    if col not in game_board.get_valid_locations():
        raise HTTPException(status_code=400, detail=f"Invalid move: column {col}.")

    return _process_player_move(col)

@app.post("/player-move", response_model=BoardResponse)
def wait_for_player_move_endpoint():
    """Endpoint to wait for camera-detected player move"""
    global game_board, winner, turn

    if game_board is None:
        raise HTTPException(status_code=400, detail="Game not started. Please start a new game first.")

    if debug_mode:
        raise HTTPException(status_code=400, detail="Use /move endpoint in debug mode.")

    # Check magazine status FIRST
    magazine1_full = check_magazine_1_status()
    magazine2_full = check_magazine_2_status()

    if not magazine1_full or not magazine2_full:
        magazines_status = []
        if not magazine1_full:
            magazines_status.append("Magazine 1 is empty")
        if not magazine2_full:
            magazines_status.append("Magazine 2 is empty")
        error_message = f"Cannot make move: {', '.join(magazines_status)}. Please fill the magazines before continuing."
        raise HTTPException(status_code=400, detail=error_message)

    if winner is not None:
        raise HTTPException(status_code=400, detail="Game is over.")

    if turn != 0:
        raise HTTPException(status_code=400, detail="It's not the player's turn.")

    # Wait for camera to detect player move
    detected_col = wait_for_player_move()

    if detected_col is None:
        raise HTTPException(status_code=408, detail="Timeout waiting for player move.")

    if detected_col not in game_board.get_valid_locations():
        raise HTTPException(status_code=400, detail=f"Invalid move detected: column {detected_col}.")

    return _process_player_move(detected_col)

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

@app.websocket("/ws/magazine-status")
async def magazine_status_websocket(websocket: WebSocket):
    await websocket.accept()
    print("Magazine status WebSocket connection accepted")

    try:
        while True:
            # Check magazine status
            magazine1_full = check_magazine_1_status()
            magazine2_full = check_magazine_2_status()

            status = {
                "magazine1_full": magazine1_full,
                "magazine2_full": magazine2_full
            }

            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(1)  # Send updates every second

    except Exception as e:
        print(f"Magazine status WebSocket error: {e}")
    finally:
        print("Magazine status WebSocket connection closed")

def check_magazine_1_status() -> bool:
    """
    Check if magazine 1 (red coins) is full.
    TODO: Implement actual sensor/hardware logic
    """
    # In debug mode, always return True
    if debug_mode:
        return True

    # Placeholder - replace with actual implementation
    # Could involve checking weight sensors, optical sensors, etc.
    return True  # Simulating full magazine

def check_magazine_2_status() -> bool:
    """
    Check if magazine 2 (yellow coins) is full.
    TODO: Implement actual sensor/hardware logic
    """
    # In debug mode, always return True
    if debug_mode:
        return True

    # Placeholder - replace with actual implementation
    # Could involve checking weight sensors, optical sensors, etc.
    return True  # Simulating full magazine

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
