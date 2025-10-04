"""Build daily climatology and anomalies from ingested real MODIS LST NetCDF yearly stacks.
Outputs:
  data_products/real_lst_climatology.nc
  data_products/real_lst_anomaly.nc
"""
from __future__ import annotations
import argparse
from pathlib import Path
import xarray as xr
import numpy as np


def open_years(data_dir: str, years):
    files = []
    for y in years:
        f = Path(data_dir)/f"lst_daily_{y}.nc"
        if f.exists():
            files.append(xr.open_dataset(f))
    if not files:
        raise SystemExit("No yearly files found")
    return xr.concat(files, dim="time")


def build_climatology(ds: xr.Dataset, baseline_years):
    base = ds.sel(time=ds.time.dt.year.isin(baseline_years))
    doy = base.time.dt.dayofyear
    base = base.assign_coords(doy=("time", doy.values))
    clim = base.groupby("doy").mean("time", keep_attrs=True)
    return clim


def anomalies(ds: xr.Dataset, clim: xr.Dataset):
    doy_full = ds.time.dt.dayofyear
    ds = ds.assign_coords(doy=("time", doy_full.values))
    clim_full = clim.sel(doy=ds.doy)
    anom = ds["LST"] - clim_full["LST"]
    return anom.to_dataset(name="LST_anomaly")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data_products/real_daily")
    ap.add_argument("--baseline", default="2010-2019")
    ap.add_argument("--event-year", type=int, default=2024)
    ap.add_argument("--out-clim", default="data_products/real_lst_climatology.nc")
    ap.add_argument("--out-anom", default="data_products/real_lst_anomaly.nc")
    args = ap.parse_args()

    start, end = args.baseline.split("-")
    baseline_years = list(range(int(start), int(end) + 1))
    years = baseline_years + [args.event_year]

    ds = open_years(args.data_dir, years)
    clim = build_climatology(ds, baseline_years)
    clim.to_netcdf(args.out_clim)
    anom = anomalies(ds, clim)
    anom.to_netcdf(args.out_anom)
    print("Wrote:", args.out_clim, args.out_anom)


if __name__ == "__main__":
    main()
