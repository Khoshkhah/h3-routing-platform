#!/bin/bash
# Stop the Streamlit web application

echo "Stopping Streamlit web application..."

# Kill all streamlit processes
pkill -f "streamlit run app/streamlit_app.py" 2>/dev/null

# Wait a moment and check if it's stopped
sleep 1

if pgrep -f "streamlit run app/streamlit_app.py" > /dev/null; then
    echo "Force killing remaining processes..."
    pkill -9 -f "streamlit run app/streamlit_app.py" 2>/dev/null
fi

if pgrep -f "streamlit run app/streamlit_app.py" > /dev/null; then
    echo "❌ Failed to stop Streamlit"
    exit 1
else
    echo "✅ Streamlit stopped successfully"
fi
