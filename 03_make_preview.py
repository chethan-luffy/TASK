"""TASK 3 + OUTPUT: Sentinel-2 pre/post composites for the top districts -> 05_composite_preview.png"""
import io, json
import requests, ee, geopandas as gpd, matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from PIL import Image
from shapely.geometry import mapping
import config as C

try:
    ee.Initialize(project=C.EE_PROJECT)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=C.EE_PROJECT)

BANDS = ["B2", "B3", "B4", "B8", "B11", "B12"]


def mask_scl(img):
    scl = img.select("SCL")                       # remove classes 1, 3, 8, 9, 10, 11
    bad = scl.eq(1).Or(scl.eq(3)).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(11))
    return img.updateMask(bad.Not())


def composite(window, geom):
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(geom).filterDate(*window)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))      # scene cloud < 30 %
    n = col.size().getInfo()
    return col.map(mask_scl).select(BANDS).median().clip(geom), n


def thumb(img, bounds, pxw, pxh):
    rgb = img.select(["B12", "B8", "B4"]).visualize(**C.VIS)            # false colour, same stretch
    region = ee.Geometry.Rectangle(list(bounds), "EPSG:32643", False)
    url = rgb.getThumbURL({"region": region, "dimensions": f"{pxw}x{pxh}",
                           "crs": "EPSG:32643", "format": "png"})
    r = requests.get(url, timeout=600)
    r.raise_for_status()
    return plt.imread(io.BytesIO(r.content), format="png")


def nice_km(width_m):
    target = width_m * 0.25 / 1000
    for k in (1, 2, 5, 10, 20, 25, 50):
        if k >= target:
            return k
    return 50


top = json.load(open("outputs/top_districts.json"))
dist = C.load_districts().set_index(C.DCOL)
dist_u = dist.to_crs(32643)

rows = []
for name in top:
    g_ll = dist.loc[name, "geometry"].simplify(0.0005)
    geom = ee.Geometry(json.loads(json.dumps(mapping(g_ll))), None, False)
    geom_u = dist_u.loc[name, "geometry"]
    minx, miny, maxx, maxy = geom_u.bounds
    w, h = maxx - minx, maxy - miny
    pxw = round(C.THUMB_PX * w / max(w, h))
    pxh = round(C.THUMB_PX * h / max(w, h))
    imgs = []
    for tag, win in (("pre", C.PRE), ("post", C.POST)):
        img, n = composite(win, geom)
        print(f"{name} {tag} {win}: {n} scenes")
        if n == 0:
            raise SystemExit(f"No scenes for {name} {tag}. Widen the window and note the reason.")
        imgs.append(thumb(img, (minx, miny, maxx, maxy), pxw, pxh))
        if C.EXPORT_TIFFS:                                              # full 10 m, 6 bands
            ee.batch.Export.image.toDrive(image=img.toUint16(), description=f"{name}_{tag}",
                                          folder="stubble", region=geom, scale=10,
                                          crs="EPSG:32643", maxPixels=1e10).start()
    rows.append(dict(name=name, imgs=imgs, geom_u=geom_u, bounds=(minx, miny, maxx, maxy), w=w, h=h))

# ---------- figure ----------
n = len(rows)
ratios = [r["h"] / r["w"] for r in rows]
fig_h = C.FIG_W / 2 * sum(ratios) + 2.6
fig, axes = plt.subplots(n, 2, figsize=(C.FIG_W, fig_h), squeeze=False,
                         gridspec_kw={"height_ratios": ratios, "hspace": 0.16, "wspace": 0.03})
fig.subplots_adjust(left=0.02, right=0.98, top=1 - 1.1 / fig_h, bottom=0.9 / fig_h)
halo = [pe.withStroke(linewidth=3, foreground="black")]

for i, r in enumerate(rows):
    minx, miny, maxx, maxy = r["bounds"]
    for j, (lab, dates) in enumerate((("Pre-fire", C.PRE_LABEL), ("Post-fire", C.POST_LABEL))):
        ax = axes[i][j]
        ax.set_facecolor("#e6e6e6")
        ax.imshow(r["imgs"][j], extent=(minx, maxx, miny, maxy), interpolation="nearest")
        gpd.GeoSeries([r["geom_u"]]).boundary.plot(ax=ax, color="black", linewidth=0.7)
        ax.set_xlim(minx, maxx); ax.set_ylim(miny, maxy)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{r['name']}  |  {lab}  |  {dates}", fontsize=13, fontweight="bold")
        # scale bar
        L = nice_km(r["w"]) * 1000
        x0, y0 = minx + 0.05 * r["w"], miny + 0.05 * r["h"]
        ax.plot([x0, x0 + L], [y0, y0], color="black", lw=6, solid_capstyle="butt")
        ax.plot([x0, x0 + L], [y0, y0], color="white", lw=3.5, solid_capstyle="butt")
        ax.text(x0 + L / 2, y0 + 0.025 * r["h"], f"{L/1000:g} km", ha="center",
                color="white", fontsize=10, fontweight="bold", path_effects=halo)
        # north arrow
        ax.annotate("", xy=(0.94, 0.93), xytext=(0.94, 0.80), xycoords="axes fraction",
                    arrowprops=dict(facecolor="white", edgecolor="black", width=4, headwidth=12))
        ax.text(0.94, 0.95, "N", transform=ax.transAxes, ha="center", va="bottom",
                color="white", fontsize=12, fontweight="bold", path_effects=halo)

fig.suptitle("Stubble burning, Punjab 2025: pre-fire vs post-fire Sentinel-2 composites",
             fontsize=17, fontweight="bold", y=1 - 0.25 / fig_h)
fig.text(0.5, 0.35 / fig_h,
         "False colour composite: R = B12, G = B8, B = B4  |  Median composites, scene cloud < 30 %, SCL-masked  |  "
         "Same contrast stretch on all panels\nData source: Copernicus Sentinel-2 L2A surface reflectance, 2025",
         ha="center", va="center", fontsize=11)

out = "05_composite_preview.png"
fig.savefig(out, dpi=C.DPI)
size = Image.open(out).size
print("saved", out, size, "OK" if size[0] >= 2000 else "TOO NARROW")
