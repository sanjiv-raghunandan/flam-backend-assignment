import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from . import db, config

LOG_DIR = Path.home() / ".queuectl" / "logs"

def run_job(job):
    """Executes a job, captures output, and updates its state."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOG_DIR / f"{job['id']}.log"
    
    conn = db.get_db()
    try:
        with open(log_file_path, "w") as log_file:
            # Redirect stdout and stderr to the log file
            subprocess.run(job['command'], shell=True, check=True, stdout=log_file, stderr=subprocess.STDOUT)
        
        # If we get here, the job was successful
        conn.execute('UPDATE jobs SET state = ?, updated_at = ? WHERE id = ?', 
                    ('completed', datetime.utcnow().isoformat(), job['id']))
        conn.commit()
    except subprocess.CalledProcessError:
        # The command returned a non-zero exit code, indicating failure
        handle_failed_job(job, conn)
    except Exception as e:
        # Handle other potential errors during job execution
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\nWorker execution error: {e}")
        handle_failed_job(job, conn)
    finally:
        conn.close()

def handle_failed_job(job, conn):
    """Handles a failed job with exponential backoff."""
    attempts = job['attempts'] + 1
    updated_at = datetime.utcnow().isoformat()
    
    if attempts >= job['max_retries']:
        conn.execute('UPDATE jobs SET state = ?, is_dlq = ?, updated_at = ? WHERE id = ?', 
                    ('dead', True, updated_at, job['id']))
    else:
        # Get configurable backoff base (default to 2)
        backoff_base = int(config.get_config('backoff-base', 2))
        delay = backoff_base ** attempts
        
        conn.execute('UPDATE jobs SET state = ?, attempts = ?, updated_at = ? WHERE id = ?', 
                    ('failed', attempts, updated_at, job['id']))
        conn.commit()
        time.sleep(delay)
        # Re-queue the job for another attempt
        conn.execute('UPDATE jobs SET state = ?, updated_at = ? WHERE id = ?', 
                    ('pending', datetime.utcnow().isoformat(), job['id']))
    conn.commit()

def start_worker():
    """Starts a worker process to poll for jobs."""
    while True:
        job = None
        conn = db.get_db()
        try:
            # Use a transaction to atomically select and update a job
            conn.execute("BEGIN")
            job_row = conn.execute(
                "SELECT id FROM jobs WHERE state = 'pending' AND is_dlq = FALSE ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            
            if job_row:
                job_id = job_row['id']
                # Lock the job and retrieve its full data
                conn.execute("UPDATE jobs SET state = 'processing', updated_at = ? WHERE id = ?", 
                           (datetime.utcnow().isoformat(), job_id))
                job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Worker DB error: {e}")
            time.sleep(1)
        finally:
            conn.close()

        if job:
            run_job(dict(job))
        else:
            # No job found, wait before polling again
            time.sleep(1) # Poll every second
