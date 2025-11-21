@echo off
echo Killing any existing Streamlit processes on port 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 >nul
echo Starting Streamlit app on port 8501...
streamlit run streamlit_app.py

