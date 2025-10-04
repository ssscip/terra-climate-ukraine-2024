#!/usr/bin/env python
"""Build an interactive portal HTML with:
- Global anomaly dot layer (synthetic or real) from data_products/global_month_anomaly.nc
- Marker for Ukraine (centroid of roi/ukraine.geojson)
- Marker for Zaporizhzhia (centroid of roi/zaporizhzhia.geojson) with popup linking to chronology video or page
- Optional creation of a simple chronology page that lists frames or embeds a video.

Outputs (by default):
  output/portal/index.html
  output/portal/chronology_zaporizhzhia.html (if chronology assets present)

CLI:
  python scripts/12_build_portal.py \
      --global-anom data_products/global_month_anomaly.nc \
      --chronology-dir output/chronology_real \
      --out-dir output/portal

If chronology video exists (chronology.mp4) it will be copied into assets and embedded.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import shutil
import numpy as np
import xarray as xr
import folium
from shapely.geometry import shape

DEFAULT_GLOBAL = Path("data_products/global_month_anomaly.nc")
ROI_UA = Path("roi/ukraine.geojson")
ROI_ZP = Path("roi/zaporizhzhia.geojson")


def load_centroid(path: Path):
    with path.open("r", encoding="utf-8") as f:
        geo = json.load(f)
    geom = shape(geo["features"][0]["geometry"])
    c = geom.centroid
    return float(c.y), float(c.x)


def build_global_layer(m: folium.Map, ds: xr.Dataset, var_name: str):
    da = ds[var_name]
    lats = da["lat"].values
    lons = da["lon"].values
    data = da.values
    # Downsample adaptively (rough grid targeting ~8k points max)
    step_lat = max(1, len(lats) // 120)
    step_lon = max(1, len(lons) // 240)
    for i in range(0, len(lats), step_lat):
        for j in range(0, len(lons), step_lon):
            val = float(data[i, j])
            if np.isnan(val):
                continue
            color = "#cccccc"
            if val > 3:
                color = "#8b0000"
            elif val > 2:
                color = "#ff0000"
            elif val > 1:
                color = "#ff8c00"
            elif val < -2:
                color = "#0000cd"
            elif val < -1:
                color = "#1e90ff"
            folium.CircleMarker(
                location=[float(lats[i]), float(lons[j])],
                radius=3,
                color=color,
                fill=True,
                fill_opacity=0.85,
                weight=0,
                popup=f"{var_name}: {val:+.2f} K",
            ).add_to(m)


def chronology_assets(src_dir: Path, dest_dir: Path):
    if not src_dir.exists():
        return None, []
    video = src_dir / "chronology.mp4"
    frames = sorted(src_dir.glob("frame_*.png"))
    assets_dir = dest_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    copied_video = None
    if video.exists():
        copied_video = assets_dir / "chronology_zaporizhzhia.mp4"
        shutil.copy2(video, copied_video)
    # Limit frames for portal page preview (e.g., first 20)
    selected_frames = frames[:20]
    copied_frames = []
    for fr in selected_frames:
        tgt = assets_dir / fr.name
        shutil.copy2(fr, tgt)
        copied_frames.append(tgt.name)
    return copied_video, copied_frames


def build_chronology_page(out_dir: Path, video_path: Path | None, frame_names: list[str]):
    html_path = out_dir / "chronology_zaporizhzhia.html"
    parts = ["<html><head><meta charset='utf-8'><title>Zaporizhzhia Heat Chronology</title>"
             "<style>body{font-family:Arial;margin:1rem;} .frames{display:flex;flex-wrap:wrap;gap:4px;} .frames img{width:180px;border:1px solid #ccc;} video{max-width:640px;width:100%;}</style>"
             "</head><body><h1>Zaporizhzhia Heat Chronology (Summer 2024)</h1>"]
    if video_path:
        parts.append(f"<h2>Video</h2><video controls src='assets/{video_path.name}'></video>")
    if frame_names:
        parts.append("<h2>Sample Frames</h2><div class='frames'>")
        for fn in frame_names:
            parts.append(f"<img src='assets/{fn}' loading='lazy'>")
        parts.append("</div>")
    parts.append("<p>Data: MODIS LST anomalies relative to 2010–2019 baseline.</p>")
    parts.append("</body></html>")
    html_path.write_text("".join(parts), encoding="utf-8")
    return html_path


def build_portal(global_anom: Path, chronology_dir: Path, out_dir: Path, var_name: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    if not global_anom.exists():
        print(f"Global anomaly file missing: {global_anom}")
        ds = None
    else:
        ds = xr.open_dataset(global_anom)
        if var_name not in ds:
            print(f"Variable {var_name} not in dataset; available: {list(ds.data_vars)}")
            ds = None

    if ds is None:
        # fallback empty map
        m = folium.Map(location=[20, 10], zoom_start=2, tiles="cartodbpositron")
    else:
        m = folium.Map(location=[25, 15], zoom_start=2, tiles="cartodbpositron")
        build_global_layer(m, ds, var_name)

    # Chronology assets
    video_path, frame_names = chronology_assets(chronology_dir, out_dir)
    chrono_page = None
    if video_path or frame_names:
        chrono_page = build_chronology_page(out_dir, video_path, frame_names)

    # ROI markers
    if ROI_UA.exists():
        lat_u, lon_u = load_centroid(ROI_UA)
        popup_html = "<b>Ukraine</b><br>Click Zaporizhzhia marker for heat chronology."  # Placeholder
        folium.Marker(location=[lat_u, lon_u], tooltip="Ukraine", popup=folium.Popup(popup_html, max_width=250)).add_to(m)
    if ROI_ZP.exists():
        lat_z, lon_z = load_centroid(ROI_ZP)
        if chrono_page:
            popup_html = ("<b>Zaporizhzhia Heat 2024</b><br>"
                          "<a href='chronology_zaporizhzhia.html' target='_blank'>Open chronology</a>")
        else:
            popup_html = "<b>Zaporizhzhia</b><br>No chronology assets yet."
        folium.Marker(location=[lat_z, lon_z], icon=folium.Icon(color="red", icon="fire", prefix="fa"),
                      tooltip="Zaporizhzhia heatwave", popup=folium.Popup(popup_html, max_width=260)).add_to(m)

    index_html = out_dir / "index.html"
    m.save(str(index_html))
    print(f"Portal index: {index_html}")
    if chrono_page:
        print(f"Chronology page: {chrono_page}")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--global-anom", default=str(DEFAULT_GLOBAL))
    ap.add_argument("--var", default="LST_global_anomaly")
    ap.add_argument("--chronology-dir", default="output/chronology_real")
    ap.add_argument("--out-dir", default="output/portal")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_portal(Path(args.global_anom), Path(args.chronology_dir), Path(args.out_dir), args.var)
