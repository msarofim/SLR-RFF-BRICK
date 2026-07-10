# Handoff 2026-07-09 — CH4/CO2 pulse → SLR paper plan (BRICK-FM coming-out paper)

## 1. What this is

Plan for a paper whose scientific core is the **relative sea-level-rise impact of CH4
vs CO2 emission pulses**, and which doubles as the **introduction/"coming-out" paper for
BRICK-FM** (the FaIR-driven, Mengel-glacier, recalibrated BRICK fork). Two workstreams
feed it:

1. **BRICK-FM v-next** — an updated model version with a proper recalibration
   (Smith 2024 emissions fix for the near-history observational discrepancy, freed
   AIS parameters, plus other straightforward improvements) BEFORE the paper's
   production runs.
2. **Cross-model comparison** — MAGICC (largely done, Phase 2 in flight) and
   FACTS2.0 (install now due; scoping complete).

Roles per standing convention: **Marcus drafts all main text**; Claude produces
figures, tables, methods sections, captions, reference compilation, and verified
numbers.

## 2. Assets already in hand

**Pulse → SLR results (FaIR → BRICK):**
- CO2 pulse × 3-BRICK study COMPLETE (SLR-RFF-BRICK, archived `brick-mengel` branch,
  commits 0a8a552/1e008fb). Weighted-median Total SLR @2100 per GtCO2:
  pre-#93 1.15e-2 / BRICK2.0 5.36e-3 / Mengel 4.69e-3 cm. Pre-#93 GIS-driven response
  is pathology; Mengel is AIS-led with a fat tipping tail. Pipeline + sanity tests
  documented in memory `project_co2ch4_pulse_3brick_plan`.
- CH4 pulses: marginal linear at 1 Tg; CH4→CO2 **oxidation harmonisation** built
  (biogenic 27 / fossil 29.8 molar-mass bookkeeping; FaIRtoFrEDI commit 05e77b8).
  Fossil-CH4 arm still to add on the FaIR→BRICK RFF side.
- Cross-gas figures exist: 4-panel GMST (e79bdd0) and SLR **per-actual-tonne
  (no-GWP)** (e1d38a3) — the no-GWP framing is a likely paper centerpiece.

**MAGICC comparison (FaIRtoFrEDI repo, `magicc_comparison/`):**
- Tracks A/B/C DONE (memory `project_magicc_comparison`): Track C hybrid proved the
  scenario-level SLR gap (@2100 SSP2-4.5: MAGICC-native 53 cm vs BRICK-Mengel 78 cm)
  is the **emulator, not the climate forcing**.
- **Level-vs-marginal inversion** — the paper's key comparison hook: BRICK-Mengel runs
  higher in scenario level (AIS median ~43 cm vs MAGICC-Nauels ~11 cm @2100
  SSP2-4.5) but MAGICC's AIS **marginal T-sensitivity is ~6× higher** — directly
  determines pulse results. Documented in the fork's `docs/brick_fm_*` files.
- Phase 1 SSP2-4.5 pulse study + CH4 pulses committed
  (`notes/handoff_2026-06-19/20/21_magicc_pulse_*.md` in FaIRtoFrEDI).
- Phase 2 (RFF-SP pulses, ~10k MAGICC runs mirroring the FaIR LHS pairing): builder +
  302c runner committed, **N=5 smoke test passed** (ed1910d). Plan:
  `FaIRtoFrEDI/notes/handoff_2026-06-21_rffsp_phase2_plan.md`.

**BRICK-FM state (msarofim/MimiBRICK.jl fork, branch `brick-fm` @ 30948fa):**
- PR1 (Mengel component only) = raddleverse/MimiBRICK.jl#111, visible to Tony.
- PR2 (full FM: Frederikse 2020 + Dangendorf 2024 targets, post-2018
  GRACE-FO/GlaMBIE/NOAA extension, FaIR-driven calibration, freed
  `ais_ocean_temperature₀`, `:mengel` + `lws=:central` defaults,
  `update_brick_mengel_params!`, custom-forcing example notebook) — pushed, red-teamed,
  ready for Tony's review.
- Calibration: RAM MCMC, 28 free params (18 physical + 10 AR(1) noise), 4×500k,
  27/28 R̂<1.05 (straggler `rho_ais`, nuisance, accepted).
- Docs: `docs/brick_fm_changes_and_rationale.md` (7 changes + 6 priority-ordered
  future targets), `docs/brick_fm_obs_discrepancies.md`, `docs/calibration_guide_mengel.md`.

## 3. BRICK-FM v-next — pre-paper model update

