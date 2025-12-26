echo "Stopping H3 Routing Platform..."

function kill_process() {
    NAME=$1
    PATTERN=$2
    if pgrep -f "$PATTERN" > /dev/null; then
        echo "Stopping $NAME..."
        pkill -f "$PATTERN"
        # Wait up to 5 seconds
        for i in {1..5}; do
            if ! pgrep -f "$PATTERN" > /dev/null; then
                echo "  -> Stopped."
                return
            fi
            sleep 1
        done
        # Force kill if still running
        echo "  -> Force killing..."
        pkill -9 -f "$PATTERN"
    else
        echo "$NAME not running."
    fi
}

kill_process "Streamlit" "streamlit run"
kill_process "API Gateway" "uvicorn api.server:app"
kill_process "C++ Engine" "routing_server"

echo "All services stopped."
