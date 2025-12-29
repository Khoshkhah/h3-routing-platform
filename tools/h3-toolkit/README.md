# H3-Toolkit

**High-performance H3 cell boundary tracing and polygon operations with C++ acceleration.**

H3-Toolkit extends Uber's H3 library with efficient algorithms for computing cell boundaries across resolution hierarchies and generating buffered polygons that guarantee containment of all child cells.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

## Documentation

Visit the **[Full Documentation](https://khoshkhah.github.io/h3-toolkit/)** to explore:
- **Interactive Demo**: Visualize boundary tracing and buffering
- **Concepts**: Learn about H3 hierarchy and memory layout
- **API Reference**: Detailed documentation of all functions

You can also run the demo locally using the provided Jupyter Notebook:
```bash
jupyter notebook notebook/demo_generation.ipynb
```

## Installation

### Prerequisites

- Python 3.10+
- CMake 3.14+
- C++17 compiler
- Boost (install via `conda install -c conda-forge boost-cpp`)

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/h3-toolkit.git
cd h3-toolkit

# Create conda environment (recommended)
conda create -n h3-toolkit python=3.11
conda activate h3-toolkit
conda install -c conda-forge boost-cpp

# Build and install
pip install -e .
```

### Verify Installation

```python
import h3_toolkit
print(h3_toolkit.get_backend())  # Should print 'cpp'
print(h3_toolkit.cpp_geom_available())  # Should print True
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

# Simple cell buffer - ~0.1ms
simple_poly = h3t.get_buffered_h3_polygon_cpp(cell, buffer_meters=100)
```

### Choosing Python vs C++

All functions have both Python and C++ versions:

```python
# Pure Python (uses Shapely)
from h3_toolkit import get_buffered_boundary_polygon
result_py = get_buffered_boundary_polygon(cell, 10)

# C++ accelerated (uses Boost.Geometry)
from h3_toolkit import get_buffered_boundary_polygon_cpp
result_cpp = get_buffered_boundary_polygon_cpp(cell, 10)

# Both return identical GeoJSON format
```

## Performance Benchmarks

Tested on resolution 6 cell with intermediate resolution 10:

| Function | Python | C++ | Speedup |
|----------|--------|-----|---------|
| `children_on_boundary_faces` | 2.5ms | 0.23ms | **11x** |
| `cell_boundary_from_children` | 150ms | 13ms | **11x** |
| `get_buffered_boundary_polygon` (accurate) | 170ms | 18ms | **9x** |
| `get_buffered_boundary_polygon` (fast) | N/A | 0.6ms | - |
| `get_buffered_h3_polygon` | 0.5ms | 0.14ms | **3x** |

## API Reference

### Core Functions

#### `children_on_boundary_faces(parent, target_res, input_faces={1,2,3,4,5,6})`

Returns all children at `target_res` that lie on the parent's boundary faces.

```python
children = h3t.children_on_boundary_faces('86283082fffffff', 10)
# Returns: ['8a28308280c7fff', '8a28308280cffff', ...]
```

#### `get_buffered_boundary_polygon_cpp(cell, intermediate_res=10, buffer_meters=None, use_convex_hull=False)`

Returns a buffered polygon guaranteed to contain all res-15 children.

**Parameters:**
- `cell`: H3 cell index (string)
- `intermediate_res`: Resolution for boundary computation (default: 10)
- `buffer_meters`: Buffer distance. If None, auto-calculates as 100% of edge length
- `use_convex_hull`: True for fast convex hull, False for accurate union

**Returns:** GeoJSON Feature with buffered polygon

```python
result = h3t.get_buffered_boundary_polygon_cpp(
    '86283082fffffff',
    intermediate_res=10,
    use_convex_hull=False
)
print(result['properties']['buffer_meters'])  # 75.86
print(result['properties']['method'])  # 'buffered_boundary_cpp'
```

### Utility Functions

#### `trace_cell_to_ancestor_faces(h, input_faces, res_parent)`

Traces which parent faces a given cell lies on.

#### `cell_to_coarsest_ancestor_on_faces(h, input_faces={1,2,3,4,5,6})`

Finds the coarsest ancestor where the cell still lies on boundary faces.

#### `get_backend()`

Returns current backend: `'cpp'` or `'python'`

#### `cpp_geom_available()`

Returns `True` if C++ geometry functions (Boost.Geometry) are available.

## Project Structure

```
h3-toolkit/
├── CMakeLists.txt           # CMake build configuration
├── README.md                # This file
├── pyproject.toml           # Python package configuration
├── src/
│   ├── cpp/
│   │   ├── include/
│   │   │   └── h3_toolkit.hpp    # C++ header
│   │   └── src/
│   │       └── h3_toolkit.cpp    # C++ implementation
│   ├── bindings/
│   │   └── python_bindings.cpp   # pybind11 bindings
│   └── python/
│       └── h3_toolkit/
│           ├── __init__.py       # Package exports
│           ├── geom.py           # Python geometry functions
│           └── utils.py          # Python utility functions
├── tests/
│   └── test_h3_toolkit.py   # Test suite
└── docs/
    └── api_reference.md     # Detailed API documentation
```

## How It Works

### Boundary Face Tracing

H3 cells have 6 faces (edges). When a cell is subdivided, child cells inherit different face relationships based on:
- **Resolution parity** (even/odd)
- **Child position** (0-6, where 0 is center)

The library uses precomputed lookup tables to efficiently trace these relationships.

### Buffered Polygons

Two modes are available:

1. **Convex Hull (fast)**: Computes convex hull of all boundary vertices, then buffers
2. **Union (accurate)**: Unions all boundary cell polygons, then buffers

The buffer distance is auto-calculated as 100% of the intermediate resolution edge length to guarantee all res-15 children are contained.

## Development

### Building from Source

```bash
# Configure with CMake
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..

# Build
make -j4

# Copy to Python package
cp _h3_toolkit_cpp*.so ../src/python/h3_toolkit/
```

### Running Tests

```bash
pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [Uber H3](https://h3geo.org/) - The H3 hexagonal hierarchical spatial index
- [Boost.Geometry](https://www.boost.org/doc/libs/release/libs/geometry/) - Polygon operations
- [pybind11](https://github.com/pybind/pybind11) - Python bindings for C++
