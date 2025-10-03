"""Compute NDVI July–August baseline vs event means and delta."""
from __future__ import annotations

from pathlib import Path
import re
import datetime as dt
import yaml
import xarray as xr
import numpy as np
from modis_io import open_mod13q1_ndvi

CONFIG_PATH = Path("config.yml")
RAW_DIR = Path("data_raw/MOD13Q1")
OUT_BASE = Path("data_products/ndvi_base_mean.nc")
OUT_EVENT = Path("data_products/ndvi_event_mean.nc")
OUT_DELTA = Path("data_products/ndvi_delta_jul_aug.nc")

DATE_RE = re.compile(r"A(\d{4})(\d{3})")  # Some MODIS products follow similar pattern


def extract_date(fname: str) -> dt.date | None:
    m = DATE_RE.search(fname)
    if not m:
        return None
    year = int(m.group(1))
    doy = int(m.group(2))
    return dt.date.fromordinal(dt.date(year, 1, 1).toordinal() + doy - 1)


def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def open_ndvi(path: Path, scale_factor: float):
    da = open_mod13q1_ndvi(path, scale_factor)
    if da is None:
        return None
    d = extract_date(path.name)
    if d is None:
        return None
    return da.expand_dims(time=[np.datetime64(d)])


def main():
    cfg = parse_config()
    start = cfg["baseline"]["start_year"]
    end = cfg["baseline"]["end_year"]
    event_year = cfg["event_year"]
    scale = cfg["thresholds"]["ndvi_scale_factor"]

    files = sorted(RAW_DIR.glob("*.hdf"))
    if not files:
        print("No MOD13Q1 files found.")
        return

    base_records = []
    event_records = []
    for fp in files:
        d = extract_date(fp.name)
        if not d:
            continue
        da = open_ndvi(fp, scale)
        if da is None:
            continue
        if start <= d.year <= end:
            base_records.append(da)
        if d.year == event_year:
            event_records.append(da)

    if not base_records or not event_records:
        print("Insufficient data for base or event.")
        return

    base = xr.concat(base_records, dim="time")
    event = xr.concat(event_records, dim="time")

    # Filter July–August
    base_jul_aug = base.sel(time=base.time.dt.month.isin([7, 8]))
    event_jul_aug = event.sel(time=event.time.dt.month.isin([7, 8]))

    base_mean = base_jul_aug.mean("time")
    event_mean = event_jul_aug.mean("time")
    delta = event_mean - base_mean

    base_mean.to_dataset(name="NDVI_base_mean").to_netcdf(OUT_BASE)
    event_mean.to_dataset(name="NDVI_event_mean").to_netcdf(OUT_EVENT)
    delta.name = "NDVI_delta_jul_aug"
    delta.to_dataset(name="NDVI_delta_jul_aug").to_netcdf(OUT_DELTA)
    print(f"Wrote {OUT_BASE}, {OUT_EVENT}, {OUT_DELTA}")


if __name__ == "__main__":
    main()
