#!/bin/bash
echo "Stopping H3 Routing Platform..."

function kill_process() {
    NAME=$1
    PATTERN=$2
    if pgrep -f "$PATTERN" > /dev/null; then
        echo "Stopping $NAME..."
        pkill -f "$PATTERN" 2>/dev/null
        sleep 1
        # Force kill if still running
        if pgrep -f "$PATTERN" > /dev/null; then
            echo "  -> Force killing..."
            pkill -9 -f "$PATTERN" 2>/dev/null
            sleep 1
        fi
        if pgrep -f "$PATTERN" > /dev/null; then
            echo "  -> WARNING: Could not kill $NAME"
        else
            echo "  -> Stopped."
        fi
    else
        echo "$NAME not running."
    fi
}

# Also kill by port in case processes are orphaned
function kill_port() {
    PORT=$1
    PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Killing process on port $PORT (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
}

kill_process "Streamlit" "streamlit run"
kill_process "API Gateway" "uvicorn api.server:app"
kill_process "C++ Engine" "routing_server"

# Extra: Kill by ports to catch orphans
kill_port 8501
kill_port 8000
kill_port 8082

echo "All services stopped."