Priority-ordered (tracks the rationale doc's future-targets section):

1. **Smith 2024 emissions splice (fixes the near-history discrepancy).** The FaIR
   calibration mean runs ~0.1 °C below IGCC @2024 because the forcing is
   SSP2-4.5-shaped post-2015, not observed emissions → GIS undershoot ~0.5–1 cm,
   total GMSL slightly low vs Dangendorf. Fix: re-run the FaIR v2.2 mean with Smith
   2024 observed-historical emissions spliced to scenario at 2021 (same splice already
   standard in the v1.4.5 pipeline), regenerate `data/observations/fair_mean_{gmst,ohc}.csv`,
   re-run the MCMC. No model-code changes.
2. **Free more Antarctic parameters.** FM freed `ais_ocean_temperature₀` but fixed the
   AIS geometry set (slope, bed height, flow₀, runoff height₀, precip₀, c, μ) at prior
   medoids. v-next should free some/all with an identifiability strategy — options:
   informative priors centered on the FM posterior; Bedmap-derived physical
   regularization; or reparameterize to fewer identifiable combinations. Highest
   science value for the AIS-led pulse tail.
3. **Reconcile the IMBIE/Dyurgerov point terms — REQUIRED before recalibration.**
   Discrepancy found 2026-07-09: the fork's `calibrate_mcmc_mengel.jl` includes both
   Gaussian point constraints unconditionally (lines ~184–185), but the SLR-RFF-BRICK
   ext refit that produced the shipped posterior **dropped both** (extended series
   constrain the modern rate instead; memory `project_brick_mengel_post2018_extension`).
   Re-running the fork script as-is will NOT reproduce the shipped posterior. Decide:
   drop (match ext) or keep-with-corrected σ. Related TODO already in the code:
   `IMBIE_SIG = 0.156` looks ~2.5× too tight vs IMBIE-2023 (Otosaka: 2720±1390 Gt →
   σ≈0.38 cm at 1σ).
4. **TE overshoot (+0.51 cm vs NOAA steric @2025, structural).** Candidate fix folded
   into the recalibration: extend the OHC target pre-1971 via a Zanna-2019 splice
   (`ohc_spliced_zanna_igcc.csv` pattern exists) or richer TE parameterization.
   Moderate effort; may partially resolve itself with item 1.
5. **FaIR-config-aware calibration (from 2026-07-09 discussion).** Current calibration
   conditions on the FaIR *mean*; the 841-config spread enters only at projection.
   Options discussed, in ascending cost:
   - **(a) Post-run importance weighting (Tony-style)** — reweight each posterior draw
     by its likelihood under each FaIR config's historical trajectory. N_post × 841
     BRICK runs ≈ hours on one node. Likely near-uniform weights if historical-window
     spread is small — cheap to test first.
   - **(b) Per-config MCMCs on a stratified subset** (~50–100 configs across the ECS
     range), importance-weight back to 841. ~10× cheaper than full.
   - **(c) Full 841 per-config MCMCs** (~8.4k core-hours; SLURM array, days on Torch).
   Key simplification (Marcus): FaIR has no feedback from BRICK → all 841 historical
   trajectories are pre-computed ONCE; per-config MCMC cost is BRICK-only.
   Recommend (a) as a scoping test; escalate only if weights are far from uniform.
6. **Small items:** DOECLIM `heat_interior` plumbing bug already fixed in the fork
   (flag upstream to Tony — also present in raddleverse BRICK 2.0; harmless to all
   standard entry points). LWS stays `:central`. Posterior for all production runs =
   full MCMC subsample, never MAP (decision 2026-07-09).

## 4. Comparison plan

**MAGICC:** finish Phase 2 RFF-SP pulse runs (builder smoke-tested; plan in
`FaIRtoFrEDI/notes/handoff_2026-06-21_rffsp_phase2_plan.md`). Carry the CH4 oxidation
harmonisation over. Deliverable: MAGICC vs BRICK-FM pulse marginals (CO2 + CH4) on
the same RFF-SP backbone — the level-vs-marginal inversion made quantitative.

**FACTS2.0:** the mid-July-2026 deferral window is NOW. Full install spec:
`notes/handoff_2026-06-21_facts_install_scoping.md` (Docker-only on this Mac — builds
native arm64; Docker NOT yet installed; use `global_only` data; FaIR-driven, so
apples-to-apples with BRICK-FM/MAGICC-hybrid). **Open feasibility question:** whether
FACTS supports clean paired pulse/baseline experiments (deterministic seeding across
its module chain) or serves only as a scenario-level benchmark. Resolve during install
before promising a FACTS pulse panel in the paper.

## 5. Paper skeleton (Claude-side deliverables)

- **Methods:** BRICK-FM description (condense §2–3 of the rationale doc + the short
  MCMC description drafted 2026-07-09 for Tony/Vivek); pulse experiment design
  (paired seeds, sizes, oxidation harmonisation); comparison protocols.
- **Figures (candidate set):** (i) BRICK-FM hindcast vs obs per component
  (postpred_ext_* pattern); (ii) calibration-version lineage (pre-#93 → 2.0 → FM)
  pulse response — the "why the model version matters 2.5×" figure; (iii) cross-gas
  4-panel GMST; (iv) SLR per-actual-tonne CH4 vs CO2, no-GWP; (v) MAGICC vs BRICK-FM
  marginals (level-vs-marginal inversion); (vi) FACTS benchmark panel (feasibility
  pending).
- **Tables:** pulse marginals by gas × horizon × model; BRICK-FM free params + priors
  vs Wong et al.; convergence diagnostics.
- **Numbers to re-verify after v-next recalibration:** every headline above changes
  when the posterior changes. Quarantine current pulse outputs per the standard
  discipline when v-next lands; regenerate to canonical paths.

## 6. Open methodological decisions (flag — do NOT silently resolve)

1. FaIR-config calibration approach: sequential (status quo) vs IW (a) vs per-config (b/c).
2. AIS geometry freeing strategy (which params, which identifiability mechanism).
3. IMBIE/Dyurgerov point terms: drop vs keep-with-corrected-σ (must decide before recal).
4. Pulse year(s) and sizes for the paper (2030 only vs multidecade; 1 GtCO2 / 1 TgCH4
   established as safe; CO2-at-1-GtC contaminated by AIS tipping → use median).
5. CH4 framing: per-actual-tonne (no-GWP) as primary vs GWP-equivalent as primary;
   biogenic vs fossil arms (fossil FaIR→BRICK arm still to build).
6. Scenario backbone: RFF-SP ensemble (Phase 2 plan) vs SSP2-4.5 (Phase 1) — or both.
7. Which BRICK lineage members appear in the paper (FM primary; 2.0 as comparator;
   pre-#93 as cautionary appendix?).
8. Whether PF-O3 CH4 amplification (GTP-100 +48%, memory `project_pf_o3_substack_figures`)
   is in scope or cited as companion work.
9. Journal target + whether BRICK-FM model description is main text or appendix.

## 7. Pulse-experiment discipline (carry-forward checklist)

- Paired seeds mandatory (FaIR v1.4.5-style stochastic runs: noise ~200× signal).
- CO2 input unit is **GtCO2** not GtC (recurring bug class).
- All 5 sanity tests per pulse experiment (zero-pert bit-identical, sign-flip, ×2
  scaling, first-principles magnitude, paired-seed check) — `climate-modeling` skill.
- float64 end-to-end through BRICK (float32 destroys small marginals).
- Report **medians** for CO2 marginals (mean contaminated by pulse-induced AIS tipping).
- LWS ≡ 0 in marginals (deterministic `:central` cancels in pairs) — verify, don't assume.
- Wong weights (ESS 0.5) apply to pre93/brick2 arms; Mengel arm equal-weighted.
- Quarantine (never delete) any outputs superseded by the v-next recalibration.

## 8. Repo map

| Repo | Role | State |
|---|---|---|
| `msarofim/MimiBRICK.jl` fork, branch `brick-fm` | BRICK-FM package (PR2) | @30948fa, ready for Tony |
| raddleverse/MimiBRICK.jl#111 | PR1 Mengel component | awaiting Tony |
| `SLR-RFF-BRICK` | BRICK study drivers, obs prep, this handoff | pulse-3BRICK drivers on archived `brick-mengel` |
| `MimiBRICK-FM` (github.com/msarofim/MimiBRICK-FM) | earlier private extraction | superseded by the fork for package work; posteriors/provenance remain |
| `FaIRtoFrEDI/magicc_comparison/` | MAGICC pulse pipeline | Phase 2 builder smoke-tested (ed1910d) |
| FACTS2.0 | not yet installed | spec in `handoff_2026-06-21_facts_install_scoping.md` |

## 9. Suggested sequencing

1. Tony/Vivek feedback window on PR1/PR2 (already shared) — fold into v-next scope.
2. Decide open items §6.1–6.3 (they gate the recalibration).
3. Build v-next: Smith-2024 forcing → point-term reconciliation → freed-AIS prior
   design → MCMC on Torch → convergence + postpred vs obs.
4. In parallel: FACTS2.0 Docker install + pulse-feasibility test; MAGICC Phase 2
   production runs.
5. Regenerate all pulse marginals on the v-next posterior (quarantine old).
6. Figures/tables/methods per §5; Marcus drafts text.
