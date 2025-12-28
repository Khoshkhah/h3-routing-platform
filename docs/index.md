---
layout: default
title: Home
nav_order: 1
has_children: true
---

# H3 Routing Platform

A high-performance **Contraction Hierarchy (CH)** routing engine designed for massive road networks.

The H3 Routing Platform provides a complete end-to-end solution for preparing, hosting, and querying large-scale routing data. It leverages **H3 Spatial Pruning** and **CSR (Compressed Sparse Row)** optimizations to achieve lightning-fast queries with a minimal memory footprint.

## Key Features

- **High Performance**: Sub-millisecond routing queries on metropolitan-scale networks.
- **Memory Optimized**: 78% memory reduction using custom CSR packing (Metro Vancouver 55M shortcuts in ~1.6 GB).
- **Modular Architecture**: 
  - **C++ Engine**: Contiguous memory graph and core routing logic.
  - **Python Processor**: Flexible offline data preparation using DuckDB.
  - **FastAPI Gateway**: Secure and extensible middleware.
- **H3 Integration**: Intelligent spatial pruning for reduced search space.
- **Ground-Truth Support**: Integrated Dijkstra algorithm for exact path verification.

## Getting Started

| Topic | Description | Link |
| :--- | :--- | :--- |
| **Architecture** | System design and component interactions | [Architecture Overview](./architecture_overview.md) |
| **Algorithms** | Deep dive into CH, Dijkstra, and Pruning | [Routing Algorithms](./algorithms.md) |
| **Data Workflow** | Preparing graph data from OSM | [Data Processing](./data_processing.md) |
| **API Reference** | HTTP Endpoints and JSON formats | [API Reference](./api_reference.md) |
| **SDK Manual** | Python and C++ Client Libraries | [SDK Manual](./sdk_manual.md) |

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/h3-routing-platform.git
cd h3-routing-platform

# Install dependencies (Python)
conda env create -f environment.yml
conda activate h3-routing

# Build C++ Engine
cd services/engine-cpp/cpp
mkdir build && cd build
cmake ..
make -j$(nproc)
```

---

*Developed for the Google DeepMind Advanced Agentic Coding project.*
