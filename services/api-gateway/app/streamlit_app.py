import streamlit as st
import streamlit.components.v1 as components

# --- 1. SET PAGE CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    page_title="Live Drag Router", 
    initial_sidebar_state="collapsed"
)

# --- 2. AGGRESSIVE STREAMLIT CSS OVERRIDE (FIXES SCROLLING) ---
# This targets the outer Streamlit containers to force full screen and remove scrolling.
st.markdown("""
<style>
    /* Remove default Streamlit padding, margins, and headers */
    #MainMenu, header, footer { visibility: hidden; }
    .stApp { margin: 0; padding: 0; overflow: hidden; height: 100vh; width: 100vw; }
    .main { margin: 0; padding: 0; overflow: hidden; height: 100vh; width: 100vw; }
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100vw !important;
        height: 100vh !important;
    }
    /* Ensure the Streamlit component iframe and container fill everything */
    [data-testid="stVerticalBlock"] { height: 100vh; width: 100vw; overflow: hidden; }
    [data-testid="stVerticalBlockBorderWrapper"] { height: 100vh; width: 100vw; overflow: hidden; }
    iframe { height: 100vh !important; width: 100vw !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION: PUT YOUR API URL HERE ---
# Original FastAPI server
# API_URL = "http://192.168.1.152:8000/route"

# New routing-server-v2 (C++ server) - uncomment to test
# API_URL = "http://localhost:8080/route"

# Use routing-pipeline Python API (Gateway to C++ server)
API_URL = "http://localhost:8000/route"

# For testing: API_URL = "https://router.project-osrm.org/route/v1/driving" 

# --- 2b. CONFIG LOADING ---
import yaml
import json
import os
import requests
from pathlib import Path

# Removed @st.cache_data to allow dynamic updates from datasets.yaml
def load_config():
    # Resolve path relative to this script file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "config", "datasets.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

config_data = load_config()
datasets = config_data.get('datasets', [])
paths_config = config_data.get('paths', {})

# Auto-detect project root: .../services/api-gateway/app/streamlit_app.py -> 3 levels up -> project_root
# Assuming streamlit_app.py is in services/api-gateway/app/
project_root = Path(__file__).resolve().parents[3]

# Context for resolution
resolution_context = {"project_root": str(project_root)}

# 1. Resolve paths_config first
resolved_paths = {}
if paths_config:
    for key, value in paths_config.items():
        if isinstance(value, str):
            resolved_paths[key] = value.format(**resolution_context)
    # Update context with resolved paths
    resolution_context.update(resolved_paths)

script_dir = os.path.dirname(os.path.abspath(__file__))

def fetch_api_datasets():
    """Fetch enriched dataset metadata from the API."""
    try:
        resp = requests.get("http://localhost:8000/datasets", timeout=2)
        if resp.ok:
            return resp.json()
    except Exception as e:
        print(f"DEBUG: Could not fetch datasets from API: {e}")
    return []

api_datasets = fetch_api_datasets()
api_dataset_map = {ds['name']: ds for ds in api_datasets}

# Convert datasets list to a dict for easier access, and load boundaries
dataset_map = {}
for ds in datasets:
    name = ds['name']
    api_ds = api_dataset_map.get(name, {})
    
    # Heuristic for center if not provided anywhere
    default_center = [37.08, -84.61] # Somerset
    if "Burnaby" in name or "Vancouver" in name:
        default_center = [49.25, -123.00] 
    
    # Priority: 1. Local Config, 2. API Enriched, 3. Heuristic
    center = ds.get('center') or api_ds.get('center') or default_center
    zoom = ds.get('zoom') or api_ds.get('zoom') or 13
    boundary = api_ds.get('boundary') # Boundary usually comes from API enrichment (WKT/GeoJSON in DB)
    
    short_name = ds.get('short_name') or api_ds.get('short_name') or name
    description = ds.get('description') or api_ds.get('description') or name

    ds_entry = {
        'name': description,
        'short_name': short_name,
        'center': center,
        'zoom': zoom,
        'boundary': boundary
    }
    
    # Load boundary from local file if specified and not already provided by API
    if not ds_entry['boundary'] and 'boundary_path' in ds:
        raw_path = ds['boundary_path']
        if resolution_context:
            raw_path = raw_path.format(**resolution_context)
            
        boundary_path = raw_path
        if not os.path.isabs(boundary_path):
             boundary_path = os.path.join(os.path.dirname(script_dir), boundary_path)

        if os.path.exists(boundary_path):
            try:
                with open(boundary_path, 'r') as f:
                    ds_entry['boundary'] = json.load(f)
                print(f"DEBUG: Loaded local boundary for {name} from {boundary_path}")
            except Exception as e:
                print(f"ERROR: Failed to load local boundary {boundary_path}: {e}")
    
    # Use the EXACT name from config as key to match what we send to backend
    dataset_map[name] = ds_entry

# --- JAVASCRIPT & HTML APPLICATION ---
# The internal component CSS already forces 100vh/100vw, but is now enforced by the outer container.

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    
    <style>
        /* FULL SCREEN & NO SCROLLING inside iframe */
        html, body, #map-container {{ height: 100vh; width: 100vw; margin: 0; padding: 0; overflow: hidden; }}
        #map-wrapper {{ 
            position: absolute; top: 0; right: 0; bottom: 0; 
            left: 320px; /* Initial space for sidebar */
            transition: left 0.3s; 
            height: 100vh; /* Ensure map fills vertical space */
        }}
        #map {{ height: 100%; width: 100%; }}
        
        /* Remove focus outline from Leaflet paths when clicked */
        .leaflet-interactive:focus {{ outline: none !important; }}
        path.leaflet-interactive:focus {{ outline: none !important; }}
        svg path:focus {{ outline: none !important; }}

        /* OSRM Sidebar Style */
        .sidebar {{
            position: fixed; top: 0; left: 0;
            width: 320px; height: 100vh;
            background: white; z-index: 1000;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            display: flex; flex-direction: column;
            transition: transform 0.3s, opacity 0.3s;
        }}
        
        /* HIDDEN STATE */
        .sidebar.hidden {{ transform: translateX(-320px); opacity: 0; }}

        .header {{
            background: #2d3436; color: white; padding: 15px;
            font-weight: 700; display: flex; align-items: center; justify-content: space-between;
        }}
        
        /* Hide Button */
        .hide-btn {{
            background: none; border: none; color: white;
            font-size: 16px; cursor: pointer; padding: 0 5px;
            transition: color 0.2s;
        }}
        .hide-btn:hover {{ color: #ccc; }}
        
        /* Input & Results Styles */
        .inputs {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .input-row {{
            background: white; border: 1px solid #ccc; border-radius: 4px;
            padding: 8px; margin-bottom: 8px; display: flex; align-items: center;
            font-size: 13px; color: #555;
        }}
        .marker-icon {{ width: 16px; height: 16px; border-radius: 50%; margin-right: 10px; flex-shrink: 0; }}
        .marker-A {{ background-color: #2ecc71; }}
        .marker-B {{ background-color: #e74c3c; }}
        
        .results {{ padding: 20px; }}
        .stat-card {{
            border-left: 4px solid #2d3436; background: #fff;
            padding: 10px; border: 1px solid #eee; border-left-width: 4px;
        }}
        .stat-time {{ font-size: 24px; font-weight: bold; color: #333; }}
        .stat-dist {{ color: #777; font-size: 14px; }}
        .loader {{ color: #007bff; font-size: 12px; display: none; margin-top:5px; }}
        
        /* Custom Map Markers */
        .custom-div-icon {{
            width: 20px !important;
            height: 20px !important;
            border-radius: 50%;
            border: 2px solid white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .icon-a {{
            background-color: #2ecc71 !important;
            color: white;
        }}
        .icon-b {{
            background-color: #e74c3c !important;
            color: white;
        }}
        
        /* Unhide Button (When Sidebar is hidden) */
        .unhide-btn {{
            position: fixed; top: 10px; left: 10px;
            z-index: 1001; background: #2d3436; color: white;
            border: none; padding: 8px 12px; border-radius: 4px;
            cursor: pointer; display: none;
        }}
    </style>
</head>
<body>

    <button id="unhide-btn" class="unhide-btn" onclick="toggleSidebar()">▶ Show Directions</button>

    <div id="sidebar" class="sidebar">
        <div class="header">
            Drag Router
            <div style="display: flex; align-items: center;">
                <div id="loader" class="loader" style="margin-right: 10px;">Updating...</div>
                <button class="hide-btn" onclick="toggleSidebar()">&#9664;</button> </div>
        </div>
        <div class="inputs">
            <div style="padding: 10px; border-bottom: 1px solid #ddd;">
                <label style="font-size: 12px; color: #666; display: block; margin-bottom: 5px;">Search Mode</label>
                <select id="search-mode" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
                    <option value="pruned">Bidirectional Pruned (Res)</option>
                    <option value="classic">Bidirectional Classic</option>
                    <option value="unidirectional">Unidirectional Phase-Based</option>
                    <option value="bi_lca">Bidirectional Phase-Based (LCA)</option>
                    <option value="m2m">Many-to-Many (KNN)</option>
                    <option value="dijkstra">Dijkstra (Baseline)</option>
                    <option value="bidijkstra">Bi-Dijkstra (Baseline)</option>
                </select>
            </div>
            <!-- Radius Container Removed -->
            <div style="padding: 10px; border-bottom: 1px solid #ddd; display: none;" id="knn-container">
                <label style="font-size: 12px; color: #666; display: block; margin-bottom: 5px;">K (Number of Candidates)</label>
                <input type="number" id="num-candidates" value="5" min="1" max="20" step="1" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
            </div>
            <div style="padding: 10px; border-bottom: 1px solid #ddd;">
                <label style="font-size: 12px; color: #666; display: block; margin-bottom: 5px;">Dataset</label>
                <select id="dataset-selector" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
                    <option value="burnaby">Burnaby, Canada</option>
                    <option value="somerset">Somerset, UK</option>
                </select>
                
                <!-- NEW: Dynamic Loading Controls -->
                <div style="margin-top: 10px; font-size: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <span id="dataset-status-text" style="color: #999;">Status: ...</span>
                    <div>
                        <button id="btn-load" onclick="loadDataset()" style="background: #2ecc71; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; display: none;">Load</button>
                        <button id="btn-unload" onclick="unloadDataset()" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; display: none;">Unload</button>
                    </div>
                </div>
            </div>
            <div class="input-row">
                <div class="marker-icon marker-A"></div>
                <div id="coord-a">Drag marker A</div>
            </div>
            <div class="input-row">
                <div class="marker-icon marker-B"></div>
                <div id="coord-b">Drag marker B</div>
            </div>
            
            <div style="padding: 10px; border-top: 1px solid #ddd; margin-top: 10px;">
                <label style="font-size: 13px; color: #333; display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="show-debug-cells" checked style="margin-right: 8px;">
                    Show Debug Cells (H3)
                </label>
            </div>
            <div style="padding: 10px; border-top: 1px solid #ddd;">
                <label style="font-size: 13px; color: #333; display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="include-alternative" style="margin-right: 8px;">
                    Show Alternative Route
                </label>
            </div>
            <div style="padding: 10px; border-top: 1px solid #ddd;" id="penalty-container">
                <label style="font-size: 12px; color: #666; display: block; margin-bottom: 5px;">Penalty Factor: <span id="penalty-value">2.0</span></label>
                <input type="range" id="penalty-factor" min="1.1" max="5.0" step="0.1" value="2.0" style="width: 100%;">
            </div>
        </div>

        <div class="results" id="results-area">
            <div class="stat-card">
                <div class="stat-time" id="disp-time">0 min</div>
                <div class="stat-dist" id="disp-dist">0 km</div>
            </div>
            <div style="margin-top: 10px; font-size: 10px; color: #999;" id="debug-info">Ready</div>
        </div>
    </div>
    
    <!-- DEBUG: Output config to verify loading -->
    <div style="display:none;" id="debug-config">
    __JSON_CONFIG_PLACEHOLDER__
    </div>
    
    <div id="map-wrapper">
        <div id="map"></div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        // --- 0. CONFIGURATION & DROPDOWN ---
        const datasetConfig = __JSON_CONFIG_PLACEHOLDER__;
        var currentLoadedDatasets = []; // Track loaded status globally

        // HELPER: API URL - hardcoded for reliability
        function getApiBase() {{
            return "http://localhost:8000";
        }}

        const selector = document.getElementById('dataset-selector');
        selector.innerHTML = ''; // Clear hardcoded options
        
        Object.keys(datasetConfig).forEach(key => {{
            const opt = document.createElement('option');
            opt.value = key; // The unique name key
            opt.textContent = datasetConfig[key].short_name || key; // Use short name
            selector.appendChild(opt);
        }});

        // --- DOM ELEMENTS ---
        const sidebar = document.getElementById('sidebar');
        const mapWrapper = document.getElementById('map-wrapper');
        const unhideBtn = document.getElementById('unhide-btn');
        const loader = document.getElementById('loader');

        // --- TOGGLE LOGIC ---
        function toggleSidebar() {{
            const isHidden = sidebar.classList.toggle('hidden');
            if (isHidden) {{
                mapWrapper.style.left = '0'; // Map takes full width
                unhideBtn.style.display = 'block';
            }} else {{
                mapWrapper.style.left = '320px'; // Map respects sidebar width
                unhideBtn.style.display = 'none';
            }}
            // Must invalidate size to redraw the map layers correctly after map size changes
            setTimeout(() => {{ map.invalidateSize(); }}, 300); 
        }}

        // --- 1. SETUP MAP ---
        var map = L.map('map', {{ zoomControl: false }}).setView([49.23, -122.96], 13);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
        }}).addTo(map);

        // --- 2. MARKER SETUP ---
        var iconA = L.divIcon({{ className: 'custom-div-icon icon-a', html: '', iconSize: [20, 20], iconAnchor: [10, 10] }});
        var iconB = L.divIcon({{ className: 'custom-div-icon icon-b', html: '', iconSize: [20, 20], iconAnchor: [10, 10] }});

        var markerA = L.marker([49.23, -122.97], {{ icon: iconA, draggable: true }}).addTo(map);
        var markerB = L.marker([49.24, -122.95], {{ icon: iconB, draggable: true }}).addTo(map);
        
        var routeLayer = null;
        var altRouteLayer = null;
        var debugLayer = L.layerGroup().addTo(map);
        
        // --- 3. API FUNCTION ---
        async function fetchRoute(latA, lonA, latB, lonB) {{
            loader.style.display = 'block';
            
            // Get selected parameters
            const dataset = document.getElementById('dataset-selector').value;
            const searchModeRaw = document.getElementById('search-mode').value;
            
            let targetAlgo = searchModeRaw;
            let targetMode = (searchModeRaw === 'm2m') ? 'knn' : 'one_to_one';
            
            const searchRadius = 2000; // Hardcoded default
            const numCandidates = document.getElementById('num-candidates').value;
            const includeAlternative = document.getElementById('include-alternative').checked;
            const penaltyFactor = parseFloat(document.getElementById('penalty-factor').value);

            try {{
                // Determine API URL dynamically using helper
                const apiBase = getApiBase();
                
                let response;
                if (includeAlternative) {{
                    // Use POST to include alternative route
                    const url = `${{apiBase}}/route`;
                    console.log("Fetching route (POST with alternative) from:", url);
                    response = await fetch(url, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            dataset: dataset,
                            source_lat: latA,
                            source_lon: lonA,
                            target_lat: latB,
                            target_lon: lonB,
                            search_radius: searchRadius,
                            num_candidates: parseInt(numCandidates),
                            search_mode: targetMode,
                            algorithm: targetAlgo,
                            include_alternative: true,
                            penalty_factor: penaltyFactor
                        }})
                    }});
                }} else {{
                    // Use GET for standard routing
                    const params = new URLSearchParams({{
                        dataset: dataset,
                        source_lat: latA,
                        source_lon: lonA,
                        target_lat: latB,
                        target_lon: lonB,
                        search_radius: searchRadius,
                        num_candidates: numCandidates,
                        search_mode: targetMode,
                        algorithm: targetAlgo
                    }});
                    const url = `${{apiBase}}/route?${{params.toString()}}`;
                    console.log("Fetching route (GET) from:", url);
                    response = await fetch(url, {{
                        method: 'GET',
                        headers: {{ 'Content-Type': 'application/json' }}
                    }});
                }}
                const data = await response.json();

                console.log("API Response:", data);
                
                if (routeLayer) map.removeLayer(routeLayer);
                if (altRouteLayer) {{ map.removeLayer(altRouteLayer); altRouteLayer = null; }}
                debugLayer.clearLayers();

                var routeCoords = [];
                var dist = 0;
                var runtime = 0;

                // Parse routing-server-v2 response
                var routeCoords = [];
                var dist = 0;
                var runtime = 0;

                if (data.success) {{
                    // Python API returns flat structure: {{success: true, geojson: {{...}}, distance: ...}}
                    
                    // Extract GeoJSON coordinates
                    if (data.geojson) {{
                        const geojson = data.geojson;
                        
                        // Handle FeatureCollection
                        if (geojson.type === 'FeatureCollection' && geojson.features) {{
                            geojson.features.forEach(feature => {{
                                if (feature.geometry.type === 'LineString') {{
                                    feature.geometry.coordinates.forEach(coord => {{
                                        routeCoords.push([coord[1], coord[0]]);
                                    }});
                                }}
                            }});
                        }} 
                        // Handle single Feature (returned by routing-server)
                        else if (geojson.type === 'Feature' && geojson.geometry && geojson.geometry.type === 'LineString') {{
                            geojson.geometry.coordinates.forEach(coord => {{
                                routeCoords.push([coord[1], coord[0]]);
                            }});
                        }}
                    }}
                    
                    dist = data.distance || 0;
                    runtime = data.runtime_ms || 0;

                    // Render Debug Cells (Source/Target/High)
                    if (data.debug && data.debug.cells) {{
                        const cells = data.debug.cells;
                        
                        const addCell = (cellData, color, label) => {{
                            if (!cellData || !cellData.boundary) return;
                            // Boundary is [lon, lat], convert to [lat, lon]
                            const latlngs = cellData.boundary.map(c => [c[1], c[0]]);
                            L.polygon(latlngs, {{
                                color: color,
                                fillColor: color,
                                fillOpacity: 0.4,
                                weight: 3
                            }}).bindTooltip(label + " (Res " + cellData.res + ")").addTo(debugLayer);
                        }};

                        console.log("Debug Cells:", cells);
                        if (cells.source) addCell(cells.source, '#00ff00', "Source");
                        if (cells.target) addCell(cells.target, '#ff0000', "Target");
                        if (cells.high) addCell(cells.high, '#0000ff', "High Cell");
                        
                        document.getElementById("debug-info").innerHTML = 
                            "Route found.<br>" +
                            "Src: " + (cells.source ? "Found" : "Miss") + 
                            " | Tgt: " + (cells.target ? "Found" : "Miss") + 
                            " | High: " + (cells.high ? "Found" : "Miss");
                    }} else {{
                        console.warn("No debug.cells in response");
                        document.getElementById("debug-info").innerHTML = "Found path, but NO debug cells.";
                    }}
                }}
                
                if (routeCoords.length > 0) {{
                    routeLayer = L.polyline(routeCoords, {{
                        color: '#0066cc', 
                        weight: 5, 
                        opacity: 0.8
                    }}).addTo(map);
                }}
                
                // Render alternative route if present
                if (data.alternative_route && data.alternative_route.geojson) {{
                    const altGeojson = data.alternative_route.geojson;
                    var altCoords = [];
                    if (altGeojson.type === 'Feature' && altGeojson.geometry && altGeojson.geometry.type === 'LineString') {{
                        altGeojson.geometry.coordinates.forEach(coord => {{
                            altCoords.push([coord[1], coord[0]]);
                        }});
                    }}
                    if (altCoords.length > 0) {{
                        altRouteLayer = L.polyline(altCoords, {{
                            color: '#ff6600',
                            weight: 4,
                            opacity: 0.7,
                            dashArray: '10, 5'
                        }}).addTo(map);
                    }}
                }}
                
                if (data.success === false) {{
                    document.getElementById('disp-time').innerText = "No route";
                    document.getElementById('disp-dist').innerText = data.error || "Path not found";
                }} else {{
                    // Parse values handling both flat (Python) and nested (C++ Engine) formats
                    let routeData = data.route || data; // Use data.route if exists, else top-level
                    
                    var costSeconds = routeData.distance || 0;
                    var physicalMeters = routeData.distance_meters || 0;
                    var runtimeMs = routeData.runtime_ms || 0;

                    // Helper for time formatting
                    function formatTime(seconds) {{
                        var m = Math.floor(seconds / 60);
                        var s = Math.floor(seconds % 60);
                        return m + " min " + s + " sec";
                    }}

                    // Helper for distance formatting
                    function formatDist(meters) {{
                        return (meters > 1000) ? (meters/1000).toFixed(2) + ' km' : meters.toFixed(0) + ' m';
                    }}

                    // Display Cost as Time
                    document.getElementById('disp-time').innerText = formatTime(costSeconds);
                    
                    // Display Physical Distance
                    document.getElementById('disp-dist').innerText = formatDist(physicalMeters);
                    
                    // Detailed Timing Display
                    let timeText = runtimeMs.toFixed(2) + ' ms';
                    let breakdownHtml = "";
                    
                    if (data.timing_breakdown) {{
                        const tb = data.timing_breakdown;
                        breakdownHtml = `
                            <div style="font-size: 10px; color: #666; margin-top: 5px;">
                                <div>Runtime: ${{timeText}}</div>
                                <div>Find Nearest: ${{tb.find_nearest_us}} µs</div>
                                <div>CH Search: ${{tb.search_us}} µs</div>
                                <div>Path Expand: ${{tb.expand_us}} µs</div>
                                <div>GeoJSON: ${{tb.geojson_us}} µs</div>
                            </div>
                        `;
                    }} else {{
                         breakdownHtml = `<div style="font-size: 10px; color: #999; margin-top: 2px;">Algo: ${{timeText}}</div>`;
                    }}
                    
                    // Append Alternative Route Info if available
                    let altInfo = "";
                    if (data.alternative_route) {{
                        let altCost = data.alternative_route.distance || 0;
                        let altDist = data.alternative_route.distance_meters || 0;
                        altInfo = `<div style="margin-top: 8px; border-top: 1px dashed #ccc; padding-top: 4px;">
                                     <strong style="color: #ff6600;">Alternative:</strong><br>
                                     ${{formatTime(altCost)}}<br>
                                     <span style="font-size: 11px; color: #555;">${{formatDist(altDist)}}</span>
                                   </div>`;
                    }}
                    
                    document.getElementById('disp-time').innerHTML = formatTime(costSeconds) + 
                        breakdownHtml + altInfo;
                    
                    // DEBUG: Show info in UI
                    document.getElementById('debug-info').innerText = "Points: " + routeCoords.length + " | Cost: " + costSeconds.toFixed(1) + "s | Len: " + (physicalMeters/1000).toFixed(2) + "km";
                }}
            }} catch (e) {{
                console.error("Routing error:", e);
                document.getElementById('disp-time').innerText = "API Error";
                document.getElementById('disp-dist').innerText = "Check Console";
                document.getElementById('debug-info').innerText = "Error: " + e.message;
            }} finally {{
                loader.style.display = 'none';
            }}
        }}

        // --- 4. DRAG EVENT LISTENERS ---
        function onDragStart() {{
            // Remove the route immediately when dragging starts
            if (routeLayer) {{
                map.removeLayer(routeLayer);
                routeLayer = null;
            }}
            if (altRouteLayer) {{
                map.removeLayer(altRouteLayer);
                altRouteLayer = null;
            }}
        }}

        function onDrag() {{
            var posA = markerA.getLatLng();
            var posB = markerB.getLatLng();

            // Update Input Text
            document.getElementById('coord-a').innerText = posA.lat.toFixed(5) + ', ' + posA.lng.toFixed(5);
            document.getElementById('coord-b').innerText = posB.lat.toFixed(5) + ', ' + posB.lng.toFixed(5);

            // Fetch new route
            fetchRoute(posA.lat, posA.lng, posB.lat, posB.lng);
        }}

        markerA.on('dragstart', onDragStart);
        markerB.on('dragstart', onDragStart);
        markerA.on('dragend', onDrag);
        markerB.on('dragend', onDrag);

        // --- 5. DATASET CHANGE HANDLER ---
        document.getElementById('dataset-selector').addEventListener('change', function() {{
            const newDataset = this.value;
            const config = datasetConfig[newDataset];
            
            // Update map center and zoom
            map.setView(config.center, config.zoom);
            
            // Reset markers to dataset center
            markerA.setLatLng([config.center[0] - 0.01, config.center[1] - 0.01]);
            markerB.setLatLng([config.center[0] + 0.01, config.center[1] + 0.01]);
            
            // Update Loading Status UI
            checkServerStatus();
            
            // Recalculate route with new dataset only if loaded
            if (currentLoadedDatasets.includes(newDataset)) {{
                onDrag();
            }} else {{
                if (routeLayer) map.removeLayer(routeLayer);
                document.getElementById('disp-time').innerText = "Not Loaded";
                document.getElementById('disp-dist').innerText = "Load first";
            }}
            
            // Update Boundary Layer
            if (window.currentBoundaryLayer) {{
                map.removeLayer(window.currentBoundaryLayer);
                window.currentBoundaryLayer = null;
            }}
            
            console.log("Boundary data for", newDataset, ":", config.boundary ? "EXISTS" : "NULL");
            if (config.boundary) {{
                console.log("Adding boundary layer with", config.boundary.features ? config.boundary.features.length : 0, "features");
                window.currentBoundaryLayer = L.geoJSON(config.boundary, {{
                    style: function(feature) {{
                        return {{
                            color: "#3388ff",
                            weight: 2,
                            opacity: 0.6,
                            dashArray: '5, 5',
                            fillOpacity: 0.05
                        }};
                    }}
                }}).addTo(map);
            }}
        }});
        
        // --- 5b. DYNAMIC LOADING LOGIC ---
        var apiRetryCount = 0;
        var apiCheckInProgress = false;
        
        async function checkServerStatus() {{
            // Prevent overlapping checks during retry
            if (apiCheckInProgress) return;
            apiCheckInProgress = true;
            
            const dataset = document.getElementById('dataset-selector').value;
            const statusLabel = document.getElementById('dataset-status-text');
            const btnLoad = document.getElementById('btn-load');
            const btnUnload = document.getElementById('btn-unload');
            
            statusLabel.innerText = apiRetryCount > 0 ? "Starting..." : "Checking...";
            statusLabel.style.color = "#999";
            
            try {{
                const apiBase = getApiBase();
                const resp = await fetch(`${{apiBase}}/server-status`);
                const data = await resp.json();
                
                apiRetryCount = 0; // Reset on success
                apiCheckInProgress = false;
                
                if (data.status === 'healthy') {{
                    const loaded = data.datasets_loaded || [];
                    currentLoadedDatasets = loaded; // Update global
                    if (loaded.includes(dataset)) {{
                        statusLabel.innerText = "Loaded";
                        statusLabel.style.color = "#2ecc71";
                        btnLoad.style.display = 'none';
                        btnUnload.style.display = 'inline-block';
                    }} else {{
                        statusLabel.innerText = "Unloaded";
                        statusLabel.style.color = "#e74c3c";
                        btnLoad.style.display = 'inline-block';
                        btnUnload.style.display = 'none';
                    }}
                }} else {{
                    statusLabel.innerText = "Server Error";
                    statusLabel.style.color = "red";
                    apiCheckInProgress = false;
                }}
            }} catch (e) {{
                apiRetryCount++;
                if (apiRetryCount < 10) {{  // Retry up to 10 times (20 seconds)
                    statusLabel.innerText = "Starting... (" + apiRetryCount + ")";
                    statusLabel.style.color = "#f39c12";
                    setTimeout(() => {{
                        apiCheckInProgress = false;
                        checkServerStatus();
                    }}, 2000);
                }} else {{
                    statusLabel.innerText = "API Offline";
                    statusLabel.style.color = "red";
                    apiRetryCount = 0;
                    apiCheckInProgress = false;
                }}
            }}
        }}

        async function loadDataset() {{
            const dataset = document.getElementById('dataset-selector').value;
            const statusLabel = document.getElementById('dataset-status-text');
            statusLabel.innerText = "Loading...";
            
            try {{
                const apiBase = getApiBase();
                
                const resp = await fetch(`${{apiBase}}/load-dataset`, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{dataset: dataset}})
                }});
                if (resp.ok) {{
                    checkServerStatus();
                    setTimeout(onDrag, 1000); // Trigger route calc
                }} else {{
                    alert("Failed to load dataset");
                    checkServerStatus();
                }}
            }} catch (e) {{
                alert("Error loading dataset: " + e.message);
            }}
        }}

        async function unloadDataset() {{
            const dataset = document.getElementById('dataset-selector').value;
            const statusLabel = document.getElementById('dataset-status-text');
            statusLabel.innerText = "Unloading...";
            
            try {{
                const apiBase = getApiBase();
                
                const resp = await fetch(`${{apiBase}}/unload-dataset`, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{dataset: dataset}})
                }});
                if (resp.ok) {{
                    checkServerStatus();
                    // Clear the map path
                    if (routeLayer) {{
                        map.removeLayer(routeLayer);
                        routeLayer = null;
                    }}
                    // Reset stats
                    document.getElementById('disp-time').innerText = "0 min";
                    document.getElementById('disp-dist').innerText = "0 km";
                    document.getElementById('debug-info').innerText = "Dataset unloaded";
                }} else {{
                    alert("Failed to unload dataset");
                    checkServerStatus();
                }}
            }} catch (e) {{
                alert("Error unloading dataset: " + e.message);
            }}
        }}

        // Add event listeners for load/unload buttons
        document.getElementById('btn-load').addEventListener('click', loadDataset);
        document.getElementById('btn-unload').addEventListener('click', unloadDataset);

        // Trigger change to load initial boundary and status
        document.getElementById('dataset-selector').dispatchEvent(new Event('change'));
        // Initial check too
        setTimeout(checkServerStatus, 500);

        // --- 6. SEARCH MODE CHANGE HANDLER ---
        document.getElementById('search-mode').addEventListener('change', function() {{
            const mode = this.value;
            const knnContainer = document.getElementById('knn-container');
            
            // Only show candidates for KNN mode (m2m)
            if (mode === 'm2m') {{
                knnContainer.style.display = 'block';
            }} else {{
                knnContainer.style.display = 'none';
            }}
            
            // Recalculate route with new search mode
            onDrag();
        }});

        // --- 7. PARAMETER CHANGE HANDLERS ---
        document.getElementById('num-candidates').addEventListener('change', onDrag);
        // Toggle Debug Cells
        document.getElementById('show-debug-cells').addEventListener('change', function() {{
            // Re-render debug layer visibility
            if (this.checked) {{
                map.addLayer(debugLayer);
            }} else {{
                map.removeLayer(debugLayer);
            }}
        }});
        // Toggle Alternative Route
        document.getElementById('include-alternative').addEventListener('change', onDrag);
        // Penalty Factor Slider
        document.getElementById('penalty-factor').addEventListener('input', function() {{
            document.getElementById('penalty-value').innerText = this.value;
        }});
        document.getElementById('penalty-factor').addEventListener('change', function() {{
            if (document.getElementById('include-alternative').checked) {{
                onDrag();
            }}
        }});

        // Initial Call
        // onDrag(); // Disabled to prevent auto-routing on load (avoids immediate crash if dataset large)

    </script>
</body>
</html>
"""

# Inject the component (removed height=900)
# We use max height/width properties on the containers instead.
import json
json_config_str = json.dumps(dataset_map)
components.html(html_code.replace("__JSON_CONFIG_PLACEHOLDER__", json_config_str), width=2000, height=9999, scrolling=False)