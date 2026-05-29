"""
extract_lhs10k_smallpulse_summary.py
====================================

Build the per-GtCO₂ small-pulse SLR marginal summary from the LHS-10k
conditional-BRICK ensemble. Companion to extract_pulse_marginals.py but
operating on the 10,000-LHS-triplet outputs instead of the 500-cell
paired design.

Marginal ΔSLR(t) = (SLR_pulse(t) - SLR_baseline(t)) / 0.01 GtCO₂
                 = per-GtCO₂ SLR sensitivity in the linear regime
                   (small-pulse avoids AIS-tipping fat tail)

The pulse arm was built with `--pulse-size 0.01` on FaIR v1.4.5's
`CO2 FFI` species, whose input_unit is GtCO₂ — so the divisor is
0.01 GtCO₂, NOT 0.01 GtC. Output values are cm per GtCO₂ directly,
no further unit conversion needed in downstream substack scripts.

Wong importance weights inherited from the baseline arm (same draws).

Inputs:
  outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv
  outputs/brick_v145_slim/brick_lhs10k_pulse_co2_pos_001gt_to2300.csv

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

# v1.4.5 slim CSVs (post-PR#93 BRICK + FaIR v1.4.5 + importance-weighting).
BASELINE_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"
PULSE_CSV    = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_pulse_co2_pos_001gt_to2300.csv"
OUT_CSV      = OUT / "co2_pulse_slr_summary_lhs10k_0p01gtc.csv"

# FaIR v1.4.5's `CO2 FFI` species has input_unit "GtCO2"; the 001gt arm
# is therefore 0.01 GtCO2, not 0.01 GtC. See ~/.claude/skills/climate-modeling
# "Unit checks: GtC vs GtCO₂" for the recurring trap.
PULSE_SIZE_GTCO2 = 0.01    # FaIR v1.4.5 CO2 FFI input unit
PLOT_YEARS       = (2025, 2300)

# Note (2026-05-26): the Lemoine-Traeger tipping-conditional means
# (mean_AIS_tipping / mean_AIS_quiescent / frac_AIS_tipping) were
# dropped from this summary in favor of the threshold-invariant
# empirical p5/p50/p95 quantiles. See outputs/quarantine/
# 20260526_lt_to_empirical/README.md.


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

    rows = []
    y_lo, y_hi = PLOT_YEARS
    for j, y in enumerate(years):
        if not (y_lo <= y <= y_hi):
            continue
        v = M[:, j]
        rows.append({
            "year": int(y),
            "mean": float(np.average(v, weights=w)),
            "p5":   w_quantile(v, w, 0.05),
            "p50":  w_quantile(v, w, 0.50),
            "p95":  w_quantile(v, w, 0.95),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}  ({len(df)} years)")

    print("\nKey small-pulse SLR sensitivities (cm per GtCO2, importance-weighted):")
    for y in (2030, 2050, 2075, 2100, 2125, 2150):
        r = df[df.year == y]
        if len(r):
            r0 = r.iloc[0]
            print(f"  {y}: median={r0.p50:+.4f}  mean={r0['mean']:+.4f}  "
                  f"p5={r0.p5:+.4f}  p95={r0.p95:+.4f}")


if __name__ == "__main__":
    main()
