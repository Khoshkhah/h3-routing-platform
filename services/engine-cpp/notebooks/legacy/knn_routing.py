"""
KNN Routing Functions for Python Notebook
Updated to match C++ implementation
"""

from heapq import heappush, heappop
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import math


@dataclass
class QueryResult:
    distance: float
    path: list
    reachable: bool


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def query_multi(source_edges: List[int], target_edges: List[int],
                fwd_adj: dict, bwd_adj: dict, edge_meta: dict) -> QueryResult:
    """
    Many-to-many bidirectional Dijkstra for KNN routing.
    
    Sources start at 0.0 (like query_classic)
    Targets start at edge_cost (like query_classic)
    
    Args:
        source_edges: List of source edge IDs
        target_edges: List of target edge IDs
        fwd_adj: Forward adjacency dict (edge -> list of shortcuts)
        bwd_adj: Backward adjacency dict (edge -> list of shortcuts)
        edge_meta: Edge metadata dict (edge -> {cost, ...})
    
    Returns:
        QueryResult with best distance, path, and reachability
    """
    inf = float('inf')
    
    def get_edge_cost(edge_id: int) -> float:
        return edge_meta[edge_id]['cost']
    
    # Initialize forward from all sources at distance 0.0
    dist_fwd, parent_fwd, pq_fwd = {}, {}, []
    for src in source_edges:
        if src in edge_meta:
            dist_fwd[src] = 0.0
            parent_fwd[src] = src
            heappush(pq_fwd, (0.0, src))
    
    # Initialize backward from all targets at edge_cost
    dist_bwd, parent_bwd, pq_bwd = {}, {}, []
    for tgt in target_edges:
        if tgt in edge_meta:
            init_dist = get_edge_cost(tgt)
            dist_bwd[tgt] = init_dist
            parent_bwd[tgt] = tgt
            heappush(pq_bwd, (init_dist, tgt))
    
    # Create sets for quick lookup
    source_set = set(source_edges)
    target_set = set(target_edges)
    
    best, meeting = inf, None
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heappop(pq_fwd)
            if d > dist_fwd.get(u, inf) or d >= best:
                pass  # stale or pruned
            else:
                for sc in fwd_adj.get(u, []):
                    if sc.inside != 1:
                        continue
                    v = sc.to_edge
                    nd = d + sc.cost
                    if nd < dist_fwd.get(v, inf):
                        dist_fwd[v] = nd
                        parent_fwd[v] = u
                        heappush(pq_fwd, (nd, v))
                        
                        # Check for meeting point
                        if v in dist_bwd:
                            total = nd + dist_bwd[v]
                            if total < best:
                                best, meeting = total, v
        
        # Backward step
        if pq_bwd:
            d, u = heappop(pq_bwd)
            if d > dist_bwd.get(u, inf) or d >= best:
                pass  # stale or pruned
            else:
                for sc in bwd_adj.get(u, []):
                    if sc.inside not in (-1, 0):
                        continue
                    prev = sc.from_edge
                    nd = d + sc.cost
                    if nd < dist_bwd.get(prev, inf):
                        dist_bwd[prev] = nd
                        parent_bwd[prev] = u
                        heappush(pq_bwd, (nd, prev))
                        
                        # Check for meeting point
                        if prev in dist_fwd:
                            total = dist_fwd[prev] + nd
                            if total < best:
                                best, meeting = total, prev
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best:
                break
        elif not pq_fwd and not pq_bwd:
            break
    
    if meeting is None or best == inf:
        return QueryResult(-1, [], False)
    
    # Reconstruct path (matching C++ implementation)
    path = []
    curr = meeting
    
    # Forward path: meeting -> source
    # Trace back through parent_fwd until we reach a source edge (parent == self)
    while True:
        path.append(curr)
        if curr not in parent_fwd:
            break
        parent = parent_fwd[curr]
        if parent == curr:  # Reached a source edge
            break
        curr = parent
    path.reverse()
    
    # Backward path: meeting -> target
    # Trace forward through parent_bwd until we reach a target edge (parent == self)
    curr = meeting
    while True:
        if curr not in parent_bwd:
            break
        parent = parent_bwd[curr]
        if parent == curr:  # Reached a target edge
            break
        curr = parent
        path.append(curr)
    
    return QueryResult(best, path, True)


def find_nearest_edges(lat: float, lng: float, edges_df, k: int = 5, 
                       radius_meters: float = 500.0) -> List[Tuple[int, float]]:
    """
    Find k nearest edges to a point using geometry.
    
    Args:
        lat: Latitude
        lng: Longitude
        edges_df: DataFrame with edge geometries
        k: Number of nearest edges to return
        radius_meters: Maximum search radius
    
    Returns:
        List of (edge_id, distance) tuples, sorted by distance
    """
    from shapely import wkt
    from shapely.geometry import Point
    
    query_point = Point(lng, lat)
    results = []
    
    for _, row in edges_df.iterrows():
        edge_id = row['id']
        try:
            geom = wkt.loads(row['geometry'])
            # Calculate distance (simplified - actual distance in meters)
            # This is approximate - for production use proper projection
            dist_deg = query_point.distance(geom)
            # Rough conversion: 1 degree ≈ 111km at equator
            dist_m = dist_deg * 111000
            
            if dist_m <= radius_meters:
                results.append((edge_id, dist_m))
        except:
            continue
    
    # Sort by distance and return top k
    results.sort(key=lambda x: x[1])
    return results[:k]


def knn_route(source_lat: float, source_lng: float,
              target_lat: float, target_lng: float,
              edges_df, fwd_adj: dict, bwd_adj: dict, edge_meta: dict,
              k: int = 5, radius: float = 500.0) -> QueryResult:
    """
    KNN routing: find k nearest edges to source and target, then route.
    
    Args:
        source_lat, source_lng: Source coordinates
        target_lat, target_lng: Target coordinates
        edges_df: DataFrame with edge geometries
        fwd_adj, bwd_adj: Adjacency lists
        edge_meta: Edge metadata
        k: Number of nearest edges to consider
        radius: Search radius in meters
    
    Returns:
        QueryResult with best path
    """
    # Find k nearest edges to source and target
    source_edges = find_nearest_edges(source_lat, source_lng, edges_df, k, radius)
    target_edges = find_nearest_edges(target_lat, target_lng, edges_df, k, radius)
    
    if not source_edges or not target_edges:
        return QueryResult(-1, [], False)
    
    # Extract just the edge IDs
    src_edge_ids = [e[0] for e in source_edges]
    tgt_edge_ids = [e[0] for e in target_edges]
    
    # Run multi-source/multi-target routing
    return query_multi(src_edge_ids, tgt_edge_ids, fwd_adj, bwd_adj, edge_meta)


def compare_knn_modes(source_lat: float, source_lng: float,
                      target_lat: float, target_lng: float,
                      edges_df, fwd_adj: dict, bwd_adj: dict, edge_meta: dict,
                      max_k: int = 10) -> Dict:
    """
    Compare KNN routing for different k values.
    
    Returns dict with k as key and (distance, path_length) as value.
    """
    results = {}
    
    for k in range(1, max_k + 1):
        result = knn_route(source_lat, source_lng, target_lat, target_lng,
                          edges_df, fwd_adj, bwd_adj, edge_meta, k=k)
        results[k] = {
            'distance': result.distance,
            'path_length': len(result.path) if result.reachable else 0,
            'reachable': result.reachable
        }
    
    return results
