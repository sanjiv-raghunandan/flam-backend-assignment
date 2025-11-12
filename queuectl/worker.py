import subprocess
import time
import json
from datetime import datetime
from . import db

def run_job(job):
    """Executes a job and updates its state."""
    conn = db.get_db()
    try:
        subprocess.run(job['command'], shell=True, check=True)
        conn.execute('UPDATE jobs SET state = ? WHERE id = ?', ('completed', job['id']))
        conn.commit()
    except subprocess.CalledProcessError:
        handle_failed_job(job, conn)
    finally:
        conn.close()

def handle_failed_job(job, conn):
    """Handles a failed job with exponential backoff."""
    attempts = job['attempts'] + 1
    if attempts >= job['max_retries']:
        conn.execute('UPDATE jobs SET state = ?, is_dlq = ? WHERE id = ?', ('dead', True, job['id']))
    else:
        delay = 2 ** attempts
        conn.execute('UPDATE jobs SET state = ?, attempts = ? WHERE id = ?', ('failed', attempts, job['id']))
        time.sleep(delay)
        # Re-queue the job for another attempt
        conn.execute('UPDATE jobs SET state = ? WHERE id = ?', ('pending', job['id']))
    conn.commit()

def start_worker():
    """Starts a worker process to poll for jobs."""
    while True:
        conn = db.get_db()
        job = conn.execute("SELECT * FROM jobs WHERE state = 'pending' AND is_dlq = FALSE ORDER BY created_at ASC LIMIT 1").fetchone()
        if job:
            conn.execute("UPDATE jobs SET state = 'processing' WHERE id = ?", (job['id'],))
            conn.commit()
            conn.close()
            run_job(dict(job))
        else:
            conn.close()
            time.sleep(1) # Poll every second
