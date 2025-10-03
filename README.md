# Terra Climate Extremes (Ukraine 2024 → Global Context)

## 🇺🇦 Мета / Purpose
UA: Показати екстремальні літні (липень–серпень 2024) аномалії температури поверхні (LST) в Україні, індикатори екосистем (NDVI, водні площі) та розмістити локальні спостереження у глобальному контексті (Італія – теплова хвиля, Альпи – низький сніг).
EN: Analyze July–August 2024 Ukrainian land surface temperature extremes (Terra MODIS) vs a 2010–2019 baseline; quantify heat days, vegetation stress (NDVI), water surface change (MNDWI), and embed results in broader European/global context (Italy heatwave, Alpine low snow, global anomaly map).

## Основні Компоненти / Key Components
1. LST daily anomalies (MOD11A1 vs DOY climatology).
2. Heat Days (>95th percentile Zaporizhzhia region).
3. ΔNDVI (July–August 2024 vs baseline mean) (MOD13Q1).
4. Water surface / MNDWI change (MOD09GA) for selected water body.
5. Global July anomaly (MOD11C1) + Italy focus + Alps (optional snow context MOD10A1).
6. Distribution histogram (baseline vs 2024) for chosen ROI.
7. Final video (frames + ffmpeg) + narration script (`VO_SCRIPT.txt`).

## Baseline
- Default Baseline A: 2010–2019 (stable pre-2020 period).
- Optional Baseline B: 2010–2023 (wider sample). To switch: edit `config.yml` and rerun climatology.
- Event year (2024) is never included in baseline.

## MODIS / ASTER Data Products
| Product | Purpose | DOI |
|---------|---------|-----|
| MOD11A1 v061 | Daily LST (tiles) | 10.5067/MODIS/MOD11A1.061 |
| MOD11C1 v061 | Global LST grid | 10.5067/MODIS/MOD11C1.061 |
| MOD13Q1 v061 | 16‑day NDVI/EVI | 10.5067/MODIS/MOD13Q1.061 |
| MOD09GA v061 | Surface reflectance (MNDWI) | 10.5067/MODIS/MOD09GA.061 |
| MOD10A1 v061 (opt) | Snow cover (Alps) | 10.5067/MODIS/MOD10A1.061 |
| ASTER L1T (opt) | High‑res scenes | 10.5067/ASTER/AST_L1T.003 |
| ASTER SR (AST_07XT) (opt) | Surface reflectance | 10.5067/ASTER/AST_07XT.003 |

See `docs/citations.txt` for references.

## Method Overview (UA/EN)
1. Build DOY climatology (baseline years) from MOD11A1.
2. Event anomalies: LST_2024(DOY) − Climatology(DOY).
3. Heat Days: count days above 95th percentile of baseline distribution (Zaporizhzhia ROI).
4. NDVI Δ: (Jul–Aug 2024 mean) − (Jul–Aug baseline mean).
5. MNDWI: Compare 2024 mean vs baseline mean (area or index change).
6. Global July anomaly (MOD11C1) + regional extracts (Italy, Alps).
7. Histogram: baseline vs 2024 distribution shift.
8. Frame rendering + video assembly + narration.

## Quick Start
```bash
conda env create -f environment.yml
conda activate terra-climate

# (1) Download raw data (see src/01_download_modis.py placeholders) into data_raw/
python src/02_build_climatology.py
python src/03_compute_anomalies.py
python src/04_compute_ndvi.py
python src/05_compute_water_mndwi.py
python src/06_global_anomalies.py   # optional/global
python src/07_histogram_distribution.py
python src/08_metrics.py
python src/09_generate_frames.py
bash src/10_make_video.sh           # or: pwsh src/10_make_video.ps1
```

## Repository Structure
```
data_raw/           # downloaded HDF/NetCDF (ignored)
data_intermediate/  # temporary composites & masks (ignored)
data_products/      # climatology, anomalies, metrics outputs
docs/               # citations, metrics.csv
notebooks/          # exploratory notebooks
roi/                # GeoJSON ROIs (Ukraine, Zaporizhzhia, Italy, Alps, water)
src/                # pipeline scripts + I/O utilities
output/
  frames_*          # generated frames
  video/            # final mp4/gif
```

