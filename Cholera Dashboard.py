# cholera_dashboard.py
# UPDATED CODE - FIXED LIGHT_SETTINGS ERROR

import streamlit as st
import geopandas as gpd
import pandas as pd
import os
import pydeck as pdk
import numpy as np

# ================================
# 1. FOLDER PATH
# ================================
folder = r"C:\Users\User\Documents\2025 Master UiTM\Sem 2\GES 723 GEOVISUALIZATION\ASSIGNMENT\cholera-deaths (1)"

if not os.path.exists(folder):
    st.error("Folder not found!")
    st.stop()

# ================================
# 2. LOAD DATA + EXACT COLUMNS
# ================================
@st.cache_data
def load_data():
    # Load shapefiles
    deaths = gpd.read_file(os.path.join(folder, "Cholera_Deaths.shp")).to_crs(epsg=4326)
    pumps  = gpd.read_file(os.path.join(folder, "Pumps.shp")).to_crs(epsg=4326)

    # Use exact column names
    death_count_col = "Count"   # ← As in your attribute table
    pump_id_col     = "Id"       # ← As in your attribute table

    # Ensure columns exist
    if death_count_col not in deaths.columns:
        st.error(f"'{death_count_col}' column not found in Cholera_Deaths.shp")
        st.stop()
    if pump_id_col not in pumps.columns:
        st.error(f"'{pump_id_col}' column not found in Pumps.shp")
        st.stop()

    total_deaths = int(deaths[death_count_col].sum())

    # Add coordinates
    deaths["lon"] = deaths.geometry.x
    deaths["lat"] = deaths.geometry.y
    pumps["lon"]  = pumps.geometry.x
    pumps["lat"]  = pumps.geometry.y

    # Distance to nearest pump + name
    def nearest(row):
        dists = pumps.geometry.distance(row.geometry)
        idx = dists.idxmin()
        return pd.Series({
            "dist_m": round(dists.min() * 111320, 1),
            "pump_id": pumps.loc[idx, pump_id_col]
        })
    deaths[["dist_m", "pump_id"]] = deaths.apply(nearest, axis=1)

    return deaths, pumps, death_count_col, pump_id_col, total_deaths

deaths_gdf, pumps_gdf, count_col, pump_col, total_deaths = load_data()

