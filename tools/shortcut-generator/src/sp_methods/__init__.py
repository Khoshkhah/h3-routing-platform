"""
SP Methods Package
==================
Contains shortest path computation algorithms for the partitioned processor.

Available methods:
- PURE: Uses pure DuckDB SQL (iterative Bellman-Ford)
- SCIPY: Uses scipy.sparse.csgraph.dijkstra
"""

from sp_methods.pure import compute_shortest_paths_pure_duckdb
from sp_methods.scipy import process_partition_scipy

__all__ = ['compute_shortest_paths_pure_duckdb', 'process_partition_scipy']
