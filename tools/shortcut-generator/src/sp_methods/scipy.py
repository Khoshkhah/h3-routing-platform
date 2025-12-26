"""
Scipy-based Shortest Path Algorithm
====================================
Uses scipy.sparse.csgraph.dijkstra for efficient shortest path computation.
"""

import logging
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

logger = logging.getLogger(__name__)


def process_partition_scipy(pdf: pd.DataFrame) -> pd.DataFrame:
    """
    Process a single partition using Scipy's shortest_path.
    EXACTLY matches Spark version for identical via_edge output.
    
    Args:
        pdf: DataFrame with columns ['from_edge', 'to_edge', 'via_edge', 'cost']
    
    Returns:
        DataFrame with shortest paths
    """
    if len(pdf) == 0:
        return pd.DataFrame(columns=['from_edge', 'to_edge', 'via_edge', 'cost'])
    
    # Map nodes to indices
    nodes = pd.concat([pdf['from_edge'], pdf['to_edge']]).unique()
    n_nodes = len(nodes)
    node_to_idx = pd.Series(data=np.arange(n_nodes), index=nodes)
    
    # Deduplicate and keep minimum cost
    pdf_dedup = pdf.loc[
        pdf.groupby(['from_edge', 'to_edge'])['cost'].idxmin()
    ]
    
    src_indices = pdf_dedup['from_edge'].map(node_to_idx).values
    dst_indices = pdf_dedup['to_edge'].map(node_to_idx).values
    costs = pdf_dedup['cost'].values
    
    # Store via_edges for direct paths (SAME AS SPARK: +1 offset)
    via_values = pdf_dedup['via_edge'].values + 1
    via_matrix = csr_matrix((via_values, (src_indices, dst_indices)), shape=(n_nodes, n_nodes))
    
    # Build graph matrix
    graph = csr_matrix((costs, (src_indices, dst_indices)), shape=(n_nodes, n_nodes))
    
    # Compute shortest paths (SAME AS SPARK: method='auto')
    dist_matrix, predecessors = shortest_path(
        csgraph=graph,
        method='auto',
        directed=True,
        return_predecessors=True
    )
    
    # Convert back to DataFrame (SAME AS SPARK: chunked processing)
    results = []
    chunk_size = 2000
    
    for start_row in range(0, n_nodes, chunk_size):
        end_row = min(start_row + chunk_size, n_nodes)
        sub_dist = dist_matrix[start_row:end_row, :]
        sub_pred = predecessors[start_row:end_row, :]
        
        valid_mask = (sub_dist != np.inf)
        rows, cols = np.where(valid_mask)
        global_rows = rows + start_row
        
        # Filter self-loops
        non_loop_mask = (global_rows != cols)
        rows = rows[non_loop_mask]
        cols = cols[non_loop_mask]
        global_rows = global_rows[non_loop_mask]
        
        if len(rows) == 0:
            continue
        
        chunk_costs = sub_dist[rows, cols]
        chunk_preds = sub_pred[rows, cols]
        chunk_src = nodes[global_rows]
        chunk_dst = nodes[cols]
        
        # Determine via_edge (SAME AS SPARK: vectorized)
        original_vias = np.array(via_matrix[global_rows, cols]).flatten() - 1
        is_direct = (chunk_preds == global_rows)
        
        final_vias = np.where(
            is_direct,
            original_vias,
            nodes[chunk_preds]
        )
        
        chunk_df = pd.DataFrame({
            'from_edge': chunk_src,
            'to_edge': chunk_dst,
            'via_edge': final_vias,
            'cost': chunk_costs
        })
        results.append(chunk_df)
    
    if not results:
        return pd.DataFrame(columns=['from_edge', 'to_edge', 'via_edge', 'cost'])
    
    return pd.concat(results, ignore_index=True)
