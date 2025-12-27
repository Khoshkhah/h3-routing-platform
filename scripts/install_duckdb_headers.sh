#!/bin/bash
# Install DuckDB C++ headers for engine build
# The conda libduckdb package only includes the shared library, not the headers.
# This script downloads and installs the headers from DuckDB releases.

set -e

DUCKDB_VERSION="${1:-1.2.2}"
DOWNLOAD_URL="https://github.com/duckdb/duckdb/releases/download/v${DUCKDB_VERSION}/libduckdb-linux-amd64.zip"

echo "Installing DuckDB ${DUCKDB_VERSION} headers..."

# Check conda environment
if [[ -z "$CONDA_PREFIX" ]]; then
    echo "Error: No conda environment active. Activate the h3-routing environment first."
    exit 1
fi

# Download and extract
TMP_DIR=$(mktemp -d)
echo "Downloading from ${DOWNLOAD_URL}..."
python3 -c "
import zipfile
import urllib.request
import os

url = '${DOWNLOAD_URL}'
urllib.request.urlretrieve(url, '${TMP_DIR}/duckdb.zip')

with zipfile.ZipFile('${TMP_DIR}/duckdb.zip', 'r') as z:
    z.extractall('${TMP_DIR}')
"

# Install headers
echo "Installing to ${CONDA_PREFIX}/include..."
cp "${TMP_DIR}/duckdb.hpp" "${CONDA_PREFIX}/include/"
cp "${TMP_DIR}/duckdb.h" "${CONDA_PREFIX}/include/"

# Cleanup
rm -rf "${TMP_DIR}"

echo "Done! DuckDB headers installed."
echo "Now rebuild the C++ engine:"
echo "  cd services/engine-cpp/cpp/build"
echo "  cmake .."
echo "  make -j4"
