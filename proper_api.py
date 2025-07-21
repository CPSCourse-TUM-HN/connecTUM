from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from fastapi.responses import JSONResponse
import numpy as np

from camera import Camera
from camera_grid import Grid
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
debug_mode = True  # New debug mode flag

# Process
camera_process = None
game_process = None
manager = Manager()
shared_dict = manager.dict()

# Global variables
current_nickname = ""
move_messages = {}

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

def run_game(args):
    global shared_dict
    import main

    shared_dict["frame"] = None
    main.start_game(shared_dict, args)

def run_camera(config_file):
    global shared_dict
    
    grid = Grid(30, 0.3)
    camera = Camera(config_file)

    camera.start_image_processing(grid, shared_dict)

@app.post("/new_game")
def new_game(option: StartGameRequest):
    global game_process

    args = argparse.Namespace(
        CONFIG_FILE="config/picam.yaml",
        level=['impossible'],
        bot_first=False,
        t=False,
        no_camera=False,
        no_motors=True,
        no_print=False
    )

    game_process = mp.Process(target=run_game, args=(args,))
    game_process.start()

    return {"status": "game started"}

@app.post("/start_camera")
def start_camera(config: StartCameraRequest):
    global camera_process

    if config.file_path not in ["config/default.yaml", "config/picam.yaml"]:
        return {"error": "The file path provided is not correct"}
    
    camera_process = mp.Process(target=run_camera, args=(config.file_path, ))
    camera_process.start()

    return {"status": "camera started"}

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
def get_options_list():
    global shared_dict

    if "camera_options" not in shared_dict:
        return JSONResponse({"error": "There is no camera initialized"})
    return JSONResponse(content=dict(shared_dict["camera_options"]))

@app.post("/option")
def update_camera_option(option: OptionUpdate):
    global shared_dict

    if "camera_options" not in shared_dict:
        return {"error": "There is no camera initialized"}
    
    shared_dict["camera_options"] = {
        **shared_dict["camera_options"],
        option.label: option.value
    }

    return {"status": "ok", "updated": {option.label: option.value}}

@app.websocket("/ws/camera")
async def camera_feed(websocket: WebSocket):
    global shared_dict
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
