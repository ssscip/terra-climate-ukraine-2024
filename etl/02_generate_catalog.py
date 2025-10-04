#!/usr/bin/env python
"""Generate enriched event catalog.
Merges base GeoJSON features + existing metrics (if available) and writes JSON list.
Currently minimal; extend with dynamic metric extraction from data_products.
"""
from __future__ import annotations
import json
from pathlib import Path
import argparse
from datetime import datetime

BASE = Path("events/catalog/events_base.geojson")
OUT = Path("events/catalog/events_enriched.json")
SCHEMA_PATH = Path("events/schema/event_schema.json")


def load_base():
    with BASE.open("r", encoding="utf-8") as f:
        gj = json.load(f)
    feats = gj.get("features", [])
    out = []
    for ft in feats:
        prop = ft.get("properties", {})
        geom = ft.get("geometry")
        # Basic expansion
        ev = {
            "id": prop["id"],
            "title": prop.get("title"),
            "category": prop.get("category"),
            "start_date": prop.get("start_date"),
            "end_date": prop.get("end_date"),
            "year": prop.get("year"),
            "lat": geom["coordinates"][1] if geom and geom["type"] == "Point" else prop.get("lat"),
            "lon": geom["coordinates"][0] if geom and geom["type"] == "Point" else prop.get("lon"),
            "geometry_type": geom["type"] if geom else "Point",
            "geometry": geom,
            "terra_instruments": prop.get("terra_instruments", ["MODIS"]),
            "products": [],
            "media": {},
            "metrics": {},
            "narrative": {"short": prop.get("title", "Event"), "long": ""},
            "sources": prop.get("sources", []),
            "confidence": prop.get("confidence", "medium"),
        }
        out.append(ev)
    return out


def validate_schema(events):
    # Lightweight validation (placeholder); robust: use jsonschema lib if installed
    required = ["id","title","category","start_date","end_date","year","lat","lon","geometry","terra_instruments","narrative","confidence"]
    for ev in events:
        missing = [k for k in required if k not in ev or ev[k] in (None,"")]
        if missing:
            print(f"WARN event {ev.get('id')} missing: {missing}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--append", help="Existing enriched catalog to merge", default=None)
    args = ap.parse_args()

    base_events = load_base()
    if args.append and Path(args.append).exists():
        with open(args.append, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    # Merge by id (base overrides minimal fields)
    merged = {ev["id"]: ev for ev in existing}
    for ev in base_events:
        merged[ev["id"]] = {**merged.get(ev["id"], {}), **ev}

    events = list(merged.values())
    validate_schema(events)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    print(f"Wrote {OUT} ({len(events)} events)")


if __name__ == "__main__":
    main()