# ================================
# STYLE
# ================================
st.set_page_config(page_title="John Snow Cholera Map – GES723", layout="wide")
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(90deg, #7f1d1d, #991b1b);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        box-shadow: 0 8px 30px rgba(220,38,38,0.5);
        margin: 2rem 0;
    }
    .death-tooltip {
        background: linear-gradient(135deg, #ff4444, #cc0000);
        color: white;
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #ff0000;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .pump-tooltip {
        background: linear-gradient(135deg, #4444ff, #0000cc);
        color: white;
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #0000ff;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .section-header {
        background: linear-gradient(90deg, #1e3a8a, #3730a3);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🗺️ John Snow's Cholera Map (1854) - Advanced 3D Visualization")
st.markdown(f'<div class="kpi-card">Cumulative Deaths<br>{total_deaths:,}</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎯 2D Interactive Map", "🏗️ 3D Extruded Map", "📊 Data Analysis"])

# =====================================
# 2D MAP - COMBINED PUMPS AND DEATHS
# =====================================
with tab1:
    st.markdown('<div class="section-header">🎯 2D Interactive Map – Deaths and Pumps Combined</div>', unsafe_allow_html=True)
    
    # COMBINED TOOLTIP FOR BOTH LAYERS
    combined_tooltip_2d = {
        "html": """
    {% if feature.properties.type == 'death' %}
    <div class="death-tooltip">
        <b>💀 CHOLERA DEATH</b><br>
        <b>Deaths at this location:</b> {Count}<br>
        <b>Nearest Pump ID:</b> {pump_id}<br>
        <b>Distance to Pump:</b> {dist_m} meters
    </div>
    {% elif feature.properties.type == 'pump' %}
    <div class="pump-tooltip">
        <b>🚰 WATER PUMP</b><br>
        <b>Pump ID:</b> {Id}<br>
    </div>
    {% endif %}
    """,
    "style": {"fontSize": "14px"}
    }
        
    

    # DEATHS LAYER - 2D
    deaths_layer_2d = pdk.Layer(
        "ScatterplotLayer", 
        data=deaths_gdf,
        get_position=["lon", "lat"], 
        get_radius=4,
        get_fill_color=[220, 38, 38, 255],
        get_line_color=[255, 255, 255],
        get_line_width=2,
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        id="deaths-layer"
    )

    # PUMPS LAYER - 2D
    pumps_layer_2d = pdk.Layer(
        "ScatterplotLayer", 
        data=pumps_gdf,
        get_position=["lon", "lat"], 
        get_radius=10,
        get_fill_color=[30, 100, 255, 255],
        get_line_color=[255, 255, 255],
        get_line_width=3,
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True,
        id="pumps-layer"
    )

    # HEATMAP LAYER
    heatmap_layer = pdk.Layer(
        "HeatmapLayer", 
        data=deaths_gdf,
        get_position=["lon", "lat"], 
        get_weight=count_col,
        radius_pixels=80, 
        intensity=1.5, 
        opacity=0.7,
        threshold=0.1,
        id="heatmap-layer"
    )

    # SINGLE COMBINED MAP
    st.pydeck_chart(pdk.Deck(
        layers=[heatmap_layer, deaths_layer_2d, pumps_layer_2d],
        initial_view_state=pdk.ViewState(
            latitude=51.5134, 
            longitude=-0.1368, 
            zoom=16.8,
            pitch=0,
            bearing=0
        ),
        map_style="light",
        tooltip=combined_tooltip_2d
    ), use_container_width=True)

# =====================================
# 3D MAP – FIXED VISUALIZATION
# =====================================
with tab2:
    st.markdown('<div class="section-header">🏗️ 3D Map – Enhanced Visualization</div>', unsafe_allow_html=True)

    # Create a base bounding box for the area
    min_lon, max_lon = deaths_gdf.lon.min(), deaths_gdf.lon.max()
    min_lat, max_lat = deaths_gdf.lat.min(), deaths_gdf.lat.max()
    
    # Expand the bounds slightly
    lon_padding = (max_lon - min_lon) * 0.1
    lat_padding = (max_lat - min_lat) * 0.1
    
    base_polygon = [{
        "polygon": [
            [min_lon - lon_padding, min_lat - lat_padding],
            [max_lon + lon_padding, min_lat - lat_padding],
            [max_lon + lon_padding, max_lat + lat_padding],
            [min_lon - lon_padding, max_lat + lat_padding]
        ]
    }]

    # BASE GROUND LAYER
    base_layer = pdk.Layer(
        "PolygonLayer",
        data=base_polygon,
        get_polygon="polygon",
        get_fill_color=[245, 245, 245, 200],  # Light gray base
        get_line_color=[200, 200, 200, 100],
        stroked=True,
        filled=True,
        extruded=False,
        pickable=False,
        id="base-layer"
    )

    # 3D DEATHS LAYER - ENHANCED
    deaths_layer_3d = pdk.Layer(
        "ColumnLayer",
        data=deaths_gdf,
        get_position=["lon", "lat"],
        disk_resolution=10,
        radius=5,
        get_elevation=count_col,
        elevation_scale=1.5,  # Increased scale for better visibility
        get_fill_color=[220, 38, 38, 240],
        get_line_color=[255, 200, 200, 255],
        get_line_width=30,
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True,
        extruded=True,
        id="deaths-3d-layer",
        coverage=1.0
    )

    # 3D PUMPS LAYER - ENHANCED
    pumps_layer_3d = pdk.Layer(
        "ColumnLayer",
        data=pumps_gdf,
        get_position=["lon", "lat"],
        disk_resolution=16,
        radius=8,
        get_elevation=10,  # Taller for emphasis
        elevation_scale=1,
        get_fill_color=[30, 100, 255, 250],
        get_line_color=[200, 200, 255, 255],
        get_line_width=40,
        line_width_min_pixels=3,
        pickable=True,
        auto_highlight=True,
        extruded=True,
        id="pumps-3d-layer",
        coverage=1.0
    )

    # COMBINED TOOLTIP FOR 3D
    combined_tooltip_3d = {
        "html": """
        {% if layer.id == 'deaths-3d-layer' %}
        <div class="death-tooltip">
            <b>💀 3D DEATH COLUMN</b><br>
            <b>Deaths at this location:</b> {Count}<br>
            <b>Nearest Pump ID:</b> {pump_id}<br>
            <b>Distance to Pump:</b> {dist_m} meters<br>
            
        </div>
        {% elif layer.id == 'pumps-3d-layer' %}
        <div class="pump-tooltip">
            <b>🚰 3D PUMP TOWER</b><br>
            <b>Pump ID:</b> {Id}<br>
            
        </div>
        {% endif %}
        """,
        "style": {"fontSize": "14px"}
    }

    # Camera controls
    col1, col2, col3 = st.columns(3)
    with col1:
        pitch = st.slider("Camera Angle", 0, 80, 45, key="pitch_3d")
    with col2:
        bearing = st.slider("Rotation", -180, 180, 0, key="bearing_3d")
    with col3:
        zoom = st.slider("Zoom Level", 15, 20, 17, key="zoom_3d")

    # COMBINED 3D VISUALIZATION - FIXED: removed light_settings from Deck
    st.pydeck_chart(pdk.Deck(
        layers=[base_layer, deaths_layer_3d, pumps_layer_3d],
        initial_view_state=pdk.ViewState(
            latitude=51.5134,
            longitude=-0.1368,
            zoom=zoom,
            pitch=pitch,
            bearing=bearing,
            min_zoom=15,
            max_zoom=20
        ),
        map_style="light",
        tooltip=combined_tooltip_3d,
        parameters={
            "blend": True,
            "blendEquation": "MAX",
            "depthTest": True,
            "clearColor": [255, 255, 255, 255],
        }
    ), use_container_width=True)

    # Visualization tips
    st.info("""
    **🎮 3D Navigation Tips:**
    - **Click & Drag**: Rotate the camera around the scene
    - **Scroll**: Zoom in and out
    - **Shift + Drag**: Pan the map
    - **Use sliders above** to adjust the view precisely
    - The light gray base helps eliminate dark shadows between columns
    """)

# =====================================
# DATA ANALYSIS TAB
# =====================================
with tab3:
    st.markdown('<div class="section-header">📊 Data Analysis & Insights</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💀 Deaths Statistics")
        st.metric("Total Deaths", f"{total_deaths:,}")
        st.metric("Unique Death Locations", len(deaths_gdf))
        st.metric("Average Deaths per Location", f"{deaths_gdf[count_col].mean():.1f}")
        st.metric("Maximum Deaths at Single Location", int(deaths_gdf[count_col].max()))
        
        # Deaths distribution
        st.subheader("Deaths Distribution")
        death_counts = deaths_gdf[count_col].value_counts().sort_index()
        st.bar_chart(death_counts)
    
    with col2:
        st.subheader("🚰 Pumps Statistics")
        st.metric("Total Pumps", len(pumps_gdf))
        st.metric("Average Distance to Nearest Pump", f"{deaths_gdf['dist_m'].mean():.1f} meters")
        st.metric("Maximum Distance to Pump", f"{deaths_gdf['dist_m'].max():.1f} meters")
        
        # Distance analysis
        st.subheader("Distance to Nearest Pump")
        st.write(f"**Closest death to any pump:** {deaths_gdf['dist_m'].min():.1f} meters")
        st.write(f"**75% of deaths within:** {deaths_gdf['dist_m'].quantile(0.75):.1f} meters of a pump")
    
    # Pump-death relationship
    st.subheader("🔗 Deaths by Nearest Pump")
    deaths_by_pump = deaths_gdf.groupby('pump_id').agg({
        count_col: 'sum',
        'dist_m': 'mean'
    }).round(1).sort_values(count_col, ascending=False)
    
    st.dataframe(
        deaths_by_pump.head(10),
        use_container_width=True,
        column_config={
            count_col: st.column_config.NumberColumn("Total Deaths", format="%d"),
            'dist_m': st.column_config.NumberColumn("Avg Distance (m)", format="%.1f")
        }
    )

# ================================
# SIDEBAR
# ================================
st.sidebar.title("🎯 GES723 Final Project")
st.sidebar.subheader("📊 Data Summary")

# Deaths Statistics
st.sidebar.markdown("**💀 Deaths Analysis**")
st.sidebar.write(f"Total Deaths: **{total_deaths:,}**")
st.sidebar.write(f"Death Locations: **{len(deaths_gdf)}**")
st.sidebar.write(f"Avg Deaths per Location: **{deaths_gdf[count_col].mean():.1f}**")

# Pumps Statistics
st.sidebar.markdown("**🚰 Pumps Analysis**")
st.sidebar.write(f"Total Pumps: **{len(pumps_gdf)}**")
st.sidebar.write(f"Avg Distance to Pump: **{deaths_gdf['dist_m'].mean():.1f} m**")

# Legend
st.sidebar.markdown("**🎨 Visualization Guide**")
st.sidebar.markdown("""
- **💀 Red Points/Columns**: Cholera death locations
- **🚰 Blue Points/Towers**: Water pump locations  
- **🔥 Heatmap**: Death density visualization
- **🏗️ 3D Height**: Represents number of deaths
""")

st.sidebar.markdown("**🖱️ Interaction Guide**")
st.sidebar.markdown("""
- **Hover**: See detailed information
- **2D Map**: Basic spatial analysis
- **3D Map**: Enhanced depth perception
- **Click & Drag**: Navigate the 3D view
""")

st.sidebar.success("💡 **Pro Tip**: Use the 3D view to understand the spatial relationship between deaths and pumps!")


