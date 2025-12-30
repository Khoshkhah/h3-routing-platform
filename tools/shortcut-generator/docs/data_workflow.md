# Shortcut Generator: Memory vs Storage Workflow

## Legend
- 🧠 = In RAM
- 💾 = DuckDB persistent/disk-backed
- 📁 = Parquet file

---

## Data Types

| Type | Description |
|------|-------------|
| **Shortcuts** | from_edge, to_edge, cost, via_edge, cells... |
| **Edges** | id, from_cell, to_cell, lca_res... (~900K rows) |

---

## Table Lifecycle

### 🔶 forward_deactivated
| Phase | Action | Location |
|-------|--------|----------|
| Init | Create empty table | 💾 persistent DB |
| Phase 1 | Insert deactivated shortcuts from workers | 💾 grows |
| Phase 2 | Insert remaining active shortcuts | 💾 grows |
| Phase 2 End | Export to Parquet (for checkpoint/resume) | 📁 |
| Phase 3 Start | **Instant RENAME to cell_0** (Zero RAM/IO) | 💾 RENAME |
| Phase 3 Start (Resume) | **Materialize from Parquet** (only if missing from DB) | 💾 load from 📁 |

### 🔷 backward_deactivated
| Phase | Action | Location |
|-------|--------|----------|
| Init | Create empty table | 💾 persistent DB |
| Phase 3 | Insert completed shortcuts | 💾 grows |
| Phase 4 | Worker Parquet results inserted | 💾 grows |
| Finalize | Deduplicate → shortcuts table | 💾 final output |

---

## SP Methods (Hybrid)

| Method | When | Shortcuts | Edges |
|--------|------|-----------|-------|
| PURE | res ≥ 10 | 💾 DuckDB | 💾 DuckDB |
| SCIPY Batched | res < 10 | 🧠 one cell | 💾 DuckDB |

**Batched SCIPY Process:**
```
for cell in cells:
    cell_df = query(current_cell = {cell})  # 🧠 one cell in RAM
    processed = scipy(cell_df)
    insert(processed)
    del cell_df  # memory cleanup
dedup(all result)
```

---

## Phase-by-Phase Memory Strategy

### Phase 1 & 2
- **Horizontal Scale**: Parquet chunks for Phase 1.
- **Vertical Scale**: Phase 2 uses disk-backed DuckDB for merging.

### Phase 3: Backward (0 → partition_res)
- **Centralized**: All data in `cell_0` (💾).
- **Handoff**: Zero-cost RENAME from Phase 2.
- **Batched SCIPY**: Iterates through resolution-N cells sequentially (🧠).

### Phase 4: Backward (partition_res → 15)

**Workers use disk-backed DuckDB with Streaming VIEWs**

| Data | Step | Location |
|------|------|----------|
| Shortcuts | **CREATE VIEW** | VIEW → 📁 (**Zero initialization RAM**) |
| Edges | **Filtered** load | 💾 materialize small subset (~50K) |
| Iteration | Materialize subset | 💾 Keep surviving shortcuts in 💾 table |
| SP | **Batched SCIPY** | 🧠 Load only active sub-cell into RAM |
| Results | Write | 📁 → 💾 🔷 backward_deactivated |

---

## Memory Bottlenecks Fixed ✅

| Issue | Fix |
|-------|-----|
| Phase 2-3 Handoff | **Zero-cost RENAME** instead of reload |
| SCIPY loads all | Batched per-cell |
| Phase 4 edges | Filtered to cell's edges |
| Phase 4 shortcuts | VIEW-based streaming (Zero RAM init) |
| Phase 4 memory | Disk-backed DuckDB per worker |
