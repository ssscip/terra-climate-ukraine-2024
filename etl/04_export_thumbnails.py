#!/usr/bin/env python
"""Export thumbnails (320x180) and optional animated GIF (first N frames) if chronology frames exist.
Searches globe_assets/*/lst_anom.png to produce thumb.jpg.
For events with frame directory output/chronology_real creates simple gif (placeholder).
"""
from __future__ import annotations
from pathlib import Path
import json
from PIL import Image
import imageio.v2 as imageio

CATALOG = Path("events/catalog/events_enriched.json")
OUT_ROOT = Path("globe_assets")
FRAMES_DIR = Path("output/chronology_real")  # reuse existing chronology frames if present


def load_catalog():
    with CATALOG.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_thumb(ev_id: str):
    ev_dir = OUT_ROOT / ev_id
    src = ev_dir / "lst_anom.png"
    if not src.exists():
        return None
    thumb = ev_dir / "thumb.jpg"
    if thumb.exists():
        return thumb
    img = Image.open(src).convert("RGB")
    img = img.resize((320, 180))
    img.save(thumb, quality=85)
    return thumb


def maybe_gif(ev_id: str):
    # Placeholder: if chronology frames exist, build a tiny gif of first 15 frames
    frames = sorted(FRAMES_DIR.glob("frame_*.png"))[:15]
    if not frames:
        return None
    gif_path = OUT_ROOT / ev_id / "anim.gif"
    images = [imageio.imread(f) for f in frames]
    imageio.mimsave(gif_path, images, duration=0.25)
    return gif_path


def update_catalog(events):
    for ev in events:
        ev_id = ev["id"]
        thumb = ensure_thumb(ev_id)
        if thumb:
            ev.setdefault("media", {})["thumbnail"] = f"globe_assets/{ev_id}/{thumb.name}"
        gif = maybe_gif(ev_id)
        if gif:
            ev.setdefault("media", {})["animation"] = f"globe_assets/{ev_id}/{gif.name}"
    with CATALOG.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    print("Updated catalog media entries.")


def main():
    events = load_catalog()
    update_catalog(events)


if __name__ == "__main__":
    main()
