#!/bin/bash

# Integration script for routing-server-v2
# This script demonstrates how to use the new persistent server

set -e

echo "🚀 Routing Pipeline v2 - Integration Demo"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "routing-server-v2" ]; then
    echo "❌ Error: routing-server-v2 directory not found"
    echo "Please run this script from the routing-pipeline root directory"
    exit 1
fi

# Build the C++ server
echo "🔨 Building C++ routing server..."
cd routing-server-v2
./scripts/build.sh

# Start the server in background
echo "🚀 Starting persistent routing server..."
./scripts/run.sh &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test the health endpoint
echo "🏥 Testing server health..."
curl -s http://localhost:8080/health | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"

echo ""
echo "✅ Server is running successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Update your client code to use HTTP calls instead of subprocess"
echo "2. Load your datasets using POST /load_dataset"
echo "3. Query routes using POST /route"
echo ""
echo "🛑 To stop the server, run: kill $SERVER_PID"

# Keep server running for testing
wait $SERVER_PID