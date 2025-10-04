#!/usr/bin/env python
"""Build per-event raster derivatives (subset, anomaly rescale, quicklook PNG).
Assumes availability of base anomaly rasters (e.g. data_products/lst_anomaly_event.nc).
For each event id: creates directory globe_assets/<event_id>/ and writes lst_anom.png if LST found.
This is a placeholder focusing on LST anomaly; extend for NDVI, AOD, etc.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import xarray as xr
from PIL import Image

CATALOG = Path("events/catalog/events_enriched.json")
LST_ANOM = Path("data_products/lst_anomaly_event.nc")  # synthetic or real local anomaly
OUT_ROOT = Path("globe_assets")


def load_events():
    with CATALOG.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_anomaly():
    if not LST_ANOM.exists():
        print("Missing anomaly dataset", LST_ANOM)
        return None
    return xr.open_dataset(LST_ANOM)


def subset_point(da, lat, lon, half_deg=2):
    return da.sel(lat=slice(lat - half_deg, lat + half_deg), lon=slice(lon - half_deg, lon + half_deg))


def scale_to_png(arr: np.ndarray, vmin=-5, vmax=8):
    clipped = np.clip(arr, vmin, vmax)
    norm = (clipped - vmin) / (vmax - vmin)
    return (norm * 255).astype("uint8")


def render_png(da, out_path: Path):
    # Take temporal mean for quicklook
    mean_arr = da.mean("time", skipna=True).values
    png_arr = scale_to_png(mean_arr)
    img = Image.fromarray(png_arr, mode="L")
    img.save(out_path)


def process_events(ds, events):
    if "LST_anomaly" not in ds:
        print("Dataset missing LST_anomaly variable")
        return
    for ev in events:
        lat = ev.get("lat")
        lon = ev.get("lon")
        ev_id = ev["id"]
        out_dir = OUT_ROOT / ev_id
        out_dir.mkdir(parents=True, exist_ok=True)
        da = ds["LST_anomaly"]
        try:
            sub = subset_point(da, lat, lon)
            render_png(sub, out_dir / "lst_anom.png")
            # Update event product entry if absent
            if not any(p.get("name") == "MOD11A1" for p in ev.get("products", [])):
                ev.setdefault("products", []).append({
                    "name": "MOD11A1", "variable": "LST_anomaly", "asset": f"globe_assets/{ev_id}/lst_anom.png"
                })
        except Exception as e:  # noqa: BLE001
            print(f"Failed event {ev_id}: {e}")

    # Persist updated catalog
    with CATALOG.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    print("Updated catalog with product assets.")


def main():
    events = load_events()
    ds = load_anomaly()
    if ds is None:
        return
    process_events(ds, events)


if __name__ == "__main__":
    main()
