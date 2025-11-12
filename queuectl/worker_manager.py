import subprocess
import sys
import os
import signal
from pathlib import Path

PID_DIR = Path.home() / ".queuectl"
PID_FILE = PID_DIR / "workers.pid"

def start_workers(count):
    """Starts a number of worker processes in the background."""
    PID_DIR.mkdir(exist_ok=True)
    
    if PID_FILE.exists():
        print("Workers are already running. Stop them first with 'queuectl worker stop'.")
        return

    pids = []
    for _ in range(count):
        # Start worker as a true background subprocess
        if sys.platform == 'win32':
            # On Windows, use pythonw.exe (windowless Python) to prevent console windows
            python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
            # If pythonw doesn't exist, fall back to using CREATE_NO_WINDOW
            if not os.path.exists(python_exe):
                python_exe = sys.executable
            
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            
            proc = subprocess.Popen(
                [python_exe, "-m", "queuectl.worker_process"],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
        else:
            # Unix-like systems
            proc = subprocess.Popen(
                [sys.executable, "-m", "queuectl.worker_process"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
        pids.append(proc.pid)

    # Write the PIDs to a file so we can stop them later
    with open(PID_FILE, "w") as f:
        f.write("\n".join(map(str, pids)))
    
    print(f"Started {count} worker(s) in the background with PIDs: {', '.join(map(str, pids))}")

def stop_workers():
    """Stops all running worker processes."""
    if not PID_FILE.exists():
        print("No workers are running.")
        return

    with open(PID_FILE, "r") as f:
        pids = [int(pid) for pid in f.read().strip().split("\n") if pid]

    stopped_count = 0
    for pid in pids:
        try:
            if sys.platform == 'win32':
                # On Windows, use taskkill or os.kill with different approach
                import subprocess as sp
                sp.run(['taskkill', '/F', '/PID', str(pid)], 
                       stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                stopped_count += 1
            else:
                # On Unix-like systems, use SIGTERM
                os.kill(pid, signal.SIGTERM)
                stopped_count += 1
        except ProcessLookupError:
            print(f"Worker with PID {pid} not found. It may have already stopped.")
        except Exception as e:
            print(f"Error stopping worker {pid}: {e}")

    # Clean up the PID file
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass
    
    print(f"Stopped {stopped_count} worker(s).")