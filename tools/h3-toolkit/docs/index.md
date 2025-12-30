---
layout: default
title: Home
nav_order: 1
---

# H3-Toolkit Documentation

High-performance H3 cell boundary tracing and polygon operations with C++ acceleration.

## Quick Links

- [Interactive Demo](demo.md)
- [API Reference](api_reference.md)
- [Concepts](concepts.md)
- [GitHub Repository](https://github.com/Khoshkhah/h3-toolkit)

## Overview

H3-Toolkit extends Uber's H3 library with efficient algorithms for computing cell boundaries across resolution hierarchies and generating buffered polygons.

### Key Features

**High Performance**
- C++ core with Python bindings via pybind11
- 10-30x speedup over pure Python
- Boost.Geometry for polygon operations

**Comprehensive API**
- Boundary tracing across resolutions
- Buffered polygon generation
- GeoJSON-compatible output

## Installation

```bash
# Clone and install
git clone https://github.com/Khoshkhah/h3-toolkit.git
cd h3-toolkit

# Create environment
conda create -n h3-toolkit python=3.11
conda activate h3-toolkit
conda install -c conda-forge boost-cpp

# Install
pip install -e .
```

## Quick Start

```python
import h3_toolkit as h3t

cell = '86283082fffffff'  # Resolution 6 cell

# Get boundary children
children = h3t.children_on_boundary_faces(cell, 10)
print(f"Found {len(children)} boundary children")

# Get buffered polygon (C++ accelerated)
result = h3t.get_buffered_boundary_polygon_cpp(
    cell, 
    intermediate_res=10,
    use_convex_hull=False
)

# Returns GeoJSON Feature
print(result['properties']['buffer_meters'])
```

## Performance

| Function | Python | C++ | Speedup |
|----------|--------|-----|---------|
| `children_on_boundary_faces` | 2.5ms | 0.23ms | **11x** |
| `cell_boundary_from_children` | 150ms | 13ms | **11x** |
| `get_buffered_boundary_polygon` | 170ms | 18ms | **9x** |

## Documentation

- [API Reference](api_reference.md) - Complete function reference
- [Concepts](concepts.md) - How boundary tracing works

## License

MIT License - see [LICENSE](https://github.com/Khoshkhah/h3-toolkit/blob/master/LICENSE)
