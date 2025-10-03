"""Compute selected metrics and update docs/metrics.csv."""
from __future__ import annotations

from pathlib import Path
import csv
import json
import yaml
import numpy as np
import xarray as xr
from shapely.geometry import shape

from utils_io import load_geojson, make_mask, apply_mask

CONFIG_PATH = Path("config.yml")
METRICS_CSV = Path("docs/metrics.csv")
LST_ANOM = Path("data_products/lst_anomaly_event.nc")
LST_EVENT = Path("data_products/lst_event.nc")
NDVI_DELTA = Path("data_products/ndvi_delta_jul_aug.nc")
BASELINE_DAILY = Path("data_products/lst_baseline_daily.nc")
ROI_DIR = Path("roi")


def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def load_dataset(path: Path):
    if not path.exists():
        print(f"Missing dataset {path}")
        return None
    try:
        return xr.open_dataset(path)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to open {path}: {e}")
        return None


def read_metrics_csv(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def write_metrics_csv(path: Path, rows):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def update_metric(rows, metric_name, value):
    for r in rows:
        if r["metric"] == metric_name:
            r["value"] = value
            return
    print(f"Metric {metric_name} not found in CSV template.")


def compute_mean_lst_anomaly(anom_ds):
    for cand in ["LST_anomaly", "LST_event"]:
        if cand in anom_ds:
            da = anom_ds[cand]
            break
    else:
        print("No anomaly variable found")
        return None
    # July-Aug subset if time coordinate exists
    if "time" in da.coords:
        da_jul_aug = da.sel(time=da.time.dt.month.isin([7, 8]))
    else:
        da_jul_aug = da
    return float(da_jul_aug.mean().values)


def compute_baseline_threshold(baseline_ds, roi_geo, percentile=95):
    if baseline_ds is None:
        return None
    da = None
    for cand in ["LST_baseline_daily", "LST_Day", "LST_Day_1km", "LST_event"]:
        if cand in baseline_ds:
            da = baseline_ds[cand]
            break
    if da is None or "time" not in da.coords:
        return None
    # Subset July-Aug
    da_jul_aug = da.sel(time=da.time.dt.month.isin([7, 8]))
    # Mask ROI
    lon_name = "lon" if "lon" in da_jul_aug.coords else ("x" if "x" in da_jul_aug.coords else None)
    lat_name = "lat" if "lat" in da_jul_aug.coords else ("y" if "y" in da_jul_aug.coords else None)
    if lon_name and lat_name and roi_geo is not None:
        mask = make_mask(da_jul_aug.to_dataset(name="baseline"), roi_geo, lon_name=lon_name, lat_name=lat_name)
        da_jul_aug = apply_mask(da_jul_aug, mask)
    vals = da_jul_aug.values.ravel()
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return None
    return float(np.percentile(vals, percentile))


def compute_heat_days(event_ds, roi_geo, threshold):
    if threshold is None:
        return None
    da = None
    for cand in ["LST_event", "LST_Day", "LST_Day_1km"]:
        if cand in event_ds:
            da = event_ds[cand]
            break
    if da is None or "time" not in da.coords:
        return None
    da_jul_aug = da.sel(time=da.time.dt.month.isin([7, 8]))
    lon_name = "lon" if "lon" in da_jul_aug.coords else ("x" if "x" in da_jul_aug.coords else None)
    lat_name = "lat" if "lat" in da_jul_aug.coords else ("y" if "y" in da_jul_aug.coords else None)
    if lon_name and lat_name and roi_geo is not None:
        mask = make_mask(da_jul_aug.to_dataset(name="event"), roi_geo, lon_name=lon_name, lat_name=lat_name)
        da_jul_aug = apply_mask(da_jul_aug, mask)
    count = (da_jul_aug > threshold).sum().item()
    return int(count)


def load_roi(name: str):
    path_map = {
        "ukraine": "ukraine.geojson",
        "zaporizhzhia": "zaporizhzhia.geojson",
    }
    for key, fname in path_map.items():
        if name.startswith(key):
            full = ROI_DIR / fname
            if full.exists():
                return load_geojson(full)
    print(f"ROI {name} not found (expected file in roi/)")
    return None


def mask_mean(ds, var_name, roi_geo):
    if var_name not in ds:
        return None
    da = ds[var_name]
    # guess lon/lat names
    lon_name = "lon" if "lon" in da.coords else ("x" if "x" in da.coords else None)
    lat_name = "lat" if "lat" in da.coords else ("y" if "y" in da.coords else None)
    if not lon_name or not lat_name:
        print("Could not identify lon/lat coords")
        return None
    mask = make_mask(da.to_dataset(name=var_name), roi_geo, lon_name=lon_name, lat_name=lat_name)
    da_masked = apply_mask(da, mask)
    return float(da_masked.mean().values)


def main():
    cfg = parse_config()
    rows = read_metrics_csv(METRICS_CSV)

    anom_ds = load_dataset(LST_ANOM)
    event_ds = load_dataset(LST_EVENT)
    ndvi_delta = load_dataset(NDVI_DELTA)
    baseline_daily = load_dataset(BASELINE_DAILY)

    # Metric: mean LST anomaly Ukraine
    uk_geo = load_roi("ukraine")
    if anom_ds is not None and uk_geo is not None:
        mean_anom = compute_mean_lst_anomaly(anom_ds)
        update_metric(rows, "mean_LST_anomaly_ukraine", f"{mean_anom:.2f}" if mean_anom is not None else "")

    # Heat days Zaporizhzhia (placeholder)
    zap_geo = load_roi("zaporizhzhia")
    if event_ds is not None and zap_geo is not None:
        threshold = compute_baseline_threshold(baseline_daily, zap_geo, percentile=cfg["thresholds"].get("heat_percentile", 95))
        if threshold is not None:
            heat_days = compute_heat_days(event_ds, zap_geo, threshold)
            update_metric(rows, "heat_days_zaporizhzhia", str(heat_days) if heat_days is not None else "")
        else:
            print("Could not compute baseline threshold for heat days.")

    # NDVI delta
    if ndvi_delta is not None:
        for cand in ["NDVI_delta_jul_aug", "NDVI_delta", "delta"]:
            if cand in ndvi_delta:
                val = float(ndvi_delta[cand].mean().values)
                update_metric(rows, "delta_ndvi", f"{val:.4f}")
                break

    write_metrics_csv(METRICS_CSV, rows)
    print(f"Updated metrics {METRICS_CSV}")


if __name__ == "__main__":
    main()
