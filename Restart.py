import os
import subprocess
import sys
import time
import socket

START_COMMAND = [
    sys.executable, "-m", "waitress", "--host=0.0.0.0", "--port=5000", "CalorieApp:app"
]
APP_PORT = 5000
DETACHED_PROCESS = 0x00000008

def find_pids_on_port(port):
    """Return a list of PIDs using the given port (Windows only)."""
    try:
        result = subprocess.check_output(
            f'netstat -ano | findstr :{port}', shell=True, stderr=subprocess.DEVNULL
        ).decode()
        pids = set()
        for line in result.strip().split('\n'):
            if line:
                pid = line.strip().split()[-1]
                if pid.isdigit():
                    pids.add(int(pid))
        return list(pids)
    except Exception:
        return []

def is_port_responding(port, timeout=2):
    """Check if the port is responding to connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def get_local_ip():
    """Get the local IP address for network access."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

def graceful_terminate(pid):
    """Try to gracefully terminate a process by PID."""
    try:
        print(f"🛑 Stopping PID {pid}...")
        # Try gentle termination
        subprocess.run(f"taskkill /PID {pid} /T", shell=True, capture_output=True)
        
        # Wait for graceful shutdown
        for i in range(5):
            result = subprocess.run(
                f'tasklist /FI "PID eq {pid}"', shell=True, capture_output=True, text=True
            )
            if str(pid) not in result.stdout:
                print(f"✅ Process {pid} stopped")
                return True
            time.sleep(1)
            
        # Force kill if necessary
        subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True)
        print(f"✅ Process {pid} force stopped")
        return True
    except Exception as e:
        print(f"❌ Error stopping PID {pid}: {e}")
        return False

def main():
    print("🔄 Restarting CalorieTracker (Windows)")
    print()
    
    # Step 1: Stop existing server
    print("🛑 Stopping existing server...")
    pids = find_pids_on_port(APP_PORT)
    if pids:
        print(f"📋 Found {len(pids)} process(es) to stop: {pids}")
        for pid in pids:
            graceful_terminate(pid)
        print("✅ Existing server stopped")
    else:
        print("📂 No existing server found")
    
    # Step 2: Wait a moment
    print()
    print("⏳ Waiting before restart...")
    time.sleep(2)
    
    # Step 3: Start new server
    print("🚀 Starting new server...")
    
    # Set environment variables
    os.environ['DATABASE_URL'] = 'sqlite:///calorie_tracker_local.db'
    os.environ['FLASK_APP'] = 'CalorieApp.py'
    os.environ['FLASK_ENV'] = 'development'
    
    local_ip = get_local_ip()
    
    try:
        print(f"📦 Command: {' '.join(START_COMMAND)}")
        process = subprocess.Popen(START_COMMAND, creationflags=DETACHED_PROCESS, close_fds=True)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(8):
            time.sleep(1)
            if is_port_responding(APP_PORT):
                break
            print("   .", end="", flush=True)
        print()
        
        # Verify restart
        if is_port_responding(APP_PORT):
            print("🎉 Server restarted successfully!")
            print()
            print("🌐 Access URLs:")
            print(f"   • Local:   http://localhost:{APP_PORT}")
            print(f"   • Mobile:  http://{local_ip}:{APP_PORT}")
            
            # Show new PID
            new_pids = find_pids_on_port(APP_PORT)
            if new_pids:
                print(f"📋 New PID(s): {new_pids}")
        else:
            print("❌ Server restart failed")
            print("💡 Try running Start.py manually to see errors")
            
    except Exception as e:
        print(f"❌ Error during restart: {e}")

if __name__ == "__main__":
    main()