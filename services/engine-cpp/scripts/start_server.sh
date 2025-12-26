#!/bin/bash
# Start the routing server
set -e

cd "$(dirname "$0")/.."

# Activate conda environment if not already
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_DEFAULT_ENV" != "h3-routing" ]]; then
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate h3-routing
fi

# Default values
PORT=${PORT:-8082}
SHORTCUTS=""
EDGES=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --shortcuts) SHORTCUTS="$2"; shift 2 ;;
        --edges) EDGES="$2"; shift 2 ;;
        --somerset)
            SHORTCUTS="/home/kaveh/projects/h3-routing-platform/tools/shortcut-generator/output/Somerset_shortcuts"
            EDGES="/home/kaveh/projects/h3-routing-platform/tools/shortcut-generator/output/Somerset_edges_old_format.csv"
            shift ;;
        --burnaby)
            SHORTCUTS="/home/kaveh/projects/h3-routing-platform/tools/shortcut-generator/output/Burnaby_shortcuts"
            EDGES="/home/kaveh/projects/h3-routing-platform/tools/osm-importer/data/output/Burnaby/Burnaby_driving_simplified_edges_with_h3.csv"
            shift ;;
        --help)
            echo "Usage: $0 [options]"
            echo "  --port PORT        Server port (default: 8082)"
            echo "  --shortcuts PATH   Shortcuts Parquet directory"
            echo "  --edges PATH       Edges CSV file"
            echo "  --somerset         Load Somerset dataset"
            echo "  --burnaby          Load Burnaby dataset"
            echo ""
            echo "If no dataset specified, server starts empty. Use /load_dataset API to load data."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "Starting routing server on port $PORT..."

if [ -n "$SHORTCUTS" ] && [ -n "$EDGES" ]; then
    echo "  Shortcuts: $SHORTCUTS"
    echo "  Edges: $EDGES"
    # Execute from cpp/build where the binary exists
    exec ./cpp/build/routing_server --shortcuts "$SHORTCUTS" --edges "$EDGES" --port "$PORT"
else
    echo "  No dataset specified. Use /load_dataset API to load data."
    exec ./cpp/build/routing_server --port "$PORT"
fi
