"""
H3-Toolkit: High-performance H3 cell boundary tracing and polygon operations.

This package provides efficient algorithms for:
- Tracing H3 cell boundaries across resolution hierarchies
- Computing boundary children at arbitrary resolutions  
- Generating buffered polygons guaranteed to contain all res-15 children
- Polygon union and convex hull operations

Key Features:
- C++ acceleration via pybind11 (10-30x speedup)
- Boost.Geometry for professional-grade polygon operations
- GeoJSON-compatible output for easy visualization

Quick Start:
    >>> import h3_toolkit as h3t
    >>> cell = '86283082fffffff'
    >>> 
    >>> # Get boundary children at resolution 10
    >>> children = h3t.children_on_boundary_faces(cell, 10)
    >>> 
    >>> # Get buffered polygon (C++ accelerated)
    >>> result = h3t.get_buffered_boundary_polygon_cpp(cell, intermediate_res=10)
    >>> print(result['properties']['buffer_meters'])

Available Functions:
    Core (C++ accelerated):
        - trace_cell_to_ancestor_faces
        - trace_cell_to_parent_faces
        - children_on_boundary_faces
        - cell_to_coarsest_ancestor_on_faces
    
    Geometry (Python or C++):
        - cell_boundary_to_geojson / cell_boundary_to_geojson_cpp
        - cell_boundary_from_children / cell_boundary_from_children_cpp
        - get_buffered_h3_polygon / get_buffered_h3_polygon_cpp
        - get_buffered_boundary_polygon / get_buffered_boundary_polygon_cpp

    Utilities:
        - get_backend(): Returns 'cpp' or 'python'
        - cpp_geom_available(): True if Boost.Geometry is available

Author: H3-Toolkit Contributors
License: MIT
"""

# =============================================================================
# Backend Selection: C++ bindings if available, else pure Python
# =============================================================================
# Try to import C++ bindings first (faster), fall back to pure Python
try:
    from ._h3_toolkit_cpp import (
        trace_cell_to_ancestor_faces,
        trace_cell_to_parent_faces,
        children_on_boundary_faces,
        cell_to_coarsest_ancestor_on_faces
    )
    _BACKEND = "cpp"
except ImportError:
    from .utils import (
        trace_cell_to_ancestor_faces,
        trace_cell_to_parent_faces,
        children_on_boundary_faces,
        cell_to_coarsest_ancestor_on_faces
    )
    _BACKEND = "python"

# Pure Python geometry implementations (use Shapely)
from .geom import (
    cell_boundary_to_geojson,
    get_boundary_cells,
    cell_boundary_from_children,
    get_buffered_h3_polygon,          # Pure Python/Shapely
    get_buffered_boundary_polygon     # Pure Python/Shapely
)

# C++ geometry wrapper (returns GeoJSON like Python version)
_CPP_GEOM_AVAILABLE = False
try:
    from ._h3_toolkit_cpp import get_buffered_boundary_polygon as _cpp_buffered_polygon
    import h3
    import geojson as _geojson
    _CPP_GEOM_AVAILABLE = True
    
    def get_buffered_boundary_polygon_cpp(
        cell: str, 
        intermediate_res: int = 10, 
        buffer_meters: float = None,
        use_convex_hull: bool = False
    ):
        """
        C++ buffered polygon using Boost.Geometry.
        
        Returns GeoJSON Feature format (same as Python version).
        
        Args:
            cell: H3 cell index
            intermediate_res: Resolution for boundary computation (default 10)
            buffer_meters: Buffer in meters. If None, auto-calculates as 100% of edge length.
            use_convex_hull: True = fast convex hull, False = accurate merged boundary (default)
        
        Returns:
            GeoJSON Feature with buffered polygon
        """
        res = h3.get_resolution(cell)
        int_res = max(res + 1, min(intermediate_res, 15))
        
        # C++ uses -1.0 to mean auto-calculate
        cpp_buffer = buffer_meters if buffer_meters is not None else -1.0
        coords = _cpp_buffered_polygon(cell, int_res, cpp_buffer, use_convex_hull)
        
        # Wrap in GeoJSON format
        geojson_coords = [[c[0], c[1]] for c in coords]
        polygon = _geojson.Polygon([geojson_coords])
        
        # Calculate actual buffer for properties
        if buffer_meters is None:
            edge_km = h3.average_hexagon_edge_length(int_res, unit='km')
            actual_buffer = edge_km * 1000 * 1.0
        else:
            actual_buffer = buffer_meters
        
        method = "buffered_boundary_cpp_hull" if use_convex_hull else "buffered_boundary_cpp"
        
        return _geojson.Feature(
            geometry=polygon,
            properties={
                "h3_index": cell,
                "intermediate_res": int_res,
                "buffer_meters": actual_buffer,
                "method": method
            }
        )
    
    # Additional C++ wrappers
    from ._h3_toolkit_cpp import cell_boundary as _cpp_cell_boundary
    from ._h3_toolkit_cpp import cell_boundary_from_children as _cpp_cell_boundary_from_children
    from ._h3_toolkit_cpp import get_buffered_h3_polygon as _cpp_get_buffered_h3_polygon
    
    def cell_boundary_to_geojson_cpp(cell: str):
        """C++ version of cell_boundary_to_geojson. Returns GeoJSON Feature."""
        coords = _cpp_cell_boundary(cell)
        geojson_coords = [[c[0], c[1]] for c in coords]
        polygon = _geojson.Polygon([geojson_coords])
        return _geojson.Feature(geometry=polygon, properties={"h3_index": cell, "method": "cpp"})
    
    def cell_boundary_from_children_cpp(parent: str, target_res: int):
        """C++ version of cell_boundary_from_children. Returns GeoJSON Feature."""
        # Get boundary children count for the property
        boundary_children = children_on_boundary_faces(parent, target_res)
        num_cells = len(boundary_children)
        
        coords = _cpp_cell_boundary_from_children(parent, target_res)
        geojson_coords = [[c[0], c[1]] for c in coords]
        polygon = _geojson.Polygon([geojson_coords])
        return _geojson.Feature(
            geometry=polygon,
            properties={
                "h3_index": parent,
                "child_resolution": target_res,
                "num_boundary_cells": num_cells,
                "method": "cpp"
            }
        )
    
    def get_buffered_h3_polygon_cpp(cell: str, buffer_meters: float = None):
        """C++ version of get_buffered_h3_polygon. Returns GeoJSON Feature."""
        cpp_buffer = buffer_meters if buffer_meters is not None else -1.0
        coords = _cpp_get_buffered_h3_polygon(cell, cpp_buffer)
        geojson_coords = [[c[0], c[1]] for c in coords]
        polygon = _geojson.Polygon([geojson_coords])
        
        if buffer_meters is None:
            res = h3.get_resolution(cell)
            int_res = min(res + 4, 15)
            edge_km = h3.average_hexagon_edge_length(int_res, unit='km')
            actual_buffer = edge_km * 1000 * 1.0
        else:
            actual_buffer = buffer_meters
        
        return _geojson.Feature(
            geometry=polygon,
            properties={
                "h3_index": cell,
                "buffer_meters": actual_buffer,
                "method": "buffered_cpp"
            }
        )
        
except ImportError:
    pass

__version__ = "0.1.0"

def get_backend():
    """Returns the current backend: 'cpp' or 'python'"""
    return _BACKEND

def cpp_geom_available():
    """Returns True if C++ geometry functions (Boost.Geometry) are available"""
    return _CPP_GEOM_AVAILABLE
