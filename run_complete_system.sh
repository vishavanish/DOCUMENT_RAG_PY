#!/bin/bash

echo "🚀 Starting Complete News + RAG System..."

# Kill existing processes
echo "Killing existing processes..."
lsof -ti:5001,8501 | xargs kill -9 2>/dev/null || true

# Install streamlit if not present
pip install streamlit pandas 2>/dev/null || true

# Start Flask API in background
echo "Starting Flask API on port 5001..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Start Streamlit interface
echo "Starting Streamlit interface on port 8501..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

echo "✅ System started successfully!"
echo "📱 Streamlit Interface: http://localhost:8501"
echo "🔧 Flask API: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $FLASK_PID $STREAMLIT_PID 2>/dev/null; exit" INT
wait