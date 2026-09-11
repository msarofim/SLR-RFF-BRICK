#!/usr/bin/env python3
"""The climate-swap figure: Ladrillo, BRICK 2.0 and MAGICC-SLR by component on the van Vuuren
markers, with Ladrillo and BRICK 2.0 shown BOTH on the shared FaIR driver and on MAGICC's own
climate — so the reader sees how much of each model-vs-MAGICC gap is the climate and how much
survives the swap (Marcus, 9/11b comment [8]).

  python3 python/plot_vv_climate_swap.py [--tag=L24] [--year=2300|2100|2150|all]
Reads  outputs/vv_model_comparison_<TAG>.csv                       Ladrillo/BRICK on FaIR, MAGICC-SLR
       outputs/scope_slr_fairunc_cells_<m>_spliced_magiccclim_<TAG>_<tap>.csv   Ladrillo on MAGICC's climate
       outputs/scope_slr_fairunc_cells_<m>_spliced_oldbrick_magiccclim.csv      BRICK 2.0 on MAGICC's climate
Writes figures/vv_climate_swap_<TAG>_<year>.png and outputs/vv_climate_swap_<TAG>.csv (stamped).

CONVENTIONS (all inherited, none new): cm rel 1995-2014; JOINT arms (posterior x climate
ensemble); the SPLICED injection convention for the swapped arms (Marcus 2026-08-31: spliced
primary, raw as check -- worth 0.00 cm for TE/glaciers/LWS and up to -43 cm for AIS at
ssp245/2300, memory `ladrillo_on_magicc_climate`). Only the driving climate changes between a
model's two points: posterior, tap, modules and draw count are identical, and [ARM-MATCH]
refuses a pair whose draw counts differ. FACTS is not drawn: it has no MAGICC-climate arm.
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
_y = next((a[len("--year="):] for a in sys.argv[1:] if a.startswith("--year=")), "2300")
HORIZONS = [2100, 2150, 2300]
YEARS = HORIZONS if _y == "all" else [int(_y)]
DESC = lf.tag_desc(TAG)
CMP_CSV = os.path.join(lf.REPO, "outputs", "vv_model_comparison_%s.csv" % TAG)
## The tap stem the joint driver writes (mirrors vv_model_comparison.joint_stem); read from
## the comparison table's own provenance rather than retyped: the FaIR-arm cells file name.
TAP_STEM = "tap4p69K_V5p64m_tau800"
LAD_MAG = os.path.join(lf.REPO, "outputs",
                       "scope_slr_fairunc_cells_%%s_spliced_magiccclim_%s_%s.csv" % (TAG, TAP_STEM))
BRK_MAG = os.path.join(lf.REPO, "outputs", "scope_slr_fairunc_cells_%s_spliced_oldbrick_magiccclim.csv")
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
for src, tmpl in (("Ladrillo", LAD_MAG), ("BRICK 2.0", BRK_MAG)):
    for k, _l, _c, _d in SCENS:
        p = tmpl % k
        if not os.path.exists(p):
            raise SystemExit("missing MAGICC-climate arm for %s %s: %s" % (src, k, os.path.relpath(p, lf.REPO)))
        c = pd.read_csv(p)
        c = c[(c.arm == "joint") & (c.horizon.isin(HORIZONS))]
        for _, r in c.iterrows():
            rows.append(dict(source=src, climate="magicc", marker=k, component=r.component,
                             year=int(r.horizon), med=r.med_cm, p05=r.p05_cm, p95=r.p95_cm,
                             n_draws=int(r.n_draws)))
R = pd.DataFrame(rows)
R = R[R.component.isin(lf.COMPONENTS) & R.year.isin(HORIZONS)]

## [ARM-MATCH] the two points of one model must come from the same number of draws.
bad = []
for src in ("Ladrillo", "BRICK 2.0"):
    a = R[(R.source == src)].groupby(["marker", "climate"]).n_draws.first().unstack()
    m = a[a.fair != a.magicc]
    if len(m):
        bad.append("%s: %s" % (src, m.to_dict("index")))
if bad:
    raise SystemExit("[ARM-MATCH] draw counts differ between a model's FaIR and MAGICC arms:\n  "
                     + "\n  ".join(bad))
print("[ARM-MATCH] Ladrillo %d draws on both climates, BRICK 2.0 %d on both; MAGICC-SLR %d members."
      % (R[R.source == "Ladrillo"].n_draws.iloc[0], R[R.source == "BRICK 2.0"].n_draws.iloc[0],
         R[R.source == "MAGICC-SLR"].n_draws.iloc[0]))

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
          inputs={"comparison": CMP_CSV, "ladrillo_magiccclim": LAD_MAG % "<marker>",
                  "brick_magiccclim": BRK_MAG % "<marker>"},
          extra="cm rel 1995-2014, joint arms, spliced injection; gap_on_X = model median on "
                "climate X minus MAGICC-SLR's median; climate_term = med_magiccclim - med_fair")
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
    axes[1, 0].set_xlabel("van Vuuren marker")
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
    fig.suptitle("Sea-level rise at %d on the van Vuuren markers — Ladrillo and BRICK 2.0 on the "
                 "FaIR driver and on MAGICC's climate, vs MAGICC-SLR   [%s]"
                 % (YEAR, lf.commit_stamp()), fontsize=12, fontweight="bold", y=0.999)
    fig.tight_layout(rect=[0, 0.10, 1, 0.925])
    cap = ("%s — %s.  Cm, rel. 1995–2014; joint arms (posterior × climate ensemble), medians "
           "with 5–95%%.  Open markers: the same posterior, tap and draws, driven by MAGICC's "
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
