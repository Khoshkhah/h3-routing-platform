# H3 Routing Platform

**A high-performance, H3 Spatial Hierarchy routing engine for city-scale navigation.**

Feature-rich routing engine capable of finding optimal paths in milliseconds using a specialized C++ backend and H3 spatial pruning.

[Architecture Overview](docs/architecture_overview.md) | [Interactive Diagrams](https://khoshkhah.github.io/h3-routing-platform/diagrams/)

## Project Structure

This monorepo contains the entire routing stack:

*   **`services/`**: Long-running applications.
    *   **[`engine-cpp`](services/engine-cpp/)**: Core C++ Routing Engine with CSR graph and CH support (Port 8082).
    *   **[`api-gateway`](services/api-gateway/)**: Python FastAPI wrapper + Streamlit UI (Port 8000).
*   **`tools/`**: Offline data processing.
    *   **[`duckOSM`](tools/duckOSM/)**: High-performance OSM to DuckDB road network converter.
    *   **[`shortcut-generator`](tools/shortcut-generator/)**: H3-partitioned contraction hierarchy shortcut generator.
    *   **[`h3-toolkit`](tools/h3-toolkit/)**: H3 spatial utilities library (C++/Python).
*   **`sdk/`**: Client libraries.
    *   **[`python`](sdk/python/)**: `pip install h3-routing-client`
*   **`architecture/`**: [Interactive Diagrams](https://khoshkhah.github.io/h3-routing-platform/diagrams/) (LikeC4).
*   **`docs/`**: [Documentation](docs/).



## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Khoshkhah/h3-routing-platform.git
cd h3-routing-platform
git submodule update --init --recursive
```

### 2. Installation
Create the unified Conda environment:
```bash
conda env create -f environment.yml
conda activate h3-routing
```

Install the H3 C library (required for C++ compilation):
```bash
bash services/engine-cpp/scripts/install_h3.sh
```

Install the DuckDB C++ headers (required for DuckDB support in the engine):
```bash
bash scripts/install_duckdb_headers.sh
```

Install the Asio networking library (required by the Crow HTTP server):
```bash
conda install -c conda-forge asio
```

### 3. Build the Engine
Compile the C++ backend:
```bash
make build
```
> **Note**: You must re-run `make build` whenever you modify C++ source code in `services/engine-cpp/cpp/`.

### 4. Prepare Data
The routing engine requires road network data in DuckDB format. Data files are not included in the repository and must be generated from OpenStreetMap source files.

Somerset, Kentucky is a small city and a good dataset for testing.

**Step 1 — Download the city boundary:**
```bash
cd tools/duckOSM
python scripts/download_boundary.py \
  --place "Somerset, Kentucky, USA" \
  --output data/boundaries/somerset.geojson
```

**Step 2 — Download the OSM extract** for the region from [Geofabrik](https://download.geofabrik.de/):
```bash
mkdir -p tools/duckOSM/data/maps
wget "https://download.geofabrik.de/north-america/us/kentucky-latest.osm.pbf" \
     -O tools/duckOSM/data/maps/kentucky.osm.pbf
```

**Step 3 — Filter the OSM extract to the city boundary:**
```bash
cd tools/duckOSM
python scripts/filter_pbf.py \
  --input data/maps/kentucky.osm.pbf \
  --boundary data/boundaries/somerset.geojson \
  --output data/maps/somerset.osm.pbf
```

**Step 4 — Import OSM data into DuckDB:**
```bash
cd tools/duckOSM
python main.py --config config/somerset.yaml
```

**Step 5 — Generate contraction hierarchy shortcuts:**
```bash
cd tools/shortcut-generator
python main.py --config config/somerset_duckdb.yaml
```

The generated `data/somerset.duckdb` file will be picked up automatically by the API gateway.

### 5. Run the Platform
Start the C++ Engine and Python API Gateway:
```bash
# Terminal 1: Core Engine
make run-engine

# Terminal 2: API Gateway
make run-api

# Terminal 3: Streamlit UI
make run-streamlit
```

Visit the UI at **http://localhost:8501**.

## Documentation
*   [Architecture Overview](docs/architecture_overview.md)
*   [API Reference](docs/api_reference.md)
*   [SDK Manual](docs/sdk_manual.md)
*   [C++ Engine Deep Dive](docs/cpp_engine_deep_dive.md)
*   [Future Roadmap](docs/roadmap.md)

## License

This project is licensed under the [MIT License](LICENSE).
