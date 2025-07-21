import argparse
import asyncio
import json
import logging
import multiprocessing as mp
import os
import time
from contextlib import asynccontextmanager
from multiprocessing import Manager
from typing import Optional, List, Dict

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Assuming these files exist in the project structure
from camera import Camera
from camera_grid import Grid
from game_board import Board

print(f"[API] PID: {os.getpid()}")

# Process
camera_process = None
game_process = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    with Manager() as manager:
        app.state.manager = manager
        app.state.shared_dict = manager.dict()
        yield
        # Shutdown


app = FastAPI(lifespan=lifespan)
# Allow CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
current_nickname = ""
game_args = None # To store game arguments between new_game and first move

# Add logging for unhandled exceptions
def log_exception(request, exc):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

app.add_exception_handler(Exception, log_exception)

class MoveRequest(BaseModel):
    column: int

class StartGameRequest(BaseModel):
    difficulty: str  # 'easy', 'medium', 'hard', 'impossible'
    who_starts: str  # 'player' or 'bot'
    no_motors: bool = False
    no_camera: bool = False
    nickname: Optional[str] = None

class OptionUpdate(BaseModel):
    label: str
    value: bool

class StartCameraRequest(BaseModel):
    file_path: str

LEADERBOARD_FILE = "leaderboard.json"

def compute_score(board_array, winner):
    """Compute the final game score based on winner and moves played"""
    moves_played = int(np.sum(board_array != 0))
    max_moves = board_array.shape[0] * board_array.shape[1]
    if winner == 1:  # BOT_PIECE
        score = moves_played
    else:
        score = max_moves * 2 - moves_played
    return score * 10

def load_leaderboard() -> Dict[str, List[Dict]]:
    """Load leaderboard from file, create empty if doesn't exist"""
    if not os.path.exists(LEADERBOARD_FILE):
        return {
            "easy": [],
            "medium": [],
            "hard": [],
            "impossible": []
        }

    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "easy": [],
            "medium": [],
            "hard": [],
            "impossible": []
        }

def save_leaderboard(leaderboard: Dict[str, List[Dict]]) -> None:
    """Save leaderboard to file"""
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f, indent=2)
    except IOError as e:
        print(f"Failed to save leaderboard: {e}")

def add_score(nickname: str, score: int, difficulty: str) -> None:
    """Add or update a score in the leaderboard, keeping only the highest score per user"""
    if difficulty not in ["easy", "medium", "hard", "impossible"]:
        raise ValueError(f"Invalid difficulty: {difficulty}")

    leaderboard = load_leaderboard()

    # Find existing entry for this user
    existing_entry = None
    existing_index = None
    for i, entry in enumerate(leaderboard[difficulty]):
        if entry["nickname"] == nickname:
            existing_entry = entry
            existing_index = i
            break

    # Only update if this score is higher than existing score, or if no existing entry
    if existing_entry is None:
        # Add new entry
        leaderboard[difficulty].append({
            "nickname": nickname,
            "score": score
        })
    elif score > existing_entry["score"]:
        # Update existing entry with higher score
        leaderboard[difficulty][existing_index]["score"] = score
    # If score is lower or equal, don't update

    # Sort by score (descending) and keep only top 100
    leaderboard[difficulty].sort(key=lambda x: x["score"], reverse=True)
    leaderboard[difficulty] = leaderboard[difficulty][:100]

    save_leaderboard(leaderboard)

def get_leaderboard_data(difficulty: str, current_player: Optional[str] = None) -> Dict:
    """Get leaderboard for a specific difficulty"""
    if difficulty not in ["easy", "medium", "hard", "impossible"]:
        raise ValueError(f"Invalid difficulty: {difficulty}")

    leaderboard = load_leaderboard()
    top_10 = leaderboard[difficulty][:10]

    result = {
        "difficulty": difficulty,
        "top_10": top_10,
        "available_difficulties": ["easy", "medium", "hard", "impossible"]
    }

    # Find current player's rank if provided
    if current_player:
        for i, entry in enumerate(leaderboard[difficulty]):
            if entry["nickname"] == current_player:
                result["current_player"] = {
                    "rank": i + 1,
                    "nickname": entry["nickname"],
                    "score": entry["score"]
                }
                break

    return result

