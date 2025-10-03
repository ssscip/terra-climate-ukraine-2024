"""Generate an interactive HTML map (Folium) of the global anomaly if available.

Outputs: output/global_anomaly_map.html
Requires: data_products/global_month_anomaly.nc (created by 06_global_anomalies.py)
"""
from __future__ import annotations

from pathlib import Path
import xarray as xr
import numpy as np
import folium

ANOM = Path("data_products/global_month_anomaly.nc")
OUT_HTML = Path("output/global_anomaly_map.html")


def main():
    if not ANOM.exists():
        print("Missing anomaly NetCDF. Run src/06_global_anomalies.py first (synthetic fallback).")
        return
    ds = xr.open_dataset(ANOM)
    if "LST_global_anomaly" not in ds:
        print("Anomaly variable not found.")
        return
    da = ds["LST_global_anomaly"]
    # Convert to simple list of points (downsample if large)
    lats = da["lat"].values
    lons = da["lon"].values
    data = da.values
    # Downsample (every 3rd cell) to limit marker count
    lat_idx = np.arange(0, lats.size, 3)
    lon_idx = np.arange(0, lons.size, 3)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")
    for i in lat_idx:
        for j in lon_idx:
            val = float(data[i, j])
            color = "#" + ("ff0000" if val > 2 else ("ffa500" if val > 1 else ("00bfff" if val < -1 else "cccccc")))
            folium.CircleMarker(
                location=[float(lats[i]), float(lons[j])],
                radius=3,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=f"Anomaly: {val:.2f} K"
            ).add_to(m)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT_HTML))
    print(f"Wrote interactive map {OUT_HTML}")


if __name__ == "__main__":
    main()
