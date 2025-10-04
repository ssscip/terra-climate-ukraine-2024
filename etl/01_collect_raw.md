# 01 Collect Raw Data

Guidance (initial skeleton):

Recommended structure:
```
raw/
  MOD11A1/ YYYY/DDD/*.hdf
  MOD13A2/ YYYY/DDD/*.hdf
  MCD64A1/ YYYY/*.hdf (burned area)
  MOD14A1/ YYYY/DDD/*.hdf (fire)
```

Steps:
1. Acquire MODIS products via LAADS / Earthdata credentials.
2. Store under `raw/<PRODUCT>/<YEAR>/<DOY>/`.
3. Maintain a manifest CSV with columns: product, date, path, checksum.
4. (Optional) Run integrity check script (future) before proceeding.

Next: `02_generate_catalog.py` builds event list.
