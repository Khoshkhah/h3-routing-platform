# H3 Routing Platform

**A high-performance, H3 Spatial Hierarchy routing engine for city-scale navigation.**

Feature-rich routing engine capable of finding optimal paths in milliseconds using a specialized C++ backend and H3 spatial pruning.

**Documentation:** https://khoshkhah.github.io/h3-routing-platform/

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
```

### 2. Setup
Run the one-time setup (initializes submodules, creates the conda environment, installs all dependencies, and builds the C++ engine):
```bash
make setup
conda activate h3-routing
```

> **Note**: Re-run `make build` whenever you modify C++ source files in `services/engine-cpp/cpp/`.

### 3. Prepare Data
Routing data is not included in the repository and must be generated from OpenStreetMap source files. Somerset, Kentucky is a small city included as a sample:

```bash
make data CITY=somerset
```

This will automatically download the city boundary, regional OSM extract, filter it, import into DuckDB, and generate contraction hierarchy shortcuts. The generated `data/somerset.duckdb` will be picked up automatically by the API gateway.

To add support for a new city, add an entry to `tools/duckOSM/config/sources.yaml` and provide the corresponding duckOSM and shortcut-generator config files.

### 4. Run the Platform
```bash
bash start_all.sh
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
