# `outputs/` — what's tracked vs. fetched

This directory holds derived data, final figures, and intermediate
ensembles. Only the small derived data and final figures are tracked in
git; the large intermediate ensembles and FaIR cubes are gitignored and
live on Zenodo (see `scripts/download_data.sh`).

## What's tracked in git

| Pattern | What it is | Consumed by |
|---|---|---|
| `outputs/plots/hawkins_sutton_*.csv` | Hawkins-Sutton variance decompositions (year-by-year V_emi / V_clim / V_int / V_brick + percentiles), small | `python/scripts/substack/updated_hawkins_sutton*.py`, `pulse_hawkins_sutton.py` |
| `outputs/plots/gmst_obs_vs_model.csv`, `slr_obs_vs_model.csv` | Pre-computed model–obs comparison series | substack & poster obs-overlay figures |
| `outputs/plots/*.png` | Final variance-decomp panels | Poster Panel C, D |
| `outputs/substack/*.csv` | Figure-input summary CSVs (exceedance tables, crossing years, pulse summaries) | substack figure scripts (one CSV per figure) |
| `outputs/substack/*.png`, `*.pdf` | Final substack figures | Substack post |
| `outputs/poster/*.png` | Final poster panel figures | `python/scripts/poster/layout_mockup.py` (composites them into the layout) |
| `outputs/anova_metadata.csv` | ANOVA factorial metadata (13,500 tuples for total-SLR H-S) | `julia/run_mimibrick_paired_explicit.jl` (Tier 2 re-runs) |
| `outputs/lhs10k_metadata.csv` | LHS-10k triplet metadata (10,000 rows of rff_idx / fair_cfg_idx / seed_idx / post_idx) | LHS-10k BRICK pipeline |
| `outputs/rff_baseline_stoch_to2300_rffs.npy` | RFF IDs used in the production FaIR cube (4 KB) | `python/scripts/build_lhs10k_metadata.py` |
| `outputs/brick_paired_rff_*.csv` (×7) | Legacy 500-cell paired ensembles, used by `pulse_convergence.py` only | `python/scripts/substack/pulse_convergence.py` |

## What's gitignored (fetch via `scripts/download_data.sh`)

| Pattern | Size | Source |
|---|---|---|
| `outputs/rff_*_stoch_to2300.npz` | ~1.9 GB each | Zenodo |
| `outputs/brick_lhs10k_*_to2300_weighted.csv` | ~80 MB each | Zenodo |
| `outputs/brick_anova_long_2300*.csv` | ~50 MB | Zenodo |
| `outputs/brick_anova_pulse_long_2300.csv` | ~50 MB | Zenodo |
| `outputs/brick_anova_marginal_long_2300_weighted.csv` | ~80 MB | Zenodo |
| `outputs/brick_lB_per_post_dangendorf.csv` | 230 KB | Zenodo |

## What's gitignored and not redistributed (rerun to regenerate)

| Pattern | Why excluded |
|---|---|
| `outputs/cross_*.csv` | Diagnostic cross-checks (R&D) |
| `outputs/lhs_pilot_*chunk*`, `*test*` | Pre-production chunk intermediates |
| `outputs/bootstrap_convergence_*.csv` | Diagnostic |
| `outputs/brick_ofat_long.csv` | One-factor-at-a-time sensitivity (superseded by H-S) |
| `outputs/fredi_input_*.csv` | FrEDI integration workstream (separate from SLR figures) |
| `outputs/figure4_gmst*`, `halfdeg_exceedance*` | Deprecated CLI variants |
| `outputs/quarantine/` | Pre-fix outputs archived per CLAUDE.md §"Quarantine bugged outputs" — moved to `../SLR-RFF-BRICK-archive/outputs/quarantine/` before commit |
| `outputs/*.log` | Job logs |

## Regenerating a figure (Tier 1)

The final substack and poster figures all regenerate from the small CSVs
tracked here. No Zenodo download needed.

```bash
# Substack example:
python python/scripts/substack/pulse_hawkins_sutton.py
# Poster example:
python python/scripts/poster/slr_band.py
python python/scripts/poster/layout_mockup.py
```

For Tier 2 (re-running BRICK from FaIR cubes) and Tier 3 (re-running FaIR
from RFF-SP emissions), see the top-level [README.md](../README.md).
