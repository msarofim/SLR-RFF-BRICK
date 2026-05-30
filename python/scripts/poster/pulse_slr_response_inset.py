"""
pulse_slr_response_inset.py
===========================

Small standalone inset figure for poster Panel D: the TOTAL pulse-marginal SLR
*response trajectory* (cm per GtCO2), median + 5-95% band, as a complement to
the Panel-D Hawkins-Sutton decomposition (which shows the *variance shares*,
not the magnitude).

Data: outputs/substack/co2_pulse_slr_summary_lhs10k_0p01gtc.csv
  (0.01-GtC small-pulse arm; SC-GHG-relevant linear-regime per-GtCO2 response,
   already in cm/GtCO2 since FaIR v1.4.5 CO2 FFI input_unit is GtCO2).

Conventions (locked 2026-05-29):
  - x-axis STARTS AT 2030 (the pulse year); the pre-pulse zero years are dropped.
  - NO ensemble-mean line: the mean is corrupted by a few pulse-induced
    AIS-tipped draws and is not pulse-size-invariant (mimibrick-quirks SS11).
    Median + 5-95% band only.

Output:
  outputs/poster/E_pulse_slr_response_inset.{png,pdf}
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
SUBSTACK = ROOT / "outputs" / "substack"
POSTER = ROOT / "outputs" / "poster"

CSV = SUBSTACK / "co2_pulse_slr_summary_lhs10k_0p01gtc.csv"
OUT_STEM = "E_pulse_slr_response_inset"

PULSE_YEAR = 2030          # x-axis starts here (the pulse year)
PLOT_END = 2150
LINE_COLOR = "#1F4E79"
BAND_COLOR = "#1F4E79"


def main():
    df = pd.read_csv(CSV)
    df = df[(df.year >= PULSE_YEAR) & (df.year <= PLOT_END)]
    yr = df.year.to_numpy()

    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    ax.fill_between(yr, df.p5, df.p95, color=BAND_COLOR, alpha=0.18,
                    label="5–95%")
    ax.plot(yr, df.p50, color=LINE_COLOR, linewidth=2.0, label="Median")
    ax.axhline(0, color="grey", linewidth=0.5)

    ax.set_xlim(PULSE_YEAR, PLOT_END)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("ΔSLR (cm per GtCO₂)", fontsize=9)
    ax.set_title("Pulse SLR response (0.01 GtCO₂)",
                 fontsize=9.5, fontweight="bold", color=LINE_COLOR)
    ax.tick_params(labelsize=8)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(alpha=0.3, linewidth=0.5)

    fig.tight_layout(pad=0.4)
    for ext in ("png", "pdf"):
        fig.savefig(POSTER / f"{OUT_STEM}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {POSTER / OUT_STEM}.{{png,pdf}}")
    print(f"  x-axis: {PULSE_YEAR}-{PLOT_END}; median at 2150 = "
          f"{df[df.year==2150].p50.iloc[0]:.4f} cm/GtCO₂")


if __name__ == "__main__":
    main()
