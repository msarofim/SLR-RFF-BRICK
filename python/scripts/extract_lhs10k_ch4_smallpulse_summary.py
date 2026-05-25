"""
extract_lhs10k_ch4_smallpulse_summary.py
========================================

CH₄ analog of extract_lhs10k_smallpulse_summary.py: build the
co2_pulse_slr_summary-style per-year envelope CSV for the v1.4.5
LHS-10k paired (baseline, 0.01-Tg CH₄ pulse) ensemble.

Output schema matches the legacy ch4_pulse_slr_summary_<size>tg.csv used
by python/scripts/substack/pulse_responses_clean.py:
  year, mean, p5, p50, p95   (cm per Tg CH₄, Wong-weighted)

The downstream pulse_responses_clean.py panel scales these by
TG_CH4_PER_GTCO2EQ = 1000 / 27.9 = 35.84 (AR6 WG1 GWP100, midpoint
between fossil and non-fossil) to produce cm per GtCO₂eq.

FaIR v1.4.5's 'CH4' species input_unit is "Mt CH4 / yr". The v1.4.5 cube
builder applies `--pulse-size 0.01` to that emission grid, which is
0.01 × 1000 = 10 Mt CH4 = 0.01 Tg CH4 pulse. Per-Tg-CH4 = ΔSLR / 0.01.

Companion to the CO₂ extract.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

# v1.4.5 inputs (slim, post-PR#93 BRICK + 10k-RFF LHS).
BASELINE_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"
PULSE_CSV    = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_pulse_ch4_pos_001tg_to2300.csv"
OUT_CSV      = OUT / "ch4_pulse_slr_summary_lhs10k_0p01tg.csv"

# FaIR v1.4.5 'CH4' input unit is Tg CH4/yr.  See
# ~/.claude/skills/climate-modeling §"Unit checks" for the corresponding
# CO2-vs-GtC discussion; CH4 has its own subtlety (Mt vs Tg).
PULSE_SIZE_TG_CH4 = 0.01    # FaIR v1.4.5 CH4 input unit
PLOT_YEARS        = (2025, 2300)


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
    print(f"loading baseline + 0.01-Tg-CH4 pulse weighted CSVs")
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
    M         = (Yp - Yb) / PULSE_SIZE_TG_CH4                  # per-Tg-CH4 marginal
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

    print("\nKey small-pulse CH4-SLR sensitivities (cm per Tg-CH4, Wong-weighted):")
    for y in (2030, 2050, 2075, 2100, 2125, 2150):
        r = df[df.year == y]
        if len(r):
            r0 = r.iloc[0]
            print(f"  {y}: median={r0.p50:+.4f}  mean={r0['mean']:+.4f}  "
                  f"p5={r0.p5:+.4f}  p95={r0.p95:+.4f}")

    # Convert to per-GtCO2eq using AR6 GWP100 = 27.9 for a quick sanity check.
    # (downstream pulse_responses_clean.py applies the conversion itself.)
    TG_CH4_PER_GTCO2EQ = 1000.0 / 27.9
    print(f"\nAs cm per GtCO₂eq (× {TG_CH4_PER_GTCO2EQ:.2f} via AR6 GWP100 = 27.9):")
    for y in (2050, 2100, 2125, 2150):
        r = df[df.year == y]
        if len(r):
            r0 = r.iloc[0]
            print(f"  {y}: median={r0.p50 * TG_CH4_PER_GTCO2EQ:+.4f}  cm/GtCO₂eq")


if __name__ == "__main__":
    main()
