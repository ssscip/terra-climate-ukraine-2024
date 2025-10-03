"""Utility IO and masking helpers for Terra Climate Extremes project."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import xarray as xr
from shapely.geometry import shape
from shapely.prepared import prep

try:  # Attempt geopandas import (preferred for speed)
    import geopandas as gpd  # type: ignore
except Exception:  # noqa: BLE001
    gpd = None  # Fallback path will be used


def load_geojson(path: str | Path) -> Dict[str, Any]:
    """Load a GeoJSON FeatureCollection and return its JSON dict.

    Parameters
    ----------
    path : str or Path
        Path to GeoJSON file.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def make_mask(ds: xr.Dataset | xr.DataArray, geo: Dict[str, Any], lon_name: str = "lon", lat_name: str = "lat") -> xr.DataArray:
    """Create a boolean mask for the provided dataset given a GeoJSON FeatureCollection.

    Assumes regular lon/lat 2D or 1D coordinate variables.
    """
    if lon_name not in ds.coords or lat_name not in ds.coords:
        raise ValueError(f"Dataset must have '{lon_name}' and '{lat_name}' coordinates")

    # Collect shapes
    geometries = []
    for feat in geo.get("features", []):
        geometries.append(shape(feat["geometry"]))

    if not geometries:
        raise ValueError("No geometries found in GeoJSON")

    # Prepare coordinate mesh
    lon = ds[lon_name]
    lat = ds[lat_name]

    if lon.ndim == 1 and lat.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon.values, lat.values)
    else:
        lon2d, lat2d = lon.values, lat.values

    if gpd is not None:
        # Vectorized path with geopandas
        points_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(lon2d.ravel(), lat2d.ravel()), crs="EPSG:4326"
        )
        poly_gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")
        joined = points_gdf.sjoin(poly_gdf, predicate="within", how="left")
        mask_flat = ~joined.index_right.isna()
        mask = mask_flat.values.reshape(lon2d.shape)
    else:
        # Fallback: pure shapely prepared geometries (slower but OK for demo grid sizes)
        prepared = [prep(g) for g in geometries]
        pts_lon = lon2d.ravel(); pts_lat = lat2d.ravel()
        inside = np.zeros(pts_lon.shape[0], dtype=bool)
        for i, (x, y) in enumerate(zip(pts_lon, pts_lat)):
            for pg in prepared:
                if pg.contains(shape({"type": "Point", "coordinates": (float(x), float(y))})):
                    inside[i] = True
                    break
        mask = inside.reshape(lon2d.shape)

    da_mask = xr.DataArray(mask, coords={lat_name: lat, lon_name: lon}, dims=(lat_name, lon_name))
    da_mask.name = "mask"
    return da_mask


def apply_mask(da: xr.DataArray, mask: xr.DataArray) -> xr.DataArray:
    """Apply boolean mask to DataArray (True inside region)."""
    # Align
    mask_aligned = mask.broadcast_like(da.isel(**{dim: 0 for dim in da.dims if dim not in mask.dims})) if set(mask.dims) != set(da.dims) else mask
    return da.where(mask_aligned, drop=False)
