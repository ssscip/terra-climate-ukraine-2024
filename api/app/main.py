from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import get_settings
from .routers import events as events_router

settings = get_settings()

app = FastAPI(title="TerraTales API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(events_router.router, prefix=settings.api_prefix)

# Static assets (thumbnails, rasters)
app.mount("/assets", StaticFiles(directory=settings.static_dir), name="assets")


@app.get("/")
async def root():
    return {"service": "TerraTales API", "endpoints": [f"{settings.api_prefix}/events", f"{settings.api_prefix}/stats/summary"]}
