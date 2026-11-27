"""Substack graphics (Marcus 2026-11-27): Ladrillo's three glacier blocks on a map of the first-order glacier regions,
and the temperature over each block next to global mean temperature.

    ~/climate-env/bin/python python/substack_glacier_blocks.py

Inputs (read only):
  - Ladrillo.jl v1.0.0 (Zenodo 10.5281/zenodo.24445689): data/drivers/glacier_block_temperature.csv (each block's
    HadCRUT5 annual anomaly, glacier-area weighted over its RGI regions, relative to 1850-1900; the model's driver to
    2024) and data/sources/hadcrut5/t_glac_hadcrut5.csv (column gmst_hadcrut5_C: HadCRUT5 global mean, same product
    and baseline). The working-tree copies are checked against the v1.0.0 tag before use.
  - GTN-G (2023) first-order glacier regions, doi:10.5904/gtng-glacreg-2023-07 (20 regions: RGI 6's region 19 is
    split into 19, the islands and coastal ring, and 20, the Antarctic mainland).
  - Land outline: the R `maps` package "world" database, exported once by Rscript (no download).
Block membership is read from Ladrillo's data/constants/glacier_block_constants.csv, not typed here.

Outputs in OUT_DIR: the two figures (PNG at DPI, plus PDF), the plotted series as CSV with a provenance column, and
the exported land layer. No random numbers are used.
"""
import hashlib
import os
import subprocess

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402

# ---- paths -----------------------------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LADRILLO = os.path.join(os.path.dirname(REPO), "Ladrillo")
LADRILLO_TAG = "v1.0.0"
LADRILLO_DOI = "10.5281/zenodo.24445689"
BLOCK_T_REL = "data/drivers/glacier_block_temperature.csv"
GMST_REL = "data/sources/hadcrut5/t_glac_hadcrut5.csv"
BLOCK_CONST_REL = "data/constants/glacier_block_constants.csv"
GMST_COL = "gmst_hadcrut5_C"
REGIONS_SHP = os.path.join(REPO, "data/observations/raw/GlacReg_2023/GTN-G_202307_o1regions.shp")
REGIONS_CITE = "GTN-G (2023) glacier regions"
OUT_TAG = "20261127"
OUT_DIR = os.path.join(REPO, "outputs", "substack", f"glacier_blocks_{OUT_TAG}")
LAND_GPKG = os.path.join(OUT_DIR, "world_land_rmaps.gpkg")
MAP_STEM = "glacier_blocks_map"
TEMP_STEM = "glacier_blocks_temperature"
CSV_NAME = "glacier_blocks_temperature_series.csv"
DPI = 200

# ---- choices (each is stated in the figure note and the README) -------------------------------------------------
BASELINE = (1850, 1900)          # the frame Ladrillo's drivers are in; asserted below, not re-baselined
SMOOTH_YEARS = 11                # centered running mean; no partial windows at the ends
INFILL_LAST_YEAR = 1897          # build_t_glac.py: missing region-years (all before 1898) are filled from the global series
INFILL_REGIONS = ["01", "03", "14", "15", "18"]   # build_t_glac.py notes (r01 1855); exact-collinearity check 11-27:
INFILL_R03 = (46, 48)            # r03 46 of 48 yrs 1850-97, r14 22 and r15 18 yrs before 1875, r18 1850-54
PROJ = "ESRI:54030"              # Robinson
PROJ_NAME = "Robinson projection"

# ---- entities: one color and one label per block, shared by both figures ---------------------------------------
BLOCKS = ["SLOWG", "FASTG", "R19"]       # Ladrillo's names, in the paper's order
COLOR = {"SLOWG": "#2a78d6", "FASTG": "#eb6834", "R19": "#1baf7a"}   # dataviz slots 1-3 (validated all-pairs on white)
NAME = {"SLOWG": "Slow-responding Arctic", "FASTG": "Faster-responding", "R19": "Antarctic and Subantarctic"}
GMST_NAME = "Global mean"
GMST_COLOR = "#52514e"
ICE_SHEET_REGIONS = {"05": "Greenland Periphery (with the Greenland ice sheet)",
                     "20": "Antarctic Mainland (the ice sheet)"}
