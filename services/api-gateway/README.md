# API Gateway & Streamlit UI

The user-facing layer of the H3 Routing Platform, providing a REST API and an interactive map interface.

## 🚀 Overview

This service acts as the gateway to the high-performance C++ routing engine.

- **FastAPI Backend**: Handles HTTP requests, dataset management, and proxies routing queries to the C++ engine.
- **Streamlit Frontend**: A polished, interactive map UI for visualization and testing.

## 🛠 Features

- **Dynamic Dataset Loading**: Load/unload datasets (DuckDB) on demand.
- **Interactive Map**: Folium-based visualization with click-to-route.
- **Real-time Metrics**: View routing latency, distance, and cost.
- **Debug Visualization**: Inspect H3 cells (Source, Target, High-level) for algorithm verification.
- **Variable-based Config**: Clean `dataset.yaml` configuration using project-relative paths.

## 📦 Setup

Dependencies are managed via the unified project environment.

```bash
conda activate h3-routing
```

## 🏃 Usage

**Recommended**: Use the daemon script from the project root:
```bash
./start_daemon.sh
```

**Manual Start**:
```bash
# 1. Start API (Port 8000)
cd api
python server.py

# 2. Start UI (Port 8501)
cd app
streamlit run streamlit_app.py
```

## ⚙️ Configuration

Datasets are defined in `config/datasets.yaml`.

Example:
```yaml
paths:
  data_root: "{project_root}/data"
  boundary_root: "{project_root}/tools/osm-importer/data/boundaries"

datasets:
  - name: "metro_vancouver"
    db_path: "{data_root}/All_Vancouver.db"
    boundary_path: "{boundary_root}/metro_vancouver_regional_district.geojson"
    # ...
```

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/datasets` | GET | List available datasets |
| `/load-dataset` | POST | Load a dataset into the C++ engine |
| `/unload-dataset` | POST | Unload a dataset |
| `/route` | GET | Compute shortest path |
| `/nearest-edge` | GET | Find nearest edge to lat/lon |

## 🖥️ UI Guide

1. **Select Dataset**: Choose a region from the sidebar.
2. **Status Check**: The UI automatically checks if the dataset is loaded in the engine.
3. **Route**: Drag markers A and B on the map.
4. **Inspect**: View the calculated path and performance metrics.
