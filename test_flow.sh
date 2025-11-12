#!/bin/bash

# Clean up previous runs
rm -f ~/.queuectl.db

echo "--- Initializing DB ---"
queuectl status

echo "--- Enqueueing a successful job ---"
queuectl enqueue "echo 'Hello from job 1'"

echo "--- Enqueueing a failing job ---"
queuectl enqueue "exit 1"

echo "--- Listing pending jobs ---"
queuectl list --state pending

echo "--- Starting a worker in the background ---"
queuectl worker start &
WORKER_PID=$!

# Give the worker time to process jobs
sleep 10

echo "--- Checking job status ---"
queuectl status

echo "--- Listing DLQ ---"
queuectl dlq list

echo "--- Stopping worker ---"
kill $WORKER_PID
