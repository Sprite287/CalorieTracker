import subprocess
import sys
import time

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

def main():
    # Check if server is already running
    pids = find_pids_on_port(APP_PORT)
    if pids:
        print(f"Server already running on port {APP_PORT} (PID(s): {pids}). Stop it first.")
        return

    print("Starting Calorie Tracker server in background...")
    subprocess.Popen(START_COMMAND, creationflags=DETACHED_PROCESS, close_fds=True)
    time.sleep(1)
    print("Server started.")

if __name__ == "__main__":
    main()