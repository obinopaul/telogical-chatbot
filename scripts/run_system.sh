#!/bin/bash

# Script to run the entire system (backend + frontend)

# Navigate to project root
cd "$(dirname "$0")/.."

# Start the backend
echo "Starting backend service..."
source venv/bin/activate
python backend/run_service.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start the frontend
echo "Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "Both services are running!"
echo "- Backend: http://localhost:8081"
echo "- Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all processes"

# Handle termination
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait