"""Substack graphics (Marcus 2026-11-27): Ladrillo's three glacier blocks on a map of the first-order glacier regions,
and the temperature over each block and southern Greenland next to global mean temperature, 1900-2050: HadCRUT5 to
2024, then Ladrillo's own continuation of its drivers on FaIR's van Vuuren Medium global temperature.

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
the exported land layer. The only random numbers pair posterior draws with FaIR configs for the joint-arm check
(JOINT_SEED, recorded in the CSV); the plotted lines do not use them.
"""
import hashlib
import os
import subprocess
import textwrap

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

# ---- Ladrillo inputs for the 2025-2050 continuation (fixed-climate arm; see src/model.jl, src/forcing.jl) ---------
GIS_T_REL = "data/drivers/greenland_zone_temperature.csv"
GIS_ZONE = "south"                              # src/posterior.jl GIS_ZONE
POSTERIOR_REL = "data/posterior/ladrillo_L27_posterior.csv"
GIS_SHAPE_REL = "data/constants/gis_amp_shape.csv"
SCENARIO = "vvM"
SCENARIO_NAME = "van Vuuren et al. (2026) Medium"
FORCING_MEAN_REL = f"data/forcing/fair_mean_gmst_{SCENARIO}.csv"
FORCING_CUBE_REL = f"data/forcing/fair_cube_gmst_{SCENARIO}_raw.csv"
FAIR_LABEL = "FaIR 2.2.4 (calib 1.6.0)"
PROJ_ROW_STEP = 5                               # posterior rows 1:5:10000, the projection draws (scripts/project_joint.jl)
MODEL_YEARS = (1850, 2300)
ANCHOR_YEARS = 11                               # src/model.jl ANCHOR_YEARS
LAST_OBS_YEAR = 2024                            # last year of the observed drivers (asserted against the files)
GIS_SHAPE_WINDOW = 30                           # src/model.jl GIS_SHAPE_WINDOW
SPLICE_YEAR, SPLICE_REF = 2014, (1995, 2014)    # src/forcing.jl, joint-arm check only
JOINT_SEED = 20261127                           # pairs draws with FaIR configs for the joint-arm check (not Ladrillo's pairing)
CHECK_CSV = f"ladrillo_drivers_{SCENARIO}_check.csv"   # written by julia/substack_glacier_blocks_check.jl
CHECK_TOL = 1e-9

# ---- choices (each is stated in the figure note and the README) -------------------------------------------------
BASELINE = (1850, 1900)          # the frame Ladrillo's drivers are in; asserted below, not re-baselined
SMOOTH_YEARS = 11                # centered running mean; no partial windows
INFILL_LAST_YEAR = 1897          # source extraction fills some region-years before 1898 from the global series;
                                 # smoothing windows start after it, so no filled year enters a plotted value
PLOT_START, PLOT_END = 1900, 2050
PROJ = "ESRI:54030"              # Robinson
PROJ_NAME = "Robinson projection"

# ---- entities: one color and one label per series, shared by both figures --------------------------------------
BLOCKS = ["SLOWG", "FASTG", "R19"]       # Ladrillo's names, in the paper's order
COLOR = {"SLOWG": "#2a78d6", "FASTG": "#eb6834", "R19": "#1baf7a", "GIS": "#eda100"}   # dataviz slots 1-4
NAME = {"SLOWG": "Slow-responding Arctic", "FASTG": "Faster-responding", "R19": "Antarctic and Subantarctic",
        "GIS": "Southern Greenland"}
GMST_NAME = "Global mean"
GMST_COLOR = "#52514e"
SERIES = BLOCKS + ["GIS", "GMST"]
ICE_SHEET_REGIONS = {"05": "Greenland Periphery (with the Greenland ice sheet)",
                     "20": "Antarctic Mainland (the ice sheet)"}
ICE_SHEET_NAME = "Covered by the ice-sheet modules"
ICE_FILL, ICE_HATCH_INK = "#e6e5e0", "#8d8c86"
LAND, COAST, SURFACE, INK, INK2, GRID, SHADE = "#d9d8d2", "#52514e", "#ffffff", "#0b0b0b", "#52514e", "#e6e5e0", "#f4f3ef"
FONT = "Arial"

