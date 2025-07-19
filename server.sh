#!/bin/bash

# Go into the environment
source venv/bin/activate

# Start backend in new terminal (api.py)
cd ~/Desktop/connectum-v2 || exit
gnome-terminal -- bash -c "uvicorn api:app; exec bash"

# Start frontend in new terminal
cd ~/Desktop/connectum-v2/connectum-frontend || exit
gnome-terminal -- bash -c "npm run dev; exec bash"

# Open browser to the frontend
sleep 8
chromium-browser --start-fullscreen http://localhost:3000