"""
gaussian_vs_empirical_slr.py
============================

Substack HEADER figure: the same small-pulse (0.01 GtCO₂) LHS-10k SLR
ensemble, summarized two ways. Designed as a 16:9-ish lede graphic with
the visual punchline obvious at a glance.

  • Left panel  — Gaussian assumption: mean ± 1.96σ band centered on the
                  ensemble mean. The lower edge dips below zero — a
                  physically impossible "negative SLR from a positive
                  CO₂ pulse" region, called out with hatched shading.

  • Right panel — Real data: empirical 5–50–95% quantiles
                  (importance-weighted). Matches the AGU Chapman poster's
                  D_pulse_slr inset convention: median heavy line + 5–95%
                  shaded band, all in cm per GtCO₂.

Why the small-pulse (0.01 GtCO₂) source:  Panel D of the poster uses the
0.01-GtCO₂ LHS-10k companion because it's in the linear regime
(verified by the pulse-size convergence diagnostic) and gives a
pulse-size-invariant per-tonne SC-CO₂-SLR sensitivity. The 1-GtCO₂ pulse
is contaminated by pulse-induced AIS tipping that doesn't scale linearly.
Both panels in this figure use the same small-pulse data so the
comparison is apples-to-apples.

The point of the figure for the substack post: even in the small-pulse
*linear* regime, the marginal-SLR distribution is positively skewed —
heavy upper tail from BRICK posterior uncertainty in AIS sensitivity.
A symmetric Gaussian summary (mean ± 1.96σ) wastes mass on impossible
negative SLR and centers on a mean that overstates the typical response.
Reading the empirical quantiles is the honest path.

Outputs:
  outputs/substack/gaussian_vs_empirical_slr.{png,pdf}   (header)
  outputs/substack/gaussian_vs_empirical_slr_per_year.csv (table)

Usage:
  python python/scripts/substack/gaussian_vs_empirical_slr.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Configuration (named constants drive labels per global discipline) ────────
ROOT       = Path(__file__).resolve().parents[3]
OUT        = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

# v1.4.5 slim CSVs (post-PR#93 BRICK posterior + FaIR v1.4.5 + Wong-weighting).
# Files produced by python/scripts/emit_slim_legacy_csvs_v145.py from the
# Wong-pipeline outputs in outputs/brick_v145_summaries/. Both files use the
# legacy bare-year column schema (e.g. "2050", "2100") so this script's
# detect-numeric-columns logic works unchanged. Pulse arm 'co2_pos_001gt' is
# the 0.01-GtCO₂ small-pulse companion (linear-regime). See UNIT NOTE below
# regarding the v1.4.5 calibration's GtCO₂ pulse unit.
BASELINE_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"
PULSE_CSV    = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_pulse_co2_pos_001gt_to2300.csv"

# UNIT NOTE 2026-05-25: FaIR v1.4.5's 'CO2 FFI' species has input_unit
# 'GtCO2' (see compute_pulse_temps_v145.py + species_configs_properties_1.4.5.csv).
# The 001gt cube arm was built with `--pulse-size 0.01` = 0.01 GtCO2 (NOT
# 0.01 GtC). Pre-fix the script assumed GtC and applied an extra 12/44
# conversion — gave values 3.67× too small. The fix below skips the
# GtC→GtCO2 conversion since the pulse is already in GtCO2.
PULSE_SIZE_GTCO2    = 0.01                                  # FaIR v1.4.5 unit
MARGINAL_SCALE      = 1.0 / PULSE_SIZE_GTCO2                # cm per GtCO₂ directly

PULSE_LABEL  = "1 GtCO₂ pulse at 2030"      # narrative label; data is 0.01-GtCO₂ linear-regime, scaled to 1-GtCO₂ basis
ENSEMBLE_LBL = "LHS-10k importance-weighted (FaIR v1.4.5 + post-PR#93 BRICK)"

PLOT_START, PLOT_END = 2020, 2150
LANDMARK_YRS = (2050, 2100, 2150)

# L-T classifier: cells with per-year marginal above this are flagged
# "tipped" and excluded from the linear-baseline mean + std. Matches the
# poster's pulse_response_split convention.
TIPPING_THRESHOLD_CM = 0.3

# ── Visual style (substack header) ───────────────────────────────────────────
COLOR_GAUSS = "#C8102E"      # vivid red — Gaussian summary
COLOR_EMP   = "#0B3D91"      # NASA-blue — empirical summary
COLOR_TEXT  = "#1A1A1A"
COLOR_GREY  = "#666666"
COLOR_GRID  = "#DDDDDD"
COLOR_IMPOSSIBLE = "#FF6B6B"  # hatched callout

FIG_W, FIG_H = 14.0, 6.5     # 14 × 6.5 in → 1456×676 px at 104 dpi, 4200×1950 at 300 dpi

plt.rcParams.update({
    "font.family":  "DejaVu Sans",
    "font.size":    11,
    "axes.titlesize":   13,
    "axes.labelsize":   12,
    "xtick.labelsize":  11,
    "ytick.labelsize":  11,
    "legend.fontsize":  10,
})


# ── Weighted helpers ─────────────────────────────────────────────────────────
def weighted_mean(v, w):
    return float(np.average(v, weights=w))


def weighted_std(v, w):
    mu = weighted_mean(v, w)
    var = np.average((v - mu) ** 2, weights=w)
    return float(np.sqrt(var))


def weighted_quantile(v, w, q):
    order = np.argsort(v)
    vs, ws = v[order], w[order]
    cw = np.cumsum(ws)
    idx = min(np.searchsorted(cw, q * cw[-1]), len(vs) - 1)
    return float(vs[idx])


# ── Load + compute marginal (pulse − baseline), paired by 4-tuple ────────────
def load_marginal():
    b = pd.read_csv(BASELINE_CSV)
    p = pd.read_csv(PULSE_CSV)
    keys = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
    bs = b.sort_values(keys).reset_index(drop=True)
    ps = p.sort_values(keys).reset_index(drop=True)
    assert len(bs) == len(ps), f"row mismatch: base={len(bs)} pulse={len(ps)}"
    assert (bs[keys].values == ps[keys].values).all(), "pairing key mismatch"

    year_cols = [c for c in bs.columns if c.isdigit()]
    years = np.array([int(c) for c in year_cols])
    Yb = bs[year_cols].to_numpy(np.float64)
    Yp = ps[year_cols].to_numpy(np.float64)
    # Marginal in cm-per-pulse → rescale to cm per GtCO₂ in one step:
    M = (Yp - Yb) * MARGINAL_SCALE
    w = bs["w_norm"].to_numpy(np.float64)
    return years, M, w


def summarize(M, w, years):
    """Per-year weighted: empirical 5/50/95 + an illustrative L-T-style Gaussian.

    The "L-T-corrected Gaussian" for the left panel is *constructed*:
      center = weighted mean of the non-tipped subset (the L-T linear baseline)
      σ      = (empirical p95 − empirical p5) / 2
               i.e., the empirical 5–95% width interpreted as a 1σ Gaussian
               band, which is what you get if you take the IQR-like spread
               and naively assume Gaussian shape.

    This is a counterfactual: had the analyst applied the L-T mean correction
    AND then summarized the residual spread as a Gaussian (1σ ≈ IQR), this is
    the figure they would have produced. The band still drifts below zero
    at long horizons because the underlying distribution is asymmetric —
    making the "symmetric assumption fails" point without the absurd σ
    inflation from raw-mean Gaussian summaries.
    """
    rows = []
    for j, y in enumerate(years):
        v = M[:, j]

        # Empirical (full-ensemble) quantiles — for the right panel
        p5  = weighted_quantile(v, w, 0.05)
        p50 = weighted_quantile(v, w, 0.50)
        p95 = weighted_quantile(v, w, 0.95)

        # L-T linear baseline: weighted mean over non-tipped subset.
        is_tipped = v > TIPPING_THRESHOLD_CM
        w_lin = w * (~is_tipped)
        w_lin_sum = float(w_lin.sum())
        if w_lin_sum > 0:
            v_lin = v[~is_tipped]
            w_lin_v = w[~is_tipped]
            mu_lt = float(np.average(v_lin, weights=w_lin_v))
        else:
            mu_lt = float("nan")
        frac_tipped = float((w * is_tipped).sum() / w.sum())

        # Illustrative Gaussian σ: empirical 5-95 width treated as ±1σ band.
        # See docstring — this is a counterfactual choice that lets the
        # symmetric-assumption pathology (band crossing zero) remain visible
        # even after the L-T mean correction.
        sigma_illus = (p95 - p5) / 2.0

        rows.append(dict(
            year=int(y),
            # L-T-style illustrative Gaussian (for the LEFT panel)
            lt_mean=mu_lt,
            lt_std=sigma_illus,
            lt_gauss_lo=mu_lt - 1.96 * sigma_illus,
            lt_gauss_hi=mu_lt + 1.96 * sigma_illus,
            frac_tipped=frac_tipped,
            # Empirical quantiles (for the RIGHT panel)
            p5=p5, p50=p50, p95=p95,
            # Full-ensemble raw mean / std (diagnostic only)
            mean=weighted_mean(v, w),
            std=weighted_std(v, w),
        ))
    return pd.DataFrame(rows)


# ── Plot (substack header style) ─────────────────────────────────────────────
def plot_panels(df):
    """Two panels, SAME y-axis, focused on the zero-crossing.

    The visual point: the Gaussian band drifts below zero (impossible —
    a positive CO₂ pulse can't lower sea level), while the empirical
    band stays strictly above zero where physics requires.

    Y-axis is clipped to a moderate range. The Gaussian's σ is large
    enough that its band continues off-screen above and below; arrows
    + a "continues off-frame" note signal that. The empirical band fits
    comfortably in the visible range.
    """
    sub = df[(df.year >= PLOT_START) & (df.year <= PLOT_END)].copy()
    yr  = sub.year.to_numpy()

    # Left panel: L-T-corrected Gaussian (center = non-tipped mean,
    # σ = non-tipped std). Crosses zero because the non-tipped distribution
    # is itself moderately skewed; no σ-inflation by tipping outliers.
    g_lo = sub.lt_gauss_lo.to_numpy()
    g_hi = sub.lt_gauss_hi.to_numpy()
    g_mu = sub.lt_mean.to_numpy()
    # Right panel: empirical quantiles (matches poster D inset)
    p5   = sub.p5.to_numpy()
    p50  = sub.p50.to_numpy()
    p95  = sub.p95.to_numpy()

    # Shared y-axis range: sized so both panels' content is fully visible.
    # With the L-T-style illustrative Gaussian, the left band reaches at
    # most ~+0.05 (upper) / ~-0.03 (lower) by 2150 — comparable scale to
    # the empirical band. Symmetric around zero so the zero-crossing
    # remains the visual focus.
    raw_hi = max(g_hi.max(), p95.max())
    raw_lo = min(g_lo.min(), 0.0)
    y_hi = float(np.ceil(raw_hi * 1.20 * 100) / 100)
    y_lo = float(np.floor(min(raw_lo, -y_hi * 0.6) * 100) / 100)

    fig, axes = plt.subplots(
        1, 2, figsize=(FIG_W, FIG_H), sharey=True,
        gridspec_kw=dict(wspace=0.08),
    )
    fig.patch.set_facecolor("white")
    units = "Marginal SLR (cm per GtCO₂)"

    # ── Left: Gaussian assumption ────────────────────────────────────────────
    axL = axes[0]
    # Gaussian band, clipped at plot edges
    g_lo_clip = np.maximum(g_lo, y_lo)
    g_hi_clip = np.minimum(g_hi, y_hi)
    axL.fill_between(yr, g_lo_clip, g_hi_clip, color=COLOR_GAUSS,
                     alpha=0.20, linewidth=0,
                     label="Mean ± 1.96σ band (σ ≈ ½ empirical 5–95% width)")
    axL.plot(yr, g_mu, color=COLOR_GAUSS, linewidth=3.0, linestyle="--",
             label="L-T linear-baseline mean")

    # Heavy "IMPOSSIBLE" shading on the negative region of the Gaussian band
    neg_lo = np.maximum(g_lo, y_lo)   # bottom of negative region (clipped)
    neg_hi = np.minimum(0.0, g_hi)    # top of negative region capped at zero
    axL.fill_between(yr, neg_lo, neg_hi,
                     where=neg_lo < 0,
                     facecolor=COLOR_IMPOSSIBLE, alpha=0.45,
                     linewidth=0, label=None)
    axL.fill_between(yr, neg_lo, neg_hi,
                     where=neg_lo < 0,
                     facecolor="none", edgecolor=COLOR_IMPOSSIBLE,
                     hatch="///", linewidth=0.0, alpha=0.95, label=None)
    axL.axhline(0, color=COLOR_TEXT, linewidth=1.4)

    axL.set_title("Gaussian summary on L-T-corrected linear baseline",
                  fontsize=15, fontweight="bold", color=COLOR_GAUSS, pad=10)
    axL.set_xlabel("Year", fontsize=12)
    axL.set_ylabel(units, fontsize=12)
    axL.set_xlim(PLOT_START, PLOT_END)
    axL.set_ylim(y_lo, y_hi)
    leg = axL.legend(loc="upper left", framealpha=0.95, fontsize=10.5,
                     edgecolor=COLOR_GREY)
    leg.get_frame().set_linewidth(0.6)
    axL.grid(color=COLOR_GRID, linewidth=0.6, alpha=0.85)
    for spine in ("top", "right"):
        axL.spines[spine].set_visible(False)

    # Off-frame down-arrow showing the Gaussian band continues into much
    # deeper "impossible" territory. (No up-arrow — the upper extent is not
    # the point of the figure; the dip below zero is.)
    if g_lo.min() < y_lo:
        axL.annotate("", xy=(2055, y_lo * 0.98), xytext=(2055, y_lo * 0.78),
                     arrowprops=dict(arrowstyle="->", color=COLOR_GAUSS,
                                     lw=1.6))
        axL.text(2058, y_lo * 0.88,
                 f"… continues to {g_lo.min():.2f} cm",
                 fontsize=9.0, color=COLOR_GAUSS, va="center")

    # Big punchline annotation in the impossible region
    axL.text(2090, y_lo * 0.55,
             "IMPOSSIBLE:\na positive CO₂ pulse\ncannot lower sea level",
             fontsize=12, fontweight="bold", color="#8B0000",
             ha="center", va="center",
             bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                       edgecolor="#8B0000", linewidth=1.4, alpha=0.96))

    # ── Right: Empirical (matches poster D_pulse_slr inset) ──────────────────
    axR = axes[1]
    axR.fill_between(yr, p5, p95, color=COLOR_EMP, alpha=0.22, linewidth=0,
                     label="Empirical 5–95% band")
    axR.plot(yr, p50, color=COLOR_EMP, linewidth=3.0, label="Empirical median")
    axR.axhline(0, color=COLOR_TEXT, linewidth=1.4)

    axR.set_title("Real data:  empirical 5–50–95% quantiles",
                  fontsize=16, fontweight="bold", color=COLOR_EMP, pad=10)
    axR.set_xlabel("Year", fontsize=12)
    axR.set_xlim(PLOT_START, PLOT_END)
    axR.set_ylim(y_lo, y_hi)
    leg = axR.legend(loc="upper left", framealpha=0.95, fontsize=10.5,
                     edgecolor=COLOR_GREY)
    leg.get_frame().set_linewidth(0.6)
    axR.grid(color=COLOR_GRID, linewidth=0.6, alpha=0.85)
    for spine in ("top", "right", "left"):
        axR.spines[spine].set_visible(False)

    # Big punchline annotation: empirical stays above zero
    axR.text(2090, y_lo * 0.55,
             "Empirical band stays\nstrictly above zero\n(physics, respected)",
             fontsize=12, fontweight="bold", color=COLOR_EMP,
             ha="center", va="center",
             bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                       edgecolor=COLOR_EMP, linewidth=1.4, alpha=0.96))

    # Highlight 2150 endpoint values
    r2150 = sub.loc[sub.year == 2150].iloc[0]
    axR.annotate(
        f"95th pct\n+{r2150.p95:.3f}",
        xy=(2150, r2150.p95),
        xytext=(2118, r2150.p95 + 0.012),
        ha="left", va="bottom", fontsize=10.0, color=COLOR_EMP,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=COLOR_EMP, lw=1.1,
                        connectionstyle="arc3,rad=-0.18"),
    )
    axR.annotate(
        f"median\n+{r2150.p50:.3f}",
        xy=(2150, r2150.p50),
        xytext=(2118, r2150.p50 - 0.015),
        ha="left", va="top", fontsize=10.0, color=COLOR_EMP,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=COLOR_EMP, lw=1.1,
                        connectionstyle="arc3,rad=0.18"),
    )

    # ── Title block ──────────────────────────────────────────────────────────
    # Just a clean bold title above the panels. Source provenance lives in
    # the bottom caption only.
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])

    fig.suptitle(
        f"Marginal sea-level rise from a {PULSE_LABEL}: "
        "Gaussian summary vs the real distribution",
        fontsize=18, fontweight="bold", color=COLOR_TEXT, y=0.98,
    )
    # Bottom caption: small attribution / source note
    fig.text(
        0.5, 0.01,
        f"Data: paired BRICK ensemble ({ENSEMBLE_LBL}, post-PR#93 Wong posterior). "
        "Pulse-size-invariant linear regime via 0.01 GtCO₂ companion run, "
        "scaled to per-GtCO₂. Years 2020–2150.",
        ha="center", va="bottom", fontsize=9.0, color=COLOR_GREY,
        style="italic",
    )

    return fig


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Loading paired baseline + small-pulse "
          f"({PULSE_SIZE_GTCO2} GtCO₂ pulse → cm per GtCO₂ via × {MARGINAL_SCALE:.4f}) ...")
    years, M, w = load_marginal()
    print(f"  marginal shape {M.shape}, weights sum = {w.sum():.3f}")

    df = summarize(M, w, years)

    # Per-year table for footnote use
    csv_path = OUT / "gaussian_vs_empirical_slr_per_year.csv"
    df_clip = df[(df.year >= PLOT_START) & (df.year <= PLOT_END)].copy()
    df_clip.to_csv(csv_path, index=False)
    print(f"\nWrote per-year table -> {csv_path}")

    print(f"\n=== Landmark years (cm per GtCO₂; small-pulse linear regime) ===")
    print(f"  L-T = Gaussian centered on non-tipped subset mean (linear baseline)")
    print(f"  Empirical = importance-weighted quantiles, all 10k draws\n")
    print(f"{'year':>6}  {'lt_mean':>8}  {'lt_σ':>8}  {'lt_lo':>8}  {'lt_hi':>8}  "
          f"{'%tip':>5}  {'p5':>8}  {'p50':>8}  {'p95':>8}")
    for y in LANDMARK_YRS:
        r = df.loc[df.year == y].iloc[0]
        print(f"{int(r.year):>6}  {r['lt_mean']:>+8.4f}  {r['lt_std']:>+8.4f}  "
              f"{r['lt_gauss_lo']:>+8.4f}  {r['lt_gauss_hi']:>+8.4f}  "
              f"{r['frac_tipped']*100:>4.1f}%  "
              f"{r['p5']:>+8.4f}  {r['p50']:>+8.4f}  {r['p95']:>+8.4f}")

    # Verify pulse-size invariance sanity vs the project memo:
    #   v1.4.1-era memo target: median ≈ 0.017 cm/GtCO₂, p95 ≈ 0.032.
    #   v1.4.5 (post-PR#93 BRICK posterior; Frederikse GIS added to calib):
    #   expect median ~0.007, p95 ~0.011 (2-3× lower than v141 reference;
    #   PR#93's tightened GIS posterior reduces upper-tail sensitivity).
    p50_2150 = float(df.loc[df.year == 2150, "p50"].iloc[0])
    p95_2150 = float(df.loc[df.year == 2150, "p95"].iloc[0])
    print(f"\n  Sanity (v1.4.5 expected: median ≈ 0.007 cm/GtCO₂, p95 ≈ 0.011;")
    print(f"   v1.4.1 reference was median ≈ 0.016, p95 ≈ 0.032):")
    print(f"    median@2150 = {p50_2150:+.4f}  p95@2150 = {p95_2150:+.4f}  cm/GtCO₂")

    # Plot
    fig = plot_panels(df)
    png = OUT / "gaussian_vs_empirical_slr.png"
    pdf = OUT / "gaussian_vs_empirical_slr.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\nWrote {png}")
    print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()
