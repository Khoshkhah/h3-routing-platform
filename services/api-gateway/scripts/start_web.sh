#!/bin/bash
# Quick start script for the enhanced web visualization

echo "🚀 Starting Enhanced Routing Visualization"
echo "=========================================="
echo ""

# Check if API is running
if ! curl -s http://localhost:8000/datasets > /dev/null 2>&1; then
    echo "⚠️  API is not running!"
    echo "Please start the API first in another terminal:"
    echo "  cd /home/kaveh/projects/routing-pipeline"
    echo "  source /home/kaveh/miniconda3/envs/ch-query-engine/bin/activate"
    echo "  ./start_api.sh"
    echo ""
    exit 1
fi

echo "✅ API is running on port 8000"
echo ""

# Activate conda environment
echo "🔧 Activating conda environment..."
source /home/kaveh/miniconda3/envs/ch-query-engine/bin/activate

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit dependencies..."
    pip install -r app/requirements.txt
fi

echo "🌐 Starting Streamlit web app..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🗺️  Open in browser: http://localhost:8501"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start streamlit
streamlit run app/streamlit_app.py --server.port 8501 --server.address localhost