ICE_SHEET_NAME = "Covered by the ice-sheet modules"
ICE_FILL, ICE_HATCH_INK = "#e6e5e0", "#8d8c86"
LAND, COAST, SURFACE, INK, INK2, GRID = "#d9d8d2", "#52514e", "#ffffff", "#0b0b0b", "#52514e", "#e6e5e0"
FONT = "Arial"

# ---- labels (derive from the constants above) -------------------------------------------------------------------
MAP_TITLE = "Ladrillo's three glacier blocks"
TEMP_TITLE = "Warming over Ladrillo's glacier blocks and the globe"
Y_LABEL = f"Temperature change from {BASELINE[0]}–{BASELINE[1]} (°C)"
TEMP_NOTE = (f"Thin lines: annual means. Thick lines: {SMOOTH_YEARS}-year centered averages. HadCRUT5, averaged over "
             f"each block's glacier regions weighted by glacier area in 2000.\nBefore {INFILL_LAST_YEAR + 1}, missing "
             f"years in {len(INFILL_REGIONS)} regions ({INFILL_R03[0]} of the {INFILL_R03[1]} years for Arctic Canada "
             f"North) are filled from the global series.")
MAP_NOTE = f"Region outlines: {REGIONS_CITE}. {PROJ_NAME}."

plt.rcParams.update({"font.family": FONT, "font.size": 12, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def ladrillo_file(rel):
    """The working-tree file, after checking it is byte-identical to the release tag."""
    path = os.path.join(LADRILLO, rel)
    tagged = subprocess.run(["git", "-C", LADRILLO, "show", f"{LADRILLO_TAG}:{rel}"], capture_output=True,
                            check=True).stdout
    assert open(path, "rb").read() == tagged, f"{rel} differs from Ladrillo {LADRILLO_TAG}"
    return path


def git_head(repo):
    return subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def block_members():
    c = pd.read_csv(ladrillo_file(BLOCK_CONST_REL), dtype={"members": str})
    m = {r.block: str(r.members).split("|") for r in c.itertuples()}
    assert set(m) == set(BLOCKS), m
    return m


def land_layer():
    if not os.path.exists(LAND_GPKG):
        r = ('suppressMessages({library(sf); library(maps)}); sf::sf_use_s2(FALSE); '
             'w <- sf::st_as_sf(maps::map("world", fill=TRUE, plot=FALSE, wrap=c(-180,180))); '
             'w <- sf::st_make_valid(w); sf::st_write(w, commandArgs(TRUE)[1], quiet=TRUE)')
        subprocess.run(["Rscript", "-e", r, LAND_GPKG], check=True)
    return gpd.read_file(LAND_GPKG)


def globe_outline(n=721):
    lon = np.linspace(-180, 180, n)
    lat = np.linspace(-90, 90, n)
    ring = ([(x, -90) for x in lon] + [(180, y) for y in lat] + [(x, 90) for x in lon[::-1]]
            + [(-180, y) for y in lat[::-1]])
    return gpd.GeoSeries([Polygon(ring)], crs="EPSG:4326").to_crs(PROJ)


# ---- figure 1: map ----------------------------------------------------------------------------------------------
LABEL_NUDGE = {"07": (0, 2e5), "04": (2e5, -2e5), "18": (5e5, 0), "11": (-2e5, -2e5),
               "12": (-2e5, -4e5), "14": (-6e5, 1e5), "15": (4e5, -3e5), "13": (0, 3e5)}


def make_map(members):
    reg = gpd.read_file(REGIONS_SHP)
    block_of = {r: b for b, rs in members.items() for r in rs}
    allowed = set(block_of) | set(ICE_SHEET_REGIONS)
    assert set(reg.o1region) == allowed, sorted(set(reg.o1region) ^ allowed)
    reg["block"] = reg.o1region.map(block_of).fillna("ICE")
    reg = reg.to_crs(PROJ)
    land = land_layer().to_crs(PROJ)
    globe = globe_outline()

    fig = plt.figure(figsize=(11, 7.0), dpi=DPI)
    ax = fig.add_axes([0.01, 0.15, 0.98, 0.76])
    fig.patch.set_facecolor(SURFACE)
    globe.plot(ax=ax, facecolor=SURFACE, edgecolor=GRID, linewidth=1.0, zorder=0)
    land.plot(ax=ax, facecolor=LAND, edgecolor="none", zorder=1)
    ice = reg[reg.block == "ICE"]
    ice.plot(ax=ax, facecolor=ICE_FILL, edgecolor=ICE_HATCH_INK, hatch="////", linewidth=0, alpha=0.9, zorder=2)
    for b in BLOCKS:
        reg[reg.block == b].plot(ax=ax, facecolor=COLOR[b], edgecolor="none", alpha=0.78, zorder=2)
    reg.boundary.plot(ax=ax, color=SURFACE, linewidth=1.0, zorder=3)                 # 2px-style surface gap
    land.boundary.plot(ax=ax, color=COAST, linewidth=0.25, alpha=0.55, zorder=4)
    globe.boundary.plot(ax=ax, color=INK2, linewidth=0.6, zorder=5)

    done = set()
    for r in reg.sort_values("o1region").itertuples():
        if r.o1region in done:
            continue
        geom = reg[reg.o1region == r.o1region].geometry.union_all()
        part = max(getattr(geom, "geoms", [geom]), key=lambda g: g.area)
        p = part.representative_point()
        dx, dy = LABEL_NUDGE.get(r.o1region, (0, 0))
        ax.text(p.x + dx, p.y + dy, r.o1region, ha="center", va="center", fontsize=9, fontweight="bold", color=INK,
                zorder=6, bbox=dict(boxstyle="round,pad=0.15", facecolor=SURFACE, edgecolor="none", alpha=0.85))
        done.add(r.o1region)

    rgi = lambda b: ", ".join(sorted(members[b]))  # noqa: E731
    handles = [Patch(facecolor=COLOR["SLOWG"], alpha=0.78, label=f"{NAME['SLOWG']}: RGI {rgi('SLOWG')}"),
               Patch(facecolor=COLOR["FASTG"], alpha=0.78, label=f"{NAME['FASTG']}: {len(members['FASTG'])} other regions"),
               Patch(facecolor=COLOR["R19"], alpha=0.78, label=f"{NAME['R19']}: RGI {rgi('R19')}"),
               Patch(facecolor=ICE_FILL, edgecolor=ICE_HATCH_INK, hatch="////",
                     label=f"{ICE_SHEET_NAME}: {', '.join(sorted(ICE_SHEET_REGIONS))}")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, fontsize=11,
              handlelength=1.6, handleheight=1.1, columnspacing=1.6)
    ax.set_axis_off()
    fig.text(0.015, 0.975, MAP_TITLE, fontsize=16, fontweight="bold", ha="left", va="top")
    fig.text(0.015, 0.012, MAP_NOTE, fontsize=9, color=INK2, ha="left", va="bottom")
    meta = {"Title": MAP_TITLE, "Description": provenance()}
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT_DIR, f"{MAP_STEM}.{ext}"), dpi=DPI, facecolor=SURFACE, bbox_inches="tight",
                    pad_inches=0.15,
                    metadata=meta if ext == "png" else {"Title": MAP_TITLE, "Subject": provenance()})
    plt.close(fig)


