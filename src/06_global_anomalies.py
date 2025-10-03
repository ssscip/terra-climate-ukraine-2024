"""Placeholder global July anomaly using MOD11C1 if available."""
from __future__ import annotations

from pathlib import Path
import yaml
import xarray as xr

CONFIG_PATH = Path("config.yml")
RAW_DIR = Path("data_raw/MOD11C1")
OUT_PATH = Path("data_products/global_july_anomaly.nc")


def parse_config():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def main():
    cfg = parse_config()
    event_year = cfg["event_year"]
    month = cfg["periods"]["global_focus_month"]
    files = sorted(RAW_DIR.glob("*.nc"))
    if not files:
        print("No MOD11C1 files present. Provide global LST NetCDF.")
        return
    # Placeholder: need baseline vs event extraction. We simply warn.
    print("Placeholder: implement global July anomaly computation if baseline & event data available.")
    if month != 7:
        print("Note: script currently assumes month=7")

    # Example stub if data existed
    # ds = xr.open_mfdataset([...])
    # Compute baseline mean for July over baseline years, subtract July event year.
    # ds_anom.to_netcdf(OUT_PATH)


if __name__ == "__main__":
    main()
