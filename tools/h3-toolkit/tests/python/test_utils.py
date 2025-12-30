import pytest
import h3
from h3_toolkit.utils import (
    trace_cell_to_ancestor_faces,
    trace_cell_to_parent_faces,
    cell_to_coarsest_ancestor_on_faces
)
from h3_toolkit.geom import (
    cell_boundary_to_geojson,
    get_boundary_cells
)

# Example H3 index for resolution 6
H3_CELL = h3.latlng_to_cell(37.775938728915946, -122.41795063018799, 6)

@pytest.mark.parametrize("input_faces", [
    {1}, {2, 3}, {4, 5, 6}, {1, 2, 3, 4, 5, 6}
])
def test_trace_cell_to_parent_faces_returns_subset(input_faces):
    result = trace_cell_to_parent_faces(H3_CELL, input_faces)
    assert isinstance(result, set)
    assert result.issubset({1, 2, 3, 4, 5, 6})


def test_trace_cell_to_ancestor_faces_valid():
    parent_res = h3.get_resolution(H3_CELL) - 2
    result = trace_cell_to_ancestor_faces(H3_CELL, {1, 2}, parent_res)
    assert isinstance(result, set)
    assert all(f in {1, 2, 3, 4, 5, 6} for f in result)


def test_trace_cell_to_ancestor_faces_invalid_resolution():
    with pytest.raises(ValueError):
        trace_cell_to_ancestor_faces(H3_CELL, {1}, res_parent=10)


def test_cell_to_coarsest_ancestor_on_faces_returns_ancestor():
    ancestor = cell_to_coarsest_ancestor_on_faces(H3_CELL, {1, 2, 3})
    assert isinstance(ancestor, str)
    assert h3.get_resolution(ancestor) <= h3.get_resolution(H3_CELL)


def test_geojson_conversion():
    feature = cell_boundary_to_geojson(H3_CELL)
    assert feature['type'] == 'Feature'
    assert feature['geometry']['type'] == 'Polygon'
    assert feature['properties']['h3_index'] == H3_CELL
