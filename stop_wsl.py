#!/usr/bin/env python3
import subprocess
import time
import os
import signal

APP_PORT = 5000
PID_FILE = "/tmp/calorie_tracker_wsl.pid"

def find_pids_on_port(port):
    """Find PIDs using the given port (multiple fallback methods)."""
    pids = []
    
    # Method 1: Try lsof
    try:
        result = subprocess.check_output(['lsof', '-ti', f':{port}'], stderr=subprocess.DEVNULL).decode().strip()
        if result:
            pids.extend([int(pid) for pid in result.split('\n') if pid.strip()])
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Method 2: Check PID file
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Verify process exists
            os.kill(pid, 0)
            if pid not in pids:
                pids.append(pid)
        except (OSError, ValueError):
            # PID file is stale, remove it
            os.remove(PID_FILE)
    
    return pids

def graceful_terminate(pid):
    """Try to gracefully terminate a process by PID (Linux/WSL)."""
    try:
        print(f"🛑 Stopping server (PID: {pid})...")
        
        # Check if process exists
        os.kill(pid, 0)
        
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)
        
        # Wait up to 10 seconds for graceful shutdown
        for i in range(10):
            try:
                os.kill(pid, 0)  # Check if process still exists
                time.sleep(1)
            except OSError:
                print(f"✅ Process {pid} terminated gracefully")
                return True
        
        # If still running, force kill
        print(f"⚠️  Process {pid} did not stop gracefully, forcing termination...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)
        
        try:
            os.kill(pid, 0)
            print(f"❌ Failed to stop process {pid}")
            return False
        except OSError:
            print(f"✅ Process {pid} force terminated")
            return True
            
    except OSError as e:
        if e.errno == 3:  # No such process
            print(f"✅ Process {pid} was already stopped")
            return True
        else:
            print(f"❌ Error stopping PID {pid}: {e}")
            return False

def main():
    print("🛑 Stopping CalorieTracker (WSL)")
    
    pids = find_pids_on_port(APP_PORT)
    if not pids:
        print(f"✅ No server running on port {APP_PORT}")
        # Clean up PID file if it exists
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print("🧹 Cleaned up stale PID file")
        return
    
    print(f"📋 Found {len(pids)} process(es) to stop: {pids}")
    
    all_stopped = True
    for pid in pids:
        if not graceful_terminate(pid):
            all_stopped = False
    
    # Clean up PID file
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    
    if all_stopped:
        print("🏁 Server stopped successfully")
    else:
        print("⚠️  Some processes may still be running")

if __name__ == "__main__":
    main()