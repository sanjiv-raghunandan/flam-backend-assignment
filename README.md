# queuectl

`queuectl` is a CLI-based background job queue system built with Python. It manages background jobs with worker processes, handles retries using exponential backoff, and maintains a Dead Letter Queue (DLQ) for permanently failed jobs.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sanjiv-raghunandan/flam-backend-assignment.git
    cd flam-backend-assignment
    ```

2.  **Install the package:**
    ```bash
    pip install -e .
    ```

## Usage Examples

### Enqueue a Job
```bash
queuectl enqueue "sleep 5 && echo 'Job Done'"
```

### Start and Stop Workers
```bash
# Start 3 workers in the background
queuectl worker start --count 3

# Stop all running workers
queuectl worker stop
```

### List Jobs
```bash
queuectl list --state <state_name>
```

### Check Status
```bash
queuectl status
```

### Manage DLQ
```bash
# List jobs in the DLQ
queuectl dlq list

# Retry a job from the DLQ
queuectl dlq retry <job_id>
```

### Configuration
```bash
# Set max retries to 5
queuectl config set max-retries 5

# Set backoff base (default is 2)
queuectl config set backoff-base 3
```

### View Job Output
```bash
# First, find the ID of a completed job
queuectl list --state completed

# Then, view the log file (replace <job_id> with the actual ID)
cat ~/.queuectl/logs/<job_id>.log
```

## Architecture Overview

### Job Lifecycle
-   **pending**: A job is created and waiting to be processed.
-   **processing**: A worker has picked up the job.
-   **completed**: The job has been executed successfully.
-   **failed**: The job failed, and will be retried.
-   **dead**: The job has failed all retries and is in the DLQ.

### Data Persistence
Job data is stored in a SQLite database located at `~/.queuectl.db`. This ensures that jobs persist across restarts.

### Worker Logic
Workers poll the database for pending jobs. When a job is found, it's locked (moved to `processing` state) using an atomic transaction to prevent race conditions. If the job fails, it's retried with exponential backoff (configurable via `backoff-base`). After exhausting all retries, it's moved to the DLQ.

### Job Logging
The output (`stdout` and `stderr`) of each job is logged to a file in the `~/.queuectl/logs/` directory. Each job has its own log file, named after the job's ID (e.g., `<job_id>.log`). This allows you to inspect the output of completed or failed jobs.

### Retry & Backoff Configuration
- **max-retries**: Configurable via `queuectl config set max-retries <value>` (default: 3)
- **backoff-base**: Configurable via `queuectl config set backoff-base <value>` (default: 2)
- Retry delay formula: `delay = backoff_base ^ attempts` seconds

## Assumptions & Trade-offs
-   **Process Management**: The current implementation uses `multiprocessing` for worker management. A more robust solution for a production environment might involve a more sophisticated process manager like `systemd` or a container orchestration platform.
-   **Job Locking**: The system uses a simple "state" field in the database for locking. This is generally safe for multiple processes on the same machine but could be a point of failure in a distributed environment.

## Testing Instructions
A basic test script is provided in `tests/test_main.py`. To run the tests:
```bash
python -m unittest discover tests
```

A manual test script `test_flow.sh` is also provided to demonstrate the core functionality.
```bash
bash test_flow.sh
```
