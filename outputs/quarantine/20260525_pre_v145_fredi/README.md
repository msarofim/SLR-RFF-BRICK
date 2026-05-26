# Pre-v1.4.5 FrEDI phaseC outputs

**Quarantined:** 2026-05-25
**Reason:** Superseded by v1.4.5 calibration + post-PR#93 BRICK posterior rerun.

## Files

- `fredi_input_rff_baseline_gmst.csv` — v1.4.1-era 500-cell paired GMST input
  (May 14 snapshot). FaIR-mean baseline subtraction = 0.5545 °C (1986-2005
  from v1.4.1 ensemble).
- `fredi_input_rff_baseline_slr.csv` — v1.4.1-era 500-cell paired BRICK SLR
  input (May 18 snapshot). Pre-PR#93 BRICK posterior.
- `fredi_slr_phaseC_rff_baseline_long.csv` — FrEDI sector damages, national,
  from the inputs above.
- `fredi_slr_phaseC_rff_baseline_state_long.csv` — same, per-state.
- `fredi_slr_phaseC_rff_baseline_quantiles.csv` — weighted quantiles.

## Why quarantined, not deleted

Per the user-CLAUDE.md convention: pre-fix outputs are kept for
postmortem, regression-testing the rerun, and answering reviewer
questions about the size of the change between v1.4.1 (pre-PR#93) and
v1.4.5 (post-PR#93). The figures these drove on the 2026-05-20 AGU
Chapman poster handoff (Panels F and H) are documented at
`outputs/poster/iec_graphics_handoff/panels/F_damage_function_methodology.pdf`
and `H_coastal_property_and_htf_damages.pdf`.

## Canonical post-fix replacements

`outputs/fredi_input_rff_baseline_gmst_v145.csv`
`outputs/fredi_input_rff_baseline_slr_v145.csv`
`outputs/fredi_slr_phaseC_rff_baseline_v145_long.csv`
`outputs/fredi_slr_phaseC_rff_baseline_v145_state_long.csv`
`outputs/fredi_slr_phaseC_rff_baseline_v145_quantiles.csv`

The v1.4.5 rerun uses N=1,000 stratified-by-weight (SIR) draws from
the v1.4.5 LHS-10k baseline ensemble (vs. 500 paired draws in v1.4.1).
