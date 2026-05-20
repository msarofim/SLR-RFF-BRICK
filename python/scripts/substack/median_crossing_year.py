"""
median_crossing_year.py
=======================

Substack table: focused single-column "median year exceeded" lookup for every
GMST threshold (rel. preindustrial 1850-1900) whose probability of exceedance
crosses 50% at some point in the FaIR ensemble's time range (1850-2300).

Companion to exceedance_table.py (probability at fixed years) and
exceedance_crossing_year.py (5th / median / 95th percentile years).  This one
strips down to just the median crossing year, which is the most-cited
"by-when" number for each threshold.

Output:
  outputs/substack/median_crossing_year.{png,pdf}
  outputs/substack/median_crossing_year.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
CUBE = ROOT / "outputs" / "lhs_pilot_gmst_full_N200_to2300.npz"
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
PI_PERIOD  = (1850, 1900)
# AR6-style bias correction — see comment block in exceedance_table.py.
RECENT_BASELINE  = (2015, 2024)
OBS_RECENT_REL_PI = 1.254   # IGCC 2024 4-dataset consensus 2015-2024 mean rel 1850-1900


def main():
    nz = np.load(CUBE)
    years = nz["years"]
    cube  = nz["gmst_traj_rff"].astype(np.float64)
    n_rff, n_cfg, n_yr = cube.shape

    recent_mask = (years >= RECENT_BASELINE[0]) & (years <= RECENT_BASELINE[1])
    traj_recent = cube[:, :, recent_mask].mean(axis=2)
    cube_pi     = cube - traj_recent[:, :, None] + OBS_RECENT_REL_PI
    flat = cube_pi.reshape(n_rff * n_cfg, n_yr)

    rows = []
    for T in THRESHOLDS:
        p = (flat > T).mean(axis=0)
        idx = np.where(p > 0.50)[0]
        if len(idx) == 0:
            continue
        rows.append({
            "threshold_C": T,
            "median_crossing_year": int(years[idx[0]]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "median_crossing_year.csv", index=False)
    print(df.to_string(index=False))

    # -------------------- render table figure --------------------
    fig, ax = plt.subplots(figsize=(7.5, 0.65 + 0.55 * (len(df) + 1)))
    ax.axis("off")

    header = ["Threshold (°C rel. preindustrial)", "Median crossing\nyear"]
    cells = [header] + [
        [f"≥ {r['threshold_C']:.1f} °C", str(int(r['median_crossing_year']))]
        for _, r in df.iterrows()
    ]
    n_rows = len(cells)
    table = ax.table(cellText=cells, colWidths=[0.60, 0.40],
                     cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.7)
    for r in range(n_rows):
        for c in range(2):
            cell = table[(r, c)]
            cell.set_edgecolor("#cccccc")
            cell.set_linewidth(0.6)
            if r == 0:
                cell.set_facecolor("#1F4E79")
                cell.set_text_props(color="white", fontweight="bold",
                                    fontsize=10)
            elif c == 0:
                cell.set_facecolor("#E0E6EE")
                cell.set_text_props(color="#1F4E79", fontweight="bold")

    fig.text(0.5, 0.08,
             f"FaIR ensemble: {n_rff} RFFs × {n_cfg} configs "
             f"({n_rff * n_cfg:,} trajectories per year).  AR6-style bias "
             f"correction:\nrebaselined at {RECENT_BASELINE[0]}–{RECENT_BASELINE[1]} "
             f"IGCC anchor (+{OBS_RECENT_REL_PI:.2f} °C rel PI). Only "
             f"thresholds with P(exceedance) ≥ 50% within "
             f"{int(years.min())}–{int(years.max())} are listed.",
             ha="center", va="bottom", fontsize=8.5, style="italic", color="#666")
    fig.tight_layout(rect=[0, 0.14, 1, 1.00])
    fig.savefig(OUT / "median_crossing_year.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "median_crossing_year.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'median_crossing_year.png'}")


if __name__ == "__main__":
    main()
