#!/bin/bash
set -e

# Activate conda environment
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_DEFAULT_ENV" != "h3-routing" ]]; then
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate h3-routing
fi

echo "==================================================="
echo "   H3 ROUTING PLATFORM - DAEMON MODE"
echo "==================================================="

mkdir -p logs

echo "[1] Stopping existing services..."
pkill -f "routing_server" || true
pkill -f "uvicorn api.server:app" || true
pkill -f "streamlit run" || true
sleep 1

# 1. Start C++ Engine
echo "[2] Starting C++ Engine..."
cd services/engine-cpp
nohup ./scripts/start_server.sh > ../../logs/engine.log 2>&1 &
echo "    -> Engine PID: $!"
cd ../..
sleep 2

# 2. Start API Gateway
echo "[3] Starting API Gateway..."
cd services/api-gateway
nohup python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 > ../../logs/api.log 2>&1 &
echo "    -> API PID: $!"
cd ../..

# 3. Start Streamlit UI
echo "[4] Starting Streamlit..."
cd services/api-gateway
nohup streamlit run app/streamlit_app.py > ../../logs/streamlit.log 2>&1 &
echo "    -> Streamlit PID: $!"
cd ../..

echo "==================================================="
echo "SUCCESS! All services run in background."
echo ""
echo "UI:  http://localhost:8501"
echo "API: http://localhost:8000/docs"
echo ""
echo "To stop everything, run: ./stop_all.sh"
echo "You can now close this terminal."
echo "==================================================="
