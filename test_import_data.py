# streamlit_app.py
import streamlit as st
import xarray as xr
import rioxarray
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import leafmap.foliumap as leafmap


# ----------------------
# Functions
# ----------------------
def load_netcdf(nc_file, var_index=0, time_sel=None):
    """Load NetCDF file into an xarray DataArray."""
    ds = xr.open_dataset(nc_file)
    var_name = list(ds.data_vars.keys())[var_index]
    da = ds[var_name]

    if "time" in da.dims and time_sel is not None:
        da = da.sel(time=time_sel)

    if not da.rio.crs:
        da = da.rio.write_crs("EPSG:4326")

    return da


def threshold_to_polygons(da, threshold):
    """Convert values above threshold into polygons (GeoDataFrame)."""
    mask = (da.values > threshold).astype(np.uint8)
    transform = da.rio.transform()

    polygons = []
    for geom, val in shapes(mask, mask=mask, transform=transform):
        if val == 1:
            polygons.append(shape(geom))

    if not polygons:
        return gpd.GeoDataFrame(geometry=[], crs=da.rio.crs), mask

    gdf = gpd.GeoDataFrame(geometry=polygons, crs=da.rio.crs)
    return gdf, mask


def summarize_mask(mask):
    """Return simple stats about the threshold exceedance mask."""
    total_cells = mask.size
    exceed_cells = int(mask.sum())
    pct = 100 * exceed_cells / total_cells if total_cells else 0
    return total_cells, exceed_cells, pct


def show_map(gdf):
    """Render GeoDataFrame on a Leafmap map and return it."""
    m = leafmap.Map(center=[0, 0], zoom=2)
    if not gdf.empty:
        m.add_gdf(gdf, layer_name="Above Threshold")
    return m


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
