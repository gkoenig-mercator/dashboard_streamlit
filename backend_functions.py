import streamlit as st
import xarray as xr
import rioxarray
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import leafmap.foliumap as leafmap

@st.cache_resource
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
