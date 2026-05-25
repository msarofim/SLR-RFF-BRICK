"""
pulse_hawkins_sutton.py
=======================

Substack figure: Hawkins-Sutton-style variance decomposition of the
marginal climate response to a 1 GtCO₂ pulse at 2030. Companion to
pulse_responses_clean.py — same envelope choices on the top row, with
the variance-source decomposition added on the bottom row.

2 × 2 grid:
  row 1: ΔGMST marginal envelope        |  ΔSLR marginal envelope
  row 2: ΔGMST variance fractions       |  ΔSLR variance fractions

  • Top row uses the same data as pulse_responses_clean.py — GMST from
    the 1 GtC production pulse (GMST is linear, pulse-size invariant);
    SLR from the 0.01 GtC small-pulse companion (avoids the AIS-tipping
    fat tail that contaminates the production-pulse mean).

  • ΔGMST decomposed into 2 sources (emissions × climate). No BRICK term
    because GMST is upstream of BRICK; no stochastic-seed term because
    the production FaIR cube has no seed dim.

  • ΔSLR decomposed into 4 sources (emissions × climate × internal × BRICK)
    from the per-tuple paired ANOVA factorial against the +1 GtC production
    pulse. The 'internal' layer is AIS-tipping-state dependence: paired BRICK
    posteriors with seeds cancel pure stochastic noise in the diff, leaving
    the cross-seed variance driven by whether the climate state at 2030
    crosses a posterior-defined AIS tipping threshold.

Inputs:
  outputs/substack/co2_pulse_gmst_summary.csv         (envelope, p5/p50/p95)
  outputs/substack/co2_pulse_slr_summary_lhs10k_0p01gtc.csv  (envelope, p5/p50/p95)
  outputs/plots/hawkins_sutton_gmst_3way_pulse.csv    (variance fractions)
  outputs/plots/hawkins_sutton_slr_4way_pulse.csv     (variance fractions)

Output:
  outputs/substack/pulse_hawkins_sutton.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT             = Path(__file__).resolve().parents[3]
# v1.4.5 CO2 GMST products: built by python/scripts/build_v145_gmst_pulse_products.py.
# Both the 3-way variance decomp and the envelope summary are stored in
# °C per GtCO2 directly (FaIR v1.4.5 CO2 FFI input unit is GtCO2).
GMST_VAR_CSV     = ROOT / "outputs" / "plots" / "hawkins_sutton_gmst_3way_pulse_v145.csv"
SLR_VAR_CSV      = ROOT / "outputs" / "plots" / "hawkins_sutton_slr_4way_pulse.csv"  # v145
GMST_BAND_CSV    = ROOT / "outputs" / "substack" / "co2_pulse_gmst_summary_v145.csv"
SLR_BAND_CSV     = ROOT / "outputs" / "substack" / "co2_pulse_slr_summary_lhs10k_0p01gtc.csv"
OUT              = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

PLOT_START, PLOT_END = 2030, 2150
# The v145 envelopes are in °C per GtCO2 (or cm per GtCO2) directly — no
# unit conversion needed.  Legacy v141 era was per-GtC and used GTC_TO_GTCO2.
ENVELOPE_UNIT_SCALE = 1.0

# Stacked-source colors (consistent with updated_hawkins_sutton_slr.py).
COLORS = {
    "emissions": "#d95f02",
    "climate":   "#7570b3",
    "internal":  "#1b9e77",
    "brick":     "#e7298a",
}


def _envelope(ax, df, color, ylabel, title):
    yp  = df.year.to_numpy()
    p5  = df.p5.to_numpy()  * ENVELOPE_UNIT_SCALE
    p50 = df.p50.to_numpy() * ENVELOPE_UNIT_SCALE
    p95 = df.p95.to_numpy() * ENVELOPE_UNIT_SCALE
    ax.fill_between(yp, p5, p95, color=color, alpha=0.20, label="5–95% band")
    ax.plot(yp, p50, color=color, linewidth=2.2, label="Median")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11.5, fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.5)


def _stack_gmst(ax, df):
    yp = df.year.to_numpy()
    f_emi  = df.f_emissions.to_numpy()
    f_clim = df.f_climate.to_numpy()
    ax.stackplot(yp, f_clim, f_emi,
                 labels=["Climate response (FaIR v2.2.4)",
                         "Emissions (RFF-SP)"],
                 colors=[COLORS["climate"], COLORS["emissions"]],
                 alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Fraction of variance", fontsize=10)
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right",
              fontsize=9, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)


def _stack_slr(ax, df):
    yp = df.year.to_numpy()
    f_emi  = df.f_emissions.to_numpy()
    f_clim = df.f_climate.to_numpy()
    f_int  = df.f_internal.to_numpy()
    f_br   = df.f_brick.to_numpy()
    ax.stackplot(yp, f_br, f_int, f_clim, f_emi,
                 labels=["BRICK posterior (AIS/GIS/TE)",
                         "AIS tipping-state dependence",
                         "Climate response (FaIR v2.2.4)",
                         "Emissions (RFF-SP)"],
                 colors=[COLORS["brick"], COLORS["internal"],
                         COLORS["climate"], COLORS["emissions"]],
                 alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Fraction of variance", fontsize=10)
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right",
              fontsize=8.5, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)


def main():
    for p in (GMST_VAR_CSV, SLR_VAR_CSV, GMST_BAND_CSV, SLR_BAND_CSV):
        if not p.exists():
            raise SystemExit(f"Missing input: {p}")
    g_var  = pd.read_csv(GMST_VAR_CSV)
    s_var  = pd.read_csv(SLR_VAR_CSV)
    g_band = pd.read_csv(GMST_BAND_CSV)
    s_band = pd.read_csv(SLR_BAND_CSV)
    g_var  = g_var [(g_var.year  >= PLOT_START) & (g_var.year  <= PLOT_END)].reset_index(drop=True)
    s_var  = s_var [(s_var.year  >= PLOT_START) & (s_var.year  <= PLOT_END)].reset_index(drop=True)
    g_band = g_band[(g_band.year >= PLOT_START) & (g_band.year <= PLOT_END)].reset_index(drop=True)
    s_band = s_band[(s_band.year >= PLOT_START) & (s_band.year <= PLOT_END)].reset_index(drop=True)

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5),
                             gridspec_kw=dict(wspace=0.22, hspace=0.28,
                                              height_ratios=[3, 2]))
    # Row 1: marginal envelopes (same as pulse_responses_clean — GMST from
    # production pulse, SLR from 0.01 GtC small-pulse to avoid AIS fat tail).
    _envelope(axes[0, 0], g_band, color="#A6361C",
              ylabel="ΔGMST  (°C per GtCO₂)",
              title="Marginal GMST — 1 GtCO₂ pulse at 2030")
    _envelope(axes[0, 1], s_band, color="#1F4E79",
              ylabel="ΔSLR  (cm per GtCO₂)",
              title="Marginal SLR — 1 GtCO₂ pulse at 2030")
    # Row 2: variance fractions (necessarily at +1 GtC production pulse for
    # SLR, since the AIS tipping-state variance only surfaces at that scale).
    _stack_gmst(axes[1, 0], g_var)
    _stack_slr(axes[1, 1], s_var)

    fig.suptitle("Sources of uncertainty in the marginal climate response\n"
                 "to a 1 GtCO₂ pulse at 2030",
                 fontsize=13, fontweight="bold", color="#1F4E79", y=1.005)
    fig.tight_layout()
    fig.savefig(OUT / "pulse_hawkins_sutton.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "pulse_hawkins_sutton.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'pulse_hawkins_sutton.png'}")

    print("\nGMST fractions at landmark years:")
    for y in (2050, 2075, 2100, 2125, 2150):
        r = g_var[g_var.year == y]
        rb = g_band[g_band.year == y]
        if len(r) and len(rb):
            r0, rb0 = r.iloc[0], rb.iloc[0]
            print(f"  {y}: f_emi={r0.f_emissions:.2f}  f_clim={r0.f_climate:.2f}  "
                  f"median ΔGMST={rb0.p50 * ENVELOPE_UNIT_SCALE:+.5f} °C/GtCO₂")
    print("\nSLR fractions at landmark years:")
    for y in (2050, 2075, 2100, 2125, 2150):
        r = s_var[s_var.year == y]
        rb = s_band[s_band.year == y]
        if len(r) and len(rb):
            r0, rb0 = r.iloc[0], rb.iloc[0]
            print(f"  {y}: f_emi={r0.f_emissions:.2f}  f_clim={r0.f_climate:.2f}  "
                  f"f_int={r0.f_internal:.2f}  f_brick={r0.f_brick:.2f}  "
                  f"median ΔSLR={rb0.p50 * ENVELOPE_UNIT_SCALE:+.4f} cm/GtCO₂")


if __name__ == "__main__":
    main()
