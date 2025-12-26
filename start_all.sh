#!/bin/bash
set -e

# Cleanup function to kill background processes on exit
trap "kill 0" EXIT

echo "Stopping any existing services..."
pkill -f "routing_server" || true
pkill -f "uvicorn api.server:app" || true
pkill -f "streamlit run" || true
sleep 1

# Activate conda environment
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_DEFAULT_ENV" != "h3-routing" ]]; then
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate h3-routing
fi

echo "==================================================="
echo "   H3 ROUTING PLATFORM - STARTING ALL SERVICES"
echo "==================================================="

# 1. Start C++ Engine (Background)
echo "[1/3] Starting C++ Routing Engine (Port 8082)..."
cd services/engine-cpp
./scripts/start_server.sh > ../../logs/engine.log 2>&1 &
ENGINE_PID=$!
cd ../..
echo "      -> Engine running (PID $ENGINE_PID). Logs: logs/engine.log"

# Wait a moment for engine to initialize
sleep 2

# 2. Start API Gateway (Background)
echo "[2/3] Starting Python API Gateway (Port 8000)..."
cd services/api-gateway
# using nohup or just backgrounding, but we need to ensure it uses the right python
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 > ../../logs/api.log 2>&1 &
API_PID=$!
cd ../..
echo "      -> API running (PID $API_PID). Logs: logs/api.log"

# 3. Start Streamlit UI (Background)
echo "[3/3] Starting Streamlit UI..."
echo "      -> Opening http://localhost:8501"
cd services/api-gateway
streamlit run app/streamlit_app.py > ../../logs/streamlit.log 2>&1 &
UI_PID=$!
cd ../..

echo "All services are running."
echo "Press Ctrl+C to stop."

# Wait for all background processes
wait