# ---- labels (derive from the constants above) -------------------------------------------------------------------
MAP_TITLE = "Ladrillo's three glacier blocks"
TEMP_TITLE = "Warming over Ladrillo's glacier blocks, southern Greenland and the globe"
Y_LABEL = f"Temperature change from {BASELINE[0]}–{BASELINE[1]} (°C)"
PROJ_TAG = "Projection:\n" + textwrap.fill(SCENARIO_NAME, 17)
NOTE_WRAP = 165                  # characters per note line
TEMP_NOTE = (f"Thin lines: annual HadCRUT5 means. Thick lines: {SMOOTH_YEARS}-year centered averages. Glacier blocks are "
             f"averaged over their regions, weighted by glacier area in 2000; southern Greenland is 59–70° N. | "
             f"Dashed lines: Ladrillo's continuation for {SCENARIO_NAME}, from {FAIR_LABEL}'s ensemble-mean global "
             f"temperature. Each region keeps its {LAST_OBS_YEAR - ANCHOR_YEARS + 1}–{LAST_OBS_YEAR} observed mean and "
             f"adds its amplification\n(posterior median) times the change in global temperature from that period; "
             f"Greenland's amplification also varies with the warming level.")
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
def observed():
    t = pd.read_csv(ladrillo_file(BLOCK_T_REL))
    gz = pd.read_csv(ladrillo_file(GIS_T_REL))[["year", GIS_ZONE]].rename(columns={GIS_ZONE: "GIS"})
    g = pd.read_csv(ladrillo_file(GMST_REL))[["year", GMST_COL]].rename(columns={GMST_COL: "GMST"})
    d = t.merge(gz, on="year", how="inner").merge(g, on="year", how="inner")
    assert d.year.is_monotonic_increasing and d.year.diff().dropna().eq(1).all()
    assert d.year.max() == t.year.max() == gz.year.max() == LAST_OBS_YEAR, "drivers end in different years"
    base = d[(d.year >= BASELINE[0]) & (d.year <= BASELINE[1])][SERIES].mean()
    assert base.abs().max() < 1e-9, f"not on a {BASELINE} baseline: {base.to_dict()}"
    for c in SERIES:
        x = d[c].where(d.year > INFILL_LAST_YEAR)
        d[f"{c}_smooth"] = x.rolling(SMOOTH_YEARS, center=True, min_periods=SMOOTH_YEARS).mean()
    return d


def running_mean(v, w):
    """src/model.jl running_mean: centred, shrinking at the ends."""
    n, lo, hi = len(v), (w - 1) // 2, w // 2
    return np.array([v[max(0, i - lo):min(n, i + hi + 1)].mean() for i in range(n)])


def continuation(gmst, obs, amp, gis_amp, shape_tbl):
    """src/model.jl glacier_driver / greenland_driver on one GMST path (years MODEL_YEARS, K rel. ~1850-1900)."""
    years = np.arange(MODEL_YEARS[0], MODEL_YEARS[1] + 1)
    g = np.asarray(gmst, float)
    gmst_rb = g - g[(years >= BASELINE[0]) & (years <= BASELINE[1])].mean()
    last_obs = int(obs.year.max())
    anch = (years > last_obs - ANCHOR_YEARS) & (years <= last_obs)
    obs_on = obs.set_index("year").reindex(years)
    out = {"GMST": gmst_rb}
    for b in BLOCKS:
        a = obs_on[b].values[anch].mean()
        out[b] = np.where(years <= last_obs, obs_on[b].values, amp[b] * gmst_rb + (a - amp[b] * gmst_rb[anch].mean()))
    shape = np.interp(running_mean(gmst_rb, GIS_SHAPE_WINDOW), shape_tbl.dt.values, shape_tbl.S.values)
    a = obs_on["GIS"].values[anch].mean()
    out["GIS"] = np.where(years <= last_obs, obs_on["GIS"].values,
                          gis_amp * shape * gmst_rb + (a - gis_amp * (shape[anch] * gmst_rb[anch]).mean()))
    return pd.DataFrame({"year": years, **out})


def projections(obs):
    post = pd.read_csv(ladrillo_file(POSTERIOR_REL)).iloc[::PROJ_ROW_STEP]
    assert len(post) == 2000
    amp = {b: float(np.median(post[f"gic_amp_{b}"])) for b in BLOCKS}
    gis_amp = float(np.median(post.gis_amp))
    shape_tbl = pd.read_csv(ladrillo_file(GIS_SHAPE_REL))
    years = np.arange(MODEL_YEARS[0], MODEL_YEARS[1] + 1)
    mean = pd.read_csv(ladrillo_file(FORCING_MEAN_REL)).set_index("year").gmst_C.reindex(years).values
    fixed = continuation(mean, obs, amp, gis_amp, shape_tbl)

    ## joint-arm check: each projection draw paired with one FaIR config (spliced at 2014), median over the pairs
    cube = pd.read_csv(ladrillo_file(FORCING_CUBE_REL)).set_index("year").reindex(years)
    cfg = [c for c in cube.columns if c.startswith("cfg_")]
    ref = (years >= SPLICE_REF[0]) & (years <= SPLICE_REF[1])
    rng = np.random.default_rng(JOINT_SEED)
    pick = np.resize(rng.permutation(len(cfg)), len(post))
    paths = []
    for k, (_, row) in enumerate(post.iterrows()):
        raw = cube[cfg[pick[k]]].values
        g = np.where(years <= SPLICE_YEAR, mean, mean[ref].mean() + raw - raw[ref].mean())
        paths.append(continuation(g, obs, {b: row[f"gic_amp_{b}"] for b in BLOCKS}, row.gis_amp, shape_tbl))
    joint = pd.DataFrame({"year": years, **{c: np.median(np.vstack([p[c].values for p in paths]), axis=0)
                                            for c in SERIES}})
    return fixed, joint, amp, gis_amp


def check_against_ladrillo(fixed):
    """Gate: the Python continuation equals Ladrillo's own Julia driver functions on the same inputs."""
    path = os.path.join(OUT_DIR, CHECK_CSV)
    if not os.path.exists(path):
        raise SystemExit(f"run first: julia --project=../Ladrillo julia/substack_glacier_blocks_check.jl {SCENARIO} "
                         f"{os.path.relpath(path, REPO)}")
    j = pd.read_csv(path)
    assert (j.year.values == fixed.year.values).all()
    col = {"GMST": "gmst_rb", "GIS": "south", **{b: b for b in BLOCKS}}
    worst = {c: float(np.abs(fixed[c].values - j[col[c]].values).max()) for c in SERIES}
    ok = max(worst.values()) < CHECK_TOL
    print(("PASS" if ok else "FAIL") + f" python continuation == Ladrillo Julia drivers (max |diff| by series {worst})")
    return ok


def place_labels(ys, gap):
    """Nudge end labels apart by at least `gap`, keeping their order."""
    order = np.argsort(ys)
    out = np.array(ys, float)
    for k in range(1, len(order)):
        i, j = order[k], order[k - 1]
        out[i] = max(out[i], out[j] + gap)
    return out


def make_temps(obs, fixed):
    o = obs[obs.year >= PLOT_START]
    last_obs = int(obs.year.max())
    f = fixed[(fixed.year > last_obs) & (fixed.year <= PLOT_END)]
    fig, ax = plt.subplots(figsize=(11, 6.8), dpi=DPI)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axvspan(last_obs + 0.5, PLOT_END + 0.5, color=SHADE, zorder=0, linewidth=0)
    ax.axhline(0, color=INK2, linewidth=0.8, zorder=1)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0.5)
    ent = [(b, COLOR[b], NAME[b]) for b in BLOCKS + ["GIS"]] + [("GMST", GMST_COLOR, GMST_NAME)]
    for c, col, lab in ent:
        ax.plot(o.year, o[c], color=col, linewidth=1.0, alpha=0.35, zorder=2)
    for c, col, lab in ent:
        ax.plot(o.year, o[f"{c}_smooth"], color=col, linewidth=2.4, zorder=3, label=lab, solid_capstyle="round")
        ax.plot(f.year, f[c], color=col, linewidth=2.4, linestyle=(0, (3, 1.6)), zorder=3)
    end = f.iloc[-1]
    label_x = PLOT_END + 2.5
    ys = place_labels([end[c] for c, _, _ in ent], gap=0.22)
    for (c, col, lab), y in zip(ent, ys):
        ax.plot([PLOT_END + 0.6, label_x - 0.6], [end[c], y], color=col, linewidth=0.8, alpha=0.8)
        ax.text(label_x, y, lab, color=INK, fontsize=11, va="center", ha="left")
    ax.text(last_obs + 1.5, 0.02, PROJ_TAG, transform=ax.get_xaxis_transform(), fontsize=10, color=INK2,
            va="bottom", ha="left", linespacing=1.3)
    ax.set_xlim(PLOT_START, PLOT_END + 34)
    ax.spines["bottom"].set_bounds(PLOT_START, PLOT_END)
    ax.set_xticks(range(PLOT_START, PLOT_END + 1, 25))
    ax.set_ylabel(Y_LABEL)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=11)
    ax.set_title(TEMP_TITLE, loc="left", fontsize=16, fontweight="bold", pad=10)
    note = "\n".join(textwrap.fill(para, NOTE_WRAP) for para in TEMP_NOTE.replace("\n", " ").split(" | "))
    fig.text(0.01, 0.01, note, fontsize=9, color=INK2, ha="left", va="bottom")
    fig.subplots_adjust(left=0.08, right=0.99, top=0.92, bottom=0.2)
    meta = {"Title": TEMP_TITLE, "Description": provenance()}
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT_DIR, f"{TEMP_STEM}.{ext}"), dpi=DPI, facecolor=SURFACE,
                    metadata=meta if ext == "png" else {"Title": TEMP_TITLE, "Subject": provenance()})
    plt.close(fig)


