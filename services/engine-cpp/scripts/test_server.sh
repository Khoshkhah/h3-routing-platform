#!/bin/bash
# Test the routing server endpoints (full API compatibility)
set -e

cd "$(dirname "$0")/.."

PORT=${1:-8080}
BASE_URL="http://localhost:$PORT"

echo "=== Routing Server API Tests ==="
echo "Testing server at $BASE_URL"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ PASS${NC}: $1"; }
fail() { echo -e "${RED}✗ FAIL${NC}: $1"; exit 1; }
info() { echo -e "${YELLOW}→${NC} $1"; }

# Test 1: Health check (empty server)
echo "1. Health check (empty server)..."
RESP=$(curl -s $BASE_URL/health)
if echo "$RESP" | grep -q '"status":"healthy"'; then
    pass "Health check"
    info "Response: $RESP"
else
    fail "Health check: $RESP"
fi

# Test 2: Load dataset via API
echo ""
echo "2. Loading Somerset dataset..."
RESP=$(curl -s -X POST $BASE_URL/load_dataset -H "Content-Type: application/json" \
    -d '{
        "dataset": "somerset",
        "shortcuts_path": "/home/kaveh/projects/shortcuts-generation/output/Somerset_shortcuts",
        "edges_path": "/home/kaveh/projects/shortcuts-generation/data/Somerset_driving_simplified_edges_with_h3.csv"
    }')
if echo "$RESP" | grep -q '"success":true'; then
    pass "Dataset loaded"
else
    fail "Failed to load dataset: $RESP"
fi

# Test 3: Health check shows dataset
echo ""
echo "3. Health check (with dataset)..."
RESP=$(curl -s $BASE_URL/health)
if echo "$RESP" | grep -q '"somerset"'; then
    pass "Dataset 'somerset' in health response"
else
    fail "Dataset not in health: $RESP"
fi

# Test 4: Route by edge with GeoJSON
echo ""
echo "4. Route by edge (with GeoJSON)..."
RESP=$(curl -s -X POST $BASE_URL/route_by_edge -H "Content-Type: application/json" \
    -d '{"dataset": "somerset", "source_edge": 100, "target_edge": 200}')
if echo "$RESP" | grep -q '"success"' && echo "$RESP" | grep -q '"runtime_ms"'; then
    pass "Route by edge with timing"
    info "Distance: $(echo $RESP | grep -o '"distance":[0-9.]*' | head -1)"
    info "Runtime: $(echo $RESP | grep -o '"runtime_ms":[0-9.]*')"
else
    fail "Route by edge failed: $RESP"
fi

# Test 5: Route by coordinates (GET)
echo ""
echo "5. Route by coordinates (GET)..."
RESP=$(curl -s "$BASE_URL/route?dataset=somerset&source_lat=37.09&source_lon=-84.60&target_lat=37.10&target_lon=-84.59")
if echo "$RESP" | grep -q '"success"'; then
    pass "Route by coordinates (GET)"
    if echo "$RESP" | grep -q '"geojson"'; then
        info "GeoJSON included in response"
    fi
else
    fail "Route GET failed: $RESP"
fi

# Test 6: Find nearest edges
echo ""
echo "6. Find nearest edges..."
RESP=$(curl -s "$BASE_URL/nearest_edges?dataset=somerset&lat=37.09&lng=-84.60&max=3")
if echo "$RESP" | grep -q '"edges"'; then
    pass "Nearest edges"
    info "Response: $(echo $RESP | head -c 100)..."
else
    fail "Nearest edges failed: $RESP"
fi

# Test 7: Unload dataset
echo ""
echo "7. Unload dataset..."
RESP=$(curl -s -X POST $BASE_URL/unload_dataset -H "Content-Type: application/json" \
    -d '{"dataset": "somerset"}')
if echo "$RESP" | grep -q '"success":true'; then
    pass "Dataset unloaded"
else
    fail "Unload failed: $RESP"
fi

# Test 8: Route fails after unload
echo ""
echo "8. Route fails after unload..."
RESP=$(curl -s "$BASE_URL/route?dataset=somerset&source_lat=37.09&source_lon=-84.60&target_lat=37.10&target_lon=-84.59")
if echo "$RESP" | grep -q '"error"'; then
    pass "Route correctly fails without dataset"
else
    fail "Should fail: $RESP"
fi

echo ""
echo "=== All tests passed! ==="
