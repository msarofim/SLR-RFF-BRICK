"""
paired_figures_hs.py
====================

Three paired Substack figures, each combining a projection band on top
with the corresponding H-S variance decomposition on bottom:

  1. paired_gmst.{png,pdf}  — Total GMST anomaly band (2020-2150) + H-S
  2. paired_slr.{png,pdf}   — Total SLR anomaly band + H-S (hybrid + tipping)
  3. paired_pulse.{png,pdf} — 2×2: pulse GMST + pulse SLR responses (top row),
                              H-S pulse GMST + H-S pulse SLR (bottom row).

All anchored at 2020. Bands are importance-weighted percentiles across the v5
LHS-10k_s ensemble. H-S decompositions are the v5/hybrid versions.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "substack"
FAI = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"

CUBE_BASE   = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10ks_baseline_flat2015.npz"
SLIM_BASE   = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv"

PLOT_START, PLOT_END = 2020, 2150
ANCHOR = 2020

# === Axis colors (match the H-S panels) ===
AXIS_COLOR = {
    "emissions": "#d95f02",
    "climate":   "#7570b3",
    "brick":     "#e7298a",
    "internal":  "#1b9e77",
    "tipping":   "#b15928",
    "interactions": "#999999",
}
AXIS_LABEL = {
    "emissions":    "Emissions (RFF-SP)",
    "climate":      "Climate response (FaIR configs)",
    "brick":        "BRICK posterior (BRICK configs)",
    "internal":     "Internal variability (FaIR seeds)",
    "tipping":      "AIS tipping nonlinearity",
    "interactions": "Interactions (climate × BRICK, emissions × BRICK)",
}


def weighted_quantile(values, q, w):
    """Lower-tail weighted quantile across the 0th axis."""
    order = np.argsort(values, axis=0)
    out_shape = (len(q),) + values.shape[1:]
    out = np.zeros(out_shape)
    for it in range(values.shape[1]):
        idx = order[:, it]
        v = values[idx, it]
        wo = w[idx]
        cum = np.cumsum(wo) / wo.sum()
        out[:, it] = np.interp(q, cum, v)
    return out


# ============================================================================
# Helper: load v5 GMST trajectories + importance weights
# ============================================================================
def load_v5_gmst():
    print("[gmst] loading v5 cube ...")
    c = np.load(CUBE_BASE, allow_pickle=True)
    cm = np.asarray(c["cells_meta"], dtype=np.int64)
    yrs = np.asarray(c["years"], dtype=np.int64)
    gmst = np.asarray(c["gmst_traj"], dtype=np.float64)
    i_lo = int(np.where(yrs == PLOT_START)[0][0])
    i_hi = int(np.where(yrs == PLOT_END)[0][0])
    g = gmst[:, i_lo:i_hi+1]
    plot_years = yrs[i_lo:i_hi+1]
    i_anchor = int(np.where(plot_years == ANCHOR)[0][0])
    g_anom = g - g[:, [i_anchor]]
    # Pull importance weights from the slim baseline, joined on (rff, cfg, seed)
    slim = pd.read_csv(SLIM_BASE, usecols=["rff_idx","fair_cfg_idx","seed_idx","w_norm"])
    cube_keys = pd.DataFrame(cm[:, :3], columns=["rff_idx","fair_cfg_idx","seed_idx"])
    cube_keys["_cube_row"] = np.arange(len(cube_keys))
    merged = slim.merge(cube_keys, on=["rff_idx","fair_cfg_idx","seed_idx"], how="left")
    assert merged._cube_row.notna().all()
    perm = merged._cube_row.to_numpy(dtype=int)
    g_anom = g_anom[perm]
    w = merged.w_norm.to_numpy()
    return plot_years, g_anom, w


def load_v5_slr():
    print("[slr] loading v5 slim baseline ...")
    yrs = np.arange(PLOT_START, PLOT_END + 1)
    cols = [str(y) for y in yrs]
    df = pd.read_csv(SLIM_BASE, usecols=["rff_idx","fair_cfg_idx","seed_idx","w_norm"] + cols)
    df = df.sort_values(["rff_idx","fair_cfg_idx","seed_idx"]).reset_index(drop=True)
    s = df[cols].to_numpy()
    s_anom = s - s[:, [int(np.where(yrs == ANCHOR)[0][0])]]
    return yrs, s_anom, df.w_norm.to_numpy()


def projection_band_panel(ax, years, traj, w, ylabel, title):
    """median + 5-95% band + ensemble mean."""
    qs = weighted_quantile(traj, np.array([0.05, 0.5, 0.95]), w)
    p5, p50, p95 = qs[0], qs[1], qs[2]
    mean = (traj * w[:, None]).sum(axis=0) / w.sum()
    ax.fill_between(years, p5, p95, color="#e0e0e0", alpha=0.9,
                    label="5–95% (importance weighted)")
    ax.plot(years, p50, color="#1F4E79", linewidth=2.4, label="Median")
    ax.plot(years, mean, color="black", linewidth=1.2, linestyle="--",
            label="Ensemble mean")
    ax.set_xlim(years.min(), years.max())
    ax.set_xlabel("")  # shared x with bottom panel
    ax.set_ylabel(ylabel, fontsize=10.5)
    ax.set_title(title, fontsize=12, fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.5)


def hs_stack_panel(ax, frac_df, ax_order, ylabel, label_override=None):
    labels = dict(AXIS_LABEL)
    if label_override:
        labels.update(label_override)
    years = frac_df.year.values
    ax.stackplot(years, *[frac_df[c].to_numpy() for c in ax_order],
                  labels=[labels[c] for c in ax_order],
                  colors=[AXIS_COLOR[c] for c in ax_order],
                  alpha=0.88, edgecolor="white", linewidth=0.4)
    ax.set_xlim(years.min(), years.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=10.5)
    ax.set_ylabel(ylabel, fontsize=10.5)
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.0,
              framealpha=0.92, handlelength=1.4, borderpad=0.4)
    ax.grid(True, axis="y", alpha=0.3)


# ============================================================================
# Figure 1 — Paired GMST
# ============================================================================
def build_paired_gmst():
    years, g_anom, w = load_v5_gmst()
    fig, (ax_t, ax_b) = plt.subplots(2, 1, figsize=(10, 9), sharex=True,
                                       gridspec_kw={"height_ratios": [3, 3]})
    projection_band_panel(
        ax_t, years, g_anom, w,
        ylabel="ΔGMST (°C, rel. 2020)",
        title="Total GMST anomaly — v5 LHS-10k_s ensemble",
    )
    hs = pd.read_csv(OUT / "shapley_hs_per_axis_total_gmst.csv")
    hs_stack_panel(ax_b, hs, ["internal", "climate", "emissions", "interactions"],
                    ylabel="Fraction of ΔGMST variance",
                    label_override={"interactions": "Interactions (emissions × climate)"})
    ax_b.set_title("Hawkins-Sutton decomposition — total GMST",
                    fontsize=11.5, fontweight="bold", color="#1F4E79")
    fig.tight_layout()
    out = OUT / "paired_gmst"
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}.{{png,pdf}}")


# ============================================================================
# Figure 2 — Paired SLR
# ============================================================================
def build_paired_slr():
    years, s_anom, w = load_v5_slr()
    fig, (ax_t, ax_b) = plt.subplots(2, 1, figsize=(10, 9), sharex=True,
                                       gridspec_kw={"height_ratios": [3, 3]})
    projection_band_panel(
        ax_t, years, s_anom, w,
        ylabel="ΔSLR (cm, rel. 2020)",
        title="Total SLR — v5 LHS-10k_s ensemble",
    )
    hs = pd.read_csv(OUT / "shapley_hs_per_axis_total_slr_hybrid_tipping.csv")
    # Show internal at bottom, residual/tipping on top
    hs_stack_panel(ax_b, hs,
                    ["internal", "brick", "climate", "emissions",
                     "tipping", "interactions"],
                    ylabel="Fraction of ΔSLR variance")
    ax_b.set_title("Hawkins-Sutton decomposition — total SLR (hybrid + tipping split)",
                    fontsize=11.5, fontweight="bold", color="#1F4E79")
    fig.tight_layout()
    out = OUT / "paired_slr"
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}.{{png,pdf}}")


# ============================================================================
# Figure 3 — Paired pulse (2 × 2)
# ============================================================================
def render_pulse_response(ax, csv_path, ylabel, title, show_mean=True):
    """show_mean=False for pulse SLR: the ensemble mean is dominated by a tiny
    number of pulse-induced AIS-tipped runs and would regress toward the median
    as the pulse → 0, so it is not a robust per-tonne quantity. The median (and
    the 5–95% band) are pulse-size-invariant and SC-GHG-relevant."""
    df = pd.read_csv(csv_path)
    df = df[(df.year >= PLOT_START) & (df.year <= PLOT_END)]
    yp = df.year.to_numpy()
    ax.fill_between(yp, df.p5, df.p95, color="#e0e0e0", alpha=0.9,
                    label="5–95% (importance weighted)")
    ax.plot(yp, df.p50, color="#1F4E79", linewidth=2.4, label="Median")
    if show_mean and "mean" in df.columns:
        ax.plot(yp, df["mean"], color="black", linewidth=1.2, linestyle="--",
                label="Ensemble mean")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_ylabel(ylabel, fontsize=10.5)
    ax.set_title(title, fontsize=11.5, fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.5)


def build_paired_pulse():
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.5), sharex=True,
                              gridspec_kw={"hspace": 0.28, "wspace": 0.22})

    # Top-left: CO2 pulse GMST response
    render_pulse_response(
        axes[0, 0], OUT / "co2_pulse_gmst_summary_v145.csv",
        ylabel="ΔGMST (°C per GtCO₂)",
        title="Pulse GMST response — 1 GtCO₂ pulse at 2030",
    )
    # Top-right: CO2 pulse SLR response (linear-regime 0.01 GtCO2).
    # No ensemble mean — the mean is tipping-corrupted (a few AIS-tipped runs)
    # and not pulse-size-invariant; median is the robust per-tonne quantity.
    render_pulse_response(
        axes[0, 1], OUT / "co2_pulse_slr_summary_lhs10k_0p01gtc.csv",
        ylabel="ΔSLR (cm per GtCO₂)",
        title="Pulse SLR response — 0.01 GtCO₂ (linear regime)",
        show_mean=False,
    )

    # Bottom-left: H-S pulse GMST (matched-seed; 100% climate, no internal)
    hs_pg = pd.read_csv(OUT / "shapley_hs_per_axis_pulse_gmst.csv")
    hs_stack_panel(axes[1, 0], hs_pg, ["climate", "emissions", "interactions"],
                    label_override={"interactions": "Interactions (emissions × climate)"},
                    ylabel="Fraction of ΔGMST_pulse variance")
    axes[1, 0].set_title("Hawkins-Sutton decomposition — pulse GMST",
                          fontsize=11.5, fontweight="bold", color="#1F4E79")
    # Bottom-right: H-S pulse SLR hybrid + tipping
    hs_ps = pd.read_csv(OUT / "shapley_hs_per_axis_pulse_slr_hybrid_tipping.csv")
    hs_stack_panel(axes[1, 1], hs_ps,
                    ["internal", "brick", "climate", "emissions",
                     "tipping", "interactions"],
                    ylabel="Fraction of ΔSLR_pulse variance")
    axes[1, 1].set_title("Hawkins-Sutton decomposition — pulse SLR (hybrid + tipping split)",
                          fontsize=11.5, fontweight="bold", color="#1F4E79")

    fig.tight_layout()
    out = OUT / "paired_pulse"
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}.{{png,pdf}}")


if __name__ == "__main__":
    build_paired_gmst()
    build_paired_slr()
    build_paired_pulse()
