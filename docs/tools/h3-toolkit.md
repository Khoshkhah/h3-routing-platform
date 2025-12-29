---
layout: default
title: H3 Toolkit
parent: Tools
nav_order: 1
---

# H3-Toolkit

**High-performance H3 cell boundary tracing and polygon operations with C++ acceleration.**

H3-Toolkit extends Uber's H3 library with efficient algorithms for computing cell boundaries across resolution hierarchies and generating buffered polygons that guarantee containment of all child cells.

## Features

### Performance
- **C++ Core**: Critical algorithms implemented in C++ with Python bindings via pybind11
- **10-30x Speedup**: C++ functions significantly outperform pure Python equivalents
- **Boost.Geometry**: Professional-grade polygon operations (buffer, union, convex hull)

### Key Functions

| Function | Description | C++ |
|----------|-------------|-----|
| `trace_cell_to_ancestor_faces` | Track which parent faces a cell touches | ✅ |
| `children_on_boundary_faces` | Get boundary children at target resolution | ✅ |
| `cell_boundary_from_children` | Merge boundary children into single polygon | ✅ |
| `get_buffered_boundary_polygon` | Buffered polygon with configurable accuracy | ✅ |
| `get_buffered_h3_polygon` | Simple buffered cell polygon | ✅ |
| `cell_to_coarsest_ancestor_on_faces` | Find coarsest ancestor on boundary | ✅ |

## Installation

### Prerequisites

- Python 3.10+
- CMake 3.14+
- C++17 compiler
- Boost (for Boost.Geometry)

### From Source

```bash
# From tools directory
cd tools/h3-toolkit

# Build and install
pip install -e .
```

## Quick Start

### Basic Usage

```python
import h3_toolkit as h3t

# Get a cell
cell = '86283082fffffff'  # Resolution 6 cell in San Francisco

# Get boundary children at resolution 10
children = h3t.children_on_boundary_faces(cell, 10)
print(f"Boundary children: {len(children)}")  # ~240 cells

# Get merged boundary polygon (C++ accelerated)
boundary = h3t.cell_boundary_from_children_cpp(cell, 10)
print(f"Vertices: {len(boundary['geometry']['coordinates'][0])}")
```

### Buffered Polygons

```python
# Fast mode (convex hull) - ~0.6ms
fast_poly = h3t.get_buffered_boundary_polygon_cpp(
    cell, 
    intermediate_res=10,
    use_convex_hull=True
)

# Accurate mode (union) - ~18ms, matches exact boundary
accurate_poly = h3t.get_buffered_boundary_polygon_cpp(
    cell,
    intermediate_res=10, 
    use_convex_hull=False
)
```

## Performance Benchmarks

Tested on resolution 6 cell with intermediate resolution 10:

| Function | Python | C++ | Speedup |
|----------|--------|-----|---------|
| `children_on_boundary_faces` | 2.5ms | 0.23ms | **11x** |
| `cell_boundary_from_children` | 150ms | 13ms | **11x** |
| `get_buffered_boundary_polygon` (accurate) | 170ms | 18ms | **9x** |
| `get_buffered_h3_polygon` | 0.5ms | 0.14ms | **3x** |
