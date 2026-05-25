# Pre-v1.4.5 BRICK weighted CSVs (quarantined)

Quarantined 2026-05-24 because these outputs were produced under the
**FaIR v1.4.1 posterior** (Smith et al. 2024) and the **pre-PR#93 BRICK
posterior** (Wong et al. 2017 calibration, `b > v0` in 97.6% of draws).
Both have been superseded:

- FaIR: **v1.4.1 → v1.4.5** (recommended by Zeke Hausfather 2026-05-22; closes
  the IGCC 2024 anchor gap from −0.30 °C to −0.08 °C).
- BRICK posterior: pre-PR#93 → **post-PR#93 joint** (delivered by Tony Wong
  2026-05-22; matches Frederikse 2020 GIS hindcast back to 1900).

## Files quarantined

| File | What it was |
|------|-------------|
| `brick_lhs10k_baseline_to2300_weighted.csv` | LHS-10k baseline, v1.4.1 + pre-PR#93 |
| `brick_lhs10k_pulse0p01gtc_to2300_weighted.csv` | LHS-10k 0.01-GtC CO₂ pulse |
| `brick_lhs10k_pulse_to2300_weighted.csv` | LHS-10k 1-GtC CO₂ pulse |
| `brick_anova_long_2300.csv` | 13,500-row ANOVA factorial baseline (unweighted) |
| `brick_anova_long_2300_weighted.csv` | Same, Wong-weighted (legacy ESS = 7,037) |
| `brick_anova_pulse_long_2300.csv` | ANOVA 1-GtC CO₂ pulse (paired) |
| `brick_anova_marginal_long_2300_weighted.csv` | ΔSLR per (rff, cfg, seed, post) tuple |

## Canonical replacements

Located at `outputs/brick_v145_slim/`:

| Replacement | Notes |
|-------------|-------|
| `brick_lhs10k_baseline_to2300_weighted.csv` | LHS-10k baseline, v1.4.5 + post-PR#93 (ESS = 3,815 / 10,000 = 38.1%) |
| `brick_lhs10k_pulse_co2_pos_001gt_to2300.csv` | LHS-10k 0.01-GtC CO₂ pulse |
| `brick_lhs10k_pulse_co2_pos_1gt_to2300.csv` | LHS-10k 1-GtC CO₂ pulse |
| `brick_anova18k_baseline_to2300_weighted.csv` | ANOVA-18k baseline (54,000 rows; ESS = 16,068 / 54,000 = 29.8%) |
| `brick_anova18k_pulse_co2_pos_1gt_to2300.csv` | ANOVA-18k 1-GtC CO₂ pulse |

CH₄ pulse arms (`pulse_ch4_{pos,neg}_{001tg,1tg}`) and small-pulse
companions also exist in the v145 slim directory for future use.

## Why both v1.4.1 and v1.4.5 era files matter for postmortem

The v1.4.1 era files can answer "how much of the v145-released numbers'
shift vs. AGU Chapman poster comes from the FaIR-calibration update vs.
the BRICK-posterior update?" See memory entries
`project_fair_calibration_version_check`,
`project_brick_post_pr93_posterior_installed`, and
`project_v145_workflow_built` for the analytical decomposition done
2026-05-22.

## Related quarantine

`data/MimiBRICK/quarantine/20260524_pre_pr93/parameters_subsample_brick.csv`
holds the pre-PR#93 BRICK posterior that produced the quarantined CSVs
above.
