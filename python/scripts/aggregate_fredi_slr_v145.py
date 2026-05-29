"""
aggregate_fredi_slr_v145.py
===========================

v1.4.5 version of the legacy `aggregate_fredi_slr.py` in
SLR-RFF-BRICK-archive: takes the long-format output of
`R/run_fredi_slr_phaseC_baseline_v145.R` (one row per
(draw_idx, sector, variant, impactType, year)) and computes
importance-weighted (or, here, uniformly-weighted since the inputs are
SIR-resampled) distributions of national coastal damages.

Inputs:
    outputs/fredi_slr_phaseC_rff_baseline_v145_long.csv
       columns: draw_idx, sector, variant, impactType, year,
                annual_impacts, driverValue, w_norm
    (w_norm = 1/N uniformly; SIR resample upstream already absorbed the
     importance weights into the draw selection.)

Outputs:
    outputs/fredi_slr_phaseC_rff_baseline_v145_quantiles.csv
       columns: sector, variant, year,
                P5, P25, P50, P75, P95, mean, ESS_eff, N

Plus a printed summary table for headline years (2050, 2100, 2150, 2300).
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
HEADLINE_YEARS = [2050, 2075, 2100, 2125, 2150, 2200, 2250, 2300]

# Default tag = v145 (single-seed LHS-10k). Override via env var to point at
# the v5 noise-isolated ensemble: FREDI_TAG=v145_lhs10ks.
TAG      = os.environ.get("FREDI_TAG", "v145")
LONG_CSV = OUT / f"fredi_slr_phaseC_rff_baseline_{TAG}_long.csv"
OUT_CSV  = OUT / f"fredi_slr_phaseC_rff_baseline_{TAG}_quantiles.csv"


def weighted_quantile(values, weights, q):
    mask = np.isfinite(values) & np.isfinite(weights) & (weights >= 0)
    v = np.asarray(values[mask], dtype=float)
    w = np.asarray(weights[mask], dtype=float)
    if len(v) == 0 or w.sum() == 0:
        return np.nan
    s = np.argsort(v)
    v, w = v[s], w[s]
    cw = np.cumsum(w)
    return float(v[np.searchsorted(cw, q * cw[-1])])


def ess(weights):
    w = np.asarray(weights, dtype=float)
    w = w[np.isfinite(w) & (w >= 0)]
    if w.sum() == 0:
        return 0.0
    return float((w.sum() ** 2) / (w ** 2).sum())


def main():
    if not LONG_CSV.exists():
        sys.exit(f"Long CSV not found: {LONG_CSV}")
    df = pd.read_csv(LONG_CSV)
    print(f"Loaded {len(df):,} rows from {LONG_CSV.name}")
    print(f"  sectors:  {df['sector'].unique().tolist()}")
    print(f"  variants: {df['variant'].unique().tolist()}")
    print(f"  draws:    {df['draw_idx'].nunique()}")
    print(f"  year range: {df['year'].min()}-{df['year'].max()}")

    rows = []
    for (sec, var), g in df.groupby(["sector", "variant"]):
        for yr, gy in g.groupby("year"):
            v = gy["annual_impacts"].to_numpy()
            w = gy["w_norm"].to_numpy()
            rows.append({
                "sector":   sec,
                "variant":  var,
                "year":     int(yr),
                "P5":       weighted_quantile(v, w, 0.05),
                "P25":      weighted_quantile(v, w, 0.25),
                "P50":      weighted_quantile(v, w, 0.50),
                "P75":      weighted_quantile(v, w, 0.75),
                "P95":      weighted_quantile(v, w, 0.95),
                "mean":     float(np.average(v[np.isfinite(v)],
                                              weights=w[np.isfinite(v)])
                                  if np.isfinite(v).any() else np.nan),
                "ESS_eff":  ess(w),
                "N":        int(np.isfinite(v).sum()),
            })

    out_df = pd.DataFrame(rows).sort_values(["sector", "variant", "year"]).reset_index(drop=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name} ({len(out_df):,} rows)")

    # Headline preview
    hl = out_df[out_df["year"].isin(HEADLINE_YEARS)].copy()
    for c in ["P5", "P25", "P50", "P75", "P95", "mean"]:
        hl[c] = hl[c] / 1e9   # USD → USD billions
    print("\n=== Headline annual coastal damages, weighted (USD BILLION) ===")
    with pd.option_context("display.max_rows", 200,
                           "display.float_format", "{:.2f}".format,
                           "display.width", 200):
        print(hl[["sector", "variant", "year",
                  "P5", "P25", "P50", "P75", "P95", "mean", "N"]]
              .to_string(index=False))


if __name__ == "__main__":
    main()
