#!/usr/bin/env python3
"""Future SLR trajectories to 2300, per component and total: Ladrillo vs BRICK 2.0.

  python3 python/plot_future_components.py --set=ssp [--tag=L21] [--arm=joint]
  python3 python/plot_future_components.py --set=vv  [--tag=L21] [--arm=joint]

Writes figures/future_components_<set>_<TAG>_<arm>.png

ONE SCRIPT, TWO SCENARIO SETS, because the figure is the same object either way -- six
components on one grid, two models, one forcing family. The set chooses the scenario table,
the colours, the provenance expectation and the OUTPUT FILENAME, all from
`ladrillo_figs.scen_set`, so a figure drawn for one set can never be captioned as the other.
(Contrast vv_model_comparison.py, which is a SIBLING of ladrillo_model_comparison.py rather
than a flag on it: there the two differ in how many SOURCES exist, which changes the columns
of the object. Here only the scenario axis changes.)

⚠ WHAT THIS FIGURE FIXES. Until 2026-08-31 there was NO per-component projection figure at
all, on either scenario set -- the component view existed only as tables
(outputs/doc_tables_<TAG>.md, outputs/*_model_comparison_*.csv), while every projection
FIGURE was total-only. And BRICK 2.0 had no joint-arm trajectory output whatsoever, so a
two-model component comparison over time was not buildable until
julia/scope_slr_fairunc_oldbrick.jl was given `paths` output (same commit).

⚠ BOTH MODELS ON THE SAME ARM. Ladrillo and BRICK 2.0 are read from the SAME
scope_slr_fairunc_paths_* schema, same 2014 splice pivot, same 1995-2014 re-reference, same
PAIR_SEED draw->config permutation. So on `--arm=joint` the two bands are the same object
and their WIDTHS are comparable -- which is the one thing the older four-source comparison
could not offer. ⚠ They are thinned differently (Ladrillo 8000 draws, BRICK 2.0 1000), so
fine width differences carry the coarser arm's Monte-Carlo noise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ladrillo_figs as lf  # noqa: E402

import textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402


def _arg(flag, default):
    return next((a[len(flag):] for a in sys.argv[1:] if a.startswith(flag)), default)


SET = _arg("--set=", "ssp")
TAG = _arg("--tag=", "L21")
ARM = _arg("--arm=", "joint")
if ARM not in ("joint", "fixed"):
    raise SystemExit("--arm must be 'joint' or 'fixed', not %r" % ARM)
DESC = lf.tag_desc(TAG)
SCENS = lf.scen_set(SET)
SETNAME = {"ssp": "CMIP6 SSPs", "vv": "van Vuuren CMIP7 markers"}[SET]
OUT = os.path.join(lf.REPO, "figures",
                   "future_components_%s_%s_%s.png" % (SET, TAG, ARM))

X0, X1 = 2000, 2300
## Bands are drawn only where they can be READ. With three scenarios every band fits; with
## seven the panel becomes unreadable, so only the two EXTREMES of the set carry one and
## the rest are medians. Derived from the scenario table, never hand-typed.
BAND_SCENS = ([s[0] for s in SCENS] if len(SCENS) <= 3
              else [SCENS[0][0], SCENS[-1][0]])
ARM_DESC = {"joint": "joint (posterior parameters x 841 FaIR configs)",
            "fixed": "fixed (posterior parameters, mean forcing)"}[ARM]

# --- gates -----------------------------------------------------------------
CHECKS = []
for k, lab, _c, _d in SCENS:
    g = lf.gate_ladrillo(k, TAG)
    print("[GATE] %-14s %-7s Ladrillo gates pass (CONTROL %s, %d configs)"
          % (lab, k, g["control"], g["configs"]))
    for gate, key, val in g["checks"]:
        CHECKS.append((lab, gate, key, val))
        print("       ⚠ %s/%s = %+.4f is OVER TOLERANCE (verdict CHECK). Drawing, and "
              "STAMPING it on the figure -- a CHECK is not a FAIL, but a figure must not "
              "assert a control it did not pass." % (gate, key, val))
## The stamp text is built here so it cannot be forgotten at the caption.
CHECK_NOTE = ("" if not CHECKS else
              "  ⚠ CONTROL OVER TOLERANCE (drawn anyway, verdict CHECK, not FAIL): "
              + "; ".join("%s %s %+.3f" % (l, k2, v) for l, _g, k2, v in CHECKS)
              + " — a cross-driver gap between the joint driver's fixed arm and the "
                "shipped panel; it predates this figure and is an OPEN item.")
## ⚠ THE PROVENANCE EXPECTATION DIFFERS BY SET AND IS NOT A STYLE CHOICE. The van Vuuren
## markers came from ONE build, so "one commit" is assertable. The three SSPs are calib
## 1.6.0 while ssp119/370/460 have no 1.6.0 cube -- the SSP family straddles two
## calibrations by construction, so here the mix is REPORTED, not asserted away.
_actual, _commits = lf.gate_driver_provenance([s[0] for s in SCENS],
                                              expect_one_commit=(SET == "vv"))
if SET == "vv":
    CALIB_NOTE = ("one build, one calibration throughout (calib 1.6.0 + CMIP7, driver "
                  "commit %s); each marker on its OWN CMIP7 land-use, irrigation and "
                  "volcanic/solar forcing" % _commits[0])
    print("[PROVENANCE] all %d van Vuuren drivers share one commit: %s"
          % (len(_actual), _commits[0]))
else:
    CALIB_NOTE = ("the three SSPs plotted here are all calib 1.6.0 + CMIP7 (driver commits "
                  "%s); ssp119/370/460 are NOT plotted and remain calib 1.4.5, so this "
                  "figure does not straddle vintages even though the SSP family does"
                  % ", ".join(sorted(set(_actual.values()))))
    print("[PROVENANCE] %d SSP drivers, %d commit(s): %s"
          % (len(_actual), len(_commits), dict(_actual)))

# --- data ------------------------------------------------------------------
LAD, BRK = {}, {}
for k, lab, _c, _d in SCENS:
    LAD[k] = lf.load_paths(k, "ladrillo", TAG, ARM)
    BRK[k] = lf.load_paths(k, "brick20", TAG, ARM)
    for name, byc in (("Ladrillo", LAD[k]), ("BRICK 2.0", BRK[k])):
        s, t = lf.check_component_sum(byc, k, name)
        ## Reported, never asserted: the sum of per-component MEDIANS is not the median of
        ## the sum unless the components are comonotonic. A large gap is a real signal
        ## about component dependence; a zero would be the suspicious result.
        print("[SUM] %-9s %-7s @2300  sum-of-medians %8.2f  vs median-of-total %8.2f  "
              "(%+.2f cm; medians do not add -- reported, not gated)"
              % (name, k, s, t, s - t))

# --- figure ----------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6))
for ax, comp in zip(axes.ravel(), lf.COMPONENTS):
    for k, lab, col, _d in SCENS:
        d = LAD[k][comp]
        d = d[(d.index >= X0)]
        ax.plot(d.index.values, d.med_cm.values, color=col, lw=1.9, ls="-")
        if k in BAND_SCENS:
            ax.fill_between(d.index.values, d.p05_cm.values, d.p95_cm.values,
                            color=col, alpha=0.13, lw=0)
        e = BRK[k][comp]
        e = e[(e.index >= X0)]
        ax.plot(e.index.values, e.med_cm.values, color=col, lw=1.5, ls="--")
    ax.axvline(2100, color="0.6", lw=0.8, ls=":")
    ax.axhline(0, color="0.85", lw=0.8)
    ax.set_xlim(X0, X1)
    ax.set_title(lf.COMP_TITLE[comp], fontsize=10, fontweight="bold", loc="left")
    ax.set_ylabel("cm SLE (rel. 1995–2014)", fontsize=8)
    ax.tick_params(labelsize=8)
axes[1, 0].set_xlabel("year")

handles = [Line2D([], [], color=c, lw=2, label=l) for _k, l, c, _d in SCENS]
handles += [Line2D([], [], color="0.3", ls="-", lw=2, label="Ladrillo %s" % TAG),
            Line2D([], [], color="0.3", ls="--", lw=1.5, label="BRICK 2.0"),
            Line2D([], [], color="0.3", alpha=0.2, lw=8,
                   label="5–95%% band (%s)" % ("all scenarios" if len(SCENS) <= 3
                                               else "extremes only"))]
fig.legend(handles=handles, ncol=min(6, len(handles)), fontsize=8.5, frameon=False,
           loc="upper center", bbox_to_anchor=(0.5, 0.975))
fig.suptitle("Sea-level rise to 2300 by component — %s vs BRICK 2.0, %s   [%s]"
             % (DESC["model"], SETNAME, lf.commit_stamp()),
             fontsize=12.5, fontweight="bold", y=0.999)
fig.tight_layout(rect=[0, 0.10, 1, 0.935])
## ⚠ THE CAPTION IS WRAPPED, NOT LEFT TO THE RENDERER. An unwrapped fig.text is one long
## line, and `bbox_inches="tight"` then expands the CANVAS to fit it -- the first render of
## this figure came out 5462x1306 px (4.2:1) instead of the 15.5x8.6 in it asks for, with
## the panels squashed into a strip. Wrap first, then save.
_cap = (
    "%s — %s; %s.  Arm: %s, IDENTICAL for both models (same cubes, same 2014 splice pivot, "
    "same 1995–2014 re-reference, same PAIR_SEED), so the bands are the same object and "
    "their widths ARE comparable.  %s  ⚠ Ladrillo is thinned to 8000 draws and BRICK 2.0 to "
    "1000, so fine width differences carry the coarser arm's Monte-Carlo noise.  %s  %s%s"
    % (DESC["model"], DESC["calib"], DESC["glacier"], ARM_DESC,
       lf.PROJ_BASELINE.capitalize(), CALIB_NOTE, DESC["note"], CHECK_NOTE))
fig.text(0.5, 0.085, "\n".join(textwrap.wrap(_cap, 185)),
         fontsize=7.2, ha="center", va="top", color="0.3")
fig.savefig(OUT, dpi=150)
print("\nwrote %s" % os.path.relpath(OUT, lf.REPO))

# --- console summary: the numbers a caption would quote --------------------
print("\nmedian cm, rel. 1995-2014, %s arm — Ladrillo %s / BRICK 2.0" % (ARM, TAG))
for y in (2100, 2150, 2300):
    print("\n  @%d" % y)
    print("    %-14s" % "scenario" + "".join("%22s" % lf.COMP_TITLE[c] for c in lf.COMPONENTS))
    for k, lab, _c, _d in SCENS:
        row = "    %-14s" % lab
        for c in lf.COMPONENTS:
            row += "%11.1f /%9.1f" % (LAD[k][c].med_cm.loc[y], BRK[k][c].med_cm.loc[y])
        print(row)
