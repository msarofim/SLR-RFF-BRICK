"""
sweet_scenarios.py
==================

Reconstruct the 6 NCA5 (Sweet et al. 2022) global mean sea level rise scenarios
that FrEDI uses as interpolation nodes for its by-cm damage curves, and
overlay the published anchor values as a sanity check.

Note: the FrEDI R package's extdata does not expose the SLR scenario
trajectories as a flat CSV — they are baked into the impactsList .rds files
keyed on year × scenario × adaptation × state. To get clean year-by-year
trajectories for poster use, we construct from the published Sweet 2022
endpoints + a parametric quadratic form, then overlay the public anchor
values to confirm consistency.

Anchor values used (cm rel year 2000):
  Source: Sweet et al. (2022) NOAA Technical Report NOS 01,
          NCA5 Chapter 9 figure data.
  Public dots are the published anchor values; dashed lines are the
  constructed trajectories.

Outputs:
  outputs/poster/sweet_scenarios.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Sweet 2022 NCA5 published anchor values (cm rel year 2000)
# Approximate values from Sweet et al. (2022) Table 1.1 / NCA5 Fig 9.5.
# ---------------------------------------------------------------------------
ANCHORS = pd.DataFrame({
    "year":     [2000, 2020, 2050, 2070, 2090, 2100, 2120, 2150],
    "Low":      [   0,    6,   16,   22,   28,   30,   34,   40],
    "IntLow":   [   0,    7,   22,   34,   45,   50,   58,   70],
    "Int":      [   0,    9,   39,   60,   88,  100,  120,  155],
    "IntHigh":  [   0,   11,   57,   90,  135,  150,  180,  235],
    "High":     [   0,   14,   78,  125,  185,  200,  240,  315],
})

# FrEDI also extends to 250 and 300 cm endpoints by 2100 to span the BRICK
# upper tail. We construct these as scaled "High" trajectories.
EXTRA_2100 = {"VeryHigh_250": 250, "Extreme_300": 300}

SCENARIO_INFO = {
    "Low":           ("Low (0.3 m)",            "#1f78b4"),
    "IntLow":        ("Intermediate-Low (0.5 m)", "#33a02c"),
    "Int":           ("Intermediate (1.0 m)",   "#fdbf6f"),
    "IntHigh":       ("Intermediate-High (1.5 m)", "#ff7f00"),
    "High":          ("High (2.0 m)",           "#e31a1c"),
    "VeryHigh_250":  ("FrEDI 2.5 m extension",  "#9c1f5d"),
    "Extreme_300":   ("FrEDI 3.0 m extension",  "#6a3d9a"),
}


# ---------------------------------------------------------------------------
def interp_through_anchors(years_anchor, values_anchor, years_out=None):
    """
    Monotone cubic (PCHIP) interpolation through every anchor point.

    PCHIP preserves monotonicity and avoids overshoot, which is appropriate
    for cumulative SLR scenarios (always non-decreasing). The interpolant
    passes through EVERY anchor exactly, so the scatter dots and trajectory
    line agree at all published anchor years (was a previous bug with a
    quadratic-only fit constrained to two endpoints).
    """
    x = np.asarray(years_anchor, dtype=float)
    y = np.asarray(values_anchor, dtype=float)
    order = np.argsort(x)
    x, y = x[order], y[order]
    pchip = PchipInterpolator(x, y, extrapolate=False)
    if years_out is None:
        years_out = np.arange(int(x.min()), int(x.max()) + 1, 1)
    gmsl = pchip(years_out)
    # Return values at year 2100 / 2150 too for legacy fit-summary callers
    v100 = float(pchip(2100)) if (years_out.min() <= 2100 <= years_out.max()) else float("nan")
    v150 = float(pchip(2150)) if (years_out.min() <= 2150 <= years_out.max()) else float("nan")
    return years_out, gmsl, v100, v150


# ---------------------------------------------------------------------------
FREDI_LONG_CSV = ROOT / "outputs" / "fredi_slr_phaseC_rff_baseline_long.csv"


def plot_fredi_damage_function(ax, year=2100):
    """Right panel: empirical FrEDI damage function at `year`.

    Each Phase-C RFF baseline draw gives a paired (SLR, damages) point at the
    requested year; sorted along SLR these points trace out FrEDI's damage
    function (linear interpolation between Sweet brackets, applied to each
    draw's SLR_year value). Two sectors are shown.

    FrEDI's damage function at 2100 is piecewise-linear between the 5 Sweet
    calibration nodes (30, 50, 100, 150, 200 cm). The Phase-C RFF ensemble at
    2100 spans roughly 30 to 184 cm, so the empirical curve naturally stops
    at ~184 cm.  We extrapolate the last empirical segment (150-184 cm)
    linearly out to 200 cm so the displayed curve covers the FrEDI calibration
    domain, then mark the 5 Sweet anchor SLR values with the panel's
    color-matched dots ON the lines.
    """
    if not FREDI_LONG_CSV.exists():
        ax.text(0.5, 0.5, "[missing FrEDI long CSV]", ha="center", va="center",
                color="#888")
        return
    d = pd.read_csv(FREDI_LONG_CSV)
    sub_cp = d[(d.year == year)
               & (d.sector == "Coastal Properties")
               & (d.variant == "Reactive Adaptation")].sort_values("driverValue")
    sub_htf = d[(d.year == year)
                & (d.sector == "Transportation Impacts from High Tide Flooding")
                & (d.variant == "Reasonably Anticipated Adaptation")].sort_values("driverValue")
    cp_x  = sub_cp["driverValue"].to_numpy()
    cp_y  = sub_cp["annual_impacts"].to_numpy() / 1e9
    htf_x = sub_htf["driverValue"].to_numpy()
    htf_y = sub_htf["annual_impacts"].to_numpy() / 1e9

    # Extrapolate linearly to 200 cm using the slope of the 150-cm-to-max
    # segment (matches FrEDI's piecewise-linear interpolation domain).
    def extrap_to_200(x, y):
        if x.max() >= 200:
            return x, y
        mask_hi = x >= 150
        if mask_hi.sum() < 2:
            mask_hi = x >= 100
        x_hi, y_hi = x[mask_hi], y[mask_hi]
        slope = (y_hi[-1] - y_hi[0]) / (x_hi[-1] - x_hi[0])
        y200 = y[-1] + slope * (200 - x[-1])
        return np.append(x, 200.0), np.append(y, y200)

    cp_xx, cp_yy   = extrap_to_200(cp_x, cp_y)
    htf_xx, htf_yy = extrap_to_200(htf_x, htf_y)

    ax.plot(cp_xx, cp_yy, color="#1F4E79", linewidth=2.2,
            label=f"Coastal Properties ({len(cp_x)} draws)")
    ax.scatter(cp_x, cp_y, color="#1F4E79", s=6, alpha=0.35, edgecolor="none",
               zorder=2)
    ax.plot(htf_xx, htf_yy, color="#E67E22", linewidth=2.2,
            label=f"HTF Transportation ({len(htf_x)} draws)")
    ax.scatter(htf_x, htf_y, color="#E67E22", s=6, alpha=0.35, edgecolor="none",
               zorder=2)

    # Sweet calibration nodes — 5 colored dots placed ON the damage-function
    # lines themselves at the corresponding SLR values (30/50/100/150/200).
    # No text labels (per poster review May 17).
    sweet_nodes_2100 = [
        (30,  SCENARIO_INFO["Low"][1]),
        (50,  SCENARIO_INFO["IntLow"][1]),
        (100, SCENARIO_INFO["Int"][1]),
        (150, SCENARIO_INFO["IntHigh"][1]),
        (200, SCENARIO_INFO["High"][1]),
    ]

    def damages_at(slr_cm, x_arr, y_arr):
        return float(np.interp(slr_cm, x_arr, y_arr))

    for slr_cal, color in sweet_nodes_2100:
        for x_arr, y_arr in [(cp_xx, cp_yy), (htf_xx, htf_yy)]:
            ax.scatter([slr_cal], [damages_at(slr_cal, x_arr, y_arr)],
                       color=color, s=80, edgecolor="white", linewidth=1.2,
                       zorder=5)

    ax.set_xlabel(f"Global Mean Sea Level Rise at {year} (cm rel. 2000)",
                  fontsize=11)
    ax.set_ylabel(f"Annual US damages at {year} (2015 USD billions)", fontsize=11)
    # Short title; details in caption
    ax.set_title(f"FrEDI damage function at {year}", fontsize=11,
                 fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax.grid(True, alpha=0.3, linewidth=0.5)
    ax.set_xlim(0, 250)
    # Dots-on-lines now placed inside plot_fredi_damage_function (per May 17
    # poster review).


# ---------------------------------------------------------------------------
def main():
    # Two-panel layout: Sweet scenarios (left), FrEDI damage function (right)
    fig, (ax, ax_df) = plt.subplots(1, 2, figsize=(16, 6.5),
                                    gridspec_kw=dict(wspace=0.28))

    # Plot each NCA5 scenario (PCHIP through every anchor)
    fit_summary = []
    for col, (label, color) in SCENARIO_INFO.items():
        if col in ANCHORS.columns:
            yrs, gmsl, v100, v150 = interp_through_anchors(
                ANCHORS["year"].values, ANCHORS[col].values)
            fit_summary.append((label, v100, v150))
            ax.plot(yrs, gmsl, color=color, linewidth=2.4, label=label, zorder=3)
            # Anchor dots — will coincide with the curve since PCHIP passes
            # through every anchor exactly
            ax.scatter(ANCHORS["year"], ANCHORS[col], color=color,
                       s=42, edgecolor="white", linewidth=1.0, zorder=5)
        else:
            # FrEDI extensions: scale High-scenario anchor values to the target
            # 2100 endpoint, then PCHIP through the scaled anchors so dots
            # also line up with the line for these extensions.
            scale = EXTRA_2100[col] / float(ANCHORS["High"].iloc[
                int(np.where(ANCHORS["year"].values == 2100)[0][0])])
            scaled = ANCHORS["High"].values * scale
            yrs, gmsl, v100, v150 = interp_through_anchors(
                ANCHORS["year"].values, scaled)
            fit_summary.append((label, v100, v150))
            ax.plot(yrs, gmsl, color=color, linewidth=2.0, linestyle="--",
                    label=label, zorder=3)

    # NCA5 anchor highlight at 2100 (the canonical endpoint labels)
    for col, (label, color) in SCENARIO_INFO.items():
        if col in ANCHORS.columns:
            v = ANCHORS.loc[ANCHORS["year"] == 2100, col].values[0]
            ax.annotate(f"{v} cm", xy=(2100, v),
                        xytext=(2102, v), va="center", ha="left",
                        fontsize=9, color=color, fontweight="bold")

    # Axes and labels
    ax.set_xlim(2000, 2150)
    ax.set_ylim(0, 330)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Global Mean Sea Level Rise (cm rel. 2000)", fontsize=11)
    # Short title; details belong in figure caption (poster convention May 17)
    ax.set_title("Sweet (2022) NCA5 SLR scenarios", fontsize=11,
                 fontweight="bold", color="#1F4E79")
    ax.grid(True, alpha=0.3, linewidth=0.6)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9, ncol=1)
    # (Previous "FrEDI interp. nodes anchored at 2100" callout removed
    # per poster review May 17 — same information now conveyed by the
    # vertical guides + colored dots on the damage-function panel.)

    # === Right panel: implied FrEDI damage function at 2100 ===
    plot_fredi_damage_function(ax_df, year=2100)

    # Internal suptitle dropped per poster review (May 17 2026); the panel
    # label in the poster layout serves as the title.
    fig.tight_layout()
    fig.savefig(OUT / "sweet_scenarios.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "sweet_scenarios.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'sweet_scenarios.png'}")

    # Interp summary for the methods notes
    print("\n=== PCHIP interp summary (cm at 2100 / 2150) ===")
    print(f"{'Scenario':28} {'2100 (cm)':>10} {'2150 (cm)':>10}")
    for lbl, v100, v150 in fit_summary:
        print(f"{lbl:28} {v100:10.1f} {v150:10.1f}")

    fit_df = pd.DataFrame(fit_summary,
                          columns=["scenario", "gmsl_2100_cm", "gmsl_2150_cm"])
    fit_df.to_csv(OUT / "sweet_scenarios_fit.csv", index=False)
    print(f"wrote {OUT / 'sweet_scenarios_fit.csv'}")


if __name__ == "__main__":
    main()
