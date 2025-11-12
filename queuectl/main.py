import click

import json
import multiprocessing
from . import job, db, config as cfg, worker as worker_module, worker_manager

@click.group()
def cli():
    """A CLI-based background job queue system."""
    db.init_db()

@cli.command()
@click.argument('command')
@click.option('--max-retries', type=int, help='Maximum number of retries.')
def enqueue(command, max_retries):
    """Add a new job to the queue."""
    job_id = job.enqueue_job(command, max_retries)
    click.echo(f"Enqueued job {job_id}")

@cli.group()
def worker():
    """Manage workers."""
    pass

@worker.command()
@click.option('--count', default=1, help='Number of workers to start.')
def start(count):
    """Start one or more workers."""
    worker_manager.start_workers(count)
    click.echo(f"Started {count} worker(s)")

@worker.command()
def stop():
    """Stop running workers gracefully."""
    worker_manager.stop_workers()
    click.echo("Stopping workers")

@cli.command()
def status():
    """Show summary of all job states & active workers."""
    conn = db.get_db()
    rows = conn.execute("SELECT state, COUNT(*) as count FROM jobs GROUP BY state").fetchall()
    conn.close()
    for row in rows:
        click.echo(f"{row['state']}: {row['count']}")

@cli.command(name="list")
@click.option('--state', help='Filter jobs by state.')
def list_jobs(state):
    """List jobs by state."""
    conn = db.get_db()
    query = "SELECT * FROM jobs"
    params = []
    if state:
        query += " WHERE state = ?"
        params.append(state)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    for row in rows:
        click.echo(dict(row))

@cli.group()
def dlq():
    """Manage the Dead Letter Queue."""
    pass

@dlq.command(name="list")
def dlq_list():
    """View DLQ jobs."""
    conn = db.get_db()
    rows = conn.execute("SELECT * FROM jobs WHERE is_dlq = TRUE").fetchall()
    conn.close()
    for row in rows:
        click.echo(dict(row))

@dlq.command()
@click.argument('job_id')
def retry(job_id):
    """Retry a DLQ job."""
    conn = db.get_db()
    conn.execute("UPDATE jobs SET state = 'pending', is_dlq = FALSE, attempts = 0 WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    click.echo(f"Retrying DLQ job: {job_id}")

@cli.group()
def config():
    """Manage configuration."""
    pass

@config.command(name="set")
@click.argument('key')
@click.argument('value')
def set_config(key, value):
    """Manage configuration (retry, backoff, etc.)."""
    cfg.set_config(key, value)
    click.echo(f"Setting config: {key} = {value}")

if __name__ == '__main__':
    cli()
