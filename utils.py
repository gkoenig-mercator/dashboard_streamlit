import geopandas as gpd

def gdf_to_geojson(gdf: gpd.GeoDataFrame) -> str:
    """Convert a GeoDataFrame to a GeoJSON string."""
    return gdf.to_json() if not gdf.empty else ""

