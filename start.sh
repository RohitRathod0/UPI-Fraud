#!/bin/bash
# Startup script for Render deployment

echo "Starting UPI Fraud Detection API..."

# Change to server directory
cd server

# Run the FastAPI application
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

