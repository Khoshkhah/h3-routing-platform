#!/bin/bash
# Start the Streamlit web application

set -e

cd "$(dirname "$0")"

echo "Starting Streamlit web application..."
echo ""

# Activate virtual environment
source ../venv/bin/activate

# Change to app directory
cd ../app

# Run streamlit (forcing localhost)
streamlit run streamlit_app.py --server.address localhost
