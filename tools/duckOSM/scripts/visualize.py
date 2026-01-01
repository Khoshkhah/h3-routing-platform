import streamlit as st
import duckdb
import pydeck as pdk
import pandas as pd
from shapely import wkt
from pathlib import Path
import time
import shapely

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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### duckOSM Explorer")
    
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
    available_modes = ["driving", "walking", "cycling"]
    
    for mode in available_modes:
        if mode in schemas:
            if st.checkbox(mode.capitalize(), value=(mode == "driving")):
                selected_modes.append(mode)
    
    for schema in schemas:
        if schema not in available_modes and schema != 'shortcuts':
            if st.checkbox(schema.capitalize(), value=False):
                selected_modes.append(schema)
    
    show_shortcuts = False
    if 'shortcuts' in schemas:
        st.markdown("---")
        st.markdown("**Hierarchy**")
        show_shortcuts = st.checkbox("Show Shortcuts", value=False)
    
    basemap_name = st.selectbox("Style", options=["Dark Matter", "Light (Positron)", "Voyager"], index=0)

    st.markdown("---")
    st.markdown("**Performance**")
    edge_limit = st.slider("Max Edges", 5000, 500000, 50000, step=5000)
    use_offset = st.checkbox("Parallel Offset (Slow)", value=False)
    st.caption("Lower limit or disable offset if too slow")

    if selected_modes:
        st.markdown("---")
        mode_colors_hex = {'driving': '#ff9f43', 'walking': '#54a0ff', 'cycling': '#1dd1a1'}
        for mode in selected_modes:
            color = mode_colors_hex.get(mode.lower(), '#c9d1d9')
            st.markdown(f'<div style="display: flex; align-items: center; margin-bottom:4px; font-size:0.85rem; color:#c9d1d9;"><div style="width: 12px; height: 12px; background-color: {color}; margin-right: 8px; border-radius: 50%;"></div>{mode.capitalize()}</div>', unsafe_allow_html=True)

# --- MAP STYLE ---
style_urls = {
    "Dark Matter": "https://basemaps.cartocdn.com/gl/dark_matter-gl-style/style.json",
    "Light (Positron)": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Voyager": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
}
chosen_style = style_urls[basemap_name]
LINE_WIDTH = 4

# --- HELPER: DATA SANITIZATION ---
def sanitize_df(df):
    """Convert all numpy types to native Python types for JSON serialization."""
    for col in df.columns:
        if df[col].dtype == 'object':
            continue
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype(object).apply(lambda x: int(x) if pd.notnull(x) else None)
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(object).apply(lambda x: float(x) if pd.notnull(x) else None)
        elif pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].astype(object).apply(lambda x: bool(x) if pd.notnull(x) else None)
    return df

# --- DATA LOADING ---
mtime = Path(__file__).stat().st_mtime

@st.cache_data(hash_funcs={duckdb.DuckDBPyConnection: id})
def fetch_network_data(db_path, mode, limit, offset_enabled, cache_key=mtime):
    try:
        cols_df = con.execute(f"DESCRIBE {mode}.edges").df()
        available_cols = set(cols_df['column_name'].tolist())
    except Exception as e:
        return None

    select_fields = []
    
    # Use column_type instead of data_type to fix KeyError
    geom_type = cols_df[cols_df['column_name'] == 'geometry']['column_type'].iloc[0] if 'geometry' in available_cols else None
    
    if geom_type == 'GEOMETRY':
        select_fields.append("ST_AsWKB(geometry) as wkb_geom")
    elif geom_type == 'VARCHAR':
        select_fields.append("ST_AsWKB(ST_GeomFromText(geometry)) as wkb_geom")
    else:
        return None
    
    # Column mapping with fallbacks
    field_map = {
        'osm_id': ('osm_id', 'id', '0'),
        'name': ('name', '"Unknown"'),
        'highway': ('highway', '"road"'),
        'is_reverse': ('is_reverse', 'false'),
        'length_m': ('length_m', 'length', '0.0'),
        'maxspeed_kmh': ('maxspeed_kmh', 'cost', '0.0')
    }
    
    for target, candidates in field_map.items():
        found = False
        for c in candidates:
            if c.strip('"') in available_cols:
                if target in ('length_m', 'maxspeed_kmh'):
                    select_fields.append(f"round({c}, 1) as {target if target != 'maxspeed_kmh' else 'speed_kmh'}")
                else:
                    select_fields.append(f"{c} as {target}")
                found = True
                break
        if not found:
            select_fields.append(f"{candidates[-1]} as {target if target != 'maxspeed_kmh' else 'speed_kmh'}")

    query = f"SELECT {', '.join(select_fields)} FROM {mode}.edges ORDER BY length_m DESC LIMIT {limit}"
    df = con.execute(query).df()
    if df.empty: return None
    
    def parse_path(row):
        try:
            wkb_data = bytes(row['wkb_geom'])
            line = shapely.from_wkb(wkb_data)
            if offset_enabled and row['is_reverse']:
                line = line.parallel_offset(0.00003, 'right', join_style=2)
            return list(line.coords)
        except:
            return []
            
    df['path'] = df.apply(parse_path, axis=1)
    
    mode_colors = {'driving': [255, 159, 67, 180], 'walking': [84, 160, 255, 180], 'cycling': [29, 209, 161, 180]}
    df['color'] = [mode_colors.get(mode.lower(), [201, 209, 217, 180])] * len(df)
    
    return sanitize_df(df)

