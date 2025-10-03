# Terra Climate Extremes (Ukraine 2024 → Global Context)

## (UA) Мета
Показати екстремальні літні (липень–серпень 2024) аномалії температури поверхні (LST) в Україні, пов’язані індикатори екосистем (NDVI, водні площі), а також розмістити локальні спостереження в глобальному контексті (італійська теплова хвиля та низьке снігове покриття в Альпах).

## (UA) Основні Компоненти
- Локальні аномалії LST (MOD11A1 + кліматологія з baseline).
- Heat Days (дні > 95-го перцентиля у Запоріжжі).
- ΔNDVI (MOD13Q1) липень–серпень 2024 vs baseline.
- Зміна водної площі за MNDWI (MOD09GA) для вибраної водойми.
- Глобальна карта аномалій LST (MOD11C1) + фокус на Італію (теплова хвиля) й Альпи (низький сніг / аномалія).
- Гістограма розподілу (baseline vs 2024) для регіону.
- Фінальне відео (30–60 с) + метрики + озвучка (VO_SCRIPT.txt).

## (UA) Baseline
НЕ включати 2024 у baseline. Поточна конфігурація за замовчуванням: 2010–2019.
Якщо хочеш 2010–2023 — змінити в `config.yml` та перегенерувати кліматологію.

## (UA) Дані (Продукти Terra MODIS / Опційні ASTER)
| Продукт | Призначення | DOI |
|---------|-------------|-----|
| MOD11A1 v061 | Денна LST (тайли) | 10.5067/MODIS/MOD11A1.061 |
| MOD11C1 v061 | Глобальна LST сітка | 10.5067/MODIS/MOD11C1.061 |
| MOD13Q1 v061 | NDVI/EVI (16-денний) | 10.5067/MODIS/MOD13Q1.061 |
| MOD09GA v061 | Відбиття (для NDWI/MNDWI) | 10.5067/MODIS/MOD09GA.061 |
| MOD10A1 v061 (опц.) | Снігове покриття | 10.5067/MODIS/MOD10A1.061 |
| ASTER L1T | High-res scene (опц.) | 10.5067/ASTER/AST_L1T.003 |
| ASTER SR (AST_07XT) | Поверхневі відбиття (опц.) | 10.5067/ASTER/AST_07XT.003 |

## (UA) Метод Узагальнено
1. Завантаження baseline тайлів/глобальних сіток → побудова кліматології по DOY.
2. Аномалії 2024 = LST_2024(DOY) – Climatology(DOY).
3. Heat Days = кількість днів, де LST (або регіональна середня) > 95-го перцентиля baseline.
4. NDVI Δ = середній NDVI (лип–сер 2024) – середній NDVI baseline (лип–сер).
5. MNDWI → водна площа 2024 vs середня baseline.
6. Глобальна аномалія (липень 2024).
7. Гістограма baseline vs 2024.
8. Генерація кадрів (локально → глобально → екстремуми → метрики).
9. Збірка відео (ffmpeg) + озвучка.

## (UA) Швидкий Старт
```
conda env create -f environment.yml
conda activate terra-climate
# Додати .netrc (інструкції в notebooks/00_quickstart.ipynb)
python src/01_download_modis.py
python src/02_build_climatology.py
python src/03_compute_anomalies.py
python src/04_compute_ndvi.py
python src/05_compute_water_mndwi.py
python src/06_global_anomalies.py
python src/07_histogram_distribution.py
python src/08_metrics.py
python src/09_generate_frames.py
bash src/10_make_video.sh
```

## (UA) Структура
```
data_raw/           # завантажені HDF/NetCDF
data_intermediate/  # тимчасові (маски, композити)
data_products/      # кліматологія, аномалії, метрики
docs/               # citations, metrics.csv
notebooks/          # Jupyter
roi/                # geojson полігони
src/                # скрипти
output/
  frames_*          # кадри
  video/            # фінальні відео
```

## (UA) Файли Конфігурації
`config.yml` — baseline роки, часові інтервали, пороги (MNDWI, percentiles).

## (UA) Озвучка
Текст у `VO_SCRIPT.txt`. Можна адаптувати (≈55 сек при середній швидкості).

---

## (EN) Summary
This repository analyzes Summer 2024 surface temperature extremes in Ukraine (MODIS Terra), derives anomalies against a 2010–2019 (default) baseline, quantifies “heat days,” NDVI and water surface changes, then places them in a global context (Italy heatwave & Alpine low snow). Outputs: reproducible pipeline, metrics, final video, and narration script.

### Data Products
See citations in `docs/citations.txt`. Do NOT include the target event year in baseline (avoid contamination).

### Pipeline Outline
1. Download & QA filter.
2. Build day-of-year climatology.
3. Compute LST anomalies + percentile exceedances.
4. Vegetation / water indices (NDVI, MNDWI).
5. Global anomalies & contrasting regions.
6. Distribution shifts (histogram).
7. Frame generation & final video assembly.

---

## (UA/EN) TODO (Initial Checklist)
- [ ] Confirm baseline final (A=2010–2019 or B=2010–2023).
- [ ] Add ROI geojson (Ukraine, Zaporizhzhia, Italy box, Alps box, water_body).
- [ ] Implement real LAADS/LP DAAC API listing (placeholders now).
- [ ] Fill metrics after computations.
- [ ] Final color palette validation.
- [ ] Add optional ASTER scenes if needed.

## Ліцензія
MIT (див. LICENSE).

## Кредити
Data courtesy of NASA EOSDIS (Terra MODIS, optionally ASTER).
Processing & analysis: (ваші імена).

---
