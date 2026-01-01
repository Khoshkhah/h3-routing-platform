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
    
    db_files = list(Path("data/output").glob("*.duckdb"))
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
        if schema not in available_modes:
            if st.checkbox(schema.capitalize(), value=False):
                selected_modes.append(schema)
    
    # Simple selection for Map Styles
    basemap_name = st.selectbox(
        "Style",
        options=["Dark Matter", "Light (Positron)", "Voyager"],
        index=0
    )

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
LINE_WIDTH = 6
EDGE_LIMIT = 20000

# --- DATA LOADING ---
@st.cache_data
def fetch_network_data(db_path, mode):
    # Fetch data without ST_OffsetCurve to avoid version issues
    query = f"""
        SELECT 
            osm_id, name, highway, is_reverse,
            round(length_m, 1) as length_m, 
            round(maxspeed_kmh, 1) as speed_kmh,
            ST_AsText(geometry) as wkt_geom
        FROM {mode}.edges
        LIMIT {EDGE_LIMIT}
    """
    df = con.execute(query).df()
    if df.empty: return None
    
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

all_layers = []
for mode in selected_modes:
    df = fetch_network_data(selected_db, mode)
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

# --- RENDERING ---
if all_layers:
    # Centering on data
    first_mode = selected_modes[0]
    first_df = fetch_network_data(selected_db, first_mode)
    first_path = list(first_df['path'])[0]
    
    view_state = pdk.ViewState(
        longitude=first_path[0][0],
        latitude=first_path[0][1],
        zoom=13,
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
