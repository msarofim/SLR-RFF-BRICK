"""
plot_state_damages_2100.py
==========================

Build state-level chloropleth maps of FrEDI SLR-driven coastal damages at
year 2100 under the Phase C RFF baseline ensemble. Two panels:

  (a) Absolute annual damages (USD billion / year, importance-weighted median)
  (b) Per-capita annual damages (USD / person / year, importance-weighted median)

Inputs:
  outputs/fredi_slr_phaseC_rff_baseline_state_long.csv
  (FrEDI ICLUS state-population CSV — accessed via R/FrEDI extdata)

Outputs:
  outputs/plots/fredi_state_damages_2100.{png,pdf}
  outputs/plots/fredi_state_damages_2100_data.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import os
ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs"
PLOTS = OUT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

TARGET_YEAR = 2100
POP_PATH = Path(
    "/Library/Frameworks/R.framework/Versions/4.5-arm64/Resources/library/"
    "FrEDI/extdata/scenarios/State ICLUS Population.csv"
)

# Tag selects which FrEDI rerun's state-long CSV to plot. Defaults to legacy
# v1.4.1 (no tag). Set FREDI_TAG=v145_lhs10ks for v5 noise-isolated ensemble.
TAG = os.environ.get("FREDI_TAG", "")
STATE_LONG_BASENAME = (
    f"fredi_slr_phaseC_rff_baseline_{TAG}_state_long.csv" if TAG
    else "fredi_slr_phaseC_rff_baseline_state_long.csv"
)
OUT_PNG_BASENAME = (
    f"fredi_state_damages_{TARGET_YEAR}_{TAG}.png" if TAG
    else f"fredi_state_damages_{TARGET_YEAR}.png"
)
OUT_PDF_BASENAME = OUT_PNG_BASENAME.replace(".png", ".pdf")
OUT_DATA_BASENAME = OUT_PNG_BASENAME.replace(".png", "_data.csv")


def weighted_median(values, weights):
    mask = np.isfinite(values) & np.isfinite(weights) & (weights >= 0)
    v = np.asarray(values[mask], dtype=float)
    w = np.asarray(weights[mask], dtype=float)
    if len(v) == 0 or w.sum() == 0:
        return np.nan
    s = np.argsort(v)
    v, w = v[s], w[s]
    cw = np.cumsum(w)
    return float(v[np.searchsorted(cw, 0.5 * cw[-1])])


def main():
    # ------------------------------------------------------------------
    # Load state-level FrEDI output at target year
    # ------------------------------------------------------------------
    state_csv = OUT / STATE_LONG_BASENAME
    print(f"Loading {state_csv} ...")
    # Stream-read only year=TARGET_YEAR rows to keep memory bounded
    # (the file is 767 MB total but we only need ~50 states × 500 draws × 2 sectors).
    df = pd.read_csv(state_csv,
                     usecols=["sector", "variant", "state", "postal", "year",
                              "annual_impacts", "draw_idx", "w_norm"])
    df = df[df["year"] == TARGET_YEAR].copy()
    print(f"  filtered to year {TARGET_YEAR}: {len(df):,} rows")
    print(f"  sectors: {df['sector'].unique().tolist()}")
    print(f"  states with data: {df['state'].nunique()}")

    # Sum across the two sectors per (draw, state) so we get total SLR
    # damages per state per draw.
    totals = df.groupby(["state", "postal", "draw_idx", "w_norm"], as_index=False)[
        "annual_impacts"
    ].sum()
    print(f"  per-(state, draw) summed rows: {len(totals):,}")

    # ------------------------------------------------------------------
    # importance-weighted median per state
    # ------------------------------------------------------------------
    rows = []
    for (state, postal), g in totals.groupby(["state", "postal"]):
        v = g["annual_impacts"].to_numpy()
        w = g["w_norm"].to_numpy()
        rows.append({
            "state":   state,
            "postal":  postal,
            "median_USD":  weighted_median(v, w),
            "N_draws":     int(np.isfinite(v).sum()),
        })
    abs_df = pd.DataFrame(rows)
    print(f"  states with nonzero medians: "
          f"{int((abs_df['median_USD'] > 0).sum())} / {len(abs_df)}")

    # ------------------------------------------------------------------
    # Load state populations at year 2100
    # ------------------------------------------------------------------
    pop = pd.read_csv(POP_PATH)
    pop_2100 = pop[pop["year"] == TARGET_YEAR][["state", "postal", "state_pop"]]
    abs_df = abs_df.merge(pop_2100, on=["state", "postal"], how="left")
    abs_df["median_USD_per_capita"] = abs_df["median_USD"] / abs_df["state_pop"]

    # Drop zero-damage rows for cleaner visualization (mostly inland states
    # already removed by FrEDI's SLR sector definition; coastal-only).
    abs_df = abs_df.dropna(subset=["median_USD"])
    print("\n=== Top 12 states by absolute damages ===")
    print(abs_df.sort_values("median_USD", ascending=False)
                .head(12)[["postal", "state", "median_USD", "state_pop",
                           "median_USD_per_capita"]]
                .to_string(index=False))

    # Save the underlying data
    out_data = PLOTS / OUT_DATA_BASENAME
    abs_df.sort_values("median_USD", ascending=False).to_csv(out_data, index=False)
    print(f"\nWrote {out_data}")

    # ------------------------------------------------------------------
    # Build chloropleth maps (matplotlib + manually placed state boxes,
    # since we don't want to depend on cartopy/geopandas)
    # ------------------------------------------------------------------
    # Use US state outlines via matplotlib's built-in support: there isn't
    # one, so we'll use a simple square-grid alternative (each state as a
    # rectangle in a tile-map layout). Tile-map coordinates from Penn State
    # Climate Communicator (US-1) for a recognisable layout.

    # Tile-map layout: (col, row) for each state
    TILEMAP = {
        "AK": (0, 0), "ME": (10, 0),
        "VT": (9, 1), "NH": (10, 1),
        "WA": (1, 2), "ID": (2, 2), "MT": (3, 2), "ND": (4, 2),
        "MN": (5, 2), "IL": (6, 2), "WI": (6, 1), "MI": (7, 2),
        "NY": (8, 2), "RI": (10, 2), "MA": (9, 2),
        "OR": (1, 3), "UT": (2, 3), "WY": (3, 3), "SD": (4, 3),
        "IA": (5, 3), "IN": (6, 3), "OH": (7, 3), "PA": (8, 3),
        "NJ": (9, 3), "CT": (10, 3),
        "CA": (1, 4), "NV": (2, 4), "CO": (3, 4), "NE": (4, 4),
        "MO": (5, 4), "KY": (6, 4), "WV": (7, 4), "VA": (8, 4),
        "MD": (9, 4), "DE": (10, 4),
        "AZ": (2, 5), "NM": (3, 5), "KS": (4, 5),
        "AR": (5, 5), "TN": (6, 5), "NC": (7, 5), "SC": (8, 5),
        "DC": (9, 5),
        "HI": (0, 6), "OK": (4, 6), "LA": (5, 6),
        "MS": (6, 6), "AL": (7, 6), "GA": (8, 6),
        "TX": (3, 7), "FL": (9, 7),
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                             gridspec_kw={"wspace": 0.05})

    # Build state→value maps
    abs_map = abs_df.set_index("postal")["median_USD"].to_dict()
    cap_map = abs_df.set_index("postal")["median_USD_per_capita"].to_dict()

    # Color normalization: log scale for absolute (huge dynamic range),
    # linear or pseudo-log for per-capita
    abs_vmin = max(abs_df["median_USD"].min(), 1e6)   # floor at $1M
    abs_vmax = abs_df["median_USD"].max()
    cap_vmin = max(abs_df["median_USD_per_capita"].min(), 1.0)
    cap_vmax = abs_df["median_USD_per_capita"].max()

    abs_norm = mcolors.LogNorm(vmin=abs_vmin, vmax=abs_vmax)
    cap_norm = mcolors.LogNorm(vmin=cap_vmin, vmax=cap_vmax)
    cmap = plt.get_cmap("YlOrRd")

    def draw_tile_map(ax, value_map, norm, title, cbar_label, fmt):
        max_row = max(r for _, r in TILEMAP.values())
        for postal, (col, row) in TILEMAP.items():
            y = max_row - row   # flip Y so row 0 is top
            v = value_map.get(postal, np.nan)
            if np.isnan(v) or v <= 0:
                face = "#f0f0f0"
                edge = "#cccccc"
                txt_color = "#999999"
            else:
                face = cmap(norm(v))
                edge = "#666666"
                # contrast: light bg → black text, dark bg → white text
                rgb = mcolors.to_rgb(face)
                luminance = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
                txt_color = "black" if luminance > 0.5 else "white"
            rect = plt.Rectangle((col, y), 0.95, 0.95, facecolor=face,
                                 edgecolor=edge, linewidth=0.8)
            ax.add_patch(rect)
            ax.text(col + 0.475, y + 0.6, postal, ha="center", va="center",
                    fontsize=8, fontweight="bold", color=txt_color)
            if not np.isnan(v) and v > 0:
                ax.text(col + 0.475, y + 0.25, fmt(v), ha="center", va="center",
                        fontsize=6.5, color=txt_color)
        ax.set_xlim(-0.5, 12)
        ax.set_ylim(-0.5, max_row + 1.5)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(title, fontsize=12, fontweight="bold")
        # Add colorbar
        sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        sm.set_array([])
        cb = plt.colorbar(sm, ax=ax, orientation="horizontal",
                          pad=0.04, shrink=0.7)
        cb.set_label(cbar_label, fontsize=9)
        cb.ax.tick_params(labelsize=8)

    draw_tile_map(
        axes[0], abs_map, abs_norm,
        title=f"Absolute annual SLR damages, {TARGET_YEAR}",
        cbar_label="USD / year (log scale)",
        fmt=lambda v: f"${v/1e9:.1f}B" if v >= 1e9 else f"${v/1e6:.0f}M",
    )
    draw_tile_map(
        axes[1], cap_map, cap_norm,
        title=f"Per-capita annual SLR damages, {TARGET_YEAR}",
        cbar_label="USD / person / year (log scale)",
        fmt=lambda v: f"${v:,.0f}" if v >= 1 else f"${v:.2f}",
    )

    # Internal suptitle dropped per poster review (May 17): the poster's
    # panel-H label "H. Coastal Properties and HTF Transportation Damages
    # by State" serves as the title.

    out_png = PLOTS / OUT_PNG_BASENAME
    out_pdf = PLOTS / OUT_PDF_BASENAME
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"\nWrote {out_png}")
    print(f"Wrote {out_pdf}")


if __name__ == "__main__":
    main()
