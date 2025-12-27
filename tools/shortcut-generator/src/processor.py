import logging
import time
from pathlib import Path
import duckdb
import h3
import pandas as pd

import utilities as utils
from sp_methods.pure import compute_shortest_paths_pure_duckdb
from sp_methods.scipy import process_partition_scipy

import logging_config as log_conf

logger = logging.getLogger(__name__)

PARTITION_RES = 7

import os
#SP_METHOD = os.environ.get("SP_METHOD", "SCIPY")
SP_METHOD = "SCIPY"





class ShortcutProcessor:
    def __init__(self, db_path: str, forward_deactivated_table: str, backward_deactivated_table: str, 
                 partition_res: int = PARTITION_RES, elementary_table: str = "elementary_table",
                 sp_method: str = None, hybrid_res: int = 10):
        self.con = utils.initialize_duckdb(db_path)
        self.forward_deactivated_table = forward_deactivated_table
        self.backward_deactivated_table = backward_deactivated_table
        self.partition_res = partition_res
        self.elementary_table = elementary_table
        self.sp_method = sp_method or SP_METHOD  # Use global if not specified
        self.hybrid_res = hybrid_res
        self.current_cells = []  # Tracks active cell IDs across phases
        # Ensure deactivated table exists (with full H3 schema)
        self.con.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.forward_deactivated_table} (
                from_edge INTEGER, 
                to_edge INTEGER, 
                cost FLOAT, 
                via_edge INTEGER,
                lca_res INTEGER,
                inner_cell BIGINT,
                outer_cell BIGINT,
                inner_res TINYINT,
                outer_res TINYINT
            )
        """)

        self.con.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.backward_deactivated_table} (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, inner_res TINYINT, outer_res TINYINT
            )
        """)

    def clear_backward_deactivated_shortcuts(self):
        self.con.execute(f"DELETE FROM {self.backward_deactivated_table}")
        self.con.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.backward_deactivated_table} (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, inner_res TINYINT, outer_res TINYINT
            )
        """)

    def get_sp_method_for_resolution(self, res: int, is_forward: bool) -> str:
        """
        Determine which SP method to use based on resolution and phase direction.
        
        For HYBRID mode:
          - Phase 1 (forward, 15 -> partition_res): 
            - res >= hybrid_res: PURE
            - res < hybrid_res: SCIPY
          - Phase 4 (backward, partition_res+1 -> 15):
            - res < hybrid_res: SCIPY
            - res >= hybrid_res: PURE
            
        For PURE or SCIPY modes, always return that method.
        """
        if self.sp_method == "HYBRID":
            if res >= self.hybrid_res:
                return "PURE"
            else:
                return "SCIPY"
        else:
            return self.sp_method


    def load_shared_data(self, edges_file: str, graph_file: str):
        """Loads edges and initial shortcuts into the database."""
        # Check if already loaded
        if self.con.sql("SELECT count(*) FROM information_schema.tables WHERE table_name = 'edges'").fetchone()[0] > 0:
            logger.info("Shared data (edges) already loaded, skipping reload.")
            return
            
        logger.info("Loading shared data...")
        utils.read_edges(self.con, edges_file)
        utils.create_edges_cost_table(self.con, edges_file)
        utils.initial_shortcuts_table(self.con, graph_file)
        
        # Pre-calculate metadata and replace elementary_table
        # Note: inner_res and outer_res are pre-computed to avoid repeated h3_resolution() calls
        logger.info("Pre-calculating H3 metadata for elementary shortcuts...")
        self.con.execute(f"""
            CREATE TABLE {self.elementary_table} AS
            SELECT 
                s.from_edge, s.to_edge, s.cost, s.via_edge,
                GREATEST(e1.lca_res, e2.lca_res) AS lca_res,
                h3_lca(e1.to_cell::BIGINT, e2.from_cell::BIGINT)::BIGINT AS inner_cell,
                h3_lca(e1.from_cell::BIGINT, e2.to_cell::BIGINT)::BIGINT AS outer_cell,
                h3_resolution(h3_lca(e1.to_cell::BIGINT, e2.from_cell::BIGINT))::TINYINT AS inner_res,
                h3_resolution(h3_lca(e1.from_cell::BIGINT, e2.to_cell::BIGINT))::TINYINT AS outer_res,
                CAST(NULL AS BIGINT) AS current_cell
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        """)
        self.con.execute("DROP TABLE shortcuts")

    def checkpoint(self):
        self.con.execute("CHECKPOINT")

    def vacuum(self):
        self.con.execute("VACUUM")

    def close(self):
        self.con.close()

    def process_forward_phase1(self, source_table: str = None):
        """
        Processes the entire Forward Phase 1:
        1. Identify chunks at partition resolution.
        2. Loop over chunks.
        3. Fetch shortcuts from source_table.
        4. Run iterative resolution loop (15 -> partition_res).
        5. Save per-cell tables.
        """
        log_conf.log_section(logger, f"PHASE 1: FORWARD PASS (15 -> {self.partition_res})")
        if source_table is None:
            source_table = self.elementary_table

        # Identify chunks at partition resolution using pre-calculated cells
        # Only include cells at resolution >= partition_res
        self.con.execute(f"""
            CREATE OR REPLACE TABLE chunks AS
            SELECT DISTINCT h3_parent(c, {self.partition_res}) as cell_id
            FROM (
                SELECT inner_cell as c FROM {source_table} WHERE inner_cell IS NOT NULL AND h3_resolution(inner_cell) >= {self.partition_res}
                UNION ALL
                SELECT outer_cell as c FROM {source_table} WHERE outer_cell IS NOT NULL AND h3_resolution(outer_cell) >= {self.partition_res}
            )
            WHERE c != 0
        """)
        chunk_ids = [r[0] for r in self.con.execute("SELECT cell_id FROM chunks").fetchall()]
        logger.info(f"Processing {len(chunk_ids)} chunks at resolution {self.partition_res}...")
        
        res_partition_cells = []
        for i, chunk_id in enumerate(chunk_ids, 1):
            # 1. Get initial shortcuts relevant to this chunk using pre-calculated cells
            self.con.execute(f"""
                CREATE OR REPLACE TABLE cell_{chunk_id} AS
                SELECT *
                FROM {source_table}
                WHERE h3_parent(inner_cell, {self.partition_res}) = {chunk_id}
                   OR h3_parent(outer_cell, {self.partition_res}) = {chunk_id}
            """)
            
            # 2. Iterative Forward Pass
            import time as time_module
            for res in range(15, self.partition_res - 1, -1):
                res_start = time_module.time()
                self.assign_cell_to_shortcuts(res, input_table=f"cell_{chunk_id}")
                method = self.get_sp_method_for_resolution(res, is_forward=True)
                active, news, decs = self.process_cell_forward(f"cell_{chunk_id}", method=method)
                res_time = time_module.time() - res_start
                if self.sp_method == "HYBRID":
                    logger.info(f"        Res {res} ({method}): {active}->{news} [{res_time:.2f}s]")
                if active == 0:
                    break
            
            # 3. Save results to per-cell table (Carry all 8 columns)
            chunk_count = self.con.sql(f"SELECT count(*) FROM cell_{chunk_id}").fetchone()[0]
            if chunk_count > 0:
                res_partition_cells.append(chunk_id)
                logger.info(f"  [{i}/{len(chunk_ids)}] Chunk {chunk_id} complete. {chunk_count} shortcuts in pool")
            else:
                logger.info(f"  [{i}/{len(chunk_ids)}] Chunk {chunk_id} complete. 0 shortcuts (all deactivated)")
            
        self.current_cells = res_partition_cells
        
        # Phase 1 summary
        logger.info("--------------------------------------------------")
        total_in_pool = sum(self.con.sql(f"SELECT count(*) FROM cell_{cid}").fetchone()[0] for cid in res_partition_cells)
        total_deactivated = self.con.sql(f"SELECT count(*) FROM {self.forward_deactivated_table}").fetchone()[0]
        logger.info(f"  Summary: {len(res_partition_cells)} cells, {total_in_pool} in pool, {total_deactivated} deactivated")
        
        return res_partition_cells

    def process_forward_phase2_consolidation(self):
        """
        Phase 2: Hierarchical Consolidation (Forward Pass)
        Merges cells upward level by level from partition_res-1 to 0.
        """
        log_conf.log_section(logger, f"PHASE 2: HIERARCHICAL CONSOLIDATION ({self.partition_res-1} -> 0)")
        logger.info(f"  Starting Phase 2 with {len(self.current_cells)} cell tables.")

        for target_res in range(self.partition_res - 1, -2, -1):
            res_start = time.time()
            
            # 1. Group cells by their parent at target_res
            parent_to_children = {}
            for cell_id in self.current_cells:
                parent_id = self.con.execute(f"SELECT h3_parent({cell_id}, {target_res})").fetchone()[0] if target_res >= 0 else 0
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                parent_to_children[parent_id].append(cell_id)
            
            logger.info(f"  Resolution {target_res}: {len(self.current_cells)} cells -> {len(parent_to_children)} parent cells.")
            
            new_cells = []
            # 2. Process each parent cell
            for parent_id, children in parent_to_children.items():
                cell_start = time.time()
                
                # Filter children to only those that actually exist (might have been parent in previous iteration)
                valid_children = []
                for child in children:
                    if self.con.sql(f"SELECT count(*) FROM information_schema.tables WHERE table_name = 'cell_{child}'").fetchone()[0] > 0:
                        valid_children.append(child)
                
                if not valid_children:
                    continue

                # 1. Merge children shortcuts (Carry all 8 columns and deduplicate)
                # If parent_id is in valid_children, we must avoid DROP TABLE collision
                # Solution: Create to a TEMP name first
                #-------------------------------------------------------------
                # warning: need to edit: current_cell column does not need to be in the group by
                #               also we can drop this column
                #-------------------------------------------------------------
                merge_sql = " UNION ALL ".join([f"SELECT * FROM cell_{child}" for child in valid_children])
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE cell_{parent_id}_tmp AS
                    SELECT 
                        from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge,
                        FIRST(lca_res) as lca_res, FIRST(inner_cell) as inner_cell, FIRST(outer_cell) as outer_cell,
                        FIRST(inner_res) as inner_res, FIRST(outer_res) as outer_res
                    FROM ({merge_sql})
                    GROUP BY from_edge, to_edge
                """)
                
                # Drop old child cell tables BEFORE renaming the parent
                for child in valid_children:
                    if child != parent_id:
                        self.con.execute(f"DROP TABLE IF EXISTS cell_{child}")
                
                self.con.execute(f"DROP TABLE IF EXISTS cell_{parent_id}")
                self.con.execute(f"ALTER TABLE cell_{parent_id}_tmp RENAME TO cell_{parent_id}")
                
                merged_count = self.con.sql(f"SELECT count(*) FROM cell_{parent_id}").fetchone()[0]
                
                # 2. Assign and process parent cell
                self.assign_cell_to_shortcuts(target_res, input_table=f"cell_{parent_id}")
                
                # Step 3: Process cell
                active, news, decs = self.process_cell_forward(f"cell_{parent_id}")
                
                # Add to new cells list (even if active is 0, we need to keep the shortcuts for next resolution)
                new_cells.append(parent_id)
                
                logger.info(f"    Parent {parent_id}: {len(valid_children)} children, {merged_count} merged -> {active} active -> {news} pool, {decs} deactivated ({format_time(time.time() - cell_start)})")
            
            # 3. Clean up generic temp tables
            self.con.execute("DROP TABLE IF EXISTS shortcuts_active")
            self.con.execute("DROP TABLE IF EXISTS shortcuts_next")
            self.checkpoint()
            
            self.current_cells = list(set(new_cells))
            logger.info(f"  Res {target_res} complete in {format_time(time.time() - res_start)}. Active cells: {len(self.current_cells)}, Deactivated: {self.con.sql(f'SELECT count(*) FROM {self.forward_deactivated_table}').fetchone()[0]}")

        # Move remaining active cells to deactivated for final processing
        remaining_active = 0
        for cell_id in self.current_cells:
            count = self.con.sql(f"SELECT count(*) FROM cell_{cell_id}").fetchone()[0]
            remaining_active += count
            self.con.execute(f"INSERT INTO {self.forward_deactivated_table} SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res FROM cell_{cell_id}")
            self.con.execute(f"DROP TABLE cell_{cell_id}")
        
        total_forward = self.con.sql(f"SELECT count(*) FROM {self.forward_deactivated_table}").fetchone()[0]
        
        # Deduplicate the deactivated table
        self.con.execute(f"""
            CREATE OR REPLACE TABLE {self.forward_deactivated_table}_dedup AS
            SELECT 
                from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge,
                FIRST(lca_res) as lca_res, FIRST(inner_cell) as inner_cell, FIRST(outer_cell) as outer_cell, FIRST(inner_res) as inner_res, FIRST(outer_res) as outer_res
            FROM {self.forward_deactivated_table}
            GROUP BY from_edge, to_edge
        """)
        self.con.execute(f"DROP TABLE {self.forward_deactivated_table}")
        self.con.execute(f"ALTER TABLE {self.forward_deactivated_table}_dedup RENAME TO {self.forward_deactivated_table}")
        dedup_count = self.con.sql(f"SELECT count(*) FROM {self.forward_deactivated_table}").fetchone()[0]
        
        #log_conf.log_section(logger, "PHASE 2 COMPLETE - FORWARD PASS METRICS")
        logger.info("--------------------------------------------------")
        logger.info(f"  Remaining active at Res -1: {remaining_active}")
        logger.info(f"  Total deactivated (before dedup): {total_forward}")  
        logger.info(f"  Deduplicated forward results: {dedup_count}")
        
        return dedup_count

    def process_backward_phase3_consolidation(self):
        """
        Phase 3: Backward Consolidation (Down from low to partition_res)
        Splits cells downward level by level from 0 (or lowest active) back to partition_res.
        """
        log_conf.log_section(logger, f"PHASE 3: BACKWARD CONSOLIDATION (0 -> {self.partition_res})")
        if not self.current_cells:
            logger.warning("No cells to process in Phase 3.")
            return

        # Start with forward pass results as shortcuts table (already deduplicated)
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts AS
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM {self.forward_deactivated_table}
        """)
        forward_count = self.con.sql("SELECT count(*) FROM shortcuts").fetchone()[0]
        logger.info(f"Starting backward consolidation with {forward_count} shortcuts from forward pass.")



        # Start at resolution 0: all shortcuts in one global cell
        self.con.execute("DROP TABLE IF EXISTS cell_0")
        self.con.execute("ALTER TABLE shortcuts RENAME TO cell_0")
        self.current_cells = [0]
        logger.info(f"  Starting with {forward_count} shortcuts in global cell_0.")

        # Hierarchical Loop (0 -> partition_res-1) - parent to children splitting
        for target_res in range(-1, self.partition_res):
            res_start = time.time()
            
            new_cells = set()  # Use set to avoid duplicates
            total_deactivated = 0
            child_res = target_res + 1
            list_children_cells  = []
            # Step 1: Collect ALL shortcuts from all parents and split into child tables at child_res
            for parent_cell in self.current_cells:
                # Check if parent table exists
                if self.con.sql(f"SELECT count(*) FROM information_schema.tables WHERE table_name = 'cell_{parent_cell}'").fetchone()[0] == 0:
                    continue

                # 1. Divide shortcuts into children using partition_to_children
                active_children = set()

                children_for_parent = self.h3_get_children(parent_cell, child_res)
                t_partition = time.time()
                self.partition_to_children(child_res, children_for_parent, input_table=f"cell_{parent_cell}")
                t_partition = time.time() - t_partition
                
                # 2. Deactivate NULL cells
                null_count = self.con.execute(f"SELECT COUNT(*) FROM cell_{parent_cell} WHERE current_cell IS NULL").fetchone()[0]
                if null_count > 0:
                    self.con.execute(f"""
                        INSERT INTO {self.backward_deactivated_table}
                        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
                        FROM cell_{parent_cell} WHERE current_cell IS NULL
                    """)
                    total_deactivated += null_count
                
                # 3. Identify non-NULL child cells
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE current_splits AS
                    SELECT DISTINCT current_cell FROM cell_{parent_cell} WHERE current_cell IS NOT NULL
                """)
                child_ids = [r[0] for r in self.con.execute("SELECT current_cell FROM current_splits").fetchall()]
                
                # 4. Save shortcuts to child cell tables
                for child_id in child_ids:
                    self.con.execute(f"""
                        CREATE OR REPLACE TABLE cell_{child_id} AS
                        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell
                        FROM cell_{parent_cell} WHERE current_cell = {child_id}
                    """)
                    active_children.add(child_id)
                
                # Handle parent table preservation/drop
                self.con.execute(f"DROP TABLE IF EXISTS cell_{parent_cell}")
              
                # Step 2: Now that all data is split, run SP on each unique child cell
                # NOTE: skip_sp optimization disabled for now (caused incorrect results)
                skip_sp = False  # len(active_children) == 1
                
                new_cells = set()
                for child_id in active_children:
                    child_start = time.time()
                    child_count = self.con.sql(f"SELECT count(*) FROM cell_{child_id}").fetchone()[0]
                    if child_count == 0:
                        self.con.execute(f"DROP TABLE IF EXISTS cell_{child_id}")
                        continue
                    
                    # Shortcuts with lca_res > child_res keep their current_cell for next iteration
                    t_assign = time.time()
                    self.assign_cell_to_shortcuts(child_res, input_table=f"cell_{child_id}")
                    t_assign = time.time() - t_assign
                    
                    # Separate active (current_cell IS NOT NULL) from inactive
                    self.con.execute(f"""
                        CREATE OR REPLACE TABLE cell_{child_id}_active AS
                        SELECT * FROM cell_{child_id} WHERE current_cell IS NOT NULL
                    """)

                    self.con.execute(f"""
                        CREATE OR REPLACE TABLE cell_{child_id}_inactive AS
                        SELECT * FROM cell_{child_id} WHERE current_cell IS NULL
                    """)
                    
                    active_count = self.con.sql(f"SELECT count(*) FROM cell_{child_id}_active").fetchone()[0]
                    
                    # Process (run SP) only if multiple children (skip if only 1 child)
                    t_sp = 0
                    if active_count > 0 and not skip_sp:
                        t_sp = time.time()
                        method = self.get_sp_method_for_resolution(child_res, is_forward=True)
                        self.run_shortest_paths(method=method, input_table=f"cell_{child_id}_active")
                        t_sp = time.time() - t_sp
                      
                    # Merge SP results with inactive shortcuts back into child table
                    self.con.execute(f"""
                        CREATE OR REPLACE TABLE cell_{child_id} AS
                        SELECT * FROM cell_{child_id}_active
                        UNION ALL
                        SELECT * FROM cell_{child_id}_inactive
                    """)
                    self.con.execute(f"DROP TABLE IF EXISTS cell_{child_id}_active")
                    self.con.execute(f"DROP TABLE IF EXISTS cell_{child_id}_inactive")
                    
                    news = self.con.sql(f"SELECT count(*) FROM cell_{child_id}").fetchone()[0]
                    new_cells.add(child_id)
              
                    total_time = time.time() - child_start
                    if skip_sp:
                        logger.info(f"      Cell {child_id}: {child_count} -> {news} (SP skipped) [assign={t_assign:.2f}s, partition={t_partition:.2f}s]")
                    else:
                        logger.info(f"      Cell {child_id}: {child_count} -> {news} [assign={t_assign:.2f}s, partition={t_partition:.2f}s, SP={t_sp:.2f}s]")
                    
                
                self.con.execute("DROP TABLE IF EXISTS current_splits")
                
                # Clean up temp tables
                self.con.execute("DROP TABLE IF EXISTS shortcuts")
                self.con.execute("DROP TABLE IF EXISTS shortcuts_next")
                self.con.execute("DROP TABLE IF EXISTS shortcuts_active")
                self.con.execute("DROP TABLE IF EXISTS children_list")
                self.checkpoint()
                
                list_children_cells += list(active_children)
            self.current_cells = list_children_cells
            
            # Memory management: vacuum every resolution to reclaim space from dropped tables
            self.vacuum()
            logger.info(f"  Res {target_res} -> {child_res} complete in {format_time(time.time() - res_start)}. Active cells: {len(list_children_cells)}, Deactivated so far: {self.con.sql(f'SELECT count(*) FROM {self.backward_deactivated_table}').fetchone()[0]}")

        # Phase 3 complete - remaining cells stay active for Phase 4
        remaining_active = sum(
            self.con.sql(f"SELECT count(*) FROM cell_{cell_id}").fetchone()[0]
            for cell_id in self.current_cells
        )
        total_backward = self.con.sql(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
        logger.info("--------------------------------------------------")
        logger.info(f"  Summary: {len(self.current_cells)} cells ({remaining_active} shortcuts) remain for Phase 4. Deactivated: {total_backward}")
        
        return total_backward

    def process_backward_phase4_chunked(self):
        """
        Phase 4: Process each partition-res cell upward individually.
        For each cell: iterative loop from partition_res+1 -> 15.
        """
        log_conf.log_section(logger, f"PHASE 4: BACKWARD CHUNKED ({self.partition_res+1} -> 15)")
        # Use current_cells from Phase 3 (already at partition_res)
        cell_ids = self.current_cells
        total_shortcuts = sum(
            self.con.sql(f"SELECT count(*) FROM cell_{cell_id}").fetchone()[0] 
            for cell_id in cell_ids
        )
        logger.info(f"Starting Phase 4 with {len(cell_ids)} cells ({total_shortcuts} shortcuts) from Phase 3.")
        
        # Continue using backward_deactivated from Phase 3 (self.backward_deactivated_table is already set)
        # No need to create a new table

        # For each cell, run iterative backward loop (partition_res -> 16)
        for i, cell_id in enumerate(cell_ids, 1):
            chunk_start = time.time()
            cell_table = f"cell_{cell_id}"
            
            cell_count = self.con.sql(f"SELECT count(*) FROM {cell_table}").fetchone()[0]
            if cell_count == 0:
                self.con.execute(f"DROP TABLE IF EXISTS {cell_table}")
                continue
            
            # Iterative backward loop: partition_res+1 -> 16
            for res in range(self.partition_res+1, 16):
                # 1. assign_cell_to_shortcuts - assigns current_cell based on lca_res
                #    Active (lca_res <= res): gets inner/outer parent
                #    Inactive (lca_res > res or both cell_res < res): gets NULL
                self.assign_cell_to_shortcuts(res, input_table=cell_table)
                
                # 2. Separate active (NOT NULL) from inactive (NULL) for SP
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE {cell_table}_active AS
                    SELECT * FROM {cell_table} WHERE current_cell IS NOT NULL
                """)
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE {cell_table}_inactive AS
                    SELECT * FROM {cell_table} WHERE current_cell IS NULL
                """)
                
                active_count = self.con.sql(f"SELECT count(*) FROM {cell_table}_active").fetchone()[0]
                
                # 3. Run SP on active shortcuts
                if active_count > 0:
                    method = self.get_sp_method_for_resolution(res, is_forward=False)
                    self.run_shortest_paths(method=method, input_table=f"{cell_table}_active")
                
                # 4. Merge SP results with inactive back into cell table
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE {cell_table} AS
                    SELECT * FROM {cell_table}_active
                    UNION ALL
                    SELECT * FROM {cell_table}_inactive
                """)
                self.con.execute(f"DROP TABLE IF EXISTS {cell_table}_active")
                self.con.execute(f"DROP TABLE IF EXISTS {cell_table}_inactive")
                
                # Check if any shortcuts remain
                remaining = self.con.sql(f"SELECT count(*) FROM {cell_table}").fetchone()[0]
                if remaining == 0:
                    self.con.execute(f"DROP TABLE IF EXISTS {cell_table}")
                    break
            
            # After processing, insert ALL remaining shortcuts to backward_deactivated
            try:
                final_count = self.con.sql(f"SELECT count(*) FROM {cell_table}").fetchone()[0]
                if final_count > 0:
                    self.con.execute(f"""
                        INSERT INTO {self.backward_deactivated_table} 
                        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
                        FROM {cell_table}
                    """)
                self.con.execute(f"DROP TABLE IF EXISTS {cell_table}")
            except:
                final_count = 0
            
            total_deactivated = self.con.sql(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
            logger.info(f"  [{i}/{len(cell_ids)}] Cell {cell_id}: {cell_count} -> {final_count} after iterative, total: {total_deactivated} ({format_time(time.time() - chunk_start)})")
        
        # Cleanup
        self.con.execute("DROP TABLE IF EXISTS active_shortcuts")
        self.con.execute("DROP TABLE IF EXISTS shortcuts_next")
        self.con.execute("DROP TABLE IF EXISTS shortcuts_active")
        
        # Phase 4 summary
        final_count = self.con.sql(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
        logger.info(f"  Summary: {final_count} total shortcuts in backward_deactivated")
        
        return final_count

    def finalize_and_save(self, output_path: str):
        """Deduplicates backward pass results and saves output."""
        log_conf.log_section(logger, "FINALIZING")
        
        # backward_deactivated contains all shortcuts from Phase 3 + Phase 4
        # Deduplicate to keep MIN(cost) per (from_edge, to_edge)
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_final AS
            SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge
            FROM {self.backward_deactivated_table}
            GROUP BY from_edge, to_edge
        """)
        
        final_count = self.con.sql("SELECT COUNT(*) FROM shortcuts_final").fetchone()[0]
        logger.info(f"Final Count (after dedup): {final_count}")
        
        # Re-rename to shortcuts for standard utilities
        self.con.execute("DROP TABLE IF EXISTS shortcuts")
        self.con.execute("ALTER TABLE shortcuts_final RENAME TO shortcuts")

        utils.add_final_info(self.con)
        utils.save_output(self.con, output_path)
        self.close()
        return final_count

    def assign_cell_to_shortcuts(self, res: int, phase: int = 1, direction: str = "forward", input_table: str = "shortcuts", single_assignment: bool = False):
        """
        Assigns each shortcut to H3 cell(s) at resolution res.
        - lca_res <= res: UNION of h3_parent(inner, res) and h3_parent(outer, res) (activates at this level)
        - lca_res > res: current_cell = NULL (not yet active)
        - Both cell_res < res: current_cell = NULL (can't compute parent)
        - When res=-1: all shortcuts get current_cell = 0 (global)
        
        OPTIMIZED: Uses pre-computed inner_res and outer_res columns.
        """
        self.con.execute(f"DROP TABLE IF EXISTS {input_table}_tmp")
        
        if res == -1:
            # Special case: global level, assign all to cell 0
            self.con.execute(f"""
                CREATE TABLE {input_table}_tmp AS
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell,
                       inner_res, outer_res, 0::BIGINT AS current_cell
                FROM {input_table}
            """)
        else:
            # Optimized 1-to-N assignment using pre-computed resolutions
            self.con.execute(f"""
                CREATE TABLE {input_table}_tmp AS
                WITH with_parents AS (
                    SELECT 
                        from_edge, to_edge, cost, via_edge, lca_res, 
                        inner_cell, outer_cell, inner_res, outer_res,
                        CASE WHEN inner_res >= {res} THEN h3_parent(inner_cell::BIGINT, {res}) ELSE NULL END AS inner_parent,
                        CASE WHEN outer_res >= {res} THEN h3_parent(outer_cell::BIGINT, {res}) ELSE NULL END AS outer_parent
                    FROM {input_table}
                )
                -- 1. Inner Parent (Active)
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, inner_parent AS current_cell
                FROM with_parents 
                WHERE lca_res <= {res} AND inner_parent IS NOT NULL
                
                UNION
                
                -- 2. Outer Parent (Active)
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, outer_parent AS current_cell
                FROM with_parents 
                WHERE lca_res <= {res} AND outer_parent IS NOT NULL
                
                UNION ALL
                
                -- 3. Inactive or Not Yet Active
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, NULL AS current_cell
                FROM with_parents 
                WHERE lca_res > {res} 
                   OR (inner_parent IS NULL AND outer_parent IS NULL)
            """)
        
        self.con.execute(f"DROP TABLE {input_table}")
        self.con.execute(f"ALTER TABLE {input_table}_tmp RENAME TO {input_table}")

    def h3_get_children(self, cell_id: int, res: int) -> list[int]:
        """Helper to get children, handling the global parent 0."""
        if cell_id == 0:
            return [int(h, 16) for h in h3.get_res0_cells()]
        return [int(h, 16) for h in h3.cell_to_children(h3.int_to_str(cell_id), res)]

    def partition_to_children(self, child_res: int, child_list: list[int], input_table: str = "shortcuts"):
        """
        Implementation of the logic:
        current_cell = (h3_parent(inner, child_res) ∩ child_list) 
                     ∪ (h3_parent(outer, child_res) ∩ child_list)
        If the intersection is empty, returns NULL (single row with NULL).
        If both parents match and are different, creates two rows (one per child).
        
        OPTIMIZED: Uses a hash join via temp table instead of IN clause.
        """
        self.con.execute(f"""
            ALTER TABLE {input_table} DROP COLUMN IF EXISTS current_cell
        """)    
        
        if not child_list:
            # Early exit: add NULL column
            self.con.execute(f"""
                ALTER TABLE {input_table} 
                ADD COLUMN IF NOT EXISTS current_cell BIGINT DEFAULT NULL
            """)
            return

        # Create temp table for hash join (much faster than IN clause for large lists)
        self.con.execute("DROP TABLE IF EXISTS _child_cells")
        self.con.execute("""
            CREATE TEMP TABLE _child_cells (cell_id BIGINT PRIMARY KEY)
        """)
        # Batch insert child list
        self.con.execute(
            "INSERT INTO _child_cells VALUES " + ",".join(f"({c})" for c in child_list)
        )

        self.con.execute(f"DROP TABLE IF EXISTS {input_table}_tmp")
        self.con.execute(f"""
            CREATE TABLE {input_table}_tmp AS
            WITH with_parents AS (
                SELECT 
                    from_edge, to_edge, cost, via_edge, lca_res, 
                    inner_cell, outer_cell, inner_res, outer_res,
                    h3_parent(inner_cell::BIGINT, {child_res}) AS inner_parent,
                    h3_parent(outer_cell::BIGINT, {child_res}) AS outer_parent
                FROM {input_table}
            ),
            inner_matches AS (
                SELECT p.*, p.inner_parent AS current_cell
                FROM with_parents p
                INNER JOIN _child_cells c ON p.inner_parent = c.cell_id
            ),
            outer_matches AS (
                SELECT p.*, p.outer_parent AS current_cell
                FROM with_parents p
                INNER JOIN _child_cells c ON p.outer_parent = c.cell_id
                WHERE p.inner_parent IS DISTINCT FROM p.outer_parent  -- Avoid duplicate if same cell
            ),
            no_matches AS (
                SELECT p.*, NULL::BIGINT AS current_cell
                FROM with_parents p
                LEFT JOIN _child_cells c1 ON p.inner_parent = c1.cell_id
                LEFT JOIN _child_cells c2 ON p.outer_parent = c2.cell_id
                WHERE c1.cell_id IS NULL AND c2.cell_id IS NULL
            )
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell FROM inner_matches
            UNION ALL
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell FROM outer_matches
            UNION ALL
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell FROM no_matches
        """)

        self.con.execute(f"DROP TABLE {input_table}")
        self.con.execute(f"ALTER TABLE {input_table}_tmp RENAME TO {input_table}")
        self.con.execute("DROP TABLE IF EXISTS _child_cells")

    def process_cell_forward(self, table_name: str, method: str = SP_METHOD):
        """
        Processes shortcuts for a specific pool:
        1. Identifies active shortcuts (current_cell IS NOT NULL).
        2. Deactivated shortcuts (current_cell IS NULL) move to deactivated_table.
        3. Runs SP on active ones.
        4. SP result becomes the new pool (no carrying forward).
        """
        # 1. Split: Active vs Deactivated
        self.con.execute(f"DROP TABLE IF EXISTS shortcuts_to_process")
        self.con.execute(f"CREATE TEMPORARY TABLE shortcuts_to_process AS SELECT * FROM {table_name} WHERE current_cell IS NOT NULL")
        
        # 2. Move deactivated shortcuts to the deactivated_table
        self.con.execute(f"""
            INSERT INTO {self.forward_deactivated_table}
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM {table_name} 
            WHERE current_cell IS NULL
        """)
        deactivated_count = self.con.sql(f"SELECT count(*) FROM {table_name} WHERE current_cell IS NULL").fetchone()[0]
        
        active_count = self.con.sql("SELECT count(*) FROM shortcuts_to_process").fetchone()[0]
        
        new_count = 0
        if active_count > 0:
            # 3. Run Shortest Paths on active ones (result replaces shortcuts_to_process)
            self.run_shortest_paths(method=method, quiet=True, input_table="shortcuts_to_process")
            
            # 4. New pool = SP result
            self.con.execute(f"DROP TABLE {table_name}")
            self.con.execute(f"ALTER TABLE shortcuts_to_process RENAME TO {table_name}")
            new_count = self.con.sql(f"SELECT count(*) FROM {table_name}").fetchone()[0]
            #-----------------------------------------------------
            # warning : there is a bug in the code that the values of new_count is less than active_count for small values of active_count
            #-----------------------------------------------------
            if new_count < active_count:
                logger.info(f"New pool size: {new_count} and active count: {active_count}")
        else:
            # No active shortcuts, empty the pool
            #logger.info(f"No active shortcuts in {table_name}, emptying pool")
            self.con.execute(f"DELETE FROM {table_name}")
            new_count = 0
            
        # Cleanup
        self.con.execute("DROP TABLE IF EXISTS shortcuts_to_process")
        self.con.execute("DROP TABLE IF EXISTS shortcuts_next")
        
        return active_count, new_count, deactivated_count

    def process_cell_backward(self, table_name: str, method: str = SP_METHOD):
        """
        Processes shortcuts for backward pass:
        1. NO deactivation at all in this step.
        2. Run SP on all shortcuts.
        Deactivation is handled separately in the phase orchestration.
        """
        # 1. Include ALL shortcuts for SP (no filtering)
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_active AS
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell
            FROM {table_name}
        """)
        active_count = self.con.sql("SELECT count(*) FROM shortcuts_active").fetchone()[0]
        
        new_count = 0
        if active_count > 0:
            # 2. Replace original table with all data
            self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.con.execute(f"ALTER TABLE shortcuts_active RENAME TO {table_name}")
            
            # 3. Run Shortest Paths on the table
            self.run_shortest_paths(method=method, quiet=True, input_table=table_name)
            new_count = self.con.sql(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        else:
            self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.con.execute(f"CREATE TABLE {table_name} (from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER, lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, current_cell BIGINT)")
            
        return active_count, new_count, 0


    def run_shortest_paths(self, method: str = None, quiet: bool = True, input_table: str = "shortcuts"):
        """
        Run shortest paths on input table. Output replaces the input table.
        
        Optimization: SLIM AND ENRICH
        1. "Drop" extra columns: Only pass core 5 columns to SP algorithms.
        2. SP Algorithm runs on slim data.
        3. "Add" info again: Re-enrich results with original H3 metadata.
        """
        if method is None:
            method = SP_METHOD
        
        # 1. Create a SLIM input table for SP algorithms (only 5 core columns)
        self.con.execute("DROP TABLE IF EXISTS sp_input")
        self.con.execute(f"CREATE TEMPORARY TABLE sp_input AS SELECT from_edge, to_edge, cost, via_edge, current_cell::BIGINT as current_cell FROM {input_table}")
        
        # 2. Run SP Algorithm on sp_input
        if method == "PURE":
            compute_shortest_paths_pure_duckdb(self.con, quiet=quiet, input_table="sp_input")
            # PURE method modifies sp_input in-place, create shortcuts_next from it
            self.con.execute("CREATE OR REPLACE TABLE shortcuts_next AS SELECT * FROM sp_input")
            
        elif method == "SCIPY":
            df = self.con.sql("SELECT * FROM sp_input").df()
            results = []
            for cell, group in df.groupby('current_cell'):
                processed = process_partition_scipy(group)
                if not processed.empty:
                    processed['current_cell'] = cell
                    results.append(processed)
            
            if results:
                final_df = pd.concat(results, ignore_index=True)
                # Deduplicate: keep row with min cost for each (from_edge, to_edge), preserving via_edge
                idx = final_df.groupby(['from_edge', 'to_edge'])['cost'].idxmin()
                final_df = final_df.loc[idx]
                self.con.execute("CREATE OR REPLACE TABLE shortcuts_next AS SELECT from_edge, to_edge, cost, via_edge, current_cell FROM final_df")
            else:
                self.con.execute(f"CREATE OR REPLACE TABLE shortcuts_next AS SELECT * FROM sp_input WHERE 1=0")

        # 3. RE-ENRICH: Calculate metadata columns for all shortcuts
        table_exists = self.con.sql("SELECT count(*) FROM information_schema.tables WHERE table_name = 'shortcuts_next'").fetchone()[0] > 0
        if table_exists:
            self.con.execute("""
                CREATE OR REPLACE TABLE shortcuts_next_enriched AS
                SELECT 
                    s.from_edge, s.to_edge, s.cost, s.via_edge,
                    GREATEST(e1.lca_res, e2.lca_res) as lca_res,
                    h3_lca(e1.to_cell, e2.from_cell)::BIGINT as inner_cell,
                    h3_lca(e1.from_cell, e2.to_cell)::BIGINT as outer_cell,
                    h3_resolution(h3_lca(e1.to_cell, e2.from_cell))::TINYINT as inner_res,
                    h3_resolution(h3_lca(e1.from_cell, e2.to_cell))::TINYINT as outer_res,
                    s.current_cell
                FROM shortcuts_next s
                LEFT JOIN edges e1 ON s.from_edge = e1.id
                LEFT JOIN edges e2 ON s.to_edge = e2.id
            """)
            self.con.execute("DROP TABLE shortcuts_next")
            self.con.execute("ALTER TABLE shortcuts_next_enriched RENAME TO shortcuts_next")
        else:
            # Fallback: create empty shortcuts_next with correct schema if it doesn't exist
            self.con.execute(f"""
                CREATE OR REPLACE TABLE shortcuts_next AS 
                SELECT from_edge, to_edge, cost, via_edge, 
                       0 as lca_res, 0::BIGINT as inner_cell, 0::BIGINT as outer_cell, 
                       0::TINYINT as inner_res, 0::TINYINT as outer_res, 0::BIGINT as current_cell
                FROM {input_table} WHERE 1=0
            """)

        # Replace input_table with result
        self.con.execute(f"DROP TABLE IF EXISTS {input_table}")
        self.con.execute(f"ALTER TABLE shortcuts_next RENAME TO {input_table}")
        
        # Cleanup
        self.con.execute("DROP TABLE IF EXISTS sp_input")


def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"

def log_system_stats(con: duckdb.DuckDBPyConnection, db_path: str):
    """Log DuckDB memory and disk usage."""
    try:
        # Disk usage
        if db_path != ":memory:":
            file_size = Path(db_path).stat().st_size
            size_mb = file_size / (1024 * 1024)
            logger.info(f"  [Stats] DB File Size: {size_mb:.2f} MB")
        
        # Memory usage (DuckDB internal)
        mem_info = con.execute("SELECT * FROM pragma_memory_info() WHERE tag = 'Total'").fetchone()
        if mem_info:
            used_mb = mem_info[1] / (1024 * 1024)
            logger.info(f"  [Stats] DuckDB Memory: {used_mb:.2f} MB")
    except Exception as e:
        logger.warning(f"Failed to log stats: {e}")

def main():
    log_conf.setup_logging("partitioned_shortcuts_single_db")
    log_conf.log_section(logger, f"SHORTCUTS GENERATION - PARTITIONED (SP_METHOD={SP_METHOD})")


    
    total_start = time.time()
    edges_file = str(config.EDGES_FILE)
    graph_file = str(config.GRAPH_FILE)
    
    # Initialize DuckDB
    db_path = ":memory:"
    if config.DUCKDB_PERSIST_DIR:
        db_path = str(Path(config.DUCKDB_PERSIST_DIR) / "single_db_partitioned.db")
        if Path(db_path).exists():
            logger.info(f"Persisted DuckDB found at {db_path}. Attempting to resume.")
        else:
            logger.info(f"No persisted DuckDB found at {db_path}. Starting fresh.")
        
    # Initialize processor (this also initializes DuckDB)
    processor = ShortcutProcessor(db_path, "forward_deactivated_shortcuts", "backward_deactivated_shortcuts",  partition_res=PARTITION_RES)
    
    # 1. Load Shared Data
    processor.load_shared_data(edges_file, graph_file)


    # PHASE 1 & 2 Check (Resume logic)
    # Check if deactivated_shortcuts exists AND has rows
    try:
        populated = processor.con.sql("SELECT count(*) FROM forward_deactivated_shortcuts").fetchone()[0] > 0
    except:
        populated = False
    
    if not populated:
        # PHASE 1: Forward 15 -> PartitionRes (Chunked)
        log_conf.log_section(logger, f"PHASE 1: FORWARD 15 -> {processor.partition_res} (CHUNKED)")
        phase1_start = time.time()
        res_partition_cells = processor.process_forward_phase1()
        logger.info(f"Phase 1 complete ({format_time(time.time() - phase1_start)}). Created {len(res_partition_cells)} cell tables.")
        processor.checkpoint()
        processor.vacuum()

        # PHASE 2: Hierarchical Consolidation
        log_conf.log_section(logger, f"PHASE 2: HIERARCHICAL CONSOLIDATION ({processor.partition_res - 1} -> -1)")
        phase2_start = time.time()
        processor.process_forward_phase2_consolidation()
        logger.info(f"Phase 2 complete ({format_time(time.time() - phase2_start)}).")
    else:
        logger.info("Skipping Phase 1 & 2: 'forward_deactivated_shortcuts' table already exists. Resuming from Phase 3.")
        processor.clear_backward_deactivated_shortcuts()



    # PHASE 3: BACKWARD CONSOLIDATION
    log_conf.log_section(logger, "PHASE 3: BACKWARD CONSOLIDATION")
    phase3_start = time.time()
    processor.process_backward_phase3_consolidation()
    logger.info(f"Phase 3 complete ({format_time(time.time() - phase3_start)}).")

    # PHASE 4: BACKWARD CHUNKED
    log_conf.log_section(logger, "PHASE 4: BACKWARD CHUNKED")
    phase4_start = time.time()
    processor.process_backward_phase4_chunked()
    logger.info(f"Phase 4 complete ({format_time(time.time() - phase4_start)}).")

    # FINALIZE
    processor.finalize_and_save(str(config.SHORTCUTS_OUTPUT_FILE))
    
    logger.info(f"Total time: {format_time(time.time() - total_start)}")

if __name__ == "__main__":
    main()
