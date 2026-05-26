# L-T → empirical p5/p50/p95 standardization

**Quarantined:** 2026-05-26
**Reason:** Methodological decision to standardize on empirical
importance-weighted p5/p50/p95 for all pulse-marginal SLR figures.

## What was here

`gaussian_vs_empirical_slr.py` plus its PNG/PDF/CSV outputs. The figure
was a substack methodological side-quest demonstrating that:

1. Naive Gaussian summaries (mean ± 1σ) of pulse-marginal SLR are
   misleading because the distribution is bimodal/asymmetric (driven by
   AIS-tipping-state dependence).
2. Even after applying a Lemoine-Traeger correction (centering the
   Gaussian on the mean over the non-tipping subset), the symmetric
   ±1σ band still drifts below zero at long horizons — i.e., the L-T
   correction handles the mean but not the asymmetric spread.

## Why retired

Per the methodological decision on 2026-05-26: empirical p5/p50/p95
quantiles are:

- **Threshold-invariant** — no L-T classifier needed
- **Pulse-size-invariant** — in the small-pulse linear regime (0.01
  GtCO₂) the per-unit percentiles are pulse-size invariant by
  construction
- **Directly answer "likely impact + uncertainty"** without a
  decomposition that requires interpretation

All other pulse figures in the substack/poster pipeline already use
empirical percentiles (pulse_responses_clean, pulse_hawkins_sutton,
slr_band, Panel D inset). This figure was the lone hold-out and is
now redundant.

## Canonical replacement

No direct replacement — the empirical p5/p50/p95 framing is already
in every other pulse-marginal figure. The L-T diagnostic utility lives
on at `python/scripts/lemoine_traeger_decomposition.py` for anyone
revisiting the decomposition.

## Files

- `gaussian_vs_empirical_slr.py` — the script (uses baseline-state
  L-T classifier `ais_2100_cm > 20 cm`, post the 2026-05-26
  classifier standardization)
- `gaussian_vs_empirical_slr.{png,pdf}` — final rendered figure
- `gaussian_vs_empirical_slr_per_year.csv` — per-year table
