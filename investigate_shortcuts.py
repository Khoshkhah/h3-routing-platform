"""
Investigate shortcut data for the U-turn bug.
Looking at edges: 1169, 2091, 1170, 2090
"""
import pyarrow.parquet as pq
import pandas as pd

SHORTCUTS_PATH = "/home/kaveh/projects/h3-routing-platform/tools/shortcut-generator/output/Somerset_shortcuts"

# Load shortcuts
print("Loading shortcuts...")
df = pq.read_table(SHORTCUTS_PATH).to_pandas()
print(f"Loaded {len(df):,} shortcuts\n")

edges_of_interest = [1169, 2091, 1170, 2090]

# Find all shortcuts involving these edges
print("=" * 60)
print("SHORTCUTS WHERE from_edge IN [1169, 2091, 1170, 2090]:")
print("=" * 60)
from_matches = df[df['from_edge'].isin(edges_of_interest)]
for _, row in from_matches.iterrows():
    print(f"  {row['from_edge']} -> {row['to_edge']}  via={row['via_edge']}  cost={row['cost']:.2f}  inside={row['inside']}")

print("\n" + "=" * 60)
print("SHORTCUTS WHERE to_edge IN [1169, 2091, 1170, 2090]:")
print("=" * 60)
to_matches = df[df['to_edge'].isin(edges_of_interest)]
for _, row in to_matches.iterrows():
    print(f"  {row['from_edge']} -> {row['to_edge']}  via={row['via_edge']}  cost={row['cost']:.2f}  inside={row['inside']}")

# Specific investigation: shortcuts from 1169
print("\n" + "=" * 60)
print("DETAILED: All shortcuts FROM edge 1169:")
print("=" * 60)
from_1169 = df[df['from_edge'] == 1169].sort_values('cost')
for _, row in from_1169.head(20).iterrows():
    print(f"  1169 -> {row['to_edge']:5}  via={row['via_edge']:5}  cost={row['cost']:8.2f}  inside={row['inside']:2}  cell={row['cell']}")

# Check: is there a direct shortcut 1169 -> 2090?
print("\n" + "=" * 60)
print("Direct shortcut 1169 -> 2090 (if exists):")
print("=" * 60)
direct = df[(df['from_edge'] == 1169) & (df['to_edge'] == 2090)]
if len(direct) > 0:
    for _, row in direct.iterrows():
        print(f"  1169 -> 2090  via={row['via_edge']}  cost={row['cost']:.2f}  inside={row['inside']}")
else:
    print("  NOT FOUND - No direct shortcut from 1169 to 2090")

# Check: shortcut 1169 -> 1170 (correct intermediate)
print("\n" + "=" * 60)
print("Shortcut 1169 -> 1170 (if exists):")
print("=" * 60)
sc_1169_1170 = df[(df['from_edge'] == 1169) & (df['to_edge'] == 1170)]
if len(sc_1169_1170) > 0:
    for _, row in sc_1169_1170.iterrows():
        print(f"  1169 -> 1170  via={row['via_edge']}  cost={row['cost']:.2f}  inside={row['inside']}")
else:
    print("  NOT FOUND")

# Check: shortcut 1169 -> 2091 (the bad one)
print("\n" + "=" * 60)
print("Shortcut 1169 -> 2091 (the PROBLEM one):")
print("=" * 60)
sc_1169_2091 = df[(df['from_edge'] == 1169) & (df['to_edge'] == 2091)]
if len(sc_1169_2091) > 0:
    for _, row in sc_1169_2091.iterrows():
        print(f"  1169 -> 2091  via={row['via_edge']}  cost={row['cost']:.2f}  inside={row['inside']}")
else:
    print("  NOT FOUND")

# Check: shortcut 2091 -> 1170
print("\n" + "=" * 60)
print("Shortcut 2091 -> 1170 (if exists):")
print("=" * 60)
sc_2091_1170 = df[(df['from_edge'] == 2091) & (df['to_edge'] == 1170)]
if len(sc_2091_1170) > 0:
    for _, row in sc_2091_1170.iterrows():
        print(f"  2091 -> 1170  via={row['via_edge']}  cost={row['cost']:.2f}  inside={row['inside']}")
else:
    print("  NOT FOUND")
