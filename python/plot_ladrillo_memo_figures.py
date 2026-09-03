#!/usr/bin/env python3
"""
plot_ladrillo_memo_figures.py — the Ladrillo sharing-memo figure set.

  figures/ladrillo_<TAG>_fig1_hindcast.png    observation comparison: posterior
      component bands vs the calibration targets, 1900-2026. Two bands are
      drawn: parameter spread (dark) and the full predictive band including
      the calibrated AR(1)+observational error model (light).
  figures/ladrillo_<TAG>_fig2_ssp_total.png   total sea level 2000-2300 for the
      three SSPs, with MAGICC-SLR and FACTS medians/ranges marked at 2100/2150.
  figures/ladrillo_<TAG>_fig3_glaciers.png    the glacier module: Ladrillo against
      MAGICC-SLR, FACTS and pre-Mengel BRICK 2.0 at 2100, the scenario-spread
      bar (the saturation diagnostic), and Ladrillo glacier trajectories to
      2300 against BRICK 2.0's Wigley-Raper module.

Units are cm. Figure 1 is referenced to 1995-2005, the calibration window;
figures 2 and 3 to 1995-2014, the projection baseline (FACTS to baseyear 2005).
BRICK bands are posterior-parameter spread on mean forcing; MAGICC and FACTS
carry climate spread too — medians are comparable, band widths are not.

--tag= (default L10) selects the posterior vintage and travels into every input
path, every output filename, and each figure's title stamp.

  L10  Ladrillo 1.0, accepted 2026-08-13.
  L14  CANONICAL since 2026-08-20: two-basin Greenland, reparameterised slow
       channel. Drawn on the TAPPED arm by default (the tap is part of the module);
       pass --no-tap for the base Greenland, which lands in _notap filenames.
  L11  the D1+D2 change set, accepted 2026-08-15. D1 drops the Dangendorf TOTAL
       from the likelihood, so the L11 total has NO calibrated error model —
       figure 1's total panel therefore has no predictive band, and the total is
       out-of-sample (bias +0.65 cm full-record, entirely pre-1950).

Inputs  outputs/postpred_<TAG>_components_timeseries.csv
        outputs/ssps_components_2300_<TAG>.csv
        outputs/ladrillo_model_comparison_<TAG>{,_spread}.csv
        outputs/ssps_gsic_2300.csv
  python3 python/plot_ladrillo_memo_figures.py [--tag=L11]
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_targets  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(REPO, "figures")
# Baselines, mirroring the drivers that produced the inputs. HINDCAST matches
# FIT_REF in julia/posterior_predictive_ladrillo.jl (the calibration re-reference);
# PROJECTION matches LADRILLO_REF in julia/ladrillo_projection.jl.
HINDCAST_BASELINE = "cm, rel. 1995-2005"
PROJECTION_BASELINE = "cm, rel. 1995-2014"

SSPS = ["ssp126", "ssp245", "ssp585"]
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
SSP_COLOR = {"ssp126": "#1b7837", "ssp245": "#2166ac", "ssp585": "#b2182b"}
LADRILLO_COLOR = "#2166ac"
# One place names the posterior vintage the whole figure set is drawn from: it
# drives every input path, every OUTPUT filename, and the vintage stamp in each
# figure's title, so an L11 run cannot overwrite or be mistaken for L10.
LADRILLO_TAG = next((a[len("--tag="):] for a in sys.argv[1:]
                     if a.startswith("--tag=")), "L10")
## WHICH ARM. The tap is part of the module (2026-08-23), so these figures are drawn
## on the TAPPED deliverable unless --no-tap is passed. Resolved through
## gis_targets.ssps_csv, which rebuilds the cell-encoded filename from the same Julia
## GIS_TAP_CELL the projection driver's TAG derives from; the f-string this used to be
## could only ever find the untapped file. The HINDCAST is arm-independent by
## construction -- the tap's onset is 4.69 K against an observational record topping
## out at 1.385 K, so it is exactly inert there and postpred carries no arm suffix.
## THE ARM IS IN THE FIGURE STEM, so an untapped figure cannot be mistaken for a
## tapped one on disk or in a talk.
TAPPED       = "--no-tap" not in sys.argv[1:]
ARM_TAG      = "" if TAPPED else "_notap"
POSTPRED_CSV = f"outputs/postpred_{LADRILLO_TAG}_components_timeseries.csv"
SSPS_CSV     = os.path.relpath(gis_targets.ssps_csv(LADRILLO_TAG, tapped=TAPPED), REPO)
CMP_CSV      = f"outputs/ladrillo_model_comparison_{LADRILLO_TAG}{ARM_TAG}.csv"
CMP_SPREAD_CSV = f"outputs/ladrillo_model_comparison_{LADRILLO_TAG}{ARM_TAG}_spread.csv"
FIGSTEM      = f"ladrillo_{LADRILLO_TAG}{ARM_TAG}"
# What each vintage IS, for the title stamp. A new tag must be declared here.
## THE VINTAGE STAMP IS DECLARED, NEVER DERIVED FROM THE TAG STRING — a figure that
## cannot say which model it is is worse than no figure. The ARM is appended from the
## same GIS_TAP_CELL the filename is built from, so a title cannot disagree with the
## file it came from.
## ⚠ THE REGISTRY IS THE POINT, NOT AN OBSTACLE. The guard below refuses an unknown tag
## rather than stamping a figure with a vintage nobody declared -- that is the
## labels-from-named-constants rule doing its job, and it is why --tag=L21 raised for as
## long as it did (an inherited open item across several handoffs). The fix is to DECLARE
## the tag, never to relax the guard. Descriptions are sourced, not invented: L15-L20 are
## superseded and deliberately absent, so asking for one still raises.
TAG_DESC = {"L10": "Ladrillo 1.0 (L10)",
            "L11": "Ladrillo L11 (D1: no total; D2: gsic+steric discrepancy)",
            "L12": "Ladrillo L12 (ordered Greenland channels, whole sheet)",
            "L14": "Ladrillo L14 (two-basin Greenland)",
            # champion since 2026-08-28 (memory INDEX_slr); melt-only glacier ratchet.
            "L21": "Ladrillo L21 (calib 1.6.0 + CMIP7, melt-only glacier ratchet)",
            # 2026-08-31 refit: L21's calibration -- `--gis-ordered --gis-basins2
            # --overdisperse`, 4 x 2M -- with the glacier ratchet replaced by a FLOORED
            # equilibrium and bounded regrowth at R = 1.
            # ⚠ AN EARLIER VERSION OF THIS COMMENT CLAIMED "verified identical chain
            # headers" ON THE STRENGTH OF A GREP THAT COULD NOT HAVE SHOWN IT. The grep
            # was for `gis_k_mid|basin`, which misses `gis_s_high` -- the one column
            # `--gis-basins2` adds and the ONLY column by which the two runs differed. The
            # first L23 attempt was consequently an `:ab` Greenland, i.e. a second moved
            # axis, and is quarantined at
            # outputs/quarantine/20260831_l23_missing_gis_flags/. The flag set is now
            # verified by a smoke run whose column set is byte-identical to L21's, and the
            # pipeline gates on that identity before it will run.
            "L23": "Ladrillo L23 (L21 + floored glacier equilibrium, bounded regrowth)",
            ## L24 = L23 with the amp prior at its SHIPPED width N(1.09, 0.180), the measured
            ## 34-model CMIP6 spread. CHAMPION since 2026-09-02. ⚠ NOT like-for-like with L21,
            ## whose amp prior is N(0.95, 0.10) — that difference is a PRIOR change.
            "L24": "Ladrillo L24 (L23 + amp prior at its shipped width N(1.09, 0.180))"}
if LADRILLO_TAG not in TAG_DESC:
    raise SystemExit(f"undeclared --tag={LADRILLO_TAG}: add it to TAG_DESC so the figure "
                     f"titles say what the vintage is. Declared: "
                     f"{', '.join(sorted(TAG_DESC))}. Do NOT relax this guard -- an "
                     f"undeclared tag would be stamped with someone else's vintage.")
VINTAGE = TAG_DESC[LADRILLO_TAG] + (
    f", tap {gis_targets.tap_cell_label()}" if TAPPED else ", NO TAP (base Greenland)")
SOURCE_COLOR = {"Ladrillo": "#2166ac", "BRICK 2.0": "#7f7f7f",
                "MAGICC-SLR": "#d62728", "FACTS": "#ff9900"}
COMPONENT_TITLE = {"ais": "Antarctic ice sheet", "glaciers": "Glaciers",
                   "gis": "Greenland ice sheet", "te": "Thermal expansion",
                   "lws": "Land-water storage", "total": "Total"}


def figure1_hindcast():
    d = pd.read_csv(os.path.join(REPO, POSTPRED_CSV))
    panels = [("ais", "ais_obs"), ("glaciers", "glaciers_obs_delta_corrected"),
              ("gis", "gis_obs"), ("te", "te_obs"), ("total", "total_obs")]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.2), sharex=True)
    for ax, (comp, obscol) in zip(axes.ravel(), panels):
        # A component dropped from the likelihood (D1 drops the total in L11)
        # has no calibrated AR(1)+obs error model, so its predictive band is all
        # NaN. fill_between would draw NOTHING and the legend would still claim a
        # predictive band -- say so on the panel instead.
        has_pred = d[f"{comp}_pred_p05"].notna().any()
        if has_pred:
            ax.fill_between(d.year, d[f"{comp}_pred_p05"], d[f"{comp}_pred_p95"],
                            color=LADRILLO_COLOR, alpha=0.15, lw=0,
                            label="predictive 5-95% (incl. error model)")
        ax.fill_between(d.year, d[f"{comp}_p05"], d[f"{comp}_p95"],
                        color=LADRILLO_COLOR, alpha=0.38, lw=0, label="parameter 5-95%")
        ax.plot(d.year, d[f"{comp}_p50"], color=LADRILLO_COLOR, lw=1.6, label="Ladrillo median")
        o = d[[obscol]].notna().values.ravel()
        ax.plot(d.year[o], d[obscol][o], "k.", ms=2.6, label="observational target")
        ax.set_title(COMPONENT_TITLE[comp] + ("" if has_pred else "  (OUT-OF-SAMPLE)"),
                     fontsize=11,
                     color="k" if has_pred else "#b2182b")
        if not has_pred:
            ax.text(0.03, 0.955, "not in the likelihood — no error model,\n"
                                 "so no predictive band; parameter band only",
                    transform=ax.transAxes, va="top", ha="left",
                    fontsize=8, color="#b2182b")
        ax.axhline(0, color="0.7", lw=0.6)
        ax.grid(alpha=0.25, lw=0.5)
    axes.ravel()[-1].axis("off")
    axes.ravel()[0].legend(loc="upper left", fontsize=8.5, frameon=False)
    for ax in axes[1]:
        ax.set_xlabel("year")
    for ax in axes[:, 0]:
        ax.set_ylabel(f"sea level ({HINDCAST_BASELINE})")
    fig.suptitle(f"{VINTAGE} — hindcast vs the calibration targets, 1900-2026  "
                 f"({HINDCAST_BASELINE.replace('cm, rel. ', 're-referenced ')}, "
                 "the calibration window)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(FIGDIR, f"{FIGSTEM}_fig1_hindcast.png")
    fig.savefig(out, dpi=180); plt.close(fig)
    return out


def figure2_ssp_total():
    b = pd.read_csv(os.path.join(REPO, SSPS_CSV))
    b["scenario"] = b.ssp.map({v: k for k, v in LABEL.items()})
    cmp_ = pd.read_csv(os.path.join(REPO, CMP_CSV))
    tot = cmp_[(cmp_.component == "total")]

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4),
                             gridspec_kw=dict(width_ratios=[1.55, 1]))
    ax = axes[0]
    for ssp in SSPS:
        s = b[(b.scenario == ssp) & (b.component == "total")].sort_values("year")
        ax.fill_between(s.year, s.p17, s.p83, color=SSP_COLOR[ssp], alpha=0.20, lw=0)
        ax.plot(s.year, s.med, color=SSP_COLOR[ssp], lw=1.8, label=LABEL[ssp])
    ax.set_xlim(2000, 2300); ax.set_ylim(bottom=-5)
    ax.set_xlabel("year"); ax.set_ylabel(f"total sea level ({PROJECTION_BASELINE})")
    ax.set_title("Ladrillo total sea level, median and 17-83%\n"
                 "(posterior-parameter spread on FaIR mean forcing)", fontsize=11)
    ax.legend(frameon=False); ax.grid(alpha=0.25, lw=0.5)

    # right: 2100 comparison across sources, one column per scenario
    # Ladrillo, BRICK 2.0 (the two SLR emulators) lead each group, then MAGICC-SLR, then
    # the FACTS process-based workflows -- so the reader's own model and its closest
    # comparator sit adjacent rather than split across the FACTS cluster.
    SOURCE_ORDER = {"Ladrillo": 0, "BRICK 2.0": 1, "MAGICC-SLR": 2, "FACTS": 3}
    ax = axes[1]
    order, xt, xl = [], [], []
    x = 0
    for ssp in SSPS:
        sub = tot[(tot.scenario == ssp) & (tot.year == 2100)].sort_values(
            "source", key=lambda s: s.map(SOURCE_ORDER), kind="stable")
        start = x
        for _, r in sub.iterrows():
            lo = r.p17 if np.isfinite(r.p17) else r.p05
            hi = r.p83 if np.isfinite(r.p83) else r.p95
            ax.vlines(x, lo, hi, color=SOURCE_COLOR[r.source], lw=2.4, alpha=0.85)
            ax.plot(x, r.med, "o", ms=5, color=SOURCE_COLOR[r.source])
            order.append(r.source)
            x += 1
        xt.append((start + x - 1) / 2); xl.append(LABEL[ssp])
        x += 1.5
    ax.set_xticks(xt); ax.set_xticklabels(xl)
    ax.set_ylabel(f"total sea level at 2100 ({PROJECTION_BASELINE})")
    ax.set_title("Total at 2100: Ladrillo vs BRICK 2.0, MAGICC-SLR and each FACTS workflow\n"
                 "median with 17-83% (FACTS rel. baseyear 2005)", fontsize=10.5)
    ax.grid(alpha=0.25, lw=0.5, axis="y")
    ax.legend(handles=[mlines.Line2D([], [], color=SOURCE_COLOR[s], lw=2.4, marker="o", label=s)
                       for s in ("Ladrillo", "BRICK 2.0", "MAGICC-SLR", "FACTS")],
              frameon=False, fontsize=9, loc="upper left")
    fig.suptitle(f"{VINTAGE} — projected total sea level", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIGDIR, f"{FIGSTEM}_fig2_ssp_total.png")
    fig.savefig(out, dpi=180); plt.close(fig)
    return out


def figure3_glaciers():
    b = pd.read_csv(os.path.join(REPO, SSPS_CSV))
    b["scenario"] = b.ssp.map({v: k for k, v in LABEL.items()})
    cmp_ = pd.read_csv(os.path.join(REPO, CMP_CSV))
    gl = cmp_[(cmp_.component == "glaciers") & (cmp_.year == 2100)]
    spread = pd.read_csv(os.path.join(REPO, CMP_SPREAD_CSV))
    spread = spread[spread.component == "glaciers"]

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.0),
                             gridspec_kw=dict(width_ratios=[1.15, 0.75, 1.1]))

    # (a) 2100 glacier comparison across sources
    ax = axes[0]
    x, xt, xl = 0, [], []
    for ssp in SSPS:
        sub = gl[gl.scenario == ssp]
        start = x
        for _, r in sub.iterrows():
            lo = r.p17 if np.isfinite(r.p17) else r.p05
            hi = r.p83 if np.isfinite(r.p83) else r.p95
            ax.vlines(x, lo, hi, color=SOURCE_COLOR[r.source], lw=2.6, alpha=0.85)
            ax.plot(x, r.med, "o", ms=5.5, color=SOURCE_COLOR[r.source])
            x += 1
        xt.append((start + x - 1) / 2); xl.append(LABEL[ssp]); x += 1.5
    ax.set_xticks(xt); ax.set_xticklabels(xl)
    ax.set_ylabel(f"glacier contribution at 2100 ({PROJECTION_BASELINE})")
    ax.set_title("(a) Glaciers at 2100", fontsize=11)
    ax.grid(alpha=0.25, lw=0.5, axis="y")
    ax.legend(handles=[mlines.Line2D([], [], color=SOURCE_COLOR[s], lw=2.6, marker="o", label=s)
                       for s in ("Ladrillo", "BRICK 2.0", "MAGICC-SLR", "FACTS")],
              frameon=False, fontsize=8.5, loc="upper left")

    # (b) scenario spread — the saturation diagnostic
    ax = axes[1]
    lbl = [f"{r.source}\n{r.module}" for _, r in spread.iterrows()]
    col = [SOURCE_COLOR[r.source] for _, r in spread.iterrows()]
    ax.barh(range(len(spread)), spread.spread_126_585, color=col, alpha=0.85)
    ax.set_yticks(range(len(spread))); ax.set_yticklabels(lbl, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("cm")
    ax.set_title("(b) Glacier scenario spread at 2100\nSSP1-2.6 → SSP5-8.5", fontsize=11)
    ax.grid(alpha=0.25, lw=0.5, axis="x")

    # (c) Ladrillo glacier trajectories + reservoir shares
    ax = axes[2]
    for ssp in SSPS:
        s = b[(b.scenario == ssp) & (b.component == "glaciers")].sort_values("year")
        ax.fill_between(s.year, s.p05, s.p95, color=SSP_COLOR[ssp], alpha=0.18, lw=0)
        ax.plot(s.year, s.med, color=SSP_COLOR[ssp], lw=1.8, label=LABEL[ssp])
    g20 = pd.read_csv(os.path.join(REPO, "outputs/ssps_gsic_2300.csv"))
    g20 = g20[g20.ssp.isin(LABEL.values())]
    for ssp in SSPS:
        s = g20[g20.ssp == LABEL[ssp]].sort_values("year")
        ax.plot(s.year, s.gsic_med, color=SSP_COLOR[ssp], lw=1.3, ls="--")
    ax.plot([], [], color="0.35", lw=1.3, ls="--", label="BRICK 2.0 (Wigley-Raper)")
    ax.set_xlim(2000, 2300)
    ax.set_xlabel("year"); ax.set_ylabel(f"glacier contribution ({PROJECTION_BASELINE})")
    ax.set_title("(c) Glacier trajectories to 2300\nsolid Ladrillo (5-95%), dashed BRICK 2.0",
                 fontsize=11)
    ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.25, lw=0.5)

    fig.suptitle(f"{VINTAGE} — the glacier module", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIGDIR, f"{FIGSTEM}_fig3_glaciers.png")
    fig.savefig(out, dpi=180); plt.close(fig)
    return out


if __name__ == "__main__":
    os.makedirs(FIGDIR, exist_ok=True)
    for f in (figure1_hindcast(), figure2_ssp_total(), figure3_glaciers()):
        print("wrote", os.path.relpath(f, REPO))