def get_jsonable_game_state(shared_dict):
    board = shared_dict.get("board")
    if isinstance(board, np.ndarray):
        board = board.tolist()

    valid_moves = shared_dict.get("valid_moves")
    if isinstance(valid_moves, np.ndarray):
        valid_moves = valid_moves.tolist()

    result = {
        "board": board,
        "winner": shared_dict.get("winner"),
        "turn": shared_dict.get("turn"),
        "valid_moves": valid_moves,
    }

    # Add final score if game is over
    winner = shared_dict.get("winner")
    if winner is not None and board is not None:
        board_array = np.array(board)
        final_score = compute_score(board_array, winner)
        result["final_score"] = final_score

        # Auto-save score to leaderboard if game is complete and we have a nickname
        nickname = shared_dict.get("nickname")
        difficulty = shared_dict.get("difficulty")
        if nickname and difficulty and not shared_dict.get("score_saved", False):
            try:
                add_score(nickname, final_score, difficulty)
                shared_dict["score_saved"] = True
            except Exception as e:
                print(f"Failed to save score: {e}")

    return result

def run_game(shared_dict, args):
    import main

    shared_dict["frame"] = None
    main.start_game(shared_dict, args)

def run_camera(shared_dict, config_file):
    grid = Grid(30, 0.3)
    camera = Camera(config_file)

    camera.start_image_processing(grid, shared_dict)

@app.post("/move")
def make_move(move: MoveRequest, request: Request):
    global game_process, game_args
    shared_dict = request.app.state.shared_dict

    # If game process isn't running, it's the first player move. Start it.
    if game_process is None and game_args is not None:
        # Prime the shared dict with the initial board state before starting
        # This ensures the game process starts with the board as it is.
        if "board" not in shared_dict:
             shared_dict["board"] = [[0] * 7 for _ in range(6)]

        game_process = mp.Process(target=run_game, args=(shared_dict, game_args,))
        game_process.start()
        # Wait for process to be ready to accept a move
        time.sleep(0.5) # A short delay to allow the process to start up

    if "turn" not in shared_dict or shared_dict.get("turn") != 0:
         raise HTTPException(status_code=400, detail="It's not the player's turn.")

    if "valid_moves" not in shared_dict or move.column not in shared_dict.get("valid_moves", []):
        raise HTTPException(status_code=400, detail="Invalid move.")

    shared_dict["player_move"] = move.column

    # Wait for the game process to consume the move
    start_time = time.time()
    while "player_move" in shared_dict:
        time.sleep(0.1)
        if time.time() - start_time > 5: # 5-second timeout
            return JSONResponse(
                status_code=500,
                content={"detail": "Game process did not respond to player move."}
            )

    # Now wait for the bot to make its move (turn becomes 0 again)
    start_time = time.time()
    # Wait until it's player's turn again (turn=0) or the game is over (winner is not None)
    while shared_dict.get("turn") != 0 and shared_dict.get("winner") is None:
        time.sleep(0.1)
        if time.time() - start_time > 20: # 20-second timeout for bot move
            return JSONResponse(
                status_code=500,
                content={"detail": "Bot did not make a move in time."}
            )

    return {"status": "ok"}

@app.get("/status")
def get_status(request: Request):
    shared_dict = request.app.state.shared_dict

    if "board" not in shared_dict:
        return JSONResponse(content={"error": "Game not started or state not available"}, status_code=404)

    return JSONResponse(content=get_jsonable_game_state(shared_dict))

@app.post("/new_game")
def new_game(option: StartGameRequest, request: Request):
    global game_process, current_nickname, game_args
    shared_dict = request.app.state.shared_dict
    manager = request.app.state.manager

    # Terminate any existing game process
    if game_process and game_process.is_alive():
        game_process.terminate()
        game_process.join()
    game_process = None

    game_args = argparse.Namespace(
        CONFIG_FILE="config/picam.yaml",
        level=[option.difficulty],
        bot_first=(option.who_starts == 'bot'),
        no_camera=option.no_camera,
        no_motors=option.no_motors,
        no_print=True
    )

    # Reset shared state for a new game
    shared_dict.clear()
    shared_dict["frame"] = None
    shared_dict["camera_options"] = manager.dict() # Re-initialize to avoid old data
    current_nickname = option.nickname or ""
    shared_dict["nickname"] = current_nickname
    shared_dict["difficulty"] = option.difficulty
    shared_dict["score_saved"] = False

    if game_args.bot_first:
        # If bot starts, launch the process and wait for its first move
        game_process = mp.Process(target=run_game, args=(shared_dict, game_args,))
        game_process.start()

        # Wait for the game process to initialize and bot to move
        start_time = time.time()
        # Wait until the turn is 0 (player's turn) or the game is over
        while shared_dict.get("turn") != 0 and shared_dict.get("winner") is None:
            time.sleep(0.1)
            if time.time() - start_time > 20: # 20-second timeout
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Game process failed to initialize in time."}
                )
        return {"status": "game started, bot has moved"}
    else:
        # If player starts, don't start the process yet.
        # Return an initial empty board state. The process will start on the first /move.
        initial_board = [[0] * 7 for _ in range(6)]
        shared_dict["board"] = initial_board
        shared_dict["turn"] = 0
        shared_dict["winner"] = None
        shared_dict["valid_moves"] = list(range(7))
        return {"status": "game ready for player move"}


