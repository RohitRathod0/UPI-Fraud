Write-Host "Starting UPI Fraud Detection API..." -ForegroundColor Green
Write-Host ""
cd server
python -m uvicorn app:app --host 0.0.0.0 --port 8000


