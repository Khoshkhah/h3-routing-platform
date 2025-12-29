# H3 Routing Platform Monorepo Makefile

.PHONY: help install build run-engine run-api clean

# Default target
help:
	@echo "H3 Routing Platform - Monorepo Commands"
	@echo "---------------------------------------"
	@echo "  make install      : Install dependencies for all services"
	@echo "  make build        : Build the C++ Routing Engine"
	@echo "  make run-engine   : Start the C++ Server (Port 8082)"
	@echo "  make run-api      : Start the Python API Gateway (Port 8000)"
	@echo "  make clean        : Clean build artifacts"

# --- Install Dependencies ---
install:
	@echo "Installing Python dependencies..."
	pip install -r services/api-gateway/requirements.txt
	pip install -r tools/osm-importer/requirements.txt
	pip install -r tools/shortcut-generator/requirements.txt
	@echo "Dependencies installed."

# --- Build C++ Engine ---
build:
	@echo "Building C++ Engine..."
	mkdir -p services/engine-cpp/cpp/build
	cd services/engine-cpp/cpp/build && cmake .. && cmake --build . -- -j4

# --- Run Services ---
run-engine:
	@echo "Starting Routing Engine..."
	cd services/engine-cpp && ./scripts/start_server.sh

run-api:
	@echo "Starting API Gateway..."
	cd services/api-gateway && ./scripts/start_api.sh

# --- Utilities ---
clean:
	rm -rf services/engine-cpp/build
	find . -type d -name "__pycache__" -exec rm -rf {} +
