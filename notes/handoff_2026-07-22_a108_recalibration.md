# Handoff — a=1.08 (σ=0.15) recalibration + sub-annual cross-model artifact (2026-07-22)

**Status: 4×2M MCMC chains RUNNING overnight.** Launched ~09:13, ETA ~14–16 h (→ finishes
~23:00–01:00). Everything downstream is wired; this note is the cold-start resume recipe.

## What is running

```
julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 2000000 <seed> \
      --overdisperse --amp-mu=1.08 --amp-sigma=0.15 --tag=extA108
```
4 parallel processes, seeds 2026–2029. Logs in the session scratchpad `a108_seed<seed>.log`.
Output → `outputs/mcmc/chain_extA108_seed<seed>_n2000000.csv`.
Confirmed at launch: `A6 prior: amp ~ N(1.080, 0.150) on [0.630, 1.530]  TAG=extA108`,
acceptance 0.238 (phase-2 was 0.234–0.237).

**Why a full recalibration:** `a` is a sampled parameter and the rest of the AIS block was
tuned against amp≈0.94; swapping the amp column in the existing posterior would not be a
valid posterior. Reused the phase-2 `adapted_cov_ext.csv` + `overdispersed_starts.csv`
(identical parameter set — only the prior changed), so the tuning stage was skipped.

## Decisions already made (do not re-litigate)

1. **Artifact rows (Marcus):** the a=1.08 run **REPLACES** "BRICK-FM · transient"; the old
   **equilibrium row is KEPT** as the sensitivity, so readers can see how much the A6
   decision moves the answer. → 2 BRICK-FM rows.
2. **The sub-annual patch is NOT needed during calibration.** Crossing the DAIS threshold
   needs ΔT_glob ≈ 2.9 K (T_ant = −18.4 + 1.08·ΔT vs threshold ≈ −15.1); the 1850–2026
   fitting window reaches ~1.3 K, so the threshold is never crossed and the patch cannot
   affect the likelihood. Calibrate annual, project sub-annual — no inconsistency.
3. **Equilibrium needs NO recalibration** (same reason). Its sub-annual levels *and* pulses
   are already computed — see `outputs/crossmodel_pulse_means_subannual.csv`.
4. **amp bounds widened to μ±3σ = [0.63, 1.53]** under a prior override; the phase-2
   hi=1.25 would have clipped N(1.08, 0.15) at +1.1σ.

## Resume recipe

```bash
# 0. confirm all four chains landed
ls -l outputs/mcmc/chain_extA108_seed{2026,2027,2028,2029}_n2000000.csv
```
```bash
# 1. deliverable-level convergence diagnostic (writes slr_convergence_extA108.csv)
julia --project=julia_v2 julia/diag_slr_convergence_by_chain.jl --tag=extA108
```
```bash
# 2. accept on the SLR deliverable, write the subsample
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=extA108 --accept-slr
```
→ `data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv`. If the filename comes back
with a `_NOTCONVERGED` suffix, the SLR gate failed — report R̂ and stop, do not paper over it.

```bash
# 3. apply the sub-annual depot patch, then project (script ABORTS if the patch is absent)
chmod u+w ~/.julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl
#   ...apply the `frac` block (see handoff_2026-07-21_crossmodel_artifact.md §4)...
julia --project=julia_v2 julia/diag_subannual_pulse_means.jl
#   ...then RESTORE the depot file from backup and chmod u-w...
```
`diag_subannual_pulse_means.jl` auto-detects the extA108 subsample (`VARIANT_ORDER` =
a108, transient, equilib) and writes level median/mean **and** pulse median/mean for every
variant × driver × horizon to `outputs/crossmodel_pulse_means_subannual.csv`.

```bash
# 4. update + republish the artifact (same URL keeps the link alive)
#    file: FaIRtoFrEDI/magicc_comparison/artifacts/crossmodel_slr_ssp245.html
#    Artifact tool: url=https://claude.ai/code/artifact/7b5f05fe-9d59-49b3-9524-3c99ca605d51
#    favicon 🌊
```

## Artifact edit plan

- `models[]`: rename row 5 `"BRICK-FM · transient" / "CMIP6-transient AIS T"` →
  **`"BRICK-FM" / "a = 1.08 ± 0.15"`**; keep row 6 equilibrium as-is.
- `D.level` and `D.pulse` (med **and** mean): replace the row-5 entries with the new
  a108 numbers; replace the row-6 (equilibrium) entries with its **sub-annual** numbers
  (already in hand, below). FACTS + MAGICC-native rows are unchanged.
- Equilibrium sub-annual numbers (from `crossmodel_pulse_means_subannual.csv`),
  [MAGICC, FaIR]: level med @2100 [64.7, 61.6], mean [65.2, 64.1]; @2150 med [127.4, 123.3],
  mean [121.7, 120.1]. Pulse ×10⁻³ cm/GtCO₂: @2100 med [22.6, 11.3], mean [22.8, 21.0];
  @2150 med [27.5, 16.7], mean [34.7, 31.8].
- **Footnotes need updating**: the pulse-median caveat currently describes the annual-step
  model. Under sub-annual the BRICK pulse *medians* rise 2–4× for the equilibrium
  calibration (the tip channel reaches the median draw, not just the tail) — this is the
  headline change a reader will notice. Levels move <1%.

## Provenance / commits

`ee0685b` wired the recalibration (additive `--amp-mu=/--amp-sigma=/--tag=` overrides on
`calibrate_mcmc_ext.jl`, `--tag=` on `postprocess_mcmc_ext.jl`, extA108 auto-detect in the
projection driver). This commit adds `--tag=` to `diag_slr_convergence_by_chain.jl` and
makes the postprocess `--accept-slr` gate read `slr_convergence_$(TAG).csv` — without these
the gate would have read the *phase-2* diagnostic and refused as stale. All defaults are
unchanged (`TAG` → `"ext"`), so the phase-2 pipeline is bit-for-bit as before.

Rationale for a=1.08 is in `notes/writeup_2026-07-22_a6_amplification_for_tony.{md,pdf}`.
