import h3

def get_lca_res(c1, c2):
    c1s, c2s = h3.int_to_str(c1), h3.int_to_str(c2)
    m = min(h3.get_resolution(c1s), h3.get_resolution(c2s))
    for r in range(m, -1, -1):
        if h3.cell_to_parent(c1s, r) == h3.cell_to_parent(c2s, r):
            return r
    return -1

def get_lca(c1, c2):
    c1s, c2s = h3.int_to_str(c1), h3.int_to_str(c2)
    m = min(h3.get_resolution(c1s), h3.get_resolution(c2s))
    for r in range(m, -1, -1):
        p1 = h3.cell_to_parent(c1s, r)
        p2 = h3.cell_to_parent(c2s, r)
        if p1 == p2:
            return h3.str_to_int(p1)
    return 0

# Edges
e23037 = {'from': 644733726844702085, 'to': 644733726844656345, 'lca': 9}
e2388 = {'from': 644733726844654150, 'to': 644733726844701849, 'lca': 9}
e23030 = {'from': 644733726844701849, 'to': 644733726844702085, 'lca': 12}

target_res = 15
target_cell = 644733726844702085

def check_shortcut(f_edge, t_edge, label):
    lca_res = max(f_edge['lca'], t_edge['lca'])
    inner_cell = get_lca(f_edge['to'], t_edge['from'])
    outer_cell = get_lca(f_edge['from'], t_edge['to'])
    
    inner_res = h3.get_resolution(h3.int_to_str(inner_cell))
    outer_res = h3.get_resolution(h3.int_to_str(outer_cell))
    
    print(f"\n--- {label} ---")
    print(f"LCA Res: {lca_res}")
    print(f"Inner: Cell={inner_cell}, Res={inner_res}")
    print(f"Outer: Cell={outer_cell}, Res={outer_res}")
    
    # Activation at Res 15
    inner_active = (lca_res <= target_res and inner_res >= target_res)
    outer_active = (lca_res <= target_res and outer_res >= target_res)
    
    if inner_active:
        cell_15 = h3.str_to_int(h3.cell_to_parent(h3.int_to_str(inner_cell), target_res))
        print(f"Active in Inner Cell at res 15: {cell_15} (Match target: {cell_15 == target_cell})")
    else:
        print("Not active in Inner Cell at res 15")
        
    if outer_active:
        cell_15 = h3.str_to_int(h3.cell_to_parent(h3.int_to_str(outer_cell), target_res))
        print(f"Active in Outer Cell at res 15: {cell_15} (Match target: {cell_15 == target_cell})")
    else:
        print("Not active in Outer Cell at res 15")

check_shortcut(e23037, e2388, "Segment 1: 23037 -> 2388")
check_shortcut(e2388, e23030, "Segment 2: 2388 -> 23030")
