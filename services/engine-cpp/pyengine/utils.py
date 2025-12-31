import h3

def int_to_str(h3_int: int) -> str:
    return h3.int_to_str(h3_int)

def str_to_int(h3_str: str) -> int:
    return h3.str_to_int(h3_str)

def get_resolution(h3_int: int) -> int:
    if h3_int == 0: return -1
    return h3.get_resolution(int_to_str(h3_int))

def cell_to_parent(h3_int: int, res: int) -> int:
    if h3_int == 0: return 0
    return str_to_int(h3.cell_to_parent(int_to_str(h3_int), res))

def find_lca(cell1: int, cell2: int) -> int:
    """Find Lowest Common Ancestor between two H3 cells."""
    if cell1 == 0 or cell2 == 0:
        return 0
    
    cell1_str = int_to_str(cell1)
    cell2_str = int_to_str(cell2)
    
    res1 = h3.get_resolution(cell1_str)
    res2 = h3.get_resolution(cell2_str)
    lca_res = min(res1, res2)
    
    while lca_res >= 0:
        p1 = h3.cell_to_parent(cell1_str, lca_res)
        p2 = h3.cell_to_parent(cell2_str, lca_res)
        if p1 == p2:
            return str_to_int(p1)
        lca_res -= 1
    
    return 0