_PROV = None
_AMPS = ""


def provenance():
    global _PROV
    if _PROV is None:
        m = lambda rel: md5(os.path.join(LADRILLO, rel))[:8]  # noqa: E731
        _PROV = (f"Ladrillo.jl {LADRILLO_TAG} (doi:{LADRILLO_DOI}): {BLOCK_T_REL} {m(BLOCK_T_REL)}, "
                 f"{GIS_T_REL}:{GIS_ZONE} {m(GIS_T_REL)}, {GMST_REL}:{GMST_COL} {m(GMST_REL)} (HadCRUT5.0.2.0 analysis, "
                 f"rel. {BASELINE[0]}-{BASELINE[1]}, degC); continuation = src/model.jl glacier_driver/greenland_driver "
                 f"on {FORCING_MEAN_REL} {m(FORCING_MEAN_REL)} ({FAIR_LABEL}, fixed-climate arm) at the posterior-median "
                 f"amplifications of {POSTERIOR_REL} {m(POSTERIOR_REL)} rows 1:{PROJ_ROW_STEP}:10000 ({_AMPS}); joint "
                 f"columns: median over 2000 draw-config pairs from {FORCING_CUBE_REL} {m(FORCING_CUBE_REL)}, numpy "
                 f"default_rng seed {JOINT_SEED} applied to the config permutation; smoothing {SMOOTH_YEARS}-yr centered "
                 f"on years > {INFILL_LAST_YEAR}; regions {REGIONS_CITE} md5 {md5(REGIONS_SHP)[:8]}; land R maps "
                 f"'world'; {PROJ}; script python/substack_glacier_blocks.py at SLR-RFF-BRICK {git_head(REPO)}")
    return _PROV


def main():
    global _AMPS
    os.makedirs(OUT_DIR, exist_ok=True)
    members = block_members()
    obs = observed()
    fixed, joint, amp, gis_amp = projections(obs)
    _AMPS = " ".join(f"{b} {amp[b]:.4f}" for b in BLOCKS) + f" GIS {gis_amp:.4f}"
    if not check_against_ladrillo(fixed):
        raise SystemExit("the continuation does not match Ladrillo; no figures written")
    make_map(members)
    make_temps(obs, fixed)
    out = pd.DataFrame({"year": fixed.year[(fixed.year >= BASELINE[0]) & (fixed.year <= PLOT_END)]})
    out = out.merge(obs[["year"] + SERIES + [f"{c}_smooth" for c in SERIES]].rename(
        columns={c: f"{c}_obs" for c in SERIES}), on="year", how="left")
    out = out.merge(fixed.rename(columns={c: f"{c}_proj_fixed" for c in SERIES}), on="year", how="left")
    out = out.merge(joint.rename(columns={c: f"{c}_proj_joint_median" for c in SERIES}), on="year", how="left")
    last_obs = int(obs.year.max())
    for c in SERIES:
        for k in ("fixed", "joint_median"):
            out.loc[out.year <= last_obs, f"{c}_proj_{k}"] = np.nan
    out["provenance"] = ""
    out.loc[out.index[0], "provenance"] = provenance()
    out.to_csv(os.path.join(OUT_DIR, CSV_NAME), index=False, float_format="%.5f")
    print(f"wrote {OUT_DIR}")
    o = obs.set_index("year")
    f, j = fixed.set_index("year"), joint.set_index("year")
    w = slice(last_obs - ANCHOR_YEARS + 1, last_obs)
    print(f"GMST {w.start}-{w.stop} mean: HadCRUT5 {o.loc[w, 'GMST'].mean():.3f}, FaIR mean (rebased) "
          f"{f.loc[w, 'GMST'].mean():.3f}")
    print(f"{PLOT_END}, fixed arm (joint-arm median; difference), degC rel. {BASELINE[0]}-{BASELINE[1]}:")
    for c in SERIES:
        print(f"  {NAME.get(c, GMST_NAME):28s} {f.loc[PLOT_END, c]:.3f} ({j.loc[PLOT_END, c]:.3f}; "
              f"{f.loc[PLOT_END, c] - j.loc[PLOT_END, c]:+.3f})")
    print(f"  ratio to global at {PLOT_END} (fixed): " + ", ".join(
        f"{NAME[c]} {f.loc[PLOT_END, c] / f.loc[PLOT_END, 'GMST']:.2f}" for c in BLOCKS + ["GIS"]))


if __name__ == "__main__":
    main()
