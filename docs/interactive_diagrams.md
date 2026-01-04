---
layout: default
title: Interactive Diagrams
nav_order: 3
---

# Interactive Architecture Diagrams

Explore the H3 Routing Platform architecture interactively using the LikeC4 diagrams below.

**Available Views:**
- **System Context** - High-level platform overview with actors
- **Container Overview** - All services, tools, databases, and SDKs
- **Data Pipeline** - OSM to DuckDB to Shortcuts flow
- **Runtime Flow** - Request routing from UI to C++ engine
- **C++ Engine Internals** - ShortcutGraph, CSR, Query Algorithms
- **API Gateway Internals** - Dataset Registry, Route Handler
- **Shortcut Generator Phases** - 4-phase H3 hierarchy processor
- **duckOSM Processing Pipeline** - 9 processing components

<div style="border: 1px solid #30363d; border-radius: 6px; overflow: hidden; margin-top: 1rem;">
  <iframe 
    src="diagrams/" 
    style="width: 100%; height: 700px; border: none;"
    title="LikeC4 Architecture Diagrams">
  </iframe>
</div>

<p style="margin-top: 0.5rem; font-size: 0.875rem; color: #8b949e;">
  <a href="diagrams/" target="_blank">Open in full screen ↗</a>
</p>
