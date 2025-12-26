import argparse
import sys
import os
import yaml
import logging
from src.network_builder import NetworkBuilder

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("osm-to-road")

def main(config_path, output_dir_override=None):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    name = config.get('name', 'output')
    pbf_file = config.get('pbf_path')
    output_dir = output_dir_override or config.get('output_dir', 'data/output')
    
    if not pbf_file:
        logger.error("pbf_path must be specified in config")
        sys.exit(1)
        
    logger.info(f"Starting OSM to Road Network conversion...")
    logger.info(f"Config: {config_path}")
    logger.info(f"Name: {name}")
    logger.info(f"PBF Path: {pbf_file}")
    
    # Build network
    builder = NetworkBuilder(pbf_file, name)
    
    logger.info("Building graph...")
    builder.build_graph()
    
    logger.info("Simplifying graph...")
    builder.simplify_graph()
    
    logger.info("Extracting edges and nodes...")
    builder.extract_edges_and_nodes()
    
    logger.info("Processing speeds...")
    builder.process_speeds()
    
    logger.info("Calculating costs...")
    builder.calculate_costs()
    
    logger.info("Adding turn restrictions...")
    builder.add_turn_restrictions()
    
    logger.info("Building edge graph...")
    edge_graph_df = builder.build_edge_graph()
    
    logger.info("Adding H3 indexing...")
    builder.add_h3_indexing()
    
    logger.info("Creating shortcut table...")
    builder.create_shortcut_table(edge_graph_df)
    
    logger.info("Saving outputs (including edge indexing)...")
    builder.save_outputs(output_dir)
    
    logger.info("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert OSM data to road network files"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--output",
        help="Override output directory"
    )
    
    args = parser.parse_args()
    main(args.config, args.output)
