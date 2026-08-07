# Handoff 2026-08-07 (night) — T2 executed (anchor 39→37.4, tension stands); T1 offline test run

**Self-contained pickup:** this note + `handoff_2026-08-07_extB3_falsified_modern_flow_tension.md`
(the decision menu this executes) + memory `project_brick_mengel_vnext_recalib`. Branch
`brick-mengel-vnext`. Nothing running. Marcus's direction (2026-08-07 evening): "definitely do T2,
and test T1" — both done this session.

## 1. T2 — GlacierMIP3 ladder-anchor scope correction: DONE, VALIDATED, TENSION NOT DISSOLVED

**Data** (`data/observations/raw/gmip3/`, commit d9835e6): GlacierMIP3 Zenodo archive v2
(10.5281/zenodo.15046588; concept 14045268; Zekollari 2025 Science adu4675). Small files tracked
(published LOWESS fits, tables S1a/S1b/S3, region characteristics incl per-region 2020 volumes,
per-experiment warming, response times); the 1.47 GB per-experiment shifted netCDF is UNTRACKED
(gitignored) — re-fetch recipe in `README_modern_extensions.md` via
`python/scripts/remote_zip_extract.py` (HTTP-range selective extraction; the whole session cost
~363 MB of transfer, not 984 MB + 1.5 GB).

**Method** (`python/t2_gmip3_scope_anchor.py`) — replicate the paper's own estimators, then
delta-transfer. Reverse-engineered from github.com/GlacierMIP/GlacierMIP3:

- Published global CENTRAL = LOWESS median over the 80 constant-climate experiments of the
  **sum of per-region model-MEDIAN volumes** / 2020 volume.
- Published global BOUNDS are NOT that fit's quantiles — the 0d aggregation notebook REPLACES
  them; they are ≈ the per-member composite over the **4 globally-covering models**
  (PyGEM-OGGM_v13, GloGEMflow, OGGM_v16, GLIMB; the authors' own only-global equivalence note,
  confirmed numerically on the `_only_global_models` file).
- Both estimators replicated with moepy + the paper's frac auto-selection (selected 0.22–0.23;
  paper 'All' used 0.23). **Validation on full-RGI reproduces the published ladder: central max
  err 1.6 pct-pts, bounds max err 2.1 (tol 3) — PASS.** A naive mass-weighted composite of
  per-region marginal quantiles over-disperses bounds by up to 11.5 pts (the authors' own
  "conservative regional sum" caveat) — in the CSV as `method=marginal_xcheck` only.

**Final excl-r5-incl-r19 anchors** (published + replicated scope delta; `method=anchor_final`
rows of `outputs/t2_gmip3_scope_anchor.csv`; r5 = Greenland periphery, 58%-committed@1.2K but
only 9.8% of stock):

| rung (global K) | published full-RGI | scope-corrected |
|---|---|---|
| +1.2 | 39 [15, 55] | **37.4 [11.8, 54.0]** |
| +1.5 | 47 [20, 64] | **46.3 [17.2, 63.2]** |
| +2.0 | 63 [43, 76] | **63.0 [41.5, 75.5]** |
| +3.0 | 77 [60, 85] | **75.5 [58.5, 83.9]** |

Sens 1.5→3K for our scope ≈ **95 mm SLE** raw-Gt basis (full-RGI raw 109; S1b BSL-corrected 98;
the shootout's `GMIP3_SENS_MM = 85` report-constant is low under any basis — update it when the
gate constants are updated). SC point under the new anchor: b 0.282, T_off −0.914 glacier-K,
committed@1850 0.087 m, demanded gap 103 mm (was 108).

**Verdict: the scope correction is real but small — modern-flow overshoot improves only
2.00× → 1.85×** (κ_D0·exc·gap arithmetic, exc window 2016–2020; same-script both-anchor
comparison). T2 alone does NOT resolve the extB3 tension, as the falsified-handoff hedged.
NB the 1.7× in that handoff used a slightly different exc convention; the apples-to-apples
numbers are this script's 2.00×→1.85×.

## 2. T1 — offline two-reservoir-ν existence test: FALSIFIED (both anchors)

`python/t1_two_reservoir_offline.py`. Design per the decision menu: at the SC point (S_eq fixed;
re-solved per anchor), can ANY fast/slow configuration pass the 4 pre-registered gates AND fit
1980–2023 flow within ~5 logL of the pathological optimum? Conventions: pre-1940 flow σ×2 (the
standing likelihood), ladder/spread at calibrator amp_g = 1.8 (eval_chain_gates convention, not
D0 ampfit), ν SCANNED not optimized (free ν rails to 0 — the D0 non-identifiability — and kills
spread), flow criterion = marginal AR(1) logL of the 1980–2023 window at each candidate's own
fitted (σ, ρ). Pathological reference = free single-N under the same objective: lands on the
extB3-chain mode (a 0.359, b 0.333, T_off −1.60, ν→0), window logL 52.82.

