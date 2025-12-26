# SDK Manual

This guide documents the client libraries available for interacting with the **H3 Routing Platform**.

## Python SDK

The Python SDK provides a user-friendly wrapper around the HTTP API.

### Installation

During development, you can install it in editable mode:
```bash
pip install -e sdk/python
```

### Usage

```python
from h3_routing_client import RoutingClient

# Initialize client (default points to localhost:8082)
client = RoutingClient(base_url="http://localhost:8082")

# Check health
if client.health().get("status") == "ok":
    print("Engine is online!")

# Calculate a route
response = client.route(
    dataset="vancouver",
    start_lat=49.25, start_lng=-123.12,
    end_lat=49.28, end_lng=-123.11,
    mode="knn"  # or "one_to_one"
)

if response.success:
    print(f"Distance: {response.distance_meters} meters")
    print(f"Time: {response.runtime_ms} ms")
    print(f"Path nodes: {len(response.path)}")
else:
    print(f"Error: {response.error}")
```

### API Reference

#### `RoutingClient(base_url)`
*   `base_url`: URL of the C++ Routing Engine (default: `http://localhost:8082`)

#### `client.route(...)`
*   `dataset`: Name of the loaded dataset (e.g., "burnaby", "vancouver")
*   `start_lat`, `start_lng`: Origin coordinates
*   `end_lat`, `end_lng`: Destination coordinates
*   `mode`: Routing mode (`knn`, `one_to_one`, `one_to_one_v2`)
*   `num_candidates`: Number of nearest neighbors to check (default: 3)
*   `algorithm`: algo variant (default: "pruned")

---

## C++ SDK

The C++ SDK is a header-only library that uses `libcurl` to communicate with the engine.

### Integration

1.  Include `sdk/cpp` in your include path.
2.  Link against `libcurl`.

```cmake
include_directories(${CMAKE_SOURCE_DIR}/sdk/cpp)
target_link_libraries(my_app curl)
```

### Usage

```cpp
#include "routing_client.hpp"
#include <iostream>

int main() {
    routing::Client client("http://localhost:8082");

    routing::RouteRequest req;
    req.dataset = "vancouver";
    req.start_lat = 49.25;
    req.start_lng = -123.12;
    req.end_lat = 49.28;
    req.end_lng = -123.11;

    nlohmann::json response = client.route(req);

    if (response.contains("route")) {
        double dist = response["route"]["distance_meters"];
        std::cout << "Distance: " << dist << "m" << std::endl;
    } else {
        std::cerr << "Error: " << response["error"] << std::endl;
    }

    return 0;
}
```
