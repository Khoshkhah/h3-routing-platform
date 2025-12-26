#!/usr/bin/env python3
"""
generate_test_data.py
=====================

Generate ground truth shortest path distances using scipy for C++ validation.

Usage:
    python scripts/generate_test_data.py \
        --shortcuts /path/to/shortcuts \
        --edges /path/to/edges.csv \
        --output /path/to/test_data.csv \
        --samples 1000
"""

import argparse
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
from pathlib import Path
import random


def load_shortcuts(shortcuts_path: str) -> pd.DataFrame:
    """Load shortcuts from Parquet directory or file."""
    path = Path(shortcuts_path)
    if path.is_dir():
        dfs = []
        for f in path.glob("*.parquet"):
            dfs.append(pq.read_table(f).to_pandas())
        return pd.concat(dfs, ignore_index=True)
    else:
        return pq.read_table(path).to_pandas()


def compute_all_pairs_scipy(shortcuts_df: pd.DataFrame):
    """Compute all-pairs shortest paths using scipy."""
    # Get unique edges
    edges = pd.concat([
        shortcuts_df['incoming_edge'],
        shortcuts_df['outgoing_edge']
    ]).unique()
    n_edges = len(edges)
    
    print(f"Building graph with {n_edges} edges...")
    
    # Map edge IDs to indices
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    idx_to_edge = {i: e for e, i in edge_to_idx.items()}
    
    # Build sparse matrix (use only via_edge==0 for base graph? Or all shortcuts?)
    # For shortcut graph: use ALL shortcuts to get shortest path through hierarchy
    src = shortcuts_df['incoming_edge'].map(edge_to_idx).values
    dst = shortcuts_df['outgoing_edge'].map(edge_to_idx).values
    costs = shortcuts_df['cost'].values
    
    # Handle duplicates - keep minimum cost
    graph = csr_matrix((costs, (src, dst)), shape=(n_edges, n_edges))
    
    print(f"Computing all-pairs shortest paths...")
    dist_matrix = shortest_path(
        csgraph=graph,
        method='auto',
        directed=True,
        return_predecessors=False
    )
    
    return dist_matrix, edge_to_idx, idx_to_edge


def generate_test_data(
    shortcuts_path: str,
    edges_path: str,
    output_path: str,
    num_samples: int = 1000,
    all_pairs: bool = False
):
    """Generate test data CSV with ground truth distances."""
    
    # Load shortcuts
    print(f"Loading shortcuts from {shortcuts_path}...")
    shortcuts_df = load_shortcuts(shortcuts_path)
    print(f"Loaded {len(shortcuts_df):,} shortcuts")
    
    # Load edge metadata to get valid edge IDs and edge costs
    print(f"Loading edges from {edges_path}...")
    edges_df = pd.read_csv(edges_path)
    valid_edges = edges_df['id'].tolist()
    
    # Build edge cost lookup
    edge_costs = {}
    for _, row in edges_df.iterrows():
        edge_costs[row['id']] = row['cost']
    print(f"Loaded {len(valid_edges):,} edges")
    
    # Compute all-pairs
    dist_matrix, edge_to_idx, idx_to_edge = compute_all_pairs_scipy(shortcuts_df)
    
    # Filter to valid edges that exist in the graph
    valid_edges = [e for e in valid_edges if e in edge_to_idx]
    print(f"Valid edges in graph: {len(valid_edges)}")
    
    # Generate test pairs
    if all_pairs:
        print(f"Generating all pairs ({len(valid_edges)} x {len(valid_edges)})...")
        pairs = [(src, dst) for src in valid_edges for dst in valid_edges]
    else:
        print(f"Generating {num_samples} random pairs...")
        random.seed(42)
        pairs = [(random.choice(valid_edges), random.choice(valid_edges)) 
                 for _ in range(num_samples)]
    
    # Look up distances - ADD TARGET EDGE COST to match query_classic
    results = []
    for src, dst in pairs:
        src_idx = edge_to_idx[src]
        dst_idx = edge_to_idx[dst]
        dist = dist_matrix[src_idx, dst_idx]
        
        if dist != np.inf:
            # Add target edge traversal cost (query_classic does this)
            dist += edge_costs.get(dst, 0)
        
        results.append({
            'source': src,
            'target': dst,
            'expected_distance': dist if dist != np.inf else -1
        })
    
    # Save
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    print(f"Saved {len(output_df):,} test cases to {output_path}")
    
    # Stats
    reachable = (output_df['expected_distance'] >= 0).sum()
    print(f"Reachable: {reachable} ({100*reachable/len(output_df):.1f}%)")


def main():
    parser = argparse.ArgumentParser(description='Generate test data for routing validation')
    parser.add_argument('--shortcuts', required=True, help='Path to shortcuts Parquet')
    parser.add_argument('--edges', required=True, help='Path to edges CSV')
    parser.add_argument('--output', required=True, help='Output CSV path')
    parser.add_argument('--samples', type=int, default=1000, help='Number of samples')
    parser.add_argument('--all-pairs', action='store_true', help='Generate all pairs')
    
    args = parser.parse_args()
    
    generate_test_data(
        shortcuts_path=args.shortcuts,
        edges_path=args.edges,
        output_path=args.output,
        num_samples=args.samples,
        all_pairs=args.all_pairs
    )


if __name__ == '__main__':
    main()
