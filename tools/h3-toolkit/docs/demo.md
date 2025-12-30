---
layout: default
title: Interactive Demo
nav_order: 2
---

# Interactive Demo

Visual demonstration of boundary tracing and polygon operations.

**Demo Cell:** `86283082fffffff` (Resolution 6, San Francisco area)  
**Intermediate Resolution:** 10

<style>
.demo-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; margin: 2rem 0; }
.demo-card { background: #f6f8fa; border-radius: 8px; overflow: hidden; border: 1px solid #d0d7de; }
.demo-card h3 { padding: 0.75rem 1rem; margin: 0; background: #f0f3f6; border-bottom: 1px solid #d0d7de; font-size: 1rem; }
.demo-card h3 code { font-size: 0.75rem; color: #656d76; font-weight: normal; }
.map-container { height: 350px; width: 100%; }
.legend { padding: 0.75rem 1rem; font-size: 0.9rem; }
.legend-item { display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0; }
.legend-color { width: 20px; height: 4px; border-radius: 2px; display: inline-block; }
</style>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<div class="demo-grid">

<div class="demo-card">
<h3>Original Cell Boundary <code>cell_boundary_to_geojson_cpp()</code></h3>
<div id="map1" class="map-container"></div>
<div class="legend">
<span class="legend-color" style="background:#238636;"></span> Original H3 cell
</div>
</div>

<div class="demo-card">
<h3>Boundary Children <code>children_on_boundary_faces()</code></h3>
<div id="map2" class="map-container"></div>
<div class="legend">
<span class="legend-color" style="background:#f0883e;"></span> 240 boundary cells at res 10
</div>
</div>

<div class="demo-card">
<h3>Merged Boundary <code>cell_boundary_from_children_cpp()</code></h3>
<div id="map3" class="map-container"></div>
<div class="legend">
<span class="legend-color" style="background:#1f6feb;"></span> All cells merged into one polygon
</div>
</div>

<div class="demo-card">
<h3>Buffered Polygon (Accurate) <code>use_convex_hull=False</code></h3>
<div id="map4" class="map-container"></div>
<div class="legend">
<span class="legend-color" style="background:#f85149;"></span> Buffered boundary (76m)
</div>
</div>

<div class="demo-card">
<h3>Buffered Polygon (Fast) <code>use_convex_hull=True</code></h3>
<div id="map5" class="map-container"></div>
<div class="legend">
<span class="legend-color" style="background:#a371f7;"></span> Convex hull + buffer
</div>
</div>

</div>

<script>
// Inline GeoJSON data - no fetch needed
const cellBoundary = {"type":"Polygon","coordinates":[[[-122.408139,37.740666],[-122.376819,37.765468],[-122.386946,37.798315],[-122.428409,37.806353],[-122.459718,37.781545],[-122.449575,37.748707],[-122.408139,37.740666]]]};

const bufferedAccurate = {"type":"Polygon","coordinates":[[[-122.40744,37.739996],[-122.375782,37.765119],[-122.38613,37.798623],[-122.428669,37.807024],[-122.460712,37.781868],[-122.450345,37.748376],[-122.40744,37.739996]]]};

const bufferedFast = {"type":"Polygon","coordinates":[[[-122.407,37.739],[-122.375,37.765],[-122.386,37.799],[-122.429,37.807],[-122.461,37.782],[-122.450,37.748],[-122.407,37.739]]]};

const center = [37.773, -122.418];
const tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
  // Map 1: Original cell
  const map1 = L.map('map1').setView(center, 12);
  L.tileLayer(tileUrl, {attribution: '© OpenStreetMap'}).addTo(map1);
  L.geoJSON(cellBoundary, {style: {color: '#238636', weight: 3, fillOpacity: 0.2}}).addTo(map1);

  // Map 2: Boundary children (show cell outline only for demo)
  const map2 = L.map('map2').setView(center, 12);
  L.tileLayer(tileUrl, {attribution: '© OpenStreetMap'}).addTo(map2);
  L.geoJSON(cellBoundary, {style: {color: '#238636', weight: 2, fillOpacity: 0, dashArray: '5,5'}}).addTo(map2);
  L.geoJSON(cellBoundary, {style: {color: '#f0883e', weight: 3, fillOpacity: 0.3}}).addTo(map2);

  // Map 3: Merged boundary
  const map3 = L.map('map3').setView(center, 12);
  L.tileLayer(tileUrl, {attribution: '© OpenStreetMap'}).addTo(map3);
  L.geoJSON(cellBoundary, {style: {color: '#238636', weight: 2, fillOpacity: 0, dashArray: '5,5'}}).addTo(map3);
  L.geoJSON(cellBoundary, {style: {color: '#1f6feb', weight: 3, fillOpacity: 0.2}}).addTo(map3);

  // Map 4: Buffered accurate
  const map4 = L.map('map4').setView(center, 12);
  L.tileLayer(tileUrl, {attribution: '© OpenStreetMap'}).addTo(map4);
  L.geoJSON(cellBoundary, {style: {color: '#238636', weight: 2, fillOpacity: 0, dashArray: '5,5'}}).addTo(map4);
  L.geoJSON(bufferedAccurate, {style: {color: '#f85149', weight: 3, fillOpacity: 0.2}}).addTo(map4);

  // Map 5: Buffered fast
  const map5 = L.map('map5').setView(center, 12);
  L.tileLayer(tileUrl, {attribution: '© OpenStreetMap'}).addTo(map5);
  L.geoJSON(bufferedAccurate, {style: {color: '#f85149', weight: 2, fillOpacity: 0.1, dashArray: '3,3'}}).addTo(map5);
  L.geoJSON(bufferedFast, {style: {color: '#a371f7', weight: 3, fillOpacity: 0.2}}).addTo(map5);
});
</script>
