#!/usr/bin/env python3
"""
plot_brickf_memo_figures.py — the BRICK-F* sharing-memo figure set.

  figures/brickf_fig1_hindcast.png    observation comparison: posterior
      component bands vs the calibration targets, 1900-2026. Two bands are
      drawn: parameter spread (dark) and the full predictive band including
      the calibrated AR(1)+observational error model (light).
  figures/brickf_fig2_ssp_total.png   total sea level 2000-2300 for the three
      SSPs, with MAGICC-SLR and FACTS medians/ranges marked at 2100 and 2150.
  figures/brickf_fig3_glaciers.png    the glacier module: BRICK-F* against
      MAGICC-SLR, FACTS and pre-Mengel BRICK 2.0 at 2100, the scenario-spread
      bar (the saturation diagnostic), and BRICK-F* glacier trajectories to
      2300 with the three reservoirs' shares.

Units are cm. Figure 1 is referenced to 1995-2005, the calibration window;
figures 2 and 3 to 1995-2014, the projection baseline (FACTS to baseyear 2005).
BRICK bands are posterior-parameter spread on mean forcing; MAGICC and FACTS
carry climate spread too — medians are comparable, band widths are not.

Inputs  outputs/postpred_extC_components_timeseries.csv
        outputs/ssps_components_2300_extC.csv
        outputs/brickf_model_comparison.csv
        outputs/ssps_gsic_2300.csv
  python3 python/plot_brickf_memo_figures.py
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(REPO, "figures")
# Baselines, mirroring the drivers that produced the inputs. HINDCAST matches
# FIT_REF in julia/posterior_predictive_brickf.jl (the calibration re-reference);
# PROJECTION matches BRICKF_REF in julia/brickf_projection.jl.
HINDCAST_BASELINE = "cm, rel. 1995-2005"
PROJECTION_BASELINE = "cm, rel. 1995-2014"

SSPS = ["ssp126", "ssp245", "ssp585"]
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
SSP_COLOR = {"ssp126": "#1b7837", "ssp245": "#2166ac", "ssp585": "#b2182b"}
BRICKF_COLOR = "#2166ac"
SOURCE_COLOR = {"BRICK-F*": "#2166ac", "BRICK 2.0": "#7f7f7f",
                "MAGICC-SLR": "#d62728", "FACTS": "#ff9900"}
COMPONENT_TITLE = {"ais": "Antarctic ice sheet", "glaciers": "Glaciers",
                   "gis": "Greenland ice sheet", "te": "Thermal expansion",
                   "lws": "Land-water storage", "total": "Total"}


def figure1_hindcast():
    d = pd.read_csv(os.path.join(REPO, "outputs/postpred_extC_components_timeseries.csv"))
    panels = [("ais", "ais_obs"), ("glaciers", "glaciers_obs_delta_corrected"),
              ("gis", "gis_obs"), ("te", "te_obs"), ("total", "total_obs")]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.2), sharex=True)
    for ax, (comp, obscol) in zip(axes.ravel(), panels):
        ax.fill_between(d.year, d[f"{comp}_pred_p05"], d[f"{comp}_pred_p95"],
                        color=BRICKF_COLOR, alpha=0.15, lw=0,
                        label="predictive 5-95% (incl. error model)")
        ax.fill_between(d.year, d[f"{comp}_p05"], d[f"{comp}_p95"],
                        color=BRICKF_COLOR, alpha=0.38, lw=0, label="parameter 5-95%")
        ax.plot(d.year, d[f"{comp}_p50"], color=BRICKF_COLOR, lw=1.6, label="BRICK-F* median")
        o = d[[obscol]].notna().values.ravel()
        ax.plot(d.year[o], d[obscol][o], "k.", ms=2.6, label="observational target")
        ax.set_title(COMPONENT_TITLE[comp], fontsize=11)
        ax.axhline(0, color="0.7", lw=0.6)
        ax.grid(alpha=0.25, lw=0.5)
    axes.ravel()[-1].axis("off")
    axes.ravel()[0].legend(loc="upper left", fontsize=8.5, frameon=False)
    for ax in axes[1]:
        ax.set_xlabel("year")
    for ax in axes[:, 0]:
        ax.set_ylabel(f"sea level ({HINDCAST_BASELINE})")
    fig.suptitle("BRICK-F* hindcast vs the calibration targets, 1900-2026  "
                 f"({HINDCAST_BASELINE.replace('cm, rel. ', 're-referenced ')}, "
                 "the calibration window)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(FIGDIR, "brickf_fig1_hindcast.png")
    fig.savefig(out, dpi=180); plt.close(fig)
    return out


def figure2_ssp_total():
    b = pd.read_csv(os.path.join(REPO, "outputs/ssps_components_2300_extC.csv"))
    b["scenario"] = b.ssp.map({v: k for k, v in LABEL.items()})
    cmp_ = pd.read_csv(os.path.join(REPO, "outputs/brickf_model_comparison.csv"))
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
    ax.set_title("BRICK-F* total sea level, median and 17-83%\n"
                 "(posterior-parameter spread on FaIR mean forcing)", fontsize=11)
    ax.legend(frameon=False); ax.grid(alpha=0.25, lw=0.5)

    # right: 2100 comparison across sources, one column per scenario
    ax = axes[1]
    order, xt, xl = [], [], []
    x = 0
    for ssp in SSPS:
        sub = tot[(tot.scenario == ssp) & (tot.year == 2100)]
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
    ax.set_title("Total at 2100: BRICK-F* vs MAGICC-SLR and each FACTS workflow\n"
                 "median with 17-83% (FACTS rel. baseyear 2005)", fontsize=10.5)
    ax.grid(alpha=0.25, lw=0.5, axis="y")
    ax.legend(handles=[mlines.Line2D([], [], color=SOURCE_COLOR[s], lw=2.4, marker="o", label=s)
                       for s in ("BRICK-F*", "MAGICC-SLR", "FACTS")],
              frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    out = os.path.join(FIGDIR, "brickf_fig2_ssp_total.png")
    fig.savefig(out, dpi=180); plt.close(fig)
    return out


def figure3_glaciers():
    b = pd.read_csv(os.path.join(REPO, "outputs/ssps_components_2300_extC.csv"))
    b["scenario"] = b.ssp.map({v: k for k, v in LABEL.items()})
    cmp_ = pd.read_csv(os.path.join(REPO, "outputs/brickf_model_comparison.csv"))
    gl = cmp_[(cmp_.component == "glaciers") & (cmp_.year == 2100)]
    spread = pd.read_csv(os.path.join(REPO, "outputs/brickf_model_comparison_spread.csv"))
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
                       for s in ("BRICK-F*", "BRICK 2.0", "MAGICC-SLR", "FACTS")],
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

    # (c) BRICK-F* glacier trajectories + reservoir shares
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
    ax.set_title("(c) Glacier trajectories to 2300\nsolid BRICK-F* (5-95%), dashed BRICK 2.0",
                 fontsize=11)
    ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.25, lw=0.5)

    fig.tight_layout()
    out = os.path.join(FIGDIR, "brickf_fig3_glaciers.png")
    fig.savefig(out, dpi=180); plt.close(fig)
    return out


if __name__ == "__main__":
    os.makedirs(FIGDIR, exist_ok=True)
    for f in (figure1_hindcast(), figure2_ssp_total(), figure3_glaciers()):
        print("wrote", os.path.relpath(f, REPO))
