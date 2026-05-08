#!/bin/bash
# Prepare routing data for a city.
# Usage: bash scripts/prepare_data.sh <city>
# Example: bash scripts/prepare_data.sh somerset
set -e

CITY="${1}"
if [ -z "$CITY" ]; then
    echo "Usage: bash scripts/prepare_data.sh <city>"
    echo "Available cities: see tools/duckOSM/config/sources.yaml"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

SOURCES_FILE="tools/duckOSM/config/sources.yaml"

# Parse sources.yaml with Python (already in env)
read -r PLACE PBF_URL PBF_REGION <<< $(python3 - <<EOF
import yaml, sys
with open("$SOURCES_FILE") as f:
    sources = yaml.safe_load(f)["sources"]
if "$CITY" not in sources:
    print(f"Error: '$CITY' not found in $SOURCES_FILE", file=sys.stderr)
    print(f"Available: {', '.join(sources.keys())}", file=sys.stderr)
    sys.exit(1)
s = sources["$CITY"]
print(s["place"], s["pbf_url"], s["pbf_region"])
EOF
)

BOUNDARY_FILE="tools/duckOSM/data/boundaries/${CITY}.geojson"
REGION_PBF="tools/duckOSM/data/maps/${PBF_REGION}.osm.pbf"
CITY_PBF="tools/duckOSM/data/maps/${CITY}.osm.pbf"

echo "==================================================="
echo "   Preparing data for: $CITY"
echo "==================================================="

# 1. Download boundary
if [ -f "$BOUNDARY_FILE" ]; then
    echo "[1/4] Boundary already exists, skipping..."
else
    echo "[1/4] Downloading boundary for '$PLACE'..."
    python3 tools/duckOSM/scripts/download_boundary.py \
        --place "$PLACE" \
        --output "$BOUNDARY_FILE"
fi

# 2. Download regional PBF
if [ -f "$REGION_PBF" ]; then
    echo "[2/4] Regional PBF already exists, skipping..."
else
    echo "[2/4] Downloading OSM extract for region '$PBF_REGION'..."
    mkdir -p tools/duckOSM/data/maps
    wget "$PBF_URL" -O "$REGION_PBF" --show-progress
fi

# 3. Filter PBF to city boundary
if [ -f "$CITY_PBF" ]; then
    echo "[3/4] Filtered PBF already exists, skipping..."
else
    echo "[3/4] Filtering OSM data to $CITY boundary..."
    python3 tools/duckOSM/scripts/filter_pbf.py \
        --input "$REGION_PBF" \
        --boundary "$BOUNDARY_FILE" \
        --output "$CITY_PBF"
fi

# 4. Import into DuckDB and generate shortcuts
echo "[4/4] Importing OSM data and generating shortcuts..."
cd tools/duckOSM
python3 main.py --config "config/${CITY}.yaml"
cd "$PROJECT_ROOT"

cd tools/shortcut-generator
python3 main.py --config "config/${CITY}_duckdb.yaml"
cd "$PROJECT_ROOT"

echo ""
echo "Data for '$CITY' is ready at data/${CITY}.duckdb"
