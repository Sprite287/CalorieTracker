import subprocess
import sys
import time
import socket
import os

# === CONFIGURATION ===
START_COMMAND = [
    sys.executable, "-m", "waitress", "--host=0.0.0.0", "--port=5000", "CalorieApp:app"
]
APP_PORT = 5000

DETACHED_PROCESS = 0x00000008

def find_pids_on_port(port):
    """Return a list of PIDs using the given port (Windows only)."""
    try:
        result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
        pids = set()
        for line in result.strip().split('\n'):
            if line:
                pid = line.strip().split()[-1]
                if pid.isdigit():
                    pids.add(int(pid))
        return list(pids)
    except Exception:
        return []

def get_local_ip():
    """Get the local IP address for network access."""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

def is_port_responding(port, timeout=3):
    """Check if the port is responding to connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    required_deps = ['flask', 'waitress', 'sqlalchemy']
    
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("📦 Install with: pip install flask waitress sqlalchemy psycopg2-binary python-dotenv")
        return False
    return True

def main():
    print("🚀 Starting CalorieTracker (Windows)")
    print()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check if server is already running
    pids = find_pids_on_port(APP_PORT)
    if pids:
        print(f"❌ Server already running on port {APP_PORT} (PID(s): {pids})")
        print("   Use Stop.py to stop it first")
        return

    # Set environment variables for local development
    os.environ['DATABASE_URL'] = 'sqlite:///calorie_tracker_local.db'
    os.environ['FLASK_APP'] = 'CalorieApp.py'
    os.environ['FLASK_ENV'] = 'development'
    
    local_ip = get_local_ip()
    
    print("📦 Starting server...")
    print(f"🔧 Using: {' '.join(START_COMMAND)}")
    print()
    
    try:
        # Start the server process
        process = subprocess.Popen(START_COMMAND, creationflags=DETACHED_PROCESS, close_fds=True)
        
        # Give server time to start
        print("⏳ Waiting for server to start...")
        for i in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            if is_port_responding(APP_PORT):
                break
            print("   .", end="", flush=True)
        print()
        
        # Check if server is responding
        if is_port_responding(APP_PORT):
            print("✅ Server started successfully!")
            print()
            print("🌐 Access URLs:")
            print(f"   • Local:          http://localhost:{APP_PORT}")
            print(f"   • Network:        http://{local_ip}:{APP_PORT}")
            print(f"   • Mobile/Device:  http://{local_ip}:{APP_PORT}")
            print()
            print("📱 Mobile Testing:")
            print("   1. Connect your mobile device to the same WiFi network")
            print(f"   2. Open browser and go to: http://{local_ip}:{APP_PORT}")
            print("   3. Enjoy testing your CalorieTracker app!")
            print()
            print("🛑 To stop the server, run: python Stop.py")
            
            # Get PID for reference
            new_pids = find_pids_on_port(APP_PORT)
            if new_pids:
                print(f"📋 Server PID(s): {new_pids}")
        else:
            print("❌ Server failed to start or is not responding")
            print("💡 Check for error messages above or try running manually:")
            print(f"   {' '.join(START_COMMAND)}")
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try running the command manually to see detailed errors:")
        print(f"   {' '.join(START_COMMAND)}")

if __name__ == "__main__":
    main()