"""
exceedance_table.py
===================

Substack figure / table: probability that GMST exceeds each of a range
of half-degree-Celsius thresholds (rel. preindustrial 1850–1900) at
each of three future-year horizons (2050 / 2100 / 2150).

Computed across the full FaIR ensemble (398 RFFs × 841 configs = 334,718
trajectories per year), with each trajectory's GMST anomaly anchored to
its OWN 1850–1900 mean (the preindustrial reference period).

Output:
  outputs/substack/exceedance_table.{png,pdf}
  outputs/substack/exceedance_table.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
# v1.4.5 LHS-10k baseline cube (10,000 cells × 451 yrs, flat schema).  Keys:
# cells_meta (n_cells, 3), years (n_year,), gmst_traj (n_cells, n_year),
# ohc_traj (n_cells, n_year), erf_2100 (n_cells,). Supersedes the legacy
# 3D lhs_pilot_gmst_full_N200_to2300.npz; the RFF inventory expanded from
# 3,000 → 10,000 in the v145 redesign.
CUBE = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
        / "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz")
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

YEARS      = [2050, 2100, 2150]
THRESHOLDS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]   # °C rel preindustrial
PI_PERIOD  = (1850, 1900)
# AR6-style bias correction: rebaseline each trajectory to a recent observed
# decadal anchor and express absolute warming as (observed anchor rel PI) +
# (trajectory's modelled change from anchor).  FaIR v2.2.4's ensemble-median
# modelled 2015-2024 is +1.04 °C rel PI vs Berkeley Earth's +1.32 °C — model
# rel-PI under-states observed present by ~0.29 °C.  Bias correction respects
# observed present and is AR6's projection framing.
RECENT_BASELINE  = (2015, 2024)
OBS_RECENT_REL_PI = 1.254                                   # IGCC 2024 4-dataset consensus 2015-2024 mean rel 1850-1900


def main():
    nz = np.load(CUBE)
    years = np.asarray(nz["years"], dtype=int)
    # v145 flat-cube schema: gmst_traj is (n_cells, n_year). Each cell is a
    # unique (rff_idx, fair_cfg_idx, seed_idx) tuple. No need to ravel a
    # multi-axis tensor — the rows are already the ensemble.
    cube = nz["gmst_traj"].astype(np.float64)
    n_cells, n_yr = cube.shape

    # Cube is rel each trajectory's 1850-1900 mean. Rebaseline each traj at
    # its own RECENT_BASELINE mean and shift up to observed BE rel-PI anchor.
    recent_mask = (years >= RECENT_BASELINE[0]) & (years <= RECENT_BASELINE[1])
    traj_recent = cube[:, recent_mask].mean(axis=1)        # (n_cells,)
    cube_pi     = cube - traj_recent[:, None] + OBS_RECENT_REL_PI
    print(f"cube: {n_cells} cells × {n_yr} years (v1.4.5 LHS-10k); "
          f"bias-corrected to IGCC {RECENT_BASELINE[0]}-{RECENT_BASELINE[1]} = "
          f"+{OBS_RECENT_REL_PI:.3f} °C rel PI")

    # Compute P(GMST > T) per (year, threshold)
    rows = []
    for y in YEARS:
        iy = int(np.where(years == y)[0][0])
        slab = cube_pi[:, iy]                              # n_cells vals
        for T in THRESHOLDS:
            p = float((slab > T).mean())
            rows.append({"year": y, "threshold_C": T, "P_exceed": p})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "exceedance_table.csv", index=False)

    # ============================================================== render table
    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    header = ["Threshold (°C rel. preindustrial)"] + [str(y) for y in YEARS]
    table_data = [header]
    for T in THRESHOLDS:
        row = [f"≥ {T:.1f} °C"]
        for y in YEARS:
            p = df[(df.year == y) & (df.threshold_C == T)].P_exceed.iloc[0]
            if p >= 0.995:
                row.append(">99%")
            elif p < 0.005:
                row.append("<1%")
            else:
                row.append(f"{100*p:.0f}%")
        table_data.append(row)

    n_rows, n_cols = len(table_data), len(header)
    col_widths = [0.46] + [0.18] * len(YEARS)
    table = ax.table(cellText=table_data, colWidths=col_widths,
                     cellLoc="center", bbox=[0.0, 0.18, 1.0, 0.82])
    table.auto_set_font_size(False)
    table.set_fontsize(11)

    # Header styling + cell colors by probability magnitude
    for r in range(n_rows):
        for c in range(n_cols):
            cell = table[(r, c)]
            cell.set_edgecolor("#cccccc")
            cell.set_linewidth(0.6)
            if r == 0:
                cell.set_facecolor("#1F4E79")
                cell.set_text_props(color="white", fontweight="bold",
                                    fontsize=10)
            else:
                if c == 0:
                    cell.set_facecolor("#E0E6EE")
                    cell.set_text_props(color="#1F4E79", fontweight="bold")
                else:
                    # color cells by probability magnitude (light gradient)
                    y = YEARS[c - 1]
                    T = THRESHOLDS[r - 1]
                    p = df[(df.year == y) & (df.threshold_C == T)].P_exceed.iloc[0]
                    # interpolate FAFAFA → C73930 via prob
                    p_clip = min(max(p, 0.0), 1.0)
                    # simple two-color blend
                    base = np.array([0.98, 0.98, 0.98])
                    hot  = np.array([0.78, 0.22, 0.19])
                    rgb = base * (1 - p_clip) + hot * p_clip
                    cell.set_facecolor(tuple(rgb))

    fig.text(0.5, 0.03,
             f"FaIR v2.2.4 (v1.4.5 calibration) LHS-10k ensemble: {n_cells:,} cells "
             f"(unique rff × cfg × seed combinations).  AR6-style bias "
             f"correction:\neach trajectory rebaselined at its own "
             f"{RECENT_BASELINE[0]}–{RECENT_BASELINE[1]} mean, shifted to "
             f"IGCC 2024 observed anchor of +{OBS_RECENT_REL_PI:.2f} °C rel "
             f"{PI_PERIOD[0]}–{PI_PERIOD[1]}.",
             ha="center", va="bottom", fontsize=8.5, style="italic", color="#666")

    fig.savefig(OUT / "exceedance_table.png", dpi=300,
                bbox_inches="tight", pad_inches=0.05)
    fig.savefig(OUT / "exceedance_table.pdf",
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"wrote {OUT / 'exceedance_table.png'}")

    # Console preview
    print()
    print(df.pivot(index="threshold_C", columns="year", values="P_exceed")
            .map(lambda v: f"{100*v:5.1f}%"))


if __name__ == "__main__":
    main()
