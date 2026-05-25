"""
slr_pulse_vs_hermans_tsls.py
============================

Single-panel substack figure: v1.4.5 per-tCO₂ SLR pulse-marginal trajectory
2030-2150 vs. the Hermans et al. 2021 (Ocean Science 17:181) empirical
Transient Sea Level Sensitivity (TSLS) expectation.

The Hermans-TSLS expectation per year is:

    ΔSLR_pulse(t) = ∫_{t_pulse}^{t}  TSLS × ΔT_pulse(τ) / 100  dτ        (cm)

with TSLS = 0.40 ± 0.05 m/century/K from historical-observation analysis
1850-2017 (their Table 2), and ΔT_pulse(τ) from the FaIR v1.4.5 single-pulse
driver (1-GtCO₂ pulse in 2030; same calibration the BRICK ensemble uses).

The v1.4.5 BRICK pulse-marginal trajectory is the importance-weighted
median + 5-95 % band from the paired (rff, cfg, seed, post) cells of
the LHS-10k baseline + 0.01-GtCO₂ pulse arm (scaled to per-1-GtCO₂).

Output: outputs/substack/slr_pulse_vs_hermans_tsls.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "outputs" / "substack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- Inputs ----
BASELINE_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"
PULSE_CSV    = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_pulse_co2_pos_001gt_to2300.csv"

# FaIR single-pulse driver outputs (1-GtCO₂ pulse at 2030, v1.4.5 calibration).
FAIR_BASELINE = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI/"
                 "fair_outputs/temp_pulse_baseline_v145.csv")
FAIR_PULSE    = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI/"
                 "fair_outputs/temp_pulse_1Gt_2030_v145.csv")

PULSE_YEAR     = 2030
PULSE_SIZE_GTCO2 = 0.01    # FaIR v1.4.5 'CO2 FFI' input unit; BRICK arm.
TSLS_CENTRAL   = 0.40      # m / century / K — Hermans 2021 historical obs
TSLS_LOW       = 0.35      # central − 1σ
TSLS_HIGH      = 0.45      # central + 1σ
PLOT_START     = 2030
PLOT_END       = 2150

# Visual style
COLOR_MODEL = "#1F4E79"
COLOR_TSLS  = "#9C2727"


def main() -> None:
    # ---- v1.4.5 BRICK pulse-marginal trajectory ----
    b = pd.read_csv(BASELINE_CSV)
    p = pd.read_csv(PULSE_CSV)
    keys = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
    b = b.sort_values(keys).reset_index(drop=True)
    p = p.sort_values(keys).reset_index(drop=True)
    assert (b[keys].values == p[keys].values).all(), "key mismatch"

    yrs = np.array(sorted(int(c) for c in b.columns if c.isdigit()))
    cols = [str(y) for y in yrs]
    yb = b[cols].to_numpy(dtype=np.float64)
    yp = p[cols].to_numpy(dtype=np.float64)
    delta = (yp - yb) / PULSE_SIZE_GTCO2   # cm per 1-GtCO₂ pulse
    w = b.w_norm.to_numpy()

    def wq(v, w, q):
        o = np.argsort(v); v, w = v[o], w[o]
        cw = np.cumsum(w); cw /= cw[-1]
        return float(v[np.searchsorted(cw, q)])

    p05 = np.array([wq(delta[:, j], w, 0.05) for j in range(len(yrs))])
    p50 = np.array([wq(delta[:, j], w, 0.50) for j in range(len(yrs))])
    p95 = np.array([wq(delta[:, j], w, 0.95) for j in range(len(yrs))])

    # ---- Hermans 2021 TSLS expectation ----
    # ΔSLR_pulse(t) = ∫_{t_pulse}^t  TSLS × ΔT_pulse(τ) / 100  dτ   in cm/yr
    fb = pd.read_csv(FAIR_BASELINE)
    fp = pd.read_csv(FAIR_PULSE)
    fb = fb.set_index("year"); fp = fp.set_index("year")
    dT = fp["temp_C"] - fb["temp_C"]   # K, indexed by year
    # Build cumulative integral from PULSE_YEAR onward on the same yrs grid
    dT_per_year = dT.reindex(yrs).fillna(0.0).to_numpy()
    # ΔSLR per year of integration: TSLS (m/century/K) × ΔT (K) / 100 = m/yr
    # Then × 100 cm/m = cm/yr
    def integrate(tsls_m_per_cent_per_K: float) -> np.ndarray:
        rate_cm_per_yr = tsls_m_per_cent_per_K * dT_per_year   # cm/yr
        cum = np.cumsum(rate_cm_per_yr)
        # Zero before pulse year
        cum = np.where(yrs < PULSE_YEAR, 0.0, cum)
        return cum
    hermans_mid  = integrate(TSLS_CENTRAL)
    hermans_low  = integrate(TSLS_LOW)
    hermans_high = integrate(TSLS_HIGH)

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    m = (yrs >= PLOT_START) & (yrs <= PLOT_END)

    ax.fill_between(yrs[m], p05[m], p95[m],
                     color=COLOR_MODEL, alpha=0.22, linewidth=0,
                     label="v1.4.5 BRICK, 5–95 % importance-weighted")
    ax.plot(yrs[m], p50[m], color=COLOR_MODEL, lw=2.4, label="v1.4.5 BRICK median")

    ax.fill_between(yrs[m], hermans_low[m], hermans_high[m],
                     color=COLOR_TSLS, alpha=0.18, linewidth=0,
                     label=f"Hermans 2021 TSLS expectation (0.40 ± 0.05 m/century/K)")
    ax.plot(yrs[m], hermans_mid[m], color=COLOR_TSLS, lw=2.4, linestyle="--",
             label="Hermans-TSLS central")

    # Annotate landmark values at 2100 and 2150
    for y in (2100, 2150):
        i = int(np.where(yrs == y)[0][0])
        ax.annotate(f"{y}: {p50[i]:.4f}",
                     xy=(y, p50[i]),
                     xytext=(y + 2, p50[i] - 0.0015),
                     fontsize=8.5, color=COLOR_MODEL)
        ax.annotate(f"{y}: {hermans_mid[i]:.3f}",
                     xy=(y, hermans_mid[i]),
                     xytext=(y + 2, hermans_mid[i] + 0.0005),
                     fontsize=8.5, color=COLOR_TSLS)
        ax.axvline(y, color="grey", lw=0.4, alpha=0.5)

    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Marginal SLR  (cm per GtCO₂ pulse at 2030)", fontsize=11)
    ax.set_title(
        "Per-tCO₂ sea-level response: model vs. historical-observation benchmark",
        fontsize=12, fontweight="bold", color="#1A1A1A")
    ax.grid(alpha=0.3, lw=0.4)
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.92)

    fig.tight_layout(rect=[0, 0.06, 1, 0.97])
    fig.text(
        0.5, 0.01,
        "Model: FaIR v2.2.4 + MimiBRICK v1.0.1.  Calibration: FaIR-calibrate "
        "v1.4.5 (Smith et al. 2024) + post-PR#93 BRICK joint posterior (Wong, 2026).  "
        "Emissions: Smith 2024 historical (1750–2020) spliced with 10,000 RFF-SP "
        "draws (Rennert et al. 2022) for 2021+; LHS-10k baseline + 0.01-GtCO₂ "
        "pulse at 2030.  Hermans-TSLS expectation = TSLS × ∫ ΔT_pulse(τ)dτ, with "
        "TSLS from Hermans et al. 2021 (OS 17:181, historical-obs central value 0.40 "
        "± 0.05 m/century/K) and ΔT_pulse from the v1.4.5 single-pulse FaIR driver.",
        ha="center", va="bottom", fontsize=7.8, style="italic",
        color="#444444", wrap=True)

    out_png = OUT_DIR / "slr_pulse_vs_hermans_tsls.png"
    out_pdf = OUT_DIR / "slr_pulse_vs_hermans_tsls.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Headline values
    print("\nLandmark per-tCO₂ pulse-marginal SLR (cm per GtCO₂):")
    print(f"  {'year':>6}  {'v1.4.5 p5/p50/p95':>30}   {'Hermans-TSLS low/mid/high':>30}   {'v145 / TSLS ratio':>18}")
    for y in (2050, 2075, 2100, 2125, 2150):
        i = int(np.where(yrs == y)[0][0])
        ratio = p50[i] / hermans_mid[i] if hermans_mid[i] > 0 else float("nan")
        print(f"  {y:>4}    "
              f"{p05[i]:>8.4f} / {p50[i]:>8.4f} / {p95[i]:>8.4f}    "
              f"{hermans_low[i]:>8.4f} / {hermans_mid[i]:>8.4f} / {hermans_high[i]:>8.4f}    "
              f"{ratio:>8.2f}×")


if __name__ == "__main__":
    main()
