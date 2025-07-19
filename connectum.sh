#!/bin/bash

# Go into the environment
source venv/bin/activate

# Start backend (main.py)
cd ~/Desktop/connectum || exit
python3 main.py &

# Start frontend in new terminal
cd ~/Desktop/connectum-frontend || exit
gnome-terminal -- bash -c "npm run dev; exec bash"

# Open browser to the frontend
sleep 2
xdg-open http://localhost:3000