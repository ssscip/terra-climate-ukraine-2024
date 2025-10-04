#!/usr/bin/env bash
# OPTIONAL: Build PMTiles (point events) using tippecanoe + pmtiles tools if installed.
# Requirements: tippecanoe, pmtiles (https://github.com/protomaps/PMTiles)
# Usage:
#   bash etl/05_build_pmtiles.sh events/catalog/events_base.geojson globe_assets/events.pmtiles
set -euo pipefail

IN_GEOJSON=${1:-events/catalog/events_base.geojson}
OUT_PM=${2:-globe_assets/events.pmtiles}
TMP_DIR=$(mktemp -d)

echo "[1] Generating MBTiles with tippecanoe" >&2
tippecanoe -o "$TMP_DIR/events.mbtiles" -zg --drop-densest-as-needed --read-parallel "$IN_GEOJSON"

echo "[2] Converting MBTiles -> PMTiles" >&2
pmtiles convert "$TMP_DIR/events.mbtiles" "$OUT_PM"

echo "Done: $OUT_PM" >&2