@st.cache_data(hash_funcs={duckdb.DuckDBPyConnection: id})
def fetch_shortcut_data(db_path, cache_key=mtime):
    try:
        cols_df = con.execute("DESCRIBE shortcuts.edges").df()
        available_cols = set(cols_df['column_name'].tolist())
    except:
        return None

    select_fields = ["s.from_edge", "s.to_edge", "s.cost"]
    geom_type = cols_df[cols_df['column_name'] == 'geometry']['column_type'].iloc[0] if 'geometry' in available_cols else None
    
    if geom_type == 'GEOMETRY':
        select_fields.append("ST_AsWKB(e.geometry) as wkb_geom")
    elif geom_type == 'VARCHAR':
        select_fields.append("ST_AsWKB(ST_GeomFromText(e.geometry)) as wkb_geom")
    else:
        return None
    
    if 'length' in available_cols: select_fields.append("round(e.length, 1) as length_m")
    elif 'length_m' in available_cols: select_fields.append("round(e.length_m, 1) as length_m")
    else: select_fields.append("0.0 as length_m")

    query = f"SELECT {', '.join(select_fields)} FROM shortcuts.shortcuts s JOIN shortcuts.edges e ON s.from_edge = e.id LIMIT 50000"
    df = con.execute(query).df()
    if df.empty: return None

    def parse_path(wkb):
        try:
            wkb_data = bytes(wkb)
            line = shapely.from_wkb(wkb_data)
            return list(line.coords)
        except:
            return []
            
    df['path'] = df['wkb_geom'].apply(parse_path)
    df['color'] = [[255, 0, 255, 120]] * len(df)
    
    return sanitize_df(df)



# --- RENDERING ---
all_layers = []
for mode in selected_modes:
    df = fetch_network_data(selected_db, mode, edge_limit, use_offset, cache_key=mtime)
    if df is not None:
        all_layers.append(pdk.Layer("PathLayer", df, pickable=True, get_path="path", get_color="color", get_width=LINE_WIDTH, width_min_pixels=1, auto_highlight=True))

if show_shortcuts:
    sdf = fetch_shortcut_data(selected_db, cache_key=mtime)
    if sdf is not None:
        all_layers.append(pdk.Layer("PathLayer", sdf, pickable=True, get_path="path", get_color="color", get_width=2, width_min_pixels=1, auto_highlight=True))

if all_layers:
    try:
        meta = con.execute("SELECT center_lat, center_lon, initial_zoom FROM main.visualization").fetchone()
        if meta:
            lat, lon, zoom = meta
        else:
            first_df = all_layers[0].data
            if not first_df.empty and len(first_df['path']) > 0:
                first_path = list(first_df['path'])[0]
                lat, lon, zoom = first_path[0][1], first_path[0][0], 13
            else:
                lat, lon, zoom = 49.2827, -123.1207, 12
    except:
        lat, lon, zoom = 49.2827, -123.1207, 12
    
    st.pydeck_chart(pdk.Deck(
        map_style=chosen_style,
        initial_view_state=pdk.ViewState(longitude=float(lon), latitude=float(lat), zoom=int(zoom), pitch=0),
        layers=all_layers,
        height=1000, 
        tooltip={
            "html": "<b>{highway}</b>: {name}<br/>OSM ID: {osm_id}<br/>{speed_kmh} km/h | {length_m}m" if not show_shortcuts else "Shortcut Cost: {cost}",
            "style": {"backgroundColor": "#161b22", "color": "#c9d1d9"}
        }
    ), key=f"deck-{basemap_name}-{'-'.join(selected_modes)}")

else:
    st.info(" Select networks in the sidebar to visualize.")