@app.post("/start_camera")
def start_camera(config: StartCameraRequest, request: Request):
    global camera_process
    shared_dict = request.app.state.shared_dict

    if config.file_path not in ["config/default.yaml", "config/picam.yaml"]:
        return {"error": "The file path provided is not correct"}
    
    camera_process = mp.Process(target=run_camera, args=(shared_dict, config.file_path, ))
    camera_process.start()

    return {"status": "camera started"}

@app.post("/reset")
def reset_game(request: Request):
    global game_process
    shared_dict = request.app.state.shared_dict

    if game_process and game_process.is_alive():
        game_process.terminate()
        game_process.join()
    game_process = None

    shared_dict.clear()
    return {"status": "game reset"}


@app.get("/kill_camera")
def kill_camera():
    print("in kill camera")
    global camera_process

    if camera_process is None:
        return JSONResponse({"error": "There is no camera initialized"})
    
    camera_process.join()
    camera_process = None

    return JSONResponse({"status": "Camera successfully killed"})
    
@app.get("/options_list")
def get_options_list(request: Request):
    shared_dict = request.app.state.shared_dict

    if "camera_options" not in shared_dict:
        return JSONResponse({"error": "There is no camera initialized"})
    return JSONResponse(content=dict(shared_dict["camera_options"]))

@app.post("/option")
def update_camera_option(option: OptionUpdate, request: Request):
    shared_dict = request.app.state.shared_dict

    if "camera_options" not in shared_dict:
        return {"error": "There is no camera initialized"}
    
    shared_dict["camera_options"] = {
        **shared_dict["camera_options"],
        option.label: option.value
    }

    return {"status": "ok", "updated": {option.label: option.value}}

@app.websocket("/ws/camera")
async def camera_feed(websocket: WebSocket):
    shared_dict = websocket.app.state.shared_dict
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

            if "frame" in shared_dict and shared_dict["frame"] is not None:
                success, jpeg = cv2.imencode(".jpg", shared_dict["frame"])
                
                if success:
                    await websocket.send_bytes(jpeg.tobytes())

            await asyncio.sleep(0.05)  # ~20 FPS
    except Exception as e:
        print("WebSocket closed:", e)

@app.websocket("/ws/magazine_status")
async def magazine_status_feed(websocket: WebSocket):
    shared_dict = websocket.app.state.shared_dict
    await websocket.accept()

    try:
        while True:
            status = {
                "magazine_1_empty": shared_dict.get("magazine_1_empty"),
                "magazine_2_empty": shared_dict.get("magazine_2_empty"),
            }
            await websocket.send_json(status)
            await asyncio.sleep(1)  # Send status every second
    except Exception as e:
        print(f"Magazine status WebSocket closed: {e}")

@app.websocket("/ws/game_state")
async def game_state_feed(websocket: WebSocket):
    shared_dict = websocket.app.state.shared_dict
    await websocket.accept()
    last_state_str = None
    try:
        while True:
            current_state = get_jsonable_game_state(shared_dict)

            if current_state.get("board") is not None:
                current_state_str = json.dumps(current_state, sort_keys=True)
                if current_state_str != last_state_str:
                    await websocket.send_json(current_state)
                    last_state_str = current_state_str

            await asyncio.sleep(0.1)  # Poll for changes
    except Exception as e:
        print(f"Game state WebSocket closed: {e}")


@app.get("/leaderboard")
def get_leaderboard(difficulty: str = "impossible", current_player: str = ""):
    """Get the leaderboard for a specific difficulty with current player's ranking"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
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

    if player_entry and player_rank:
        result["current_player"] = {
            "rank": player_rank,
            "nickname": player_entry["nickname"],
            "score": player_entry["score"]
        }

    return result

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
