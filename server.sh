#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p ./log

echo "Starting Connectum services..."

# Go into the environment
source ./venv/bin/activate || exit
echo "✓ Virtual environment activated"

# Start backend in background
uvicorn api:app > ./log/api.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

# Start frontend in background
cd ./connectum-frontend || exit
npm run dev > ../log/webapp.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "Services are running in background:"
echo "  Backend:  http://localhost:8000 (PID: $BACKEND_PID)"
echo "  Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "Check logs:"
echo "  Backend:  tail -f ./log/api.log"
echo "  Frontend: tail -f ./log/webapp.log"
echo ""
echo "To stop services: kill $BACKEND_PID $FRONTEND_PID"

# Wait briefly, then try to open the browser on port 3000
sleep 2
echo "Opening browser at http://localhost:3000..."
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:3000
elif command -v gnome-open >/dev/null 2>&1; then
  gnome-open http://localhost:3000
elif command -v open >/dev/null 2>&1; then
  open http://localhost:3000
else
  echo "Could not auto-open browser. Please visit http://localhost:3000 manually."
fi

deactivate
