# H3 Routing Platform

**A high-performance, H3-indexed Contraction Hierarchy routing engine for city-scale navigation.**

Feature-rich routing engine capable of finding optimal paths in milliseconds using a specialized C++ backend and H3 spatial pruning.

[Architecture Overview](docs/architecture_overview.md)

## Project Structure

This monorepo contains the entire routing stack:

*   **`services/`**: Long-running applications.
    *   **[`engine-cpp`](services/engine-cpp/)**: The core C++ Routing Engine (Port 8082).
    *   **[`api-gateway`](services/api-gateway/)**: Python FastAPI wrapper + Streamlit UI (Port 8000).
*   **`tools/`**: Offline data processing.
    *   **[`osm-importer`](tools/osm-importer/)**: Converts raw `.osm.pbf` files into graph CSVs.
    *   **[`shortcut-generator`](tools/shortcut-generator/)**: Runs CH algorithm (DuckDB) to produce shortcuts.
*   **`sdk/`**: Client libraries.
    *   **[`python`](sdk/python/)**: `pip install h3-routing-client`
    *   **[`cpp`](sdk/cpp/)**: Header-only C++ client.
*   **`docs/`**: [Documentation](docs/).

## Getting Started

### 1. Installation
Create the unified Conda environment:
```bash
conda env create -f environment.yml
conda activate h3-routing
```

### 2. Build the Engine
Compile the C++ backend:
```bash
make build
```
> **Note**: You must re-run `make build` whenever you modify C++ source code in `services/engine-cpp/cpp/`.


### 3. Run the Platform
Start the C++ Engine and Python API Gateway:
```bash
# Terminal 1: Core Engine
make run-engine

# Terminal 2: API & UI
make run-api
```

Visit the UI at **http://localhost:8501**.

## Documentation
*   [Architecture Overview](docs/architecture_overview.md)
*   [API Reference](docs/api_reference.md)
*   [SDK Manual](docs/sdk_manual.md)
*   [C++ Engine Deep Dive](docs/cpp_engine_deep_dive.md)
*   [Future Roadmap](docs/roadmap.md)
