#!/bin/bash
set -e

# Activate conda environment
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_DEFAULT_ENV" != "h3-routing" ]]; then
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate h3-routing
fi

echo "==================================================="
echo "   H3 ROUTING PLATFORM - CSR ENGINE DAEMON"
echo "==================================================="

mkdir -p logs

echo "[1] Stopping existing services..."
pkill -f "routing_server" || true
pkill -f "uvicorn api.server:app" || true
pkill -f "streamlit run" || true
sleep 1

# 1. Start C++ Engine (CSR Version)
echo "[2] Starting C++ Engine (CSR)..."
cd services/engine-cpp

# Force file paths for Metro Vancouver
SHORTCUTS="/home/kaveh/projects/h3-routing-platform/data/All_Vancouver_shortcuts"
EDGES="/home/kaveh/projects/h3-routing-platform/data/All_Vancouver_edges.csv"

# Launch CSR server (Start empty for fast boot)
nohup ./cpp/build/routing_server_csr \
    --port 8082 \
    --index rtree \
    > ../../logs/engine.log 2>&1 &
    
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
echo "SUCCESS! All services run in background (CSR Mode)."
echo ""
echo "UI:  http://localhost:8501"
echo "API: http://localhost:8000/docs"
echo ""
echo "To stop everything, run: ./stop_all_csr.sh"
echo "You can now close this terminal."
echo "==================================================="
