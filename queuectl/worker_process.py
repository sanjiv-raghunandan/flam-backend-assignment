"""Standalone worker process entry point."""
if __name__ == "__main__":
    # Import here to avoid circular imports
    from queuectl.worker import start_worker
    start_worker()

