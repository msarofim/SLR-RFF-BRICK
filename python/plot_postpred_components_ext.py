#!/usr/bin/env python3
"""
Historical sea-level reconstruction figure: the full updated model stack
(BRICK + Mengel 2-tau glacier + FaIR forcing), MCMC-calibrated to Frederikse 2020
components + Dangendorf 2024 total and EXTENDED past 2018 with GRACE-FO / GlaMBIE /
NOAA, vs observations and vs the OLD (stock single-reservoir) BRICK.

2x3 panels: AIS, GSIC, GIS, Steric/TE, Total GMSL + residual (model - obs). Each
component panel shows obs provenance separately -- Frederikse (grey) vs the modern
extension (red dashed, over its full range incl. the 2003-2018 overlap, taking over
at the dotted 2018 splice) -- plus the new BRICK-Mengel band+median and the old-BRICK
median. All curves re-referenced to a common 1970-2020 window FOR DISPLAY (the
calibration itself used 1995-2005; re-baselining to the longer modern window centers
the strongly-trended components -- esp. Greenland -- better). Model bands carry
PARAMETER uncertainty only (AR(1) obs-noise excluded), so they are narrow.

Inputs:  outputs/postpred_ext_components_timeseries.csv (new BRICK-Mengel, extended fit)
         outputs/postpred_oldbrick_components_timeseries.csv (old stock BRICK)
         outputs/recalib_targets_ext_sources.csv (Frederikse vs modern, separated)
         outputs/recalib_targets_ext.csv (obs uncertainty bands)
Output:  outputs/postpred_<TAG>_components.png  (--tag=, default L21 = the champion;
         --tag=ext reproduces the legacy 2026-06-13 outputs/postpred_ext_components.png)
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as ml
import matplotlib.patches as mp

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")

## --tag= SELECTS THE MODEL ARM, and 2026-08-30 it defaults to the CHAMPION.
## This script was hardcoded to outputs/postpred_ext_components_timeseries.csv, a
## 2026-06-13 vintage that predates L14, L21 and the calib 1.6.0 migration, so the figure
## on disk was 2.5 months behind the model it claimed to show. `--tag=ext` still reads
## that legacy file for provenance.
## ⚠ THE OUTPUT NAME CARRIES THE TAG, so regenerating on L21 cannot overwrite the legacy
## figure -- the rule scope_ais_ton_band_hindcast.jl broke at the cost of a measurement.
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L21")
_src = ("outputs/postpred_ext_components_timeseries.csv" if TAG == "ext"
        else f"outputs/postpred_{TAG}_components_timeseries.csv")
d    = pd.read_csv(os.path.join(REPO, _src))
## SCHEMA SHIM. The legacy `ext` file uses `<c>_p5` and calls the glacier component
## `gsic`; the tagged postpred writer uses `<c>_p05` and `glaciers`. Normalise onto the
## legacy names the plotting code below already speaks, rather than touching that code.
d = d.rename(columns={c: c.replace("glaciers_", "gsic_") for c in d.columns})
d = d.rename(columns={c: c.replace("_p05", "_p5") for c in d.columns})
_need = [f"{c}_{q}" for c in ("ais", "gsic", "gis", "te", "total") for q in ("p5", "p50", "p95", "obs")]
_missing = [c for c in _need if c not in d.columns]
if _missing:
    raise SystemExit(f"{_src} is missing {_missing} -- schema shim needs updating.")
old  = pd.read_csv(os.path.join(REPO, "outputs/postpred_oldbrick_components_timeseries.csv")).set_index("year")
tg   = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets_ext.csv")).set_index("year")
prov = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets_ext_sources.csv")).set_index("year")
OUT  = os.path.join(REPO, f"outputs/postpred_{TAG}_components.png")

## PROVENANCE PER ARM, as named constants, because the caption must not be able to drift
## from the arm it describes (`figure_captions`). ⚠ The hardcoded caption said
## "v1.4.5 Smith calibration ... 4x500k, 27/28 R-hat<1.05" — L11-era facts still printed
## under an L21 figure until 2026-08-30. Verified for L21: chains are
## chain_L21_seed{2026..2029}_n2000000 (4 x 2M) and the subsample is 10,000 draws.
PROV = {
    ## ⚠ GLACIER AND GIS STRUCTURE ARE PER-ARM AND WERE MISLABELLED UNTIL 2026-08-30.
    ## The panel title and caption said "Mengel 2-τ" under an L21 figure. The 2-τ form is
    ## ONE reservoir with two relaxation timescales (params a, b, T_off, f, tau_f, tau_s --
    ## see d0_glacier_shootout.py); extC REPLACED it (build_overdispersed_starts_extc.py
    ## calls the 2-τ layout "the stale 2-tau 39-col file"). L21's posterior carries
    ## gic_{a,b,T_off,log10_kappa}_{R19,SLOWP,FAST} -- THREE blocks with ONE relaxation
    ## kappa each -- and no tau_f/tau_s. Verified from the subsample's own columns.
    "L21": dict(model="Ladrillo L21", calib="calib 1.6.0 + CMIP7",
                chains="4x2M, 10k draws",
                ## 18, not 20. `outputs/log_l21_postprocess_driver.txt:97` reads
                ## "** 18 marginals not converged; ACCEPTED ON DELIVERABLE **".
                conv="convergence disclosed under the --accept-slr gate (18 marginals "
                     "unconverged; projected SLR R-hat<1.05 at all horizons)",
                glacier="THREE-reservoir Mengel-form glacier (blocks R19 / SLOWP / FAST, "
                        "one relaxation κ each)",
                gis="TWO-basin Greenland (active = SW+CW+CE+SE+NW, high = NO+NE), each "
                    "basin carrying the A+B fast/slow channels",
                gpanel="Glaciers (3-block: R19/SLOWP/FAST)", gispanel="Greenland (2-basin)"),
    ## L23 = L21's calibration with ONLY the glacier law changed (floored equilibrium +
    ## bounded regrowth at R = 1). Chain column set verified byte-identical to L21's.
    ## ⚠ TWO axes moved from L21, not one: the glacier law AND the proposal covariance
    ## (L23 carries no --adcov and fell through to adapted_cov_L11tune3 where L21/L22
    ## passed adapted_cov_L14tune). The column-set identity check above cannot see it.
    ## The 19-marginal figure was read from a `p_postprocess.log` that is NO LONGER ON
    ## DISK -- unverifiable here, unlike L21's, which has
    ## outputs/log_l21_postprocess_driver.txt. Re-run postprocess to restore the receipt.
    "L23": dict(model="Ladrillo L23", calib="calib 1.6.0 + CMIP7",
                chains="4x2M, 10k draws",
                conv="convergence disclosed under the --accept-slr gate (19 marginals "
                     "unconverged; projected SLR R-hat 1.001 at 2100 and 2150)",
                glacier="THREE-reservoir Mengel-form glacier (blocks R19 / SLOWP / FAST, "
                        "one relaxation κ each), FLOORED equilibrium with bounded "
                        "regrowth at R = 1",
                gis="TWO-basin Greenland (active = SW+CW+CE+SE+NW, high = NO+NE), each "
                    "basin carrying the A+B fast/slow channels",
                gpanel="Glaciers (3-block, floored + regrowth)",
                gispanel="Greenland (2-basin)"),
    "ext": dict(model="BRICK-Mengel (2026-06 'ext' fit)", calib="calib 1.4.5 (Smith)",
                chains="4x500k, 10k draws", conv="27/28 R-hat<1.05",
                glacier="Mengel 2-τ glacier (single reservoir, fast+slow relaxation), as "
                        "labelled at that vintage",
                gis="Greenland A+B", gpanel="Glaciers (Mengel 2-τ)", gispanel="Greenland"),
}
P = PROV.get(TAG)
if P is None:
    raise SystemExit(f"--tag={TAG}: no provenance entry. Add one to PROV rather than "
                     f"letting the caption describe an arm it was not written for.")

X0, SPLICE = 1920, 2018                 # plot start; Frederikse->modern handoff year
REF0, REF1 = 1970, 2020                 # DISPLAY re-reference window (calibration used 1995-2005)
CAL_BASE   = "1995-2005"
yr   = d["year"].values
FRED_C, MODERN_C, MENGEL_C, OLD_C = "0.25", "#c0392b", "#1763b8", "#0f9b6c"
OBSCOL = {"ais": "ais", "gsic": "gsic", "gis": "gis", "te": "steric", "total": "dang"}
SRCLAB = {"ais": "GRACE-FO", "gsic": "GlaMBIE", "gis": "GRACE-FO", "te": "NOAA NCEI", "total": "NOAA STAR"}
panels = [("ais",   "Antarctic Ice Sheet — GRACE-FO ext (post-2020 pause)"),
          ("gsic",  f"{P['gpanel']} — GlaMBIE ext (acceleration)"),
          ("gis",   f"{P['gispanel']} — GRACE-FO ext"),
          ("te",    "Steric / Thermal expansion — NOAA NCEI ext"),
          ("total", "TOTAL GMSL — Dangendorf + NOAA STAR ext")]

def winmean(s):
    """Mean of a year-indexed series over the display reference window."""
    w = s.reindex(range(REF0, REF1 + 1)).dropna()
    return w.mean()

fig, axes = plt.subplots(2, 3, figsize=(16.5, 9))
ax_list = list(axes.flat)

for ax, (c, title) in zip(ax_list[:5], panels):
    oc = OBSCOL[c]
    # --- assemble series (all currently rel 1995-2005) ---
    fred   = prov[f"{oc}_fred"]
    modern = prov[f"{oc}_modern"]
    obs_merged = fred.combine_first(modern)                       # one obs curve for the offset
    if c == "total":
        olo = tg["dang"] - 1.645 * tg["dang_sig"]; ohi = tg["dang"] + 1.645 * tg["dang_sig"]
    else:
        olo = tg[f"{oc}_lo"]; ohi = tg[f"{oc}_hi"]
    p5  = pd.Series(d[f"{c}_p5"].values,  index=yr); p50 = pd.Series(d[f"{c}_p50"].values, index=yr)
    p95 = pd.Series(d[f"{c}_p95"].values, index=yr)
    o50 = old[f"{c}_p50"]
    # --- re-reference each curve to its own 1970-2020 mean (display only) ---
    obs_off = winmean(obs_merged); m_off = winmean(p50); o_off = winmean(o50)
    fred, modern, olo, ohi = fred-obs_off, modern-obs_off, olo-obs_off, ohi-obs_off
    p5, p50, p95 = p5-m_off, p50-m_off, p95-m_off
    o50 = o50 - o_off

    ax.axvspan(SPLICE, yr.max(), color="orange", alpha=0.05, lw=0)
    ax.fill_between(olo.index, olo.values, ohi.values, color="0.80", alpha=0.55, lw=0)
    flab = "Dangendorf 2024" if c == "total" else "Frederikse 2020"
    ax.plot(fred.index,   fred.values,   color=FRED_C,   lw=1.7, zorder=5)
    ax.plot(modern.index, modern.values, color=MODERN_C, lw=1.3, ls="--", marker="o", ms=2.5,
            markevery=2, zorder=6)
    ax.plot(o50.index, o50.values, color=OLD_C, lw=1.5, ls="-.", zorder=4)
    ax.axvline(SPLICE, color="orange", lw=0.9, ls=":", zorder=3)
    ax.fill_between(p5.index, p5.values, p95.values, color=MENGEL_C, alpha=0.22, lw=0, zorder=2)
    ax.plot(p50.index, p50.values, color=MENGEL_C, lw=2.1, zorder=7)
    # end-year obs-vs-model annotation (re-referenced)
    ey = int(modern.dropna().index.max()); mo = p50.reindex([ey]).iloc[0]; oo = modern.reindex([ey]).iloc[0]
    ax.set_title(title, fontsize=10.5)
    ax.axhline(0, color="k", lw=0.4, alpha=0.4); ax.grid(alpha=0.25)
    ax.set_ylabel(f"cm (rel {REF0}-{REF1})", fontsize=8.5)
    ax.set_xlim(X0, yr.max())

# All 5 component panels share the same series types. With several rising curves
# (incl. the steep old-BRICK line) no single in-panel quadrant is reliably clear, so
# the shared series legend goes ABOVE the panels as one horizontal row -> zero line
# overlap. The residual panel keeps its own (component-colour) legend below.
fig.legend(handles=[
    mp.Patch(color="0.80", alpha=0.55, label="obs uncertainty"),
    ml.Line2D([], [], color=FRED_C, lw=1.7, label="Frederikse 2020 / Dangendorf (≤2018)"),
    ml.Line2D([], [], color=MODERN_C, lw=1.3, ls="--", marker="o", ms=3, label="modern extension (GRACE-FO/GlaMBIE/NOAA, ≥2003)"),
    ml.Line2D([], [], color=MENGEL_C, lw=2.1, label=f"{P['model']}: median + 90% param"),
    ml.Line2D([], [], color=OLD_C, lw=1.5, ls="-.", label="old BRICK (single-reservoir, old posterior)"),
], fontsize=8.2, loc="upper center", bbox_to_anchor=(0.5, 0.945), ncol=5, framealpha=0.9)

# residual panel (re-referenced model p50 - obs), exposes compensating biases
axr = ax_list[5]
res_colors = {"ais": "#1763b8", "gsic": "#0f9b6c", "gis": "#b8480f", "te": "#9b1fb8", "total": "k"}
for c, _ in panels:
    oc = OBSCOL[c]
    obs_merged = prov[f"{oc}_fred"].combine_first(prov[f"{oc}_modern"])
    p50 = pd.Series(d[f"{c}_p50"].values, index=yr)
    res = (p50 - winmean(p50)) - (obs_merged - winmean(obs_merged))
    res = res.reindex(range(X0, int(yr.max()) + 1))
    axr.plot(res.index, res.values, color=res_colors[c], lw=(2.4 if c == "total" else 1.5),
             label=f"{c} ({res.dropna().iloc[-1]:+.2f})")
axr.axvspan(SPLICE, yr.max(), color="orange", alpha=0.05, lw=0)
axr.axhline(0, color="k", lw=0.6); axr.grid(alpha=0.25)
axr.set_title("Residual: new-fit median − obs (re-ref %d-%d)" % (REF0, REF1), fontsize=10.5)
axr.set_ylabel("cm", fontsize=8.5); axr.set_xlim(X0, yr.max())
# residuals swing widely in the early century (left) and settle near 0 late -> the
# UPPER-RIGHT is the open quadrant for this panel's legend.
axr.legend(fontsize=7.5, loc="upper right", title="end-yr Δ (cm)", title_fontsize=7.5, ncol=2)
for ax in axes[1, :]:
    ax.set_xlabel("year")

fig.suptitle(f"Historical sea-level reconstruction: Ladrillo {TAG} vs stock BRICK v2.0.0 "
             f"vs observations", fontsize=13, y=0.985)

# Audience = Tony Wong (BRICK author): present the four changes since stock BRICK
# v2.0.0 (green dash-dot) EVENLY, not headlining the obs extension. FaIR is the
# v2.2.4 MODEL with the v1.4.5 Smith calibration dataset (NOT "FaIR v1.4.5").
fig.text(0.5, 0.008,
         f"{P['model']} = stock BRICK v2.0.0 (green dash-dot, plotted alongside) with four coupled upgrades, "
         f"weighted equally: (1) a {P['glacier']} replacing stock BRICK's single-reservoir glacier, with a "
         f"{P['gis']}; "
         f"(2) FaIR 2.2.4 ({P['calib']}) obs-driven forcing — external GMST + ocean heat — replacing "
         f"SNEASY's internal climate; (3) Bayesian MCMC recalibration ({P['chains']}; {P['conv']}) to Frederikse "
         "2020 components + Dangendorf 2024 total, AIS equilibrium ocean temperature freed; (4) historical data drawn "
         "from Frederikse 2020 (grey), extended with GRACE-FO (AIS/GIS), GlaMBIE (glaciers), NOAA NCEI (steric), "
         "NOAA STAR (total) — spliced at 2018 (dotted) by overlap offset-matching (no rescale; modern curve drawn over "
         f"its full range incl. the 2003–2018 overlap). Model bands carry PARAMETER uncertainty only (AR(1) obs-noise "
         f"excluded → narrow). Calibrated rel {CAL_BASE}; all curves re-referenced to {REF0}–{REF1} for display. "
         f"⚠ The residual panel is the BARE MODULE: the postpred writer applies no d2 discrepancy term, so these are "
         f"PRE-discrepancy residuals. For steric/TE the fit itself carries a −0.66 cm delta at 2025, and the residual "
         f"the likelihood actually scores there is ~4.5σ, not the ~17.8σ a bare-module reading gives.",
         ha="center", va="bottom", fontsize=7.6, color="0.3", wrap=True)
## bottom margin sized for the CAPTION, which grew when the per-arm structure text was
## added -- at 0.055 it overlapped the x-axis labels.
fig.tight_layout(rect=[0, 0.105, 1, 0.915])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
