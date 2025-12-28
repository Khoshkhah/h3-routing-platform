
// ============================================================
// QUERY: UNIDIRECTIONAL PRUNED
// ============================================================

// State for unidirectional search: (edge_id, counter, used_minus1)
struct MinHeapState {
    double dist;
    uint64_t state; // packed state
    
    bool operator>(const MinHeapState& other) const {
        return dist > other.dist;
    }
};

CSRQueryResult CSRGraph::query_unidirectional(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    // Validate edges
    if (!is_valid_edge(source_edge)) return {-1, {}, false, "Source edge not found"};
    if (!is_valid_edge(target_edge)) return {-1, {}, false, "Target edge not found"};
    
    CSRHighCell high = compute_high_cell(source_edge, target_edge);
    
    // Priority queue storing (dist, state)
    std::priority_queue<MinHeapState, std::vector<MinHeapState>, std::greater<MinHeapState>> pq;
    
    // Map: state -> dist
    std::unordered_map<uint64_t, double> dist_map;
    // Map: state -> parent_state (for path reconstruction)
    std::unordered_map<uint64_t, uint64_t> parent_map;
    
    // Initial state: (source_edge, 0, false)
    uint64_t start_state = (static_cast<uint64_t>(source_edge) << 4) | (0 << 1) | 0;
    
    dist_map[start_state] = 0.0;
    parent_map[start_state] = start_state; // root points to self
    pq.push({0.0, start_state});
    
    double best_dist = INF;
    uint64_t best_end_state = 0;
    bool found = false;
    
    while (!pq.empty()) {
        auto [d, curr_packed] = pq.top(); pq.pop();
        
        // Unpack state
        uint32_t u = static_cast<uint32_t>(curr_packed >> 4);
        uint32_t counter = static_cast<uint32_t>((curr_packed >> 1) & 0x7);
        bool used_minus1 = (curr_packed & 1) != 0;
        
        if (d > dist_map[curr_packed]) continue;
        if (d >= best_dist) continue;
        
        // Target check
        if (u == target_edge) {
            if (d < best_dist) {
                best_dist = d;
                best_end_state = curr_packed;
                found = true;
            }
            continue;
        }
        
        // Pruning logic - get u's resolution
        const auto* meta = get_edge_meta(u);
        int u_res = meta ? meta->lca_res : -1;
        
        // Explore neighbors
        auto [start, end] = get_fwd_range(u);
        for (uint32_t i = start; i < end; ++i) {
            const auto& sc = shortcuts_[i];
            
            // --- Pruning Rules (match Python prototype) ---
            bool can_use = false;
            uint32_t next_counter = counter;
            bool next_used_minus1 = used_minus1;
            
            if (u_res > high.res) {
                // High resolution (fine) -> Low resolution (coarse)
                // Logic: strict, must use inside=1 (climb up) 
                // UNLESS we already used a -1 (down) edge, effectively locking us in local search?
                // Wait, Python logic: 
                // if u_res > high_res:
                //    if inside == 1: allowed
                //    elif inside == -1 and not used_minus1: allowed, next_used_minus1 = True
                //    else: continue
                
                if (sc.inside == 1) {
                    can_use = true;
                } else if (sc.inside == -1) {
                    if (!used_minus1) {
                        can_use = true;
                        next_used_minus1 = true;
                    }
                }
            } else {
                // Low resolution (coarse) or equal
                // Logic:
                // if inside == -1: allowed
                // elif (inside == 0 or inside == -2):
                //     if counter < MAX_USES (2): allowed, next_counter++
                
                if (sc.inside == -1) {
                    can_use = true;
                } else if (sc.inside == 0 || sc.inside == -2) {
                    if (counter < 2) {
                        can_use = true;
                        next_counter++;
                    }
                }
            }
            
            if (!can_use) continue;
            
            // Relaxation
            double new_dist = d + sc.cost;
            uint64_t next_state = (static_cast<uint64_t>(sc.to) << 4) | (next_counter << 1) | (next_used_minus1 ? 1 : 0);
            
            auto it = dist_map.find(next_state);
            if (it == dist_map.end() || new_dist < it->second) {
                dist_map[next_state] = new_dist;
                parent_map[next_state] = curr_packed;
                pq.push({new_dist, next_state});
            }
        }
    }
    
    if (!found) {
        return {-1, {}, false, "No path found"};
    }
    
    // Reconstruct path
    std::vector<uint32_t> path;
    uint64_t curr = best_end_state;
    
    while (true) {
        uint32_t u = static_cast<uint32_t>(curr >> 4);
        path.push_back(u);
        
        auto it = parent_map.find(curr);
        if (it == parent_map.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    return {best_dist, path, true, ""};
}
