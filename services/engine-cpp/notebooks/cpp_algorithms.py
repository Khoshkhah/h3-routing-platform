"""
Python versions of C++ shortest path algorithms from shortcut_graph.cpp

This module provides exact translations of the C++ algorithms for testing and comparison.

Algorithms:
- query_classic: Bidirectional Dijkstra with inside filtering only
- query_pruned: + H3 resolution-based pruning
- dijkstra_general: Standard Dijkstra using ALL shortcuts (baseline)
- expand_path: Expand shortcut path to base edges

Usage:
    from cpp_algorithms import *
    
    # Load data first (see load_data function)
    data = load_data(shortcuts_path, edges_path)
    
    # Run algorithms
    result_classic = query_classic(source, target, data)
    result_pruned = query_pruned(source, target, data)
    result_dijkstra = dijkstra_general(source, target, data)
"""

from heapq import heappop, heappush
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import math


@dataclass
class QueryResult:
    distance: float
    path: list
    reachable: bool


@dataclass 
class HighCell:
    cell: int
    res: int


@dataclass
class Shortcut:
    from_edge: int
    to_edge: int
    cost: float
    via_edge: int
    cell: int
    inside: int
    cell_res: int


@dataclass
class AlgorithmData:
    """Data structures needed by the algorithms."""
    shortcuts: List[Shortcut]
    fwd_adj: Dict[int, List[Shortcut]]  # edge_id -> list of shortcuts
    bwd_adj: Dict[int, List[Shortcut]]  # edge_id -> list of shortcuts
    edge_meta: Dict[int, dict]  # edge_id -> {'cost', 'lca_res', 'to_cell', 'from_cell'}
    shortcut_lookup: Dict[int, int]  # (from<<32|to) -> shortcut index


def load_data(shortcuts_path: str, edges_path: str) -> AlgorithmData:
    """Load shortcuts and edges into algorithm data structures."""
    import pyarrow.parquet as pq
    import pandas as pd
    import h3
    
    # Load shortcuts
    df = pq.read_table(shortcuts_path).to_pandas()
    
    # Load edges
    edges_df = pd.read_csv(edges_path)
    
    # Build edge metadata
    edge_meta = {}
    for _, row in edges_df.iterrows():
        edge_id = int(row.get('edge_index', row.get('id', 0)))
        edge_meta[edge_id] = {
            'cost': float(row['cost']),
            'lca_res': int(row['lca_res']),
            'to_cell': int(row.get('to_cell', row.get('incoming_cell', 0))),
            'from_cell': int(row.get('from_cell', row.get('outgoing_cell', 0))),
        }
    
    def get_res(c):
        if c == 0:
            return -1
        try:
            return h3.get_resolution(h3.int_to_str(c))
        except:
            return -1
    
    # Build shortcuts and adjacency
    shortcuts = []
    fwd_adj = defaultdict(list)
    bwd_adj = defaultdict(list)
    shortcut_lookup = {}
    
    for idx, row in df.iterrows():
        from_edge = int(row.get('from_edge', row.get('incoming_edge', 0)))
        to_edge = int(row.get('to_edge', row.get('outgoing_edge', 0)))
        cell = int(row.get('cell', 0))
        
        sc = Shortcut(
            from_edge=from_edge,
            to_edge=to_edge,
            cost=float(row['cost']),
            via_edge=int(row['via_edge']),
            cell=cell,
            inside=int(row['inside']),
            cell_res=get_res(cell)
        )
        shortcuts.append(sc)
        fwd_adj[from_edge].append(sc)
        bwd_adj[to_edge].append(sc)
        
        # Build lookup (keep first)
        key = (from_edge << 32) | to_edge
        if key not in shortcut_lookup:
            shortcut_lookup[key] = len(shortcuts) - 1
    
    return AlgorithmData(
        shortcuts=shortcuts,
        fwd_adj=dict(fwd_adj),
        bwd_adj=dict(bwd_adj),
        edge_meta=edge_meta,
        shortcut_lookup=shortcut_lookup
    )


