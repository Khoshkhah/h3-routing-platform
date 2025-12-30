"""
Core utility functions for H3 boundary tracing.
"""
import h3
from typing import Set, List, Dict, Optional

# Face mappings
# Organized by resolution parity (even/odd) and child position (1–6). Position 0 is center.

_boundary_face_mapping_hex: Dict[int, Dict[int, Dict[int, int]]] = {
    0: {  # Even resolutions
        0: {},
        1: {2: 3, 3: 1, 1: 1},
        2: {4: 6, 2: 2, 6: 2},
        3: {6: 2, 2: 3, 3: 3},
        4: {1: 5, 4: 4, 5: 4},
        5: {1: 5, 3: 1, 5: 5},
        6: {4: 6, 5: 4, 6: 6},
    },
    1: {  # Odd resolutions
        0: {},
        1: {3: 3, 1: 3, 5: 1},
        2: {2: 6, 6: 6, 3: 2},
        3: {2: 2, 1: 3, 3: 2},
        4: {4: 5, 5: 5, 6: 4},
        5: {1: 1, 4: 5, 5: 1},
        6: {4: 4, 2: 6, 6: 4},
    }
}

_reversed_boundary_face_mapping_hex: Dict[int, Dict[int, Dict[int, Set[int]]]] = {
    0: {  # Even resolutions
        1: {1: {1, 3}, 3: {2}},
        2: {2: {2, 6}, 6: {4}},
        3: {2: {6}, 3: {2, 3}},
        4: {4: {4, 5}, 5: {1}},
        5: {5: {1, 5}, 1: {3}},
        6: {4: {5}, 6: {4, 6}},
        0: {}
    },
    1: {  # Odd resolutions
        1: {3: {1, 3}, 1: {5}},
        2: {6: {2, 6}, 2: {3}},
        3: {2: {2, 3}, 3: {1}},
        4: {5: {4, 5}, 4: {6}},
        5: {1: {1, 5}, 5: {4}},
        6: {4: {4, 6}, 6: {2}},
        0: {}
    }
}

_boundary_face_mapping_pent: Dict[int, Dict[int, Dict[int, int]]] = {
    0: {  # Even resolutions
        0: {},
        1: {4: 5, 2: 1, 6: 1},
        2: {6: 1, 3: 2, 2: 2},
        3: {5: 2, 4: 2, 6: 4},
        4: {3: 2, 5: 4, 1: 2},
        5: {5: 3, 6: 5, 4: 5},
        6: {},
    },
    1: {  # Odd resolutions
        0: {},
        1: {2: 5, 6: 5, 3: 1},
        2: {3: 1, 2: 1, 1: 2},
        3: {1: 4, 4: 3, 5: 3},
        4: {1: 2, 5: 2, 4: 4},
        5: {2: 5, 4: 3, 6: 3},
        6: {},
    }
}

_reversed_boundary_face_mapping_pent: Dict[int, Dict[int, Dict[int, Set[int]]]] = {
    0: {  # Even resolutions
        1: {1: {2, 6}, 5: {4}},
        2: {1: {6}, 2: {2, 3}},
        3: {4: {1}, 3: {4, 5}},
        4: {4: {5}, 2: {1, 3}},
        5: {5: {4, 6}, 3: {5}},
        6: {},
        0: {},
    },
    1: {  # Odd resolutions
        1: {5: {2, 6}, 1: {3}},
        2: {2: {1}, 1: {2, 3}},
        3: {3: {6}, 4: {4, 5}},
        4: {4: {4}, 2: {1, 5}},
        5: {5: {2}, 3: {4, 6}},
        6: {},
        0: {},
    }
}


