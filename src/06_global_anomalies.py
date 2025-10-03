"""Compute global (or regional) monthly anomaly using MOD11C1 if available.

Logic:
1. Discover MOD11C1 files in `data_raw/MOD11C1`.
2. Parse year & day-of-year (or assume monthly aggregates if already monthly files).
3. Build baseline monthly mean for configured baseline years.
4. Extract event year month, compute anomaly (event_month - baseline_mean_month).
5. Output NetCDF + optional quick PNG.

Fallback / Synthetic:
If `--synthetic` flag is provided (or no files found), generate a coarse 1° global grid with
baseline field + anomaly patch over Europe / Mediterranean.
"""
from __future__ import annotations

from pathlib import Path
import yaml
import xarray as xr
import numpy as np
import re
import argparse
import matplotlib.pyplot as plt

CONFIG_PATH = Path("config.yml")
RAW_DIR = Path("data_raw/MOD11C1")
OUT_PATH = Path("data_products/global_month_anomaly.nc")
PNG_OUT = Path("output/frames_global/global_month_anomaly.png")

DATE_RE = re.compile(r"A(\d{4})(\d{3})")  # similar pattern if daily files


def extract_date(fname: str):
    m = DATE_RE.search(fname)
    if not m:
        return None
    year = int(m.group(1)); doy = int(m.group(2))
    base = np.datetime64(f"{year}-01-01") + np.timedelta64(doy - 1, 'D')
    return base


def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def synthetic_global(cfg):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lons = np.arange(-180, 180.1, 1.0)
    lats = np.arange(-60, 81, 1.0)
    # Baseline mean ~ 290K with latitudinal gradient
    lat_grad = 290 - 0.3 * (np.abs(lats[:, None]))
    base = lat_grad + np.random.normal(0, 0.4, lat_grad.shape)
    # Event anomaly patch over Europe (lon 0–40, lat 35–55)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    anomaly_pattern = np.exp(-(((lon_grid - 20) ** 2) / 400 + ((lat_grid - 45) ** 2) / 150)) * 4.0
    event = base + anomaly_pattern
    anomaly = event - base
    ds = xr.Dataset({
        "LST_global_baseline_mean": ("lat", "lon", base.astype("float32")),
        "LST_global_event": ("lat", "lon", event.astype("float32")),
        "LST_global_anomaly": ("lat", "lon", anomaly.astype("float32")),
    }, coords={"lat": lats, "lon": lons})
    ds.to_netcdf(OUT_PATH)
    print(f"Wrote synthetic global anomaly {OUT_PATH}")
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9,4))
    anomaly_da = ds["LST_global_anomaly"]
    im = anomaly_da.plot(cmap="coolwarm", vmin=-3, vmax=5, add_colorbar=True)
    if hasattr(im, 'colorbar') and im.colorbar:
        im.colorbar.set_label('K')
    plt.title("Synthetic Global Anomaly (Monthly)")
    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=120)
    plt.close()
    return True


def compute_real_global(cfg, month: int):
    files = sorted(RAW_DIR.glob("*.nc"))
    if not files:
        return False
    # Open multi-file dataset (may be daily)
    ds = xr.open_mfdataset(files, combine="by_coords")
    # Attempt to find LST variable
    lst_var = None
    for cand in ["LST_Day_CMG", "LST_Day", "LST_Day_1km", "LST"]:
        if cand in ds:
            lst_var = ds[cand]
            break
    if lst_var is None:
        print("Could not find LST variable in MOD11C1 files.")
        return False
    if "time" not in lst_var.coords:
        print("Expected time dimension in MOD11C1 data.")
        return False
    cfg_base = cfg["baseline"]
    base_years = [y for y in range(cfg_base["start_year"], cfg_base["end_year"] + 1)]
    event_year = cfg["event_year"]
    # Subset month
    subset = lst_var.sel(time=lst_var.time.dt.month == month)
    base_subset = subset.sel(time=subset.time.dt.year.isin(base_years))
    event_subset = subset.sel(time=subset.time.dt.year == event_year)
    if event_subset.time.size == 0 or base_subset.time.size == 0:
        print("Insufficient data for selected month.")
        return False
    baseline_mean = base_subset.mean("time")
    event_mean = event_subset.mean("time")
    anomaly = event_mean - baseline_mean
    ds_out = xr.Dataset({
        "LST_global_baseline_mean": baseline_mean,
        "LST_global_event_mean": event_mean,
        "LST_global_anomaly": anomaly,
    })
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ds_out.to_netcdf(OUT_PATH)
    print(f"Wrote global anomaly {OUT_PATH}")
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9,4))
    im = anomaly.plot(cmap="coolwarm", vmin=-5, vmax=8, add_colorbar=True)
    if hasattr(im, 'colorbar') and im.colorbar:
        im.colorbar.set_label('K')
    plt.title(f"Global LST Anomaly Month={month}")
    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=120)
    plt.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Compute or synthesize global monthly anomaly (MOD11C1)")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic global anomaly")
    args = parser.parse_args()
    cfg = parse_config()
    month = cfg["periods"]["global_focus_month"]
    if args.synthetic:
        synthetic_global(cfg)
        return
    ok = compute_real_global(cfg, month)
    if not ok:
        print("Falling back to synthetic global anomaly (no real MOD11C1 data).")
        synthetic_global(cfg)


if __name__ == "__main__":
    main()
