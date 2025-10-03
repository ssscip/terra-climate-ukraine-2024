"""Generate synthetic demo datasets so the pipeline can be viewed without real MODIS downloads.

Creates (all in data_products/):
  - lst_baseline_daily.nc (LST_baseline_daily variable)
  - lst_climatology.nc (LST_climatology variable grouped by DOY)
  - lst_event.nc (LST_event variable for Jul–Aug 2024)
  - lst_anomaly_event.nc (LST_anomaly variable)
  - ndvi_base_mean.nc / ndvi_event_mean.nc / ndvi_delta_jul_aug.nc
  - mndwi_mean_baseline_jul_aug.nc / mndwi_mean_event_jul_aug.nc / mndwi_delta_jul_aug.nc

Also optionally runs metrics & frame generation if flags are set.

Usage:
  python scripts/demo_generate_mock_data.py --run-metrics --make-frames

The synthetic grid roughly spans Ukraine (lon 20–44E, lat 40–56N) so ROI masks work.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import xarray as xr
import datetime as dt
import subprocess
import sys

DATA_PROD = Path("data_products")
DATA_PROD.mkdir(parents=True, exist_ok=True)


def build_grid():
    lon = np.arange(20.0, 44.01, 0.25, dtype="float32")  # ~96 cols
    lat = np.arange(40.0, 56.01, 0.25, dtype="float32")  # ~64 rows
    return lon, lat


def generate_baseline(years=range(2010, 2020)):
    lon, lat = build_grid()
    # Daily time index for all baseline years (ignore leap day for simplicity)
    dates = []
    for y in years:
        start = dt.date(y, 1, 1)
        for d in range(365):
            dates.append(start + dt.timedelta(days=d))
    time = np.array(dates, dtype="datetime64[D]")
    L = lon[None, None, :]
    T = lat[None, :, None]
    # Base seasonal cycle (sinusoidal) + spatial gradient + noise
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    seasonal = 290 + 10 * np.sin(2 * np.pi * (day_of_year - 180) / 365)  # K
    seasonal = seasonal[:, None, None]
    spatial = 0.5 * (T - 48) + 0.3 * (L - 32)
    noise = np.random.normal(0, 0.8, size=(time.size, lat.size, lon.size))
    data = seasonal + spatial + noise
    da = xr.DataArray(
        data.astype("float32"),
        coords={"time": time, "lat": lat, "lon": lon},
        dims=("time", "lat", "lon"),
        name="LST_baseline_daily",
        attrs={"units": "K", "description": "Synthetic baseline daily LST"},
    )
    # Write baseline daily
    da.to_dataset(name="LST_baseline_daily").to_netcdf(DATA_PROD / "lst_baseline_daily.nc")
    # Climatology by DOY
    doy = xr.DataArray(day_of_year, coords={"time": time}, dims="time")
    da_doy = da.assign_coords(doy=("time", doy))
    clim = da_doy.groupby("doy").mean("time")
    clim.name = "LST_climatology"
    clim.to_dataset(name="LST_climatology").to_netcdf(DATA_PROD / "lst_climatology.nc")


def generate_event(year=2024):
    lon, lat = build_grid()
    # Event period July 1 – Aug 31
    start = dt.date(year, 7, 1)
    end = dt.date(year, 8, 31)
    num_days = (end - start).days + 1
    dates = [start + dt.timedelta(days=i) for i in range(num_days)]
    time = np.array(dates, dtype="datetime64[D]")
    # Load climatology to reconstruct expected values
    clim = xr.open_dataset(DATA_PROD / "lst_climatology.nc")["LST_climatology"]
    # Map each date to DOY and sample climatology
    doy_vals = np.array([d.timetuple().tm_yday for d in dates])
    # handle DOY indexing: climatology dims 'doy'
    base_stack = []
    for doy in doy_vals:
        base_stack.append(clim.sel(doy=doy).values)
    base_arr = np.stack(base_stack, axis=0)
    # Add a localized heat anomaly patch
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    patch = np.exp(-(((lon_grid - 34) ** 2) / 10 + ((lat_grid - 49) ** 2) / 6)) * 5.0  # up to +5K
    event = base_arr + patch[None, :, :] + np.random.normal(0, 0.6, base_arr.shape)
    da_event = xr.DataArray(
        event.astype("float32"),
        coords={"time": time, "lat": lat, "lon": lon},
        dims=("time", "lat", "lon"),
        name="LST_event",
        attrs={"units": "K", "description": "Synthetic event LST (with heat anomaly)"},
    )
    da_event.to_dataset(name="LST_event").to_netcdf(DATA_PROD / "lst_event.nc")
    # Anomaly: event - climatology
    # Align by DOY
    doy_da = xr.DataArray(doy_vals, coords={"time": time}, dims="time", name="doy")
    clim_for_event = clim.sel(doy=doy_da)
    anom = da_event - clim_for_event
    anom.name = "LST_anomaly"
    anom.to_dataset(name="LST_anomaly").to_netcdf(DATA_PROD / "lst_anomaly_event.nc")


def generate_ndvi_and_mndwi():
    lon, lat = build_grid()
    # NDVI base mean & event mean over Jul–Aug
    base = 0.6 + 0.05 * np.random.normal(0, 1, (lat.size, lon.size))
    # Event stress: reduce NDVI in center
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    stress = np.exp(-(((lon_grid - 33) ** 2) / 25 + ((lat_grid - 50) ** 2) / 16)) * 0.15
    event = base - stress + 0.01 * np.random.normal(0, 1, (lat.size, lon.size))
    ndvi_base = xr.DataArray(base.astype("float32"), coords={"lat": lat, "lon": lon}, dims=("lat", "lon"), name="NDVI_base_mean_jul_aug")
    ndvi_event = xr.DataArray(event.astype("float32"), coords={"lat": lat, "lon": lon}, dims=("lat", "lon"), name="NDVI_event_mean_jul_aug")
    ndvi_delta = (ndvi_event - ndvi_base).rename("NDVI_delta_jul_aug")
    ndvi_base.to_dataset().to_netcdf(DATA_PROD / "ndvi_base_mean.nc")
    ndvi_event.to_dataset().to_netcdf(DATA_PROD / "ndvi_event_mean.nc")
    ndvi_delta.to_dataset().to_netcdf(DATA_PROD / "ndvi_delta_jul_aug.nc")

    # MNDWI baseline/event (simulate minor water loss)
    base_w = -0.2 + 0.4 * np.exp(-(((lon_grid - 31) ** 2) / 40 + ((lat_grid - 48) ** 2) / 25))
    event_w = base_w - 0.05 * np.exp(-(((lon_grid - 31) ** 2) / 20 + ((lat_grid - 48) ** 2) / 12))
    m_base = xr.DataArray(base_w.astype("float32"), coords={"lat": lat, "lon": lon}, dims=("lat", "lon"), name="MNDWI_base_mean_jul_aug")
    m_event = xr.DataArray(event_w.astype("float32"), coords={"lat": lat, "lon": lon}, dims=("lat", "lon"), name="MNDWI_event_mean_jul_aug")
    m_delta = (m_event - m_base).rename("MNDWI_delta_jul_aug")
    m_base.to_dataset().to_netcdf(DATA_PROD / "mndwi_mean_baseline_jul_aug.nc")
    m_event.to_dataset().to_netcdf(DATA_PROD / "mndwi_mean_event_jul_aug.nc")
    m_delta.to_dataset().to_netcdf(DATA_PROD / "mndwi_delta_jul_aug.nc")


def run_metrics():
    print("Running metrics script...")
    subprocess.run([sys.executable, "src/08_metrics.py"], check=False)


def run_frames():
    print("Generating frames...")
    subprocess.run([sys.executable, "src/09_generate_frames.py"], check=False)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic demo data for Terra Climate Extremes project")
    parser.add_argument("--run-metrics", action="store_true", help="Run metrics script after generating data")
    parser.add_argument("--make-frames", action="store_true", help="Generate frames after data generation")
    args = parser.parse_args()

    print("Creating synthetic baseline...")
    generate_baseline()
    print("Creating synthetic event data...")
    generate_event()
    print("Creating synthetic NDVI & MNDWI products...")
    generate_ndvi_and_mndwi()

    if args.run_metrics:
        run_metrics()
    if args.make_frames:
        run_frames()
    print("Demo data generation complete. View frames in output/frames_local (if generated).")


if __name__ == "__main__":
    main()
