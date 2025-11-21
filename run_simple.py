"""
Simplified app runner with error handling
"""
import sys
import os

# Change to server directory
os.chdir(os.path.join(os.path.dirname(__file__), 'server'))
sys.path.insert(0, os.getcwd())

print("=" * 60)
print("Starting UPI Fraud Detection API...")
print("=" * 60)

try:
    import uvicorn
    print("✓ Uvicorn found")
except ImportError:
    print("✗ Uvicorn not found. Installing...")
    os.system("pip install uvicorn")
    import uvicorn

try:
    print("\nLoading application...")
    from app import app
    print("✓ Application loaded successfully!")
    
    print("\n" + "=" * 60)
    print("Server starting on http://localhost:8000")
    print("Press CTRL+C to stop")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("\nTrying to install missing dependencies...")
    os.system("pip install -r ../requirements.txt")
    print("\nPlease run this script again.")
    
except Exception as e:
    print(f"\n✗ Error starting app: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're in the project root directory")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Check if models exist in server/models/")
    input("\nPress Enter to exit...")


