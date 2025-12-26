#!/usr/bin/env python3
"""
Small end-to-end check to validate the gateway API is reachable and returns expected JSON keys.

Usage: from the project root run:
  python3 -m pytest -q tests/test_api_end_to_end.py

This test expects a running API at http://localhost:8000.
"""
import requests


def test_route_endpoint_returns_json_and_success():
    url = "http://localhost:8000/route"
    params = {
        "dataset": "somerset",
        # These coordinates were used earlier when debugging and returned 200 OK from the API
        "source_lat": 51.5,
        "source_lon": -2.5,
        "target_lat": 51.6,
        "target_lon": -2.4,
    }

    r = requests.get(url, params=params, timeout=10)
    assert r.status_code == 200, f"API did not return 200 OK (got {r.status_code})"

    j = r.json()
    # Verify the response contains expected top-level keys
    assert isinstance(j, dict), "Response JSON not an object"
    assert "success" in j or "detail" in j or "geojson" in j, "Response does not contain expected keys"


if __name__ == "__main__":
    # Run locally without pytest for quick feedback
    try:
        test_route_endpoint_returns_json_and_success()
        print("OK — /route returned 200 and expected JSON keys")
    except AssertionError as e:
        print("FAILED:", e)
        raise
