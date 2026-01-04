---
layout: default
title: Interactive Diagrams
nav_order: 3
---

# Interactive Architecture Diagrams

Explore the H3 Routing Platform architecture interactively using the LikeC4 diagrams below.

> **Note**: The diagrams use LikeC4's built-in viewer with its own styling. Click "Open in full screen" for the best experience.

**Available Views (9 total):**

| View | Description |
|------|-------------|
| System Context | High-level platform overview with actors |
| Container Overview | All containers, databases, and SDKs |
| Data Pipeline | OSM → duckOSM → DuckDB → Shortcuts flow |
| Runtime Flow | Request routing from UI to C++ engine |
| C++ Engine Internals | ShortcutGraph, CSR, Query Algorithms |
| API Gateway Internals | Dataset Registry, Coord Translator, Route Handler |
| Shortcut Generator | 9-component dataflow with 4 phases |
| duckOSM Pipeline | 9 processor components |
| Routing Sequence | Dynamic request/response flow |

<div style="background: #0d1117; border: 1px solid #30363d; border-radius: 6px; overflow: hidden; margin-top: 1rem; padding: 2px;">
  <iframe 
    src="diagrams/" 
    style="width: 100%; height: 750px; border: none; border-radius: 4px;"
    title="LikeC4 Architecture Diagrams">
  </iframe>
</div>

<p style="margin-top: 0.5rem; font-size: 0.875rem; color: #8b949e;">
  <a href="diagrams/" target="_blank">🔗 Open in full screen ↗</a> &nbsp;|&nbsp;
  <a href="architecture_overview">📖 Read architecture docs</a>
</p>
