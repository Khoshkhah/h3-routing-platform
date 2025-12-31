from typing import Dict, List, Tuple, Optional, Set, Any
import duckdb
import h3
from dataclasses import dataclass

@dataclass
class Shortcut:
    from_edge: int
    to_edge: int
    cost: float
    via_edge: int
    cell: int
    inside: int
    lca_res: int

class ShortestPathData:
    def __init__(self):
        self.fwd_adj: Dict[int, List[Shortcut]] = {}
        self.bwd_adj: Dict[int, List[Shortcut]] = {}
        self.via_lookup: Dict[Tuple[int, int], int] = {}
        self.edge_meta: Dict[int, Dict[str, Any]] = {}

def load_shortcut_data(con: duckdb.DuckDBPyConnection) -> ShortestPathData:
    data = ShortestPathData()
    
    # Load shortcuts
    # C++ query: SELECT from_edge, to_edge, cost, via_edge, cell, inside FROM shortcuts
    shortcuts = con.execute("SELECT from_edge, to_edge, cost, via_edge, cell, inside FROM shortcuts").fetchall()
    for row in shortcuts:
        cell_val = row[4]
        try:
            # H3 cell resolution calculation
            lca_res = h3.get_resolution(h3.int_to_str(cell_val)) if cell_val and cell_val != 0 else -1
        except:
            lca_res = -1
            
        sc = Shortcut(
            from_edge=row[0],
            to_edge=row[1],
            cost=row[2],
            via_edge=row[3],
            cell=cell_val,
            inside=row[5],
            lca_res=lca_res
        )
        
        # Forward adjacency
        if sc.from_edge not in data.fwd_adj:
            data.fwd_adj[sc.from_edge] = []
        data.fwd_adj[sc.from_edge].append(sc)
        
        # Backward adjacency
        if sc.to_edge not in data.bwd_adj:
            data.bwd_adj[sc.to_edge] = []
        data.bwd_adj[sc.to_edge].append(sc)
        
        # Via lookup
        if sc.via_edge != 0:
            data.via_lookup[(sc.from_edge, sc.to_edge)] = sc.via_edge
            
    # Load edge meta
    # C++ query: SELECT id, from_cell, to_cell, lca_res, length, cost, geometry FROM edges
    edges = con.execute("SELECT id, to_cell, from_cell, lca_res, cost FROM edges").fetchall()
    for row in edges:
        data.edge_meta[row[0]] = {
            "to_cell": row[1],
            "from_cell": row[2],
            "lca_res": row[3],
            "cost": row[4]
        }
        
    return data

def expand_path(shortcut_path: List[int], via_lookup: Dict[Tuple[int, int], int]) -> List[int]:
    """Expand a shortcut path to base edges using the via_lookup table."""
    if not shortcut_path:
        return []
    
    expanded = []
    
    def expand_edge_pair(u: int, v: int, visited: Set[Tuple[int, int]]):
        if (u, v) in visited:
            return [u, v]
        visited.add((u, v))
        
        via = via_lookup.get((u, v), 0)
        
        # If no via edge, or via edge points to one of the endpoints, it's a base edge
        if via == 0 or via == u or via == v:
            return [u, v]
        
        # Recursively expand
        left = expand_edge_pair(u, via, visited)
        right = expand_edge_pair(via, v, visited)
        
        # Combine
        return left[:-1] + right

    for i in range(len(shortcut_path) - 1):
        u, v = shortcut_path[i], shortcut_path[i+1]
        pair_expanded = expand_edge_pair(u, v, set())
        if i == 0:
            expanded.extend(pair_expanded)
        else:
            expanded.extend(pair_expanded[1:])
            
    return expanded
