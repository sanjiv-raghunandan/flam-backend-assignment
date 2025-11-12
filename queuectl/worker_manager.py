import multiprocessing
import time
from . import worker

processes = []

def start_workers(count):
    """Starts a number of worker processes."""
    for _ in range(count):
        proc = multiprocessing.Process(target=worker.start_worker)
        processes.append(proc)
        proc.start()

def stop_workers():
    """Stops all running worker processes."""
    for proc in processes:
        proc.terminate()
    for proc in processes:
        proc.join()
    processes.clear()