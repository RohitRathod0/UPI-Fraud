@echo off
echo Checking if port 8000 is available...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo Port 8000 is in use. Trying port 8001 instead...
    cd server
    python -m uvicorn app:app --host 0.0.0.0 --port 8001
) else (
    echo Port 8000 is free. Starting server...
    cd server
    python -m uvicorn app:app --host 0.0.0.0 --port 8000
)
pause


