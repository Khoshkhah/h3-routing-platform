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
DB_PATH=""
SHORTCUTS=""
EDGES=""

# Base data directory
DATA_DIR="/home/kaveh/projects/h3-routing-platform/data"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --db) DB_PATH="$2"; shift 2 ;;
        --shortcuts) SHORTCUTS="$2"; shift 2 ;;
        --edges) EDGES="$2"; shift 2 ;;
        --somerset)
            DB_PATH="${DATA_DIR}/Somerset.db"
            shift ;;
        --burnaby)
            DB_PATH="${DATA_DIR}/Burnaby.db"
            shift ;;
        --help)
            echo "Usage: $0 [options]"
            echo "  --port PORT        Server port (default: 8082)"
            echo "  --db PATH          DuckDB database file (preferred)"
            echo "  --shortcuts PATH   Shortcuts Parquet directory (legacy)"
            echo "  --edges PATH       Edges CSV file (legacy)"
            echo "  --somerset         Load Somerset dataset from DuckDB"
            echo "  --burnaby          Load Burnaby dataset from DuckDB"
            echo ""
            echo "If no dataset specified, server starts empty. Use /load_dataset API to load data."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "Starting routing server on port $PORT..."

if [ -n "$DB_PATH" ]; then
    # DuckDB loading (new way)
    echo "  DuckDB: $DB_PATH"
    exec ./cpp/build/routing_server --db "$DB_PATH" --port "$PORT"
elif [ -n "$SHORTCUTS" ] && [ -n "$EDGES" ]; then
    # Legacy file loading
    echo "  Shortcuts: $SHORTCUTS"
    echo "  Edges: $EDGES"
    exec ./cpp/build/routing_server --shortcuts "$SHORTCUTS" --edges "$EDGES" --port "$PORT"
else
    echo "  No dataset specified. Use /load_dataset API to load data."
    exec ./cpp/build/routing_server --port "$PORT"
fi
