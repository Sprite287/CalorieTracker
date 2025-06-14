#!/usr/bin/env python3
import subprocess
import sys
import time
import os

def main():
    print("🔄 Restarting CalorieTracker (WSL)")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Stop the server
    print("🛑 Stopping server...")
    stop_result = subprocess.run([sys.executable, os.path.join(script_dir, "stop_wsl.py")])
    
    # Wait a moment
    time.sleep(2)
    
    # Start the server
    print("🚀 Starting server...")
    start_result = subprocess.run([sys.executable, os.path.join(script_dir, "start_wsl.py")])
    
    if start_result.returncode == 0:
        print("🎉 Server restarted successfully")
    else:
        print("❌ Failed to restart server")

if __name__ == "__main__":
    main()