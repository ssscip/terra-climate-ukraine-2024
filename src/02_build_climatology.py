"""Build day-of-year LST climatology from MOD11A1 baseline years.

Expects MOD11A1 HDF files in data_raw/MOD11A1 with filenames containing 'A{YYYY}{DDD}'.
Outputs NetCDF: data_products/lst_climatology.nc
"""
from __future__ import annotations

import re
from pathlib import Path
import datetime as dt
import yaml
import xarray as xr
import numpy as np
from modis_io import open_mod11a1_lst

CONFIG_PATH = Path("config.yml")
RAW_DIR = Path("data_raw/MOD11A1")
OUT_PATH = Path("data_products/lst_climatology.nc")
BASELINE_DAILY_PATH = Path("data_products/lst_baseline_daily.nc")

def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)

DATE_RE = re.compile(r"A(\d{4})(\d{3})")


def extract_date(fname: str) -> dt.date | None:
    m = DATE_RE.search(fname)
    if not m:
        return None
    year = int(m.group(1))
    doy = int(m.group(2))
    return dt.date.fromordinal(dt.date(year, 1, 1).toordinal() + doy - 1)


def read_lst(path: Path, scale_factor: float) -> xr.DataArray | None:
    da = open_mod11a1_lst(path, scale_factor)
    if da is None:
        return None
    date = extract_date(path.name)
    if date is None:
        return None
    da = da.expand_dims(time=[np.datetime64(date)])
    return da


def main():
    cfg = parse_config()
    start = cfg["baseline"]["start_year"]
    end = cfg["baseline"]["end_year"]
    scale = cfg["thresholds"]["lst_scale_factor"]

    files = sorted(RAW_DIR.glob("*.hdf"))
    if not files:
        print("No MOD11A1 files found. Populate data_raw/MOD11A1.")
        return

    records = []
    for fp in files:
        d = extract_date(fp.name)
        if d and start <= d.year <= end:
            da = read_lst(fp, scale)
            if da is not None:
                records.append(da)

    if not records:
        print("No baseline year data opened.")
        return

    combined = xr.concat(records, dim="time")
    combined["doy"] = ("time", combined["time"].dt.dayofyear)
    clim = combined.groupby("doy").mean("time", keep_attrs=True)
    clim.name = "LST_climatology"
    clim.to_dataset(name="LST_climatology").to_netcdf(OUT_PATH)
    # Also persist raw baseline daily stack for percentile calculations
    combined.to_dataset(name="LST_baseline_daily").to_netcdf(BASELINE_DAILY_PATH)
    print(f"Wrote climatology {OUT_PATH} and baseline daily {BASELINE_DAILY_PATH}")


if __name__ == "__main__":
    main()
