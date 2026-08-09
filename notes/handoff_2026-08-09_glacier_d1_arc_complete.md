# Handoff 2026-08-09 — Glacier structural program (D1→D1d) complete; offline cells converged; FIRST TASKS: S(1900) box analysis + honest structural assessment

**Self-contained pickup:** this note + memory `project_brick_mengel_vnext_recalib` (top
blocks) is sufficient. Deeper background in order of usefulness:
`notes/note_2026-08-09_d1d_fourrung_seam_verdict.md` (final state),
`notes/memo_2026-08-08_geometry_drift_literature.md` (the uncharted-ice mechanism,
primary-source verified), `notes/handoff_2026-08-08_d1c_uncharted_verdict.md`,
`notes/handoff_2026-08-07_d1_multireservoir_verdict.md`,
`notes/note_2026-08-08_d1b_slow_split_verdict.md`,
`notes/memo_2026-08-07_glacier_constraint_anatomy.md` (why one reservoir can't work).
Branch `brick-mengel-vnext`. Nothing running. extA108 still canonical for production;
pulse arms parked. Repo commits for the arc: 903367f (D1), 05e2171 (D1b), f8c31dd +
f694d29 (literature), 690b29b (D1c), 3165dca (D1d).

## 1. One-paragraph summary of the arc

The Mengel/Nauels single-reservoir glacier component could not jointly satisfy the
GlaMBIE/Frederikse hindcast, the GlacierMIP3 committed ladder, and scenario spread
(extB3/T1 falsifications). The D1 cells established: (i) a 2–3 reservoir split with
per-reservoir S_eq frames and GlacierMIP3-response-time-anchored transients passes all
four projection-side gates out-of-sample — no prior structure ever had; (ii) the
century-integral gap (~50 mm) that remained is NOT structural: it decomposes into a
PRIMARY-SOURCE-VERIFIED scope mismatch (Parkes & Marzeion 2018 uncharted glaciers ARE
in the Frederikse-based target, uniform-sampled 16.7–48.0 mm — and are structurally
outside the model's present-RGI stock; every cell's fitted U lands at the Frederikse
central ≈32 mm from a flat prior) plus a Marzeion-2015 early-segment bias δ ≈ 0.3 mm/yr
on 1900–1960 (the provenance-exact pure-M15 window; ≤1σ of the Roe-2021-motivated
prior); (iii) after the r19 accounting seam and Farinotti-BSL basis are fixed, every
underlying datum is satisfied within ~1.3σ and the free-dynamics arm fits the whole
scope-consistent century at noise level — the remaining pre-registered "failures" are
hard-box edges. The offline point-optimization program is CONVERGED; the venue for the
remaining marginal tensions is the extC MCMC, which is NOT yet green-lit.

## 2. Standing Marcus decisions (do not re-litigate)

- T5c (hindcast/projection hybrid) REJECTED. T5d (structured early-segment discrepancy)
  ACCEPTABLE. T3/T4 rejected earlier. Reassigning subpolar regions into FAST REJECTED
  (D1b: one-pool failure resurrects inside the merged block).
- Geometry-drift as transient physics PARKED (no literature quantification; direction
  ambiguous). The uncharted-ice scope mechanism replaced it (options 1+4 executed).
- GlacierMIP3 rungs must carry APPROPRIATE UNCERTAINTY — no overconstraint (implemented:
  rung σ = band/2 floor 3 pct-pts, cross-rung corr 0.6, soft Farinotti a-priors;
  verified all rung |z| ≤ 0.2).
- FrEDI/FaIR side of the projects unaffected throughout.

## 3. The current model structure (D1d "C_both" = the working candidate)

Three Nauels-ν reservoirs, S_eq,b = a_b(1−exp(−b_b(T_b − T_off_b))), dS_b/dt =
min(κ_b·exc^ν_b, 1)(S_eq,b − S_b):

| res | regions | a (m SLE) | b | T_off (glac-K) | amp_b | κ_anch | ν_anch | τ50 tgt |
|---|---|---|---|---|---|---|---|---|
| R19 | 19 | 0.069 (Farinotti r19, ±0.018) | 0.459 | +0.27 | 1.03 | 0.00093 | 1.54 | 828/213 |
| SLOWP | 03/09/07/06 | 0.146 (±0.033) | 0.394 | +0.24 | 1.70 | 0.00073 | 1.62 | 523/113 |
| FAST | rest (13) | 0.140 (±0.024) | 0.421 | −1.06 | 1.23 | 0.00339 | 1.57 | 130/37 |

plus, on the model side of the target comparison only:
- **F_unch(t)**: uncharted-ice cumulative melt, U ~ flat[14.5, 41.8] mm scope
  (= global [16.7, 48.0] × 0.87 non-r5), TAPER profile (const rate 1901–1970, linear→0
  by 2005; const-with-1990-step and frontload both inferior/falsified);
- **δ**: rate bias on the 1900–1960 obs segment (pure-M15 window), prior N(0, 0.30) mm/yr;
- **obs_adj**: target with GlaMBIE r19 cumulative removed post-2018 (net 0.38 mm) —
  the whole target is then scope-without-r19, matching Frederikse's own convention;
  R19 is EXCLUDED from the hindcast flow sum but RETAINED in all gates + projections.
- Anchors are all data-derived (4-rung correlated fits + Farinotti a-priors + τ50
  anchoring); the hindcast fits only (σ, ρ, U, δ) in the ANCH arm.

Current numbers (ANCH/unc_t5d, taper): flow-window deficit 8.2 vs fully-fitted patho
(tol was 5; FREE arm reaches −0.4..+0.9 → data fully compatible with the structure);
S(1900) 8.1 mm (box 10–30; Leclercq z −1.2, predicted direction — see task T1);
modern hindcast rate 0.97 vs adj-obs ~0.81 (MID arm: 0.84, deficit 5.1–6.6 — the data
want ~±30% κ freedom around the anchors); spread 6.7 cm (gate 4.5–13.5), SSP levels
7.7/9.8/14.1 vs AR6 9/12/18 (MID ≈ on them); ladder in-band all rungs; inventory z 0.55;
U = 29.6 (Frederikse central); δ = +0.30 (1.0σ).

## 4. FIRST TASKS after this handoff (Marcus, 2026-08-09)

### T1 — explicit analysis of the S(1900) box

The 10–30 mm box (from D0's pre-registration, ≈ Leclercq 20±9 at ±~1σ) predates the
uncharted-scope and BSL understandings. Required: a short memo that
1. traces the box's provenance (D0 handoff §3 → `d0_glacier_shootout.py`
   S1900_GATE_MM) and what the Leclercq 2011 datum actually measures (length-record,
   total-scope, surviving-glacier records upscaled — check its r5/r19 treatment in the
   paper; PDF may be needed → ask Marcus or check `~/Documents/2026/ClaudeDocs/Papers/`);
2. enumerates the scope corrections between "Leclercq total 1850–1900 melt" and "model
   inventory-scope S(1900)" with magnitudes and uncertainties: (a) pre-1900 melt of the
   later-uncharted small glaciers (P&M 2018 starts 1901 — is a pre-1901 estimate
   derivable from their supplement, or bound it: the same small-glacier stock that shed
   17–48 mm over 1901–1990 plausibly shed some mm before 1900 — needs an honest range,
   not a point); (b) r19 (Frederikse-convention zero; Leclercq's scope?); (c) r5;
3. proposes EITHER a re-derived box for the inventory-scope model OR (cleaner)
   replacing the box with the Leclercq likelihood term evaluated at a scope-corrected
   mean/σ — presented as options for Marcus, NOT silently adopted;
4. checks sensitivity: does any defensible re-derivation change the D1d verdict
   pattern (S1900 8.1–9.8 passing or not)?

### T2 — honest assessment of the overall model structure

A memo answering Marcus's questions directly — "how well does it match observations &
future projections? Is it overly complex, or is it reasonable?" No advocacy; for the
extC / paper-framing decision. Must include:
1. **Obs match:** era-rate table (obs vs corrected-obs vs model, 1900–2023) for the
   headline; S(1900), S(2020), inventory, GlaMBIE per-reservoir modern rates; explicit
   statement of the ANCH modern overshoot (0.97 vs 0.81) and that MID (κ within priors)
   resolves it; the FREE-at-noise-level result as the "data compatibility" statement.
2. **Projection match:** SSP levels/spread vs AR6 ch.9 medians and the FACTS/B2
   comparison conventions; committed ladder vs GlacierMIP3 (model-basis vs data-basis
   nuance); the response-time behavior (τ collapse expressed by ν≈1.5–1.6).
3. **Complexity audit — the "overly complex?" question, answered honestly:** count
   every parameter and term, and for each name its data source or prior: 3 reservoirs
   × (a, b, T_off) from rungs+Farinotti (9, fitted to 12 rung data + 3 priors), κ/ν
   from τ50 pairs (6, from 6 data), U (1, flat literature prior), δ (1, literature
   prior), σ/ρ (2, nuisance) — versus the alternatives' counts (Wong 2.0 GSIC ~4
   params but 0/4 gates; single-reservoir Nauels 5 params, falsified). Also count the
   CONVENTIONS a reviewer must swallow (r5-in-GIS, r19 hindcast exclusion, uncharted
   term, splice, δ window, taper shape) — the complexity cost is more in conventions
   than parameters, and the memo should say so plainly if that's the honest reading.
   Include: which pieces could be dropped at what cost (e.g. merge R19 into SLOWP?
   drop δ? drop the block GlaMBIE terms?) — a minimality table.
4. A recommendation section clearly separated from the analysis.

### Then (pending Marcus): extC green-light

Assets ready (verdict-note §3): structure + rung covariances + Farinotti a-priors +
U/δ priors + obs_adj + τ50-as-priors (~±30% κ freedom) + widened T_off bounds
(calibrator currently (−2.00, −0.10); SLOWP/R19 need up to ~+0.7). Surgery scope
sketch in the T5a spec §4 (extC tag family) still applies, now for 3 reservoirs.

## 5. Traps / non-obvious state

- **Shell cwd resets between calls** — `git -C`, absolute paths.
- **exec-rebind trap**: every d1* script execs the d0 prefix; output paths must be set
  AFTER the exec. All five scripts do this correctly — keep the pattern.
- **Caches**: `outputs/d1_gmip3_steady_cache.nc` (71 KB; replaces the untracked 1.47 GB
  GlacierMIP3 nc) + `outputs/d1_block_ladder_cache.csv` (exact-estimator ladders, keyed
  by sorted region set) + `outputs/d1b_singleton_ladder_cache.csv` (diagnostic-grade,
  DIFFERENT estimator — never mix with the block cache). Delete caches to force rebuild
  after any change to steady window/model set/scope. With caches, cells run 25–45 min.
- **Patho convention**: the criterion's pathological comparator must be re-fit per
  (likelihood variant, obs vector) WITH matched U/δ freedom, or deficits are biased.
  Regression anchors: sx2/no-U patho = 52.82 (T1/D1); D1 ANCH/sx2 deficit 20.7.
- **ρ rails at 0.99** in σ×2 variants (AR(1) as level-discrepancy absorber); with U+δ
  it relaxes (0.94–0.97). Same bound applies to patho — comparisons are like-for-like.
- **λ-bridge between two-rung and four-rung frames is stillborn** (both endpoints share
  the S(1900) miss) — do not re-propose.
- **Sanity-check lesson**: r19 has positive-mass-balance YEARS — never assert
  monotonicity of the r19-adjusted target (fixed in d1d, commit 3165dca).
- **GlacierMIP3 metric flag**: the 2025 paper's headline response times are
  80%-response; our pipeline uses the regchar −50% columns (fine, don't cross-compare).
- **regchar amp ratios are ISIMIP3-based and low** (aggregate 1.34 vs amp_g 1.8 / obs
  1.59; obs-fit per-block 1.76/1.40 vs regchar 1.44/1.23) — internally consistent as
  used; an obs-amp sensitivity arm was never run (flag, cheap with caches).
- **Marcus's paper PDFs live in `~/Documents/2026/ClaudeDocs/Papers/`** — check before
  fighting paywalls (memory `reference_claudedocs_papers_folder`).
- Leclercq underpins BOTH the S(1900) gate and the A2b likelihood term — T1's scope
  re-derivation touches both; change together or not at all.
- The pre-registered FLOW_TOL=5-vs-pathological criterion has been missed by four
  successively better cells (20.7 → 11.5 → 8.4 → 7.3); any revision is Marcus's
  explicit call, with the original metric still reported.

## 6. File inventory (the arc)

Scripts: `python/d1_multireservoir_cell.py`, `d1b_slow_split.py`,
`d1c_uncharted_cell.py`, `d1d_fourrung_seam.py` (all exec the d0 prefix; all carry
sanity batteries and commit-tagged outputs).
Outputs: `outputs/d1_multireservoir_{cell,blocks}.csv`, `d1b_{slow_split,blocks,member_twoparam}.csv`,
`d1c_{uncharted_cell,blocks}.csv`, `d1d_{fourrung_seam,blocks}.csv` + caches + figures
`figures/d1{,b,c,d}_*.png`.
Notes: listed in the header. Memory: `project_brick_mengel_vnext_recalib` (current),
MEMORY.md index line updated 2026-08-09.