def trace_cell_to_ancestor_faces(
    h: str,  # H3 index (str)
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6},
    res_parent: Optional[int] = None
) -> Set[int]:
    """
    Traces which of the given `input_faces` the target H3 cell lies on for an ancestor
    cell at a coarser resolution.

    Args:
        h: Target H3 cell index (hex string).
        input_faces: Subset of face numbers {1–6} to trace upward.
        res_parent: Resolution of the ancestor cell. If None, defaults to immediate parent.

    Returns:
        Set of face numbers (1–6) that the target cell maps to at the ancestor's boundary.
        Returns empty set if no traceable boundary remains.

    Raises:
        ValueError: If `res_parent` is invalid.
    """
    h_res = h3.get_resolution(h)
    if res_parent is None:
        res_parent = h_res - 1

    if res_parent >= h_res:
        raise ValueError(f"res_parent ({res_parent}) must be less than cell resolution ({h_res}).")
    if res_parent < 0:
        raise ValueError("res_parent cannot be negative.")
    if not input_faces:
        return set()

    current_h = h
    for res in range(h_res, res_parent, -1):
        if h3.is_pentagon(current_h):
            return set()

        parity = res % 2
        # cell_to_child_pos returns 0-6. 0 is center.
        # Note: h3-py v4+ might have different API, assuming typical behavior or v3 compatibility.
        # But cell_to_child_pos is strict.
        child_pos = h3.cell_to_child_pos(current_h, res - 1)
        parent = h3.cell_to_parent(current_h, res - 1)
        parent_is_pent = h3.is_pentagon(parent)

        if child_pos == 0:
            return set()

        mapping_dict = _boundary_face_mapping_pent if parent_is_pent else _boundary_face_mapping_hex
        face_map = mapping_dict[parity].get(child_pos, {})
        
        mapped_faces = {face_map[f] for f in input_faces if f in face_map}

        if not mapped_faces:
            return set()

        input_faces = mapped_faces
        current_h = parent

    return input_faces


def trace_cell_to_parent_faces(
    h: str,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6},
) -> Set[int]:
    """
    Traces which boundary faces the target cell lies on with respect to its parent cell.
    """
    parent_res = h3.get_resolution(h) - 1
    return trace_cell_to_ancestor_faces(h, input_faces, res_parent=parent_res)


def cell_to_coarsest_ancestor_on_faces(
    h: str,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6},
) -> str:
    """
    Finds the coarsest ancestor (lowest resolution) such that the target cell `h`
    lies on at least one of the specified `input_faces`.
    """
    res = h3.get_resolution(h)
    current_h = h

    while res > 0:
        parent_res = res - 1
        boundary_faces = trace_cell_to_ancestor_faces(current_h, input_faces, res_parent=parent_res)
        
        if not boundary_faces:
            return current_h

        current_h = h3.cell_to_parent(current_h, parent_res)
        input_faces = boundary_faces
        res = parent_res

    return current_h


def children_on_boundary_faces(
    parent: str,
    target_res: int,
    input_faces: Set[int] = {1, 2, 3, 4, 5, 6},
) -> List[str]:
    """
    Returns all children of the given parent cell at `target_res` resolution
    that lie on the parent's specified boundary `input_faces`.
    """
    res_parent = h3.get_resolution(parent)
    if target_res < res_parent:
        raise ValueError("target_res must be greater than parent cell resolution.")

    def _children_by_face(current: str, res: int, faces: Set[int]) -> List[str]:
        if res == target_res:
            return [current]

        parity = (res + 1) % 2
        result = []
        is_pent = h3.is_pentagon(current)
        
        mapping_dict = _reversed_boundary_face_mapping_pent if is_pent else _reversed_boundary_face_mapping_hex
        reverse_mapping = mapping_dict[parity]

        for child in h3.cell_to_children(current, res + 1):
            child_pos = h3.cell_to_child_pos(child, res)

            # Get the child face if it matches input_faces via reverse mapping
            mapped_faces = set()
            # reverse_mapping[child_pos] is a dict {parent_face: {child_faces}}
            child_mapping = reverse_mapping.get(child_pos, {})
            
            for parent_face in faces:
                if parent_face in child_mapping:
                    mapped_faces.update(child_mapping[parent_face])

            if mapped_faces:
                result.extend(_children_by_face(child, res + 1, mapped_faces))
        return result

    return _children_by_face(parent, res_parent, input_faces)
