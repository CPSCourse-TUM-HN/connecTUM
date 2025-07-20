#!/bin/bash

# Go into the connectum folder
cd ~/Desktop/connectum-v2 || exit

# Go into the environment
source venv/bin/activate || exit

# Start backend in background
uvicorn api:app > ~/Desktop/connectum-v2/log/api.log 2>&1 &

API_PID = $!

# Start frontend in background
cd ~/Desktop/connectum-v2/connectum-frontend || exit
npm run dev > ~/Desktop/connectum-v2/log/webapp.log 2>&1 &

WEBAPP_PID = $!

echo "[API]: $API_PID"
echo "[WEBAPP]: $WEBAPP_PID"

# Open browser to the frontend
sleep 8
chromium-browser --start-fullscreen http://localhost:3000