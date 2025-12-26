#!/bin/bash
# Stop the routing server

echo "Stopping routing server..."
pkill -f "routing_server" 2>/dev/null && echo "Server stopped." || echo "No server running."
