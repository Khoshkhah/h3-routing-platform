#!/bin/bash
# Build the routing engine and server
set -e

cd "$(dirname "$0")/.."

# Activate conda environment if not already
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_DEFAULT_ENV" != "routing-engine" ]]; then
    echo "Activating conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate routing-engine
fi

echo "Building routing engine..."
echo "Using compiler: $(which c++ 2>/dev/null || echo 'default')"
mkdir -p cpp/build
cd cpp/build

# Clean if switching generators or CMakeCache exists with wrong generator
if [ -f CMakeCache.txt ]; then
    if command -v ninja &> /dev/null; then
        if ! grep -q "CMAKE_GENERATOR:INTERNAL=Ninja" CMakeCache.txt 2>/dev/null; then
            echo "Cleaning build for Ninja..."
            rm -rf *
        fi
    else
        if grep -q "CMAKE_GENERATOR:INTERNAL=Ninja" CMakeCache.txt 2>/dev/null; then
            echo "Cleaning build for Make..."
            rm -rf *
        fi
    fi
fi

# Use ninja if available, otherwise use make
if command -v ninja &> /dev/null; then
    cmake -G Ninja -DCMAKE_PREFIX_PATH="$HOME/miniconda3/envs/h3-routing" ..
    ninja
else
    cmake -G "Unix Makefiles" -DCMAKE_PREFIX_PATH="$HOME/miniconda3/envs/h3-routing" ..
    make -j$(nproc)
fi

echo ""
echo "Build complete!"
echo "  CLI:    ./cpp/build/routing_engine"
echo "  Server: ./cpp/build/routing_server"
echo "  Tests:  ./cpp/build/test_routing"
