# 20260930_gis_matched_targets_calib145 — the Greenland matched 2300 targets on calib 1.4.5

## 1. Why these files are here

These files are **not bugged**. They are a consistent calib 1.4.5 record: a model driven
by calib 1.4.5 forcing, scored against targets derived at calib 1.4.5.

They were retired because the default moved. Marcus ruled on 2026-09-30 that every paper
calculation and every future calculation is **FaIR 2.2.4 calib 1.6.0**. The forcing
files moved to calib 1.6.0 on 2026-08-28 (commit `839a176`), but the matched targets were
never re-derived. Any re-run after that date therefore scored a 1.6.0 model against 1.4.5
targets. That mismatch was measured to put a verdict on the wrong side of 1: the cell-B
flux ratio was 0.97 as shipped, 1.07 mismatched, and 0.83 like-for-like.

For the measurement and decision, see `notes/proposal_2026-09-30_gis_matched_targets_calib160.md`.

The target tables here are **still read** by `python/gis_targets.py`, as its
`MATCHED_2300_M_BY_CALIB["1.4.5"]` set. Its literals are verified against
`gis_matched_targets_2300.csv` in this directory at import. The frozen consumers in §3
score against this set. Do not delete these files.

## 2. What is here → the canonical calib 1.6.0 replacement

**Targets.** `gis_matched_targets_2300.csv` rebuilds byte-for-byte from
`git show 839a176^:data/observations/fair_mean_gmst_<ssp>.csv`.

| file here (calib 1.4.5) | canonical calib 1.6.0 replacement |
|---|---|
| `gis_matched_targets_2300.csv` | `outputs/gis_matched_targets_2300.csv` (now carries `calib` + `provenance`) |
| `scope_gis_cool_band_targets.csv` | `outputs/scope_gis_cool_band_targets.csv` (same) |
| `scope_gis_cool_band_forcing.csv` | `outputs/scope_gis_cool_band_forcing.csv` |
| `log_build_gis_matched_targets.txt`, `log_scope_gis_cool_band_forcing.txt` | same names in `outputs/` |

**Consumers re-run on calib 1.6.0.** For each consumer, its pre-09-30 output and log
moved here under the same basename, and the replacement sits at the original path.
`.rerun_map.txt` lists script → output → log:

- `scope_gis_leq_ridge_vs_literature_matched.csv`
- `scope_gis_rate_power_vs_literature_matched.csv`
- `scope_gis_reservoir_offline_tolspread.csv`
- `scope_gis_gamma_offline.csv`
- `scope_gis_onset_rescan.csv`
- `diag_gis_cell_vs_priority_ladder.csv` (Julia)
- `diag_gis_matched_band_score.csv`
- `diag_gis_amp_above_275.csv`
- `diag_gis_cascade_rate_crit.csv`
- `diag_gis_k_vs_residual.csv`
- `diag_gis_residual_band.csv`
- `diag_gis_scorecard_logo.csv`
- `diag_gis_separation_target.csv`

`scope_gis_3basin_partition_matched.csv` and `scope_gis_tap_l13_matched.csv` had never
been written before; they are new, with nothing quarantined.

Reproducibility caveats on the quarantined consumer outputs, all measured on the
original forcing:
- `diag_gis_residual_band.csv`, `diag_gis_scorecard_logo.csv` and
  `diag_gis_cell_vs_priority_ladder.csv` did **not** reproduce byte-for-byte from the
  09-30 code even on 1.4.5 forcing.
- The Julia ladder's difference is kernel drift since 08-23, at most 1.2 cm.

## 3. NOT moved: consumers FROZEN at calib 1.4.5

These consumers were left in place and labelled instead. Each declares
`gis_targets.frozen(__name__, "1.4.5", reason)`. Run as a script on today's forcing, it
refuses with its reason. Their outputs are the calib 1.4.5 record and stay at their
paths.

| script | why it cannot be re-run on 1.6.0 |
|---|---|
| `scope_gis_basin_mock_vs_literature.py` | GMT frame check recorded on 1.4.5 forcing (gated) |
| `scope_gis_basin_zonespace_vs_literature.py` | same (gated) |
| `scope_gis_ridge_vs_ssp_bands.py` | gated against the calib 1.4.5 L14 projection. Its matched output was **renamed** `outputs/scope_gis_ridge_vs_ssp_bands_matched_calib145.csv` (+ log). |
| `plot_gis_basin_mock.py` | renders the frozen basin_mock output |
| `diag_gis_npv_tau_sensitivity.py` | reads `ssps_components_2300_L14.csv` (calib 1.4.5, not re-projected) |
| `diag_gis_2150_band_veto.py` | reads the calib 1.4.5 `--wide-v` scan and carries the 1.4.5 base (49.9 cm). Its p50 now comes from the 1.4.5 set explicitly. |
| `scope_gis_reservoir_rate_rank.py` | its repro gate is pinned to the 1.4.5-era scan (135/86) and fails even on 1.4.5 |

Marcus, 2026-09-30: old Ladrillo versions (L12/L14) are not to be re-projected on 1.6.0.
