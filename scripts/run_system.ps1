# PowerShell script to run the entire system (backend + frontend)

# Start the backend
Start-Process -NoNewWindow powershell -ArgumentList "-Command `"cd '$pwd'; .\venv\Scripts\Activate.ps1; python backend\run_service.py`""

# Wait for backend to start
Write-Host "Starting backend service..."
Start-Sleep -Seconds 5

# Start the frontend
Write-Host "Starting frontend development server..."
Start-Process -NoNewWindow powershell -ArgumentList "-Command `"cd '$pwd\frontend'; npm run dev`""

Write-Host "Both services are running!"
Write-Host "- Backend: http://localhost:8081"
Write-Host "- Frontend: http://localhost:3000"
Write-Host "Press Ctrl+C to stop all processes"

# Keep the script running
while ($true) { Start-Sleep -Seconds 1 }