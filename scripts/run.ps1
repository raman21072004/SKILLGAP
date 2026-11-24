# Starts backend (port 8000) and frontend (port 5173) in two windows.
$root = Split-Path -Parent $PSScriptRoot
Start-Process powershell -WorkingDirectory "$root\backend" -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -WorkingDirectory "$root\frontend" -ArgumentList "-NoExit", "-Command", "npm run dev"
Write-Host "Backend: http://localhost:8000/docs   Frontend: http://localhost:5173"
