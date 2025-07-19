#!/bin/bash

# Go into the environment
source venv/bin/activate

# Start backend (main.py)
cd ~/Desktop/test-ui || exit
#gnome-terminal -- bash -c "python3 main.py --no-motors --no-camera; exec bash" &
python3 main.py --no-motors --no-camera &

# Start frontend in new terminal
cd ~/Desktop/test-ui/connectum-frontend || exit
gnome-terminal -- bash -c "npm run dev; exec bash"

# Open browser to the frontend
sleep 8
chromium-browser --start-fullscreen http://localhost:3000
