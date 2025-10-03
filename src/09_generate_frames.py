"""Generate PNG frames for Ukraine LST anomalies July–August."""
from __future__ import annotations

from pathlib import Path
import yaml
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

from utils_io import load_geojson, make_mask, apply_mask

CONFIG_PATH = Path("config.yml")
ANOM_PATH = Path("data_products/lst_anomaly_event.nc")
OUT_DIR = Path("output/frames_local")
ROI_FILE = Path("roi/ukraine.geojson")


def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def main():
    cfg = parse_config()
    if not ANOM_PATH.exists():
        print("Missing anomaly file. Run 03_compute_anomalies.py")
        return
    ds = xarray_open(ANOM_PATH)
    if ds is None:
        return

    if "LST_anomaly" in ds:
        da = ds["LST_anomaly"]
    else:
        # fall back to event
        for cand in ["LST_event", "LST_Day"]:
            if cand in ds:
                da = ds[cand]
                break
        else:
            print("No anomaly or event variable found")
            return

    if "time" not in da.coords:
        print("No time coordinate in anomaly data")
        return

    # July–August subset
    da_sub = da.sel(time=da.time.dt.month.isin([7, 8]))

    if ROI_FILE.exists():
        geo = load_geojson(ROI_FILE)
        lon_name = "lon" if "lon" in da_sub.coords else ("x" if "x" in da_sub.coords else None)
        lat_name = "lat" if "lat" in da_sub.coords else ("y" if "y" in da_sub.coords else None)
        if lon_name and lat_name:
            mask = make_mask(da_sub.to_dataset(name="LST_anomaly"), geo, lon_name=lon_name, lat_name=lat_name)
            da_sub = apply_mask(da_sub, mask)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    vmin, vmax = -5, 8
    for t in da_sub.time.values:
        frame = da_sub.sel(time=t)
        date_str = np.datetime_as_string(t, unit="D")
        plt.figure(figsize=(6, 5))
        im = frame.plot(cmap="coolwarm", vmin=vmin, vmax=vmax, add_colorbar=True)
        # Ensure colorbar label is set to Kelvin
        if hasattr(im, 'colorbar') and im.colorbar:
            im.colorbar.set_label("K")
        plt.title(f"LST Anomaly {date_str}")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        out_file = OUT_DIR / f"frame_{date_str}.png"
        plt.savefig(out_file, dpi=120)
        plt.close()
    print(f"Frames written to {OUT_DIR}")


def xarray_open(path: Path):
    try:
        return xr.open_dataset(path)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to open {path}: {e}")
        return None


if __name__ == "__main__":
    main()
