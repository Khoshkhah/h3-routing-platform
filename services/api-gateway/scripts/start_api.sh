#!/bin/bash
# Start the API server

set -e

cd "$(dirname "$0")/.."

# Activate conda environment if not already
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_DEFAULT_ENV" != "h3-routing" ]]; then
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate h3-routing
fi

echo "Starting Contraction Hierarchies API server..."
echo "API will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
echo ""

python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
