"""
hawkins_sutton_panels.py
========================

Poster-styled hybrid Hawkins-Sutton panels for the AGU Chapman SLR poster.
Replaces the older nested-ANOVA panels C_total_slr_hawkins_sutton.pdf and
D_pulse_slr.pdf in iec_graphics_handoff/.

Reads the unified hybrid decomposition CSVs (built by
python/scripts/substack/hybrid_hs_slr_unified.py):
  outputs/substack/v5_hybrid_decomp_{total,pulse}_{unclip,clip}.csv

Emits to:
  outputs/poster/C_total_slr_hawkins_sutton.{png,pdf}
  outputs/poster/D_pulse_slr.{png,pdf}
And replaces in-place into iec_graphics_handoff/panels/.

Poster panel area for C: 15" × 7.5"; for D: 15" × 8". The figure itself is
sized smaller (the panel area holds figure + label + caption); poster fonts
need to be large enough to read at print scale.
"""
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
SUBSTACK = ROOT / "outputs" / "substack"
POSTER   = ROOT / "outputs" / "poster"
HANDOFF  = POSTER / "iec_graphics_handoff" / "panels"

# display-only temporal smoothing of per-year Sobol jitter (raw CSVs unchanged)
SMOOTH_WIN = 11


def _smooth(a, win=SMOOTH_WIN):
    a = np.asarray(a, float)
    if win <= 1 or a.size < win:
        return a
    pad = win // 2
    ap = np.pad(a, (pad, pad), mode="edge")
    return np.convolve(ap, np.ones(win) / win, mode="valid")[:a.size]

# Poster aesthetic
TITLE_COLOR = "#1F4E79"
AX_LABEL_FS = 12
TICK_FS     = 11
TITLE_FS    = 14
LEGEND_FS   = 10

# Same 6-axis decomposition as substack render
LABELS = {
    "internal":     "Internal variability (FaIR seeds)",
    "brick":        "BRICK posterior (BRICK configs)",
    "climate":      "Climate response (FaIR configs)",
    "emissions":    "Emissions (RFF-SP)",
    "tipping":      "AIS tipping nonlinearity",
    "interactions": "Interactions (climate × BRICK, emissions × BRICK)",
}
COLORS = {
    "emissions":    "#d95f02",
    "climate":      "#7570b3",
    "brick":        "#e7298a",
    "internal":     "#1b9e77",
    "tipping":      "#b15928",
    "interactions": "#999999",
}
ORDER = ["internal", "brick", "climate", "emissions", "tipping", "interactions"]


def build_panel(target_name, title_text, figsize, out_stem, handoff_stem,
                x_start=None):
    """Same decomposition framework as the substack render: clipped axes +
    tipping wedge = V_total_unclipped on a single denominator.

    x_start: if given, the displayed x-axis starts here (e.g. 2030 for the
    pulse panel — variance shares of the pulse-marginal response are not
    meaningful before the pulse year)."""
    unc = pd.read_csv(SUBSTACK / f"v5_hybrid_decomp_{target_name}_unclip.csv")
    clp = pd.read_csv(SUBSTACK / f"v5_hybrid_decomp_{target_name}_clip.csv")
    years = unc.year.values

    v_emi   = clp.V_emissions.values
    v_clim  = clp.V_climate.values
    v_brick = clp.V_brick.values
    v_seed  = clp.V_seed.values
    v_resid_clp = clp.V_residual.values
    v_total_unc = unc.V_total.values
    v_total_clp = clp.V_total.values

    v_tipping = np.maximum(v_total_unc - v_total_clp, 0.0)
    v_interactions = v_resid_clp

    parts = dict(internal=v_seed, brick=v_brick, climate=v_clim, emissions=v_emi,
                  tipping=v_tipping, interactions=v_interactions)
    parts = {k: _smooth(v) for k, v in parts.items()}   # display smoothing
    denom = sum(parts.values())
    fracs = {k: np.nan_to_num(parts[k] / denom, nan=0.0) for k in parts}

    fig, ax = plt.subplots(figsize=figsize)
    ax.stackplot(years, *[fracs[c] for c in ORDER],
                  labels=[LABELS[c] for c in ORDER],
                  colors=[COLORS[c] for c in ORDER],
                  alpha=0.88, edgecolor="white", linewidth=0.4)
    ax.set_xlim(x_start if x_start is not None else years.min(), years.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=AX_LABEL_FS)
    ax.set_ylabel("Fraction of variance", fontsize=AX_LABEL_FS)
    ax.tick_params(labelsize=TICK_FS)
    # No in-figure title: the poster panel label (C / D′) already names the
    # chart, so an axes title would be redundant. (title_text kept for the
    # console landmark print + any standalone use.)
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=LEGEND_FS,
              framealpha=0.92, handlelength=1.4, borderpad=0.4)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    png = POSTER / f"{out_stem}.png"
    pdf = POSTER / f"{out_stem}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png}")
    print(f"wrote {pdf}")

    if HANDOFF.exists():
        dest = HANDOFF / f"{handoff_stem}.pdf"
        shutil.copyfile(pdf, dest)
        print(f"copied → {dest}")

    # Headline numbers for the captioning
    print(f"  fractions at landmarks ({target_name}):")
    for y in [2025, 2050, 2100, 2150]:
        if y not in years: continue
        i = int(np.where(years == y)[0][0])
        parts_str = " ".join([f"{c}={fracs[c][i]:.2f}" for c in ORDER])
        print(f"    {y}: {parts_str}")


if __name__ == "__main__":
    # Panel C — Total SLR
    build_panel(
        "total",
        "Total ΔSLR — sources of uncertainty (relative to 2020)",
        figsize=(9.5, 5.5),
        out_stem="C_total_slr_hawkins_sutton",
        handoff_stem="C_total_slr_hawkins_sutton",
    )
    # Panel D — Pulse SLR
    build_panel(
        "pulse",
        "Pulse-marginal ΔSLR per GtCO₂ — sources of uncertainty",
        figsize=(9.5, 5.5),
        out_stem="D_pulse_slr_hawkins_sutton",
        handoff_stem="D_pulse_slr",
        x_start=2030,   # pulse year — shares before the pulse are meaningless
    )
