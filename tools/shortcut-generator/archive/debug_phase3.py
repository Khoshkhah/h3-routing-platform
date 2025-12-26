#!/usr/bin/env python3
"""Debug script to run Phase 3 and 4 only, using existing Phase 2 results."""

import time
import sys
sys.path.insert(0, 'src')

print("Starting debug script...")

from generate_shortcuts_partitioned import ShortcutProcessor, format_time, SP_METHOD, logger, log_conf

def main():
    db_path = "persist/single_db_partitioned.db"
    print(f"Connecting to {db_path}...")
    
    # Create processor (this connects and loads h3)
    processor = ShortcutProcessor(
        db_path=db_path,
        deactivated_table="deactivated_shortcuts",
        partition_res=7,
        elementary_table="elementary"
    )
    con = processor.con
    print("Processor created.")
    
    # Check if deactivated_shortcuts exists
    count = con.sql("SELECT count(*) FROM deactivated_shortcuts").fetchone()[0]
    print(f"Found {count} shortcuts in deactivated_shortcuts from Phase 2.")
    logger.info(f"Found {count} shortcuts in deactivated_shortcuts from Phase 2.")
    
    # PHASE 3
    print("Starting Phase 3...")
    log_conf.log_section(logger, "PHASE 3: BACKWARD CONSOLIDATION (DEBUG)")
    phase3_start = time.time()
    processor.process_backward_phase3_consolidation()
    print(f"Phase 3 complete ({format_time(time.time() - phase3_start)}).")
    logger.info(f"Phase 3 complete ({format_time(time.time() - phase3_start)}).")
    
    # PHASE 4
    print("Starting Phase 4...")
    log_conf.log_section(logger, "PHASE 4: BACKWARD CHUNKED (DEBUG)")
    phase4_start = time.time()
    processor.process_backward_phase4_chunked()
    print(f"Phase 4 complete ({format_time(time.time() - phase4_start)}).")
    logger.info(f"Phase 4 complete ({format_time(time.time() - phase4_start)}).")
    
    # Summary
    forward = con.sql("SELECT count(*) FROM deactivated_shortcuts").fetchone()[0]
    try:
        backward = con.sql("SELECT count(*) FROM final_deactivated").fetchone()[0]
    except:
        backward = 0
    print(f"Forward: {forward}, Backward: {backward}")
    logger.info(f"Forward: {forward}, Backward: {backward}")
    
    con.close()

if __name__ == "__main__":
    main()
