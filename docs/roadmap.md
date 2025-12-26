# Routing Engine Roadmap

This document outlines suggested future improvements and feature additions for the routing engine.

---

## 1. Algorithmic Features

### Alternative Routes (k-Shortest Paths)
*   **Current State**: The engine returns only the single absolute best path.
*   **Goal**: Provide users with 2-3 meaningful route choices (e.g., "Fastest", "Shortest", "Scenic").
*   **Approach**: Implement "Penalty" or "Plateau" generation methods in the C++ engine to find paths that are geometrically distinct but similar in cost.

### Dynamic Traffic Weights
*   **Current State**: Edge costs are static (Length / Speed Limit).
*   **Goal**: Incorporate real-time traffic (rush hour delays).
*   **Approach**: Implement *Customizable Contraction Hierarchies (CCH)* or a hybrid approach where edge weights can be updated in-memory without re-contracting the whole graph.

### Map Matching (HMM)
*   **Current State**: Basic `nearest_edge` lookup.
*   **Goal**: Accurately snap noisy GPS traces to the road network.
*   **Approach**: Implement a Hidden Markov Model (HMM) matcher in C++ to reconstruct paths from raw GPS logs.

---

## 2. Infrastructure & DevEx

### Dockerization & Cloud Deployment
*   **Current State**: Manual script-based startup.
*   **Goal**: "One-click" deployment to AWS/GCP.
*   **Approach**: Create a multi-stage `Dockerfile` to compile the C++ server and minimized runtime container.

### Testing & Benchmarking
*   **Current State**: Basic unit tests.
*   **Goal**: Prevent performance regressions.
*   **Approach**: Add a `benchmark` suite that runs standard routing scenarios (random 10k queries) and tracks latency trends over time.

### Binary API (Protobuf / Flatbuffers)
*   **Current State**: JSON API (Bottle-neck for large payloads).
*   **Goal**: Ultra-low latency communication.
*   **Approach**: Replace internal JSON serialization with Flatbuffers or gRPC for Python<->C++ communication.
