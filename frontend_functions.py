import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap

def time_selector(time_steps):
    """Show a selectbox for time steps and return the selected value."""
    if time_steps is None:
        return None
    selected = st.selectbox("Select time step", time_steps)
    return selected

def download_button(geojson_str: str, label="Download GeoJSON", file_name="data.geojson"):
    """Create a Streamlit download button for a GeoJSON string."""
    if geojson_str:
        st.download_button(
            label,
            geojson_str,
            file_name=file_name,
            mime="application/geo+json"
        )

def display_warning_if_empty(gdf: gpd.GeoDataFrame, message: str):
    """Show a warning if GeoDataFrame is empty."""
    if gdf.empty:
        st.warning(message)
        return True
    return False

def render_map(gdf: gpd.GeoDataFrame, layer_name="Above Threshold", height=600):
    """Render a GeoDataFrame on a Leafmap map in Streamlit."""
    if gdf.empty:
        return None
    m = leafmap.Map(center=[0, 0], zoom=2)
    m.add_gdf(gdf, layer_name=layer_name)
    m.to_streamlit(height=height)
    return m
