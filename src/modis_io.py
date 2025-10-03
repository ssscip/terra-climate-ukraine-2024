"""MODIS IO helpers for Terra Climate Extremes.

Provides functions to open MODIS HDF (MOD11A1, MOD09GA, MOD13Q1) using rioxarray/rasterio.
These are lightweight wrappers; real production should include full QC bitmask handling.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import re
import xarray as xr
import rioxarray  # noqa: F401  (ensures GDAL drivers registered)

LST_BAND_CANDIDATES = [
    "LST_Day_1km",  # MOD11A1 standard
    "LST_Day",      # sometimes simplified
]
NDVI_BAND_CANDIDATES = [
    "NDVI", "ndvi", "NDVI_1km", "250m 16 days NDVI"]

# MOD09GA spectral mapping (Collection 6.1): 1=Red, 2=NIR, 3=Blue, 4=Green, 5=SWIR1 (1.24µm), 6=SWIR2 (1.64µm), 7=SWIR3 (2.13µm)
# For MNDWI we generally use Green (band4) and SWIR1 (band5) or SWIR2 depending on convention; here choose band5 as SWIR1.
MOD09GA_GREEN = re.compile(r"(?i)sur_refl_b04")
MOD09GA_SWIR1 = re.compile(r"(?i)sur_refl_b05")


def _pick_band(ds: xr.Dataset, candidates) -> Optional[str]:
    for c in candidates:
        if c in ds.data_vars:
            return c
    # try fuzzy
    lowered = {k.lower(): k for k in ds.data_vars}
    for c in candidates:
        if c.lower() in lowered:
            return lowered[c.lower()]
    return None


def open_mod11a1_lst(path: Path, scale: float) -> xr.DataArray | None:
    """Open MOD11A1 HDF and return scaled daytime LST (Kelvin)."""
    try:
        ds = xr.open_dataset(path, engine="netcdf4")  # GDAL HDF4 to NetCDF virtual
    except Exception:
        # fallback: try rioxarray.open_rasterio (subdataset discovery)
        try:
            ds = xr.open_dataset(path)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to open {path}: {e}")
            return None
    band = _pick_band(ds, LST_BAND_CANDIDATES)
    if not band:
        print(f"No LST band found in {path.name}")
        return None
    da = ds[band].astype("float32") * scale
    # NaN invalid fill values
    if hasattr(da, "_FillValue"):
        da = da.where(da != da._FillValue)
    return da


def open_mod13q1_ndvi(path: Path, scale: float) -> xr.DataArray | None:
    try:
        ds = xr.open_dataset(path, engine="netcdf4")
    except Exception as e:  # noqa: BLE001
        print(f"NDVI open fail {path}: {e}")
        return None
    band = _pick_band(ds, NDVI_BAND_CANDIDATES)
    if not band:
        print(f"No NDVI band in {path.name}")
        return None
    da = ds[band].astype("float32") * scale
    if hasattr(da, "_FillValue"):
        da = da.where(da != da._FillValue)
    return da


def open_mod09ga_bands(path: Path):
    """Return (green, swir1) reflectance as float32 scaled (assumes scale factor 0.0001 if attribute present)."""
    try:
        ds = xr.open_dataset(path, engine="netcdf4")
    except Exception as e:  # noqa: BLE001
        print(f"MOD09GA open fail {path}: {e}")
        return None, None
    green_name = None
    swir_name = None
    for var in ds.data_vars:
        if MOD09GA_GREEN.fullmatch(var):
            green_name = var
        if MOD09GA_SWIR1.fullmatch(var):
            swir_name = var
    if green_name is None or swir_name is None:
        print(f"Could not find required bands in {path.name}")
        return None, None
    green = ds[green_name].astype("float32")
    swir1 = ds[swir_name].astype("float32")
    # scale
    scale = ds[green_name].attrs.get("scale_factor") or 0.0001
    green *= scale
    swir1 *= scale
    return green, swir1
