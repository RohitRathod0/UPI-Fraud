@echo off
echo Starting UPI Fraud Detection API...
echo.
cd server
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause


