"""TASK 1: clean VIIRS fire points (confidence n/h, inside state, cropland only)."""
import os
import numpy as np, pandas as pd, geopandas as gpd, rasterio
import config as C

os.makedirs("outputs", exist_ok=True)
dist = C.load_districts()
print("districts found:", len(dist))
print(sorted(dist[C.DCOL]))

df = pd.concat([pd.read_csv(f) for f in C.FIRMS_FILES], ignore_index=True)
print("raw points:", len(df))
df = df[df["acq_date"].between(C.START, C.END)]
df = df[df["confidence"].astype(str).str.lower().isin(["n", "h"])]     # drop 'l'
print("after confidence n/h:", len(df))

pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4326)
pts = gpd.sjoin(pts, dist, predicate="within").drop(columns="index_right")   # clip + tag district
pts = pts[~pts.index.duplicated()].reset_index(drop=True)
print("inside state:", len(pts))

# ESA WorldCover 2021: read class at each point straight from the web (3x3 degree tiles)
BASE = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
pts["wc"] = 0
la = (np.floor(pts.latitude / 3) * 3).astype(int)
lo = (np.floor(pts.longitude / 3) * 3).astype(int)
with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
    for (a, b), g in pts.groupby([la, lo]):
        name = f"ESA_WorldCover_10m_2021_v200_N{a:02d}E{b:03d}_Map.tif"
        print("sampling", name, len(g), "points (can take a few minutes)")
        with rasterio.open(BASE + name) as src:
            pts.loc[g.index, "wc"] = [v[0] for v in src.sample(list(zip(g.longitude, g.latitude)))]

pts = pts[pts["wc"] == 40].copy()                                       # cropland only
print("FINAL clean points (cropland):", len(pts))
pts.to_file("outputs/clean_points.gpkg", driver="GPKG")