def get_edge_cost(edge_id: int, data: AlgorithmData) -> float:
    """Get edge traversal cost."""
    if edge_id in data.edge_meta:
        return data.edge_meta[edge_id]['cost']
    return 0.0


def compute_high_cell(source_edge: int, target_edge: int, data: AlgorithmData) -> HighCell:
    """Compute LCA cell for source and target edges."""
    import h3
    
    src_meta = data.edge_meta.get(source_edge, {})
    tgt_meta = data.edge_meta.get(target_edge, {})
    
    src_cell = src_meta.get('to_cell', 0)
    tgt_cell = tgt_meta.get('to_cell', 0)
    src_res = src_meta.get('lca_res', -1)
    tgt_res = tgt_meta.get('lca_res', -1)
    
    if src_cell == 0 or tgt_cell == 0:
        return HighCell(0, -1)
    
    # Get cells at their LCA resolutions
    def safe_parent(cell, res):
        if cell == 0 or res < 0:
            return 0
        try:
            cell_str = h3.int_to_str(cell)
            cell_res = h3.get_resolution(cell_str)
            if res > cell_res:
                return cell
            return h3.str_to_int(h3.cell_to_parent(cell_str, res))
        except:
            return 0
    
    src_cell = safe_parent(src_cell, src_res)
    tgt_cell = safe_parent(tgt_cell, tgt_res)
    
    if src_cell == 0 or tgt_cell == 0:
        return HighCell(0, -1)
    
    # Find LCA
    try:
        src_str = h3.int_to_str(src_cell)
        tgt_str = h3.int_to_str(tgt_cell)
        min_res = min(h3.get_resolution(src_str), h3.get_resolution(tgt_str))
        for res in range(min_res, -1, -1):
            if h3.cell_to_parent(src_str, res) == h3.cell_to_parent(tgt_str, res):
                lca = h3.str_to_int(h3.cell_to_parent(src_str, res))
                return HighCell(lca, res)
    except:
        pass
    
    return HighCell(0, -1)


# =============================================================================
# ALGORITHM 1: query_classic (C++ lines 270-398)
# =============================================================================

def query_classic(source_edge: int, target_edge: int, data: AlgorithmData) -> QueryResult:
    """
    Classic bidirectional Dijkstra with inside filtering only.
    Direct translation of C++ ShortcutGraph::query_classic.
    """
    INF = float('inf')
    
    if source_edge == target_edge:
        return QueryResult(get_edge_cost(source_edge, data), [source_edge], True)
    
    dist_fwd: Dict[int, float] = {}
    dist_bwd: Dict[int, float] = {}
    parent_fwd: Dict[int, int] = {}
    parent_bwd: Dict[int, int] = {}
    pq_fwd: List[Tuple[float, int]] = []
    pq_bwd: List[Tuple[float, int]] = []
    
    dist_fwd[source_edge] = 0.0
    parent_fwd[source_edge] = source_edge
    heappush(pq_fwd, (0.0, source_edge))
    
    target_cost = get_edge_cost(target_edge, data)
    dist_bwd[target_edge] = target_cost
    parent_bwd[target_edge] = target_edge
    heappush(pq_bwd, (target_cost, target_edge))
    
    best = INF
    meeting = None
    found = False
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heappop(pq_fwd)
            
            if u in dist_fwd and d > dist_fwd[u]:
                pass  # stale, continue to bwd
            elif d >= best:
                pass  # pruned
            else:
                for sc in data.fwd_adj.get(u, []):
                    if sc.inside != 1:
                        continue
                    
                    nd = d + sc.cost
                    if sc.to_edge not in dist_fwd or nd < dist_fwd[sc.to_edge]:
                        dist_fwd[sc.to_edge] = nd
                        parent_fwd[sc.to_edge] = u
                        heappush(pq_fwd, (nd, sc.to_edge))
                        
                        if sc.to_edge in dist_bwd:
                            total = nd + dist_bwd[sc.to_edge]
                            if total < best:
                                best = total
                                meeting = sc.to_edge
                                found = True
        
        # Backward step
        if pq_bwd:
            d, u = heappop(pq_bwd)
            
            if u in dist_bwd and d > dist_bwd[u]:
                pass  # stale
            elif d >= best:
                pass  # pruned
            else:
                for sc in data.bwd_adj.get(u, []):
                    if sc.inside != -1 and sc.inside != 0:
                        continue
                    
                    nd = d + sc.cost
                    if sc.from_edge not in dist_bwd or nd < dist_bwd[sc.from_edge]:
                        dist_bwd[sc.from_edge] = nd
                        parent_bwd[sc.from_edge] = u
                        heappush(pq_bwd, (nd, sc.from_edge))
                        
                        if sc.from_edge in dist_fwd:
                            total = dist_fwd[sc.from_edge] + nd
                            if total < best:
                                best = total
                                meeting = sc.from_edge
                                found = True
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best:
                break
        elif not pq_fwd and not pq_bwd:
            break
    
    if not found:
        return QueryResult(-1, [], False)
    
    # Reconstruct path
    path = []
    curr = meeting
    
    while True:
        path.append(curr)
        if curr not in parent_fwd or parent_fwd[curr] == curr:
            break
        curr = parent_fwd[curr]
    path.reverse()
    
    curr = meeting
    while True:
        if curr not in parent_bwd or parent_bwd[curr] == curr:
            break
        curr = parent_bwd[curr]
        path.append(curr)
    
    return QueryResult(best, path, True)


