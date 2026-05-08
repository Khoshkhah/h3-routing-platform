#!/bin/bash
# Full environment setup for h3-routing-platform.
# Run once after cloning: bash scripts/setup.sh
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==================================================="
echo "   H3 ROUTING PLATFORM - SETUP"
echo "==================================================="

# 1. Submodules
echo "[1/6] Initializing git submodules..."
git submodule update --init --recursive

# 2. Conda environment
echo "[2/6] Setting up conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh

if conda env list | grep -q "^h3-routing "; then
    echo "      -> Environment exists, updating..."
    conda env update -f environment.yml --prune
else
    echo "      -> Creating environment..."
    conda env create -f environment.yml
fi

conda activate h3-routing

# 3. H3 C library
echo "[3/6] Installing H3 C library..."
bash services/engine-cpp/scripts/install_h3.sh

# 4. DuckDB headers
echo "[4/6] Installing DuckDB C++ headers..."
bash scripts/install_duckdb_headers.sh

# 5. Asio
echo "[5/6] Installing Asio networking library..."
conda install -c conda-forge asio -y

# 6. Build C++ engine
echo "[6/6] Building C++ engine..."
make build

echo ""
echo "==================================================="
echo "   Setup complete!"
echo "   Activate the environment: conda activate h3-routing"
echo "   Prepare data:             make data CITY=somerset"
echo "   Run the platform:         bash start_all.sh"
echo "==================================================="
