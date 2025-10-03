# ROI GeoJSON Files

Provide the following GeoJSON files inside this directory (all in WGS84 EPSG:4326):

Required files:
- ukraine.geojson (national boundary)
- zaporizhzhia.geojson (oblast boundary or focused polygon)
- water_body.geojson (polygon(s) delineating key water reservoir / lake area)
- italy_box.geojson (bounding box or polygon for selected Italy heatwave ROI)
- alps_box.geojson (optional polygon covering Alpine study area)

Format: Each file should be a valid GeoJSON FeatureCollection with one or more Polygon / MultiPolygon features. Properties can be minimal (e.g., {"name": "ukraine"}).

How to create:
1. Visit https://geojson.io
2. Draw or import the boundary (you can copy from GADM, Natural Earth, or other open sources ensuring license compatibility).
3. Ensure geometry type is Polygon/MultiPolygon.
4. Save as the exact filename listed above.

Quality Tips:
- Simplify cautiously to reduce file size but preserve key shape.
- Validate using a linter or `geojson` Python package if uncertain.
- Keep all coordinates longitude, latitude (not reversed).

These ROIs are referenced by scripts for masking, metric computation, and frame generation.