# =============================================================================
# ALGORITHM 2: query_pruned (C++ lines 400-580)
# =============================================================================

def query_pruned(source_edge: int, target_edge: int, data: AlgorithmData) -> QueryResult:
    """
    Pruned bidirectional Dijkstra with H3 resolution-based pruning.
    Direct translation of C++ ShortcutGraph::query_pruned.
    """
    INF = float('inf')
    
    if source_edge == target_edge:
        return QueryResult(get_edge_cost(source_edge, data), [source_edge], True)
    
    high = compute_high_cell(source_edge, target_edge, data)
    
    dist_fwd: Dict[int, float] = {}
    dist_bwd: Dict[int, float] = {}
    parent_fwd: Dict[int, int] = {}
    parent_bwd: Dict[int, int] = {}
    
    # Priority queue entries: (distance, edge_id, resolution)
    pq_fwd: List[Tuple[float, int, int]] = []
    pq_bwd: List[Tuple[float, int, int]] = []
    
    # Get initial resolutions
    src_res = data.edge_meta.get(source_edge, {}).get('lca_res', -1)
    tgt_res = data.edge_meta.get(target_edge, {}).get('lca_res', -1)
    
    dist_fwd[source_edge] = 0.0
    parent_fwd[source_edge] = source_edge
    heappush(pq_fwd, (0.0, source_edge, src_res))
    
    target_cost = get_edge_cost(target_edge, data)
    dist_bwd[target_edge] = target_cost
    parent_bwd[target_edge] = target_edge
    heappush(pq_bwd, (target_cost, target_edge, tgt_res))
    
    best = INF
    meeting = None
    found = False
    min_arrival_fwd = INF
    min_arrival_bwd = INF
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u, u_res = heappop(pq_fwd)
            
            # Check meeting
            if u in dist_bwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                total = d + dist_bwd[u]
                if total < best:
                    best = total
                    meeting = u
                    found = True
            
            if u in dist_fwd and d > dist_fwd[u]:
                pass  # stale
            elif d >= best:
                pass  # pruned
            else:
                # FAST PRUNING: resolution comparison
                if u_res < high.res:
                    min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                else:
                    if u_res == high.res:
                        min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                    
                    for sc in data.fwd_adj.get(u, []):
                        if sc.inside != 1:
                            continue
                        
                        nd = d + sc.cost
                        if sc.to_edge not in dist_fwd or nd < dist_fwd[sc.to_edge]:
                            dist_fwd[sc.to_edge] = nd
                            parent_fwd[sc.to_edge] = u
                            heappush(pq_fwd, (nd, sc.to_edge, sc.cell_res))
        
        # Backward step
        if pq_bwd:
            d, u, u_res = heappop(pq_bwd)
            
            # Check meeting
            if u in dist_fwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                total = dist_fwd[u] + d
                if total < best:
                    best = total
                    meeting = u
                    found = True
            
            if u in dist_bwd and d > dist_bwd[u]:
                continue  # stale
            if d >= best:
                continue
            
            # FAST PRUNING: check = (u_res >= high.res)
            check = (u_res >= high.res)
            
            if u_res == high.res or not check:
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
            
            for sc in data.bwd_adj.get(u, []):
                # FAST resolution-based filtering
                allowed = False
                if sc.inside == -1 and check:
                    allowed = True
                elif sc.inside == 0 and u_res <= high.res:
                    allowed = True
                elif sc.inside == -2 and not check:
                    allowed = True
                
                if not allowed:
                    continue
                
                nd = d + sc.cost
                if sc.from_edge not in dist_bwd or nd < dist_bwd[sc.from_edge]:
                    dist_bwd[sc.from_edge] = nd
                    parent_bwd[sc.from_edge] = u
                    heappush(pq_bwd, (nd, sc.from_edge, sc.cell_res))
        
        # Early termination
        if best < INF:
            bound_fwd = min_arrival_fwd
            bound_bwd = min_arrival_bwd
            if pq_fwd:
                bound_fwd = min(bound_fwd, pq_fwd[0][0])
            if pq_bwd:
                bound_bwd = min(bound_bwd, pq_bwd[0][0])
            
            fwd_good = pq_fwd and (pq_fwd[0][0] + bound_bwd < best)
            bwd_good = pq_bwd and (pq_bwd[0][0] + bound_fwd < best)
            if not fwd_good and not bwd_good:
                break
    
    if not found:
        return QueryResult(-1, [], False)
    
    # Reconstruct path
    path = []
    curr = meeting
    
    while True:
        path.append(curr)
        if curr not in parent_fwd or parent_fwd[curr] == curr:
            break
        curr = parent_fwd[curr]
    path.reverse()
    
    curr = meeting
    while True:
        if curr not in parent_bwd or parent_bwd[curr] == curr:
            break
        curr = parent_bwd[curr]
        path.append(curr)
    
    return QueryResult(best, path, True)


