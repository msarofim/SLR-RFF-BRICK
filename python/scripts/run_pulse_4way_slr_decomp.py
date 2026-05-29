"""
run_pulse_4way_slr_decomp.py
============================

Compute and plot the 4-way Hawkins-Sutton decomposition of the **marginal
SLR response** to a 1 GtCO₂ pulse at 2030 — i.e. the "where does the
mitigation BENEFIT uncertainty come from?" complement to the total-SLR
decomp in run_4way_slr_decomp.py.

Marginal ΔSLR(t) = SLR_pulse(t) − SLR_baseline(t) per (rff, cfg, seed, post)
tuple from the same ANOVA factorial. Stochastic noise cancels in the diff
(paired Wong design). Wong importance weights inherit from the baseline
draw's trajectory.

Inputs:
  outputs/brick_anova_long_2300_weighted.csv     -- baseline + w_norm
  outputs/brick_anova_pulse_long_2300.csv        -- pulse, unweighted

Outputs:
  outputs/brick_anova_marginal_long_2300_weighted.csv  -- per-tuple marginal SLR
  outputs/plots/hawkins_sutton_slr_4way_pulse.csv
  outputs/plots/hawkins_sutton_slr_4way_pulse.png/.pdf

Usage:
  python python/scripts/run_pulse_4way_slr_decomp.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hawkins_sutton import decompose_slr_4way, plot_hs_stack


def _plot_pulse_composite(decomp_plot, marg, out_png, out_pdf):
    """Composite Panel D figure for the pulse-SLR decomp.

    Main:   Hawkins-Sutton stacked variance fractions (4 components) over time.
    Inset:  Median (line) and 5-95% band of the per-unit pulse-marginal SLR
            from the 0.01-GtC small-pulse arm — the SC-GHG-relevant
            linear-regime response. Pulse-size invariant per the 1 / 0.1 /
            0.01 GtC convergence diagnostic (see pulse_convergence.py).

    The earlier marginal-outcome AIS-tipping-regime inset (mean over all
    tuples vs mean over non-tipped) was retired 2026-05-26 because its
    classifier (per-year marginal > 0.3 cm) was pulse-size sensitive,
    introducing discontinuities in cross-pulse-size comparisons. The
    project standard L-T classifier is now baseline `ais_2100_cm > 20 cm`
    (see extract_lhs10k_smallpulse_summary.py + gaussian_vs_empirical_slr.py
    + lemoine_traeger_decomposition.py).
    """
    yrs = decomp_plot["year"].to_numpy()
    components = ["emissions", "climate", "internal", "brick"]
    colors = ["#d95f02", "#7570b3", "#1b9e77", "#e7298a"]
    labels = ["Emissions (RFF-SP background)",
              "Climate config (FaIR v2.2.4)",
              "Tipping-point state dependence (FaIR seed)",
              "BRICK posterior (AIS/GIS/TE sensitivity)"]
    fracs = [decomp_plot[f"f_{c}"].to_numpy() for c in components]

    fig, ax = plt.subplots(figsize=(9.0, 6.0))
    ax.stackplot(yrs, *fracs, labels=labels, colors=colors, alpha=0.85,
                 edgecolor="white", linewidth=0.4)
    ax.set_xlim(yrs.min(), yrs.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year")
    ax.set_ylabel("Fraction of total variance")
    # Internal title dropped per poster review (May 18): duplicates the
    # poster's panel-D label "D. PULSE SLR — sources of uncertainty …".
    # Reverse legend so order matches visual top→bottom stack order:
    # BRICK (top), Tipping-point state dep., Climate cfg, Emissions (bottom).
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="lower right",
              framealpha=0.92, fontsize=8.5)
    ax.grid(True, axis="y", alpha=0.3)

    # ===== Inset: median + 5–95% pulse SLR response (small-pulse linear regime) =====
    # Replaces the earlier marginal-magnitude tipping split, which was pulse-size
    # sensitive.  Median and 5-95% from the 0.01-GtC companion pulse run are
    # pulse-size invariant (verified via the 1 / 0.1 / 0.01 GtC convergence
    # diagnostic in pulse_convergence.py), so this inset shows the SC-GHG-
    # relevant LINEAR per-unit SLR response.  Values rescaled per-GtC ÷ 3.664
    # to display on a per-GtCO2 (CO2 mass) basis, matching the rest of the
    # poster's "1 GtCO2 pulse" framing.
    #
    # Sourced from the LHS-10k conditional-BRICK ensemble (10,000 paired
    # baseline + 0.01 GtC small-pulse triplets, Wong-importance-weighted).
    # Replaces the earlier 500-cell paired summary; percentiles agree to
    # within ~1-2 cm but the 10k LHS gives much tighter sampling noise.
    #
    # UNITS: The v1.4.5 LHS-10k small-pulse summary CSV is in cm per GtCO₂
    # already — FaIR v1.4.5 'CO2 FFI' input_unit is GtCO2, not GtC (see
    # `~/.claude/skills/climate-modeling` GtC-vs-GtCO2 note + memory entry
    # `project_fair_v145_co2ffi_is_gtco2.md`). The legacy v1.4.1-era
    # pre-2026-05-25 code path divided by 44/12 ≈ 3.667 to "convert"; that
    # produces values 3.67× too small under v1.4.5 and has been removed.
    ax2 = ax.inset_axes([0.12, 0.56, 0.45, 0.40])   # shifted right from 0.06
                                                     # to clear parent y-label
    SMALLPULSE_SUMMARY = ROOT / "outputs" / "substack" / "co2_pulse_slr_summary_lhs10k_0p01gtc.csv"
    if SMALLPULSE_SUMMARY.exists():
        sdf = pd.read_csv(SMALLPULSE_SUMMARY)
        sdf = sdf[(sdf.year >= yrs.min()) & (sdf.year <= yrs.max())]
        sy = sdf.year.to_numpy()
        ax2.fill_between(sy, sdf.p5, sdf.p95,
                         color="#1F4E79", alpha=0.20, label="5–95% band")
        ax2.plot(sy, sdf.p50, color="#1F4E79", linewidth=1.8,
                 label="Median")
        ax2.set_xlim(sy.min(), sy.max())
        ymax = float(sdf.p95.max()) * 1.10
    else:
        ax2.text(0.5, 0.5, f"missing {SMALLPULSE_SUMMARY.name}",
                 ha="center", va="center", transform=ax2.transAxes,
                 fontsize=7, color="#888")
        ymax = 0.05
    ax2.set_facecolor("white")
    ax2.patch.set_alpha(0.92)
    ax2.set_ylim(0, ymax)
    ax2.tick_params(labelsize=7)
    ax2.set_ylabel("ΔSLR (cm per GtCO₂)", fontsize=7)
    ax2.grid(alpha=0.3, linewidth=0.4)
    ax2.legend(loc="upper left", fontsize=6.5, framealpha=0.9, handlelength=1.6)

    fig.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out_png}")
    print(f"  wrote {out_pdf}")

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs"
PLOTS = OUT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

T_ANCHOR = 2020
DECOMP_YEARS = list(range(2020, 2301))
PLOT_END_YEAR = 2150

# v1.4.5 slim ANOVA-18k (post-PR#93 BRICK + FaIR v1.4.5 + importance-weighting),
# 54,000 paired (rff, cfg, seed, post) rows × 451 years 1850-2300.
# Replaces the legacy 13,500-row brick_anova_long_2300_*.csv files (now in
# outputs/quarantine/20260524_pre_v145_e2e/).
BASELINE_CSV = OUT / "brick_v145_slim" / "brick_anova18k_baseline_to2300_weighted.csv"
PULSE_CSV    = OUT / "brick_v145_slim" / "brick_anova18k_pulse_co2_pos_1gt_to2300.csv"
MARGINAL_CSV = OUT / "brick_v145_slim" / "brick_anova18k_marginal_co2_pos_1gt_to2300_weighted.csv"


def build_marginal(base_df, pulse_df):
    """Return a marginal-SLR DataFrame paired by (rff, cfg, seed, post)."""
    keys = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
    base = base_df.sort_values(keys).reset_index(drop=True)
    pulse = pulse_df.sort_values(keys).reset_index(drop=True)
    if len(base) != len(pulse):
        raise ValueError(f"row count mismatch: base={len(base)} pulse={len(pulse)}")
    if not (base[keys].values == pulse[keys].values).all():
        raise ValueError("key column mismatch after sort — pairing broken")

    # Year columns: drop summary cols, keep only numeric year columns
    year_cols = [c for c in base.columns if c.isdigit()]
    print(f"  pairing on {len(base)} tuples × {len(year_cols)} year columns")

    margin = base[keys + ["w_norm"]].copy()
    Yb = base[year_cols].to_numpy(dtype=np.float64)
    Yp = pulse[year_cols].to_numpy(dtype=np.float64)
    D = Yp - Yb
    for j, y in enumerate(year_cols):
        margin[y] = D[:, j]
    return margin


def main():
    if not BASELINE_CSV.exists():
        sys.exit(f"Missing baseline weighted CSV: {BASELINE_CSV}")
    if not PULSE_CSV.exists():
        sys.exit(f"Missing pulse CSV: {PULSE_CSV}")

    print(f"Loading baseline (with w_norm): {BASELINE_CSV.name}")
    base = pd.read_csv(BASELINE_CSV)
    print(f"  rows: {len(base):,}")
    print(f"Loading pulse:                    {PULSE_CSV.name}")
    pulse = pd.read_csv(PULSE_CSV)
    print(f"  rows: {len(pulse):,}")

    print("\nBuilding per-tuple marginal CSV...")
    marg = build_marginal(base, pulse)
    marg.to_csv(MARGINAL_CSV, index=False)
    print(f"  wrote {MARGINAL_CSV}  shape={marg.shape}")

    # Quick sanity check: marginal at anchor year 2020 should be ~0 (pre-pulse),
    # at 2030 should be tiny, at 2100 should be positive median.
    print("\nSanity: marginal SLR (cm) at key years (unweighted median):")
    for y in (2020, 2030, 2050, 2100, 2150, 2300):
        col = str(y)
        if col in marg.columns:
            v = marg[col].to_numpy()
            print(f"  {y}: median={np.median(v):+.4f}  P5={np.percentile(v, 5):+.4f}  "
                  f"P95={np.percentile(v, 95):+.4f}")

    print(f"\nComputing 4-way decomp on the marginal at {len(DECOMP_YEARS)} years "
          f"(anchor={T_ANCHOR})...")
    decomp = decompose_slr_4way(marg, DECOMP_YEARS, t_anchor=T_ANCHOR,
                                weights_col="w_norm")

    # Attach EMPIRICAL importance-weighted P5/P50/P95 per year so the inset in
    # plot_hs_stack uses real percentiles instead of mean ± 1.96σ. The pulse-
    # marginal distribution is asymmetric (near-zero floor + fat AIS-tipping
    # upper tail) so a Gaussian band gives misleading negative lower bounds.
    w = marg["w_norm"].to_numpy()
    p5_arr, p50_arr, p95_arr = [], [], []
    for y in decomp["year"]:
        col = str(int(y))
        if col in marg.columns:
            v = marg[col].to_numpy()
            order = np.argsort(v)
            v_sorted = v[order]; w_sorted = w[order]
            cw = np.cumsum(w_sorted)
            total = cw[-1] if cw[-1] > 0 else 1.0
            p5_arr.append(float(v_sorted[np.searchsorted(cw, 0.05 * total)]))
            p50_arr.append(float(v_sorted[np.searchsorted(cw, 0.50 * total)]))
            p95_arr.append(float(v_sorted[np.searchsorted(cw, 0.95 * total)]))
        else:
            p5_arr.append(np.nan); p50_arr.append(np.nan); p95_arr.append(np.nan)
    decomp["p5"] = p5_arr
    decomp["p50"] = p50_arr
    decomp["p95"] = p95_arr

    out_csv = PLOTS / "hawkins_sutton_slr_4way_pulse.csv"
    decomp.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  ({len(decomp)} years)")

    print("\nPulse-SLR 4-way decomp preview at key years:")
    for y in (2030, 2050, 2075, 2100, 2125, 2150, 2200, 2300):
        m = decomp[decomp["year"] == y]
        if not len(m):
            continue
        r = m.iloc[0]
        print(f"  {y}: V_tot={r['V_total']:.4f}  "
              f"V_emi={r['V_emissions']:.4f}  V_clim={r['V_climate']:.4f}  "
              f"V_int={r['V_internal']:.4f}  V_brick={r['V_brick']:.4f}  "
              f"f_emi={r['f_emissions']:.2f}  f_clim={r['f_climate']:.2f}  "
              f"f_int={r['f_internal']:.2f}  f_brick={r['f_brick']:.2f}  "
              f"mean={r['mean']:+.4f}")

    # Plot truncated to 2150
    decomp_plot = decomp[decomp["year"] <= PLOT_END_YEAR].reset_index(drop=True)

    # Composite Panel D figure: main = Hawkins-Sutton variance-fraction
    # stackplot; inset = small-pulse (0.01 GtCO₂) per-unit SLR median + band.
    _plot_pulse_composite(
        decomp_plot, marg,
        out_png=PLOTS / "hawkins_sutton_slr_4way_pulse.png",
        out_pdf=PLOTS / "hawkins_sutton_slr_4way_pulse.pdf",
    )

    # Caveat sidecar
    caveat = (
        "Decomposition of the marginal SLR response (pulse − baseline) to a "
        "1 GtCO₂ pulse at 2030. Paired BRICK with shared posts across seeds "
        "(post-fix 2026-05-16) cancels FaIR stochastic noise in the diff for "
        "the bulk of the distribution (median per-cell Var_seed = 1.6e-7 cm²). "
        "The non-zero 'internal-variability' component is NOT paired-noise leak "
        "but TIPPING-POINT STATE DEPENDENCE: for BRICK posterior draws near an "
        "AIS tipping threshold, whether the +1 GtCO₂ pulse crosses the threshold "
        "depends on the FaIR stochastic climate state at 2030. A ~5% fat tail of "
        "(rff,cfg,post) cells shows 10× ΔSLR variance across seeds; integrated "
        "over the ensemble this contributes ~24%% of marginal-SLR variance at 2100. "
        "V_brick (~59%%) captures BRICK posterior parameter sensitivity to the "
        "marginal forcing — particularly AIS, GIS, and TE rate constants — and "
        "is the dominant source of uncertainty in SC-CO₂-SLR at mid-century."
    )
    caveat_path = PLOTS / "hawkins_sutton_slr_4way_pulse_caveat.txt"
    caveat_path.write_text(caveat + "\n")
    print(f"  wrote caveat sidecar: {caveat_path}")


if __name__ == "__main__":
    main()
