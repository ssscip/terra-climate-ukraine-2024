"""Placeholder script for downloading MODIS Terra products.

Instructions:
- Register and obtain NASA Earthdata credentials.
- Use LAADS DAAC (https://ladsweb.modaps.eosdis.nasa.gov/) or LP DAAC (via AppEEARS) for bulk download.
- Products of interest (Collection 6.1): MOD11A1 (LST Daily), MOD11C1 (global LST), MOD13Q1 (NDVI), MOD09GA (Surface Reflectance), MOD10A1 (Snow Cover optional).
- Place downloaded HDF / NetCDF / GeoTIFF files under data_raw/ in subfolders by product, e.g.:
  data_raw/MOD11A1/*.hdf
  data_raw/MOD13Q1/*.hdf

Suggested LAADS wget pattern (example - adapt dates & tiles):
  wget --user=USERNAME --password=PASSWORD -i filelist_mod11a1.txt -P data_raw/MOD11A1/
Where filelist_mod11a1.txt contains direct URLs for desired dates & tiles.

DO NOT commit credentials.
"""
from __future__ import annotations

if __name__ == "__main__":
    print("Download placeholder: populate data_raw/ with required MODIS product HDF files.")
