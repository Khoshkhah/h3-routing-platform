import h3_toolkit
import json
import h3

# Use the demo map center
lat = 37.773
lng = -122.418
origin_res = 7
intermediate_res = 10 

# Get the origin cell
origin = h3.latlng_to_cell(lat, lng, origin_res)

# Box 1: Original Cell Boundary
cell_boundary_gj = h3_toolkit.cell_boundary_to_geojson_cpp(origin)

# Box 2: Boundary Children
boundary_children = h3_toolkit.children_on_boundary_faces(origin, intermediate_res)
boundary_children_gj = {
    'type': 'FeatureCollection',
    'features': [h3_toolkit.cell_boundary_to_geojson_cpp(c) for c in boundary_children]
}

# Box 3: Merged Boundary
merged_boundary_gj = h3_toolkit.cell_boundary_from_children_cpp(origin, intermediate_res)

# Box 4: Buffered Accurate (Res 7 -> 10, convex=False, buffer=None i.e. auto)
buffered_accurate_gj = h3_toolkit.get_buffered_boundary_polygon_cpp(origin, intermediate_res, None, False)

# Box 5: Buffered Fast (Res 7 -> 10, convex=True, buffer=None i.e. auto)
buffered_fast_gj = h3_toolkit.get_buffered_boundary_polygon_cpp(origin, intermediate_res, None, True)

print("Writing to docs/demo_data.js...")
with open('docs/demo_data.js', 'w') as f:
    f.write('var cellBoundary = ' + json.dumps(cell_boundary_gj) + ';\n')
    f.write('var boundaryChildren = ' + json.dumps(boundary_children_gj) + ';\n')
    f.write('var mergedBoundary = ' + json.dumps(merged_boundary_gj) + ';\n')
    f.write('var bufferedAccurate = ' + json.dumps(buffered_accurate_gj) + ';\n')
    f.write('var bufferedFast = ' + json.dumps(buffered_fast_gj) + ';\n')
print("Done.")
