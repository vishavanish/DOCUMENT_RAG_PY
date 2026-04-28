#!/bin/bash

echo "Setting up News Collection Project..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database (requires MySQL root access)
echo "Setting up MySQL database..."
mysql -u root -p < setup_database.sql

echo "Setup complete!"
echo "To run the project:"
echo "1. Start Redis: redis-server"
echo "2. Start Celery worker: celery -A tasks worker --loglevel=info"
echo "3. Start Celery beat: celery -A tasks beat --loglevel=info"
echo "4. Start Flask app: python app.py"