# Rotate screen
wlr-randr --output HDMI-A-1 --transform 180

# Start servers (backend and frontend)
~/Desktop/connectum-v2/server.sh

# Wait for the servers to start
sleep 8

# Set display variables for GUI apps
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority

# Open browser to the frontend
chromium-browser --start-fullscreen http://localhost:3000