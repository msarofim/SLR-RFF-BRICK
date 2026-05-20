"""
extract_pulse_marginals.py
==========================

Produce small ensemble-summary CSVs for the Substack pulse-response figures:

  • Marginal GMST: GMST_pulse(t) - GMST_baseline(t) per paired (rff, cfg, seed),
    then importance-weighted P5 / P50 / P95 / mean across the ensemble per year.

  • Marginal SLR:  SLR_pulse(t) - SLR_baseline(t) per row of the matched
    paired BRICK CSV; same weighted percentile summary.

Each output is one row per year with columns:
  year, mean, p5, p50, p95

Outputs:
  outputs/substack/co2_pulse_gmst_summary.csv
  outputs/substack/co2_pulse_slr_summary.csv
  outputs/substack/ch4_pulse_gmst_summary.csv
  outputs/substack/ch4_pulse_slr_summary.csv   (only if CH4 paired BRICK exists)

Designed to run on Torch (where the FaIR cubes live).  Pull the small CSVs
to laptop for plotting.

Usage:
  python python/scripts/extract_pulse_marginals.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

_TORCH = Path("/scratch/ms17839/SLR-RFF-BRICK")
ROOT = _TORCH if _TORCH.exists() else Path(__file__).resolve().parents[2]
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)


CO2_BASELINE_CUBE = ROOT / "outputs/rff_baseline_stoch_to2300.npz"
CO2_PULSE_CUBE    = ROOT / "outputs/rff_pulse_stoch_to2300.npz"
CH4_BASELINE_CUBE = ROOT / "outputs/rff_baseline_stoch_to2300.npz"   # same baseline
CH4_PULSE_CUBE    = ROOT / "outputs/rff_ch4pulse_stoch_to2300.npz"

# For CO2: pre-fix baseline + pre-fix CO2 pulse (paired May 13; both
# pre-fix, so get_model() noise cancels in the diff).
CO2_BRICK_BASELINE = ROOT / "outputs/brick_paired_rff_baseline_to2300_weighted.csv"
CO2_BRICK_PULSE    = ROOT / "outputs/brick_paired_rff_pulse_to2300_weighted.csv"
# For CH4: post-fix baseline + post-fix CH4 pulse (paired May 18, both
# use Random.seed!() before get_model so initial state matches per row).
CH4_BRICK_BASELINE = ROOT / "outputs/brick_paired_rff_baseline_postfix_to2300_weighted.csv"
CH4_BRICK_PULSE    = ROOT / "outputs/brick_paired_rff_ch4pulse_to2300_weighted.csv"

# Small-pulse companion runs added 2026-05-19 to support pulse-size-invariance
# diagnostics and SC-GHG-relevant linear-regime extraction.  Each is paired
# against the SAME (rff,cfg,seed) baseline as its 1.0-GtC / 1.0-Tg counterpart.
CO2_BRICK_PULSE_0P1   = ROOT / "outputs/brick_paired_rff_pulse0p1gtc_to2300_weighted.csv"
CO2_BRICK_PULSE_0P01  = ROOT / "outputs/brick_paired_rff_pulse0p01gtc_to2300_weighted.csv"
CH4_BRICK_PULSE_0P1   = ROOT / "outputs/brick_paired_rff_ch4pulse0p1tg_to2300_weighted.csv"
CH4_BRICK_PULSE_0P01  = ROOT / "outputs/brick_paired_rff_ch4pulse0p01tg_to2300_weighted.csv"

PLOT_YEARS = (2025, 2300)

# AIS-state classifier for the marginal SLR split.  We classify each paired
# draw by its BASELINE AIS contribution to SLR at the reference year
# (ais_2100_cm column in the baseline weighted CSV).  This is a property of
# the (rff, cfg, seed, post) baseline trajectory, independent of pulse size.
#
# Why: a marginal-magnitude threshold (the poster's "ΔSLR > 0.3 cm" cut) is
# pulse-size sensitive — at 1/10 or 10× the pulse, a different fraction of
# draws would exceed the cut and the mean(all) vs mean(non-tipped) gap would
# shift.  Classifying on the BASELINE makes the split invariant to pulse
# size, and the non-tipping-prone subset's marginal is the linear-regime
# per-tonne sensitivity that scales cleanly for SC-GHG.  The tipping-prone
# subset captures nonlinear AIS amplification that does NOT scale linearly
# with pulse size.
AIS_TIPPING_REFERENCE_YEAR = 2100   # which baseline column to read
AIS_TIPPING_THRESHOLD_CM   = 20.0   # baseline ais_2100_cm > this → tipping-prone.
                                     # ≈ top 45% of the weighted baseline ensemble.
                                     # Calibrated to capture *near-tipping* baselines
                                     # (those sitting just below the AIS threshold
                                     # that a small pulse can push over).  Tested at
                                     # 16.6/20/30/40/52.9; threshold values above 25 cm
                                     # miss the single CH4 pulse-induced tipping
                                     # event (baseline ais_2100 = 29.6 cm) and put it
                                     # in the wrong subset, inverting the CH4 panel.


def w_quantile(v, w, q):
    mask = np.isfinite(v) & (w >= 0)
    vv, ww = v[mask], w[mask]
    if ww.sum() <= 0 or len(vv) == 0:
        return float("nan")
    order = np.argsort(vv)
    vs, ws = vv[order], ww[order]
    cw = np.cumsum(ws)
    return float(vs[min(np.searchsorted(cw, q * cw[-1]), len(vs) - 1)])


def summary_table(M, weights, years, *,
                  baseline_ais=None, ais_threshold=None):
    """M shape (n_draws, n_year); return DataFrame with one row per year.

    If `baseline_ais` (n_draws,) and `ais_threshold` (scalar) are both
    provided, emits the baseline-AIS-state split:
        - mean_AIS_tipping:   weighted mean of marginal SLR over draws with
                              baseline_ais > ais_threshold (tipping-prone)
        - mean_AIS_quiescent: weighted mean over the complement
        - frac_AIS_tipping:   weighted fraction tipping-prone (constant per
                              CSV — depends only on baseline, not on year
                              or pulse size)
    The split is pulse-size invariant by construction: the classifier
    depends only on the baseline trajectory's AIS state, never on the
    marginal.  Non-tipping-prone mean is the linear-regime sensitivity
    that scales cleanly for SC-GHG; tipping-prone mean carries the
    nonlinear AIS amplification that does NOT scale linearly with pulse.
    """
    rows = []
    w_sum = float(weights.sum()) if weights.sum() > 0 else 1.0
    if baseline_ais is not None and ais_threshold is not None:
        is_tipping  = baseline_ais > ais_threshold
        w_tip       = weights * is_tipping
        w_qui       = weights * (~is_tipping)
        w_tip_sum   = float(w_tip.sum())
        w_qui_sum   = float(w_qui.sum())
        frac_tipping = w_tip_sum / w_sum
    else:
        is_tipping = None
        frac_tipping = float("nan")
    for j, y in enumerate(years):
        v = M[:, j]
        row = {
            "year": int(y),
            "mean":  float(np.average(v, weights=weights)),
            "p5":    w_quantile(v, weights, 0.05),
            "p50":   w_quantile(v, weights, 0.50),
            "p95":   w_quantile(v, weights, 0.95),
        }
        if is_tipping is not None:
            row["mean_AIS_tipping"]   = (float((w_tip * v).sum() / w_tip_sum)
                                          if w_tip_sum > 0 else float("nan"))
            row["mean_AIS_quiescent"] = (float((w_qui * v).sum() / w_qui_sum)
                                          if w_qui_sum > 0 else float("nan"))
            row["frac_AIS_tipping"]   = frac_tipping
        else:
            row["mean_AIS_tipping"]   = float("nan")
            row["mean_AIS_quiescent"] = float("nan")
            row["frac_AIS_tipping"]   = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def gmst_marginal(baseline_cube_p, pulse_cube_p, brick_csv_p, label,
                  fallback_weights=None):
    print(f"\n=== {label} GMST marginal ===")
    if not baseline_cube_p.exists() or not pulse_cube_p.exists():
        print(f"  missing cube(s): "
              f"baseline={baseline_cube_p.exists()}  "
              f"pulse={pulse_cube_p.exists()} — skipping")
        return None

    nb = np.load(baseline_cube_p)
    nz = np.load(pulse_cube_p)
    yrs = nb["years"]
    Gb = nb["gmst_traj_rff"]
    Gp = nz["gmst_traj_rff"]
    print(f"  cube shapes: base={Gb.shape}, pulse={Gp.shape}")
    # Build pulse vs baseline diff for the SAME (rff,cfg,seed) draws used by BRICK.
    if brick_csv_p.exists():
        b = pd.read_csv(brick_csv_p,
                        usecols=["rff_idx", "fair_cfg_idx", "seed_idx", "w_norm"])
        unique_rffs = nb["unique_rffs"]
        rff_to_pos = {int(r): k for k, r in enumerate(unique_rffs)}
        rff_pos = np.array([rff_to_pos[int(r)] for r in b["rff_idx"].values])
        cfg = b["fair_cfg_idx"].values.astype(int)
        seed = (b["seed_idx"].values.astype(int) if "seed_idx" in b.columns
                else np.zeros(len(b), dtype=int))
        weights = b["w_norm"].to_numpy()
        # Handle 4D vs 3D cubes
        if Gb.ndim == 4:
            M = (Gp[rff_pos, cfg, seed, :] - Gb[rff_pos, cfg, seed, :]).astype(np.float64)
        else:
            M = (Gp[rff_pos, cfg, :] - Gb[rff_pos, cfg, :]).astype(np.float64)
    else:
        # No paired BRICK CSV: take all (rff,cfg,seed) tuples with equal weight.
        print(f"  no BRICK CSV ({brick_csv_p.name}); using full cube with equal weights")
        if Gb.ndim == 4:
            M = (Gp - Gb).reshape(-1, Gb.shape[-1]).astype(np.float64)
        else:
            M = (Gp - Gb).reshape(-1, Gb.shape[-1]).astype(np.float64)
        weights = np.ones(M.shape[0], dtype=np.float64) if fallback_weights is None else fallback_weights
    print(f"  built marginal: {M.shape}  weights sum={weights.sum():.1f}")
    return yrs, M, weights


def slr_marginal_from_brick(baseline_csv_p, pulse_csv_p, label):
    print(f"\n=== {label} SLR marginal ===")
    if not baseline_csv_p.exists() or not pulse_csv_p.exists():
        print(f"  missing brick csv(s): "
              f"baseline={baseline_csv_p.exists()}  "
              f"pulse={pulse_csv_p.exists()} — skipping")
        return None
    b = pd.read_csv(baseline_csv_p)
    p = pd.read_csv(pulse_csv_p)
    # Align on the metadata keys
    keys = [k for k in ("rff_idx", "fair_cfg_idx", "seed_idx", "post_idx")
            if k in b.columns and k in p.columns]
    print(f"  pairing on: {keys}")
    bs = b.sort_values(keys).reset_index(drop=True)
    ps = p.sort_values(keys).reset_index(drop=True)
    assert len(bs) == len(ps), f"row mismatch base={len(bs)} pulse={len(ps)}"
    assert (bs[keys].values == ps[keys].values).all(), "key mismatch"
    year_cols = [c for c in bs.columns if c.isdigit()]
    yrs = np.array([int(c) for c in year_cols])
    Yb = bs[year_cols].to_numpy(np.float64)
    Yp = ps[year_cols].to_numpy(np.float64)
    M = Yp - Yb
    weights = bs["w_norm"].to_numpy() if "w_norm" in bs.columns else np.ones(len(bs))
    # Carry the per-draw baseline AIS state forward for the AIS-state split.
    ais_col = f"ais_{AIS_TIPPING_REFERENCE_YEAR}_cm"
    baseline_ais = (bs[ais_col].to_numpy(np.float64)
                    if ais_col in bs.columns else None)
    print(f"  built marginal: {M.shape}  weights sum={weights.sum():.1f}  "
          f"baseline {ais_col}: "
          f"{'available' if baseline_ais is not None else 'MISSING'}")
    return yrs, M, weights, baseline_ais


def emit(yrs, M, weights, fname, year_lo, year_hi,
         baseline_ais=None, ais_threshold=None):
    df = summary_table(M, weights, yrs,
                       baseline_ais=baseline_ais, ais_threshold=ais_threshold)
    df = df[(df.year >= year_lo) & (df.year <= year_hi)].reset_index(drop=True)
    df.to_csv(OUT / fname, index=False)
    extra = (f" + AIS-state split @ baseline ais_{AIS_TIPPING_REFERENCE_YEAR}>"
             f"{ais_threshold} cm  (frac_tipping={df.frac_AIS_tipping.iloc[0]:.3f})"
             if baseline_ais is not None and ais_threshold is not None else "")
    print(f"  wrote {OUT / fname}  ({len(df)} years){extra}")


def main():
    y_lo, y_hi = PLOT_YEARS

    # CO2 GMST (no AIS split — GMST has no tipping nonlinearity)
    co2_gmst = gmst_marginal(CO2_BASELINE_CUBE, CO2_PULSE_CUBE,
                             CO2_BRICK_BASELINE, "CO2")
    if co2_gmst is not None:
        emit(*co2_gmst, "co2_pulse_gmst_summary.csv", y_lo, y_hi)

    # CO2 SLR (with baseline-AIS-state split — pulse-size invariant classifier).
    # Three pulse sizes; each produces its own summary CSV for pulse-size-
    # invariance diagnostics and Lemoine-style decomposition.
    for pulse_csv, size_tag, divisor in [
        (CO2_BRICK_PULSE,      "1p0gtc",  1.0),
        (CO2_BRICK_PULSE_0P1,  "0p1gtc",  0.1),
        (CO2_BRICK_PULSE_0P01, "0p01gtc", 0.01),
    ]:
        co2_slr = slr_marginal_from_brick(CO2_BRICK_BASELINE, pulse_csv, f"CO2 {size_tag}")
        if co2_slr is not None:
            yrs, M, w, ais = co2_slr
            # Divide marginal by pulse magnitude so the saved CSV is per unit pulse
            emit(yrs, M / divisor, w, f"co2_pulse_slr_summary_{size_tag}.csv",
                 y_lo, y_hi, baseline_ais=ais,
                 ais_threshold=AIS_TIPPING_THRESHOLD_CM)
    # Back-compat: legacy filename is the 1.0-GtC case
    co2_slr = slr_marginal_from_brick(CO2_BRICK_BASELINE, CO2_BRICK_PULSE, "CO2 1p0gtc (legacy)")
    if co2_slr is not None:
        yrs, M, w, ais = co2_slr
        emit(yrs, M, w, "co2_pulse_slr_summary.csv", y_lo, y_hi,
             baseline_ais=ais, ais_threshold=AIS_TIPPING_THRESHOLD_CM)

    # CH4 GMST (no AIS split)
    ch4_gmst = gmst_marginal(CH4_BASELINE_CUBE, CH4_PULSE_CUBE,
                             CH4_BRICK_BASELINE, "CH4")
    if ch4_gmst is not None:
        emit(*ch4_gmst, "ch4_pulse_gmst_summary.csv", y_lo, y_hi)

    # CH4 SLR (same AIS-state classifier as CO2 — both panels comparable).
    for pulse_csv, size_tag, divisor in [
        (CH4_BRICK_PULSE,      "1p0tg",   1.0),
        (CH4_BRICK_PULSE_0P1,  "0p1tg",   0.1),
        (CH4_BRICK_PULSE_0P01, "0p01tg",  0.01),
    ]:
        ch4_slr = slr_marginal_from_brick(CH4_BRICK_BASELINE, pulse_csv, f"CH4 {size_tag}")
        if ch4_slr is not None:
            yrs, M, w, ais = ch4_slr
            emit(yrs, M / divisor, w, f"ch4_pulse_slr_summary_{size_tag}.csv",
                 y_lo, y_hi, baseline_ais=ais,
                 ais_threshold=AIS_TIPPING_THRESHOLD_CM)
    # Back-compat: legacy filename is the 1.0-Tg case
    ch4_slr = slr_marginal_from_brick(CH4_BRICK_BASELINE, CH4_BRICK_PULSE, "CH4 1p0tg (legacy)")
    if ch4_slr is not None:
        yrs, M, w, ais = ch4_slr
        emit(yrs, M, w, "ch4_pulse_slr_summary.csv", y_lo, y_hi,
             baseline_ais=ais, ais_threshold=AIS_TIPPING_THRESHOLD_CM)


if __name__ == "__main__":
    main()
