"""
Startup script for Railway deployment
"""
import os
import sys

# Add server directory to Python path
server_dir = os.path.join(os.path.dirname(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

# Change to server directory for relative imports
os.chdir(server_dir)

# Get port from environment variable (Railway provides this)
port = int(os.environ.get('PORT', 8000))

if __name__ == "__main__":
    import uvicorn
    print(f"Starting UPI Fraud Detection API on port {port}...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}")
    
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

