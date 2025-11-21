Write-Host "Starting UPI Fraud Detection API..." -ForegroundColor Green
Write-Host ""

# Check if port 8000 is in use
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "Port 8000 is in use. Using port 8001 instead..." -ForegroundColor Yellow
    Write-Host "Access at: http://localhost:8001" -ForegroundColor Cyan
    $port = 8001
} else {
    Write-Host "Port 8000 is available. Starting server..." -ForegroundColor Green
    Write-Host "Access at: http://localhost:8000" -ForegroundColor Cyan
    $port = 8000
}

cd server
python -m uvicorn app:app --host 0.0.0.0 --port $port