# =============================================================================
# ALGORITHM 3: dijkstra_general (baseline - no inside filtering)
# =============================================================================

def dijkstra_general(source_edge: int, target_edge: int, data: AlgorithmData) -> QueryResult:
    """
    Standard Dijkstra using ALL shortcuts (no inside filtering).
    This is the baseline for finding the true shortest path.
    """
    INF = float('inf')
    
    if source_edge == target_edge:
        return QueryResult(get_edge_cost(source_edge, data), [source_edge], True)
    
    dist = {source_edge: 0.0}
    parent = {source_edge: None}
    pq = [(0.0, source_edge)]
    
    while pq:
        d, u = heappop(pq)
        
        if u == target_edge:
            break
        
        if d > dist.get(u, INF):
            continue
        
        for sc in data.fwd_adj.get(u, []):
            nd = d + sc.cost
            if sc.to_edge not in dist or nd < dist[sc.to_edge]:
                dist[sc.to_edge] = nd
                parent[sc.to_edge] = u
                heappush(pq, (nd, sc.to_edge))
    
    if target_edge not in dist:
        return QueryResult(-1, [], False)
    
    # Reconstruct path
    path = []
    curr = target_edge
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    # Add target edge cost to match bidirectional algorithms
    total_cost = dist[target_edge] + get_edge_cost(target_edge, data)
    
    return QueryResult(total_cost, path, True)


