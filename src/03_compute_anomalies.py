"""Compute 2024 LST anomalies using pre-built climatology."""
from __future__ import annotations

from pathlib import Path
import re
import datetime as dt
import yaml
import xarray as xr
import numpy as np
from modis_io import open_mod11a1_lst

CONFIG_PATH = Path("config.yml")
RAW_DIR = Path("data_raw/MOD11A1")
CLIM_PATH = Path("data_products/lst_climatology.nc")
OUT_EVENT = Path("data_products/lst_event.nc")
OUT_ANOM = Path("data_products/lst_anomaly_event.nc")

DATE_RE = re.compile(r"A(\d{4})(\d{3})")

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


def open_event_lst(path: Path, scale_factor: float):
    da = open_mod11a1_lst(path, scale_factor)
    if da is None:
        return None
    d = extract_date(path.name)
    if d is None:
        return None
    return da.expand_dims(time=[np.datetime64(d)])


def main():
    cfg = parse_config()
    event_year = cfg["event_year"]
    scale = cfg["thresholds"]["lst_scale_factor"]
    clim_ds = xr.open_dataset(CLIM_PATH)
    if "LST_climatology" in clim_ds:
        clim = clim_ds["LST_climatology"]
    else:
        # Allow alternative naming fallback
        clim_var = list(clim_ds.data_vars)[0]
        clim = clim_ds[clim_var]

    files = sorted(RAW_DIR.glob("*.hdf"))
    records = []
    for fp in files:
        d = extract_date(fp.name)
        if d and d.year == event_year:
            da = open_event_lst(fp, scale)
            if da is not None:
                records.append(da)
    if not records:
        print("No event year data found.")
        return

    event = xr.concat(records, dim="time")
    event["doy"] = ("time", event["time"].dt.dayofyear)
    # Align with climatology by DOY
    anom = event.groupby("doy") - clim
    event.to_dataset(name="LST_event").to_netcdf(OUT_EVENT)
    anom.name = "LST_anomaly"
    anom.to_dataset(name="LST_anomaly").to_netcdf(OUT_ANOM)
    print(f"Wrote {OUT_EVENT} and {OUT_ANOM}")


if __name__ == "__main__":
    main()
