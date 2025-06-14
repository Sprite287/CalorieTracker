import subprocess
import time
import socket

APP_PORT = 5000

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

def is_port_responding(port, timeout=1):
    """Check if the port is still responding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def get_process_name(pid):
    """Get the process name for a given PID."""
    try:
        result = subprocess.run(f'tasklist /FI "PID eq {pid}" /FO CSV /NH', 
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            # Parse CSV output: "process_name","pid","session_name","session#","mem_usage"
            parts = result.stdout.strip().split(',')
            if len(parts) >= 1:
                return parts[0].strip('"')
    except:
        pass
    return "Unknown"

def graceful_terminate(pid):
    """Try to gracefully terminate a process by PID."""
    process_name = get_process_name(pid)
    
    try:
        print(f"🛑 Stopping server process: {process_name} (PID: {pid})")
        
        # First try graceful termination
        result = subprocess.run(f"taskkill /PID {pid} /T", shell=True, capture_output=True)
        
        # Wait and check if process terminated
        print("⏳ Waiting for graceful shutdown...")
        for i in range(10):
            time.sleep(1)
            check_result = subprocess.run(f'tasklist /FI "PID eq {pid}"', 
                                        shell=True, capture_output=True, text=True)
            if str(pid) not in check_result.stdout:
                print(f"✅ Process {pid} terminated gracefully")
                return True
            print("   .", end="", flush=True)
        print()
        
        # If still running, force kill
        print(f"⚠️  Process {pid} did not stop gracefully, forcing termination...")
        subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True)
        
        # Final check
        time.sleep(1)
        final_check = subprocess.run(f'tasklist /FI "PID eq {pid}"', 
                                   shell=True, capture_output=True, text=True)
        if str(pid) not in final_check.stdout:
            print(f"✅ Process {pid} force terminated")
            return True
        else:
            print(f"❌ Failed to terminate process {pid}")
            return False
            
    except Exception as e:
        print(f"❌ Error terminating PID {pid}: {e}")
        return False

def main():
    print("🛑 Stopping CalorieTracker (Windows)")
    print()
    
    # Check if anything is running on the port
    if is_port_responding(APP_PORT):
        print(f"🔍 Found server running on port {APP_PORT}")
    else:
        print(f"📋 No active server detected on port {APP_PORT}")
    
    # Get PIDs using the port
    pids = find_pids_on_port(APP_PORT)
    
    if not pids:
        print(f"✅ No processes found using port {APP_PORT}")
        print("   Server is already stopped")
        return
    
    print(f"📋 Found {len(pids)} process(es) to stop: {pids}")
    print()
    
    all_stopped = True
    for pid in pids:
        if not graceful_terminate(pid):
            all_stopped = False
        print()
    
    # Final verification
    print("🔍 Verifying server shutdown...")
    time.sleep(1)
    
    if not is_port_responding(APP_PORT):
        print("🏁 Server stopped successfully!")
        print(f"✅ Port {APP_PORT} is now free")
    else:
        print("⚠️  Server may still be running")
        print("💡 You can check manually with: netstat -ano | findstr :5000")
    
    remaining_pids = find_pids_on_port(APP_PORT)
    if remaining_pids:
        print(f"⚠️  Warning: Processes still using port {APP_PORT}: {remaining_pids}")

if __name__ == "__main__":
    main()