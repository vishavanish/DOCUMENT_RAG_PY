#!/bin/bash

echo "🚀 Starting News Collection + RAG System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install Flask mysql-connector-python celery redis requests python-dotenv PyPDF2 scikit-learn numpy openai==0.28.1 -q

# Create uploads directory
mkdir -p uploads

# Start Flask app
echo "Starting Flask application on http://localhost:5001"
python app.py