# =============================================================================
# EXPAND PATH (convert shortcut path to base edges)
# =============================================================================

def expand_path(shortcut_path: List[int], data: AlgorithmData) -> List[int]:
    """
    Expand a shortcut path to base edges.
    
    Algorithm:
    1. For each consecutive pair (u, v) in path, call expand_edge_pair(u, v)
    2. expand_edge_pair looks up (u, v) in table to get via_edge
    3. If via_edge == u or via_edge == v, return [u, v] (base pair)
    4. Otherwise, recursively expand (u, via) and (via, v), combine results
    """
    if not shortcut_path:
        return []
    if len(shortcut_path) == 1:
        return [shortcut_path[0]]
    
    # Build expansion table: (from_edge, to_edge) -> via_edge
    # Key is the pair, value is the via_edge to expand through
    expansion_table = {}
    for sc in data.shortcuts:
        key = (sc.from_edge, sc.to_edge)
        if key not in expansion_table:
            expansion_table[key] = sc.via_edge
    
    def expand_edge_pair(u: int, v: int, visited: set) -> List[int]:
        """Expand a single edge pair (u, v) to base edges."""
        key = (u, v)
        
        # Cycle detection
        if key in visited:
            return [u, v]
        visited.add(key)
        
        # Look up via_edge for this pair
        if key not in expansion_table:
            # No expansion found - this is a base pair
            return [u, v]
        
        via = expansion_table[key]
        
        # If via equals u or v, can't expand further - base pair
        if via == u or via == v or via == 0:
            return [u, v]
        
        # Recursively expand (u, via) and (via, v)
        left = expand_edge_pair(u, via, visited)
        right = expand_edge_pair(via, v, visited)
        
        # Combine: left ends with junction point, right starts with it
        # Avoid duplicating the junction
        if left and right and left[-1] == right[0]:
            return left + right[1:]
        else:
            return left + right
    
    # Expand each consecutive pair in the path
    result = []
    for i in range(len(shortcut_path) - 1):
        u, v = shortcut_path[i], shortcut_path[i + 1]
        visited = set()
        expanded = expand_edge_pair(u, v, visited)
        
        # Merge with previous result, avoiding duplicate junction
        if not result:
            result = expanded
        elif result and expanded and result[-1] == expanded[0]:
            result.extend(expanded[1:])
        else:
            result.extend(expanded)
    
    return result


# =============================================================================
# COMPARISON UTILITIES
# =============================================================================

def compare_algorithms(source: int, target: int, data: AlgorithmData) -> dict:
    """Compare all algorithms for a single query."""
    r_dijkstra = dijkstra_general(source, target, data)
    r_classic = query_classic(source, target, data)
    r_pruned = query_pruned(source, target, data)
    
    dijkstra_classic_match = abs(r_dijkstra.distance - r_classic.distance) < 0.01 if r_classic.reachable else False
    dijkstra_pruned_match = abs(r_dijkstra.distance - r_pruned.distance) < 0.01 if r_pruned.reachable else False
    classic_pruned_match = abs(r_classic.distance - r_pruned.distance) < 0.01 if r_classic.reachable and r_pruned.reachable else r_classic.reachable == r_pruned.reachable
    
    return {
        'source': source,
        'target': target,
        'dijkstra_cost': r_dijkstra.distance,
        'classic_cost': r_classic.distance,
        'pruned_cost': r_pruned.distance,
        'dijkstra_path': r_dijkstra.path,
        'classic_path': r_classic.path,
        'pruned_path': r_pruned.path,
        'dijkstra_classic_match': dijkstra_classic_match,
        'dijkstra_pruned_match': dijkstra_pruned_match,
        'classic_pruned_match': classic_pruned_match,
    }


