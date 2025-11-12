import uuid
import json
from datetime import datetime
from . import db
from . import config

def enqueue_job(command, max_retries=None):
    """Adds a new job to the queue."""
    if max_retries is None:
        max_retries = int(config.get_config('max-retries', 3))
    
    job = {
        "id": str(uuid.uuid4()),
        "command": command,
        "state": "pending",
        "attempts": 0,
        "max_retries": max_retries,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    conn = db.get_db()
    conn.execute(
        'INSERT INTO jobs (id, command, state, attempts, max_retries, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (job['id'], job['command'], job['state'], job['attempts'], job['max_retries'], job['created_at'], job['updated_at'])
    )
    conn.commit()
    conn.close()
    return job['id']
