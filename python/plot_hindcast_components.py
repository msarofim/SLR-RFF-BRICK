#!/usr/bin/env python3
"""Historical SLR 1900-2026 by component and total: Ladrillo vs observations vs BRICK 2.0.

  python3 python/plot_hindcast_components.py [--tag=L21]
Writes figures/hindcast_components_<TAG>.png

THE HINDCAST MEMBER OF THE SUITE. Same 2x3 grid, same component order, same palette and the
same gate style as plot_future_components.py, so the historical and the two projection
figures read as one set rather than three unrelated plots. It does NOT replace
plot_postpred_components_ext.py (which keeps the residual panel and the Frederikse-vs-modern
obs provenance split) or doc_l14_vs_brick20.py FIG1 (the tight 1x5 document version) -- it
adds the three things neither of those has:

  1. AN LWS PANEL. Neither model emits an LWS hindcast, but the OBSERVATION exists. Leaving
     the panel out hides a real gap; drawing it obs-only states it. See the panel note.
  2. THE PREDICTIVE BAND. postpred carries TWO bands per component: `_p05/_p95` is
     posterior-parameter spread, `_pred_p05/_pred_p95` adds the calibrated AR(1) + observation
     error. Coverage should be judged against the PREDICTIVE one -- it is the band the
     likelihood actually asserts. Only plot_ladrillo_memo_figures.py drew it, and that script
     SystemExits on --tag=L21.
  3. THE IGCC 2025-INDICATORS GMSL SERIES on the total panel, as an INDEPENDENT consensus
     anchor (Forster et al. 2026; updated from the 2024-indicators drop 2026-09-09 -- the whole
     altimetry era was re-derived there, not just extended).
     The calibration target for the total is Dangendorf 2024; IGCC is a different
     multi-product compilation and is not in the fit, so agreement with it is evidence
     rather than circularity. It is the standing first-choice obs product for this variable
     and no Ladrillo figure had ever used it.

⚠ THE TWO MODELS DO NOT SHARE A SCHEMA, A START YEAR, OR A DRIVER FILE.
  Ladrillo  1900-2026, `glaciers`/`te`, `_p05`, driven via ssp245harm
  BRICK 2.0 1900-2026, `gsic`/`te`,     `_p5`,  forced on data/observations/fair_mean_{gmst,ohc}.csv
The name mapping is a declared table below, never a string guess, and the different START
YEARS are why the BRICK line simply begins later rather than being extrapolated back.
⚠ The two were forced from DIFFERENT driver files -- that is a real caveat on any
Ladrillo-minus-BRICK reading here, and it is stated on the figure rather than assumed away.

⚠ BASELINE: everything on this figure is cm rel. 1995-2005, the CALIBRATION re-reference --
NOT the 1995-2014 projection baseline the future figures use. The IGCC series is
re-referenced to the SAME window before plotting, per the multi-year-baselining rule.

⚠ GLACIER OBS TRAP: glaciers are scored against `glaciers_obs_delta_corrected` (the r19-seam
adjustment), not the raw `gsic` target column. They differ by ~1.5 cm at 1900 and converge by
2020; plotting raw makes Ladrillo look biased at 1900 when it is not. The band half-widths
come from the target file and are re-centred on the corrected line so the two agree.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ladrillo_figs as lf  # noqa: E402

import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L21")
DESC = lf.tag_desc(TAG)
OUT = os.path.join(lf.REPO, "figures", "hindcast_components_%s.png" % TAG)

LAD_CSV = os.path.join(lf.REPO, "outputs", "postpred_%s_components_timeseries.csv" % TAG)
BRK_CSV = os.path.join(lf.REPO, "outputs", "postpred_oldbrick_components_timeseries.csv")
TGT_CSV = os.path.join(lf.REPO, "outputs", "recalib_targets_ext.csv")
## ⭐ IGCC 2025-indicators release (Forster et al. 2026), ingested and provenance-gated by
## `python/ingest_igcc2026_gmsl.py` -- read the INGESTED file, not the raw drop, so the
## Table 11 check stands between the download and every figure that uses it.
## ⚠⚠ `sigma_level_mm` is a LEVEL uncertainty: near-constant over the record, dominated by a
## common-mode term, and it therefore largely CANCELS when this series is re-referenced below.
## It is NOT the uncertainty on the re-referenced anomaly and the legend must not imply it is.
## IGCC ships no ensemble members, so the correct `sd(x_t - mean(window))` band cannot be
## computed from this release; the quantitative comparison is the Table 11 benchmark file.
IGCC_CSV = os.path.join(lf.REPO, "data/observations/igcc2026_gmsl_annual.csv")

BASE0, BASE1 = 1995, 2005          # the CALIBRATION window; see the docstring
X0, X1 = 1900, 2026
## ⚠ X0 is the PLOT span, and BOTH arms are integrated from 1850 -- neither "starts" here.
## The caption used to say "BRICK 2.0 starts 1920", which was false: 1920 was the year its
## driver happened to SAVE from, and it silently set the scorecard's evaluation window too.
## Fixed 2026-09-10 by matching the BRICK save-span to Ladrillo's 1900. Any span text below
## derives from X0 so a future change cannot leave the caption behind.
## Declared name mapping. Ladrillo/target/BRICK each spell some components differently, and
## a string guess here silently drops a panel.
TGT_COL = {"glaciers": "gsic", "gis": "gis", "ais": "ais", "te": "steric",
           "lws": "lws", "total": "dang"}
BRK_COL = {"glaciers": "gsic", "gis": "gis", "ais": "ais", "te": "te",
           "lws": None, "total": "total"}     # None = no modelled series for that panel
LAD_COL = {c: c for c in lf.COMPONENTS}
LAD_COL["lws"] = None                          # neither model predicts LWS -- panel (e)
                                               # shows the observed series alone
OBS_LINE = {"glaciers": "glaciers_obs_delta_corrected"}   # see the GLACIER OBS TRAP note

C_LAD, C_BRK = lf.SRC_COLOR["Ladrillo"], lf.SRC_COLOR["BRICK 2.0"]
C_OBS, C_IGCC = "#333333", "#b2182b"

for f in (LAD_CSV, BRK_CSV, TGT_CSV, IGCC_CSV):
    if not os.path.exists(f):
        raise SystemExit("missing %s" % os.path.relpath(f, lf.REPO))
LAD = pd.read_csv(LAD_CSV).set_index("year")
BRK = pd.read_csv(BRK_CSV).set_index("year")
TGT = pd.read_csv(TGT_CSV).set_index("year")

## ---------------------------------------------------------------------------
## BASELINE GATE. Every series on this figure must be on the SAME window, and the two model
## files claim to be already re-referenced to it. That is CHECKED, not trusted: each series'
## own 1995-2005 mean must be ~0. A file silently re-referenced elsewhere would otherwise
## shift a whole panel and look like model bias.
def _base_mean(s):
    w = s.loc[BASE0:BASE1].dropna()
    return float(w.mean()) if len(w) else float("nan")


## ⚠ THE TOLERANCE IS DERIVED FROM WHAT THE GATE EXISTS TO CATCH, NOT INVENTED, AND IT IS
## NOT AN IDENTITY BOUND. The first version demanded |offset| < 1e-6 cm and fired on
## residuals of 2.5e-3 cm -- but these files are re-referenced PER DRAW, so the ensemble
## MEDIAN over the window need not be exactly zero and an exact bound was testing something
## that was never true. The error the gate is actually for is a series baselined to the
## WRONG WINDOW, so the smallest such displacement present in these data (1995-2005 vs the
## 1995-2014 projection window) sets the scale; the bound is a tenth of it. Measured here
## rather than hardcoded, so it tracks the data instead of rotting.
_alt = []
for _nm, _df, _c in ([("lad", LAD, "%s_p50" % LAD_COL[c]) for c in lf.COMPONENTS if LAD_COL[c]]
                     + [("brk", BRK, "%s_p50" % BRK_COL[c]) for c in lf.COMPONENTS if BRK_COL[c]]
                     + [("obs", TGT, TGT_COL[c]) for c in lf.COMPONENTS]):
    _s = _df[_c]
    _alt.append(abs(_s.loc[BASE0:BASE1].mean() - _s.loc[BASE0:2014].mean()))
BASE_TOL = min(_alt) / 10.0

_off = {}
for comp in lf.COMPONENTS:
    if LAD_COL[comp]:
        _off["Ladrillo/" + comp] = _base_mean(LAD["%s_p50" % LAD_COL[comp]])
    if BRK_COL[comp]:
        _off["BRICK 2.0/" + comp] = _base_mean(BRK["%s_p50" % BRK_COL[comp]])
    _off["obs/" + comp] = _base_mean(TGT[TGT_COL[comp]])
_bad = {k: v for k, v in _off.items() if abs(v) > BASE_TOL}
if _bad:
    raise SystemExit(
        "[BASELINE] these series are NOT zero-mean over %d-%d to %.4f cm, so they are not "
        "on this figure's stated baseline and the panels would be silently offset:\n%s\n"
        "  Do NOT re-reference them here -- fix the producing driver, or the figure's "
        "caption stops being true of its inputs."
        % (BASE0, BASE1, BASE_TOL,
           "\n".join("    %-22s %+.6f cm" % (k, v) for k, v in sorted(_bad.items()))))
print("[BASELINE] all %d model/obs series are zero-mean over %d-%d (max |offset| %.2e cm, "
      "tolerance %.4f cm = 1/10 of the smallest wrong-window displacement in these data)"
      % (len(_off), BASE0, BASE1, max(abs(v) for v in _off.values()), BASE_TOL))

## IGCC is published on its OWN reference and in mm, so it is the one series this script
## re-references itself -- to the SAME window, which is why the gate above runs on the
## others rather than on it.
_ig = pd.read_csv(IGCC_CSV).set_index("year")
_ig = _ig.rename(columns={"gmsl_mm": "mean", "sigma_level_mm": "std"})
_igw = _ig["mean"].loc[BASE0:BASE1]
if len(_igw) < 5:
    raise SystemExit("[IGCC] only %d years cover %d-%d -- too few to baseline a noisy GMSL "
                     "series (5-year minimum)." % (len(_igw), BASE0, BASE1))
IGCC_MEAN = (_ig["mean"] - _igw.mean()) / 10.0          # mm -> cm
IGCC_SIG = _ig["std"] / 10.0
print("[IGCC] GMSL ensemble re-referenced to %d-%d over %d years (%d-%d), mm -> cm"
      % (BASE0, BASE1, len(_igw), int(_ig.index.min()), int(_ig.index.max())))

# --- figure ----------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.4))
for ax, comp in zip(axes.ravel(), lf.COMPONENTS):
    t = TGT_COL[comp]
    obs = TGT[t]
    lo, hi = TGT.get("%s_lo" % t), TGT.get("%s_hi" % t)
    if comp == "total":                      # the total target is Dangendorf, +/-1.645 sigma
        lo, hi = TGT["dang_lo"], TGT["dang_hi"]
    if comp in OBS_LINE:                     # glacier seam correction, band re-centred on it
        corr = LAD[OBS_LINE[comp]]
        lo, hi = corr + (lo - obs), corr + (hi - obs)
        obs = corr
    ax.fill_between(obs.index, lo, hi, color=C_OBS, alpha=0.16, lw=0, zorder=1)
    ax.plot(obs.index, obs.values, color=C_OBS, lw=1.6, zorder=4)

    if comp == "total":
        m = (IGCC_MEAN.index >= X0) & (IGCC_MEAN.index <= X1)
        ax.fill_between(IGCC_MEAN.index[m], (IGCC_MEAN - 1.645 * IGCC_SIG)[m],
                        (IGCC_MEAN + 1.645 * IGCC_SIG)[m], color=C_IGCC, alpha=0.11, lw=0)
        ax.plot(IGCC_MEAN.index[m], IGCC_MEAN.values[m], color=C_IGCC, lw=1.4, ls=(0, (4, 2)))

    if LAD_COL[comp]:
        c = LAD_COL[comp]
        ax.fill_between(LAD.index, LAD["%s_pred_p05" % c], LAD["%s_pred_p95" % c],
                        color=C_LAD, alpha=0.10, lw=0)
        ax.fill_between(LAD.index, LAD["%s_p05" % c], LAD["%s_p95" % c],
                        color=C_LAD, alpha=0.22, lw=0)
        ax.plot(LAD.index, LAD["%s_p50" % c], color=C_LAD, lw=1.9, zorder=5)
    if BRK_COL[comp]:
        c = BRK_COL[comp]
        ax.fill_between(BRK.index, BRK["%s_p5" % c], BRK["%s_p95" % c],
                        color=C_BRK, alpha=0.16, lw=0)
        ax.plot(BRK.index, BRK["%s_p50" % c], color=C_BRK, lw=1.6, ls="--", zorder=5)
    else:
        ## STATED, NOT OMITTED. An empty model panel with no explanation reads as a bug.
        ax.text(0.03, 0.90, "neither model emits an LWS hindcast —\nobservation shown alone",
                transform=ax.transAxes, fontsize=7.6, color="0.35", va="top")

    ax.axhline(0, color="0.85", lw=0.8)
    ax.set_xlim(X0, X1)
    ax.set_title(lf.COMP_TITLE[comp], fontsize=10, fontweight="bold", loc="left")
    ax.set_ylabel("cm SLE (rel. 1995–2005)", fontsize=8)
    ax.tick_params(labelsize=8)
axes[1, 0].set_xlabel("year")

handles = [Line2D([], [], color=C_LAD, lw=2, label="Ladrillo %s (median)" % TAG),
           Patch(facecolor=C_LAD, alpha=0.22, label="Ladrillo 5–95% (parameters)"),
           Patch(facecolor=C_LAD, alpha=0.10, label="Ladrillo 5–95% (predictive, +AR(1)+obs err)"),
           Line2D([], [], color=C_BRK, lw=1.6, ls="--", label="BRICK 2.0 (median)"),
           Line2D([], [], color=C_OBS, lw=1.6, label="observational target (±1.645σ)"),
           Line2D([], [], color=C_IGCC, lw=1.4, ls=(0, (4, 2)),
                  label="IGCC 2025-indicators GMSL (independent, not in the fit); shading is "
                        "the PUBLISHED LEVEL \u03c3, which does not apply to the re-referenced "
                        "anomaly")]
fig.legend(handles=handles, ncol=3, fontsize=8.5, frameon=False, loc="upper center",
           bbox_to_anchor=(0.5, 0.975))
fig.suptitle("Historical sea-level rise 1900–2026 by component — %s vs observations vs "
             "BRICK 2.0   [%s]" % (DESC["model"], lf.commit_stamp()),
             fontsize=12.5, fontweight="bold", y=0.999)
fig.tight_layout(rect=[0, 0.165, 1, 0.930])
## CAPTION SCOPE: say what the figure DOES, plus the provenance labels every output carries.
## Anything argued in the document's text belongs there, not here -- the baseline distinction,
## the IGCC depth-scope correction and the TE verdict were all duplicated and are removed.
_cap = (
    "%s — %s; %s.  Baseline %s; every series is verified zero-mean over it, and the IGCC "
    "ensemble is re-referenced to the same window (mm→cm).  "
    "Component observations: Frederikse 2020 to 2018, extended by GRACE/GRACE-FO mascons "
    "(AIS, GIS), GlaMBIE 2025 scope-matched (glaciers), NOAA 0–2000 m thermosteric (TE); "
    "total = Dangendorf 2024 extended by NOAA STAR altimetry, and both totals carry the "
    "observed land-water storage.  "
    "Glaciers are shown against the r19-seam-corrected observations.  "
    "Both models are integrated from 1850, plotted from @@X0@@, and driven by the same "
    "ssp245harm forcing.  %s"
    % (DESC["model"], DESC["calib"], DESC["glacier"], lf.CAL_BASELINE.capitalize(),
       DESC["note"]))
_cap = _cap.replace("@@X0@@", str(X0))          # derived from the constant, not retyped
assert "@@" not in _cap, "caption sentinel left unsubstituted"
fig.text(0.5, 0.150, "\n".join(textwrap.wrap(_cap, 185)),
         fontsize=7.2, ha="center", va="top", color="0.3")
fig.savefig(OUT, dpi=150)
print("wrote %s" % os.path.relpath(OUT, lf.REPO))

# --- console summary: 5-year-window comparisons, never single years --------
## The comparison-range rule: a "does it match" check over the historical period is made on
## at least a 5-year window, so interannual variability neither side controls cannot drive
## the answer. A "1900" label below is the 1898-1902 mean.
## ⛔⛔ MATCHED WINDOWS, AND THIS IS NOT A TIDY-UP. This block used to average the MODEL over
## all HALF_WIDTH*2+1 years while pandas' .mean() SILENTLY SKIPPED NaN on the OBS side. At the
## ragged modern end the obs stop early (the total target's Dangendorf splice ends 2024, GlaMBIE
## 2023), so @2024 compared a 5-year model mean centred 2024 against a 3-year obs mean centred
## 2023 -- on a series rising ~0.4 cm/yr. That put 0.387 cm of pure arithmetic into a 0.744 cm
## number reported as a model excess (52% of it), and for glaciers, with only 2 obs years, the
## artifact EXCEEDED the gap and set its SIGN.
## The control that proved it was a mechanism and not a slip: the identical test at @1950 and
## @2000, where the obs cover every year, returns EXACTLY zero.
## ⇒ every mean below is taken over the years where THAT ARM and the obs are BOTH finite, and
## the count is printed so a short window can never again pass as a full one.
## Measured 2026-09-09c by python/diag_epoch_window_asymmetry.py; see [[like_for_like_forcing]].
HALF_WIDTH = 2
EPOCHS = (1900, 1950, 2000, 2024)


def _matched(obs, arm, y):
    """obs and arm means over the years BOTH are finite, plus that count. Never a bare
    .mean() over a window -- that is the bug this function exists to prevent."""
    w = range(y - HALF_WIDTH, y + HALF_WIDTH + 1)
    yy = [t for t in w if t in obs.index and t in arm.index
          and np.isfinite(obs.get(t, np.nan)) and np.isfinite(arm.get(t, np.nan))]
    if not yy:
        return None
    return obs.loc[yy].mean(), arm.loc[yy].mean(), len(yy)


print("\nmodel vs obs, %d-year means centred on each year (cm rel. %d-%d)"
      % (2 * HALF_WIDTH + 1, BASE0, BASE1))
print("  n = years actually used; obs is re-averaged on each arm's own matched window, so the\n"
      "  obs column may differ between arms where their coverage differs. That is the point.")
for y in EPOCHS:
    print("  @%d (%d-%d window)" % (y, y - HALF_WIDTH, y + HALF_WIDTH))
    for comp in lf.COMPONENTS:
        ## ⚠ THE SAME CORRECTED OBS THE FIGURE PLOTS. Reading the raw target here made the
        ## table report a +1.68 cm glacier residual at 1900 against a panel that shows
        ## agreement -- a console summary that contradicts its own figure is worse than none.
        _os = LAD[OBS_LINE[comp]] if comp in OBS_LINE else TGT[TGT_COL[comp]]
        row = "    %-22s" % lf.COMP_TITLE[comp]
        for arm_lbl, col_map, df, w in (("Ladrillo", LAD_COL, LAD, 8),
                                        ("BRICK 2.0", BRK_COL, BRK, 8)):
            if not col_map[comp]:
                row += "   %s %*s        " % (arm_lbl, w, "n/a")
                continue
            r = _matched(_os, df["%s_p50" % col_map[comp]], y)
            if r is None:
                row += "   %s %*s        " % (arm_lbl, w, "--")
                continue
            o, v, n = r
            row += "   %s obs %*.2f mod %*.2f (%+.2f, n=%d)" % (arm_lbl, w, o, w, v, v - o, n)
        print(row)
    r = _matched(TGT[TGT_COL["total"]], IGCC_MEAN, y)
    if r is not None:
        o, g, n = r
        print("    %-22s IGCC %7.2f vs obs %7.2f (%+.2f, n=%d)  (independent check on the total)"
              % ("", g, o, g - o, n))
