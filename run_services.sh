#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Function to run services in background
run_service() {
    echo "Starting $1..."
    $2 &
    echo "$1 started with PID $!"
}

# Start Redis (if not running)
if ! pgrep redis-server > /dev/null; then
    run_service "Redis" "redis-server"
fi

# Start Celery worker
run_service "Celery Worker" "celery -A tasks worker --loglevel=info"

# Start Celery beat scheduler
run_service "Celery Beat" "celery -A tasks beat --loglevel=info"

# Start Flask app
echo "Starting Flask application..."
python app.py