"""
run_4way_slr_decomp.py
======================

Compute and plot the 4-way SLR H-S decomposition (emissions, climate-cfg,
internal-variability, BRICK-posterior) from the ANOVA factorial BRICK runs,
plus an OFAT cross-check.

Inputs:
  outputs/brick_anova_long.csv  -- 13,500 rows from run_mimibrick_paired_explicit.jl
                                   over the ANOVA metadata (100 rffs × 15 cfgs
                                   × 3 seeds × 3 posts), with full year-by-year
                                   SLR columns 1850..2100.
  outputs/brick_ofat_long.csv   -- 761 rows from the same driver over OFAT
                                   metadata; used for axis-by-axis cross-check.

Outputs:
  outputs/plots/hawkins_sutton_slr_4way.{png,pdf,csv}
  outputs/plots/hawkins_sutton_slr_4way_ofat_compare.csv
  outputs/plots/hawkins_sutton_slr_4way_ofat_compare.png

Usage:
  python python/scripts/run_4way_slr_decomp.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Import from sibling hawkins_sutton.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hawkins_sutton import (
    decompose_slr_4way,
    ofat_variance,
    plot_hs_stack,
)

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs"
PLOTS = OUT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

T_ANCHOR = 2020
# Decomp computed to 2300 but plotted only to 2150 (per Marcus, May 2026):
# FrEDI damage saturation kicks in past ~2150 in some scenarios; SLR uncertainty
# bands also get very wide. Keep the headline plot at 2150 for clarity; the
# 2151-2300 values remain in the underlying CSV for SC-GHG NPV use.
DECOMP_YEARS_FULL = list(range(2020, 2301))
PLOT_END_YEAR = 2150


def main():
    # ------------------------------------------------------------------
    # ANOVA 4-way decomp — prefer the Wong-weighted 1850-2300 CSV if it
    # exists; fall back to the unweighted Phase A 2100 CSV otherwise.
    # ------------------------------------------------------------------
    # v1.4.5 slim ANOVA-18k (54,000 paired rows). Legacy v1.4.1 CSVs are
    # quarantined under outputs/quarantine/20260524_pre_v145_e2e/.
    weighted_csv = OUT / "brick_v145_slim" / "brick_anova18k_baseline_to2300_weighted.csv"
    unweighted_2300_csv = OUT / "brick_anova_long_2300.csv"
    unweighted_2100_csv = OUT / "brick_anova_long.csv"

    if weighted_csv.exists():
        anova_csv = weighted_csv
        weights_col = "w_norm"
        decomp_years = DECOMP_YEARS_FULL
        run_label = "Wong-weighted, 1850-2300"
    elif unweighted_2300_csv.exists():
        anova_csv = unweighted_2300_csv
        weights_col = None
        decomp_years = DECOMP_YEARS_FULL
        run_label = "Unweighted, 1850-2300"
    elif unweighted_2100_csv.exists():
        anova_csv = unweighted_2100_csv
        weights_col = None
        decomp_years = list(range(2020, 2101))
        run_label = "Unweighted, 1850-2100 (Phase A)"
    else:
        sys.exit("No ANOVA CSV found in outputs/.")

    print(f"Loading {anova_csv}  ({run_label}) ...")
    df = pd.read_csv(anova_csv)
    print(f"  rows: {len(df):,}")
    print(f"  unique rffs: {df['rff_idx'].nunique()}")
    print(f"  unique cfgs: {df['fair_cfg_idx'].nunique()}")
    print(f"  unique seeds: {df['seed_idx'].nunique()}")
    print(f"  unique posts: {df['post_idx'].nunique()}")
    print(f"  weights_col: {weights_col}")
    cell_counts = df.groupby(["rff_idx", "fair_cfg_idx", "seed_idx"]).size()
    print(f"  posts per (rff,cfg,seed) cell: min={cell_counts.min()} "
          f"max={cell_counts.max()} (balanced if min==max)")

    print(f"\nComputing 4-way decomp at {len(decomp_years)} years (anchor={T_ANCHOR})...")
    decomp = decompose_slr_4way(df, decomp_years, t_anchor=T_ANCHOR,
                                weights_col=weights_col)

    # Attach EMPIRICAL importance-weighted P5/P50/P95 of ΔSLR(year) − SLR(anchor)
    # per year so plot_hs_stack's inset uses real percentiles instead of the
    # mean ± 1.96σ Gaussian fallback. The total-SLR anchored distribution is
    # close to symmetric so the Gaussian was a decent approximation, but
    # empirical percentiles are correct and audit-friendly (poster review
    # May 18 — "use real data when you have it").
    anchor_col = str(int(T_ANCHOR))
    w_arr = (df[weights_col].to_numpy() if weights_col is not None
             else np.ones(len(df)))
    anchor_vec = df[anchor_col].to_numpy() if anchor_col in df.columns else None
    p5, p50, p95 = [], [], []
    for y in decomp["year"]:
        col = str(int(y))
        if col not in df.columns or anchor_vec is None:
            p5.append(np.nan); p50.append(np.nan); p95.append(np.nan); continue
        v = df[col].to_numpy() - anchor_vec
        order = np.argsort(v); vs, ws = v[order], w_arr[order]
        cw = np.cumsum(ws); total = cw[-1] if cw[-1] > 0 else 1.0
        p5.append(float(vs[np.searchsorted(cw, 0.05 * total)]))
        p50.append(float(vs[np.searchsorted(cw, 0.50 * total)]))
        p95.append(float(vs[np.searchsorted(cw, 0.95 * total)]))
    decomp["p5"] = p5; decomp["p50"] = p50; decomp["p95"] = p95

    out_csv = PLOTS / "hawkins_sutton_slr_4way.csv"
    decomp.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  ({len(decomp)} years, full range)")
    print("\nPreview at key years:")
    for y in (2025, 2050, 2075, 2100, 2150, 2200, 2300):
        m = decomp[decomp["year"] == y]
        if not len(m):
            continue
        r = m.iloc[0]
        print(f"  {y}: V_tot={r['V_total']:.3f}  "
              f"V_emi={r['V_emissions']:.3f}  V_clim={r['V_climate']:.3f}  "
              f"V_int={r['V_internal']:.3f}  V_brick={r['V_brick']:.3f}  "
              f"f_emi={r['f_emissions']:.2f}  f_clim={r['f_climate']:.2f}  "
              f"f_int={r['f_internal']:.2f}  f_brick={r['f_brick']:.2f}  "
              f"mean={r['mean']:.2f}")

    # Truncate the PLOT window to 2150 per project standard; full data
    # remains in the CSV for SC-GHG NPV (2300-horizon) use.
    decomp_plot = decomp[decomp["year"] <= PLOT_END_YEAR].reset_index(drop=True)

    caveat = (
        "V_internal is FaIR's stochastic GMST/OHC variability transmitted "
        "through MimiBRICK's deterministic ice-sheet and steric modules. "
        "Intrinsic SLR variability (AIS calving, GIS surface-mass-balance noise, "
        "ocean dynamic SL, land water storage) is not represented in MimiBRICK "
        "and would add additional internal variance not captured here."
    )

    # Short title; detailed Hawkins-Sutton / ANOVA factorial info belongs in
    # the poster figure caption (poster convention May 17).
    plot_hs_stack(
        decomp_plot,
        components=["emissions", "climate", "internal", "brick"],
        colors=["#d95f02", "#7570b3", "#1b9e77", "#e7298a"],
        labels=["Emissions (RFF-SP)", "Climate config (FaIR v2.2.4)",
                "Internal variability (FaIR seed)", "BRICK posterior"],
        title="",  # internal title dropped (May 18); duplicates poster panel-C label
        out_png=PLOTS / "hawkins_sutton_slr_4way.png",
        out_pdf=PLOTS / "hawkins_sutton_slr_4way.pdf",
        y_total_label="Var(GMSL) [cm²]",
        inset_units="cm",
    )

    # Append the intrinsic-noise caveat to the figure file as a sidecar text
    # so it travels with the plot. (Matplotlib's title can't hold all of it.)
    caveat_path = PLOTS / "hawkins_sutton_slr_4way_caveat.txt"
    caveat_path.write_text(caveat + "\n")
    print(f"  wrote caveat sidecar: {caveat_path}")

    # ------------------------------------------------------------------
    # OFAT cross-check
    # ------------------------------------------------------------------
    ofat_csv = OUT / "brick_ofat_long.csv"
    if not ofat_csv.exists():
        print(f"  [warn] OFAT CSV not found: {ofat_csv}; skipping cross-check")
        return

    print(f"\nLoading {ofat_csv} ...")
    ofat = pd.read_csv(ofat_csv)
    print(f"  rows: {len(ofat):,}")
    print(f"  axes: {sorted(ofat['axis'].unique())}")

    # OFAT data is from Phase A (1850-2100); clamp the OFAT year range to
    # what's actually in the OFAT CSV so we don't KeyError on years > 2100.
    ofat_year_cols = [int(c) for c in ofat.columns if c.isdigit()]
    ofat_year_max = max(ofat_year_cols) if ofat_year_cols else 2100
    ofat_years = [y for y in decomp_years if y <= ofat_year_max]
    print(f"  OFAT compare year range: {min(ofat_years)}-{max(ofat_years)} "
          f"(clamped to OFAT CSV max year {ofat_year_max})")
    ofat_var = ofat_variance(ofat, ofat_years, t_anchor=T_ANCHOR)
    out_csv = PLOTS / "hawkins_sutton_slr_4way_ofat_compare.csv"

    # Pivot OFAT to wide form so we can plot all 4 axes vs ANOVA on one figure
    ofat_wide = ofat_var.pivot(index="year", columns="axis", values="V_local").reset_index()
    # Merge with ANOVA decomp
    comp = decomp[["year", "V_emissions", "V_climate", "V_internal", "V_brick"]].copy()
    axis_to_anova = {
        "vary_rff":  "V_emissions",
        "vary_cfg":  "V_climate",
        "vary_seed": "V_internal",
        "vary_post": "V_brick",
    }
    merged = ofat_wide.merge(comp, on="year", how="inner")
    merged.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}")

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    titles = {
        "vary_rff":  ("V_emissions",  "Emissions (vary RFF)"),
        "vary_cfg":  ("V_climate",   "Climate cfg (vary FaIR cfg)"),
        "vary_seed": ("V_internal",  "Internal (vary seed; N=10 only)"),
        "vary_post": ("V_brick",     "BRICK posterior (vary post)"),
    }
    for ax, (axis, (anova_col, lbl)) in zip(axes.flat, titles.items()):
        if axis not in merged.columns:
            ax.set_title(f"{lbl} (no OFAT data)")
            continue
        ax.plot(merged["year"], merged[anova_col], color="#1b9e77",
                linewidth=1.5, label="ANOVA (global)")
        ax.plot(merged["year"], merged[axis], color="#d95f02",
                linewidth=1.5, linestyle="--", label="OFAT (local)")
        ax.set_title(lbl, fontsize=11)
        ax.set_ylabel("variance [cm²]", fontsize=9)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("Year")
    fig.suptitle("ANOVA vs OFAT: variance contribution per axis (centroid: "
                 "rff=1000, cfg=420, seed=0, post=5000)", fontsize=11, y=1.00)
    fig.tight_layout()
    out_png = PLOTS / "hawkins_sutton_slr_4way_ofat_compare.png"
    out_pdf = PLOTS / "hawkins_sutton_slr_4way_ofat_compare.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out_png}")
    print(f"  wrote {out_pdf}")


if __name__ == "__main__":
    main()
