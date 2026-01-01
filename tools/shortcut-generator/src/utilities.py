
import os
import duckdb
import h3
from pathlib import Path


def initialize_duckdb(db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    """Initialize DuckDB connection and register UDFs."""
    con = duckdb.connect(db_path)
    
    # Enforce memory limit if configured via environment variable
    memory_limit = os.environ.get("DUCKDB_MEMORY_LIMIT")
    if memory_limit:
        con.execute(f"SET memory_limit='{memory_limit}'")
    
    # Tuning for performance/memory
    con.execute("SET preserve_insertion_order=false")
    
    # Load spatial extension (required for RTREE indexes in DuckOSM DBs)
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
    except Exception:
        pass
    
    # Set temp directory for spilling if persistence is enabled
    persist_dir = os.environ.get("DUCKDB_PERSIST_DIR")
    if persist_dir:
        temp_dir = Path(persist_dir) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        con.execute(f"SET temp_directory='{temp_dir}'")
    
    # Register H3 UDFs (may already exist if connecting to persistent DB)
    register_h3_udfs(con)
    
    return con


def register_h3_udfs(con: duckdb.DuckDBPyConnection) -> None:
    """Register H3 UDFs for both BIGINT and UBIGINT types."""
    def register_udf(name, func, args, ret):
        try:
            con.create_function(name, func, args, ret)
        except duckdb.CatalogException:
            pass # Function already exists
        except Exception:
            pass
            
    register_udf("h3_lca", _find_lca_impl, ["BIGINT", "BIGINT"], "BIGINT")
    register_udf("h3_resolution", _find_resolution_impl, ["BIGINT"], "INTEGER")
    register_udf("h3_parent", _get_parent_cell_impl, ["BIGINT", "INTEGER"], "BIGINT")
    
    # Register UBIGINT versions (for DuckOSM compatibility)
    register_udf("h3_lca", _find_lca_impl, ["UBIGINT", "UBIGINT"], "BIGINT")
    register_udf("h3_resolution", _find_resolution_impl, ["UBIGINT"], "INTEGER")
    register_udf("h3_parent", _get_parent_cell_impl, ["UBIGINT", "INTEGER"], "BIGINT")

# ============================================================================
# H3 IMPLEMENTATIONS (Pure Python)
# ============================================================================

def _find_lca_impl(cell1: int, cell2: int) -> int:
    """Find the LCA of two H3 cells (Fast Bitwise)."""
    if cell1 == 0 or cell2 == 0:
        return 0
    
    a = cell1
    b = cell2

    # 1. Extract resolutions (bits 52-55)
    res_a = (a >> 52) & 0xF
    res_b = (b >> 52) & 0xF
    common_res = min(res_a, res_b)

    # 2. Mask both to the coarsest input resolution
    # This zeroes out any 'extra' detail bits in the finer cell
    shift_alignment = 45 - (common_res * 3)
    alignment_mask = (0xFFFFFFFFFFFFFFFF << shift_alignment) & 0xFFFFFFFFFFFFFFFF
    
    a_aligned = a & alignment_mask
    b_aligned = b & alignment_mask

    # 3. XOR to find where they diverge
    # Mask out Resolution bits (52-55) to check only Base Cell + Index Digits
    RES_MASK = ~(0xF << 52) 
    diff = (a_aligned & RES_MASK) ^ (b_aligned & RES_MASK)

    if diff == 0:
        # One cell is a direct ancestor of the other
        return cell1 if res_a < res_b else cell2

    # 4. Find divergence resolution
    msb_diff = diff.bit_length()
    
    if msb_diff > 45: 
        return 0 # Different base cells -> No common ancestor

    diverge_res = (45 - msb_diff) // 3
    
    # 5. Construct the final Parent Index
    final_shift = 45 - (diverge_res * 3)
    
    lcp_int = (a & (0xFFFFFFFFFFFFFFFF << final_shift))
    lcp_int &= ~(0xF << 52)         # Clear resolution bits
    lcp_int |= (diverge_res << 52)  # Set new resolution bits
    
    # Set 'unused' child bits to 1s (padding)
    padding_mask = ~(0xFFFFFFFFFFFFFFFF << final_shift) & 0xFFFFFFFFFFFFFFFF
    lcp_int |= padding_mask

    return lcp_int

def _find_lca_impl_old(cell1: int, cell2: int) -> int:
    """Find the LCA of two H3 cells."""
    if cell1 == 0 or cell2 == 0:
        return 0
    try:
        cell1_str = h3.int_to_str(cell1)
        cell2_str = h3.int_to_str(cell2)
        min_res = min(h3.get_resolution(cell1_str), h3.get_resolution(cell2_str))
        for res in range(min_res, -1, -1):
            p1 = h3.cell_to_parent(cell1_str, res)
            p2 = h3.cell_to_parent(cell2_str, res)
            if p1 == p2:
                return h3.str_to_int(p1)
    except:
        pass
    return 0

def _find_resolution_impl(cell: int) -> int:
    """Get resolution of an H3 cell."""
    if cell == 0:
        return -1
    try:
        return h3.get_resolution(h3.int_to_str(cell))
    except:
        return -1

def _get_parent_cell_impl(cell: int, target_res: int) -> int:
    """Get parent cell at target resolution."""
    if cell == 0 or target_res < 0:
        return 0
    try:
        cell_str = h3.int_to_str(cell)
        cell_res = h3.get_resolution(cell_str)
        if target_res > cell_res:
            return cell
        return h3.str_to_int(h3.cell_to_parent(cell_str, target_res))
    except:
        return 0

# ============================================================================
# DATA OPERATIONS
# ============================================================================

def read_edges(con: duckdb.DuckDBPyConnection, file_path: str) -> None:
    """Load edges into 'edges' table."""
    con.execute(f"""
        CREATE OR REPLACE TABLE edges AS 
        SELECT edge_index AS id, from_cell, to_cell, lca_res::TINYINT as lca_res
        FROM read_csv_auto('{file_path}')
    """)

def create_edges_cost_table(con: duckdb.DuckDBPyConnection, file_path: str) -> None:
    """Load edges with cost calculation into 'edges_cost' table."""
    con.execute(f"""
        CREATE OR REPLACE TABLE edges_cost AS 
        SELECT 
            edge_index AS id,
            CASE 
                WHEN maxspeed <= 0 THEN 1e308 
                ELSE length / maxspeed 
            END AS cost
        FROM read_csv_auto('{file_path}')
    """)

def initial_shortcuts_table(con: duckdb.DuckDBPyConnection, file_path: str) -> None:
    """Create 'shortcuts' table from edge graph and edge costs."""
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts AS
        SELECT 
            g.from_edge,
            g.to_edge,
            c.cost,
            g.to_edge AS via_edge
        FROM read_csv_auto('{file_path}') g
        LEFT JOIN edges_cost c ON g.from_edge = c.id
    """)

def assign_cell_forward(con: duckdb.DuckDBPyConnection, current_res: int) -> None:
    """
    Update 'shortcuts' table with 'current_cell' for FORWARD pass.
    Creates 'shortcuts_next' with valid assignments.
    
    MATCHES SPARK: Returns UNION of inner_cell AND outer_cell assignments.
    Shortcuts valid for both will appear twice with different cells.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_next AS
        WITH calculated AS (
            SELECT 
                s.*,
                -- Join A (incoming)
                e1.to_cell AS a_to, 
                e1.from_cell AS a_from, 
                e1.lca_res AS lca_in,
                -- Join B (outgoing)
                e2.to_cell AS b_to, 
                e2.from_cell AS b_from, 
                e2.lca_res AS lca_out,
                -- Computations
                GREATEST(e1.lca_res, e2.lca_res)::TINYINT AS lca_res,
                h3_lca(e1.to_cell, e2.from_cell) AS inner_cell,
                h3_lca(e1.from_cell, e2.to_cell) AS outer_cell
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        ),
        resolutions AS (
            SELECT 
                *,
                h3_resolution(inner_cell) AS inner_res,
                h3_resolution(outer_cell) AS outer_res
            FROM calculated
        ),
        -- Part 1: Assign to INNER_CELL
        -- Valid when: lca_res <= current_res AND inner_res >= current_res
        inner_assignments AS (
            SELECT 
                from_edge, to_edge, cost, via_edge,
                CASE 
                    WHEN inner_res < {current_res} THEN h3_parent(a_from, {current_res})
                    ELSE h3_parent(inner_cell, {current_res})
                END AS current_cell
            FROM resolutions
            WHERE lca_res <= {current_res} AND inner_res >= {current_res}
        ),
        -- Part 2: Assign to OUTER_CELL
        -- Valid when: lca_res <= current_res AND outer_res >= current_res
        outer_assignments AS (
            SELECT 
                from_edge, to_edge, cost, via_edge,
                CASE 
                    WHEN outer_res < {current_res} THEN h3_parent(a_from, {current_res})
                    ELSE h3_parent(outer_cell, {current_res})
                END AS current_cell
            FROM resolutions
            WHERE lca_res <= {current_res} AND outer_res >= {current_res}
        )
        -- Union both (shortcuts valid for both will appear twice with different cells)
        SELECT * FROM inner_assignments
        UNION ALL
        SELECT * FROM outer_assignments
    """)

def assign_cell_phase2(con: duckdb.DuckDBPyConnection, current_res: int, chunk_cell_id: int = None) -> None:
    """
    Cell assignment for Phase 2 consolidation.
    
    Creates single-copy cell assignments:
    - If inner_cell is valid at current_res, assign to inner_cell
    - Else if outer_cell is valid, assign to outer_cell
    - Only deactivates when BOTH are NULL at this resolution
    
    Creates 'shortcuts_next' with exactly ONE copy per shortcut.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_next AS
        WITH calculated AS (
            SELECT 
                s.from_edge, s.to_edge, s.cost, s.via_edge,
                e1.to_cell AS a_to, 
                e1.from_cell AS a_from, 
                GREATEST(e1.lca_res, e2.lca_res)::TINYINT AS lca_res,
                h3_lca(e1.to_cell, e2.from_cell) AS inner_cell,
                h3_lca(e1.from_cell, e2.to_cell) AS outer_cell
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        ),
        resolutions AS (
            SELECT 
                *,
                h3_resolution(inner_cell) AS inner_res,
                h3_resolution(outer_cell) AS outer_res,
                (lca_res <= {current_res} AND h3_resolution(inner_cell) >= {current_res}) AS inner_valid,
                (lca_res <= {current_res} AND h3_resolution(outer_cell) >= {current_res}) AS outer_valid
            FROM calculated
        )
        SELECT 
            from_edge, to_edge, cost, via_edge,
            CASE 
                WHEN inner_valid THEN h3_parent(inner_cell, {current_res})
                WHEN outer_valid THEN h3_parent(outer_cell, {current_res})
                ELSE NULL
            END AS current_cell
        FROM resolutions
    """)

def assign_cell_backward(con: duckdb.DuckDBPyConnection, current_res: int) -> None:
    """
    Update 'shortcuts' table with 'current_cell' for BACKWARD pass.
    
    Key difference from forward:
    - Assigns shortcuts to BOTH inner_cell AND outer_cell (UNION)
    - Filters: lca_res <= current_res AND (inner_res >= current_res OR outer_res >= current_res)
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_next AS
        WITH calculated AS (
            SELECT 
                s.*,
                e1.to_cell AS a_to, 
                e1.from_cell AS a_from, 
                e1.lca_res AS lca_in,
                e2.to_cell AS b_to, 
                e2.from_cell AS b_from, 
                e2.lca_res AS lca_out,
                GREATEST(e1.lca_res, e2.lca_res)::TINYINT AS lca_res,
                h3_lca(e1.to_cell, e2.from_cell) AS inner_cell,
                h3_lca(e1.from_cell, e2.to_cell) AS outer_cell
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        ),
        resolutions AS (
            SELECT 
                *,
                h3_resolution(inner_cell) AS inner_res,
                h3_resolution(outer_cell) AS outer_res
            FROM calculated
        ),
        -- Part 1: Assign to INNER_CELL
        -- Valid when: lca_res <= current_res AND inner_res >= current_res
        inner_assignments AS (
            SELECT 
                from_edge, to_edge, cost, via_edge,
                CASE 
                    WHEN inner_res < {current_res} THEN h3_parent(a_from, {current_res})
                    ELSE h3_parent(inner_cell, {current_res})
                END AS current_cell
            FROM resolutions
            WHERE lca_res <= {current_res} AND inner_res >= {current_res}
        ),
        -- Part 2: Assign to OUTER_CELL  
        -- Valid when: lca_res <= current_res AND outer_res >= current_res
        outer_assignments AS (
            SELECT 
                from_edge, to_edge, cost, via_edge,
                CASE 
                    WHEN outer_res < {current_res} THEN h3_parent(a_from, {current_res})
                    ELSE h3_parent(outer_cell, {current_res})
                END AS current_cell
            FROM resolutions
            WHERE lca_res <= {current_res} AND outer_res >= {current_res}
        )
        -- Union both (shortcuts valid for both will appear twice with different cells)
        SELECT * FROM inner_assignments
        UNION ALL
        SELECT * FROM outer_assignments
    """)

def assign_cell_backward_from_table(con: duckdb.DuckDBPyConnection, current_res: int, source_table: str) -> None:
    """
    Backward cell assignment from a specific source table (for chunked processing).
    Uses to_edge for cell assignment direction.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_next AS
        WITH calculated AS (
            SELECT 
                s.from_edge, s.to_edge, s.cost, s.via_edge,
                e1.to_cell AS a_to, 
                e1.from_cell AS a_from, 
                GREATEST(e1.lca_res, e2.lca_res)::TINYINT AS lca_res,
                h3_lca(e1.to_cell, e2.from_cell) AS inner_cell,
                h3_lca(e1.from_cell, e2.to_cell) AS outer_cell
            FROM {source_table} s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        ),
        resolutions AS (
            SELECT 
                *,
                h3_resolution(inner_cell) AS inner_res,
                h3_resolution(outer_cell) AS outer_res,
                (lca_res <= {current_res} AND h3_resolution(outer_cell) >= {current_res}) AS outer_valid,
                (lca_res <= {current_res} AND h3_resolution(inner_cell) >= {current_res}) AS inner_valid
            FROM calculated
        )
        SELECT 
            from_edge, to_edge, cost, via_edge,
            CASE 
                WHEN outer_valid THEN h3_parent(outer_cell, {current_res})
                WHEN inner_valid THEN h3_parent(inner_cell, {current_res})
                ELSE NULL
            END AS current_cell
        FROM resolutions
    """)

def assign_cell_phase2_backward(con: duckdb.DuckDBPyConnection, current_res: int) -> None:
    """
    Cell assignment for Phase 4 backward consolidation.
    Uses to_edge direction - prioritizes outer_cell over inner_cell.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_next AS
        WITH calculated AS (
            SELECT 
                s.from_edge, s.to_edge, s.cost, s.via_edge,
                e1.to_cell AS a_to, 
                e1.from_cell AS a_from, 
                GREATEST(e1.lca_res, e2.lca_res)::TINYINT AS lca_res,
                h3_lca(e1.to_cell, e2.from_cell) AS inner_cell,
                h3_lca(e1.from_cell, e2.to_cell) AS outer_cell
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        ),
        resolutions AS (
            SELECT 
                *,
                h3_resolution(inner_cell) AS inner_res,
                h3_resolution(outer_cell) AS outer_res,
                (lca_res <= {current_res} AND h3_resolution(outer_cell) >= {current_res}) AS outer_valid,
                (lca_res <= {current_res} AND h3_resolution(inner_cell) >= {current_res}) AS inner_valid
            FROM calculated
        )
        SELECT 
            from_edge, to_edge, cost, via_edge,
            CASE 
                WHEN outer_valid THEN h3_parent(outer_cell, {current_res})
                WHEN inner_valid THEN h3_parent(inner_cell, {current_res})
                ELSE NULL
            END AS current_cell
        FROM resolutions
    """)

def merge_shortcuts(con: duckdb.DuckDBPyConnection) -> None:

    """
    Merge 'shortcuts_next' into 'shortcuts', keeping min cost.
    Optimized for memory by using TEMPORARY tables.
    """
    con.execute("DROP TABLE IF EXISTS shortcuts_merged")
    con.execute("""
        CREATE TEMPORARY TABLE shortcuts_merged AS
        SELECT from_edge, to_edge, cost, via_edge FROM shortcuts
        UNION ALL
        SELECT from_edge, to_edge, cost, via_edge FROM shortcuts_next
    """)
    
    # Use arg_min to get via_edge from row with minimum cost
    con.execute("""
        CREATE OR REPLACE TABLE shortcuts AS
        SELECT 
            from_edge, 
            to_edge, 
            min(cost) as cost, 
            arg_min(via_edge, cost) as via_edge
        FROM shortcuts_merged
        GROUP BY from_edge, to_edge
    """)
    
    con.execute("DROP TABLE shortcuts_merged")
    con.execute("DROP TABLE IF EXISTS shortcuts_next")

def add_final_info(con: duckdb.DuckDBPyConnection) -> None:
    """
    Finalize 'shortcuts' table: add 'cell' and 'inside'.
    Filters invalid shortcuts.
    Casts to C++-compatible types: INT for edge IDs, TINYINT for inside.
    """
    con.execute("""
        CREATE OR REPLACE TABLE shortcuts_final AS
        WITH calculated AS (
            SELECT 
                s.*,
                e1.lca_res AS lca_in,
                e2.lca_res AS lca_out,
                GREATEST(e1.lca_res, e2.lca_res)::TINYINT AS lca_res,
                h3_resolution(h3_lca(e1.to_cell, e2.from_cell))::TINYINT AS inner_res,
                h3_lca(e1.from_cell, e2.to_cell) AS outer_cell,
                h3_resolution(h3_lca(e1.from_cell, e2.to_cell))::TINYINT AS outer_res
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        ),
        with_inside AS (
            SELECT 
                from_edge, to_edge, cost, via_edge,
                outer_cell, lca_in, lca_out, lca_res, inner_res, outer_res,
                CASE 
                    WHEN lca_res > inner_res THEN -2 -- outer-only (base edge)
                    WHEN lca_in = lca_out THEN 0     -- lateral
                    WHEN lca_in < lca_out THEN -1    -- downward
                    ELSE 1                           -- upward
                END AS inside
            FROM calculated
            WHERE lca_res <= inner_res OR lca_res <= outer_res
        )
        SELECT 
            CAST(from_edge AS INT) AS from_edge,
            CAST(to_edge AS INT) AS to_edge,
            cost,
            CAST(via_edge AS INT) AS via_edge,
            CAST(inside AS TINYINT) AS inside,
            h3_parent(outer_cell, CAST(LEAST(lca_in, lca_out) AS INTEGER)) AS cell
        FROM with_inside
    """)
    
    con.execute("CREATE OR REPLACE TABLE shortcuts AS SELECT * FROM shortcuts_final")
    con.execute("DROP TABLE shortcuts_final")

def checkpoint(con: duckdb.DuckDBPyConnection) -> None:
    """Flush WAL to database file."""
    con.execute("CHECKPOINT")

def save_output(con: duckdb.DuckDBPyConnection, output_path: str) -> None:
    """Save 'shortcuts' table to Parquet."""
    con.execute(f"COPY shortcuts TO '{output_path}' (FORMAT PARQUET)")
