#!/bin/bash

echo "🚀 Starting News Collection + RAG System..."

# Kill existing processes
lsof -ti:5001,8501 | xargs kill -9 2>/dev/null || true

# Start Flask API
echo "Starting Flask API on port 5001..."
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "Flask PID: $FLASK_PID"

# Wait for Flask to start
sleep 3

# Start Streamlit
echo "Starting Streamlit on port 8501..."
streamlit run streamlit_app.py --server.port 8501 --server.address localhost &
STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

echo ""
echo "✅ System started successfully!"
echo "📱 Streamlit Interface: http://localhost:8501"
echo "🔧 Flask API: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $FLASK_PID $STREAMLIT_PID 2>/dev/null; exit" INT
wait
