import subprocess
import time

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

def graceful_terminate(pid):
    """Try to gracefully terminate a process by PID."""
    try:
        print(f"Attempting graceful termination of PID {pid}...")
        subprocess.call(f"taskkill /PID {pid} /T", shell=True)
        for _ in range(10):
            result = subprocess.run(f'tasklist /FI "PID eq {pid}"', shell=True, capture_output=True, text=True)
            if str(pid) not in result.stdout:
                print(f"Process {pid} terminated gracefully.")
                return True
            time.sleep(1)
        print(f"Process {pid} did not terminate gracefully, forcing kill...")
        subprocess.call(f"taskkill /PID {pid} /F", shell=True)
        return False
    except Exception as e:
        print(f"Error terminating PID {pid}: {e}")
        return False

def main():
    pids = find_pids_on_port(APP_PORT)
    if not pids:
        print(f"No server running on port {APP_PORT}.")
        return
    for pid in pids:
        graceful_terminate(pid)
    print("Server stopped.")

if __name__ == "__main__":
    main()