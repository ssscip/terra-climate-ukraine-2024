# ETL Pipeline (TerraTales)

Stages:
1. Collect raw products (MODIS LST, NDVI, etc.) into standardized folder layout.
2. Generate unified event catalog (merge curated + derived) -> `events/catalog/events_enriched.json`.
3. Build raster derivatives per event (subset, anomaly, colorized) -> `globe_assets/evt_*/*`.
4. Export thumbnails & micro-animations.
5. (Optional) Package point/polygon events as PMTiles/vector tiles for performant globe rendering.

Scripts here act on existing baseline products or download raw sources (future extension).
