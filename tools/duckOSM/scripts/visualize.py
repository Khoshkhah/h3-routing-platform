import streamlit as st
import duckdb
import pydeck as pdk
import pandas as pd
from shapely import wkt
from shapely.geometry import LineString
from pathlib import Path
import time

# --- PAGE CONFIG ---
st.set_page_config(
    layout="wide", 
    page_title="duckOSM Viewer",
    page_icon="",
    initial_sidebar_state="expanded"
)

# --- CSS: TRUE MINIMALIST FULLSCREEN ---
st.markdown("""
    <style>
    /* Force 100% viewport height and hide everything extraneous */
    html, body, [data-testid="stApp"] {
        height: 100vh;
        overflow: hidden;
        background-color: #0e1117 !important;
    }
    
    [data-testid="stAppViewBlockContainer"] {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        height: 100vh !important;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    /* Fixed Sidebar styling - Dark Theme */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Hide menus, footer and padding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}

    /* Sidebar text visibility */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #c9d1d9 !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Dark mode selectbox */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        border-color: #30363d !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: MINIMAL & CLEAN ---
with st.sidebar:
    st.markdown("### duckOSM Explorer")
    
    # Search in multiple locations
    search_paths = [Path("data/output"), Path("../../data")]
    db_files = []
    for p in search_paths:
        if p.exists():
            db_files.extend(list(p.glob("*.duckdb")))
    
    if not db_files:
        st.error("No DuckDB files found.")
        st.stop()
        
    selected_db = st.selectbox("Database", options=db_files, format_func=lambda x: x.name)
    
    @st.cache_resource
    def get_con(path):
        c = duckdb.connect(str(path), read_only=True)
        c.execute("INSTALL spatial; LOAD spatial;")
        return c
    
    con = get_con(selected_db)
    
    # Discovery
    schemas = [r[0] for r in con.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'main', 'raw')").fetchall()]
    
    st.markdown("---")
    st.markdown("**Networks**")
    selected_modes = []
    
    # Define standard modes
    available_modes = ["driving", "walking", "cycling"]
    
    # Create checkboxes for each standard mode if they exist in schemas
    for mode in available_modes:
        if mode in schemas:
            if st.checkbox(mode.capitalize(), value=(mode == "driving")):
                selected_modes.append(mode)
    
    # Handle non-standard schemas
    for schema in schemas:
        if schema not in available_modes and schema != 'shortcuts':
            if st.checkbox(schema.capitalize(), value=False):
                selected_modes.append(schema)
    
    # Shortcut visualization toggle
    show_shortcuts = False
    if 'shortcuts' in schemas:
        st.markdown("---")
        st.markdown("**Hierarchy**")
        show_shortcuts = st.checkbox("Show Shortcuts", value=False)
    
    
    # Simple selection for Map Styles
    basemap_name = st.selectbox(
        "Style",
        options=["Dark Matter", "Light (Positron)", "Voyager"],
        index=0
    )

    st.markdown("---")
    st.markdown("**Performance**")
    edge_limit = st.slider("Max Edges", 5000, 500000, 50000, step=5000)
    use_offset = st.checkbox("Parallel Offset (Slow)", value=False)
    st.caption("Lower limit or disable offset if too slow")
    
    

    if selected_modes:
        st.markdown("---")
        # High contrast legend
        mode_colors_hex = {'driving': '#ff9f43', 'walking': '#54a0ff', 'cycling': '#1dd1a1'}
        for mode in selected_modes:
            color = mode_colors_hex.get(mode.lower(), '#c9d1d9')
            st.markdown(f'<div style="display: flex; align-items: center; margin-bottom:4px; font-size:0.85rem; color:#c9d1d9;"><div style="width: 12px; height: 12px; background-color: {color}; margin-right: 8px; border-radius: 50%;"></div>{mode.capitalize()}</div>', unsafe_allow_html=True)

# --- MAP STYLE & CACHE BUSTING ---
map_key = f"deck-{basemap_name}-{'-'.join(selected_modes)}"

style_urls = {
    "Dark Matter": "https://basemaps.cartocdn.com/gl/dark_matter-gl-style/style.json",
    "Light (Positron)": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Voyager": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
}
chosen_style = style_urls[basemap_name]

# Hardcoded constants
LINE_WIDTH = 4
# Removed EDGE_LIMIT as requested


# --- DATA LOADING ---
mtime = Path(__file__).stat().st_mtime

@st.cache_data(hash_funcs={duckdb.DuckDBPyConnection: id})
def fetch_network_data(db_path, mode, limit, offset_enabled, cache_key=mtime):
    # Discover available columns in the table
    try:
        cols_df = con.execute(f"DESCRIBE {mode}.edges").df()
        available_cols = set(cols_df['column_name'].tolist())
    except Exception as e:
        st.error(f"Error discovering columns for {mode}: {e}")
        return None

    # Define desired columns and their fallbacks
    select_fields = []
    
    # Priority columns for visualization - Use WKB for speed
    geom_type = cols_df[cols_df['column_name'] == 'geometry']['column_type'].iloc[0] if 'geometry' in available_cols else None
    
    if geom_type == 'GEOMETRY':

        select_fields.append("ST_AsWKB(geometry) as wkb_geom")
    elif geom_type == 'VARCHAR':
        select_fields.append("ST_AsWKB(ST_GeomFromText(geometry)) as wkb_geom")
    else:
        return None # Can't visualize without geometry
    
    
    if 'osm_id' in available_cols: select_fields.append("osm_id")
    elif 'id' in available_cols: select_fields.append("id as osm_id")
    else: select_fields.append("0 as osm_id")
    
    if 'name' in available_cols: select_fields.append("name")
    else: select_fields.append("'Unknown' as name")
    
    if 'highway' in available_cols: select_fields.append("highway")
    else: select_fields.append("'road' as highway")
    
    if 'is_reverse' in available_cols: select_fields.append("is_reverse")
    else: select_fields.append("false as is_reverse")
    
    if 'length_m' in available_cols: select_fields.append("round(length_m, 1) as length_m")
    elif 'length' in available_cols: select_fields.append("round(length, 1) as length_m")
    else: select_fields.append("0.0 as length_m")
    
    if 'maxspeed_kmh' in available_cols: select_fields.append("round(maxspeed_kmh, 1) as speed_kmh")
    elif 'cost' in available_cols: select_fields.append("round(cost, 1) as speed_kmh")
    else: select_fields.append("0.0 as speed_kmh")

    query = f"""
        SELECT 
            {', '.join(select_fields)}
        FROM {mode}.edges
        ORDER BY length_m DESC
        LIMIT {limit}
    """
    df = con.execute(query).df()
    if df.empty: return None
    
    # Fast WKB parsing using shapely.from_wkb
    import shapely
    
    # Pre-convert to bytes to avoid 'got int' errors with bytearray in shapely
    def parse_path(row):
        try:
            # Explicitly convert bytearray to bytes
            wkb_data = bytes(row['wkb_geom'])
            line = shapely.from_wkb(wkb_data)
            if offset_enabled and row['is_reverse']:
                line = line.parallel_offset(0.00003, 'right', join_style=2)
            return list(line.coords)
        except Exception as e:
            return []
            
    df['path'] = df.apply(parse_path, axis=1)
    df.drop(columns=['wkb_geom'], inplace=True)
    
    # Terminal logging for debug
    print(f"Loaded {len(df)} edges for {mode}")
    
    
    
    
    
    # Helper for Python-side parallel offset
    def parse_path_with_offset(row):
        try:
            line = wkt.loads(row['wkt_geom'])
            if row['is_reverse']:
                # Apply slight offset in Python for visibility
                line = line.parallel_offset(0.00003, 'right', join_style=2)
            return list(line.coords)
        except:
            # Fallback to simple parse if offset fails
            try:
                line = wkt.loads(row['wkt_geom'])
                return list(line.coords)
            except:
                return []
            
    df['path'] = df.apply(parse_path_with_offset, axis=1)
    
    mode_colors = {
        'driving': [255, 159, 67, 180],
        'walking': [84, 160, 255, 180],
        'cycling': [29, 209, 161, 180]
    }
    df['color'] = [mode_colors.get(mode.lower(), [201, 209, 217, 180])] * len(df)
    return df

@st.cache_data(hash_funcs={duckdb.DuckDBPyConnection: id})
def fetch_shortcut_data(db_path, cache_key=mtime):
    # Discover columns in shortcuts.edges
    try:
        cols_df = con.execute("DESCRIBE shortcuts.edges").df()
        available_cols = set(cols_df['column_name'].tolist())
    except Exception as e:
        return None

    # Fetch shortcuts and their corresponding edge geometries
    select_fields = ["s.from_edge", "s.to_edge", "s.cost"]
    
    geom_type = cols_df[cols_df['column_name'] == 'geometry']['column_type'].iloc[0] if 'geometry' in available_cols else None
    
    if geom_type == 'GEOMETRY':

        select_fields.append("ST_AsWKB(e.geometry) as wkb_geom")
    elif geom_type == 'VARCHAR':
         # Use ST_GeomFromText for WKT columns
        select_fields.append("ST_AsWKB(ST_GeomFromText(e.geometry)) as wkb_geom")
    else:
        return None
    
    
    if 'length' in available_cols: select_fields.append("round(e.length, 1) as length_m")
    elif 'length_m' in available_cols: select_fields.append("round(e.length_m, 1) as length_m")
    else: select_fields.append("0.0 as length_m")

    query = f"""
        SELECT 
            {', '.join(select_fields)}
        FROM shortcuts.shortcuts s
        JOIN shortcuts.edges e ON s.from_edge = e.id
        LIMIT 50000 
    """
    df = con.execute(query).df()
    if df.empty: return None

    import shapely
    def parse_path(wkb):
        try:
            # Explicitly convert bytearray to bytes
            wkb_data = bytes(wkb)
            line = shapely.from_wkb(wkb_data)
            return list(line.coords)
        except Exception as e:
            return []
            
    df['path'] = df['wkb_geom'].apply(parse_path)
    df.drop(columns=['wkb_geom'], inplace=True)
    
    # Terminal logging for debug
    print(f"Loaded {len(df)} shortcuts")
    
    df['color'] = [[255, 0, 255, 120]] * len(df) # Magenta for shortcuts
    return df



all_layers = []
for mode in selected_modes:
    df = fetch_network_data(selected_db, mode, edge_limit, use_offset, cache_key=mtime)



    if df is not None:
        all_layers.append(pdk.Layer(
            "PathLayer",
            df,
            pickable=True,
            get_path="path",
            get_color="color",
            get_width=LINE_WIDTH,
            width_min_pixels=1,
            auto_highlight=True
        ))

if show_shortcuts:
    sdf = fetch_shortcut_data(selected_db, cache_key=mtime)

    if sdf is not None:
        all_layers.append(pdk.Layer(
            "PathLayer",
            sdf,
            pickable=True,
            get_path="path",
            get_color="color",
            get_width=2,
            width_min_pixels=1,
            auto_highlight=True
        ))


# --- RENDERING ---
if all_layers:
    # Centering on data using main.visualization if available
    try:
        meta = con.execute("SELECT center_lat, center_lon, initial_zoom FROM main.visualization").fetchone()
        if meta:
            lat, lon, zoom = meta
        else:
            first_mode = selected_modes[0]
            first_df = fetch_network_data(selected_db, first_mode, edge_limit, use_offset, cache_key=mtime)
            if first_df is not None and not first_df.empty and len(first_df['path']) > 0:


                first_path = list(first_df['path'])[0]
                lat, lon, zoom = first_path[0][1], first_path[0][0], 13
            else:
                lat, lon, zoom = 49.2827, -123.1207, 12 # Vancouver fallback
    except:
        lat, lon, zoom = 49.2827, -123.1207, 12 # Vancouver fallback
    
    
    view_state = pdk.ViewState(
        longitude=lon,
        latitude=lat,
        zoom=zoom,
        pitch=0
    )

    placeholder = st.empty()
    with placeholder:
        st.pydeck_chart(pdk.Deck(
            map_style=chosen_style,
            initial_view_state=view_state,
            layers=all_layers,
            height=1000, 
            tooltip={
                "html": "<b>{highway}</b>: {name}<br/>OSM ID: {osm_id}<br/>{speed_kmh} km/h | {length_m}m",
                "style": {"backgroundColor": "#161b22", "color": "#c9d1d9"}
            }
        ), key=map_key)
else:
    st.info(" Select networks in the sidebar to visualize.")
