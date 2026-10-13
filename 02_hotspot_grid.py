"""TASK 2: 5 km hex grid in EPSG:32643, counts per hex, totals per district, pick top 3."""
import json
import numpy as np, pandas as pd, geopandas as gpd, matplotlib.pyplot as plt
from shapely.geometry import Polygon
import config as C

pts = gpd.read_file("outputs/clean_points.gpkg")
dist = C.load_districts()
pts_u, dist_u = pts.to_crs(32643), dist.to_crs(32643)     # equal-area-ish metres
state_u = dist_u.geometry.union_all()

W = 5000                                  # hex width flat-to-flat = 5 km
R = W / np.sqrt(3)                        # circumradius
minx, miny, maxx, maxy = dist_u.total_bounds
hexes, y, row = [], miny, 0
while y < maxy + R:
    x = minx + (W / 2 if row % 2 else 0)
    while x < maxx + W:
        hexes.append(Polygon([(x + R * np.cos(np.radians(a)), y + R * np.sin(np.radians(a)))
                              for a in range(30, 390, 60)]))
        x += W
    y += 1.5 * R
    row += 1
grid = gpd.GeoDataFrame(geometry=hexes, crs=32643)
grid = grid[grid.intersects(state_u)].reset_index(drop=True)

j = gpd.sjoin(pts_u[["geometry"]], grid, predicate="within")
j = j[~j.index.duplicated()]
grid["fires"] = j.groupby("index_right").size().reindex(grid.index).fillna(0).astype(int)

# district totals: (a) straight from points, (b) summing hex counts by hex centroid
by_pts = pts.groupby(C.DCOL).size()
cent = grid.copy(); cent["geometry"] = grid.centroid
by_hex = gpd.sjoin(cent, dist_u, predicate="within").groupby(C.DCOL)["fires"].sum()
table = (pd.DataFrame({"fires_points": by_pts, "fires_hex_sum": by_hex})
         .fillna(0).astype(int).sort_values("fires_points", ascending=False))
print(table.head(10))

top = list(table.index[:3])
print("TOP DISTRICTS:", top)
json.dump(top, open("outputs/top_districts.json", "w"))
table.to_csv("outputs/district_counts.csv")
grid.to_file("outputs/hex_grid.gpkg", driver="GPKG")

ax = grid.plot(column="fires", cmap="YlOrRd", legend=True, figsize=(8, 8))
dist_u.boundary.plot(ax=ax, color="black", linewidth=0.5)
ax.set_title("Fire points per 5 km hex (check figure, not submitted)")
ax.figure.savefig("outputs/hex_check.png", dpi=120)
