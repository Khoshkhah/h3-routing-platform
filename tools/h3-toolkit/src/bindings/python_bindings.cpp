#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "h3_toolkit.hpp"
#include <h3api.h>
#include <sstream>
#include <iomanip>

namespace py = pybind11;

// Helper: Convert H3Index to hex string (Python uses strings for H3)
std::string h3_to_string(H3Index h) {
    std::stringstream ss;
    ss << std::hex << h;
    return ss.str();
}

// Helper: Convert hex string to H3Index
H3Index string_to_h3(const std::string& s) {
    H3Index h;
    std::stringstream ss;
    ss << std::hex << s;
    ss >> h;
    return h;
}

// Wrapper for trace_cell_to_ancestor_faces
std::set<int> py_trace_cell_to_ancestor_faces(
    const std::string& h_str,
    const std::set<int>& input_faces,
    int res_parent
) {
    H3Index h = string_to_h3(h_str);
    return h3_toolkit::trace_cell_to_ancestor_faces(h, input_faces, res_parent);
}

// Wrapper for trace_cell_to_parent_faces
std::set<int> py_trace_cell_to_parent_faces(
    const std::string& h_str,
    const std::set<int>& input_faces
) {
    H3Index h = string_to_h3(h_str);
    return h3_toolkit::trace_cell_to_parent_faces(h, input_faces);
}

// Wrapper for children_on_boundary_faces
std::vector<std::string> py_children_on_boundary_faces(
    const std::string& parent_str,
    int target_res,
    const std::set<int>& input_faces
) {
    H3Index parent = string_to_h3(parent_str);
    auto children = h3_toolkit::children_on_boundary_faces(parent, target_res, input_faces);
    
    std::vector<std::string> result;
    result.reserve(children.size());
    for (H3Index child : children) {
        result.push_back(h3_to_string(child));
    }
    return result;
}

PYBIND11_MODULE(_h3_toolkit_cpp, m) {
    m.doc() = "H3-Toolkit C++ bindings for Python";
    
    m.def("trace_cell_to_ancestor_faces", &py_trace_cell_to_ancestor_faces,
          py::arg("h"), py::arg("input_faces"), py::arg("res_parent"),
          "Trace which faces of an ancestor cell a given cell lies on.");
    
    m.def("trace_cell_to_parent_faces", &py_trace_cell_to_parent_faces,
          py::arg("h"), py::arg("input_faces"),
          "Trace which faces of the parent cell a given cell lies on.");
    
    m.def("children_on_boundary_faces", &py_children_on_boundary_faces,
          py::arg("parent"), py::arg("target_res"),
          py::arg("input_faces") = std::set<int>{1, 2, 3, 4, 5, 6},
          "Returns all children at target_res that lie on parent's boundary faces.");
    
    m.def("cell_to_coarsest_ancestor_on_faces",
          [](const std::string& h_str, const std::set<int>& input_faces) {
              H3Index h = string_to_h3(h_str);
              H3Index result = h3_toolkit::cell_to_coarsest_ancestor_on_faces(h, input_faces);
              return h3_to_string(result);
          },
          py::arg("h"), py::arg("input_faces") = std::set<int>{1, 2, 3, 4, 5, 6},
          "Finds the coarsest ancestor where h still lies on specified faces.");
    
    m.def("cell_boundary",
          [](const std::string& cell_str) {
              H3Index cell = string_to_h3(cell_str);
              auto coords = h3_toolkit::cell_boundary(cell);
              py::list result;
              for (const auto& p : coords) {
                  result.append(py::make_tuple(p.first, p.second));
              }
              return result;
          },
          py::arg("cell"),
          "Returns cell boundary as list of (lon, lat) pairs.");
    
    m.def("cell_boundary_from_children",
          [](const std::string& parent_str, int target_res) {
              H3Index parent = string_to_h3(parent_str);
              auto coords = h3_toolkit::cell_boundary_from_children(parent, target_res);
              py::list result;
              for (const auto& p : coords) {
                  result.append(py::make_tuple(p.first, p.second));
              }
              return result;
          },
          py::arg("parent"), py::arg("target_res"),
          "Returns merged boundary polygon of all boundary children.");
    
    m.def("get_buffered_h3_polygon",
          [](const std::string& cell_str, double buffer_meters) {
              H3Index cell = string_to_h3(cell_str);
              auto coords = h3_toolkit::get_buffered_h3_polygon(cell, buffer_meters);
              py::list result;
              for (const auto& p : coords) {
                  result.append(py::make_tuple(p.first, p.second));
              }
              return result;
          },
          py::arg("cell"), py::arg("buffer_meters") = -1.0,
          "Returns buffered polygon of a single cell.");
    
    m.def("get_buffered_boundary_polygon", 
          [](const std::string& cell_str, int intermediate_res, double buffer_meters, bool use_convex_hull) {
              H3Index cell = string_to_h3(cell_str);
              auto coords = h3_toolkit::get_buffered_boundary_polygon(cell, intermediate_res, buffer_meters, use_convex_hull);
              // Return as list of [lon, lat] pairs
              py::list result;
              for (const auto& p : coords) {
                  result.append(py::make_tuple(p.first, p.second));
              }
              return result;
          },
          py::arg("cell"), py::arg("intermediate_res") = 10, py::arg("buffer_meters") = -1.0, py::arg("use_convex_hull") = true,
          "Returns a buffered polygon. use_convex_hull=True is fast, use_convex_hull=False is accurate.");
}
