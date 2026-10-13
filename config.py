"""Edit ONLY this file. Everything else reads from here."""
import geopandas as gpd

# ---------- inputs (Tasks 1-2) ----------
DISTRICT_FILE = "data/gadm41_IND_2.shp"      # GADM India level-2 shapefile
STATE_COL, STATE_NAME = "NAME_1", "Punjab"   # set STATE_COL = None if file is already Punjab-only
DCOL = "NAME_2"                              # district-name column
FIRMS_FILES = ["data/fire_archive_SV-C2_821688.csv", "data/fire_archive_J1V-C2_821687.csv"]
START, END = "2025-10-01", "2025-11-30"

# ---------- Sentinel-2 (Task 3) ----------
EE_PROJECT = "food-order-chat-bot-iwnd"           # your Google Earth Engine / Cloud project id
PRE  = ("2025-10-01", "2025-10-16")          # end date is exclusive  -> 1-15 Oct
POST = ("2025-11-12", "2025-12-01")          # end date is exclusive  -> 12-30 Nov
PRE_LABEL, POST_LABEL = "1-15 Oct 2025", "12-30 Nov 2025"
# Same contrast stretch for pre and post (reflectance x10000). Tweak, but keep identical for both.
VIS = {"min": [0, 0, 0], "max": [4000, 4500, 3000]}   # R=B12, G=B8, B=B4

# ---------- output image ----------
THUMB_PX = 1800        # longest side of each panel image (lower it if Earth Engine says request too large)
FIG_W, DPI = 16, 200   # 16 in x 200 dpi = 3200 px wide
EXPORT_TIFFS = False   # True = also start full 10 m GeoTIFF exports to your Google Drive


def load_districts():
    d = gpd.read_file(DISTRICT_FILE)
    if STATE_COL:
        d = d[d[STATE_COL] == STATE_NAME]
    return d[[DCOL, "geometry"]].to_crs(4326).reset_index(drop=True)
