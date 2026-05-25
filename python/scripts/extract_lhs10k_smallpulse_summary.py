"""
extract_lhs10k_smallpulse_summary.py
====================================

Build the per-GtC small-pulse SLR marginal summary from the LHS-10k
conditional-BRICK ensemble. Companion to extract_pulse_marginals.py but
operating on the 10,000-LHS-triplet outputs instead of the 500-cell
paired design.

Marginal ΔSLR(t) = (SLR_pulse(t) - SLR_baseline(t)) / 0.01 GtC
                 = per-GtC SLR sensitivity in the linear regime
                   (small-pulse avoids AIS-tipping fat tail)

Wong importance weights inherited from the baseline arm (same draws).

Inputs:
  outputs/brick_lhs10k_baseline_to2300_weighted.csv
  outputs/brick_lhs10k_pulse0p01gtc_to2300_weighted.csv

Output:
  outputs/substack/co2_pulse_slr_summary_lhs10k_0p01gtc.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

# v1.4.5 slim CSVs (post-PR#93 BRICK + FaIR v1.4.5 + Wong-weighting).
BASELINE_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"
PULSE_CSV    = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_pulse_co2_pos_001gt_to2300.csv"
OUT_CSV      = OUT / "co2_pulse_slr_summary_lhs10k_0p01gtc.csv"

# FaIR v1.4.5's `CO2 FFI` species has input_unit "GtCO2"; the 001gt arm
# is therefore 0.01 GtCO2, not 0.01 GtC. See ~/.claude/skills/climate-modeling
# "Unit checks: GtC vs GtCO₂" for the recurring trap.
PULSE_SIZE_GTCO2           = 0.01    # FaIR v1.4.5 CO2 FFI input unit
PLOT_YEARS                 = (2025, 2300)
AIS_TIPPING_REFERENCE_YEAR = 2100
AIS_TIPPING_THRESHOLD_CM   = 20.0


def w_quantile(v, w, q):
    mask = np.isfinite(v) & (w >= 0)
    vv, ww = v[mask], w[mask]
    if ww.sum() <= 0 or len(vv) == 0:
        return float("nan")
    order = np.argsort(vv)
    vs, ws = vv[order], ww[order]
    cw = np.cumsum(ws)
    return float(vs[min(np.searchsorted(cw, q * cw[-1]), len(vs) - 1)])


def main():
    print(f"loading baseline + pulse weighted CSVs from {ROOT/'outputs'}")
    b = pd.read_csv(BASELINE_CSV)
    p = pd.read_csv(PULSE_CSV)
    keys = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
    b = b.sort_values(keys).reset_index(drop=True)
    p = p.sort_values(keys).reset_index(drop=True)
    assert (b[keys].values == p[keys].values).all(), "pairing key mismatch"
    print(f"  paired on {len(b)} tuples")

    year_cols = [c for c in b.columns if c.isdigit()]
    years     = np.array([int(c) for c in year_cols])
    Yb        = b[year_cols].to_numpy(np.float64)
    Yp        = p[year_cols].to_numpy(np.float64)
    M         = (Yp - Yb) / PULSE_SIZE_GTCO2                  # per-GtCO2 marginal
    w         = b["w_norm"].to_numpy()

    ais_col      = f"ais_{AIS_TIPPING_REFERENCE_YEAR}_cm"
    baseline_ais = b[ais_col].to_numpy() if ais_col in b.columns else None
    is_tipping   = (baseline_ais > AIS_TIPPING_THRESHOLD_CM) if baseline_ais is not None else None

    rows = []
    w_sum = float(w.sum())
    if is_tipping is not None:
        w_tip = w * is_tipping
        w_qui = w * (~is_tipping)
        w_tip_sum = float(w_tip.sum())
        w_qui_sum = float(w_qui.sum())
        frac_tipping = w_tip_sum / w_sum
    else:
        frac_tipping = float("nan")

    y_lo, y_hi = PLOT_YEARS
    for j, y in enumerate(years):
        if not (y_lo <= y <= y_hi):
            continue
        v = M[:, j]
        row = {
            "year": int(y),
            "mean": float(np.average(v, weights=w)),
            "p5":   w_quantile(v, w, 0.05),
            "p50":  w_quantile(v, w, 0.50),
            "p95":  w_quantile(v, w, 0.95),
        }
        if is_tipping is not None:
            row["mean_AIS_tipping"]   = (float((w_tip * v).sum() / w_tip_sum)
                                          if w_tip_sum > 0 else float("nan"))
            row["mean_AIS_quiescent"] = (float((w_qui * v).sum() / w_qui_sum)
                                          if w_qui_sum > 0 else float("nan"))
            row["frac_AIS_tipping"]   = frac_tipping
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}  ({len(df)} years)")

    print("\nKey small-pulse SLR sensitivities (cm per GtCO2, Wong-weighted):")
    for y in (2030, 2050, 2075, 2100, 2125, 2150):
        r = df[df.year == y]
        if len(r):
            r0 = r.iloc[0]
            print(f"  {y}: median={r0.p50:+.4f}  mean={r0['mean']:+.4f}  "
                  f"p5={r0.p5:+.4f}  p95={r0.p95:+.4f}")


if __name__ == "__main__":
    main()
