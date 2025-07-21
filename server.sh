#!/bin/bash

# Go into the connectum folder
cd ~/Desktop/connectum-v2 || exit

# Go into the environment
source venv/bin/activate || exit

# Start backend in background
uvicorn api:app > ~/Desktop/connectum-v2/log/api.log 2>&1 &

# Start frontend in background
cd ~/Desktop/connectum-v2/connectum-frontend || exit
npm run  dev > ~/Desktop/connectum-v2/log/webapp.log 2>&1 &

deactivate