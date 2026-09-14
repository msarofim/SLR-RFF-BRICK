#!/usr/bin/env python3
"""Historical SLR 1900-2026 by component and total: Ladrillo vs observations vs BRICK 2.0.

  python3 python/plot_hindcast_components.py [--tag=L24]
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

⚠ THE TWO MODELS DO NOT SHARE A SCHEMA, but they DO share a driver and a span.
  Ladrillo  1900-2026, `glaciers`/`te`, `_p05`, driven via ssp245harm
  BRICK 2.0 1900-2026, `gsic`/`te`,     `_p5`,  driven via fair_mean_{gmst,ohc}_ssp245harm.csv
The name mapping is a declared table below, never a string guess. Both arms are integrated
from 1850 and saved from 1900 on the SAME ssp245harm FaIR-mean forcing (matched 2026-09-10;
see the X0 note below), so a Ladrillo-minus-BRICK reading here is a MODULE difference, not
a driver difference.

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

TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
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
## ⭐ THE TE DEPTH-SCOPE BAND (2026-09-11b, Marcus: "deliberately omitting expansion below 2000 m
## from observations seems wrong"). The steric target is 0-2000 m; both models expand FULL-DEPTH
## ocean heat. Rather than leave the reader to discount the model, the panel shades ABOVE the
## observation the MOST the >2000 m ocean could add: IGCC's own deep-ocean heat (its
## `ocean_2000-6000m` column, re-referenced to the same window) times the UPPER-ocean expansion
## coefficient implied by the observations themselves (target steric rate / IGCC 0-2000 m heat
## rate over 1993-2024). Deep water is colder and expands LESS per joule, so this is an upper
## bound, not a point -- which is why it is a band from the observation UP, not a shifted line.
## ⚠ IGCC's deep column is a PRESCRIBED constant rate (2 distinct increments over 1971-2024),
## so the band has no curvature of its own; it is a slope allowance, drawn over the column's
## 1971-2024 span only.
IGCC_EEI = os.path.join(lf.REPO, "data/observations/raw/igcc2024/ClimateIndicator-data-2cd2409/"
                        "data/earth_energy_imbalance/earth_energy_imbalance.csv")
DEEP_COL, UPPER_COLS = "ocean_2000-6000m", ("ocean_0-700m", "ocean_700-2000m")
DEEP_RATE_WINDOW = (1993, 2024)     # where alpha_obs is measured: the altimetry-era rate
ZJ_TO_1E22J = 0.1
## ⭐ MAGICC-SLR's HISTORY (2026-09-11, Marcus's 9/11 comment [1]: does MAGICC's historical
## Greenland match observations?). The source run spans 1750-2305; the extractor now writes a
## separate hindcast file on THIS figure's baseline. ⚠ MAGICC's Greenland module STARTS IN 1990
## (`slr_gis_*_startyear`) -- the series is identically zero before, so there is no MAGICC
## Greenland hindcast to compare before 1991, by construction; the file carries NaN there and
## the line simply begins. MAGICC runs on its OWN emissions-driven climate, not the ssp245harm
## FaIR driver the other two share (history is scenario-invariant before 2015, [HIST-SCEN]).
## Drawn on the GREENLAND panel, which is what was asked; MAGICC has every other component
## too (glaciers/TE from 1851) and the console summary reports them all.
MAG_CSV = os.path.join(lf.REPO, "data/comparison/magicc_nauels_components_hist.csv")
MAG_PANELS = ("gis",)

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
C_MAG = lf.SRC_COLOR["MAGICC-SLR"]
C_OBS, C_IGCC = "#333333", "#b2182b"

for f in (LAD_CSV, BRK_CSV, TGT_CSV, IGCC_CSV, MAG_CSV, IGCC_EEI):
    if not os.path.exists(f):
        raise SystemExit("missing %s" % os.path.relpath(f, lf.REPO))
LAD = pd.read_csv(LAD_CSV).set_index("year")
BRK = pd.read_csv(BRK_CSV).set_index("year")
TGT = pd.read_csv(TGT_CSV).set_index("year")
## MAGICC: long table -> one wide frame per component, columns med/p05/p95, NaN before start.
_mg = pd.read_csv(MAG_CSV)
assert (_mg.unit == "cm rel %d-%d" % (BASE0, BASE1)).all(), \
    "MAGICC hindcast file is not on this figure's baseline: %s" % _mg.unit.unique()
MAG = {c: g.set_index("year")[["med", "p05", "p95"]].sort_index()
       for c, g in _mg.groupby("component")}
MAG_START = {c: int(g.start_year.iloc[0]) for c, g in _mg.groupby("component")}
MAG_COL = {"glaciers": "glaciers", "gis": "gis", "ais": "ais", "te": "te", "lws": "lws",
           "total": "total"}

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
                     + [("obs", TGT, TGT_COL[c]) for c in lf.COMPONENTS]
                     + [("mag", MAG[MAG_COL[c]], "med") for c in lf.COMPONENTS
                        if MAG_START[MAG_COL[c]] <= BASE0]):
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
    if MAG_START[MAG_COL[comp]] <= BASE0:          # a module that starts inside the window
        _off["MAGICC-SLR/" + comp] = _base_mean(MAG[MAG_COL[comp]]["med"])   # cannot be gated
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

## The deep-scope band: alpha_obs x deep heat anomaly, both from observations only.
_eei = pd.read_csv(IGCC_EEI)
_eei["year"] = np.floor(_eei["time"]).astype(int)
_eei = _eei.set_index("year")
_deep = _eei[DEEP_COL].dropna() * ZJ_TO_1E22J
_upper = _eei[list(UPPER_COLS)].sum(axis=1).dropna() * ZJ_TO_1E22J
_w = range(DEEP_RATE_WINDOW[0], DEEP_RATE_WINDOW[1] + 1)
_yy = [t for t in _w if t in _upper.index and t in TGT.index and np.isfinite(TGT.loc[t, "steric"])]
_alpha_obs = (np.polyfit(_yy, TGT.loc[_yy, "steric"].values, 1)[0]
              / np.polyfit(_yy, _upper.loc[_yy].values, 1)[0])          # cm per 1e22 J
_deep_anom = _deep - _deep.loc[BASE0:BASE1].mean()
DEEP_BOUND = _alpha_obs * _deep_anom                                     # cm, rel BASE0-BASE1
_r = (_deep.loc[_yy[-1]] - _deep.loc[_yy[0]]) / (_upper.loc[_yy[-1]] - _upper.loc[_yy[0]])
print("[DEPTH-SCOPE] alpha_obs = %.4f cm per 1e22 J (target steric / IGCC 0-2000 m heat, %d-%d); "
      "deep/upper heat ratio %.3f; band = alpha_obs x IGCC >2000 m heat anomaly, %d-%d, "
      "reaching %+.2f cm at %d (an UPPER bound: deep water expands less per joule)"
      % (_alpha_obs, DEEP_RATE_WINDOW[0], DEEP_RATE_WINDOW[1], _r, int(DEEP_BOUND.index.min()),
         int(DEEP_BOUND.index.max()), DEEP_BOUND.iloc[-1], int(DEEP_BOUND.index.max())))

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
    if comp == "te":
        yrs = [t for t in DEEP_BOUND.index if t in obs.index and np.isfinite(obs.loc[t])]
        ax.fill_between(yrs, obs.loc[yrs].values, obs.loc[yrs].values + DEEP_BOUND.loc[yrs].values,
                        facecolor="#e08214", edgecolor="#b35806", hatch="////", lw=0, alpha=0.45,
                        zorder=3)
        ax.text(0.03, 0.90, "hatched: the most the ocean below 2000 m could add\n"
                "(observation is 0–2000 m; both models are full-depth)",
                transform=ax.transAxes, fontsize=7.4, color="0.35", va="top")

    if comp == "total":
        ## No shading: IGCC's published sigma is a LEVEL uncertainty that cancels on
        ## re-referencing, so the only honest band was one the legend had to disclaim (09-11b).
        m = (IGCC_MEAN.index >= X0) & (IGCC_MEAN.index <= X1)
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
    if comp in MAG_PANELS:
        m = MAG[MAG_COL[comp]].dropna()
        ax.fill_between(m.index, m["p05"], m["p95"], color=C_MAG, alpha=0.14, lw=0)
        ax.plot(m.index, m["med"], color=C_MAG, lw=1.6, ls=(0, (2, 1.2)), zorder=5)
        ax.text(0.03, 0.90, "MAGICC-SLR's Greenland module starts in %d —\nzero before, "
                "so no earlier hindcast exists" % MAG_START[MAG_COL[comp]],
                transform=ax.transAxes, fontsize=7.6, color="0.35", va="top")
    if not BRK_COL[comp]:
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
           Line2D([], [], color=C_MAG, lw=1.6, ls=(0, (2, 1.2)),
                  label="MAGICC-SLR (median, 5–95%%; Greenland only, from %d)" % MAG_START["gis"]),
           Line2D([], [], color=C_OBS, lw=1.6, label="observational target (±1.645σ)"),
           Patch(facecolor="#e08214", edgecolor="#b35806", hatch="////", alpha=0.45,
                 label="TE: most the >2000 m ocean could add (upper bound)"),
           Line2D([], [], color=C_IGCC, lw=1.4, ls=(0, (4, 2)),
                  label="IGCC 2025-indicators GMSL (not a calibration target)")]
fig.legend(handles=handles, ncol=2, fontsize=8.5, frameon=False, loc="upper center",
           bbox_to_anchor=(0.5, 0.978))
fig.suptitle("Historical sea-level rise 1900–2026 by component — %s vs observations vs "
             "BRICK 2.0 (and MAGICC-SLR at Greenland)   [%s]" % (DESC["model"], lf.commit_stamp()),
             fontsize=12.5, fontweight="bold", y=0.999)
fig.tight_layout(rect=[0, 0.09, 1, 0.915])
## CAPTION SCOPE: say what the figure DOES, plus the provenance labels every output carries.
## Anything argued in the document's text belongs there, not here -- the baseline distinction,
## the IGCC depth-scope correction and the TE verdict were all duplicated and are removed.
## CAPTION STYLE (Marcus 2026-09-11b): what the reader needs to read the panels, nothing that is
## implied or belongs in the text -- no verification notes, no unit conversions, no model
## specification beyond the vintage line.
_cap = (
    "%s — %s.  Baseline %d–%d.  "
    "Component observations: Frederikse et al. (2020), 1900–2018, extended by GRACE/GRACE-FO "
    "(AIS, GIS), GlaMBIE 2025 (glaciers), NOAA 0–2000 m thermosteric (TE); total = Dangendorf "
    "2024 extended by NOAA STAR altimetry, and both totals carry the observed land-water storage.  "
    "Both models are run from 1850, plotted from @@X0@@, on the same ssp245harm forcing.  "
    "MAGICC-SLR (v7.5.3 + Nauels 2025) is drawn on the Greenland panel from 1991, on its own "
    "climate.  Thermal expansion: the hatched band above the observation is the most the ocean "
    "below 2000 m could add (IGCC deep-ocean heat × the observed upper-ocean expansion "
    "coefficient), drawn over 1971–2024."
    % (DESC["model"], DESC["calib"], BASE0, BASE1))
_cap = _cap.replace("@@X0@@", str(X0))          # derived from the constant, not retyped
assert "@@" not in _cap, "caption sentinel left unsubstituted"
fig.text(0.5, 0.075, "\n".join(textwrap.wrap(_cap, 185)),
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
                                        ("BRICK 2.0", BRK_COL, BRK, 8),
                                        ("MAGICC-SLR", MAG_COL, None, 8)):
            if not col_map[comp]:
                row += "   %s %*s        " % (arm_lbl, w, "n/a")
                continue
            arm = (MAG[col_map[comp]]["med"] if df is None
                   else df["%s_p50" % col_map[comp]])
            r = _matched(_os, arm, y)
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
