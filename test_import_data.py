# streamlit_app.py
import streamlit as st
import xarray as xr
import rioxarray
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import leafmap.foliumap as leafmap
from backend_functions import load_netcdf, threshold_to_polygons, summarize_mask, show_map

# ----------------------
# Streamlit app
# ----------------------
st.set_page_config(page_title="NetCDF Threshold Zones", layout="wide")
st.title("🌍 NetCDF Threshold Dashboard")

nc_file = st.file_uploader("Upload a NetCDF file", type=["nc"])
threshold = st.number_input("Threshold value", value=10.0)

if nc_file:
    ds = xr.open_dataset(nc_file)
    var_name = list(ds.data_vars.keys())[0]
    da_preview = ds[var_name]

    # Time selector
    time_sel = None
    if "time" in da_preview.dims:
        times = da_preview["time"].values
        time_sel = st.selectbox("Select time step", times)

    # Process data
    da = load_netcdf(nc_file, time_sel=time_sel)
    gdf, mask = threshold_to_polygons(da, threshold)
    total_cells, exceed_cells, pct = summarize_mask(mask)

    # Show map
    st.subheader("Exceedance Zones")
    if gdf.empty:
        st.warning("No exceedance polygons found for this threshold.")
    else:
        m = show_map(gdf)
        m.to_streamlit(height=600)

        # Allow download
        geojson_str = gdf.to_json()
        st.download_button(
            "Download polygons as GeoJSON",
            geojson_str,
            file_name="exceedance_polygons.geojson",
            mime="application/geo+json"
        )

    # Show stats
    st.subheader("Summary")
    st.write(f"**Total cells:** {total_cells}")
    st.write(f"**Exceeding cells:** {exceed_cells}")
    st.write(f"**% Above Threshold:** {pct:.2f}%")
