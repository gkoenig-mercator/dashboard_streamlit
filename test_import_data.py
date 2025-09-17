# streamlit_app.py
import streamlit as st
import xarray as xr
import rioxarray
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import leafmap.foliumap as leafmap

st.set_page_config(page_title="NetCDF Threshold Zones", layout="wide")
st.title("🌍 NetCDF Threshold Dashboard")

# --- Input ---
nc_file = st.file_uploader("Upload a NetCDF file", type=["nc"])
threshold = st.number_input("Threshold value", value=10.0)

if nc_file:
    # --- Load dataset ---
    ds = xr.open_dataset(nc_file)

    # Assume first variable is of interest
    var_name = list(ds.data_vars.keys())[0]
    da = ds[var_name]

    # Select a time step if needed
    if "time" in da.dims:
        times = da["time"].values
        selected_time = st.selectbox("Select time step", times)
        da = da.sel(time=selected_time)

    # Ensure CRS exists
    if not da.rio.crs:
        da = da.rio.write_crs("EPSG:4326")

    # --- Threshold mask ---
    mask = (da.values > threshold).astype(np.uint8)

    # --- Extract polygons from mask ---
    transform = da.rio.transform()
    polygons = []
    for geom, val in shapes(mask, mask=mask, transform=transform):
        if val == 1:  # keep only "True" polygons
            polygons.append(shape(geom))

    if len(polygons) == 0:
        st.warning("No exceedance polygons found for this threshold.")
    else:
        # Create GeoDataFrame from polygons
        gdf = gpd.GeoDataFrame(geometry=polygons, crs=da.rio.crs)

        # --- Map ---
        st.subheader("Exceedance Zones")
        m = leafmap.Map(center=[0, 0], zoom=2)
        m.add_gdf(gdf, layer_name="Above Threshold")
        m.to_streamlit(height=600)

        # --- Stats ---
        st.subheader("Summary")
        total_cells = mask.size
        exceed_cells = int(mask.sum())
        st.write(f"**Total cells:** {total_cells}")
        st.write(f"**Exceeding cells:** {exceed_cells}")
        st.write(f"**% Above Threshold:** {100 * exceed_cells / total_cells:.2f}%")

        # Optional: let user download the polygons
        geojson_str = gdf.to_json()
        st.download_button(
            "Download exceedance polygons as GeoJSON",
            geojson_str,
            file_name="exceedance_polygons.geojson",
            mime="application/geo+json"
        )
