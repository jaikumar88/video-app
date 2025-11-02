"""
Quick Health Check - Verify Backend is Running
"""
import requests
import sys

try:
    print("Checking backend health...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print(f"✅ Backend is running: {response.json()}")
        sys.exit(0)
    else:
        print(f"❌ Backend returned status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Backend is not running: {e}")
    print("Please start the backend first: python main.py")
    sys.exit(1)
