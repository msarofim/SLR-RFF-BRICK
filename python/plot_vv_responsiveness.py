#!/usr/bin/env python3
"""Scenario RESPONSIVENESS by component: the High-minus-Very-Low van Vuuren difference, per
model and per horizon — "how responsive is each component in each model" (Marcus, 9/11
comment [9]; may inform the pulse analysis).

  python3 python/plot_vv_responsiveness.py [--tag=L24]
Reads  outputs/vv_model_comparison_<TAG>.csv        (the four-source table; no new runs)
       data/observations/fair_mean_gmst_<marker>.csv (FaIR driver GMST, mean config, per marker)
       data/comparison/magicc_gmst_vv.csv           (MAGICC's own GMST per marker)
Writes figures/vv_responsiveness_<TAG>.png and outputs/vv_responsiveness_<TAG>.csv (stamped).

THE THREE DESIGN CHOICES, STATED (handoff 2026-09-11 §1c; none resolved silently):
  (i)   FACTS is drawn PER MODULE, never collapsed. Its modules disagree by up to 8x on a
        level, so a median across them summarises nothing (`median_needs_agreement`); the
        deliverable's "148 / 259" only reproduce as a mean over four workflows and this
        script does not make one.
  (ii)  DIFFERENCE OF MEDIANS, med(vvH) - med(vvVL), for ALL four sources. Only Ladrillo and
        BRICK 2.0 have paired draws (same FaIR config on both markers), so a median of paired
        differences exists for two arms only; using it there and a difference of medians
        elsewhere would put two statistics in one panel. Like-for-like wins; the paired
        variant is a one-line change if wanted.
  (iii) Baseline 1995-2014 (the projection baseline every input is already on), cm SLE. A
        difference between two markers on the same baseline is baseline-invariant anyway.
⚠ MAGICC-SLR responds to ITS OWN climate: vvH-vvVL is a different GMST gap there than on the
FaIR driver the other three share (printed below, with cm per K). The figure is in cm — the
scenario response as each model delivers it — and the per-K normalisation is the console table.
⚠ LWS: FACTS's landwaterstorage takes an SSP-family POPULATION pathway (vvH = ssp3, vvVL =
ssp1), so its LWS "response" is socioeconomics, not climate; Ladrillo/BRICK LWS is scenario-
free by construction (0). Stated on the panel.
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

TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
DESC = lf.tag_desc(TAG)
CMP_CSV = os.path.join(lf.REPO, "outputs", "vv_model_comparison_%s.csv" % TAG)
FAIR_GMST = os.path.join(lf.REPO, "data/observations", "fair_mean_gmst_%s.csv")   # per marker
MAG_GMST_CSV = os.path.join(lf.REPO, "data/comparison/magicc_gmst_vv.csv")
CLASSES_CSV = os.path.join(lf.REPO, "benchmark/comparator_classes.csv")
OUT_PNG = os.path.join(lf.REPO, "figures", "vv_responsiveness_%s.png" % TAG)
OUT_CSV = os.path.join(lf.REPO, "outputs", "vv_responsiveness_%s.csv" % TAG)

HI, LO = "vvH", "vvVL"                 # the pair: High minus Very Low
HORIZONS = [2100, 2150, 2300]
STAT = "med"                           # difference of MEDIANS, choice (ii)
SOURCES = ["Ladrillo", "BRICK 2.0", "MAGICC-SLR", "FACTS"]
SRC_LABEL = {"Ladrillo": "Ladrillo %s" % TAG, "BRICK 2.0": "BRICK 2.0",
             "MAGICC-SLR": "MAGICC-SLR (Nauels 2025; own climate)",
             "FACTS": "FACTS n200 (per module)"}
SLOT = {"Ladrillo": -0.30, "BRICK 2.0": -0.12, "MAGICC-SLR": 0.06, "FACTS": 0.30}
FACTS_FAN = 0.055
MARK = {"Ladrillo": "s", "BRICK 2.0": "s", "MAGICC-SLR": "D", "FACTS": "o"}
SEJ_MARK = "^"
TITLE = ("Scenario responsiveness by component — %s minus %s van Vuuren scenario, %s vs "
         "BRICK 2.0 vs MAGICC-SLR vs FACTS   [%s]")
YLAB = "Δ cm SLE, High − Very Low (each on %s)" % lf.PROJ_BASELINE.split(", ")[1]

for f in (CMP_CSV, FAIR_GMST % HI, FAIR_GMST % LO, MAG_GMST_CSV, CLASSES_CSV):
    if not os.path.exists(f):
        raise SystemExit("missing %s" % os.path.relpath(f, lf.REPO))
D = pd.read_csv(CMP_CSV)
D = D[D.marker.isin([HI, LO]) & D.year.isin(HORIZONS)]
CLASS = dict(zip(*[c.astype(str) for _, c in
                   pd.read_csv(CLASSES_CSV, comment="#")[["module", "class"]].items()]))

# --- the difference table ----------------------------------------------------
key = ["source", "module", "component", "year"]
hi = D[D.marker == HI].set_index(key)[STAT]
lo = D[D.marker == LO].set_index(key)[STAT]
both = hi.index.intersection(lo.index)
missing = sorted(set(hi.index.symmetric_difference(lo.index)))
if missing:
    print("[PAIR] %d (source, module, component, year) cells present on ONE marker only -- "
          "dropped, not imputed: %s" % (len(missing), missing[:6]))
R = pd.DataFrame({"hi_med": hi.loc[both], "lo_med": lo.loc[both]}).reset_index()
R["delta_cm"] = R.hi_med - R.lo_med
R["stat"] = "difference of medians (%s - %s)" % (HI, LO)
R["cls"] = R.module.map(lambda m: CLASS.get(m, "model"))

# --- GMST gaps, so the console can say cm per K --------------------------------
## The shared driver is the MEAN-config FaIR path (the same file build_shared_climate_nc.py
## splices to); a marker-to-marker difference is baseline-invariant.
_gh = pd.read_csv(FAIR_GMST % HI).set_index("year").gmst_C
_gl = pd.read_csv(FAIR_GMST % LO).set_index("year").gmst_C
fair_dT = {y: float(_gh.loc[y] - _gl.loc[y]) for y in HORIZONS if y in _gh.index and y in _gl.index}
mg = pd.read_csv(MAG_GMST_CSV)
mag_dT = {}
for y in HORIZONS:
    a = mg[(mg.scenario == HI) & (mg.year == y)].med
    b = mg[(mg.scenario == LO) & (mg.year == y)].med
    if len(a) and len(b):
        mag_dT[y] = float(a.iloc[0] - b.iloc[0])
R["dT_K"] = [mag_dT.get(y, np.nan) if s == "MAGICC-SLR" else fair_dT.get(y, np.nan)
             for s, y in zip(R.source, R.year)]
R["delta_cm_per_K"] = R.delta_cm / R.dT_K

# --- figure ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.0))
for ax, comp in zip(axes.ravel(), lf.COMPONENTS):
    sub = R[R.component == comp]
    for i, y in enumerate(HORIZONS):
        for src in SOURCES:
            rows = sub[(sub.source == src) & (sub.year == y)].sort_values("module")
            if rows.empty:
                continue
            if src == "FACTS":
                x0 = i + SLOT[src] - FACTS_FAN * (len(rows) - 1) / 2
                xs = [x0 + j * FACTS_FAN for j in range(len(rows))]
            else:
                xs = [i + SLOT[src]]
            for x, (_, r) in zip(xs, rows.iterrows()):
                sej = r.cls == "sej"
                ax.plot([x], [r.delta_cm], marker=SEJ_MARK if sej else MARK[src],
                        ms=5.5 if src == "FACTS" else 7.5, ls="none",
                        color=lf.SRC_COLOR[src], mfc="none" if sej else lf.SRC_COLOR[src],
                        mew=1.4, zorder=5)
    ax.axhline(0, color="0.85", lw=0.8, zorder=1)
    ax.set_xticks(range(len(HORIZONS)))
    ax.set_xticklabels([str(y) for y in HORIZONS], fontsize=9)
    ax.set_xlim(-0.6, len(HORIZONS) - 0.4)
    ax.set_title(lf.COMP_TITLE[comp], fontsize=10, fontweight="bold", loc="left")
    ax.set_ylabel(YLAB, fontsize=8)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", alpha=0.25, lw=0.6)
    if comp == "lws":
        ax.text(0.03, 0.92, "FACTS LWS follows the scenario's SSP population\npathway "
                "(ssp3 vs ssp1) — socioeconomics, not climate;\nLadrillo/BRICK LWS is "
                "scenario-free by construction", transform=ax.transAxes, fontsize=7.4,
                color="0.35", va="top")
axes[1, 0].set_xlabel("horizon")

sej_drawn = sorted(set(R[(R.source == "FACTS") & (R.cls == "sej")].module))
handles = [Line2D([], [], color=lf.SRC_COLOR[s], marker=MARK[s], ls="none", ms=7,
                  label=SRC_LABEL[s]) for s in SOURCES if s in set(R.source)]
if sej_drawn:
    handles.append(Line2D([], [], color=lf.SRC_COLOR["FACTS"], marker=SEJ_MARK, ls="none",
                          mfc="none", mew=1.4, ms=7,
                          label="FACTS, structured expert judgement (%s)" % ", ".join(sej_drawn)))
fig.legend(handles=handles, ncol=3, fontsize=8.5, frameon=False, loc="upper center",
           bbox_to_anchor=(0.5, 0.965))
fig.suptitle(TITLE % (HI, LO, DESC["model"], lf.commit_stamp()), fontsize=12.5,
             fontweight="bold", y=0.999)
fig.tight_layout(rect=[0, 0.12, 1, 0.925])
cap = ("%s — %s.  Each point is med(%s) − med(%s) at that horizon, both on %s; FACTS per "
       "module.  Ladrillo, BRICK 2.0 and FACTS share one FaIR 2.2.4 calib 1.6.0 + CMIP7 driver "
       "(GMST gap %s K at %s); MAGICC-SLR runs on its own climate (gap %s K).  FACTS n200 is "
       "rel. baseyear 2005; MAGICC-SLR is v7.5.3 + Nauels 2025."
       % (DESC["model"], DESC["calib"], HI, LO, lf.PROJ_BASELINE,
          "/".join("%.2f" % fair_dT[y] for y in HORIZONS if y in fair_dT),
          "/".join(str(y) for y in HORIZONS if y in fair_dT),
          "/".join("%.2f" % mag_dT[y] for y in HORIZONS if y in mag_dT)))
fig.text(0.5, 0.105, "\n".join(textwrap.wrap(cap, 185)), fontsize=7.2, ha="center", va="top",
         color="0.3")
fig.savefig(OUT_PNG, dpi=150)
print("wrote %s" % os.path.relpath(OUT_PNG, lf.REPO))

# --- outputs + console -----------------------------------------------------------
out = stamp(R.sort_values(["component", "year", "source", "module"]), os.path.basename(__file__),
            tag=TAG, inputs={"comparison": CMP_CSV, "fair_gmst_hi": FAIR_GMST % HI,
                             "fair_gmst_lo": FAIR_GMST % LO, "magicc_gmst": MAG_GMST_CSV},
            extra="delta_cm = med(%s) - med(%s), %s; dT_K = same pair's GMST gap on each "
                  "source's OWN driver (FaIR mean for Ladrillo/BRICK/FACTS, MAGICC median)"
                  % (HI, LO, lf.PROJ_BASELINE))
out.to_csv(OUT_CSV, index=False)
print("wrote %s  (%d rows)" % (os.path.relpath(OUT_CSV, lf.REPO), len(out)))

print("\nGMST gap %s - %s:  FaIR driver %s   MAGICC %s"
      % (HI, LO, {y: round(v, 2) for y, v in fair_dT.items()},
         {y: round(v, 2) for y, v in mag_dT.items()}))
for y in HORIZONS:
    print("\n=== @%d  Δ cm (and Δ cm per K of that source's own GMST gap) ===" % y)
    for comp in lf.COMPONENTS:
        sub = R[(R.component == comp) & (R.year == y)].sort_values(["source", "module"])
        print("  %-20s " % lf.COMP_TITLE[comp] + "  ".join(
            "%s%s %+.1f (%+.1f/K)" % (r.source if r.source != "FACTS" else "FACTS:",
                                      "" if r.source != "FACTS" else r.module,
                                      r.delta_cm, r.delta_cm_per_K)
            for _, r in sub.iterrows()))
