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
import math

# Optional: use pyproj if available for better area estimates
try:  # noqa: SIM105
    from pyproj import Geod
    _GEOD = Geod(ellps="WGS84")
except Exception:  # noqa: BLE001
    _GEOD = None

CONFIG_PATH = Path("config.yml")
METRICS_CSV = Path("docs/metrics.csv")
LST_ANOM = Path("data_products/lst_anomaly_event.nc")
LST_EVENT = Path("data_products/lst_event.nc")
NDVI_DELTA = Path("data_products/ndvi_delta_jul_aug.nc")
BASELINE_DAILY = Path("data_products/lst_baseline_daily.nc")
MNDWI_BASE = Path("data_products/mndwi_mean_baseline_jul_aug.nc")
MNDWI_EVENT = Path("data_products/mndwi_mean_event_jul_aug.nc")
MNDWI_DELTA = Path("data_products/mndwi_delta_jul_aug.nc")
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
        "water_body": "water_body.geojson",
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
    mndwi_base_ds = load_dataset(MNDWI_BASE)
    mndwi_event_ds = load_dataset(MNDWI_EVENT)
    mndwi_delta_ds = load_dataset(MNDWI_DELTA)

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

    # Water (MNDWI) delta area (km2) using threshold & water_body ROI
    water_geo = load_roi("water_body")
    mndwi_threshold = cfg["thresholds"].get("mndwi_water", 0.3)

    def _extract_da(ds, candidates):
        if ds is None:
            return None
        for c in candidates:
            if c in ds:
                return ds[c]
        # fallback first var
        if len(ds.data_vars):
            first = list(ds.data_vars)[0]
            return ds[first]
        return None

    base_mndwi = _extract_da(mndwi_base_ds, ["MNDWI_base_mean_jul_aug", "MNDWI_base_mean"])  # type: ignore
    event_mndwi = _extract_da(mndwi_event_ds, ["MNDWI_event_mean_jul_aug", "MNDWI_event_mean"])  # type: ignore

    def estimate_pixel_area_km2(da):
        # Prefer lon/lat in degrees
        lon_name = None
        lat_name = None
        for cand in ["lon", "x"]:
            if cand in da.coords:
                lon_name = cand
                break
        for cand in ["lat", "y"]:
            if cand in da.coords:
                lat_name = cand
                break
        if lon_name in ("x",) and lat_name in ("y",):
            # Assume projected meters
            xs = da[lon_name].values
            ys = da[lat_name].values
            if xs.size < 2 or ys.size < 2:
                return None
            dx = float(np.abs(np.diff(xs)).mean())
            dy = float(np.abs(np.diff(ys)).mean())
            return (dx * dy) / 1e6  # m^2 -> km^2
        if lon_name and lat_name and lon_name != "x" and lat_name != "y":
            lons = da[lon_name].values
            lats = da[lat_name].values
            if lons.size < 2 or lats.size < 2:
                return None
            dlon = float(np.abs(np.diff(lons)).mean())
            dlat = float(np.abs(np.diff(lats)).mean())
            mean_lat = float(np.nanmean(lats))
            # Approximate length of a degree
            km_per_deg_lat = 111.32
            km_per_deg_lon = 111.32 * math.cos(math.radians(mean_lat))
            return dlon * km_per_deg_lon * dlat * km_per_deg_lat
        return None

    def roi_mask(da, geo):
        if geo is None:
            return None
        lon_name = None
        lat_name = None
        for cand in ["lon", "x"]:
            if cand in da.coords:
                lon_name = cand
                break
        for cand in ["lat", "y"]:
            if cand in da.coords:
                lat_name = cand
                break
        if not lon_name or not lat_name:
            return None
        return make_mask(da.to_dataset(name="mndwi"), geo, lon_name=lon_name, lat_name=lat_name)

    if base_mndwi is not None and event_mndwi is not None:
        mask = roi_mask(base_mndwi, water_geo) if water_geo else None
        if mask is not None:
            base_m = apply_mask(base_mndwi, mask)
            event_m = apply_mask(event_mndwi, mask)
        else:
            base_m = base_mndwi
            event_m = event_mndwi
        # Binary classification
        base_water = (base_m > mndwi_threshold)
        event_water = (event_m > mndwi_threshold)
        pixel_area = estimate_pixel_area_km2(base_m)
        if pixel_area is not None:
            base_area = float(base_water.sum().item()) * pixel_area
            event_area = float(event_water.sum().item()) * pixel_area
            delta_area = event_area - base_area
            update_metric(rows, "delta_water_area", f"{delta_area:.2f}")

    write_metrics_csv(METRICS_CSV, rows)
    print(f"Updated metrics {METRICS_CSV}")


if __name__ == "__main__":
    main()
