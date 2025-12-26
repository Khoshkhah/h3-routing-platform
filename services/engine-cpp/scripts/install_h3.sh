#!/bin/bash
# Install H3 library from source into conda environment
set -e

if [ -z "$CONDA_PREFIX" ]; then
    echo "Error: Conda environment not activated. Run 'conda activate routing-engine' first."
    exit 1
fi

echo "Installing H3 into $CONDA_PREFIX ..."

# Clone H3 if not present
H3_SRC="${HOME}/src/h3"
if [ ! -d "$H3_SRC" ]; then
    mkdir -p "${HOME}/src"
    git clone https://github.com/uber/h3.git "$H3_SRC"
fi

# Build and install
cd "$H3_SRC"
git checkout v4.1.0  # Use stable release
cmake -S . -B build \
    -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_DOCS=OFF \
    -DBUILD_TESTING=OFF

cmake --build build -j$(nproc)
cmake --install build

echo "H3 installed successfully to $CONDA_PREFIX"