Machinery validation: single-N ν=1 at SC = 4/4 gates, window deficit **21.2** — matches the
whitened per-era chain attribution (−17.8 − 5.2 ≈ −23) from `diag_pathology_terms.jl`. ✓

Arms (per anchor: 2 N1 refs + 90-cell P grid (φ × τ_s × ν) + 16-cell P2 grid (φ × ν) + free P +
free R): **0/110 configs feasible under BOTH anchors.**

- **P (Nauels-ν fast pool + linear slow pool):** the binding gate is SPREAD (61% of grid fails
  it; inventory/ladder/S1900 essentially never fail). Monotone trade-off: flow-optimal low-φ
  cells (best deficit 10.8 at φ=0.2, τ_s=150, ν=0.5) saturate at spread ≈ 2.8–3.5 vs the
  4.5 gate floor; 4/4-gate cells exist only at φ=0.8 (single-reservoir-in-disguise), best
  deficit 15.6 vs single-N's 16.8 — **the split buys ~1 logL**. Even flow-optimal cells sit at
  modern rate 0.87–1.05 mm/yr (obs ~0.6): the slow pool's committed outflow G_s/τ_s plus the
  wiggle-tracking fast response floors the total.
- **R (explicit rate cap, free fit):** deficit 0.3 — nails modern flow — but the cap binds in
  projections too: spread 0.0. Rejected as a free-fit device (a scenario-dependent cap would be
  pure tuning).
- **P2 (two Nauels pools, slow pool keeps ν — the "committed ice quiet at modern excess,
  mobilized at strong-warming excess" mechanism):** 16/16 cells pass 4/4 gates, but the best
  deficit (16.3 pub / 16.8 t2, at φ=0.1, ν=0.5) is IDENTICAL to single-N ν=0.5 — and the fitted
  κ_s ≈ κ_f, i.e. the optimizer collapses the two pools back into one reservoir. The high-ν
  mobilization dial never beats ν=0.5. The family reduces to, not improves on, single-N.
- **Ungated floor:** even ignoring ALL gates, the P-family free optimum (ν→0, spread dead) only
  reaches deficit ~9.7–10.8 — above the 5-logL tolerance before the spread gate is even applied.
  Only the rate cap gets below it, and the cap kills projections.

**Reading:** committed-ice retention and ν-driven scenario spread both load onto the same
fast-pool response; decoupling them structurally relocates, not resolves, the tension. Under
this falsification standard the two-reservoir surgery is NOT the way out.

## 3. Where this leaves the T1–T4 menu

- T2: executed — adopt the scope-corrected anchors for any future gate evaluation regardless of
  the structural decision (they are the scope-correct numbers), but they do not rescue ν.
- T1: offline-falsified in the tested family (fast/slow split incl. the two-Nauels variant;
  rate cap rejected on principle after the free fit showed cap-binding-in-projections).
- T3: remains rejected (down-weights the best-measured segment).
- T4 (accept ν≈0 at the hindcast optimum; report scenario spread as structurally
  under-dispersed; carry ν as a labeled projection-informed sensitivity arm) — **now the live
  default, per the falsified-handoff's own fallback logic ("T4 is the fallback if T1 fails
  offline"). Structural surgery beyond the tested family (e.g., separate S_eq shapes per pool,
  regionally-resolved glacier blocks) would be new scope — Marcus's call, do not resolve
  silently.**

## 4. Traps / state

- `outputs/t2_gmip3_scope_anchor.csv` `method` column: `anchor_final` = the adoptable numbers;
  `exact` = raw replicated per-scope values (carry ~1–2 pt replication noise); `marginal_xcheck`
  = the over-dispersed naive composite (do not use); `sc_solve` = tension-metric rows.
  `validation_pass` column gates downstream consumption (t1 loader checks it).
- The T1 CSV (`outputs/t1_two_reservoir_offline.csv`) has per-era window logLs
  (`flow_1900_1919` … `flow_2000_2023`) and `rate_modern_mm_yr` (2015–2023 mean) per config.
- moepy pip-installed into ~/climate-env (2026-08-07). tqdm bars from moepy spam stderr —
  filter `it/s` when logging.
- The gmip3 netCDF member inside the Zenodo zip is deflate-compressed: ranged extraction of the
  member costs ~358 MB, not 1.47 GB.
- d0_glacier_shootout constants (`GMIP3_CENTRAL/LIKELY/SENS_MM`) are still the published
  full-RGI values — swap to the anchor_final numbers only WITH a Marcus decision on the gate
  set, since the pre-registered gates were declared on the published anchors.
- Shell cwd resets between calls — `git -C` / absolute paths.
