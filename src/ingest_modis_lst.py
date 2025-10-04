"""Ingest MOD11C1 daily LST files into yearly NetCDF stacks, applying QC + optional ROI mask.
Requires GDAL/rasterio to understand HDF4 subdatasets.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
import numpy as np
import xarray as xr
import rasterio
from shapely.geometry import shape
import json

LST_SDS_CANDIDATES = [
    # Common grid names for MOD11 products (collection 6.1)
    "MODIS_Grid_Daily_1Deg_CMG:LST_Day_CMG",
    "MODIS_Grid_8Day_1km_LST:LST_Day_CMG",
]
QC_SDS_CANDIDATES = [
    "MODIS_Grid_Daily_1Deg_CMG:QC_Day",
    "MODIS_Grid_8Day_1km_LST:QC_Day",
]
SCALE = 0.02
FILL_VALUE = 0


def list_hdf(root: str, years=None):
    rootp = Path(root)
    for year_dir in sorted(rootp.glob("*/")):
        if years and year_dir.name not in {str(y) for y in years}:
            continue
        for doy_dir in sorted(year_dir.glob("*/")):
            for hdf in doy_dir.glob("*.hdf"):
                yield hdf


def _gdalinfo(hdf_path: Path) -> list[str]:
    out = subprocess.check_output(["gdalinfo", str(hdf_path)], text=True, errors="ignore")
    lines = [l.strip() for l in out.splitlines() if "SUBDATASET_" in l and "=HDF4_EOS" in l]
    return [l.split("=", 1)[1] for l in lines]


def _select_subdataset(hdf_path: Path, sds_candidates: list[str]):
    # Returns first matching subdataset full path (HDF4_EOS:...) else raises
    info_paths = _gdalinfo(hdf_path)
    for cand in sds_candidates:
        for line in info_paths:
            if line.endswith(cand):
                return line
    raise RuntimeError(f"None of {sds_candidates} found in {hdf_path.name}")


def _read_array(subdataset_path: str):
    with rasterio.open(subdataset_path) as src:
        arr = src.read(1)
        profile = src.profile
    return arr, profile


def decode_qc(qc_arr: np.ndarray):
    # Accept if bits 0-1 in {0,1}
    flags = qc_arr & 0b11
    return np.isin(flags, [0, 1])


def _roi_mask(profile, roi_geojson: str):
    from rasterio import features
    with open(roi_geojson, "r", encoding="utf-8") as f:
        geo = json.load(f)
    geom = shape(geo["features"][0]["geometry"])  # first feature
    mask = features.rasterize(
        [(geom, 1)],
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        fill=0,
    ).astype(bool)
    return mask


def ingest(hdf_files, roi_geojson: str | None = None):
    times = []
    cubes = []
    roi_mask_local = None
    for hdf in sorted(hdf_files):
        name = hdf.name  # MOD11C1.AYYYYDDD...
        year = int(name[9:13])
        doy = int(name[13:16])
        import datetime
        dt = datetime.datetime.strptime(f"{year}-{doy:03d}", "%Y-%j").date()
        lst_sds = _select_subdataset(hdf, LST_SDS_CANDIDATES)
        qc_sds = _select_subdataset(hdf, QC_SDS_CANDIDATES)
        lst_raw, profile = _read_array(lst_sds)
        qc_raw, _ = _read_array(qc_sds)
        good = decode_qc(qc_raw)
        data = lst_raw.astype("float32")
        data[data == FILL_VALUE] = np.nan
        data = data * SCALE
        data[~good] = np.nan
        if roi_geojson:
            if roi_mask_local is None:
                roi_mask_local = _roi_mask(profile, roi_geojson)
            data[~roi_mask_local] = np.nan
        cubes.append(data)
        times.append(np.datetime64(dt))
    stack = np.stack(cubes, axis=0)  # time,y,x
    transform = profile["transform"]
    h = profile["height"]
    w = profile["width"]
    ys = np.arange(h)
    xs = np.arange(w)
    lats = transform.f + ys * transform.e
    lons = transform.c + xs * transform.a
    ds = xr.Dataset(
        {"LST": (("time", "y", "x"), stack)},
        coords={
            "time": times,
            "lat": ("y", lats),
            "lon": ("x", lons),
        },
        attrs={"product": "MOD11C1", "scale": SCALE}
    )
    return ds


def save_yearly(ds: xr.Dataset, out_dir: str):
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    for year, sub in ds.groupby("time.year"):
        fn = outp / f"lst_daily_{int(year)}.nc"
        sub.to_netcdf(fn)


__all__ = ["list_hdf", "ingest", "save_yearly"]