# ---- figure 2: temperatures -------------------------------------------------------------------------------------
def series():
    t = pd.read_csv(ladrillo_file(BLOCK_T_REL))
    g = pd.read_csv(ladrillo_file(GMST_REL))[["year", GMST_COL]]
    d = t.merge(g, on="year", how="inner").rename(columns={GMST_COL: "GMST"})
    assert d.year.is_monotonic_increasing and d.year.diff().dropna().eq(1).all()
    base = d[(d.year >= BASELINE[0]) & (d.year <= BASELINE[1])][BLOCKS + ["GMST"]].mean()
    assert base.abs().max() < 1e-9, f"not on a {BASELINE} baseline: {base.to_dict()}"
    for c in BLOCKS + ["GMST"]:
        d[f"{c}_smooth"] = d[c].rolling(SMOOTH_YEARS, center=True, min_periods=SMOOTH_YEARS).mean()
    return d


def place_labels(ys, gap):
    """Nudge end labels apart by at least `gap`, keeping their order."""
    order = np.argsort(ys)
    out = np.array(ys, float)
    for k in range(1, len(order)):
        i, j = order[k], order[k - 1]
        out[i] = max(out[i], out[j] + gap)
    return out


def make_temps(d):
    fig, ax = plt.subplots(figsize=(11, 6.4), dpi=DPI)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axhline(0, color=INK2, linewidth=0.8, zorder=1)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ent = [(b, COLOR[b], NAME[b]) for b in BLOCKS] + [("GMST", GMST_COLOR, GMST_NAME)]
    for c, col, lab in ent:
        ax.plot(d.year, d[c], color=col, linewidth=1.0, alpha=0.35, zorder=2)
    for c, col, lab in ent:
        ax.plot(d.year, d[f"{c}_smooth"], color=col, linewidth=2.4, zorder=3, label=lab,
                solid_capstyle="round")
    last = d.dropna(subset=[f"{c}_smooth" for c, _, _ in ent]).iloc[-1]
    LABEL_X = d.year.max() + 3            # end labels start right of the last annual value
    ys = place_labels([last[f"{c}_smooth"] for c, _, _ in ent], gap=0.17)
    for (c, col, lab), y in zip(ent, ys):
        ax.plot([last.year + 0.8, LABEL_X - 0.8], [last[f"{c}_smooth"], y], color=col, linewidth=0.8, alpha=0.8)
        ax.text(LABEL_X, y, lab, color=INK, fontsize=11, va="center", ha="left")
    ax.set_xlim(d.year.min(), d.year.max() + 44)
    ax.spines["bottom"].set_bounds(d.year.min(), d.year.max())
    ax.set_xticks(range(1850, 2030, 25))
    ax.set_ylabel(Y_LABEL)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=11)
    ax.set_title(TEMP_TITLE, loc="left", fontsize=16, fontweight="bold", pad=10)
    fig.text(0.01, 0.01, TEMP_NOTE, fontsize=9, color=INK2, ha="left", va="bottom")
    fig.subplots_adjust(left=0.08, right=0.99, top=0.92, bottom=0.17)
    meta = {"Title": TEMP_TITLE, "Description": provenance()}
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT_DIR, f"{TEMP_STEM}.{ext}"), dpi=DPI, facecolor=SURFACE,
                    metadata=meta if ext == "png" else {"Title": TEMP_TITLE, "Subject": provenance()})
    plt.close(fig)


