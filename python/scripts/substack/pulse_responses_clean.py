"""
pulse_responses_clean.py
========================

Replacement substack figure for `pulse_responses.py`.  Uses the small-pulse
(linear-regime) SLR runs so the median + 5–95% band is pulse-size invariant
and directly SC-GHG-relevant.  GMST panels keep the production-pulse data
(no AIS tipping nonlinearity affects GMST, so 1 GtC / 1 Tg pulses already
sit in the linear regime).

2 × 2 grid:
    row 1: CO₂ pulse — Marginal GMST (1 GtC pulse)   |  Marginal SLR (0.01 GtC pulse)
    row 2: CH₄ pulse — Marginal GMST (1 Tg pulse)    |  Marginal SLR (1 Tg pulse)

Each panel shows median (heavy line) and 5–95% band.  No mean line — for the
SLR panels the mean is pulse-size sensitive at large pulse, so a clean per-
tonne SC-GHG number is best read off the median.  For CH4 SLR the 1-Tg
pulse is already in the linear regime (verified via 1 / 0.1 / 0.01 Tg
convergence in pulse_convergence.py); for CO2 SLR we use the 0.01 GtC
companion run because the 1-GtC pulse contaminates the upper tail with
pulse-induced AIS tipping that would not happen at infinitesimal pulse.

Output:
  outputs/substack/pulse_responses_clean.{png,pdf}
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

# Unit conversions so both gases display on a per-GtCO2(eq) mass basis.
#
# CO2: production runs use --pulse-gtc in carbon-mass units; 1 GtC of carbon
# = 3.664 GtCO2 by molecular weight (44/12).  Per-GtC marginal ÷ 3.664 =
# per-GtCO2 mass marginal.  Existing co2_pulse_*_summary.csv values are
# per-GtC; we scale them to per-GtCO2 here.
GTC_TO_GTCO2       = 44.0 / 12.0           # ≈ 3.667
PER_GTC_TO_PER_GTCO2 = 1.0 / GTC_TO_GTCO2  # ≈ 0.2727

# CH4: AR6 WG1 Ch.7 GWP100 = 27.0 (non-fossil) / 29.8 (fossil); use 27.9 as
# the conventional midpoint.  1 GtCO2eq via GWP100=27.9 ⇒ 1/27.9 Gt CH4 =
# 35.84 Tg CH4, so per-Tg-CH4 marginal × 35.84 = per-GtCO2eq marginal.
GWP100_CH4         = 27.9
TG_CH4_PER_GTCO2EQ = 1000.0 / GWP100_CH4   # ≈ 35.84

# Each panel: (csv_filename, gas_label, impact_label, display_units,
#              scale_factor, color, ax_row, ax_col)
PANELS = [
    # v1.4.5 CO2 GMST summary (LHS-10k Wong-weighted; per-GtCO2 directly,
    # so scale = 1.0). The legacy v1.4.1-era co2_pulse_gmst_summary.csv was
    # per-GtC and needed PER_GTC_TO_PER_GTCO2 to convert.
    ("co2_pulse_gmst_summary_v145.csv",   "1 GtCO₂ pulse at 2030",
        "Marginal GMST",                  "°C per GtCO₂",
        1.0,                              "#A6361C", 0, 0),
    # CO2 SLR scale = 1.0: the v1.4.5 summary is already in cm per GtCO₂
    # (FaIR CO2 FFI input_unit is "GtCO2"). The CH4 panels below still use
    # the GWP100 conversion because their summaries are per-Tg-CH4.
    ("co2_pulse_slr_summary_lhs10k_0p01gtc.csv", "1 GtCO₂ pulse at 2030",
        "Marginal SLR",   "cm per GtCO₂",
        1.0,                              "#1F4E79", 0, 1),
    # CH4 GMST: legacy v1.4.1-era summary retained.  The v1.4.5 cube stores
    # GMST in float32; the per-Tg CH4 marginal at 2100/2150 (~1e-5 °C/Tg)
    # hits the float32 precision floor and rounds many cells to 0,
    # making weighted percentiles unreliable.  Per Test 1
    # (2026-05-25), FaIR v141 vs v145 ensemble-mean GMST pulse response
    # agrees within 5%, so this v141 summary is faithful to v145 physics.
    ("ch4_pulse_gmst_summary.csv",        "1 GtCO₂eq CH₄ pulse at 2030",
        "Marginal GMST",
        f"°C per GtCO₂eq (AR6 GWP100={GWP100_CH4:.1f})",
        TG_CH4_PER_GTCO2EQ,               "#A6361C", 1, 0),
    # v1.4.5 CH4 small-pulse summary (0.01-Tg CH4 pulse, post-PR#93 BRICK,
    # 10k-RFF LHS). Replaces the v1.4.1-era 1-Tg paired-RFF summary
    # (ch4_pulse_slr_summary_1p0tg.csv) so CH4 and CO2 panels are now both on
    # the same v1.4.5 + post-PR#93 calibration footing.
    ("ch4_pulse_slr_summary_lhs10k_0p01tg.csv", "1 GtCO₂eq CH₄ pulse at 2030",
        "Marginal SLR",
        f"cm per GtCO₂eq (AR6 GWP100={GWP100_CH4:.1f})",
        TG_CH4_PER_GTCO2EQ,               "#1F4E79", 1, 1),
]


def render_panel(ax, csv_path, gas, impact, display_units, scale, color):
    if not csv_path.exists():
        ax.text(0.5, 0.5, f"[missing]\n{csv_path.name}",
                ha="center", va="center", fontsize=10, color="#888",
                transform=ax.transAxes)
        ax.set_title(f"{gas} — {impact}",
                     fontsize=11, fontweight="bold", color="#1F4E79")
        ax.set_xlim(PLOT_START, PLOT_END)
        return
    df = pd.read_csv(csv_path)
    df = df[(df.year >= PLOT_START) & (df.year <= PLOT_END)]
    yp  = df.year.to_numpy()
    p5  = df.p5.to_numpy()  * scale
    p50 = df.p50.to_numpy() * scale
    p95 = df.p95.to_numpy() * scale
    ax.fill_between(yp, p5, p95, color=color, alpha=0.18, label="5–95% band")
    ax.plot(yp, p50, color=color, linewidth=2.4, label="Median")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel(display_units, fontsize=10)
    ax.set_title(f"{gas} — {impact}",
                 fontsize=11, fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.5)


def main():
    fig, axes = plt.subplots(2, 2, figsize=(12, 8),
                             gridspec_kw=dict(wspace=0.22, hspace=0.32))
    for csv, gas, impact, disp, scale, color, r, c in PANELS:
        render_panel(axes[r, c], OUT / csv, gas, impact, disp, scale, color)

    fig.suptitle("Marginal climate response to greenhouse-gas pulses\n"
                 "Per GtCO₂ mass for CO₂; per GtCO₂eq for CH₄ "
                 f"(AR6 GWP100={GWP100_CH4:.1f}).",
                 fontsize=12.5, fontweight="bold", color="#1F4E79", y=1.01)
    fig.tight_layout()
    fig.savefig(OUT / "pulse_responses_clean.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "pulse_responses_clean.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'pulse_responses_clean.png'}")

    print(f"\nHeadline median values at landmark years (scales: CO₂ ÷"
          f" {GTC_TO_GTCO2:.3f}; CH₄ × {TG_CH4_PER_GTCO2EQ:.2f} Tg/GtCO₂eq):")
    for csv, gas, impact, disp, scale, color, r, c in PANELS:
        path = OUT / csv
        if not path.exists(): continue
        df = pd.read_csv(path)
        for y in (2050, 2100, 2150):
            sub = df[df.year == y]
            if len(sub):
                r0 = sub.iloc[0]
                print(f"  {gas} {impact} @ {y}: "
                      f"median={r0.p50*scale:+.5g} {disp}  "
                      f"P5={r0.p5*scale:+.5g}  P95={r0.p95*scale:+.5g}")


if __name__ == "__main__":
    main()
