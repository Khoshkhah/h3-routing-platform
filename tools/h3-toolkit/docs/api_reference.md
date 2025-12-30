---
layout: default
title: API Reference
nav_order: 3
---

# H3-Toolkit API Reference

Complete API documentation for H3-Toolkit.

## Table of Contents

- [Core Functions](#core-functions)
- [Geometry Functions](#geometry-functions)
- [Utility Functions](#utility-functions)
- [C++ API](#c-api)

---

## Core Functions

These functions have both Python and C++ implementations. The C++ version is used automatically when available.

### `trace_cell_to_ancestor_faces`

```python
trace_cell_to_ancestor_faces(
    h: str,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6},
    res_parent: int = None
) -> Set[int]
```

Traces which boundary faces of an ancestor cell the given cell lies on.

**Parameters:**
- `h`: H3 cell index (string)
- `input_faces`: Set of face numbers {1-6} to trace
- `res_parent`: Resolution of ancestor. If None, uses immediate parent

**Returns:** Set of face numbers at the ancestor's boundary

**Example:**
```python
from h3_toolkit import trace_cell_to_ancestor_faces

cell = '8928308280fffff'  # Resolution 9
faces = trace_cell_to_ancestor_faces(cell, {1, 2, 3, 4, 5, 6}, res_parent=6)
print(faces)  # e.g., {2, 5}
```

---

### `trace_cell_to_parent_faces`

```python
trace_cell_to_parent_faces(
    h: str,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6}
) -> Set[int]
```

Convenience function that traces to the immediate parent (res - 1).

---

### `children_on_boundary_faces`

```python
children_on_boundary_faces(
    parent: str,
    target_res: int,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6}
) -> List[str]
```

Returns all children at `target_res` that lie on the parent's specified boundary faces.

**Parameters:**
- `parent`: Parent H3 cell index
- `target_res`: Resolution to descend to (must be > parent resolution)
- `input_faces`: Set of face numbers {1-6} to filter by

**Returns:** List of child H3 cell indices

**Example:**
```python
from h3_toolkit import children_on_boundary_faces

children = children_on_boundary_faces('86283082fffffff', 10)
print(f"Found {len(children)} boundary children")  # ~240 cells
```

**Performance:**
- Python: ~2.5ms
- C++: ~0.23ms (11x faster)

---

### `cell_to_coarsest_ancestor_on_faces`

```python
cell_to_coarsest_ancestor_on_faces(
    h: str,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6}
) -> str
```

Finds the coarsest ancestor (lowest resolution) where the cell still lies on at least one of the specified boundary faces.

**Returns:** H3 cell index of the coarsest ancestor

---

## Geometry Functions

### Pure Python Functions

These use Shapely for geometry operations.

#### `cell_boundary_to_geojson`

```python
cell_boundary_to_geojson(h: str) -> Dict[str, Any]
```

Returns a GeoJSON Feature representing the cell boundary.

#### `cell_boundary_from_children`

```python
cell_boundary_from_children(parent: str, target_res: int) -> Dict[str, Any]
```

Returns the merged boundary polygon of all boundary children at `target_res`.

**Returns:** GeoJSON Feature with properties:
- `h3_index`: Parent cell index
- `child_resolution`: Target resolution used
- `num_boundary_cells`: Number of boundary children

#### `get_buffered_h3_polygon`

```python
get_buffered_h3_polygon(cell: str, buffer_meters: float = None) -> Dict[str, Any]
```

Returns a buffered polygon of the cell's native boundary.

**Parameters:**
- `cell`: H3 cell index
- `buffer_meters`: Buffer distance. If None, auto-calculates as 100% of edge length

**Returns:** GeoJSON Feature with properties:
- `h3_index`: Cell index
- `buffer_meters`: Buffer distance used
- `method`: "buffered_python"

#### `get_buffered_boundary_polygon`

```python
get_buffered_boundary_polygon(
    cell: str,
    intermediate_res: int = 10,
    buffer_meters: float = None
) -> Dict[str, Any]
```

Hybrid approach: computes boundary at intermediate resolution, then buffers.

**Returns:** GeoJSON Feature with properties:
- `h3_index`: Cell index
- `intermediate_res`: Resolution used for boundary
- `buffer_meters`: Buffer distance used
- `num_boundary_cells`: Number of cells in boundary computation
- `method`: "buffered_boundary"

---

### C++ Accelerated Functions

These use Boost.Geometry and provide significant speedups. All return GeoJSON-compatible output.

#### `cell_boundary_to_geojson_cpp`

```python
cell_boundary_to_geojson_cpp(cell: str) -> Dict[str, Any]
```

C++ version of cell boundary to GeoJSON.

#### `cell_boundary_from_children_cpp`

```python
cell_boundary_from_children_cpp(parent: str, target_res: int) -> Dict[str, Any]
```

C++ version using Boost.Geometry union operations.

**Performance:** ~13ms (vs ~150ms Python, **11x faster**)

#### `get_buffered_h3_polygon_cpp`

```python
get_buffered_h3_polygon_cpp(cell: str, buffer_meters: float = None) -> Dict[str, Any]
```

C++ version of simple buffered polygon.

**Performance:** ~0.14ms (vs ~0.5ms Python, **3x faster**)

#### `get_buffered_boundary_polygon_cpp`

```python
get_buffered_boundary_polygon_cpp(
    cell: str,
    intermediate_res: int = 10,
    buffer_meters: float = None,
    use_convex_hull: bool = False
) -> Dict[str, Any]
```

C++ buffered polygon with configurable accuracy.

**Parameters:**
- `cell`: H3 cell index
- `intermediate_res`: Resolution for boundary computation (default: 10)
- `buffer_meters`: Buffer distance. If None, auto-calculates as 100% of edge length
- `use_convex_hull`: 
  - `True`: Fast convex hull approximation (~0.6ms)
  - `False`: Accurate union of all cells (~18ms)

**Returns:** GeoJSON Feature with properties:
- `h3_index`: Cell index
- `intermediate_res`: Resolution used
- `buffer_meters`: Buffer distance used
- `method`: "buffered_boundary_cpp" or "buffered_boundary_cpp_hull"

**Example:**
```python
from h3_toolkit import get_buffered_boundary_polygon_cpp

# Accurate mode (default)
result = get_buffered_boundary_polygon_cpp(
    '86283082fffffff',
    intermediate_res=10,
    use_convex_hull=False
)
print(result['properties']['method'])  # 'buffered_boundary_cpp'

# Fast mode
result = get_buffered_boundary_polygon_cpp(
    '86283082fffffff',
    intermediate_res=10,
    use_convex_hull=True
)
print(result['properties']['method'])  # 'buffered_boundary_cpp_hull'
```

---

## Utility Functions

### `get_backend`

```python
get_backend() -> str
```

Returns the current backend: `'cpp'` or `'python'`.

### `cpp_geom_available`

```python
cpp_geom_available() -> bool
```

Returns `True` if C++ geometry functions (Boost.Geometry) are available.

---

## C++ API

For direct C++ usage, include `h3_toolkit.hpp`:

```cpp
#include "h3_toolkit.hpp"

// Trace faces
std::set<int> faces = h3_toolkit::trace_cell_to_ancestor_faces(
    cell, input_faces, res_parent
);

// Get boundary children
std::vector<H3Index> children = h3_toolkit::children_on_boundary_faces(
    parent, target_res
);

// Get buffered polygon (returns vector of (lon, lat) pairs)
std::vector<std::pair<double, double>> polygon = 
    h3_toolkit::get_buffered_boundary_polygon(
        cell, 
        intermediate_res, 
        buffer_meters,
        use_convex_hull
    );
```

### Function Signatures

```cpp
namespace h3_toolkit {

std::set<int> trace_cell_to_ancestor_faces(
    H3Index h,
    const std::set<int>& input_faces,
    int res_parent
);

std::set<int> trace_cell_to_parent_faces(
    H3Index h,
    const std::set<int>& input_faces
);

std::vector<H3Index> children_on_boundary_faces(
    H3Index parent,
    int target_res,
    const std::set<int>& input_faces = {1,2,3,4,5,6}
);

H3Index cell_to_coarsest_ancestor_on_faces(
    H3Index h,
    const std::set<int>& input_faces = {1,2,3,4,5,6}
);

std::vector<std::pair<double, double>> cell_boundary(H3Index cell);

std::vector<std::pair<double, double>> cell_boundary_from_children(
    H3Index parent,
    int target_res
);

std::vector<std::pair<double, double>> get_buffered_h3_polygon(
    H3Index cell,
    double buffer_meters = -1.0
);

std::vector<std::pair<double, double>> get_buffered_boundary_polygon(
    H3Index cell,
    int intermediate_res = 10,
    double buffer_meters = -1.0,
    bool use_convex_hull = true
);

} // namespace h3_toolkit
```

---

## Performance Summary

| Function | Python | C++ | Speedup |
|----------|--------|-----|---------|
| `trace_cell_to_ancestor_faces` | 0.05ms | 0.005ms | 10x |
| `children_on_boundary_faces` | 2.5ms | 0.23ms | 11x |
| `cell_boundary_from_children` | 150ms | 13ms | 11x |
| `get_buffered_boundary_polygon` (accurate) | 170ms | 18ms | 9x |
| `get_buffered_boundary_polygon` (fast) | N/A | 0.6ms | - |
| `get_buffered_h3_polygon` | 0.5ms | 0.14ms | 3x |

*Benchmarks on resolution 6 cell with intermediate resolution 10*
