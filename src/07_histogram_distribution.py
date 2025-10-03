"""Build histogram distributions for baseline vs event LST if data present."""
from __future__ import annotations

from pathlib import Path
import csv
import numpy as np
import xarray as xr

BASELINE_PATH = Path("data_products/lst_climatology.nc")  # Ideally raw baseline, but we only have climatology.
EVENT_PATH = Path("data_products/lst_event.nc")
OUT_CSV = Path("docs/distribution_histogram.csv")


def main():
    if not EVENT_PATH.exists():
        print("Missing event LST: run 03_compute_anomalies.py")
        return
    # We only have climatology mean per DOY, not full baseline distribution -> limited histogram.
    event = xarray_open(EVENT_PATH)
    if event is None:
        return

    lst_event = None
    for cand in ["LST_event", "LST_Day", "LST_Day_1km"]:
        if cand in event:
            lst_event = event[cand]
            break
    if lst_event is None:
        print("No LST variable found in event dataset.")
        return

    # Flatten ignoring NaNs
    arr_event = lst_event.values.ravel()
    arr_event = arr_event[~np.isnan(arr_event)]

    hist_event, bins = np.histogram(arr_event, bins=50)

    # Placeholder baseline: use climatology values aggregated
    if BASELINE_PATH.exists():
        clim = xarray_open(BASELINE_PATH)
        lst_clim = clim["LST_climatology"]
        clim_vals = lst_clim.values.ravel()
        clim_vals = clim_vals[~np.isnan(clim_vals)]
        hist_base, _ = np.histogram(clim_vals, bins=bins)
    else:
        print("No baseline distribution available; writing event only.")
        hist_base = [""] * len(hist_event)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bin_left", "bin_right", "baseline_count", "event_count"])
        for i in range(len(hist_event)):
            writer.writerow([bins[i], bins[i + 1], hist_base[i] if hist_base[i] != "" else "", hist_event[i]])

    print(f"Wrote histogram {OUT_CSV}")


def xarray_open(path: Path):
    try:
        return xarray_lazy_open(path)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to open {path}: {e}")
        return None


def xarray_lazy_open(path: Path):  # separate to allow patching
    return xr.open_dataset(path)


if __name__ == "__main__":
    main()
