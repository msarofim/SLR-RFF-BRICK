"""
exceedance_crossing_year.py
===========================

Substack figure / table: median year of crossing for each half-degree-Celsius
GMST threshold (rel. preindustrial 1850-1900), together with the 5th and
95th percentile years.  Only thresholds for which P(exceedance) >50% at
some point in the cube's time range are shown.

Method: for each threshold T, compute P(GMST(y) > T) for every year y over
all 398×841 trajectories (each anchored to its own 1850-1900 mean).  The
median crossing year is the first y at which P > 0.50; the P5 crossing
year is the first y at which P > 0.05 (when 5% of the ensemble has
crossed); the P95 crossing year is the first y at which P > 0.95.

Output:
  outputs/substack/exceedance_crossing_year.{png,pdf}
  outputs/substack/exceedance_crossing_year.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
# v1.4.5 LHS-10k baseline cube (flat schema: gmst_traj is (n_cells, n_year)).
# Supersedes the legacy 3D lhs_pilot_gmst_full_N200_to2300.npz.
CUBE = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
        / "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz")
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]   # °C rel preindustrial
PI_PERIOD  = (1850, 1900)
# AR6-style bias correction — see comment block in exceedance_table.py.
RECENT_BASELINE  = (2015, 2024)
OBS_RECENT_REL_PI = 1.254   # IGCC 2024 4-dataset consensus 2015-2024 mean rel 1850-1900


def first_year_above(p_series, years, p_threshold):
    idx = np.where(p_series > p_threshold)[0]
    if len(idx) == 0:
        return None
    return int(years[idx[0]])


def main():
    nz = np.load(CUBE)
    years = np.asarray(nz["years"], dtype=int)
    # v145 flat-cube schema (n_cells, n_year). Each cell = one (rff, cfg, seed).
    cube = nz["gmst_traj"].astype(np.float64)
    n_cells, n_yr = cube.shape

    recent_mask = (years >= RECENT_BASELINE[0]) & (years <= RECENT_BASELINE[1])
    traj_recent = cube[:, recent_mask].mean(axis=1)        # (n_cells,)
    cube_pi     = cube - traj_recent[:, None] + OBS_RECENT_REL_PI
    print(f"cube: {n_cells} cells × {n_yr} years (v1.4.5 LHS-10k); "
          f"bias-corrected to IGCC {RECENT_BASELINE[0]}-{RECENT_BASELINE[1]} = "
          f"+{OBS_RECENT_REL_PI:.3f} °C rel PI")

    rows = []
    for T in THRESHOLDS:
        # Fraction of trajectories above T, per year
        p_year = (cube_pi > T).mean(axis=0)
        y_p5  = first_year_above(p_year, years, 0.05)
        y_p50 = first_year_above(p_year, years, 0.50)
        y_p95 = first_year_above(p_year, years, 0.95)
        rows.append({
            "threshold_C": T,
            "year_p5_crossing":  y_p5,
            "year_p50_crossing": y_p50,
            "year_p95_crossing": y_p95,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "exceedance_crossing_year.csv", index=False)

    # Keep only thresholds for which P(exceedance) > 50% is reached (i.e.,
    # year_p50_crossing is non-null) per Marcus's spec.
    df_show = df[df.year_p50_crossing.notna()].copy()
    print()
    print(df_show.to_string(index=False))

    # ============================================================== render table
    fig, ax = plt.subplots(figsize=(9.0, 4.0))
    ax.axis("off")

    def fmt_year(v):
        if v is None or pd.isna(v):
            return "—"
        return str(int(v))

    header = ["Threshold (°C rel. preindustrial)",
              "5th percentile\nyear",
              "Median year\n(50% crossed)",
              "95th percentile\nyear"]
    table_data = [header]
    for _, r in df_show.iterrows():
        table_data.append([
            f"≥ {r['threshold_C']:.1f} °C",
            fmt_year(r["year_p5_crossing"]),
            fmt_year(r["year_p50_crossing"]),
            fmt_year(r["year_p95_crossing"]),
        ])

    n_rows = len(table_data)
    n_cols = 4
    col_widths = [0.46, 0.18, 0.18, 0.18]
    table = ax.table(cellText=table_data, colWidths=col_widths,
                     cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.7)

    for r in range(n_rows):
        for c in range(n_cols):
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

    fig.text(0.5, 0.06,
             f"FaIR v1.4.5 LHS-10k ensemble: {n_cells:,} cells "
             f"(unique rff × cfg × seed combinations).  AR6-style bias "
             f"correction:\neach trajectory rebaselined at its own "
             f"{RECENT_BASELINE[0]}–{RECENT_BASELINE[1]} mean, shifted to "
             f"IGCC 2024 observed anchor of +{OBS_RECENT_REL_PI:.2f} °C rel "
             f"{PI_PERIOD[0]}–{PI_PERIOD[1]}.",
             ha="center", va="bottom", fontsize=8.5, style="italic", color="#666")

    fig.tight_layout(rect=[0, 0.10, 1, 1.00])
    fig.savefig(OUT / "exceedance_crossing_year.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "exceedance_crossing_year.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'exceedance_crossing_year.png'}")


if __name__ == "__main__":
    main()
