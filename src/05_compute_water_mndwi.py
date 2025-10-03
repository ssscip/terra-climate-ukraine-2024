"""Compute MNDWI (Modified Normalized Difference Water Index) from MOD09GA.

Formula: (Green - SWIR1) / (Green + SWIR1)
Bands: using surface reflectance sur_refl_b04 (Green) & sur_refl_b05 (SWIR1) by convention here.

Outputs:
  data_products/mndwi_mean_event_jul_aug.nc (event subset)
  data_products/mndwi_mean_baseline_jul_aug.nc (baseline years)
  data_products/mndwi_delta_jul_aug.nc (event - baseline)

Currently no QA masking; add bitmask filtering for production (clouds, etc.).
"""
from __future__ import annotations

from pathlib import Path
import re
import datetime as dt
import yaml
import numpy as np
import xarray as xr
from modis_io import open_mod09ga_bands

CONFIG_PATH = Path("config.yml")
RAW_DIR = Path("data_raw/MOD09GA")
OUT_BASE = Path("data_products/mndwi_mean_baseline_jul_aug.nc")
OUT_EVENT = Path("data_products/mndwi_mean_event_jul_aug.nc")
OUT_DELTA = Path("data_products/mndwi_delta_jul_aug.nc")

DATE_RE = re.compile(r"A(\d{4})(\d{3})")


def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def extract_date(name: str):
    m = DATE_RE.search(name)
    if not m:
        return None
    y = int(m.group(1)); doy = int(m.group(2))
    return dt.date.fromordinal(dt.date(y, 1, 1).toordinal() + doy - 1)


def mndwi(green: xr.DataArray, swir: xr.DataArray) -> xr.DataArray:
    return (green - swir) / (green + swir)


def main():
    cfg = parse_config()
    start = cfg["baseline"]["start_year"]; end = cfg["baseline"]["end_year"]; event_year = cfg["event_year"]
    files = sorted(RAW_DIR.glob("*.hdf"))
    if not files:
        print("No MOD09GA files found.")
        return
    base_stack = []
    event_stack = []
    for fp in files:
        date = extract_date(fp.name)
        if not date:
            continue
        green, swir1 = open_mod09ga_bands(fp)
        if green is None or swir1 is None:
            continue
        da = mndwi(green, swir1).astype("float32")
        da = da.expand_dims(time=[np.datetime64(date)])
        if start <= date.year <= end and date.month in (7, 8):
            base_stack.append(da)
        if date.year == event_year and date.month in (7, 8):
            event_stack.append(da)
    if not base_stack or not event_stack:
        print("Insufficient baseline or event MNDWI data.")
        return
    base = xr.concat(base_stack, dim="time")
    event = xr.concat(event_stack, dim="time")
    base_mean = base.mean("time")
    event_mean = event.mean("time")
    delta = event_mean - base_mean
    base_mean.name = "MNDWI_base_mean_jul_aug"
    event_mean.name = "MNDWI_event_mean_jul_aug"
    delta.name = "MNDWI_delta_jul_aug"
    base_mean.to_dataset().to_netcdf(OUT_BASE)
    event_mean.to_dataset().to_netcdf(OUT_EVENT)
    delta.to_dataset().to_netcdf(OUT_DELTA)
    print(f"Wrote {OUT_BASE}, {OUT_EVENT}, {OUT_DELTA}")


if __name__ == "__main__":
    main()
