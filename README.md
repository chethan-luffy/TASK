# Stubble Burning Detection: Punjab 2025

Identifies the Punjab districts most affected by paddy residue burning (1 Oct - 30 Nov 2025) from NASA VIIRS fire detections, then shows the top districts as pre-fire and post-fire Sentinel-2 false colour composites.

The final output is one image: `chethan prasad_1DA25SCS04.png`.

> Burn indices (NBR / dNBR) are intentionally **not** computed here. They belong to the next stage.

## Pipeline

| Step | Script | What it does | Output |
|------|--------|--------------|--------|
| 1 | `01_fire_points.py` | Merges VIIRS S-NPP + NOAA-20 375 m points, keeps confidence `n`/`h`, clips to Punjab, keeps cropland only (ESA WorldCover 2021, class 40) | `outputs/clean_points.gpkg` |
| 2 | `02_hotspot_grid.py` | Builds a 5 km hex grid (EPSG:32643), counts fires per hex and per district, picks the top 3 districts | `outputs/top_districts.json`, `district_counts.csv`, `hex_grid.gpkg`, `hex_check.png` |
| 3 | `03_make_preview.py` | Builds Sentinel-2 L2A median composites (pre and post) via Google Earth Engine and draws the final figure | `05_composite_preview.png` |

## Data (not included in the repo)

Place these in `data/`:

- **Fire points:** NASA FIRMS archive download (https://firms.modaps.eosdis.nasa.gov/download/), VIIRS S-NPP 375 m and VIIRS NOAA-20 375 m, CSV, 2025-10-01 to 2025-11-30
  - `fire_archive_SV-C2_821688.csv`
  - `fire_archive_J1V-C2_821687.csv`
- **District boundaries:** GADM 4.1 India, level 2 shapefile (https://gadm.org/download_country.html). Copy all `gadm41_IND_2.*` files (`.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`).

ESA WorldCover is read directly from the web at run time. Sentinel-2 comes from Google Earth Engine.

## Setup

Requires Python 3.10+ (3.11+ recommended) and a Google Earth Engine account.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Earth Engine:

1. Register at https://code.earthengine.google.com/register (non-commercial / academic use).
2. Note your Google Cloud **project ID** (the ID, not the display name).
3. Set `EE_PROJECT` in `config.py`.
4. The first run of `03_make_preview.py` opens a browser to authorise access.

## Configuration

All settings live in `config.py`:

| Setting | Meaning |
|---------|---------|
| `DISTRICT_FILE`, `STATE_COL`, `STATE_NAME`, `DCOL` | Boundary file and the columns used to select Punjab and read district names |
| `FIRMS_FILES`, `START`, `END` | Fire CSVs and date range |
| `EE_PROJECT` | Your Earth Engine / Google Cloud project ID |
| `PRE`, `POST` | Composite windows (end date is exclusive): 1-15 Oct and 12-30 Nov 2025 |
| `VIS` | False colour contrast stretch, identical for pre and post panels |
| `THUMB_PX`, `FIG_W`, `DPI` | Panel image size and final figure size (about 3200 px wide) |
| `EXPORT_TIFFS` | `True` also starts full 10 m six-band GeoTIFF exports to Google Drive |

## Run

```bash
python 01_fire_points.py
python 02_hotspot_grid.py
python 03_make_preview.py
```

Step 1 samples WorldCover remotely and can take a few minutes.

## Method summary

- **Fire filter:** VIIRS confidence `n` and `h` only; points must fall inside Punjab and on cropland.
- **Hex grid:** 5 km flat-to-flat hexagons in UTM 43N. District totals are reported both from points and by summing hex counts (by hex centroid).
- **Composites:** `COPERNICUS/S2_SR_HARMONIZED`, scene cloud cover < 30 %, SCL mask removing classes 1, 3, 8, 9, 10, 11, median of B2, B3, B4, B8, B11, B12.
- **Display:** R = B12, G = B8, B = B4. Each panel has district name, dates, scale bar and north arrow; the footer states the band combination and data source.

## Limitations

- VIIRS points are detections, not burned area. One fire can be detected by both satellites.
- Fires can be missed between overpasses or under cloud and smoke.
- Two-week median composites can blend dates, and late-November imagery may show newly sown wheat.
- GADM boundaries may not include recently created districts.
- The preview panels are downsampled from the 10 m composite. Use `EXPORT_TIFFS = True` for full-resolution inspection.

## Data sources and credits

- NASA FIRMS, VIIRS 375 m active fire product
- ESA WorldCover 2021 v200
- Copernicus Sentinel-2 Level 2A (processed in Google Earth Engine)
- GADM 4.1 administrative boundaries

- personal intelligence used is "Cluade"