def run_comparison(data: AlgorithmData, n_samples: int = 100, seed: int = 42) -> dict:
    """Run comparison on random samples."""
    import random
    random.seed(seed)
    
    all_edges = list(data.fwd_adj.keys())
    
    results = {
        'dijkstra_classic_matches': 0,
        'dijkstra_pruned_matches': 0,
        'classic_pruned_matches': 0,
        'total': 0,
        'failures': []
    }
    
    for i in range(n_samples):
        source = random.choice(all_edges)
        target = random.choice(all_edges)
        if source == target:
            continue
        
        r = compare_algorithms(source, target, data)
        results['total'] += 1
        
        if r['dijkstra_classic_match']:
            results['dijkstra_classic_matches'] += 1
        if r['dijkstra_pruned_match']:
            results['dijkstra_pruned_matches'] += 1
        if r['classic_pruned_match']:
            results['classic_pruned_matches'] += 1
        
        if not r['dijkstra_classic_match'] or not r['dijkstra_pruned_match']:
            if len(results['failures']) < 5:
                results['failures'].append(r)
    
    return results


# =============================================================================
# C++ SERVER COMPARISON
# =============================================================================

def query_cpp_server(source_edge: int, target_edge: int, 
                     dataset: str = "somerset",
                     server_url: str = "http://localhost:8082") -> QueryResult:
    """Query the C++ routing server."""
    import requests
    
    try:
        resp = requests.post(
            f"{server_url}/route_by_edge",
            json={"dataset": dataset, "source_edge": source_edge, "target_edge": target_edge},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            route = data.get('route', {})
            return QueryResult(
                distance=route.get('distance', -1),
                path=route.get('shortcut_path', []),
                reachable=data.get('success', False)
            )
    except Exception as e:
        print(f"Error querying C++ server: {e}")
    
    return QueryResult(-1, [], False)


def compare_with_cpp(source: int, target: int, data: AlgorithmData,
                     dataset: str = "somerset") -> dict:
    """Compare all Python algorithms with C++ server."""
    r_dijkstra = dijkstra_general(source, target, data)
    r_classic = query_classic(source, target, data)
    r_pruned = query_pruned(source, target, data)
    r_cpp = query_cpp_server(source, target, dataset)
    
    def match(a, b):
        if a < 0 or b < 0:
            return a < 0 and b < 0
        return abs(a - b) < 0.01
    
    return {
        'source': source,
        'target': target,
        'dijkstra_cost': r_dijkstra.distance,
        'classic_cost': r_classic.distance,
        'pruned_cost': r_pruned.distance,
        'cpp_cost': r_cpp.distance,
        'dijkstra_path': r_dijkstra.path,
        'classic_path': r_classic.path,
        'pruned_path': r_pruned.path,
        'cpp_path': r_cpp.path,
        'dijkstra_cpp_match': match(r_dijkstra.distance, r_cpp.distance),
        'classic_cpp_match': match(r_classic.distance, r_cpp.distance),
        'pruned_cpp_match': match(r_pruned.distance, r_cpp.distance),
    }


def run_cpp_comparison(data: AlgorithmData, n_samples: int = 100, 
                       dataset: str = "somerset", seed: int = 42) -> dict:
    """Run comparison of Python algorithms vs C++ server."""
    import random
    random.seed(seed)
    
    all_edges = list(data.fwd_adj.keys())
    
    results = {
        'dijkstra_cpp_matches': 0,
        'classic_cpp_matches': 0,
        'pruned_cpp_matches': 0,
        'total': 0,
        'examples': []
    }
    
    for i in range(n_samples):
        source = random.choice(all_edges)
        target = random.choice(all_edges)
        if source == target:
            continue
        
        r = compare_with_cpp(source, target, data, dataset)
        results['total'] += 1
        
        if r['dijkstra_cpp_match']:
            results['dijkstra_cpp_matches'] += 1
        if r['classic_cpp_match']:
            results['classic_cpp_matches'] += 1
        if r['pruned_cpp_match']:
            results['pruned_cpp_matches'] += 1
        
        if len(results['examples']) < 5:
            results['examples'].append(r)
    
    return results
