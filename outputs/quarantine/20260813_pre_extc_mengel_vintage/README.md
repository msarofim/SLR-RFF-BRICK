# Quarantine 2026-08-13 — the pre-extC BRICK-Mengel projection vintage ("78.02 cm")

## 1. This is a VINTAGE DIFFERENCE, NOT A BUG

Nothing here was computed wrongly. These files are the SSP projection deliverable
of an **earlier calibration of the model**, kept out of the canonical output paths
so that a later reader cannot pick up a superseded projection by filename alone.
They remain the provenance for anything already circulated on those numbers, and
they are the only way to reproduce the vintage comparison in §4.

The standing rule this follows is in `~/.claude/CLAUDE.md`: quarantine, never
delete — pre-change outputs are needed for postmortem, for regression-testing the
change, and for answering "how big was it?", while leaving them at canonical paths
invites silent retrieval.

## 2. What is in here

Everything produced from **`data/MimiBRICK/parameters_subsample_brick_mengel.csv`**
(the 2018-baseline posterior, the "78.02 cm" vintage) and from
**`..._mengel_ext.csv`** (its post-2018-extended sibling), by
`julia/project_ssps_2100_mengel.jl` with TAG "" and "ext" respectively:

| file | posterior | written by |
|---|---|---|
| `proj_ssps_mengel_summary.csv` | `..._brick_mengel.csv` | `project_ssps_2100_mengel.jl` |
| `proj_ssps_mengel_timeseries.csv` | `..._brick_mengel.csv` | same |
| `proj_ssps_mengel_components_timeseries.csv` | `..._brick_mengel.csv` | same |
| `proj_ssps_mengel_run.log`, `..._components_run.log` | `..._brick_mengel.csv` | same |
| `proj_ssps_mengel_ext_{summary,timeseries}.csv`, `..._ext_run.log` | `..._brick_mengel_ext.csv` | same, TAG=ext |
| `ssp_projections_2100_mengel{,_ext}.png` | as above | `python/plot_ssp_projections_mengel.py` |

## 3. The canonical replacement

**`outputs/ssps_components_2300_L10.csv`** — Ladrillo 1.0, posterior
`data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv` (accepted on the
deliverable 2026-08-13), Greenland A+B with the amp(GMST) law, written by
`julia/project_ssps_components_ladrillo.jl`. Hindcast counterpart:
`outputs/postpred_L10_*`.

## 4. How big the difference is, and where it lives

SSP2-4.5 medians at 2100 (cm), this vintage → extC → L10:

| component | mengel (here) | extC | L10 (canonical) |
|---|---|---|---|
| Antarctic | 43.05 | 11.74 | 5.95 |
| glaciers | 6.27 | 10.56 | 11.03 |
| Greenland | 7.42 | 7.27 | 8.17 |
| thermal expansion | 18.45 | 17.27 | 16.85 |
| **total** | **78.02** | **49.48** | **45.01** |

**The Antarctic is the whole story** (110% of the mengel→extC shift; glaciers
partly offset it). And the shift is **not a level shift**: it is −0.01 cm at
SSP1-2.6 and −28.54 at SSP2-4.5, because what changed is the **probability of
Antarctic tipping by 2100**, not the contribution conditional on tipping. The
distribution is bimodal and the movement sits at a different quantile in every
scenario.

Two consequences that survive into the canonical vintage:
- **"BRICK-F* is 28 cm lower at SSP2-4.5 2100" is a misleading sentence** and
  should not be written. Quote a distribution, not a median.
- The largest movement in the programme lives in the **least data-constrained**
  part of the posterior: the AIS block is where `ais_iceflow0` sits at R̂ 2.359
  in L10, and the SSP2-4.5 p83 was already recorded as prior- rather than
  data-driven by the 2026-08-11 red team.

Greenland is *untouched* by this vintage step (−0.15 cm mengel → extC); its own
change arrives later, with the A+B module and the amp law.

## 5. What was deliberately NOT quarantined

- **The MAGICC-comparison and CO2/CH4 pulse study outputs**
  (`proj_magicc_hybrid_ssp245_mengel_*`, `proj_matched_ssp245_mengel_*`, the
  pulse pair files). These also run on `..._brick_mengel.csv`, but they are
  deliverables of a **study about that model version**, not superseded
  projections of the current one — and the Mengel model is canonical in its own
  right in the MimiBRICK-FM repo. Quarantining them would misfile them.
- **The extC-vintage outputs** (`ssps_components_2300_extC.csv`,
  `postpred_extC_*`). They ARE superseded by L10, but five live consumers still
  read them (`plot_ladrillo_memo_figures.py`, `ladrillo_model_comparison.py`,
  `diag_gis_likelihood_leverage.py`, `diag_noise_model_and_grip.py`,
  `scope_greenland_*.py`). Migrating those to the L10 outputs changes every
  number in the memo figures and is its own reviewed piece of work; moving the
  files first would just break the pipeline. **That migration is the open item** —
  until it is done, `_extC` outputs are live inputs, not archive.

## 6. Consumers repointed at this directory

`python/diag_mengel_to_ladrillo_attribution.py` and
`python/plot_ssp_projections_ext_compare.py` legitimately read this vintage — they
are cross-vintage comparisons — and now read it from here.
