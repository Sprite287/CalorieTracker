import os
import subprocess
import sys
import time

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

def graceful_terminate(pid):
    """Try to gracefully terminate a process by PID."""
    try:
        print(f"Attempting graceful termination of PID {pid}...")
        # Try gentle termination, suppressing error output
        subprocess.call(f"taskkill /PID {pid} /T", shell=True, stdout=subprocess.DEVNULL)
        for _ in range(10):
            result = subprocess.run(
                f'tasklist /FI "PID eq {pid}"', shell=True, capture_output=True, text=True
            )
            if str(pid) not in result.stdout:
                print(f"Process {pid} terminated gracefully.")
                return True
            time.sleep(1)
        print(f"Process {pid} did not terminate gracefully, forcing kill...")
        subprocess.call(f"taskkill /PID {pid} /F", shell=True, stdout=subprocess.DEVNULL)
        return False
    except Exception as e:
        print(f"Error terminating PID {pid}: {e}")
        return False

def main():
    print("Restarting Calorie Tracker server (Waitress WSGI)...")
    pids = find_pids_on_port(APP_PORT)
    if pids:
        for pid in pids:
            graceful_terminate(pid)
    else:
        print(f"No process found on port {APP_PORT}.")

    time.sleep(1)
    print(f"Starting: {' '.join(START_COMMAND)}")
    subprocess.Popen(START_COMMAND, creationflags=DETACHED_PROCESS, close_fds=True)
    print("Server restarted in background.")

if __name__ == "__main__":
    main()