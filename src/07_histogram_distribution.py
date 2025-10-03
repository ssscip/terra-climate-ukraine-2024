"""Build histogram distributions for baseline vs event LST if data present."""
from __future__ import annotations

from pathlib import Path
import csv
import numpy as np
import xarray as xr

BASELINE_PATH = Path("data_products/lst_baseline_daily.nc")  # Prefer full baseline daily stack if available.
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

    # Baseline distribution: use daily baseline stack if present
    if BASELINE_PATH.exists():
        base_ds = xarray_open(BASELINE_PATH)
        base_var = None
        for cand in ["LST_baseline_daily", "LST_climatology", "LST_Day_1km"]:
            if cand in base_ds:
                base_var = base_ds[cand]
                break
        if base_var is None:
            print("No suitable baseline variable.")
            hist_base = [0] * len(hist_event)
            base_vals = np.array([])
        else:
            if "time" in base_var.coords:
                # Restrict to July-Aug to match event window
                base_sub = base_var.sel(time=base_var.time.dt.month.isin([7, 8]))
            else:
                base_sub = base_var
            base_vals = base_sub.values.ravel()
            base_vals = base_vals[~np.isnan(base_vals)]
            hist_base, _ = np.histogram(base_vals, bins=bins)
    else:
        print("No baseline distribution available; writing event only.")
        hist_base = [0] * len(hist_event)
        base_vals = np.array([])

    # Compute distribution shift metrics (mean shift, tail shift 95-99th)
    mean_shift = ""
    tail_shift = ""
    if base_vals.size > 0:
        mean_shift = float(np.nanmean(arr_event) - np.nanmean(base_vals))
        # Tail shift: difference between mean of top 5% for event and baseline
        def tail_mean(arr):
            if arr.size == 0:
                return np.nan
            thresh = np.percentile(arr, 95)
            return np.nanmean(arr[arr >= thresh])
        tm_event = tail_mean(arr_event)
        tm_base = tail_mean(base_vals)
        tail_shift = float(tm_event - tm_base) if not np.isnan(tm_event) and not np.isnan(tm_base) else ""

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bin_left", "bin_right", "baseline_count", "event_count", "mean_shift", "tail_shift_95p"])
        for i in range(len(hist_event)):
            # Only write mean/tail shift on first row to avoid repetition
            if i == 0:
                writer.writerow([bins[i], bins[i + 1], hist_base[i], hist_event[i], mean_shift, tail_shift])
            else:
                writer.writerow([bins[i], bins[i + 1], hist_base[i], hist_event[i], "", ""])

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
