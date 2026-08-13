# Quarantine 2026-08-13 — the extC vintage, superseded by Ladrillo 1.0 (L10)

## 1. VINTAGE DIFFERENCE, NOT A BUG

Nothing here was computed wrongly. extC was the accepted Ladrillo posterior from
2026-08-10 (commit `205ccbf`) and everything in this directory is a correct
product of it. It is quarantined because L10 replaced it on 2026-08-13 and
leaving these at canonical paths invites silent retrieval of a superseded
vintage. Standing rule: quarantine, never delete.

## 2. What is in here

| file | what it is |
|---|---|
| `ssps_components_2300_extC.csv` | per-component SSP projections, 1990-2300, extC posterior, stock-SIMPLE Greenland |
| `postpred_extC_components_timeseries.csv` | hindcast bands vs targets, 1900-2026 |
| `postpred_extC_bias.csv`, `postpred_extC_coverage.csv` | the bias and coverage tables from the same run |
| `slr_convergence_L10_constamp.csv` | **the original L10 acceptance certificate**, computed CONSTANT-AMP — see §5 |

## 3. The canonical replacement

| superseded | canonical |
|---|---|
| `ssps_components_2300_extC.csv` | `outputs/ssps_components_2300_L10.csv` |
| `postpred_extC_*` | `outputs/postpred_L10_*` |

Both from the L10 posterior
(`data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv`), Greenland A+B with
the amp(GMST) law, written by `julia/project_ssps_components_ladrillo.jl` and
`julia/posterior_predictive_ladrillo.jl`.

## 4. What changed, extC → L10 (medians at 2100, cm)

| ssp | glaciers | gis | ais | te | **total** |
|---|---|---|---|---|---|
| SSP1-2.6 | 8.54 → 9.01 | 6.63 → 6.18 | 4.88 → 4.77 | 13.18 → 12.86 | **35.91 → 35.41** |
| SSP2-4.5 | 10.56 → 11.03 | 7.27 → 8.17 | 11.74 → 5.95 | 17.27 → 16.85 | **49.48 → 45.01** |
| SSP5-8.5 | 14.69 → 15.16 | 8.80 → 13.57 | 45.78 → 37.72 | 25.91 → 25.28 | **97.75 → 94.25** |

Three changes are superimposed and should not be conflated:
1. **a new posterior** (L10: 4 × 2M chains with Greenland A+B inside the joint
   likelihood) — this is what moves the Antarctic;
2. **a new Greenland module** (A+B two-channel on a regional driver, replacing
   stock SIMPLE) — more responsive to scenario;
3. **the amp(GMST) law** on the projection splice — damps that responsiveness,
   hardest where it is largest.

So **Greenland moves in both directions** between the vintages (−0.45 cm at
SSP1-2.6, +4.78 at SSP5-8.5) and "the amp law lowered Greenland" is the wrong
summary. The G4 scenario spread went 2.16 (extC, stock) → 9.80 (A+B, constant
amp) → 7.37 cm (A+B + law) against a 6.3-7.3 evaluation band.

## 5. The constant-amp acceptance certificate

`slr_convergence_L10_constamp.csv` is the file `postprocess_mcmc_ext.jl
--tag=L10 --accept-slr` read when the L10 posterior was accepted. It certified
SLR@2100 R̂ 1.000 / @2150 1.000 — but it was computed with the CONSTANT-AMP
Greenland splice, i.e. before the amp law existed. It is preserved here as the
record of the acceptance decision as actually taken.

`outputs/mcmc/slr_convergence_L10.csv` was regenerated under the law so that the
certificate describes the model that is shipped, and it now carries a
`gis_shape` column so the two cannot be confused on disk again.

## 6. Consumers pinned here rather than migrated

Four scripts read the extC outputs from this directory instead of being pointed
at L10, because each one **describes** the extC vintage — its header, its
argument and its recorded conclusions are about that model. Repointing them at
L10 would make their prose wrong, not update it:

- `scope_greenland_options.py` — the study that SELECTED the A+B module by
  showing why stock SIMPLE under-responds. Its premise is the extC Greenland.
- `scope_greenland_bochow2026.py` — compares the Bochow 2026 tipping emulator to
  "Ladrillo's own Greenland", which at the time was stock SIMPLE. **Re-running
  this against L10's A+B is live work**, not a path edit: it belongs to the
  open thread on what replaces proportional relaxation at high warming.
- `diag_gis_likelihood_leverage.py`, `diag_noise_model_and_grip.py` — calibration
  diagnostics tied to the extC CHAINS as well as its outputs. Re-running them on
  the L10 chains is part of preparing the next calibration.

`diag_mengel_to_ladrillo_attribution.py` reads BOTH quarantines: the attribution
on record is mengel → extC, so both its arms are now archived vintages, which is
correct. The further extC → L10 step is the table in §4.

Migrated to L10 (not pinned): `plot_ladrillo_memo_figures.py`,
`ladrillo_model_comparison.py` — those are live deliverables and now read the
L10 outputs.
