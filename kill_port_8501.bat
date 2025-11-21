@echo off
echo Killing process on port 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    echo Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo Port 8501 should now be free.
timeout /t 2 >nul
echo Starting Streamlit app...
streamlit run streamlit_app.py

