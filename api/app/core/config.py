from __future__ import annotations
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    api_prefix: str = "/api"
    cors_origins: str = "*"
    catalog_path: str = "events/catalog/events_enriched.json"
    static_dir: str = "globe_assets"

    class Config:
        env_prefix = "TERRATALES_"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
