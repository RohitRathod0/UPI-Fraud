"""
Simple test script to check if app can start
"""
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

print("Testing imports...")

try:
    print("1. Testing FastAPI...")
    from fastapi import FastAPI
    print("   [OK] FastAPI OK")
except Exception as e:
    print(f"   [ERROR] FastAPI Error: {e}")
    sys.exit(1)

try:
    print("2. Testing database...")
    from database import SessionLocal, Base, engine
    print("   [OK] Database OK")
except Exception as e:
    print(f"   [ERROR] Database Error: {e}")
    sys.exit(1)

try:
    print("3. Testing schemas...")
    from schemas import TransactionRequest
    print("   [OK] Schemas OK")
except Exception as e:
    print(f"   [ERROR] Schemas Error: {e}")
    sys.exit(1)

try:
    print("4. Testing config...")
    from config import Config
    print("   [OK] Config OK")
except Exception as e:
    print(f"   [ERROR] Config Error: {e}")
    sys.exit(1)

print("\n5. Testing agents (this may take a moment)...")
try:
    from agents.phish_agent import PhishingAgent
    print("   [OK] PhishingAgent OK")
except Exception as e:
    print(f"   [WARN] PhishingAgent Error: {e} (may still work)")

try:
    from agents.qr_guard_agent import QuishingAgent
    print("   [OK] QuishingAgent OK")
except Exception as e:
    print(f"   [WARN] QuishingAgent Error: {e} (may still work)")

print("\n[SUCCESS] All basic imports successful!")
print("\nYou can now try running the app with:")
print("  cd server")
print("  python -m uvicorn app:app --host 0.0.0.0 --port 8000")

