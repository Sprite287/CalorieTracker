#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import signal
import socket

# Configuration
APP_PORT = 5000
PID_FILE = "/tmp/calorie_tracker_wsl.pid"

# Check if we have virtual environment and dependencies
def setup_environment():
    """Set up virtual environment, install dependencies, and configure environment."""
    venv_path = os.path.join(os.path.dirname(__file__), "venv")
    venv_python = os.path.join(venv_path, "bin", "python")
    venv_pip = os.path.join(venv_path, "bin", "pip")
    
    # Check if virtual environment exists
    if not os.path.exists(venv_python):
        print("📦 Virtual environment not found, creating one...")
        try:
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    
    # Check if dependencies are installed
    try:
        result = subprocess.run([venv_python, "-c", "import flask, sqlalchemy, psycopg2, dotenv"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("📥 Installing dependencies...")
            subprocess.run([venv_pip, "install", "flask", "sqlalchemy", "psycopg2-binary", "python-dotenv", "waitress"], check=True)
            print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    
    # Set environment variables
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///calorie_tracker_local.db'
    os.environ['FLASK_APP'] = 'CalorieApp.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Check which server to use
    try:
        subprocess.run([venv_python, "-c", "import waitress"], check=True, capture_output=True)
        return True, [venv_python, "-m", "waitress", "--host=0.0.0.0", f"--port={APP_PORT}", "CalorieApp:app"]
    except subprocess.CalledProcessError:
        print("⚠️  Waitress not found, using Flask dev server")
        return True, [venv_python, "-m", "flask", "run", "--host=0.0.0.0", f"--port={APP_PORT}"]

def is_port_in_use(port):
    """Check if port is in use using socket."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def find_pids_on_port(port):
    """Find PIDs using the given port (fallback method)."""
    try:
        # Try lsof first
        result = subprocess.check_output(['lsof', '-ti', f':{port}'], stderr=subprocess.DEVNULL).decode().strip()
        if result:
            return [int(pid) for pid in result.split('\n') if pid.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Fallback: check PID file
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Verify process exists
            os.kill(pid, 0)
            return [pid]
        except (OSError, ValueError):
            os.remove(PID_FILE)
    
    return []

def main():
    print("🚀 Starting CalorieTracker (WSL)")
    
    # Setup environment and get start command
    setup_result = setup_environment()
    if setup_result is False:
        return
    
    has_deps, start_command = setup_result
    if not has_deps:
        return
    
    # Check if server is already running
    if is_port_in_use(APP_PORT):
        pids = find_pids_on_port(APP_PORT)
        if pids:
            print(f"❌ Server already running on port {APP_PORT} (PID: {pids[0]})")
        else:
            print(f"❌ Port {APP_PORT} is in use by another process")
        print("   Use stop_wsl.py to stop it first")
        return

    print(f"📦 Starting server: {' '.join(start_command)}")
    
    try:
        # Start the process in background
        process = subprocess.Popen(
            start_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Save PID to file
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        # Give it time to start
        time.sleep(3)
        
        # Verify it started
        if process.poll() is None and is_port_in_use(APP_PORT):
            print(f"✅ Server started successfully (PID: {process.pid})")
            print(f"🌐 Local access: http://localhost:{APP_PORT}")
            
            # Get network IPs for external access
            try:
                # Get WSL IP
                hostname_result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                wsl_ip = hostname_result.stdout.strip().split()[0] if hostname_result.returncode == 0 else "unknown"
                
                # Try to get Windows ethernet IP
                try:
                    windows_ip_result = subprocess.run(['cmd.exe', '/c', 'ipconfig | findstr "192.168"'], capture_output=True, text=True)
                    if windows_ip_result.returncode == 0:
                        # Extract IP from ipconfig output
                        for line in windows_ip_result.stdout.split('\n'):
                            if 'IPv4 Address' in line and '192.168' in line:
                                windows_ip = line.split(':')[-1].strip()
                                break
                        else:
                            windows_ip = None
                    else:
                        windows_ip = None
                except:
                    windows_ip = None
                
                print(f"🖥️  Windows access: http://{wsl_ip}:{APP_PORT}")
                
                if windows_ip:
                    print(f"📱 Mobile access: http://{windows_ip}:{APP_PORT}")
                    print(f"   (Use this IP: {windows_ip} - your Windows ethernet IP)")
                else:
                    print(f"📱 Mobile access: Try http://192.168.86.25:{APP_PORT}")
                    print("   (Based on your ipconfig, try your Windows ethernet IP)")
                
                print()
                print("📋 Mobile Testing Instructions:")
                print("   1. Connect mobile device to same WiFi network")
                print("   2. Use the Windows ethernet IP (192.168.86.x), NOT the WSL IP")
                print("   3. Server binds to 0.0.0.0 so it listens on all network interfaces")
                
            except:
                print("⚠️  Could not determine network IPs")
                print("📱 For mobile access, use your Windows ethernet IP:")
                print(f"   Try: http://192.168.86.25:{APP_PORT}")
                print("   (From your ipconfig output)")
        else:
            print("❌ Failed to start server")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
    
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

if __name__ == "__main__":
    main()