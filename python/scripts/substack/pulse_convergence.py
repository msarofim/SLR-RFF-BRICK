"""
pulse_convergence.py
====================

Substack figure: marginal SLR per unit pulse vs year for three pulse sizes
each of CO2 and CH4.  Demonstrates pulse-size sensitivity / linearity of
the SC-GHG-relevant per-unit marginal:

  - CH4: all three pulse sizes (1, 0.1, 0.01 Tg) give identical per-unit
    marginal — pulse-size invariant; SC-CH4 well-defined at 1 Tg.
  - CO2: per-unit median is stable across pulse sizes, but per-unit mean
    is NOT — large pulses trigger pulse-induced AIS tipping that biases
    the mean.  Smaller pulses also reveal an "always-tips" draw (row 201,
    baseline ais_2100 = 29.6 cm) whose absolute jump is fixed regardless
    of pulse magnitude, so its per-unit contribution scales as 1/pulse.

Each panel overlays the three pulse sizes' per-unit median and ±band.
Reads the brick_paired_rff_<scen>_to2300_weighted.csv files produced by
slurm/submit_repair_with_ais2150.sh and slurm/submit_small_pulse_brick.sh.

Output:
  outputs/substack/pulse_convergence.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

PLOT_START, PLOT_END = 2030, 2150
KEYS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]

# Mass-CO2 / CO2-eq conversions so the displayed marginal is on a per-tCO2
# basis (the SC-GHG convention).  Production pulses are in GtC for CO2 and
# Tg for CH4; the unit display scale below is "per pulse unit → per GtCO2(eq)".
GTC_TO_GTCO2       = 44.0 / 12.0     # 1 GtC = 3.667 GtCO2 by mass
GWP100_CH4         = 27.9            # AR6 GWP100 midpoint (non-fossil/fossil)
TG_CH4_PER_GTCO2EQ = 1000.0 / GWP100_CH4   # ≈ 35.84

# Scenario inventory: (label, baseline CSV, pulse CSV, native pulse magnitude,
#                     conversion from per-native-unit → per-GtCO2(eq))
CO2_BASE = ROOT / "outputs" / "brick_paired_rff_baseline_to2300_weighted.csv"
CH4_BASE = ROOT / "outputs" / "brick_paired_rff_baseline_postfix_to2300_weighted.csv"

SCENARIOS = {
    "CO2": [
        # Pulse label, baseline, pulse CSV, GtC magnitude.  Marginal / GtC then
        # ÷ GTC_TO_GTCO2 = per-GtCO2 mass.  Apply both as `1/(size * 3.667)`.
        ("1.0 GtCO₂",  CO2_BASE, ROOT / "outputs/brick_paired_rff_pulse_to2300_weighted.csv",         1.0),
        ("0.1 GtCO₂",  CO2_BASE, ROOT / "outputs/brick_paired_rff_pulse0p1gtc_to2300_weighted.csv",   0.1),
        ("0.01 GtCO₂", CO2_BASE, ROOT / "outputs/brick_paired_rff_pulse0p01gtc_to2300_weighted.csv",  0.01),
    ],
    "CH4": [
        # Pulse label (Tg CH4) maps to GtCO2eq via × 35.84; net per-GtCO2eq
        # conversion = `35.84 / size`.
        ("1.0 Tg",   CH4_BASE, ROOT / "outputs/brick_paired_rff_ch4pulse_to2300_weighted.csv",        1.0),
        ("0.1 Tg",   CH4_BASE, ROOT / "outputs/brick_paired_rff_ch4pulse0p1tg_to2300_weighted.csv",   0.1),
        ("0.01 Tg",  CH4_BASE, ROOT / "outputs/brick_paired_rff_ch4pulse0p01tg_to2300_weighted.csv",  0.01),
    ],
}

# Color per pulse size (shared across gases so the legend reads as
# "pulse magnitude" not "scenario").  Largest → darkest.
COLORS = {"1.0": "#1F4E79", "0.1": "#3F7EB0", "0.01": "#7FB2D8"}


def per_unit_marginal(base_csv, pulse_csv, pulse_size, gas):
    """Returns per-GtCO2(eq) marginal SLR matrix.  Native pulse units are
    GtC (CO2) or Tg CH4 (CH4); convert to per-GtCO2 mass for CO2 (÷ 3.667)
    and per-GtCO2eq via GWP100 for CH4 (× 35.84)."""
    b = pd.read_csv(base_csv).sort_values(KEYS).reset_index(drop=True)
    p = pd.read_csv(pulse_csv).sort_values(KEYS).reset_index(drop=True)
    assert (b[KEYS].values == p[KEYS].values).all(), "key mismatch"
    yc = [c for c in b.columns if c.isdigit()]
    yrs = np.array([int(c) for c in yc])
    Mraw = (p[yc].to_numpy() - b[yc].to_numpy()) / pulse_size   # per-native cm
    if gas == "CO2":
        M = Mraw / GTC_TO_GTCO2          # per-GtCO2 mass
    else:  # CH4
        M = Mraw * TG_CH4_PER_GTCO2EQ    # per-GtCO2eq via GWP100
    w = b.w_norm.values
    return yrs, M, w


def w_quantile(v, w, q):
    o = np.argsort(v); v=v[o]; w=w[o]; cw=np.cumsum(w)
    return v[np.searchsorted(cw, q * cw[-1])]


def yearly_stats(M, w, yrs, plot_mask):
    mean   = np.array([np.average(M[:, j], weights=w) for j in range(M.shape[1])])
    median = np.array([w_quantile(M[:, j], w, 0.50) for j in range(M.shape[1])])
    p5     = np.array([w_quantile(M[:, j], w, 0.05) for j in range(M.shape[1])])
    p95    = np.array([w_quantile(M[:, j], w, 0.95) for j in range(M.shape[1])])
    return (yrs[plot_mask], mean[plot_mask], median[plot_mask],
            p5[plot_mask], p95[plot_mask])


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5),
                             gridspec_kw=dict(wspace=0.22))
    for col, gas in enumerate(["CO2", "CH4"]):
        ax = axes[col]
        unit_label = ("cm per GtCO₂" if gas == "CO2"
                      else f"cm per GtCO₂eq (AR6 GWP100={GWP100_CH4:.1f})")
        for label, base, pulse, size in SCENARIOS[gas]:
            yrs, M, w = per_unit_marginal(base, pulse, size, gas)
            plot_mask = (yrs >= PLOT_START) & (yrs <= PLOT_END)
            yp, mn, md, p5, p95 = yearly_stats(M, w, yrs, plot_mask)
            color_key = label.split()[0]
            c = COLORS[color_key]
            ax.fill_between(yp, p5, p95, color=c, alpha=0.10,
                            label=f"{label}: 5–95% band")
            ax.plot(yp, md, color=c, linewidth=2.2,
                    label=f"{label}: median")
            ax.plot(yp, mn, color=c, linewidth=1.0, linestyle="--",
                    label=f"{label}: mean")
        ax.axhline(0, color="grey", linewidth=0.5)
        ax.set_xlim(PLOT_START, PLOT_END)
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel(f"Marginal SLR per unit pulse ({unit_label})", fontsize=11)
        ax.set_title(f"{gas} pulse at 2030 — per-unit marginal SLR vs year\n"
                     "across three pulse magnitudes",
                     fontsize=12, fontweight="bold", color="#1F4E79")
        ax.grid(alpha=0.3, linewidth=0.5)
        # For CO2 the 1.0-GtCO2 pulse mean (per GtCO2) jumps to ~0.23 cm —
        # cap y-axis so smaller-pulse-size bands stay visible.
        if gas == "CO2":
            ax.set_ylim(0, 0.085)
        ax.legend(loc="upper left", fontsize=8.5, framealpha=0.92, ncol=3)

    fig.suptitle("Pulse-size convergence: linear regime vs nonlinear tipping",
                 fontsize=13.5, fontweight="bold", color="#1F4E79", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "pulse_convergence.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "pulse_convergence.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'pulse_convergence.png'}")

    # Print headline numbers (cm per GtCO2 or per GtCO2eq)
    print("\nHeadline per-unit marginal at 2150 (cm per GtCO₂[eq]):")
    for gas in ["CO2", "CH4"]:
        print(f"\n  === {gas} ===")
        for label, base, pulse, size in SCENARIOS[gas]:
            yrs, M, w = per_unit_marginal(base, pulse, size, gas)
            j = int(np.where(yrs == 2150)[0][0])
            mn = np.average(M[:, j], weights=w)
            md = w_quantile(M[:, j], w, 0.50)
            p95 = w_quantile(M[:, j], w, 0.95)
            print(f"    {label}: median={md:.5f}  mean={mn:.5f}  p95={p95:.5f}")


if __name__ == "__main__":
    main()
