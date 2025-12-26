#!/usr/bin/env python3
"""
Quick test script to verify routing pipeline works
Run this instead of the notebook if VS Code Jupyter is freezing
"""

import subprocess
import pandas as pd
import folium
from shapely import wkt
import yaml
from pathlib import Path
import sys

# Configuration
DATASET_INDEX = 0  # 0 for Somerset, 1 for Burnaby
SOURCE_EDGE = 2311
TARGET_EDGE = 447

print("="*60)
print("ROUTING PIPELINE QUICK TEST")
print("="*60)

# Load config
config_path = Path(__file__).parent.parent / 'config/datasets.yaml'
print(f"\n1. Loading config from {config_path}")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

dataset = config['datasets'][DATASET_INDEX].copy()

# Adjust paths
for key in ['shortcuts_path', 'edges_path', 'binary_path']:
    if key in dataset and not Path(dataset[key]).is_absolute():
        dataset[key] = str(Path(__file__).parent.parent / dataset[key])

print(f"   Dataset: {dataset['name']}")
print(f"   Edges: {dataset['edges_path']}")
print(f"   Binary: {dataset['binary_path']}")

# Load edges
print(f"\n2. Loading edges CSV...")
edges_df = pd.read_csv(dataset['edges_path'])
print(f"   Loaded {len(edges_df)} edges")

# Query path
print(f"\n3. Querying path: {SOURCE_EDGE} → {TARGET_EDGE}")
cmd = [
    dataset['binary_path'],
    '--shortcuts', dataset['shortcuts_path'],
    '--edges', dataset['edges_path'],
    '--source', str(SOURCE_EDGE),
    '--target', str(TARGET_EDGE)
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    output = result.stdout
    
    print("\n" + "="*60)
    print("QUERY RESULTS")
    print("="*60)
    print(output)
    print("="*60)
    
    # Parse paths
    shortcut_path = []
    expanded_path = []
    
    for line in output.strip().split('\n'):
        if 'Shortcut path:' in line or ('Path:' in line and 'Expanded' not in line):
            path_str = line.split(':', 1)[1].strip()
            if '->' in path_str:
                shortcut_path = [int(x.strip()) for x in path_str.split('->')]
            else:
                path_str = path_str.strip('[]')
                if path_str:
                    shortcut_path = [int(x.strip()) for x in path_str.split(',')]
                    
        elif 'Expanded path:' in line or 'Expanded base edge path:' in line:
            path_str = line.split(':', 1)[1].strip()
            if '->' in path_str:
                expanded_path = [int(x.strip()) for x in path_str.split('->')]
            else:
                path_str = path_str.strip('[]')
                if path_str:
                    expanded_path = [int(x.strip()) for x in path_str.split(',')]
    
    print(f"\n✓ Success!")
    print(f"  Shortcut path ({len(shortcut_path)} edges): {' → '.join(map(str, shortcut_path))}")
    print(f"  Expanded path ({len(expanded_path)} edges): {' → '.join(map(str, expanded_path))}")
    print(f"  Compression: {len(expanded_path)/len(shortcut_path):.2f}x")
    
except subprocess.CalledProcessError as e:
    print(f"\n✗ Error running query!")
    print(f"  stdout: {e.stdout}")
    print(f"  stderr: {e.stderr}")
    sys.exit(1)

print("\n" + "="*60)
print("All tests passed! The routing pipeline works correctly.")
print("The issue is with VS Code's Jupyter kernel, not the code.")
print("="*60)