_PROV = None


def provenance():
    global _PROV
    if _PROV is None:
        _PROV = (f"Ladrillo.jl {LADRILLO_TAG} (doi:{LADRILLO_DOI}) {BLOCK_T_REL} md5 "
                 f"{md5(os.path.join(LADRILLO, BLOCK_T_REL))[:8]}, {GMST_REL}:{GMST_COL} md5 "
                 f"{md5(os.path.join(LADRILLO, GMST_REL))[:8]}; HadCRUT5.0.2.0 analysis, relative to "
                 f"{BASELINE[0]}-{BASELINE[1]}, degC; smoothing {SMOOTH_YEARS}-yr centered; regions {REGIONS_CITE} "
                 f"md5 {md5(REGIONS_SHP)[:8]}; land R maps 'world'; {PROJ}; script python/substack_glacier_blocks.py "
                 f"at SLR-RFF-BRICK {git_head(REPO)}; no RNG")
    return _PROV


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    members = block_members()
    d = series()
    make_map(members)
    make_temps(d)
    out = d.copy()
    out.insert(len(out.columns), "provenance", "")
    out.loc[out.index[0], "provenance"] = provenance()
    out.to_csv(os.path.join(OUT_DIR, CSV_NAME), index=False, float_format="%.5f")
    last = d.dropna(subset=["GMST_smooth"]).iloc[-1]
    print(f"wrote {OUT_DIR}")
    print(f"{SMOOTH_YEARS}-yr means centered on {int(last.year)} (degC rel. {BASELINE[0]}-{BASELINE[1]}): "
          + ", ".join(f"{NAME.get(c, GMST_NAME)} {last[c + '_smooth']:.2f}" for c in BLOCKS + ["GMST"]))
    print(f"ratio to global: " + ", ".join(f"{NAME[c]} {last[c + '_smooth'] / last['GMST_smooth']:.2f}" for c in BLOCKS))


if __name__ == "__main__":
    main()
