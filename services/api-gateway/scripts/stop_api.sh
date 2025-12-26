#!/bin/bash
# Stop the API server

echo "Stopping API server..."

# Kill all uvicorn processes
pkill -f "uvicorn api.server:app" 2>/dev/null

# Wait a moment and check if it's stopped
sleep 1

if pgrep -f "uvicorn api.server:app" > /dev/null; then
    echo "Force killing remaining processes..."
    pkill -9 -f "uvicorn api.server:app" 2>/dev/null
fi

if pgrep -f "uvicorn api.server:app" > /dev/null; then
    echo "❌ Failed to stop API server"
    exit 1
else
    echo "✅ API server stopped successfully"
fi
