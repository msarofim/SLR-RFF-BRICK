# Handoff — Upstreaming BRICK-FM into Tony's MimiBRICK.jl (fork + 2 PRs) (2026-06-21)

## Context
Tony Wong (raddleverse) endorsed contributing the FM/Mengel work back via the
normal fork→branch→PR route: *"the easiest way to integrate changes into the
MimiBRICK repo and keep the party going will be if you're able to make a branch
or fork, and then reincorporate your modification from there."* Marcus's account
`msarofim` has **pull-only** access to `raddleverse/MimiBRICK.jl`, so a direct
branch there is impossible — hence the fork.

Plan (Marcus + Tony 2026-06-21): **TWO PRs** —
1. **Mengel-only** (small, mergeable): the Mengel-2016 glacier emulator as an
   OPTIONAL alternative to the default GSIC.
2. **Full FM** ("latest and greatest"): Mengel + FaIR v2.2 ocean-heat driving +
   updated/additional calibration datasets + recalibration. Tony: *"FaIR v2.2 has
   ocean heat, so seems like a good version… use the latest and greatest, probably
   with the additional/updated calibration data sets."*

## DONE
- **Fork created:** `github.com/msarofim/MimiBRICK.jl` (fork of
  `raddleverse/MimiBRICK.jl`, public). Cloned to
  `~/Documents/2026/CodeProjects/MimiBRICK.jl` (`origin`=fork, `upstream`=Tony).
- **Branch `mengel-glaciers`** (PR 1) checked out.
- **PR 1 port IN PROGRESS** (sub-agent): add `src/components/glaciers_mengel_component.jl`
  as an optional component, wired into `src/create_models/{BRICK_DOECLIM,SNEASY_BRICK}.jl`
  via a `glacier_model::Symbol=:gsic` kwarg (`:mengel` swaps it in); default
  bit-identical to upstream. Verification = construct+run default vs :mengel,
  confirm glacier SLR differs and the rest is unchanged. NOT pushed yet (review first).

## KEY STRUCTURAL FACT
The standalone `msarofim/MimiBRICK-FM` repo is **fresh-history** (not a fork of
MimiBRICK.jl) with a research-driver layout (`julia/`, `python/`, `outputs/`), so
it CANNOT PR into Tony's repo. The PRs must be built on the FORK (shared history +
package layout `src/components/`, `src/create_models/`). "Reincorporate the
modifications" = port the FM code from `MimiBRICK-FM/julia/*` onto the fork's src tree.

## FM SOURCE → FORK MAPPING (what goes where)
FM code at `~/Documents/2026/CodeProjects/MimiBRICK-FM/julia/`:
| FM file | role | fork destination / PR |
|---|---|---|
| `glaciers_mengel_component.jl` (62 ln) | Mengel emulator component | `src/components/` — **PR 1 + 2** |
| `brick_mengel.jl` (81 ln) | model builder wiring Mengel in | informs the create_models wiring — PR 1 + 2 |
| `demo_drive_with_fair.jl` (117 ln) | drive BRICK from external GMST+OHC (FaIR) | the FaIR-driving interface — **PR 2** |
| `calibrate_mcmc.jl` (155 ln), `calibrate_mcmc_ext.jl`, `postprocess_mcmc*.jl`, `posterior_predictive_ext.jl` | MCMC recalibration | `calibration/` — **PR 2** (decide what's package-appropriate vs research) |
| `project_ssps_2100_mengel.jl`, `brick_param_updates.jl` | analysis drivers | likely NOT upstream (research) |

Upstream model assembly lives in `src/create_models/BRICK_DOECLIM.jl` +
`SNEASY_BRICK.jl`; components in `src/components/`; main in `src/MimiBRICK.jl`.

## PR 2 (full FM) — PLAN + OPEN DECISIONS
Branch: `brick-fm` (off `master`, or stacked on `mengel-glaciers` once PR 1 settles).
Contents:
1. **Mengel component** (from PR 1).
2. **FaIR v2.2 ocean-heat driving interface.** Port the external-forcing driver
   (`demo_drive_with_fair.jl` + the obs-driven interface that already exists in
   SLR-RFF-BRICK `julia/run_mimibrick_obs_driven.jl`): drive BRICK's
   `global_surface_temperature` + thermal-expansion `ocean_heat_interior` from an
   external GMST(°C, rel 1850-1900) + OHC(1e22 J stock) time series. NB the OHC
   unit/stock conventions (memory `project_magicc_comparison` "KEY units" — ZJ=1e21,
   ×0.1 to BRICK's 1e22 J; stock since 1750). FaIR 2.2 emits OHC directly (Tony's
   point) so no flux-integration needed.
3. **Updated/additional calibration datasets** — Tony wants the "latest and
   greatest." Candidates already assembled in the FM/SLR-RFF-BRICK work: Dangendorf
   2024 GMSL, Frederikse 2020 components, IGCC 2024 + Gouretski OHC (Cheng is the
   low-side outlier), GRACE-FO AIS/GIS, GlaMBIE GSIC, NOAA steric/STAR (post-2018
   extension). **DECISION (Marcus + Tony): which datasets go into the upstream PR**
   — full post-2018 multi-component extension, or a conservative subset? See memory
   `project_brick_mengel_post2018_extension`, `project_obs_data_sources`,
   `obs-model-comparisons` skill.
4. **Recalibration machinery** — decide what belongs in core `calibration/` vs stays
   research. The Mengel MCMC recalibration (4×500k, 27/28 R̂<1.05) is in the FM repo.

OPEN DECISIONS for Marcus/Tony:
- PR 2 stacked on PR 1, or independent?
- Which calibration datasets + which BRICK base version ("latest and greatest" =
  current upstream master + Mengel, or the BRICK 2.0 the FM was built on?).
- How much recalibration code is package-appropriate vs research-only.
- Posterior parameter files: the FM Mengel posterior
  (`parameters_subsample_brick_mengel.csv`) — ship a subsample with the package?

## NEXT STEPS
1. Review the sub-agent's PR-1 diff; verify default unchanged + :mengel runs; push
   `mengel-glaciers` to the fork; open PR 1 to `raddleverse/MimiBRICK.jl:master`
   (only when Marcus says go — outward-facing).
2. Scope PR 2 with Marcus/Tony (decisions above); build `brick-fm` branch.
3. The fork's Julia env must be instantiated for verification (`julia --project=.`
   in the fork; deps incl. Mimi, MimiSNEASY, RobustAdaptiveMetropolisSampler).

## DO NOT
- Do NOT push to `raddleverse/MimiBRICK.jl` (pull-only; and outward-facing).
- Do NOT auto-open PRs without Marcus's explicit go.
- The standalone `MimiBRICK-FM` repo stays as-is (provenance / collaborator-facing);
  the upstream contribution is the fork, not that repo.
