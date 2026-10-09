#!/usr/bin/env python3
"""The climate-swap figure: Ladrillo, BRICK 2.0 and MAGICC-SLR by component on the van Vuuren
markers, with Ladrillo and BRICK 2.0 shown BOTH on the shared FaIR driver and on MAGICC's own
climate — so the reader sees how much of each model-vs-MAGICC gap is the climate and how much
survives the swap (Marcus, 9/11b comment [8]).

  python3 python/plot_vv_climate_swap.py [--tag=L27] [--year=2300|2100|2150|all]
Reads  outputs/vv_model_comparison_<TAG>.csv                       Ladrillo/BRICK on FaIR, MAGICC-SLR
       outputs/scope_slr_fairunc_cells_<m>_spliced_magiccclim_<TAG>_<tap>.csv   Ladrillo on MAGICC's climate
       outputs/scope_slr_fairunc_cells_<m>_spliced_oldbrick_magiccclim.csv      BRICK 2.0 on MAGICC's climate
Writes figures/vv_climate_swap_<TAG>_<year>.png and outputs/vv_climate_swap_<TAG>.csv (stamped).

CONVENTIONS (all inherited, none new): cm rel 1995-2014; JOINT arms (posterior x climate
ensemble); the SPLICED injection convention for the swapped arms (Marcus 2026-08-31: spliced
primary, raw as check -- worth 0.00 cm for TE/glaciers/LWS and up to -43 cm for AIS at
ssp245/2300, memory `ladrillo_on_magicc_climate`). Only the driving climate changes between a
model's two points: posterior, tap, modules and DRAWS are identical. FACTS is not drawn: it has
no MAGICC-climate arm.

COMMON DRAW SET (Marcus 2026-10-08). Ladrillo's FaIR joint arm is record-conditioned: it drops each
draw whose Antarctic fast dynamics fire by the record end on its OWN FaIR config (187 and 610 on
every marker). The MAGICC-climate arm is NOT conditioned (the 10-08 ruling's scope). The swap holds
the draws fixed and moves only the climate, so Ladrillo's MAGICC point is recomputed here from that
arm's per-draw file on the FaIR arm's kept draws. The shipped MAGICC arm is untouched. BRICK 2.0 is
conditioned on neither climate and is read as shipped.
GATES:
  [SOURCE-MATCH]       the comparison table's FaIR-arm cells equal the driver's cells files. A stale
                       comparison table paired with fresh MAGICC arms is exactly how the 10-08 retry
                       wrote a mixed-vintage swap (quarantine 20261008_vv_climate_swap_mixed_vintage).
  [RECOMPUTE-IDENTITY] recomputing the MAGICC cells from the per-draw file with NO drop reproduces
                       the driver's own cells, so the common-set statistic is the driver's statistic.
  [ARM-MATCH]          keyed by DRAW: a model's two points carry the same draw ids, and every draw
                       removed from the MAGICC point is one the FaIR arm's gates list as REJECTED.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ladrillo_figs as lf  # noqa: E402
from provenance import stamp  # noqa: E402

import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L27")
_y = next((a[len("--year="):] for a in sys.argv[1:] if a.startswith("--year=")), "2300")
HORIZONS = [2100, 2150, 2300]
YEARS = HORIZONS if _y == "all" else [int(_y)]
DESC = lf.tag_desc(TAG)
CMP_CSV = os.path.join(lf.REPO, "outputs", "vv_model_comparison_%s.csv" % TAG)
## The tap stem the joint driver writes (mirrors vv_model_comparison.joint_stem); read from
## the comparison table's own provenance rather than retyped: the FaIR-arm cells file name.
TAP_STEM = lf.joint_stem("")[1:]          # "tap..." with no leading underscore
LAD_MAG = os.path.join(lf.REPO, "outputs",
                       "scope_slr_fairunc_cells_%%s_spliced_magiccclim_%s_%s.csv" % (TAG, TAP_STEM))
BRK_MAG = os.path.join(lf.REPO, "outputs", "scope_slr_fairunc_cells_%s_spliced_oldbrick_magiccclim.csv")
## The per-draw files and the FaIR arm's gates, for the common draw set and the source checks.
LAD_FAIR = os.path.join(lf.REPO, "outputs", "scope_slr_fairunc_cells_%%s_spliced_%s_%s.csv" % (TAG, TAP_STEM))
BRK_FAIR = os.path.join(lf.REPO, "outputs", "scope_slr_fairunc_cells_%s_spliced_oldbrick.csv")
LAD_FAIR_DRAWS = LAD_FAIR.replace("_cells_", "_draws_")
LAD_FAIR_GATES = LAD_FAIR.replace("_cells_", "_gates_")
LAD_MAG_DRAWS = LAD_MAG.replace("_cells_", "_draws_")
## Identity tolerances, cm. The two sides are the same draws through two code paths (Julia's and
## numpy's type-7 quantile), so only float noise separates them: measured 5.7e-14 on 10-08. The
## mixed-vintage swap this guards against was off by 10.4 cm (Ladrillo) and 13.7 cm (BRICK 2.0).
IDENTITY_TOL_CM = 1e-9
OUT_CSV = os.path.join(lf.REPO, "outputs", "vv_climate_swap_%s.csv" % TAG)

## Five arms, two of them "the same model on the other climate". Open marker = MAGICC's climate.
ARMS = [("Ladrillo", "fair"), ("Ladrillo", "magicc"), ("BRICK 2.0", "fair"), ("BRICK 2.0", "magicc"),
        ("MAGICC-SLR", "magicc")]
SLOT = {("Ladrillo", "fair"): -0.30, ("Ladrillo", "magicc"): -0.19,
        ("BRICK 2.0", "fair"): -0.04, ("BRICK 2.0", "magicc"): 0.07, ("MAGICC-SLR", "magicc"): 0.24}
MARK = {"Ladrillo": "s", "BRICK 2.0": "s", "MAGICC-SLR": "D"}
SCENS = lf.scen_set("vv")

# --- data --------------------------------------------------------------------------
D = pd.read_csv(CMP_CSV)
rows = []
for src in ("Ladrillo", "BRICK 2.0", "MAGICC-SLR"):
    s = D[D.source == src]
    for _, r in s.iterrows():
        rows.append(dict(source=src, climate="magicc" if src == "MAGICC-SLR" else "fair",
                         marker=r.marker, component=r.component, year=int(r.year),
                         med=r.med, p05=r.p05, p95=r.p95, n_draws=int(r.n_draws)))
def need(p, what):
    if not os.path.exists(p):
        raise SystemExit("missing %s: %s" % (what, os.path.relpath(p, lf.REPO)))
    return p


def joint_cells(p):
    c = pd.read_csv(need(p, "cells file"))
    return c[(c.arm == "joint") & c.horizon.isin(HORIZONS) & c.component.isin(lf.COMPONENTS)]


def cells_from_draws(d):
    """med/p05/p95/n_draws per component x horizon, as the Julia driver computes them (type-7)."""
    g = d.groupby(["component", "horizon"]).value_cm
    return pd.DataFrame({"med_cm": g.median(), "p05_cm": g.quantile(0.05), "p95_cm": g.quantile(0.95),
                         "n_draws": g.size()})


def worst(a, b):
    j = a.join(b, rsuffix="_b", how="outer")
    if j.isna().any().any() or (j.n_draws != j.n_draws_b).any():
        return np.inf
    return max(float((j[q] - j[q + "_b"]).abs().max()) for q in ("med_cm", "p05_cm", "p95_cm"))


## [SOURCE-MATCH] the comparison table's FaIR-arm cells must be the driver's current cells.
cmp_cells = D.rename(columns={"med": "med_cm", "p05": "p05_cm", "p95": "p95_cm", "year": "horizon"})
src_bad = []
for src, tmpl in (("Ladrillo", LAD_FAIR), ("BRICK 2.0", BRK_FAIR)):
    for k, _l, _c, _d in SCENS:
        a = joint_cells(tmpl % k).set_index(["component", "horizon"])[["med_cm", "p05_cm", "p95_cm", "n_draws"]]
        b = cmp_cells[(cmp_cells.source == src) & (cmp_cells.marker == k)
                      & cmp_cells.component.isin(lf.COMPONENTS) & cmp_cells.horizon.isin(HORIZONS)]
        w = worst(a, b.set_index(["component", "horizon"])[["med_cm", "p05_cm", "p95_cm", "n_draws"]])
        if not w <= IDENTITY_TOL_CM:
            src_bad.append("%s %s: %.3g cm" % (src, k, w))
if src_bad:
    raise SystemExit("[SOURCE-MATCH] %s does not match the FaIR-arm cells files (stale comparison table?):\n  %s"
                     % (os.path.relpath(CMP_CSV, lf.REPO), "\n  ".join(src_bad)))
print("[SOURCE-MATCH] the comparison table's Ladrillo and BRICK 2.0 FaIR cells equal the driver's, "
      "all %d markers (tol %.0e cm)" % (len(SCENS), IDENTITY_TOL_CM))

ident, match, n_common = [], [], {}
for src, tmpl in (("Ladrillo", LAD_MAG), ("BRICK 2.0", BRK_MAG)):
    for k, _l, _c, _d in SCENS:
        c = joint_cells(tmpl % k)
        if src == "Ladrillo":
            ## the common draw set: the MAGICC arm's draws minus the FaIR arm's REJECTED draws
            d = pd.read_csv(need(LAD_MAG_DRAWS % k, "MAGICC-climate per-draw file"))
            d = d[(d.arm == "joint") & d.horizon.isin(HORIZONS) & d.component.isin(lf.COMPONENTS)]
            ## [RECOMPUTE-IDENTITY] no drop -> the driver's own cells
            w = worst(cells_from_draws(d),
                      c.set_index(["component", "horizon"])[["med_cm", "p05_cm", "p95_cm", "n_draws"]])
            ident.append(w)
            if not w <= IDENTITY_TOL_CM:
                raise SystemExit("[RECOMPUTE-IDENTITY] %s: cells recomputed from %s differ from the driver's by "
                                 "%.3g cm" % (k, os.path.basename(LAD_MAG_DRAWS % k), w))
            gt = pd.read_csv(need(LAD_FAIR_GATES % k, "FaIR-arm gates"))
            rejected = {int(s.split("_")[1]) for s in gt[gt.gate == "REJECTED"].key}
            fd = pd.read_csv(need(LAD_FAIR_DRAWS % k, "FaIR-arm per-draw file"), usecols=["draw", "arm"])
            fair_ids = set(fd[fd.arm == "joint"].draw)
            mag_ids = set(d.draw)
            keep = mag_ids - rejected
            ## [ARM-MATCH] same draw ids on both climates; only REJECTED draws removed, and each one existed
            if keep != fair_ids or not rejected <= mag_ids:
                match.append("%s: FaIR %d ids, MAGICC %d, rejected %s, common-set mismatch %d"
                             % (k, len(fair_ids), len(mag_ids), sorted(rejected), len(keep ^ fair_ids)))
                continue
            n_common[k] = (len(keep), sorted(rejected))
            cc = cells_from_draws(d[d.draw.isin(keep)]).reset_index()
            for _, r in cc.iterrows():
                rows.append(dict(source=src, climate="magicc", marker=k, component=r.component,
                                 year=int(r.horizon), med=r.med_cm, p05=r.p05_cm, p95=r.p95_cm,
                                 n_draws=int(r.n_draws)))
        else:
            for _, r in c.iterrows():
                rows.append(dict(source=src, climate="magicc", marker=k, component=r.component,
                                 year=int(r.horizon), med=r.med_cm, p05=r.p05_cm, p95=r.p95_cm,
                                 n_draws=int(r.n_draws)))
print("[RECOMPUTE-IDENTITY] Ladrillo MAGICC cells from the per-draw files, no drop: max %.2e cm (tol %.0e)"
      % (max(ident), IDENTITY_TOL_CM))
R = pd.DataFrame(rows)
R = R[R.component.isin(lf.COMPONENTS) & R.year.isin(HORIZONS)]

## [ARM-MATCH] Ladrillo: by draw id (above). BRICK 2.0 is unconditioned on both climates, so its
## two points must simply carry the same count.
a = R[(R.source == "BRICK 2.0")].groupby(["marker", "climate"]).n_draws.first().unstack()
m = a[a.fair != a.magicc]
if len(m):
    match.append("BRICK 2.0: %s" % m.to_dict("index"))
if match:
    raise SystemExit("[ARM-MATCH] a model's FaIR and MAGICC points do not carry the same draws:\n  "
                     + "\n  ".join(match))
print("[ARM-MATCH] Ladrillo on the common draw set, by draw id: %s; BRICK 2.0 %d on both; MAGICC-SLR %d members."
      % ("; ".join("%s %d (dropped %s)" % (k, n, r) for k, (n, r) in n_common.items()),
         R[R.source == "BRICK 2.0"].n_draws.iloc[0], R[R.source == "MAGICC-SLR"].n_draws.iloc[0]))

# --- the swap table: for each model/marker/component/horizon, gap on FaIR, gap on MAGICC ---
piv = R.pivot_table(index=["source", "marker", "component", "year"], columns="climate", values="med")
mag = R[R.source == "MAGICC-SLR"].set_index(["marker", "component", "year"]).med
T = []
for (src, k, comp, y), r in piv.iterrows():
    if src == "MAGICC-SLR":
        continue
    m = mag.get((k, comp, y), np.nan)
    T.append(dict(source=src, marker=k, component=comp, year=y, med_fair=r.get("fair", np.nan),
                  med_magiccclim=r.get("magicc", np.nan), magicc_slr=m,
                  gap_on_fair=r.get("fair", np.nan) - m, gap_on_magicc=r.get("magicc", np.nan) - m,
                  climate_term=r.get("magicc", np.nan) - r.get("fair", np.nan)))
T = pd.DataFrame(T)
T = stamp(T, os.path.basename(__file__), tag=TAG,
          inputs={"comparison": CMP_CSV, "ladrillo_magiccclim": LAD_MAG_DRAWS % "<marker>",
                  "ladrillo_fair_gates": LAD_FAIR_GATES % "<marker>",
                  "brick_magiccclim": BRK_MAG % "<marker>"},
          extra="cm rel 1995-2014, joint arms, spliced injection; Ladrillo on the COMMON draw set (its "
                "MAGICC point drops the FaIR arm's record-conditioning REJECTED draws); gap_on_X = model "
                "median on climate X minus MAGICC-SLR's median; climate_term = med_magiccclim - med_fair")
T.to_csv(OUT_CSV, index=False)
print("wrote %s (%d rows)" % (os.path.relpath(OUT_CSV, lf.REPO), len(T)))

# --- figure ------------------------------------------------------------------------
for YEAR in YEARS:
    OUT = os.path.join(lf.REPO, "figures", "vv_climate_swap_%s_%d.png" % (TAG, YEAR))
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.4))
    for ax, comp in zip(axes.ravel(), lf.COMPONENTS):
        for i, (k, lab, _c, _d) in enumerate(SCENS):
            cell = R[(R.marker == k) & (R.component == comp) & (R.year == YEAR)]
            pts = {}
            for src, clim in ARMS:
                r = cell[(cell.source == src) & (cell.climate == clim)]
                if r.empty:
                    continue
                r = r.iloc[0]
                x = i + SLOT[(src, clim)]
                col = lf.SRC_COLOR[src]
                open_mk = clim == "magicc" and src != "MAGICC-SLR"
                ax.plot([x, x], [r.p05, r.p95], color=col, lw=0.9, alpha=0.6, zorder=2)
                ax.plot([x], [r.med], marker=MARK[src], ms=7, ls="none", color=col,
                        mfc="none" if open_mk else col, mec=col, mew=1.5, zorder=4)
                pts[(src, clim)] = (x, r.med)
            ## the swap, drawn: a thin connector from a model's FaIR point to its MAGICC point
            for src in ("Ladrillo", "BRICK 2.0"):
                if (src, "fair") in pts and (src, "magicc") in pts:
                    (x0, y0), (x1, y1) = pts[(src, "fair")], pts[(src, "magicc")]
                    ax.plot([x0, x1], [y0, y1], color=lf.SRC_COLOR[src], lw=1.0, alpha=0.8,
                            zorder=3)
        ax.axhline(0, color="0.85", lw=0.8, zorder=1)
        ax.set_xticks(range(len(SCENS)))
        ax.set_xticklabels([l for _k, l, _c2, _d in SCENS], fontsize=7.6)
        ax.set_xlim(-0.6, len(SCENS) - 0.4)
        ax.set_title(lf.COMP_TITLE[comp], fontsize=10, fontweight="bold", loc="left")
        ax.set_ylabel("cm SLE (rel. 1995–2014)", fontsize=8)
        ax.tick_params(labelsize=8)
        ax.grid(axis="y", alpha=0.25, lw=0.6)
        if comp == "lws":
            ax.text(0.03, 0.92, "LWS is scenario-free in all three; the swap moves nothing",
                    transform=ax.transAxes, fontsize=7.4, color="0.35", va="top")
    axes[1, 0].set_xlabel("van Vuuren scenario")
    handles = [Line2D([], [], color=lf.SRC_COLOR["Ladrillo"], marker="s", ls="none", ms=7,
                      label="Ladrillo %s on the FaIR driver" % TAG),
               Line2D([], [], color=lf.SRC_COLOR["Ladrillo"], marker="s", ls="none", ms=7,
                      mfc="none", mew=1.5, label="Ladrillo %s on MAGICC's climate" % TAG),
               Line2D([], [], color=lf.SRC_COLOR["BRICK 2.0"], marker="s", ls="none", ms=7,
                      label="BRICK 2.0 on the FaIR driver"),
               Line2D([], [], color=lf.SRC_COLOR["BRICK 2.0"], marker="s", ls="none", ms=7,
                      mfc="none", mew=1.5, label="BRICK 2.0 on MAGICC's climate"),
               Line2D([], [], color=lf.SRC_COLOR["MAGICC-SLR"], marker="D", ls="none", ms=7,
                      label="MAGICC-SLR (Nauels 2025), its own climate"),
               Line2D([], [], color="0.3", lw=0.9, label="5–95%; connector = the climate swap")]
    fig.legend(handles=handles, ncol=3, fontsize=8.5, frameon=False, loc="upper center",
               bbox_to_anchor=(0.5, 0.972))
    fig.suptitle("Sea-level rise at %d on the van Vuuren scenarios — Ladrillo and BRICK 2.0 on the "
                 "FaIR driver and on MAGICC's climate, vs MAGICC-SLR   [%s]"
                 % (YEAR, lf.commit_stamp()), fontsize=12, fontweight="bold", y=0.999)
    fig.tight_layout(rect=[0, 0.10, 1, 0.925])
    cap = ("%s — %s.  Cm, rel. 1995–2014; joint arms (posterior × climate ensemble), medians "
           "with 5–95%%.  Open symbols: the same posterior, threshold channel and draws (Ladrillo: the "
           "draws its record-conditioned FaIR arm keeps), driven by MAGICC's "
           "600-member emissions-driven climate instead of the FaIR 2.2.4 calib 1.6.0 + CMIP7 "
           "driver (spliced injection).  MAGICC-SLR is v7.5.3 + Nauels 2025.  FACTS has no "
           "MAGICC-climate arm and is not drawn." % (DESC["model"], DESC["calib"]))
    fig.text(0.5, 0.088, "\n".join(textwrap.wrap(cap, 185)), fontsize=7.2, ha="center",
             va="top", color="0.3")
    fig.savefig(OUT, dpi=150)
    print("wrote %s" % os.path.relpath(OUT, lf.REPO))

# --- console: totals and the AIS split at each horizon --------------------------------
for y in HORIZONS:
    print("\n=== @%d  total (cm): model on FaIR -> on MAGICC's climate | MAGICC-SLR ===" % y)
    for k, lab, _c, _d in SCENS:
        line = "  %-14s" % lab
        for src in ("Ladrillo", "BRICK 2.0"):
            t = T[(T.source == src) & (T.marker == k) & (T.component == "total") & (T.year == y)]
            if len(t):
                t = t.iloc[0]
                line += "  %s %6.1f -> %6.1f" % (src[:8], t.med_fair, t.med_magiccclim)
        m = mag.get((k, "total", y), np.nan)
        print(line + "  | MAGICC %6.1f" % m)