## Pipeline Steps
| Step | Script | Output (Representative) | Status |
|------|--------|-------------------------|--------|
| 1 | 01_download_modis.py | data_raw/* | Placeholder/manual |
| 2 | 02_build_climatology.py | data_products/lst_climatology.nc; lst_baseline_daily.nc | Active |
| 3 | 03_compute_anomalies.py | lst_event.nc; lst_anomaly_event.nc | Active |
| 4 | 04_compute_ndvi.py | ndvi_base_mean.nc; ndvi_event_mean.nc; ndvi_delta_jul_aug.nc | Active |
| 5 | 05_compute_water_mndwi.py | mndwi_base_mean.nc; mndwi_event_mean.nc; mndwi_delta.nc | Active (needs QA) |
| 6 | 06_global_anomalies.py | (planned) global_july_anomaly.nc | Placeholder |
| 7 | 07_histogram_distribution.py | docs/distribution_histogram.csv | Active (limited) |
| 8 | 08_metrics.py | docs/metrics.csv (appended) | Partial (more metrics TBD) |
| 9 | 09_generate_frames.py | output/frames_local/*.png | Active |
| 10 | 10_make_video.sh / .ps1 | output/video/final_video.mp4 | Active |

## Configuration
`config.yml` centralizes:
- baseline years
- event year
- focus date window (e.g., Jul–Aug)
- percentile thresholds (e.g., 0.95 heat days)
- MNDWI threshold
- video parameters (fps, width)

## Narration / Voice Over
Edit `VO_SCRIPT.txt` (≈50–60 s). Sync any updated metrics before final recording.

## TODO / Roadmap
- [ ] Real LAADS/LP DAAC API download + retry logic
- [ ] MODIS QC bitmask filtering (cloud / emissivity / snow flags)
- [ ] Robust MNDWI area extraction (threshold & polygon intersection)
- [ ] Add water & snow metrics into `docs/metrics.csv`
- [ ] Global anomaly (MOD11C1) implementation
- [ ] Optional MOD10A1 Alps snow anomaly
- [ ] Percentile tail metrics (97.5 / 99%)
- [ ] Dask chunking & performance tuning
- [ ] GitHub Actions: add tests (currently only lint)
- [ ] Potential Git LFS for large NetCDF outputs
- [ ] Enhanced color maps & legend layout

## Demo Mode (No Real MODIS Data)
To quickly preview the pipeline outputs without downloading MODIS, generate synthetic data that mimics baseline and 2024 anomalies:

```bash
conda activate terra-climate  # after creating environment
python scripts/demo_generate_mock_data.py --run-metrics --make-frames
```

This will create synthetic NetCDF files in `data_products/`, update `docs/metrics.csv`, and (with `--make-frames`) produce anomaly frames in `output/frames_local`. You can then run:

```bash
python src/10_make_video.ps1  # PowerShell
# OR (Linux/macOS)
bash src/10_make_video.sh
```

Resulting video will appear in `output/video/` (ensure `ffmpeg` available or install via system package or `conda install ffmpeg`).

Synthetic characteristics:
- Heat anomaly localized (~+5 K peak) over central grid.
- NDVI stress patch (negative delta) and mild water area reduction (MNDWI).
- Spatial grid spans lon 20–44E, lat 40–56N to overlap Ukraine ROI polygons.

Remove synthetic outputs by deleting the created NetCDFs in `data_products/` and frames in `output/frames_local/` before running with real data.

### Global Anomaly & HTML Preview
Run synthetic or real global anomaly:
```bash
python src/06_global_anomalies.py --synthetic
python scripts/preview_global_html.py
```
Interactive map: `output/global_anomaly_map.html`.

### If You Cannot Install Conda (Minimal Pip Demo)
For the synthetic demo only (no real raster geospatial I/O), you can use a lightweight virtual env:
```
python -m venv .venv
./.venv/Scripts/activate    # Windows PowerShell
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements-demo.txt
python scripts/run_all_demo.py --regenerate --no-video
```
To build the video install ffmpeg separately (e.g. Chocolatey: `choco install ffmpeg` or download static build and add to PATH) then rerun without `--no-video`.
Full functionality (rasterio, rioxarray, cartopy) still requires the conda environment because of compiled GDAL dependencies.

## License / Ліцензія
MIT (see `LICENSE`).

## Credits / Кредити
Data: NASA EOSDIS LP DAAC (Terra MODIS; optional ASTER).  
Processing & analysis: Your names / contributors.  
Please cite DOIs in `docs/citations.txt`.

## Acknowledgements / Подяки
Scaffold prepared for rapid, reproducible climate anomaly assessment integrating local Ukrainian extremes into global context.
