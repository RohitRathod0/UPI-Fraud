@echo off
echo Killing process using port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Process %%a killed
)
echo Port 8000 is now free!
pause


