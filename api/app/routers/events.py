from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json
from pathlib import Path

router = APIRouter()

CAT_PATH = Path("events/catalog/events_enriched.json")


def load_catalog():
    if not CAT_PATH.exists():
        return []
    with CAT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/events")
def list_events(year: Optional[int] = Query(None), category: Optional[str] = Query(None)):
    events = load_catalog()
    if year is not None:
        events = [e for e in events if e.get("year") == year]
    if category is not None:
        events = [e for e in events if e.get("category") == category]
    return events


@router.get("/events/{event_id}")
def event_detail(event_id: str):
    events = load_catalog()
    for e in events:
        if e.get("id") == event_id:
            return e
    raise HTTPException(status_code=404, detail="Event not found")


@router.get("/stats/summary")
def stats_summary():
    events = load_catalog()
    per_category = {}
    per_year = {}
    for e in events:
        cat = e.get("category")
        per_category[cat] = per_category.get(cat, 0) + 1
        yr = e.get("year")
        per_year[yr] = per_year.get(yr, 0) + 1
    return {"count": len(events), "per_category": per_category, "per_year": per_year}
