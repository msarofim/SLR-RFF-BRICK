#!/usr/bin/env python3
"""
Air-quality mortality per-capita by state (FrEDI), as a tile-map panel that
complements the per-capita SLR-damages map (the right map of poster Panel I).

Left  panel : per-capita annual SLR damages, 2100  (replica of Panel I right map;
              USD/person/yr, YlOrRd + LogNorm) — read from the SLR poster data.
Right panel : per-capita air-quality MORTALITY, 2100 (deaths / 100,000 / yr),
              summing FrEDI's climate-driven AQ (Fann et al., ozone+PM2.5) +
              Wildfire + Southwest Dust. Diverging RdBu_r scale because the
              ozone response is a net *benefit* (negative) in several northern
              states.

Style matches plot_state_damages_2100.py (same TILEMAP, DejaVu Sans, tile
geometry, luminance-contrasted labels). Outputs both the combined 2-map figure
and the AQ panel alone.

Basis note: the SLR map is the RFF-SP baseline importance-weighted median; the
AQ map is FrEDI on the SSP2-4.5 temperature pathway (the readily available
state-level baseline). Both are "central" but not the same ensemble — see the
figure caption / README.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["font.family"] = "DejaVu Sans"
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

TARGET_YEAR = 2100
SLR_REPO = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
FTF_REPO = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI")
SLR_DATA = SLR_REPO / "outputs/plots/fredi_state_damages_2100_data.csv"
AQ_DATA  = FTF_REPO / "fredi_outputs/aq_mortality_per_state_2100_ssp245.csv"
OUT_DIR  = SLR_REPO / "outputs/plots"

# Tile-map layout (col, row) — identical to plot_state_damages_2100.py
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
MAX_ROW = max(r for _, r in TILEMAP.values())


def _txt_color(face):
    rgb = mcolors.to_rgb(face)
    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return "black" if lum > 0.5 else "white"


def draw_tile_map(ax, value_map, norm, cmap, title, cbar_label, fmt,
                  gray_nonpos=True, cbar_ticks=None, subtitle=None):
    """gray_nonpos=True grays NaN and v<=0 (sequential maps);
       False colors all finite values via the (diverging) norm."""
    for postal, (col, row) in TILEMAP.items():
        y = MAX_ROW - row
        v = value_map.get(postal, np.nan)
        missing = np.isnan(v) or (gray_nonpos and v <= 0)
        if missing:
            face, edge, txt = "#f0f0f0", "#cccccc", "#999999"
        else:
            face = cmap(norm(v))
            edge = "#666666"
            txt = _txt_color(face)
        ax.add_patch(plt.Rectangle((col, y), 0.95, 0.95, facecolor=face,
                                   edgecolor=edge, linewidth=0.8))
        ax.text(col + 0.475, y + 0.6, postal, ha="center", va="center",
                fontsize=8, fontweight="bold", color=txt)
        if not np.isnan(v) and not (gray_nonpos and v <= 0):
            ax.text(col + 0.475, y + 0.25, fmt(v), ha="center", va="center",
                    fontsize=6.5, color=txt)
    ax.set_xlim(-0.5, 12)
    ax.set_ylim(-0.5, MAX_ROW + 1.5)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=20)
    if subtitle:
        ax.text(0.5, 1.004, subtitle, transform=ax.transAxes, ha="center",
                va="bottom", fontsize=7.5, color="#555")
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cb = plt.colorbar(sm, ax=ax, orientation="horizontal", pad=0.04, shrink=0.7,
                      ticks=cbar_ticks)
    cb.set_label(cbar_label, fontsize=9)
    cb.ax.tick_params(labelsize=8)


def main():
    # ---- SLR per-capita (Panel I right map) ----
    slr = pd.read_csv(SLR_DATA)
    slr_map = slr.set_index("postal")["median_USD_per_capita"].to_dict()
    slr_vmin = max(slr["median_USD_per_capita"].min(), 1.0)
    slr_vmax = slr["median_USD_per_capita"].max()
    slr_norm = mcolors.LogNorm(vmin=slr_vmin, vmax=slr_vmax)
    slr_cmap = plt.get_cmap("YlOrRd")

    # ---- AQ mortality per capita (deaths / 100k / yr) ----
    aq = pd.read_csv(AQ_DATA)
    aq_map = aq.set_index("postal")["per100k"].to_dict()
    vmax = float(np.ceil(aq["per100k"].max()))
    vmin = float(np.floor(aq["per100k"].min()))
    lim = max(abs(vmin), abs(vmax))
    aq_norm = mcolors.TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=vmax)
    aq_cmap = plt.get_cmap("RdBu_r")  # red = more deaths, blue = AQ benefit
    aq_ticks = [t for t in (-2, 0, 2, 4, 6, 8) if -lim <= t <= vmax]

    natl = aq["deaths"].sum()
    aq_title = f"Air-quality mortality per capita, {TARGET_YEAR}"
    aq_cbar = "deaths / 100,000 / year  (red = excess, blue = benefit)"
    aq_sub = (f"Climate-driven AQ (Fann; O₃+PM₂.₅) + wildfire + dust  "
              f"·  SSP2-4.5  ·  {natl:,.0f} U.S. deaths/yr")
    aq_fmt = lambda v: f"{v:.1f}"

    # ===== combined 2-panel figure =====
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"wspace": 0.05})
    draw_tile_map(axes[0], slr_map, slr_norm, slr_cmap,
                  title=f"Per-capita annual SLR damages, {TARGET_YEAR}",
                  cbar_label="USD / person / year (log scale)",
                  fmt=lambda v: f"${v:,.0f}" if v >= 1 else f"${v:.2f}",
                  gray_nonpos=True)
    draw_tile_map(axes[1], aq_map, aq_norm, aq_cmap,
                  title=aq_title, cbar_label=aq_cbar, fmt=aq_fmt,
                  gray_nonpos=False, cbar_ticks=aq_ticks, subtitle=aq_sub)
    for f in ("aq_slr_state_panels_2100.png", "aq_slr_state_panels_2100.pdf"):
        fig.savefig(OUT_DIR / f, dpi=150, bbox_inches="tight")
    print("Wrote", OUT_DIR / "aq_slr_state_panels_2100.png")

    # ===== AQ panel alone =====
    fig2, ax2 = plt.subplots(1, 1, figsize=(7, 6))
    draw_tile_map(ax2, aq_map, aq_norm, aq_cmap,
                  title=aq_title, cbar_label=aq_cbar, fmt=aq_fmt,
                  gray_nonpos=False, cbar_ticks=aq_ticks, subtitle=aq_sub)
    for f in ("aq_mortality_state_2100.png", "aq_mortality_state_2100.pdf"):
        fig2.savefig(OUT_DIR / f, dpi=150, bbox_inches="tight")
    print("Wrote", OUT_DIR / "aq_mortality_state_2100.png")


if __name__ == "__main__":
    main()
