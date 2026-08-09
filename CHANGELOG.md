# Changelog

All notable changes to this project. Older history reconstructed from the
commit log; recent entries are explicit.

## [unreleased] — 2026-08-09 (latest) — extC green-lit: D1f obs-amp arm + full 3-reservoir calibrator surgery (validated 5e-13, smoke-passed); launch gated on amp-basis call

- **Marcus green-lit extC + the obs-amp sensitivity arm**, and set the sharing-memo
  spec (abstract w/ data+structure choices; obs comparison; SSP vs FACTS+MAGICC;
  methodology for Tony; declarative style; only legacy comparison = pre-Mengel
  BRICK 2.0 — memory `feedback_brickf_sharing_memo_spec`).
- **D1f obs-amp arm (`python/d1f_obsamp_arm.py`) — MATERIAL per its pre-registered
  rule:** obs through-origin amps R19 0.61 / SLOWP 2.48 / FAST 1.40 vs regchar
  1.03/1.70/1.23; ANCH modern-rate bias flips sign (+26% → −11%), deficit ±1.7;
  **MID (the extC design) deficit-invariant** (6.79→6.79) with projections moving
  toward AR6 (ds245 10.2→11.3, spread 6.5→7.9). Amp basis = Marcus call; a
  cross-dataset amp check (Berkeley Earth / GISTEMP vs HadCRUT5) was requested
  and is running (`python/diag_amp_dataset_comparison.py`).
- **extC surgery COMPLETE (commit 6771ed5):** `glaciers_nu3` component (per-block
  lagged drivers; slot-contract `gsic_sea_level` = R19+SLOWP+FAST; `gsic_hind`
  for the seam scope) + `build_brick_nu3`/`update_brick_nu3!`/`set_glacier_forcing3!`;
  calibrator now 39 physical + 10 AR(1) = 49 params — per-block (a, b, T_off,
  log10κ) with Farinotti a-priors, bounds-only b/T_off (the per-block rung
  likelihood constrains them; corr 0.6, band σ, data-basis committed %),
  τ50-as-priors on log10κ (σ 0.114 ≈ ±30%), ν FIXED at anchored (MID design);
  likelihood-only params gic_u_unch (F_unch, flat[14.5,41.8] + taper in flow AND
  total channels, never in the Mimi graph), gic_delta (N(0,0.3), obs-side ramp
  1900–1959), gic_u_pre + gic_s_r5 (the Option-D ledger, replacing the pre-D A2b);
  A2 on sum(a_b) − S_all(2000); per-block GlaMBIE rate terms (SLOWP/FAST);
  obs_adj gsic target (r19 seam); OLD38_NAMES covariance branch (extB3c
  preferred); positional-KAPPA_IDX trap removed; `--amp-basis=regchar|obsfit`.
- **Machine-generated calibrator inputs** (`python/build_extc_inputs.py`, full
  precision): `t_glac_blocks.csv`, `extc_block_constants.csv` (both amp bases),
  `recalib_targets_ext_gsicadj.csv`. **Port validation** (`julia/
  validate_glaciers_nu3.jl` — includes the calibrator itself): drivers + series
  ≤5e-13 vs python on BOTH bases, slot contract exact, logposterior(θ0) finite.
  Smoke 50-iter: accept 0.34, all 16 glacier/ledger params moving plausibly.
  Two precision lessons: 6-decimal artifact CSVs broke 1e-9 validation (drivers
  are multi-region averages; amp truncation leaks through the splice tail) —
  all artifacts now %.12f/%.12g.
- **Two-stage launch still mandatory** (overdispersed_starts.csv predates extC):
  tuning (common start) → rebuild starts+cov → production. Pending: amp-basis
  call → tuning launch; eval_chain_gates.py rewrite + diag_slr_convergence
  repoint before --accept-slr.

## [unreleased] — 2026-08-09 — Marcus ruled Option D; P&M 2018 read from primary; D1e ledger cell built + launched

- **Marcus's S(1900) ruling: Option D** — the model-side ledger ("make the best
  defensible historical data target with appropriate set-asides… then work on getting
  the model to fit that data target"), framed by his two-issue decomposition:
  (a) dataset/model scope matching (pre-2000-melted glaciers held separately),
  (b) model design for remaining-history + present + scenario responsiveness.
  The S(1900) question is ~entirely (a); its only (b) content is keeping a pre-1900
  regularizer in extC.
- **P&M 2018 now on disk and read in full** (`ClaudeDocs/Papers/`, 9 pp): seven new
  primary receipts in `notes/memo_2026-08-09_d_ledger_target_spec.md` §1, most
  notably the derivable 1901 uncharted stock (18.8–50.4 mm SLE), the CRU origin of
  the 1901 start, r19-removal RAISING the uncharted estimate (49.1+6.3), and the
  global-only upscaling (Frederikse's 13%-r5 regionalization is their own invention
  vs P&M's 43.1% r5 small-glacier area share — target-content caveat).
- **D1e cell** (`python/d1e_dside_ledger.py`, commit 0646571): datum untouched at
  N(20,9); set-asides U_pre ~ flat[0,25] mm (0-edge = charted-scope reading) +
  S_r5 ~ N(2.5,2.0)[0,8] mm on the model side; g_lec |z|≤2 replaces g_s1900
  (legacy box still reported); matched-freedom patho; era-rate + per-reservoir-rate
  emitters (the T2 cheap item); evaluation-based sanity (d1d θ identity);
  pre-registered P1 (ANCH deficit unchanged 8.21±0.05), P2 (ledger interior,
  ANCH/MID 4/4), P3 (FREE decouples from the Leclercq pull), MID/sx2 5.07-vs-5
  watch item. Julia A2b carries the D-ledger spec + TODO(extC surgery)
  (change-together trap).
- **D1e EXECUTED (`notes/note_2026-08-09_d1e_dside_ledger_verdict.md`): P1/P2
  CONFIRMED, P3 FALSIFIED, 0/6 feasible (expected).** Sanity 4/4 (structures
  reproduce d1d to 5e-6; θ evaluation identity). ANCH deficit 8.22 (unchanged);
  every ANCH/MID row now **4/4 gates** with the ledger interior: 8.1 + 2.5 (S_r5,
  prior mean) + 9.4–10.5 (U_pre, mid-range of the P&M construction) = 20.0, z ≈ 0.
  Minimal bar misses only on δ = 1.005σ vs the ≤1.0 edge (third decimal). MID/sx2
  watch: 5.32, no feasibility flip (old ll_lec's κ-pull was mildly flow-aligned;
  MID re-priced honestly +0.2–0.3). **P3 falsified informatively: FREE keeps legacy
  S(1900) 26.3–27.1 with U_pre railed at 0 — the d1d FREE ~27–28 mm was
  flow-preference, not Leclercq pull** (revises the T1/D1d inference; the flow data
  independently want ~26 mm of pre-1901 melt). New emitters: per-reservoir modern
  rates (ANCH overshoot in BOTH blocks: SLOWP +37%/FAST +25%; MID puts SLOWP dead
  on GlaMBIE) + era rates (residuals small, mixed-sign). U_pre caveat stated: no
  independent constraint — interior-not-railed is literature-consistency, not
  data corroboration.

- **`notes/memo_2026-08-09_t1_s1900_box_scope.md` (T1):** the 20±9 mm Leclercq datum
  traced to the 2026-08-06 receipts family {10, 18.5, 21.8, 28.0} — the box floor (10)
  IS the lowest family member, zero margin; Leclercq 2011 primary-verified (Springer
  full text): 349 surviving-glacier length records calibrated onto 1951–2009 charted
  mass balance → two defensible scope readings (total-scope vs effectively-charted),
  so the uncharted correction to the datum is honestly 0–23 mm (reading-(i) central
  ≈9); r19/r5 corrections offset (+1–2 / −2–3 mm). Options A (keep+label) /
  B (re-derived box) / C (likelihood-only, recommended, e.g. N(15,10)) for Marcus.
  Sensitivity: any defensible re-derivation → all ANCH/MID rows 4/4 gates; deficits
  and 0/12 feasibility untouched (ANCH S(1900) is an analytic constant of the fit —
  bit-identical 8.12281 across variants); closest feasibility candidate
  C_both/MID/unc_sx2 at deficit 5.07 vs tol 5 flagged. Python + Julia constants must
  change together.
- **`notes/memo_2026-08-09_t2_structural_assessment.md` (T2):** century budget
  1900→2020 decomposed (blocks 38.4 / U 29.6 / δ 18.1 / resid 0.5 mm — 56%
  non-dynamical, both terms literature-anchored); era table with scope-corrected obs;
  parameter census (19 nominal; 4 hindcast-fitted, none dynamics; **a_b prior-pinned
  to 5 dp — the rungs determine 6 params, not 9** — new finding); comparator ledger
  (Wong WR-GSIC fails ≥3/4 itemized, NOT script-produced "0/4"; Nauels-ν 0/4;
  reassign catastrophic); 11-convention ledger — complexity lives in conventions,
  not parameters; minimality table (every remaining piece costs likelihood or scope
  honesty); recommendation separated: green-light extC after the T1 call + two cheap
  pre-extC items (obs-amp arm; era-rate emitter).
- **Record corrections (do not propagate):** (1) "adj-obs ~0.81" modern rate is the
  UNADJUSTED 2015–23 number; the like-for-like r19-adjusted comparator is **0.766**
  → ANCH overshoot 1.26× (not ~1.19×), MID 1.10×; (2) the arc handoff's SSP quote
  "7.7/9.8/14.1" is the A_4rung ablation row — headline C_both/ANCH is
  **9.06/11.23/15.78** vs AR6 9/12/18, and MID is slightly LOW at all three (not "on
  them"); (3) D1d gate status is 3/4, not 4/4 (the 4/4 claims belong to D1/D1c).
- Papers checked: Leclercq 2011 and P&M 2018 are NOT in ClaudeDocs/Papers (fetched
  key facts from publisher pages instead); Frederikse 2020 EDF Fig. 6a (on disk)
  gives the P&M time profile — near-constant to ~1980, exhausted by ~2000 —
  corroborating the taper.

## [unreleased] — 2026-08-09 — D1d (4-rung fits + r19 seam): bars NOT met but the offline program has CONVERGED — every datum within ~1.3σ

- **`python/d1d_fourrung_seam.py`** (Marcus green-lit options 1+4): 4-rung correlated-
  Gaussian S_eq fits (rung σ = band/2 floor 3, corr 0.6, soft Farinotti a-priors
  0.221±0.057 / r19 0.069±0.018) + r19 as third reservoir excluded from the hindcast
  (obs_adj removes GlaMBIE r19 post-2018; net 0.38 mm) + Farinotti-SLE r19 basis
  (resolves the Gt-vs-SLE BSL sub-decision). Sanity 3/3 after fixing an over-strict
  monotonicity assertion (r19 has positive-balance years). **All rung |z| ≤ 0.2 —
  no overconstraint** (the explicit Marcus requirement, verified).
- **Bars NOT met (0/12):** deficits improved to 7.3–8.2 (δ ≤ 1σ, U ≈ Frederikse
  central) but S(1900) drops to 8.1–9.8 mm — below the 10–30 box — because the
  (physically right) BSL r19 stock reduction removes ~1.4 mm of early melt; ANCH
  modern rate overshoots (0.97) in the seam variants, MID resolves it (0.84–0.85).
  λ-bridge diagnostic considered and NOT run (both frame endpoints share the S1900
  miss — stillborn).
- **Conclusion (`notes/note_2026-08-09_d1d_fourrung_seam_verdict.md`): the offline
  point-optimization program has converged** — FREE arms fit the adjusted century at
  noise level; every underlying constraint is met within ~1.3σ (S1900 z −1.2 vs
  Leclercq, in the direction the inventory-vs-total scope argument predicts); the
  remaining "failures" are pre-registered box edges. Assets for extC assembled
  (structure, rung covariances, priors, obs_adj, T_off bounds). Whether to re-derive
  the S(1900) box for inventory scope is a Marcus call.

## [unreleased] — 2026-08-08 (night) — D1c uncharted-ice cell EXECUTED: pre-registered prediction NOT confirmed (best 8.4 vs tol 5) but U fits at the Frederikse central and the gap is now fully literature-priced

- **`python/d1c_uncharted_cell.py`** (Marcus green-light): ANCH 2-block + exogenous
  F_unch(t) with U flat-prior on the scope-scaled P&M bounds [14.5, 41.8] mm; BOOK1
  (uncharted subtraction from the melt-to-date partition) + BOOK2 (r19-zero historical
  split); ablation arms repro/book/unc_sx2/unc_t5d × ANCH/MID/FREE + profile
  sensitivities (const/frontload/taper); pathological comparators re-fit per variant
  with matched U/δ freedom. Sanity 3/3; ANCH/repro ≡ D1 (|diff|=0.00); sx2 patho 52.82.
- **Verdict (`notes/handoff_2026-08-08_d1c_uncharted_verdict.md`): 0/14 feasible — the
  pre-registered prediction (feasible with δ≤1σ) FAILED** (const: 9.0 deficit, δ 1.2σ;
  taper: 8.4, δ 0.9σ). But: U FITS at 27.6–32.5 mm scope ≈ the Frederikse-expected
  central (31.7–32.5 global vs 32.35), not railed; early-century era logLs reach the
  noise floor; FREE/unc_sx2 deficit 0.55 (free dynamics + U fit the century at noise
  level — only the ν-spread coupling survives anywhere); profile ranking taper < const
  << frontload (frontload falsified; const's 1990 hard stop = step artifact ~0.6 logL).
  Residual ~8 logL localized to 1980–2023 with three priced candidates: bookfix→
  two-rung interpolation sensitivity (book-only ablation +2.5; modern rate 0.855→0.764),
  the Frederikse/GlaMBIE r19 modern-target seam, and late-century ν-shape.
- Abandoned within the cell: the frontload profile; and the notion that the 1990 profile
  step materially carried the deficit (taper bought only 0.6).
- Decision menu: D1d modern-seam cleanup vs accept-with-label (offline program complete)
  vs extC surgery directly (needs widened per-block T_off bounds). Marcus to rule.

## [unreleased] — 2026-08-08 (evening) — geometry-drift literature verdict: transient-physics version PARKED; verified scope mismatch (uncharted ice IS in the target, NOT in the model stock) covers most of the century-integral gap

- **`notes/memo_2026-08-08_geometry_drift_literature.md`** (all citations verified against
  primary sources). Mechanism A (state-dependent response times): qualitative support
  (JRW 1989; Christian 2018; Zekollari 2020 slope control; GlacierMIP3 2025 state
  dependence) but direction ambiguous for LIA-extended geometries and NO global
  quantification → no defensible prior; PARKED. Mechanism B (inventory-scope drift):
  Parkes & Marzeion 2018 — uncharted (missing + disappeared) glaciers contributed
  16.7–48.0 mm SLE 1901–2015 (0.17–0.53 mm/yr), explicitly absent from inventory-based
  models; **Frederikse 2020 (Parkes co-author) includes it in its glacier component**
  (confirmed via Gangadharan et al. ESD) → our GSIC target contains 17–48 mm of melt the
  model's V=0.290 present-RGI stock structurally cannot produce. Explains D1b's
  topology-invariance. Covers ~25–75% of t5d's fitted δ=0.69 mm/yr; residual within
  ~0.5–1.7σ of the ORIGINAL Roe prior. Roe 2021 initialization critique verified with
  specifics (mass-turnover τ, t* extrapolation, NAT-deficit implausibility) — T5d prior
  now literature-armed either way. NB GlacierMIP3 paper headline response times are 80%
  metrics; our pipeline uses regchar −50% columns (no bug).
- **Proposed (awaiting Marcus): D1c cell** — ANCH unchanged + exogenous uncharted-ice
  term F_unch(t) with the P&M prior (taper by 2000; r5-scope partition flagged) +
  optional T5d δ at the original prior. Prediction: deficit inside tol with δ ≤ ~1σ.

## [unreleased] — 2026-08-08 (later) — Marcus rulings after D1/D1b: T5c REJECTED; T5d acceptable; geometry-drift to be investigated for a literature basis

- **T5c (hindcast/projection hybrid) is OFF the menu** (Marcus: "I don't like T5c").
  **T5d (structured early-segment discrepancy) is acceptable.** **Geometry-drift**
  (state-dependent response times and/or inventory scope drift) to be scoped against the
  literature before any implementation. Literature verification launched for: JRW-1989
  response-time scaling, Roe/Christian/Marzeion attribution + initialization critique,
  Marzeion 2014 adjustment fraction, Zekollari 2020 Alps imbalance, GlacierMIP3 τ50
  definition, Leclercq 2011 independence, Parkes & Marzeion 2018 uncharted/vanished-ice
  contribution (candidate exogenous early-melt source absent from present-RGI models).

## [unreleased] — 2026-08-08 — D1b: splitting/reassigning the SLOW block does not recover the century integral; the cap is topology-invariant

- **Marcus: the D1 SLOW block (inert until ~1990, yet assigned ~33 mm of history) should
  maybe be split, or partly reassigned to FAST.** `python/d1b_slow_split.py` tests both
  against the unchanged D1 criteria (sanity 2/2; both pathological refs reproduce D1
  exactly). **Per-member two-rung diagnostic:** heterogeneity is real but does NOT map
  onto τ50 — r09/r07 carry their high commitment via STEEP b (threshold-like S_eq, ~96%
  loss by +2K) with T_off +1.6/+1.1, while the actual historical melters r03/r06
  (T_off −0.69/−0.93) have τ50 too slow to matter. **3BLOCK** (POLAR {19,03} / SUBPOLAR
  {09,07,06} / FAST) ≈ identical to D1 (ANCH deficit 20.6/12.0 vs 20.7/11.5; 4/4 gates;
  S2020 59 mm). **REASSIGN** (τ*≈500) much worse (1/4 gates, deficit 17.3–67.8): the
  merged FASTX composite T_off rises to −0.08, killing early excess and overshooting
  modern — the one-pool shape failure resurrected inside FASTX. 0/12 feasible.
- **Conclusion (`notes/note_2026-08-08_d1b_slow_split_verdict.md`):** the missing
  ~45–50 mm of pre-2000 melt is invariant to block topology — capped by GlacierMIP3
  response times + committed ladders + the exponential S_eq form. Reassignment is off
  the menu; the §6 decision menu (T5c / T5d-extended / geometry-drift κ(t) as new scope)
  stands. Abandoned: the hypothesis that τ-based splitting recovers equilibrium-proximity
  coherence (the two axes are independent in the data).

## [unreleased] — 2026-08-07 (late night 2) — D1 multi-reservoir cell EXECUTED: pre-registered FAIL (0/10) but first-ever 4/4-gate pass; tension isolated to the pre-2000 century integral

- **`python/d1_multireservoir_cell.py` built and run** (D0-exec pattern; sanity battery 3/3
  — blocks-sum identity 2.8e-17, ν=0 Mengel nesting exact, reproducibility; the sx2
  pathological reference reproduces T1's 52.82 exactly). Block anchors all data-derived:
  drivers = GlaMBIE-area-weighted per-region HadCRUT5; amp_b = regchar ISIMIP3 ratios
  (FLAGGED low: aggregate 1.34 vs amp_g 1.8 / obs-fit 1.59); (b_b, T_off_b) closed-form from
  the block's own two-rung EXACT GlacierMIP3 composite (moepy, cached:
  `outputs/d1_gmip3_steady_cache.nc` 71 KB + `d1_block_ladder_cache.csv`); (κ_b, ν_b) solved
  exactly from the block τ50 pairs (SLOW 665/159 → ν=1.35; FAST 130/37 → ν=1.60).
- **Verdict (`notes/handoff_2026-08-07_d1_multireservoir_verdict.md`): 0/10 pre-registered
  configs feasible** — ANCH passes ALL 4 gates out-of-sample in every variant (first
  structure ever; spread 6.5–6.9 cm in-band, modern rate 0.85 vs obs 0.81) but misses the
  1980–2023 flow criterion by 11.5–22.6 logL (tol 5). Anatomy: model S(2020)=57 mm vs target
  107 mm — the SLOW two-rung solve yields T_off=+0.465 glacier-K (preindustrial equilibrium,
  late-onset melt), so GlacierMIP3-consistent physics cannot produce the pre-2000 flow.
  POST-HOC MID arm (κ free, ν held at anchored): deficit unchanged, fitted κ ≈ anchored —
  the κ anchors are innocent; ν≥1.35 (the spread dial) carries the deficit. FREE rails ν→0
  (spread dies) but with NO P2 collapse (κ ratio 4.1). T5d absorbs half the deficit at
  δ=+0.69 mm/yr = 2.3σ of the Roe prior. Driver-swap control: per-block drivers ≈ 0 logL on
  aggregate flow. τ* and hist-split scans verdict-invariant. New sub-decision H (1850–2000
  melt split; Hugonnet default, scanned) flagged, not resolved.
- **Abandoned within this cell:** treating the FREE arm's shared-ν prior N(1.0,0.5) as able
  to hold ν up against the hindcast (it rails to 0 exactly as in D0/extB3 — reconfirmed);
  and the hypothesis that per-block DRIVERS carry the historical flow shape (the control
  killed it — the payoff is per-block S_eq frames + anchored transients).
- Structural decision (T5c vs T5b+T5d vs T5d-extended vs accept-with-label) awaits Marcus;
  no extC calibrator surgery until then.

## [unreleased] — 2026-08-07 (late night) — T5a multi-reservoir regional blocks = LEAD candidate; D1 offline cell specced

- **Marcus: multiple glacial reservoirs (T5a) is the lead candidate.** Handoff
  `notes/handoff_2026-08-07_t5a_multireservoir_lead.md` specs the D1 offline feasibility cell
  (no Julia surgery): 2 blocks by GlacierMIP3 response time (τ*=250 yr; SLOW = r19/r03/r09/r07/
  r06 ≈ 72% of stock, 71% of committed, 36% of modern melt, τ50 ~665→159 yr @1.5→3 °C; FAST =
  the rest incl Alaska), per-block drivers from `t_glac_regions_hadcrut5.csv` (area-weighted,
  per-block amp from GlacierMIP3 regional ratios), per-block (b,T_off) from the block's OWN
  two-rung ladder composite (exact per-experiment estimator, nc on disk), and an ANCHORED
  transient arm with (κ_b, ν_b) set by the block's two response times — making the hindcast an
  out-of-sample test — plus a free arm. Criteria = the T1 standard (4/4 adopted-anchor gates +
  1980–2023 flow within 5 logL of pathological) + per-block modern-split reports + the D0-style
  driver-swap control. T5d (early-segment discrepancy term) carried as a switch; failure mode
  pre-registered (P2-signature collapse → T5c/T5b+T5d discussion). Sub-decisions A–G flagged
  (block count/threshold, driver weighting, ν sharing, inventory partition basis incl the
  Gt-vs-Farinotti-SLE 0.343-vs-0.290 BSL note, optional Zemp-2019 fetch, σ×2-vs-discrepancy,
  ladder estimator). Calibrator-surgery scope sketched for planning only (extC tag family).

## [unreleased] — 2026-08-07 (night) — scope-corrected anchors ADOPTED in the gate machinery; T4 rejected; constraint-anatomy memo scopes T5

- **Anchors adopted (Marcus): `d0_glacier_shootout.py` gate constants swapped to the
  scope-corrected ladder** (37.4/46.3/63.0/75.5 central; [11.8,54.0]/[17.2,63.2]/[41.5,75.5]/
  [58.5,83.9] likely; sens 95 mm) with a provenance comment preserving the superseded published
  values; `d0_final` SC solve now derives COM12 from the same constant; eval/T1 inherit by exec;
  eval self-test still passes 4/4 on the C_nu1.0 point.
- **T4 REJECTED (Marcus) — new-structure scoping requested.** `python/diag_constraint_anatomy.py`
  + `notes/memo_2026-08-07_glacier_constraint_anatomy.md`: constraint inventory with per-item
  confidence; the one-reservoir arithmetic (rate = κ(a−S)(1−e^{−b·exc})exc^ν — gap and excess
  both functions of ONE state) showing the law demands 1.92× acceleration (2000-23/1920-49)
  where the target shows 0.76× (deceleration); branch A (fit-history) overshoots the
  best-measured modern rate 1.67× (1.36 vs target-derived 0.81 mm/yr, 2015-23) while
  under-melting the century (S2020 86 vs 107 mm); branch B (fit-modern-rate) misses total melt
  2.3×. **Corner scan: the ladder band floor (11.8%) is UNREACHABLE (the flow data's own slope
  forces more committed melt) and the overshoot is anchor-insensitive (1.36–1.51 mm/yr at
  com12 20–37.4%) — the tension is the SHAPE mismatch (monotone excess path vs non-monotone
  century flow), not the anchor level.** NB the target's own 2015–23 rate is 0.81 mm/yr, not
  the handoff's ~0.6 (GlaMBIE-2020 scope figure): overshoot ratios restated on the target basis.
  Per-region anatomy (S1a/S3/regchar/Hugonnet): stock-weighted response time 513 yr vs
  melt-weighted 285 yr, collapsing to 125 yr at ~3 °C (GlacierMIP3's own spread mechanism);
  regional warming spans 0.14–2.82 K — the single area-weighted driver mutes the ETCW that the
  early flow needs. Scoping menu: **T5a regional blocks (lead; per-region drivers/anchors/
  response times all on disk), T5b κ(T) single reservoir (only with T5d), T5c hindcast/projection
  hybrid (fallback), T5d early-segment discrepancy model (replaces σ×2)** — awaiting Marcus's
  §5 asks.

## [unreleased] — 2026-08-07 (evening 2) — T2 executed: GlacierMIP3 anchor scope-corrected (39→37.4 @1.2K), tension NOT dissolved; T1 offline test built

- **T2 (ladder-anchor scope correction) DONE — the anchor moves −1.7 pts at the +1.2K rung and
  the modern-flow overshoot only improves 2.00×→1.85×; the structural tension stands.** Data:
  GlacierMIP3 archive (Zenodo 10.5281/zenodo.15046588 v2; Zekollari 2025 Science adu4675) —
  small files tracked under `data/observations/raw/gmip3/`, the 1.47 GB per-experiment shifted
  netCDF untracked with a range-request re-fetch recipe (`python/scripts/remote_zip_extract.py`
  pulled 358 MB of ranged reads instead of the 984 MB zip).
- **Method (python/t2_gmip3_scope_anchor.py): replicate the paper's own 'All' estimators, then
  delta-transfer.** Reverse-engineered from GlacierMIP/GlacierMIP3: the published global CENTRAL
  = LOWESS median over 80 constant-climate experiments of the per-region model-MEDIAN composite;
  the published global BOUNDS were REPLACED downstream (0d aggregation notebook) and are ≈ the
  per-member composite over the 4 globally-covering models (PyGEM-OGGM_v13, GloGEMflow, OGGM_v16,
  GLIMB — their own cell-9 equivalence, confirmed on the only_global file). Replicated both
  estimators with moepy + the paper's frac auto-selection (selected 0.22–0.23 vs paper 0.23);
  **validation on full-RGI reproduces the published ladder: central max err 1.6, bounds max err
  2.1 pct-pts (PASS ≤3)**. A naive mass-weighted composite of per-region marginal quantiles
  over-disperses bounds by up to 11.5 pts (the authors' own "conservative regional sum" caveat) —
  kept in the CSV as a labeled cross-check arm only.
- **Final excl-r5-incl-r19 anchors (published + replicated scope delta):
  +1.2K 37.4 [11.8, 54.0]; +1.5K 46.3 [17.2, 63.2]; +2.0K 63.0 [41.5, 75.5]; +3.0K 75.5
  [58.5, 83.9]** (r5 is high-committed — 58% @1.2K — but only 9.8% of stock; r19 stays in scope).
  Scope sens 1.5→3K ≈ 95 mm SLE raw (full-RGI raw 109 / S1b BSL-corrected 98) — the shootout's
  85 mm report-constant was low under any basis. SC point under the new anchor: b 0.282,
  T_off −0.914, committed@1850 0.087 m, demanded gap 103 mm (was 108).
- **T1 offline two-reservoir-ν test built (python/t1_two_reservoir_offline.py)** — existence
  test at the SC point: fast/slow split (Nauels-ν fast pool share φ, linear slow pool τ_s,
  GlacierMIP3-response-time prior 463 [216–805] yr) + rate-cap arm, ν SCANNED not optimized
  (free ν rails to 0 and kills spread — same D0 non-identifiability), pre-1940 σ×2 likelihood,
  ladder/spread at calibrator amp 1.8, criterion = 4/4 gates AND 1980–2023 flow logL within 5
  of the free-N pathological optimum. First pass (pub anchor) validated the machinery: N1 ν=1
  at SC = 4/4 gates at deficit 21.2 (matches diag_pathology's −17.8−5.2 whitened attribution);
  free rate-cap hits deficit 0.3 but spread 0.0 (cap binds in projections — device rejected as
  a free fit).
- **T1 FALSIFIED (both anchors): 0/110 configs feasible** (4/4 gates AND 1980–2023 flow within
  5 logL of the pathological optimum). Binding gate = SPREAD (61% of the P grid; inventory/
  ladder/S1900 essentially never fail); monotone trade-off — flow-optimal low-φ cells saturate
  at spread 2.8–3.5 vs the 4.5 floor, and 4/4-gate cells exist only at φ=0.8
  (single-reservoir-in-disguise, deficit 15.6 vs single-N 16.8: the split buys ~1 logL). The
  two-NAUELS-pool variant (P2, slow pool keeps ν — quiet-now/mobilize-later) passes gates
  everywhere but its best deficit equals single-N ν=0.5 exactly, with fitted κ_s ≈ κ_f (the
  pools collapse). Ungated family floor ≈ 10 logL > the 5 tolerance. **Committed-ice retention
  and ν-spread load onto the same response; the split relocates, not resolves, the tension.
  Per the prior handoff's fallback logic, T4 (accept ν≈0 + labeled projection-ν sensitivity
  arm) is now the live default — awaiting Marcus.** Handoff:
  `notes/handoff_2026-08-07_t2_scope_anchor_t1_two_reservoir.md`.

## [unreleased] — 2026-08-07 (evening) — extB3/b/c ALL falsified; binding tension = modern flow vs GlacierMIP3 ladder; Dangendorf v2 SE adopted

- **All three tuning arms failed 0/4 gates on the same ν≈0.1 / T_off≈−1.8 mode** (extB3 baseline;
  extB3b + pre-1940 GSIC σ×2; extB3c + corrected Dangendorf σ — the last passes inventory at the
  median and improves S1900 to 34 mm, but spread stays ≤1.6 cm and ν piles at 0).
- **Diagnosis overturned the handoff item-7 framing** (`julia/diag_pathology_terms.jl` + whitened
  per-era attribution): flow_gsic alone buys the pathology (SC ν=1 point pays −25 logL; all other
  glacier terms favor SC +5); with early σ×2 active the price is MODERN (−17.8 in 2000–2023, −5.2
  in 1980–99, only −1.5 in 1900–19). Analytic check: ladder-demanded committed gap 0.105 m × κ·exc
  → 1.1 mm/yr at 2020 vs observed ~0.6 = 1.7× overshoot. **The single-reservoir ν transient cannot
  satisfy the GlacierMIP3 committed ladder and the GlaMBIE-era observed rate simultaneously**; the
  Roe/Marzeion early-segment question is resolved (σ×2 works), the remaining tension is structural.
  Decision menu (T1 two-reservoir/rate-cap; T2 ladder-anchor scope correction; T3 rejected; T4
  accept ν≈0) in `notes/handoff_2026-08-07_extB3_falsified_modern_flow_tension.md` — awaiting Marcus.
- **Dangendorf corrected Global_v2.nc ingested** (Sönke pers.comm.): old file's GMSL/SE slots held
  barystatic; v2 validates our Fields-derived dang values BIT-EXACTLY; SE is in meters
  (SE(2021)=2.68 mm). "Frederikse-sd conservative" claim falsified (true SE 1.3–2× larger
  1900–2010) → **dang_sig switched to native v2 SE** (Marcus), targets rebuilt (only dang_sig/lo/hi
  changed), prep script asserts units.
- Chains extB3/b/c + eval CSVs retained as falsification evidence; smoke junk deleted.

## [unreleased] — 2026-08-07 — extB3 tuning falsified (wiggle-tracking mode); extB3b σ-fallback launched

- **Gate machinery (`python/eval_chain_gates.py`)**: per-draw evaluation of the pre-registered
  gates on chain draws (2nd half), reusing the D0 formulas by exec (no new math). Hindcast on the
  calibrator driver convention (obs T_glac + 1.8×GMST splice); ladder/spread at amp_g 1.8;
  calibrator-bounds interior check; full-maxlag Geyer ESS; wiggle-mode co-indicators. Self-test
  reproduces the d0_final C_nu1.0 row (hindcast metrics to CSV precision, 4/4 gates).
- **extB3 tuning run (500k, seed 2026, accept 0.237, 36 min) FAILED gates 0/4** — the chain
  camped on exactly the wiggle-tracking mode pre-registered in handoff §2 item 7, all three
  co-indicators firing: σ_gsic → 0.032 cm (ρ 0.96), gic_nu piled at 0 (median 0.12,
  P(ν<0.05)=0.24 → scenario spread dead at 1.6 cm), S(1900) median 45 mm (P(>40)=0.77) with
  T_off dragged to −1.81 (10% from its bound; deep-offset partially back, committed@1850
  ≈ 0.155 m). Inventory z median −1.19; ladder over-committed (58/66/75/87%). Chain + eval CSV
  kept as the tuning evidence (`chain_extB3_seed2026_n500000.csv`, `eval_gates_extB3_seed2026.csv`).
- **extB3b = the documented fallback**: GSIC flow σ ×2 pre-1940 (Marzeion-2015-derived target
  segment = Roe-2021 initialization artifact; precedes the HadCRUT5 ETCW ramp ~1918). Flag-gated
  (`--gsic-early-sigma-x2`) so extB3 stays exactly reproducible; smoke-tested; 500k tuning
  relaunched under `--tag=extB3b`.
- Stale-comment fix: calibrator A2 header said S_raw(2020); code has used idx(2000) since the
  2026-08-06 Farinotti-epoch fix.

## [unreleased] — 2026-08-06 — D0 shootout: T_glac driver validated; ν needs a prior; deep offset was a driver artifact

- **T_glac data prep (`python/build_t_glac.py`)**: glacier-area-weighted observed temperature,
  HadCRUT5.0.2.0 analysis × GTN-G 2023 region polygons × GlaMBIE year-2000 area weights, scope
  excl-r5-incl-r19 (matches A2 V=0.290). ETCW in-driver 2.3× global (1930-40); amp_g fit 1.56-1.63
  vs GlacierMIP3 1.8. Pre-1898 gaps (r03 largest) filled by per-region OLS on global, flagged.
  New raw inputs documented in `data/observations/raw/README_modern_extensions.md` (HadCRUT5 nc
  untracked by size; GlacReg zip tracked).
- **D0 six-cell shootout (`python/d0_glacier_shootout.py`, follow-up arms in
  `python/d0_final_selfconsistent.py`)**: {Mengel-2τ, Nauels-ν} × {Gfair, Gobs, Tglac}.
  T_glac wins the decadal flow shape by ~+10 logL; the Gobs control shows the gain is the
  regional ETCW signal, not obs interannual variability. **ν rails to 0 in every arm** — the
  hindcast cannot identify ν (Nauels 2017 Table 2 fetched: κ 0.0079-0.0131, ν 0.096-0.445, fit
  to smooth CMIP5-forced projections); ν must enter via an informative prior.
- **Deep-offset pathology dissolved**: solving glacier-frame consistency directly (slope@0/amp_g,
  inventory at observed melt level, GlacierMIP3 39% @+1.2K) gives a 0.383 / b 0.286 / T_off
  −0.96 glacier-K ≈ −0.60 global-K (inside PAGES-2k amplified LIA minima), committed@1850 only
  0.092 m — the 0.20 m demand was the GMST driver compensating for missing regional warming.
  With ν ∈ [0.5, 2] at this point **all pre-registered gates pass simultaneously** (S(1900),
  inventory, GlacierMIP3 ladder, AR6-family scenario spread) — a first. Residual: 1900-1920 flow
  segment (Roe-2021/Marzeion-init-artifact question) — data-trust decision pending.
- **Tried and superseded within the session**: naive frame-scaled crossing (a .452, b .332,
  T_off −1.77) kept committed=0.20 and failed inventory/ladder — replaced by the direct solve;
  A2b-enforced (×25) optimization walked to a shallow-offset b-ceiling solution (ladder 92-100%)
  — enforcement alone does not find the healthy region.
- **GIS diagnostic (`python/diag_gis_regional_driver.py`)**: GIS melt rate correlates +0.71 with
  Greenland-region temperature vs +0.16 with GMST; Greenland ETCW 5.5× global; Greenland cooled
  −1.8 °C/century 1940-90 while global warmed. GIS = confirmed Option-D candidate (own
  workstream). TE = OHC story, no regional-T fix; AIS already has A6.
- Decision menu for extB3: memo §5-D0 (ν prior, early-century σ, amp_g, T_glac freeze, GIS timing).
- **extB3 implementation (2026-08-07)**: `julia/glaciers_nu_component.jl` (Mengel S_eq +
  Nauels-ν single-reservoir transient, melt-only clamp, driver param renamed
  `glacier_surface_temperature` to enforce the frame contract), `build_brick_nu`/
  `update_brick_nu!`/`set_glacier_forcing!` added to `brick_mengel.jl` (old paths kept for
  provenance), `calibrate_mcmc_ext.jl` rewired (T_glac driver + 1.8×GMST splice; gic block
  (a, b, T_off, log10κ, ν) with glacier-frame priors, b re-centered 0.29; 39→38 params;
  extB2 proposal covariance name-mapped, glacier rows fresh). Port validation
  `validate_glaciers_nu.jl` + `validate_glaciers_nu_compare.py`: Julia↔Python 1e-16,
  ν=0≡Mengel nesting 4e-19, non-glacier components bit-identical across the swap
  (AIS feels the glacier via global_sea_level coupling — matched-glacier A/B). 50-iter
  smoke test PASS (accept 0.36, finite start). Tuning run (500k, --tag=extB3) NOT yet launched.


## [unreleased] — 2026-08-05 — Mengel A0 confirmed; A1-LIA falsified; component review vs FACTS/AR6

- **A0 offline profile (`python/a0_mengel_profile.py`) CONFIRMED the T_lia-floor diagnosis** on all
  three handoff predictions: (P1) the algebraic (a,b|T_lia) curve crosses inventory-consistency at
  T_lia −1.14 / a 0.486 / b 0.464 (full-RGI) — Mengel's published values; (P2) the GSIC profile
  likelihood improves monotonically past the −1.00 floor and the railing is driven by the pre-1950
  target years; (P3) freeing `gic_sl0` absorbs the committed-melt demand but degenerates (a→∞, b→0)
  without an inventory term.
- **A1 as specified (widen T_lia from an LIA reconstruction) is FALSIFIED by the reconstruction:**
  PAGES 2k global LIA = −0.03..−0.14 °C rel 1850-1900 (tail −0.45); amplified glacier-region minima
  −0.5..−0.65. **Mengel 2016 has no T_lia at all** (equilibrium ≡ 0 at preindustrial; natural melt
  subtracted from calib data via Marzeion 2014, contested by Roe 2021). The parameter must be
  reinterpreted as an effective disequilibrium offset — GlacierMIP3 (Zekollari 2025: 39% of glacier
  mass committed at PRESENT climate) supports the ≈−1.1 offset physics while killing the LIA label.
  A pure sl0 (initial-state) fix fails GlacierMIP3 outright — tried on paper, abandoned.
- **A2 scope finding (agent-verified, Hock 2023):** the Frederikse glacier target EXCLUDES peripheral
  regions 5+19 → scope-matched inventory 0.221±0.057 m SLE vs full-RGI 0.324±0.084 (the 0.32
  `gic_a` floor). Our spliced GSIC target is internally scope-mixed (GlaMBIE tail includes
  peripheries). Scope choice = open decision; only the full-RGI crossing passes GlacierMIP3.
- **B1 hindcast stats on extA108** (`python/b1_component_hindcast_stats.py`): AIS now clean (the 1900
  overshoot is resolved); GIS/GSIC undershoot 1950-1993; TE overshoots pre-1950.
- **B2 projections review**: BRICK-AM per-component 3-SSP bands to 2300
  (`julia/project_ssps_components_2300.jl`); FACTS `global.coupling.{ssp126,ssp585}.n200` runs
  (native FaIR-1.6.4 climate needed `fair==1.6.4` baked into the image — the neutered-pip fix had
  broken the climate step); comparison table + figure
  (`python/b2_component_comparison.py`, `python/plot_b2_component_comparison.py`). Headlines @2100
  vs AR6 T9.9: glaciers low + spread-collapsed (0.8 vs 9 cm across SSPs); AIS too binary (low at
  SSP1-2.6, 46 vs 12 cm at SSP5-8.5, runaway post-2100); GIS modestly low; TE/LWS in family;
  total scenario-sensitivity ~2× AR6's.
- **A5 recalibration NOT launched** — §5 decision menu (inventory scope, GlacierMIP3 role, sl0,
  offset prior) in `notes/memo_2026-08-05_mengel_a0_results_and_recalib_options.md` awaits Marcus.

## [unreleased] — 2026-08-03 — Headline metric table complete; component-split claim refuted

- **The §0 table's missing pulse-relative cells are filled** (stochastic arms; deterministic still
  running). `python/metric_horizon_table.py` forms both metrics identically — ensemble MEAN marginal
  per GWP-100-equivalent tonne, so CO₂ ≡ 1.0 and the CH₄ entry *is* the metric:

  | yr after pulse | calendar | temperature (GTP-style) | total SLR | SLR ÷ temperature |
  |---|---|---|---|---|
  | 20 | 2050 | 3.70 | 4.63 | 1.25× |
  | 70 | 2100 | 0.79 | 2.24 | 2.82× |
  | 100 | 2130 | 0.52 | 1.68 | 3.23× |
  | 120 | 2150 | 0.45 | 1.45 | 3.23× |
  | 150 | 2180 | 0.38 | 1.22 | 3.18× |
  | 270 | 2300 | 0.24 | 0.79 | 3.34× |

  At the GWP-100-matched **100-yr** horizon an SLR metric values CH₄ at **1.68×** its GWP-100 while an
  endpoint-temperature metric values it at **0.52×**. The divergence is only ~1.25× at 20 yr and
  saturates near 3.2× from 100 yr on — it *opens with horizon*, it is not a fixed offset.
  **The SLR÷temperature column is GWP-INVARIANT** (the basis cancels), so the headline does not
  depend on the open GWP-basis choice (§4.3) — that choice moves both metrics identically.
- **REGRESSION PASS:** at the four horizons the earlier 4-horizon `_subann` run also covers, the
  6-horizon `_pr` run is **bit-identical** (worst relative difference 0.00e+00), confirming the
  2026-08-02 metric-packing fix (hardcoded offset `4` → `length(HORIZONS)`) perturbs nothing.
- **Research-plan §1 contribution 1: first example REFUTED, second CONFIRMED** (CLAUDE NOTE added at
  the claim, not a rewrite — Marcus's call on wording).
  - "CH₄-TE-led vs CO₂-AIS-led split" is **not supported**: both gases are AIS-led with near-identical
    shares and the small difference runs *opposite* to the claim (AIS @2130 CO₂ 78.8% / CH₄ 79.6%;
    TE 15.8% / 14.1%).
  - "Crossover horizon shifts vs a thermosteric-only estimate" **is** supported and is the stronger
    claim: a TE-only calculation gives 0.84–0.89× the full-SLR metric and crosses parity **~57 yr
    earlier (TE-only ~2184 vs full SLR ~2241)**. Both interpolated between bracketing horizons; the
    ~57 yr *shift* is the robust quantity, the levels are ±a decade or two.
  - `te@2300` was spliced from the `_subann` runs (the `_pr` run's comp-years were 2130/2150/2180);
    legitimate because the two runs are bit-identical at shared horizons. **Future runs should put
    2300 in `--comp-years`** so no splice is needed.
- **Tried and rejected:** extrapolating the full-SLR crossover off the short 2150→2180 segment gave
  ~2208 vs ~2241 when interpolating across the bracketing 2180→2300 segment — the metric is convex in
  horizon, so short-segment linear extrapolation overshoots the decline. Interpolate between horizons
  that actually bracket parity.
- **Basis sensitivity settled for the headline (§4.2):** stochastic and `_nonoise_flatsolar` agree on
  the MEAN to within **1.4% at every horizon**, on both the SLR metric and the SLR÷temperature ratio.
  For the headline table the basis choice is **immaterial**; it remains material only for the
  tip-fraction / mode decomposition (23% vs 33%), which is a separate open question.
- **Fossil-CH₄ arm complete (stochastic).** Wide files `_ch4foss1tg{,_nonoise_flatsolar}` built; the
  zero-pulse gate on the new basis **PASSED** (every metric exactly 0.000e+00 across all 6 horizons
  and all components). Fossil (GWP-100 = 29.8) vs biogenic (27), stochastic:

  | yr | SLR bio | SLR foss | temp bio | temp foss | SLR÷temp bio | SLR÷temp foss |
  |---|---|---|---|---|---|---|
  | 20 | 4.63 | 4.23 | 3.70 | 3.42 | 1.25 | 1.24 |
  | 70 | 2.24 | 2.11 | 0.79 | 0.81 | 2.82 | 2.60 |
  | 100 | 1.68 | 1.60 | 0.52 | 0.56 | 3.23 | 2.85 |
  | 150 | 1.22 | 1.19 | 0.38 | 0.44 | 3.18 | 2.71 |
  | 270 | 0.79 | 0.80 | 0.24 | 0.31 | 3.34 | 2.62 |

  Two consequences. (1) **The >3× divergence is a BIOGENIC-CH₄ statement** — the oxidation CO₂ makes a
  fossil pulse more CO₂-like and compresses it to ~2.6–2.85×. Both are large, but the arm must be
  labelled. (2) **GWP-100 = 29.8 increasingly UNDER-corrects for the oxidation carbon**: the physical
  fossil/biogenic marginal ratio climbs 1.02 → 1.13 → 1.27 → 1.43 at 20/70/150/270 yr against a fixed
  GWP ratio of 1.104, so by 270 yr a fossil tonne is worth ~1.29× its biogenic counterpart per
  GWP-equivalent tonne on temperature. (A fixed 100-yr integral cannot track a 270-yr endpoint.)
  See the FaIRtoFrEDI CHANGELOG for the fossil two-pass concentration-leak fix that preceded this.
- **GOTCHA documented in the driver header — `_arg` is `findfirst`, so the FIRST occurrence of a flag
  wins and later repeats are silently ignored.** A queued fossil job built its command as
  `"$BASE_ARGS $OVERRIDES"`; the intended 3-config zero-pulse smoke gate therefore ran as a full
  841×2000 production job (harmless — it produced the valid production stochastic arm, and the real
  zero-pulse gate was run afterwards and passed — but it cost a duplicate ~50 min run, which was
  killed mid-flight with the depot verified pristine afterwards). Never append overrides; state each
  flag exactly once.
- **Sequencing rule reaffirmed:** BRICK arms must never run concurrently under `run_subannual.sh` —
  the wrapper patches the SHARED MimiBRICK depot and restores it via an EXIT trap, so a second
  wrapper's trap would swap the integrator under a live run. Killing the *only* running wrapper is
  safe (the trap restores pristine, which is the desired end state) and was verified by diff.

## [unreleased] — 2026-08-02 — Metric framing, pulse-relative horizons, safe-patch wrapper

- **KEY MESSAGE fixed (Marcus):** CH4's SLR impact is much longer-lasting than its temperature impact,
  and that drives the CO2/CH4 comparison — an SLR metric values CH4 ABOVE GWP-100 while a GTP-style
  metric values it WELL BELOW. Quantified per GWP-100-equivalent tonne (CO2 ≡ 1.0), years after pulse:
  temperature 0.79/0.52/0.45/0.38/0.24 at 70/100/120/150/270 yr vs SLR 2.24 @70, 1.45 @120, 0.79 @270 —
  the two metrics differ by >3× at matched horizons. Component attribution is an intermediate step, NOT
  the headline (earlier framing over-elevated it).
- **`--horizons=` / `--comp-years=` flags**: the paper's key variable is YEARS SINCE THE PULSE (100/150
  yr = 2130/2180 for a 2030 pulse), not calendar 2100/2150. 4-arm re-run launched on
  2050,2100,2130,2150,2180,2300.
- **BUG FIXED — metric-packing offset was hardcoded `4 + 4*(ci-1)`** instead of `length(HORIZONS)`; with
  >4 horizons component writes clobbered horizon slots and left `met` partly uninitialized → NaN.
  **Caught by the zero-pulse gate.** No prior result affected (identical expression at 4 horizons;
  default-horizon re-run byte-compares 0.0 vs the original pre-change reference) — no quarantine.
- **`scripts/run_subannual.sh`**: applies the sub-annual DAIS patch and GUARANTEES restore via an EXIT
  trap (success/failure/interrupt), resolving the depot from the MimiBRICK `julia_v2` actually loads.
  The patch mutates a SHARED depot file, so a crashed hand-patch would silently change later jobs.
- Handoff: `notes/handoff_2026-08-02_ch4co2_metric_horizons.md`.

## [unreleased] — 2026-08-02 (late) — CH4 pulse arm: per-gas SLR marginals on BRICK-AM

- **FaIR CH4 biogenic 1 Tg @2030 pulse** (SSP2-4.5, 841 cfg, stochastic + `_nonoise_flatsolar`);
  pre-pulse marginal exactly 0.0 (paired seeds); wide files dumped; CH4 and CO2 arms share the SAME
  baseline (verified: 2.5e-12 cm through BRICK, zero tip-classifier disagreements) → cleanly paired.
- **Headline (MEAN total-SLR marginal, sub-annual, per GWP-100=27 CO2e): CH4/CO2 = 2.24 @2100,
  1.45 @2150, 0.79 @2300** — reproduces the research plan's placeholder crossover (~2.2-2.3 / ~1.4 /
  0.6-0.7) on a DIFFERENT posterior (BRICK-AM vs pre-FM Mengel) and DIFFERENT backbone (SSP2-4.5 vs
  RFF-SP). Basis-insensitive: stochastic vs deterministic agree to 0.04-1.7%.
- **FLAG — contradicts a stated paper novelty claim.** The research plan (§1 contribution 1) expects
  component resolution to reveal a "CH4-TE-led vs CO2-AIS-led split". It does NOT, here: BOTH gases
  are AIS-led with near-identical component shares (@2100 AIS 76% CH4 vs 75% CO2; TE 17% vs 19%), and
  the CH4/CO2 ratio is roughly uniform ACROSS components (2.26/2.66/2.59/2.05 for ais/gsic/gis/te).
  The real differential is in the DECLINE RATE: TE's ratio falls fastest (2.05→0.53 by 2300), AIS
  slowest (2.26→0.82). The crossover is a timing effect that scales all components, not a component-mix
  difference. The novelty argument needs rebasing on that, or the claim dropped.
- **FLAG — tip-classifier threshold needs re-tuning.** The documented baseline-AIS@2100 > 20 cm
  classifier (mimibrick-quirks item 11, calibrated on LHS-10k where it selects ~5%) selects **37.6%**
  on BRICK-AM extA108 (amp 1.08 puts far more mass near tipping; baseline AIS p50 6.99 / p75 32.50 cm).
  MEANS are classifier-free and unaffected; only the mode decomposition depends on this choice.

## [unreleased] — 2026-08-02 — Paired pulse arm + fast engine; production run locally (Torch now optional)

- **`weight_and_project_brick_fair.jl`: paired 10-GtCO2 pulse arm** (`--pulse=off|on|zero`,
  `--basis=`, `--pulse-gt=`, `--out-tag=`). Pulse runs in-process on the same model instance right
  after each baseline run (exact per-(config,draw) pairing); per-pair Δ dumped
  (`wong_cond_pulse_pairs*.csv`, 16 base + 16 Δ metrics — too big to commit; all statistics
  recomputable in post). Defaults reproduce the staged driver BYTE-FOR-BYTE (verified).
- **Fast engine (`--engine=fast`, default): ~30× — and it saved the Monday launch.** Discovery: any
  `update_param!` triggers a ~14 ms Mimi rebuild of the 451-yr model per run (integration is ~2 ms;
  `diag_wpf_runtime_breakdown.jl`), so the staged full run was ~12–14 h, not the estimated 1–2.5 h —
  it would have TIMED OUT on cpu_short. Fast path mutates the built instance in place (shared-backing
  SubArray views for forcing; ScalarModelParameter boxes for scalars; `run(mi)` — Mimi 1.6.0 internals)
  → 0.88–1.3 ms/run. Bit-identical to legacy: per-component, full-smoke CSVs, and the 24k-pair
  60cfg×400draw pulse run all byte-compare clean; `--engine=legacy` kept for A/B.
- **Five-test battery PASS** on the pulse arm (`python/check_pulse_battery_wpf.py`; companion ±10/+20
  GtCO2 FaIR arms dumped to `curv_wide` via `dump_fair_wide_curv.py`): zero-pulse Δ=0.0 exactly;
  sign-flip −1.000..−1.005 and doubling 0.998–1.000 on linear metrics; AIS shows genuine convex
  tipping asymmetry (dbl 1.06@2100 → 1.25@2300); cross-process bit-reproducibility; first-principles
  vs the 7.7e-3 cm/GtCO2 artifact reference (flag: 60-cfg preview medians ~4.7e-3 — reconcile on the
  full run before quoting).
- **60cfg×400draw preview:** conditional weighting leaves the pulse-marginal MEDIAN ~unmoved (+0.2%)
  and trims the AIS-tipping upper tail (95th −1.7% @2100, −4% @2300) — the coupling bites in the tail.
- **Full production COMPLETE, locally** (4 runs × 3.36M BRICK runs: {stochastic, nonoise_flatsolar} ×
  {annual, sub-annual patch}; depot patched from `julia/patches/` with backup and RESTORED pristine).
  **Headline results:** (1) levels — coupling immaterial (total@2100 COUPLED 46.68 vs INDEP 46.38 cm,
  width −0.68); (2) **pulse marginal — coupling ALSO immaterial** (mean ratio 1.003–1.009, TE 1.000,
  tip fraction 23.31→23.41%): the "may matter more on the marginal" conjecture is answered NO — the
  independent pipeline stands everywhere, unblocking the CH4/CO2 comparison; (3) sub-annual patch
  REQUIRED for quotable pulse numbers — cross-product mean @2100 1.469e-2 cm/GtCO2 reproduces the
  artifact's 1.498e-2 within 2%, driver-basis-consistent to 0.05%; the pooled MEDIAN is sample-fragile
  (23–33% tip-advance mode puts the 50th pctile in the bimodal density gap — quote mean or
  mode-decomposition, never bare pooled median); (4) the patch is a perfect no-op at mean forcing
  (ℓ^B bit-identical) but 401/1.68M hot-config × low-threshold pairs cross DAIS pre-2026 (ℓ^FB
  changes; immaterial). Annual-step pulse outputs re-tagged `_annualstep` (diagnostic only). Torch
  demoted to optional cross-check.

## [unreleased] — 2026-08-01 (late) — Conditional Wong-weighting: BRICK-AM draws consistent with FaIR

- **`julia/weight_brick_conditional_fair.jl`** — the ENDORSED forward-propagation consistency method (the
  correct alternative to the rejected joint calibration). For each FaIR config *k* it reweights the BRICK-AM
  posterior draws by historical-SLR consistency, `w_{i|k} ∝ exp[c·(ℓ^FB_{ik} − ℓ^B_i)]`, **normalized WITHIN
  each config** so `p(config)` stays uniform — every FaIR parameter set stays equally likely; SLR never
  touches the forcing marginal. `ℓ^B` at the mean (calibration) forcing so the ratio isolates the pairing
  and cancels the intrinsic fit (mitigates the Mengel double-count). Reuses `calibrate_mcmc_ext.jl` (now
  behind a `PROGRAM_FILE` guard) for the FREE list + θ→BRICK apply + dang-channel AR(1) likelihood.
- **Validated locally (60 configs × 400 draws):** (1) mean-forcing recovery — max|ℓ^FB−ℓ^B|=0, weight
  ESS/N=1.000 (exactly uniform at the calibration climate); (2) coupling signature — corr(weight, te_α)
  vs config OHC@2018 = −0.46 (hottest configs −0.156, coldest +0.113: hot ocean-heat down-weights high-te_α
  draws, TE∝te_α·OHC); (3) gentle, c=0.145 → mean conditional ESS/N=0.60 (≈ Tony's c≈0.2 for GMSL-only).
- Recovers the te_α↔OHC coupling in PROPAGATION, forcing marginal untouched.
- **Launch code built** (`julia/weight_and_project_brick_fair.jl` + `slurm/weight_and_project_brick_fair.sbatch`):
  one BRICK run per (config, draw) to 2300 yields BOTH ℓ^FB (weight) AND future SLR (bands); reports
  COUPLED (conditional-weighted, config equal) vs INDEPENDENT (equal) bands at 2050/2100/2150/2300 + comps.
  Local smoke (5 cfg × 100 draws) runs clean. **HELD for Monday launch (fairshare recovery)** — full run
  = DRAWS=2000 CONFIGS=all (~1.68M runs to 2300, fits cpu_short 4h). Run the 5-cfg smoke on Torch first.

## [unreleased] — 2026-08-01 — Joint FaIR/BRICK forcing calibration: BUILT, TESTED, **REJECTED**

- **Tried and abandoned.** Question (Marcus 2026-07-24): does jointly calibrating BRICK params + the
  FaIR forcing (recovering the `te_α↔OHC` coupling the mean-forcing shortcut drops) beat the shortcut?
- **Built:** `julia/diag_coupling_reweight.jl` (step-1 proxy), `calibrate_mcmc_joint.jl` (discrete index,
  mixed poorly), `calibrate_mcmc_joint_cont.jl` (continuous K=3 forcing-PCA reparam; basis
  `outputs/forcing_pca_basis.csv` via `python/precompute_forcing_pca.py`), `project_slr_joint_cont.jl`
  (deliverable R̂), `project_slr_coupling_test.jl`. Torch run: 4×4M chains, acceptance 0.237, recovery
  bit-identical to ext, deliverable total-SLR R̂ 1.001 (converged).
- **Result 1 — coupling real:** pooled corr(te_α, fpc2/fpc3) = −0.52/−0.61, te_α R̂ 1.004.
- **Result 2 — coupling IMMATERIAL to total SLR:** shuffle test tightens the TE component ~29 % but only
  −2.3 %/−0.55 cm on total @2100 (AIS tipping tail dominates).
- **Result 3 — freeing the forcing is HARMFUL:** the SLR likelihood re-inferred the forcing, drifting
  fpc1 (the ±0.68 °C ECS/atmosphere mode) to bend GMST **−0.28 °C @2100** (→ −0.48 @2300) vs the ensemble
  mean; this (not the coupling, not the params) drove the entire joint-vs-extA108 gap (−7.7/−45/−122 cm).
  The joint's lower SLR is low for the wrong reason.
- **Reason for rejection (Marcus 2026-08-01):** SLR must not re-infer atmospheric variables (forcing/ECS)
  that other data constrain far better; PROPAGATE FaIR uncertainty forward, don't RE-CALIBRATE it. OHC-only
  freedom also rejected (double-count vs FaIR's OHC constraint + te_α↔OHC degeneracy → low-value).
- **Canonical BRICK-AM stays `calibrate_mcmc_ext.jl` (mean forcing) + forward-propagated FaIR uncertainty.**
  Joint drivers retained, banner-marked DIAGNOSTIC/REJECTED. Full record:
  `notes/negresult_2026-08-01_joint_forcing_calibration.md`, memory `project_fair_brick_coupling_joint_calib`.

## [unreleased] — 2026-07-22 (late 3) — OHC time-component test: CONFIRMED (second-order)

- `python/reduce_cmip6_ohc_deck.py` (zostoga = thermosteric SLR, OHC proxy, 17 DECK models)
  + `python/diag_pai_ohc.py`: test whether OHC carries the Antarctic time-component that
  GMST alone misses. Fit ΔT_ant ~ α·ΔGMST (M1) vs α·ΔGMST + β·ΔOHC (M2), pooled over
  1pctCO2 + abrupt-4xCO2 (decorrelated in abrupt → identifies β).
- **RESULT — Marcus's hypothesis CONFIRMED, second-order:** β_OHC > 0 in **17/17** models;
  partial correlation r(T_ant, OHC | GMST) **positive in 17/17, median 0.46**; a GMST+OHC
  map fit on abrupt-4xCO2 predicts 1pctCO2 with **~40% lower error** (transfer RMSE
  0.98→0.61 K) and tracks the abrupt slow-rise GMST-only under-predicts. But within-scenario
  R² barely moves (0.94→0.95) — OHC is the cross-pathway/time correction GMST cannot supply,
  not a dominant term. Earns its keep for stabilization/long-horizon, not ramp projections.
- A6 note proposal 5B upgraded "OHC candidate" → **tested/confirmed** with Figure 3; caveat
  + provenance added; PDF re-rendered (now 3 figures).

## [unreleased] — 2026-07-22 (late 2) — denominator/aerosol test; terminology + note polish

- **New `python/reduce_cmip6_hemis.py` + `python/diag_pai_denominator.py`**: test Marcus's
  hypothesis that the mid-century amplification-ratio noise is a global-denominator (NH
  aerosol) artifact. CONFIRMED: mid-century NH aerosols depress the global mean below the
  SH mean (1980: global 0.31 K < SH 0.35 K), inflating the Antarctic/global ratio to a
  ~1.7 peak ~1980 that relaxes as aerosols clear; referencing to the SH mean halves the
  inter-model IQR (0.97→0.46 @1980) and removes the peak. (SH ref not usable for `a` — it
  settles ~1.39 since the SH warms less than the globe — but confirms the noise mechanism.)
  Textbook aerosol signature in `outputs/diag_pai_denominator.png`.
- **A6 note updates** (Marcus review): (1) ratio renamed "secant/level ratio" →
  **"Antarctic amplification ratio"** throughout (note + Figure 1 labels); T_AIS notation
  dropped from the figure; (2) the polar-cap/mask discussion moved to a **footnote**;
  (3) the aerosol/denominator finding added as a footnote; (4) proposal 5B gains **OHC as
  the observable slow-mode predictor** (already a BRICK input); (5) note serif switched
  Charter→Georgia (clean capital A). PDF re-rendered.

## [unreleased] — 2026-07-22 (late) — switch scenario diagnostic to the SECANT ratio; a ≈ 1.08

- `diag_pai_cmip6_time.py` reworked from the 41-yr windowed MARGINAL trend ratio to the
  **secant (level) ratio** R = (T_AIS−T_AIS,PI)/(T_glob−T_glob,PI), 30-yr running means,
  pre-1950 dropped (Marcus's request — the secant is what BRICK `a` actually is, so no
  marginal→level integration needed).
- **RESULT: the direct secant is ≈1.06–1.10 at crossing-relevant warming (2.5–3.5 K) and
  nearly FLAT across 2–5 K** (ssp245/ssp585 collapse). This CORRECTS the earlier
  integrated-marginal estimate of 0.97–1.03, which was biased ~0.1 low by a too-low
  extrapolated ΔT→0 intercept. The corrected secant now AGREES with the DECK 1pctCO2
  GHG-only secant (1.07–1.13), so the previously-claimed ~0.08 "aerosol suppression gap"
  was an artifact and is retracted.
- **A6 note consequences:** proposal A center moved 1.00 → **1.08** (`a ~ N(1.08, 0.15)`,
  equilibrium 1.196 now at +0.7σ); the "Level vs marginal slope" section deleted (moot);
  proposal B's marginal amp(ΔT) exponential replaced by the DECK two-mode map
  T_ant−T_ant,PI ≈ 1.08·ΔT_fast + 1.70·ΔT_slow; Figure 1 + captions synced. PDF re-rendered.

## [unreleased] — 2026-07-22 (evening) — DECK 1pctCO2/abrupt-4xCO2: the time component IS real

- `python/reduce_cmip6_tas_pai_deck.py` + `python/diag_pai_deck.py`: 41 models, GHG-only
  (aerosols/ozone at piControl — the confound-free test), anomalies rel. piControl mean.
- **At matched warming (2.5–4.5 K), amplification depends on forcing AGE**: abrupt-4xCO2
  reaches those levels ~6–22 yr after forcing (level ratio 0.93–1.11); 1pctCO2 takes
  ~100–124 yr (1.07–1.13). Paired D = −0.13…−0.08, bootstrap CIs exclude zero. The
  scenario-based null was an estimator-power result, not absence: cross-SSP forcing-age
  contrasts are ~10× smaller than the DECK contrast.
- **abrupt R(t) climbs 0.95 → ~1.2 over ~100 yr and asymptotes at 1.23 [IQR 1.11–1.45]**
  ≈ the DAIS equilibrium 1.196 (n=2 runs to 300 yr hint slightly higher). Gregory
  fast/slow-mode slopes: 1.08 / 1.70 — the slow (deep Southern Ocean) mode is strongly
  polar-amplified and drags the ratio up with time.
- Interpretation: along century-scale ramps, level and forcing-age co-vary, so the
  scenario amp(ΔT) closure silently absorbs the time dependence (fine for ramp-like
  futures); it would misextrapolate under stabilization (amp keeps rising while ΔT
  stalls) — relevant to post-2100/2150 horizons. 1pct GHG-only level ratio at 2.5–3.5 K
  (~1.07–1.13) sits ~0.08 above the scenario-based secant (0.97–1.03), consistent with
  ozone/aerosol suppression baked into real-world trajectories.

## [unreleased] — 2026-07-22 (later) — 5-scenario level-vs-rate test: NO identifiable rate component

- Added ssp119/ssp126/ssp370 to the PAI reduction (`python/reduce_cmip6_tas_pai_ext.py`,
  same members as the base pull; `data/cmip6_pai/tas_series_ext_*.csv`) and a level+rate
  decomposition (`python/diag_pai_cmip6_rate.py`): matched-warming table + joint fit
  pai = 1.196 − (1.196−a0)exp(−dT/Ts) − c·rate on the 32-model common subset.
- **RESULT: the rate/time component is NOT identified** — c = −0.50 [−0.91, +0.11]
  per (K/decade), CI spans zero, sign driven entirely by ssp126's degenerate stabilized
  windows; with the three well-behaved scenarios (245/370/585, rates 0.25–0.5 K/dec) the
  residuals from the level-only fit are flat in rate. The ssp245>ssp585 crossover at
  2.5–3 K that motivated the test is NOT corroborated as a rate effect (ssp370, nearly as
  fast as 585, sits with 245).
- Two contaminations diagnosed and filtered (named constants): ozone-hole/aerosol-era
  windows (centres <2005; median Antarctic trend negative under non-GHG forcing) and
  stabilized windows (global trend <0.10 K/dec; trend-ratio estimator degenerates +
  ozone-recovery confound — visually obvious for ssp119/126 post-2040).
- Conclusion: the level-dependent amp(ΔT) form stands as the supported parsimonious
  model; a genuine time/rate test needs idealized runs (1pctCO2 vs abrupt-4xCO2) or a
  single-model large ensemble, which remove the composition confound.
- **SSP3-7.0 subsequently EXCLUDED from the analysis** (Marcus: it is the aerosol
  outlier; SH forcing-mix confound). Rerun on the 33-model {126,245,585} subset:
  conclusion unchanged — c = −0.64 [−1.06, +0.07], matched-warming flat at 2.0–2.5 K
  (245 1.13 vs 585 1.14 @2.5 K); the crossover survives only in the 3.0 K bin. The A6
  note gained §4 (multi-scenario test) + Figure 2 and was re-rendered to PDF.

## [unreleased] — 2026-07-22 — PAI-vs-time diagnostic (CMIP6): amp rises with warming; A6 prior reference-frame flag

- **New `python/reduce_cmip6_tas_pai.py`** (streams Amon tas for 35 models from the public
  Pangeo/GCS zarr archive; annual global + AIS-proxy means to `data/cmip6_pai/`, 780 KB total)
  and **`python/diag_pai_cmip6_time.py`** (windowed 41-yr trend-ratio PAI1, Xie-2022 gate,
  collapse test) + **`python/diag_pai_mask_sensitivity.py`**.
- **RESULT (34 models, land≥50% south of 60°S):** within-scenario PAI1 RISES in both SSP2-4.5
  (+0.035/decade; median 1.06→1.19) and SSP5-8.5 (+0.016/decade; 1.13→1.19), and the two
  scenarios roughly COLLAPSE onto one curve in global warming level: ~0.9 at ΔT≈0.7 K rising
  to ~1.15–1.2 by ΔT≈2 K, then flattening at ≈ the DAIS equilibrium value 1.196. Supports a
  warming-level-dependent GMST→AIS amplification interpolating transient→equilibrium.
- **MASK FINDING (A6 flag):** our land-only AIS metric gives full-window (2015–2100) PAI1
  1.13/1.16 (ssp245/585) — Xie et al. 2022's 0.95/1.03 is instead reproduced by the ALL-points
  polar-cap mask (6-model test: cap60 0.92/0.98). Xie's "AIS" metric is cap-like; DAIS's
  temperature lineage (ice-core/continent) argues for the land-referenced number, so the A6
  transient prior N(0.95, 0.10) may sit ~0.15 low in DAIS's reference frame — which would
  overstate the transient-vs-equilibrium contrast and part of the phase-2 76→40 cm drop.
  Flagged for the M5/A6 revisit; NOT resolved here.

## [unreleased] — 2026-07-21 — artifact pulse-MEAN column (sub-annual) + BRICK-FM write-up

- **New `julia/diag_subannual_pulse_means.jl`**: full-ensemble 10-GtCO₂ pulse means under the
  temporary sub-annual DAIS-crossing depot patch (applied for the run, restored after), both
  calibrations × both drivers → `outputs/crossmodel_pulse_means_subannual.csv`. Also writes the
  equilib posterior subsample `data/MimiBRICK/parameters_subsample_brick_mengel_extA6eq.csv`
  once (10k rows, loadpost-identical thinning of the 4 extA6eq chains; untracked like its
  siblings) so equilib runs are prefix-reproducible.
- **RESULTS** (×10⁻³ cm/GtCO₂, [MAGICC, FaIR]): transient mean @2100 [15.9, 12.1], @2150
  [29.1, 22.9]; equilib @2100 [22.8, 21.0], @2150 [34.7, 31.8]. Cross-checks: levels move <1%
  under the patch, transient medians +6–15% — but **equilibrium medians rise 2–4×** (@2100
  MAGICC 5.4→22.6): most equilib draws are already tipped, so the previously-quantized
  tip-advance channel reaches the median draw, not just the tail. Raises the stakes of the
  pending sub-annual-integrator adoption decision (M2).
- **`notes/writeup_2026-07-21_brick_fm_vs_wong_brick.md`**: BRICK-FM vs the original Tony Wong
  BRICK — structure (Mengel glacier), interface (external forcing, precip_log, LWS lock),
  calibration (phase-1/phase-2 A2/A4/A5/A6/geometry/obs), results deltas, pending integrator
  decision, provenance table.
- Cross-model artifact republished with the pulse-mean column (snapshot + details in
  FaIRtoFrEDI `magicc_comparison/artifacts/`).

## [unreleased] — 2026-07-20 (later) — phase-2 production run DONE + accepted; A6 sensitivity running

- **Two-stage launch executed.** Tuning chain (1M, acceptance 0.237) → built
  `overdispersed_starts.csv` + 39-param `adapted_cov_ext.csv` → **4×2M over-dispersed
  production run** (acceptance 0.234–0.237, ~3 h). All phase-2 terms confirmed working in the
  tuning posterior: SMB β_total→1860 Gt/yr (target 1863); amp 1.195→0.944; T_on sd 0.1;
  λ/γ/κ sampling paleo.
- **Production converged on the deliverable + accepted:** SLR@2100 R̂ **1.006**, SLR@2150 R̂
  **1.008** (10 param marginals still fail — the ridge). `postprocess_mcmc_ext.jl --accept-slr`
  wrote the canonical phase-2 `parameters_subsample_brick_mengel_ext.csv` (10k of 4M draws).
- **HEADLINE (SSP2-4.5, rel 1995–2014):** SLR@2100 median **39.7 cm** [36.9–75.0]
  (v-next 76.1), @2150 **62.8 cm** [55.7–153.5] (159.1). Threshold crossing ~82%→~29%.
  Production medians match the tuning preview (39.9/63.0) — robust. Moves BRICK-Mengel from
  above-AR6 to ~AR6-central for SSP2-4.5. Key params cooled: ais_ocean_temperature₀ 0.862
  (base 0.981), anto_alpha 0.296 (0.405).
- **A6-equilibrium sensitivity RUNNING** (`run_A6eq_sensitivity.sh`, amp pinned 1.196, infix
  `extA6eq`, ~3.7 h) to isolate A6's share of the headline drop (Marcus-approved attribution).
- **M2 downstream REFRAMED — NOT a mechanical repoint.** 12 drivers read the June-13
  `parameters_subsample_brick_mengel.csv` (incl. the pulse/MAGICC-vs-FaIR pipeline). Repointing
  to phase-2 halves the SLR-based pulse results, mostly via A6 (judgment-call σ). Gated on the
  A6 attribution + Marcus's decision on which posterior the pulse paper adopts. Held.

## [unreleased] — 2026-07-20 — phase-2 begun: M1 accept, Dangendorf/Frederikse untangle, A2/A4/A5/A6 wired

Phase-2 kickoff (Marcus decisions 2026-07-19/20). Nothing launched yet — the phase-2
recalibration awaits Marcus sign-off on the pinned numbers (see the pre-run summary /
handoff §5). What landed this session:

### M1 — accept the v-next posterior on the deliverable (DONE)
- Added `--accept-slr` to `postprocess_mcmc_ext.jl`: writes the canonical (no-suffix)
  subsample + proposal seed iff `outputs/mcmc/slr_convergence_ext.csv` (now emitted by
  `diag_slr_convergence_by_chain.jl`) shows SLR R̂<1.05 at all horizons AND is fresher than
  every chain file. Regenerated `parameters_subsample_brick_mengel_ext.csv` (canonical) +
  `README_brick_mengel_ext_acceptance.md`. Downstream drivers deliberately NOT repointed yet
  (done once, at the phase-2 posterior, with the M2 pulse rerun).
- Fixed a stray-chain trap: a 2-iteration smoke chain (`chain_ext_seed2026_n2.csv`) matched
  the `chain_ext_seed*` glob and had (1) collapsed the marginal diagnostic to 1 draw/chain,
  (2) leaked one smoke draw into row 1 of the prior subsample. Quarantined
  (`outputs/quarantine/20260720_smoke_chain_n2/`); postprocess now errors loudly on a
  chain-length mismatch (shortest < ½ longest). **This means the handoff's marginal numbers
  (worst R̂ 1.458) always came from the four full chains — the 18:22 "certification" was the
  degenerate 1-draw read, now confirmed.**

### Dangendorf / Frederikse — two-layer data bug untangled (A3 + M3 pre-check)
- `data/observations/dangendorf_2024_gmsl.csv` was **Frederikse 2020's own observed GMSL**
  (bit-identical). Renamed → `frederikse2020_gmsl_total.csv`; relabeled the active pipeline
  (`prep_recalib_targets_ext.py`, `apply_wong_weights.py`, `hawkins_sutton.py`,
  `julia/compute_lB_per_post.jl` — the "Dangendorf importance weights" were FREDERIKSE
  weights; `dangendorf` kept as a deprecated alias that warns).
- Fetched the **real Dangendorf 2024** (Zenodo 10621070). Its `KalmanSmootherHR_Global.nc`
  is mis-written upstream (the "GMSLHR" slot holds the BARYSTATIC mean — proved: cos-weighted
  mean of the Fields-nc `Bary` reproduces it to 0.000 mm). True GMSL = cos-lat-weighted mean
  of the `HR` field (`Fields.nc`), per the record's own `Master_Final.m`; validated vs the
  paper (1900–2021 1.52 vs 1.5±0.19; 1993–2021 3.17 vs 3.4±0.42 mm/yr). Extracted →
  `dangendorf2024_gmsl_annual.csv`. **SE unattributable (same slot-shift) — resolve before
  any likelihood use.**
- **Bonus:** the record also redistributes the full 5000-member weighted **Frederikse
  component ensemble** (`GMSL_ensembles_F20.nc`) — the exact object the 2026-07-19 σ-fix said
  was missing; enables the correct re-referenced per-component band σ (M3 implement).
- Tension diag (`python/diag_dangendorf_vs_frederikse.py`, ref 1995–2005): Dangendorf sits
  INSIDE Frederikse's 5–95% at every trend window; mid-century 1930–1970 D 1.44 vs F 1.85
  (6.8th pctl) is the real but bounded tension; 1993–2018 D 3.03 agrees with altimetry 2.86
  better than F 3.36 does. 11/119 yr outside the F band. Figure + summary in `outputs/`.

### A2/A4/A5/A6 — phase-2 calibration changes WIRED (not yet run), 35→39 params
- **A2:** freed `λ`, `ais_γ`, `ais_κ` under their existing paleo marginals (param_priors.csv).
  Observationally unidentified over the historical window → they sample the prior; the point
  is to propagate fast-dynamics uncertainty and de-bias the hot medoid (λ 0.0137→prior 0.0104).
- **A4:** runoff line reparameterized to its identified direction (`T_on = −h0/c`, `c`) under a
  rebuilt joint paleo prior (`compute_paleo_geo_prior_ton.jl` → `paleo_geo_prior_ton.csv`;
  paleo T_on −15.64±5.54, r(T_on,c)=+0.64 vs the posterior r(h0,c)=0.9997 it replaces).
  `h0 = −T_on·c` reconstructed per draw.
- **A5:** SMB likelihood term on model `β_total` (1979–2008 mean) vs area-scaled Rignot 2019
  (2098×0.888 = **1863 ± 118 Gt/yr**; σ from Rignot's spread, Mottram-2021 alternative flagged).
  At the medoid β_total = 2389 Gt/yr (z=4.45) — target is interior to the paleo-prior-vs-SLR-fit
  tension, so it anchors precip0 to a physical intermediate and breaks the 34:1 input–output
  degeneracy. **σ is a Marcus sign-off item.**
- **A6:** GMST→Antarctic-temperature map sampled as transient amplification `amp` (anchor
  T_ant(GMST=0) preserved); prior **N(0.95, 0.10)** on CMIP6 PAI1 (Xie et al. 2022, Sci Rep
  12:16548: 0.88/0.95/0.97/1.03 for SSP1-2.6/2-4.5/3-7.0/5-8.5; no published inter-model sd —
  0.10 spans the scenario range without re-admitting the equilibrium 1.196). Replaces the
  hard-coded 0.8365/15.42 (amp 1.196, ~26% high). **σ is a Marcus sign-off item;** biggest
  headline-mover (could shift "82% crossed by 2100" to a minority).
- Smoke-tested (200 iter): 39 params, θ0 logpost −799 (vs baseline −779), amp anchor identity
  exact, all new params tracked. Launch is TWO-STAGE (common-start tuning run → build
  over-dispersed starts + adapted cov → 4×2M production); `--overdisperse` now errors clearly
  when the starts file predates the current parameter set.

---

## [unreleased] — 2026-07-19 — σ-fix re-baseline: accept-on-deliverable, + pulse-size robustness

### σ-fix re-baseline (4 × 2M, over-dispersed starts, corrected Frederikse band)

- **Parameter marginals NOT converged** — worst R̂ **1.458** (`ais_slope`), the same
  identifiability ridge. **This is slightly WORSE than run 3 (1.320), not better.**
  **Correction to an earlier claim:** I said the σ fix "plausibly fixes the sampling
  problem." It does not — widening the observational σ *flattens* the likelihood, which
  makes the weakly-identified ridge *less* identified, so param-level mixing got marginally
  worse. The σ fix remains correct (the uncertainty really was wrong), but its effect on
  sampling is neutral-to-negative, not positive.
- **Deliverable IS converged, now under OVER-DISPERSED starts:** SLR@2100 R̂ **1.003**,
  SLR@2150 R̂ **1.004** (`diag_slr_convergence_by_chain.jl`, chains started from
  `ais_iceflow0` quantiles 0.02/0.35/0.65/0.98). This closes the anti-conservative-R̂ hole:
  chains that start far apart on the failing direction still agree on projected SLR to ~5 cm
  against a ~23–35 cm within-chain sd. Projected SLR @2100 median 76.1 cm, @2150 159 cm.
- **Accept-on-the-deliverable is now vindicated:** the posterior gives a converged,
  over-dispersed-robust SLR projection despite the nuisance marginals. Subsample written to
  `data/MimiBRICK/parameters_subsample_brick_mengel_ext_NOTCONVERGED.csv` (the suffix is
  honest about the *marginals*; it is accepted for SLR-level use — see the naming decision below).

### Two postprocess convergence-gate bugs (both found because the re-baseline was FALSELY certified "all converged")

1. `ess(arr; maxlag = size(arr,1))` trips an internal "draws after splitting is 0" path on
   ≥1e6-draw chains → returns **NaN**, and `NaN < ESS_MIN` is `false`, so NaN-ESS params
   silently PASS. Fixed: `maxlag = min(nmin−4, 200000)` and require `isfinite(r) && isfinite(e)`.
2. The full 37-col × 2e6-row × 4-chain read (~5.7 GB) returns **corrupted** data (NaN R̂/ESS
   for every param) on the swap-bound machine. Fixed: read only diagnosed columns.
   Verified against a low-memory selective read: true worst R̂ 1.458, not "all converged".

### Pulse-size robustness ladder (Marcus's test) — answered and verified

`julia/diag_pulse_size_robustness.jl`: BRICK-Mengel paired at 7 sizes 0.03–30 GtCO₂, climate
by IRF scaling (validated vs real FaIR 20gt/0.01gt, <0.06% median error; P=10 rung reproduces
the production driver bit-identically). Two independent verifiers confirmed paired discipline,
units, linearity, horizons.

- **Per-ton MEDIAN robust to 0.7–2.2% over 0.03–1 GtCO₂** — quantization does NOT move the
  median (the median member never tips). ✔ we are OK at SCC pulse sizes.
- **Genuine large-pulse NONLINEARITY** (not quantization): median +9–20% at 10 GtCO₂,
  +42–101% at 30 GtCO₂, monotonic (compounding disintegration). **ACTIONABLE: the canonical
  BRICK-Mengel pulse tables were run at 10 GtCO₂ → they overstate per-ton median by ~9–20%.
  Recompute the headline at ≤1 GtCO₂.**
- **MEAN unusable** (90–111% ladder spread, non-monotone).
- **The median under-states fast dynamics** in the opposite direction from the mean: the tip
  fraction never reaches 50% at any rung, so the median is always the smooth-channel
  background (mean/median 11–18×). Median = *central* marginal, not the expectation. For a
  fat-tail-inclusive number use the Lemoine-Traeger P(tip)·ΔSLR_tip decomposition, not the mean.

### DECISION PENDING (Marcus)
- **Naming/acceptance:** is the SLR-level R̂ (1.003/1.004) the accepted convergence criterion,
  so the `_NOTCONVERGED` subsample should be renamed to a canonical "accepted-on-deliverable"
  path? Or hold for the parameter-level ridge (which needs a mixture/re-fix, not more iterations)?
- **Recompute the pulse headline at ≤1 GtCO₂** (the 10-GtCO₂ tables are ~9–20% high).

## [unreleased] — 2026-07-18 — BRICK-Mengel **v-next recalibration** (Strategy B: 28 → 35 params)

Branch **`brick-mengel-vnext`** (new). `brick-mengel` is archived/frozen per CLAUDE.md,
so this work branches off it rather than committing onto it. **Flagged for Marcus:**
confirm this is the intended home — the alternative is moving the calibration drivers
into the MimiBRICK-FM repo, which is now the canonical home of the Mengel model.

### Changed
- **`julia/calibrate_mcmc_ext.jl`** — the 7 DAIS geometry params (`ais_μ`,
  `bedheight₀`, `slope`, `iceflow₀`, `precipitation₀`, `runoffline_snowheight₀`, `c`),
  previously **fixed at the prior medoid**, are now **free** under a joint MvNormal
  paleo-covariance prior. 28 → 35 free params (25 physical + 10 AR(1) noise).
- **Forcing** switched from the RFF-SP-central splice to the **SSP2-4.5 harmonized**
  splice (`fair_mean_{gmst,ohc}_ssp245harm.csv`), so the calibration and the pulse
  projections sit on the same forcing. Both share the Smith historical → 1850–2020
  unchanged (1850/1900/1971 bit-identical); differs only over ~2020–2026 of the fit
  window (mean |ΔGMST| 0.03 °C) and in the tail.
- **`FaIRtoFrEDI/build_fair_mean_v145.py`** parameterized (`--emissions-file`, `--tag`,
  `--scenario-label`) so alternate forcings can be built **without overwriting** the
  canonical `fair_mean_{gmst,ohc}.csv`. Defaults unchanged.

### Added
- **`MimiBRICK.jl/calibration/compute_paleo_geo_prior.jl`** → `outputs/paleo_geo_prior.csv`.

### Quarantined
- June-13 28-param `ext` posterior → `outputs/quarantine/20260718_pre_vnext_28param_ext/`
  (**superseded, NOT bugged**). Necessary because `postprocess_mcmc_ext.jl` globs
  `chain_ext_seed*` and would otherwise silently mix 28- and 35-column chains.

### Tried and abandoned / rejected
- **Raw paleo covariance as the prior — rejected.** The 7 params span scales 1e-4…1e3,
  giving `cond(Σ) = 5.2e13`. Used the **standardized** form instead — `MvNormal(0, C)`
  on `z=(θ−μ)/sd`, `cond(C) = 2.75` — which keeps the paleo correlation structure
  without the ill-conditioning.
- **Continuing on the fork's `calibration/calibrate_mcmc_mengel.jl` — abandoned.**
  It does not run: it calls MimiBRICK internals (`get_model`, `set_external_forcing!`,
  `_apply_mengel_defaults!`) unqualified, as if lifted out of the module with the import
  dropped, and separately crashes on missing values because the extended targets gained
  trailing empty years after it was written. Evidence it was refactored for the PR and
  never re-run. My edits to it were **reverted**; pivoted to `calibrate_mcmc_ext.jl`,
  which runs and already had the Mengel emulator, the freed `ais_ocean_temperature₀`,
  the dropped point terms, and NaN handling. *Open: whether to also fix the fork script
  as separate cleanup / flag to Tony.*
- **`islog=true` for `precipitation₀` — rejected.** `setp!` applies `log()` when
  `islog=true`, and MimiBRICK v2.0.0 already computes `exp(ais_precipitation₀)`
  (default `log(0.37)`), so that would log twice. Sampled in log space with `islog=false`.
- **Geometry-specific proposal scale as the fix for low acceptance — rejected by test.**
  Plausible (paleo sd for `ais_μ` is 1.8 vs a chain spread of ~0.004) but **wrong**:
  it moved acceptance only 0.022 → 0.029. `GEO_PROP_SCALE` is retained as a sane default,
  not as the fix. The actual cause was the **θ0 start point** — geometry fell back to the
  paleo prior *mean* rather than the *medoid* the rest of the MAP was conditioned on
  (medoid `precip₀` 0.94 m/yr vs paleo mean 0.40, a 2.3× difference; `iceflow₀` −1.4 sd).
  That put `logpost(θ0)` at −5636 vs the 28-param baseline's −771. Isolated by running the
  original 28-param script at the same iteration count/seed (acceptance 0.192) as a control.
  With the medoid start: `logpost(θ0)` = −779, acceptance 0.196 → 0.222 after adaptation.

### Run 1 (4 × 500k) — NOT CONVERGED; diagnosed, not a bug

Acceptance healthy (0.224–0.241), but **12 params fail R̂<1.05**, and the failures are
exactly the 7 geometry params (R̂ 1.44–1.98) plus the AIS block they correlate with
(`ais_ocean_temperature₀` 1.09, `antarctic_alpha` 1.49, `anto_alpha` 1.25, `anto_beta` 1.51).
ESS ≈ 2000 with bad R̂ = good *within*-chain mixing, bad *between*-chain agreement.

Diagnosed with three tests rather than assumed:
- **Not multimodal.** Per-chain median `log_post` = 126.7 / 128.5 / 129.7 / 126.8 — all four
  chains sit on the same plateau. No chain found a better mode.
- **Not bound-railing.** Only 5% of pooled `ais_c` draws and 10% of `ais_runoff_h0` fall
  within 2% of a paleo bound. **This corrects the "watch `ais_c` railing" flag raised from
  the 50k tuning chain — it was an over-read of one short chain.**
- **The geometry block is weakly identified.** Posterior sd / prior sd = 0.46–0.76
  (`ais_bedheight0` 0.76 ≈ unidentified; the rest roughly halve the prior sd). Per-chain
  medians differ by 1.5–4.5 within-chain sd while posterior density is equal.

So the target is a broad, correlated, weakly-identified ridge — which is *why* the original
calibration fixed these at the medoid. Not a defect in the implementation.

### Run 2 (4 × 1M) — in progress
Reseeded from the **empirical 35×35 posterior covariance** written by postprocess. Run 1
started from the 28×28 embed + diagonal, which encoded nothing about the geometry ridge;
the empirical covariance captures its correlation, so this tests better mixing rather than
brute-forcing iterations. Run-1 chains quarantined to
`outputs/quarantine/20260718_vnext_run1_notconverged/` to keep the `chain_ext_seed*` glob clean.

**A non-converged subsample was written to the canonical
`data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` and has been moved out** to
`outputs/quarantine/20260718_vnext_NOTCONVERGED_subsample/`. The June-13 `_ext` subsample at
that path was overwritten in the process — it is untracked, but regenerable from the
quarantined June-13 chains. The four MAGICC-vs-FaIR tables are unaffected: their driver
reads the non-`_ext` `parameters_subsample_brick_mengel.csv`, which is untouched.

### 2026-07-19 — ADVERSARIAL AUDIT: several of the above diagnoses were WRONG

A 4-lens adversarial audit of the convergence diagnosis (workflow `wf_e17a59f6-443`)
found real defects. Retractions, with what replaced them:

- **RETRACTED: every ESS number reported for runs 1–3.** `postprocess_mcmc_ext.jl:37`
  called `ess(arr)` with MCMCDiagnosticTools' default `maxlag=250`, which truncates the
  Geyer sum at τ≤500 and therefore **floors ESS at ntotal/500**. Reported values were
  exactly that floor (run1 ~2000, run2 ~4000, run3 ~8000). The "ESS doubled → mixing
  improved" reading — which I used twice as evidence — was the floor doubling with
  `ntotal`. **True run-3 ESS: `ais_iceflow0` 10.6 (τ=376,230), `antarctic_alpha` 19.6,
  `ais_precip0_LOG` 41.9, `ais_slope` 47.7.** Fixed; ESS now reported with τ.
- **RETRACTED: "longer chains, no methodological change."** Reaching ESS 400 for
  `ais_iceflow0` needs ~38M iterations *per chain* (~80 h/chain). Run 3 (2 M) confirmed
  it empirically: R̂ did **not** improve over run 2 and the worst param got *worse*
  (1.245 → 1.320). Chain length is not the lever.
- **RETRACTED: the identifiability causal story — it was backwards.** The parameters that
  fail R̂ are the **constrained, correlated** ones; the weakly-identified ones mix
  *trivially* (`ais_bedheight0` ESS 7218, `ais_c` 5356) because the sampler just draws the
  prior. Correspondingly, "re-fix `ais_bedheight0`" was exactly backwards — it is the
  best-converged parameter in the set (R̂ 1.000).
- **RETRACTED: run-1 provenance.** Run 1 did **not** use a 28×28 embed; its log shows the
  full-35×35 branch fired. Both runs were seeded 35×35 (run 1 from the 50k pilot). The
  earlier commit message and handoff describing a diagonal-vs-tuned contrast are wrong.
- **RETRACTED: "not multimodal."** Per-chain median `log_post` cannot distinguish a flat
  ridge from equal-height modes. Run 1 never reached the typical set (plateau ~126 vs the
  stationary ~135, ≈3000× in density), and run-2 seed2029 sat at ~126 for 600k iterations
  then jumped to ~135 — a metastable neck, escape time O(3–6 × 10⁵).
- **CORRECTED: bound-railing.** Holds for run 2 (max 0.0075 within 2% of a bound) but was
  **false for run 1**, where chains spent ~50% of draws against the `ais_runoff_h0`
  ceiling. The 2%-of-range band was too thin to see it.
- **UPHELD:** R̂ *is* rank-normalized split-R̂ (Vehtari 2021), verified by independent
  reimplementation. Reseeding the proposal is legitimate adaptive MCMC (fixed before the
  run, diminishing adaptation satisfied) — the R̂ validity problem is the shared start, not
  the reseed. `ais_runoff_h0`↔`ais_c` posterior correlation +0.954 (prior +0.228) is a
  genuine structural degeneracy. Rotating onto the *prior's* principal axes would be a
  no-op, since RAM already adapts a full covariance.

### THE RESULT THAT MATTERS: the deliverable IS converged

`julia/diag_slr_convergence_by_chain.jl` (new) runs 400 thinned draws per chain forward
on SSP2-4.5 and diagnoses **projected SLR** rather than the nuisance marginals:

| quantity | R̂ | ESS | between-chain median spread |
|---|---|---|---|
| SLR@2100 | **1.001** | 1564 | 4.5 cm vs 22 cm within-chain sd |
| SLR@2150 | **1.002** | 1420 | 5.1 cm vs 34 cm within-chain sd |

Verified **not** an artifact of parameters silently failing to set: a one-at-a-time
sensitivity probe gives each badly-mixed param large individual leverage on SLR
(`ais_iceflow0` up to 57 cm @2100, `ais_precip0_LOG` 49 cm), and the chains genuinely
disagree on those marginals. So the AIS geometry sits on a **compensating ridge** —
individually consequential, jointly constrained. Pooled median SLR@2100 = 76.8 cm
corroborates the earlier 77.7 cm posterior-predictive value.

### Run 4 (4 × 2M, OVER-DISPERSED starts) — in progress
The one remaining validity hole: all runs to date started all 4 chains at an identical
θ0, making R̂ anti-conservative (it cannot see mass no chain reached) — including the SLR
R̂ above. `--overdisperse` now starts each chain from a real posterior draw at
`ais_iceflow0` quantiles 0.02/0.35/0.65/0.98. Random jitter was tried first and failed
(200/200 non-finite logposterior). Expect R̂ to look worse; that is the diagnostic working.

### DECISION PENDING (Marcus) — superseded framing below

*(The original three options were written before the audit. Options 1 and 2 are now dead:
chain length cannot work, and `ais_bedheight0` was the wrong parameter to re-fix.)*

The live decision is **what to gate acceptance on**:

- **RECOMMENDED — gate on the deliverable.** Accept the posterior on SLR@2100/@2150 R̂
  (1.001/1.002) plus the AIS projection knobs, and report the 7 geometry marginals as a
  weakly-identified nuisance block on a compensating ridge. Requires disclosure in methods
  (see below). Conditional on run 4 confirming under over-dispersed starts.
- **Alternative — re-fix the hard-mixing params** (`ais_iceflow0` / `ais_slope` /
  `ais_precip0_LOG`, *not* `ais_bedheight0`). Cheap, but `ais_precip0_LOG` is the most
  projection-coupled geometry param (r = −0.282 with `antarctic_alpha`, +0.364 with
  `anto_beta`), so fixing it is not free.
- **Alternative — change sampler.** The ridge is curved; a linear reparameterization is a
  no-op under RAM. Would need HMC/NUTS on a transformed target or tempering.

**Must be disclosed in the paper's methods** regardless of choice: R̂ is rank-normalized
split-R̂; several AIS marginals do not reach R̂<1.05 at 4 × 2M and are reported as a
weakly-identified nuisance block; convergence is asserted on posterior-predictive SLR, not
on those marginals; the `ais_runoff_h0`↔`ais_c` degeneracy (posterior r = +0.954).

## [unreleased] — 2026-07-09 — CH4/CO2 pulse → SLR **research plan** (adversarially reviewed)

- **`notes/research_plan_2026-07-09_ch4co2_slr_paper.md`** — full research plan
  expanding the same-day handoff into a submission-oriented document: paper thesis
  + 4 contributions, literature positioning/novelty (Sterner-Johansson-Azar 2014 and
  Zickfeld 2017 as ancestors; Nauels 2025 / SURFER v3.0 / Wong's own arXiv preprint as
  threats), the **RFF-SP-vs-SSP backbone decision** (recommend RFF-SP primary for the
  gas headline + uncertainty band; SSP2-4.5 as the shared cross-model-panel backbone
  and AR6-anchor/curvature layer), pulse-experiment design + discipline, MAGICC Phase 2
  and FACTS comparison plans, figure/table set, 11 open methodological decisions, an
  11-row risk register, dependency-ordered sequencing, journal strategy, and a compiled
  reference list with DOIs.
- **Built from a 7-agent context sweep** over the BRICK-FM fork docs, MAGICC Phase 1/2
  handoffs, the completed 3-BRICK pulse study, FACTS scoping, the backbone evidence, and
  a verified literature search; then **adversarially reviewed by 3 independent critics**
  (numeric consistency — all headline numbers recompute and match source; novelty/strategy;
  methods/execution risk). Fixes folded in: reframed "level-vs-marginal inversion" as a
  mechanism decomposition (pre-empts the "expected threshold-model behavior" objection);
  added a **required CH4-specific scenario-sensitivity test** (the ~8% scenario-insensitivity
  is a CO2 cross-check, not CH4 — and RFF under-projects CH4 growth, obs ≥ p95); elevated
  Wong coordination and the reference-arm reuse-vs-re-run question to explicit gates; split
  the fossil-CH4 doc-vs-lock contradiction by arm; flagged the RFF CO2-unit (1000×) and
  MAGICC float32-floor pulse-size risks; and made GWP-basis dependence of the crossover a
  first-class result.

## [unreleased] — 2026-07-09 — CH4/CO2 pulse → SLR paper plan (BRICK-FM coming-out paper)

- **`notes/handoff_2026-07-09_ch4co2_slr_paper_plan.md`** — plan for the paper
  combining CH4-vs-CO2 pulse SLR impacts with the BRICK-FM introduction. Covers:
  BRICK-FM v-next recalibration scope (Smith 2024 emissions splice, freed AIS
  geometry params, IMBIE/Dyurgerov point-term reconciliation, TE overshoot,
  FaIR-config-aware calibration options), MAGICC Phase 2 + FACTS2.0 comparison
  plan, paper skeleton, open methodological decisions, and sequencing.
- **Discrepancy flagged (must resolve before recalibration):** the fork's
  `calibrate_mcmc_mengel.jl` includes the IMBIE + Dyurgerov Gaussian point terms
  unconditionally, but the ext refit that produced the shipped posterior dropped
  both — re-running the fork script as-is will not reproduce the shipped posterior.

## [unreleased] — 2026-06-24 — Phase 2 RFF-SP 2k subsample + extractor --subset flag

- **`outputs/rff_subset_2k.csv`** — canonical 2000-draw RFF-SP subsample for the
  Phase 2 MAGICC-vs-BRICK-Mengel comparison. Stride-5 selection (rff_idx 1,6,11,…,
  9996); deterministic and evenly-spaced across the RFF-SP inventory. Decision
  confirmed by Marcus 2026-06-24 (2k subsample + 1:1 LHS MAGICC member pairing).
- **`extract_pulse_marginals_3brick.py`** — added `--subset <csv>` flag.  Optional
  path to a CSV with `rff_idx` column; filters the 10k per-draw arm files to the
  specified subset before computing weighted marginals. Default (no flag) = full 10k
  (existing behavior unchanged). Subset output named
  `marginals_summary_<stem>.csv` to avoid overwriting the canonical 10k result.
  Validated on 2k: Mengel CO2 medians agree with full-10k to 0.3% (@2100) / 0.6%
  (@2300) — within sampling noise.
- **`extract_fossil_ch4_marginals_3brick.py`** — same `--subset` flag added.
  Output named `marginals_fossil_ch4_summary_<stem>.csv`.

## [unreleased] — 2026-06-17 — LWS seed lock + brick-mengel archived

- **Root cause** of the ~0.4 cm total-SLR drift between Mengel SSP-projection re-runs: MimiBRICK's
  `get_model` draws `lws_random_sample ~ Normal(0.0003, 0.00018)` UNSEEDED on every call. (Diagnosis:
  GSIC/GIS/TE bit-identical, AIS float-noise, LWS the entire delta with mixed signs across SSPs.)
- **Fix:** `build_brick_mengel` now takes `lws=:seeded` (default; fixed-seed LOCAL RNG, `LWS_SEED=2026`,
  reproducible realization), `:central` (0.3 mm/yr mean = MimiBRICK-FM), `:zero`, or `:random` (legacy
  unseeded). Local RNG keeps the global stream (FaIR-member pairing seeds) untouched. Verified bit-identical
  across re-runs; LWS now a single locked value (2.596 cm) across all SSPs (correct — LWS is climate-independent).
  Regenerated SSP / matched / hybrid Mengel outputs (shifts immaterial, sub-0.5 cm).
- **All canonical BRICK versions now have locked LWS:** `main` (BRICK2.0) and `brick-v1.2-vehicle`
  (preBRICK2.0) already seed `Random.seed!` immediately before `get_model` in their canonical drivers
  (obs-driven, flatcube); MimiBRICK-FM uses the `:central` mean; brick-mengel uses `:seeded`.
- **`brick-mengel` ARCHIVED** (annotated tag `archive/brick-mengel-2026-06-17`, branch kept). Frozen final
  state of the calibration/working branch; the Mengel model is canonical in MimiBRICK-FM, and this tag
  preserves the study drivers (MAGICC comparison, CO2/CH4 pulse 3-BRICK, recalibration diagnostics) that
  were never extracted there. Canonical going forward: brick-v1.2-vehicle, main, MimiBRICK-FM.

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: headline reframed to CH4-as-CO2eq (Marcus)

Marcus: drop the fossil-CH4 variant from the HEADLINE (the co-emitted oxidation CO2 is an instantaneous
pulse, an inexact stand-in — a real fossil pulse spreads the oxidation CO2 over the methane oxidation
lifetime) and express the headline CH4 marginal in **CO2-equivalent (AR6 non-fossil GWP-100 = 27.0)** so
both gases are on cm/GtCO2(eq).
- `marginals_summary_co2eq.csv` — CH4 rows ×(1000/27.0)=×37.037 (exact linear rescale of every quantile/
  mean/component); CO2 unchanged. The physical `marginals_summary.csv` (cm/TgCH4) stays as source of truth.
- `plot_pulse3brick_marginals.py` regenerated → `pulse3brick_marginals.png` now plots CO2 (top row) vs
  CH4-as-CO2eq (bottom row) with the **y-axis SHARED per horizon column**, so the short-lived-forcer
  crossover is visible: CH4-eq Total towers over CO2 at 2100 (~2.2–2.7e-2 vs ~0.5–1.2e-2 cm/GtCO2eq) and
  falls below it by 2300. GWP from a named constant; fossil exclusion noted in the caption.
- `headline_table_co2eq.md` is the headline table (CO2 vs CH4-CO2eq + ratio + per-component); the fossil
  sensitivity stays in `headline_table_fossil_ch4.md` (NOT headline). CH4-CO2eq ÷ CO2 ratio ~2.2–2.3× @2100,
  ~1.4× @2150, ~0.6–0.7× @2300, all 3 versions.

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: STEPS 5–7 DONE — STUDY COMPLETE

Steps 5 (per-version Wong weights), 6 (paired weighted marginals), and 7 (headline figure) all
complete. The CO2/CH4 pulse→SLR / 3-BRICK-version study is finished through the figure; narrative
is Marcus's to draft.

- **Step 5a/b — per-post baseline l_B (Dangendorf):** `slurm/submit_lB_pulse3brick.sh` (2-task array,
  4 cpu, ~1–2 min each). pre93 via `julia/compute_lB_per_post_v121.jl` (julia_v121, pre-#93 35-col
  posterior, precip_log=false); brick2 via NEW `julia/compute_lB_per_post_brick2.jl` (julia_v2,
  post-#93 posterior, **precip_log=true**, v2.0.0 get_model — a copy of the v121 script with the
  precip log-shim + brick2 defaults). mengel SKIPPED (equal-weighted; no Wong — locked 2026-06-15).
  Outputs Torch `outputs/brick_lB_per_post_{pre93,brick2}.csv` (10000 rows, all finite).
  - **Tried + abandoned:** running `compute_lB_per_post_v121.jl` as-was in julia_v121 — FAILED
    (`ArgumentError: Package Distributions not found`; the pinned v1.2.1 env has no Distributions).
    Fix: replaced the `MvNormal` logpdf with a Cholesky logpdf using only `LinearAlgebra` (stdlib),
    numerically identical. Did NOT mutate the pinned env (no Pkg.add). brick2 unaffected (julia_v2
    has Distributions; left as-is — each version's Wong weight uses only its own (l_FB − l_B), so
    cross-version logl-implementation differences are irrelevant).
  - **Uniformity check (per "suspicious uniformity = bug" discipline):** pre93 l_B is very tight
    (std 1.9, range 364–385) vs brick2 (std 79). NOT a degenerate code path — **9959/10000 unique**
    l_B values; the tightness is real, driven by the pre-#93 posterior's near-constant AR(1) nuisance
    params (rho_gmsl CV 0.4 %, sd_gmsl CV 0.19 vs brick2 0.41) under a *fixed* default-ssp245 backbone
    (the logl scale is set by sd/rho, which barely vary).
- **Step 5d — Wong weights:** NEW `python/apply_wong_weights_pulse3brick.py` (split-CSV adaptation of
  `apply_wong_weights.py`; reuses its Kalman logl / ESS / loaders verbatim). Reads l_FB from
  `{version}_baseline.csv`'s `slr_<year>` 1850–2300 trajectory (cm, re-ref to 2000; verified slr_2000==0),
  merges l_B. **post_idx convention bug caught:** Step-4 cells store post_idx **0-based** (driver does
  `post_idx_1b = post_i + 1`), but `load_posterior`/Julia l_B are **1-based** → fixed with a +1 map for
  the sd/rho lookup and l_B merge, keeping the 0-based cell key in the output. Replaced the coarse grid
  c-tuner with a **bisection** root-solve (ESS_fraction is monotone in c, and the grid over/undershot
  the steep ESS curve). Both arms hit **ESS = 50.0 %** exactly: pre93 c=0.262, brick2 c=0.00857.
  Wong shifts are modest (pre93 total SLR@2100 83.7→83.5 cm; brick2 73.8→77.9). Outputs Torch
  `outputs/wong_weights_{pre93,brick2}.csv` (per-cell w_norm + l_FB/l_B/log_w + keys).
  `--obs dangendorf` (1900–2018, 119 yrs) kept in sync between Julia l_B and the Python l_FB.
- **Step 6 — paired weighted marginals:** NEW `python/scripts/extract_pulse_marginals_3brick.py`.
  Pairs pulse↔baseline on the 4 keys (validate one-to-one; 10000/version/species), differences each
  of {total, ais, gsic, gis, te, lws} × {2100,2150,2300}, ÷ pulse size (CO2 0.01 GtCO2, CH4 1.0 Tg),
  weighted quantiles (pre93/brick2 Wong; mengel uniform) + unweighted for the §0 sanity check.
  Output `outputs/pulse3brick_v145/marginals_summary.csv` (108 rows; committed).
  - **Sanity PASSED:** unweighted total-q50 matches handoff §0 to **0.1–0.3 %** (ratios 0.999–1.003).
    Component means sum to total to machine precision (~1e-14). LWS marginal = 0 everywhere (the
    deterministic landwater add-on cancels in the pulse−baseline difference — correct).
  - **Physics (weighted q50, cm/unit):** pre93 CO2 is **GIS-dominated** (GIS 9.1e-3 of 1.15e-2 total
    @2100; 2.8e-2 of 3.1e-2 @2300 — the pre-#93 GIS pathology). brick2 GIS is tamed (5e-4) and the
    marginal is TE/GSIC-led. mengel has the largest **AIS** (8.99e-4@2100 → 3.78e-3@2300) with a fat
    tipping tail (CO2 mean 4.3e-2 ≫ median 4.7e-3). pre93 AIS marginal is slightly negative (~−1e-4).
- **Step 7 — headline figure:** NEW `python/plot_pulse3brick_marginals.py` → `outputs/pulse3brick_marginals.png`
  (2 rows species × 3 cols horizon; x = {Total, AIS, GSIC, GIS, TE}, grouped bars per version at the
  WEIGHTED median, Total bars carry weighted 5–95 % whiskers). **Grouped median bars (not a stacked
  mean)** deliberately, because the marginals are heavily right-skewed (mean ≫ median in the AIS-tipping
  tail) so a mean-stack misrepresents the central estimate; LWS omitted (marginal≡0). The figure makes
  the version story legible: pre-#93's Total is **GIS-driven** (towering red GIS bar), BRICK-Mengel
  leads on **AIS**, BRICK 2.0/Mengel TE comparable. Labels all from named constants; the caption text
  box is a placeholder for Marcus's narrative. Companion `outputs/pulse3brick_v145/headline_table.md`
  (Total median [5–95] + per-component attribution) committed for the writeup.
- **Canonical outputs (Torch unless noted):** l_B `outputs/brick_lB_per_post_{pre93,brick2}.csv`;
  weights `outputs/wong_weights_{pre93,brick2}.csv`; marginals `outputs/pulse3brick_v145/marginals_summary.csv`
  (committed); figure `outputs/pulse3brick_marginals.png` + `headline_table.md` (committed).

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: STEP 4 DONE (90k BRICK runs)

Launched + completed the production run (Marcus go). Outputs: `outputs/pulse3brick_v145/{pre93,brick2,mengel}_{baseline,co2,ch4}.csv`.
- **Bug caught at launch + fixed:** the first submit (job 10846724) failed all 9 tasks in 48 s —
  `NPZ.jl: unsupported type U171`. The 2026-06-14 cube seed-provenance addition embedded numpy
  **string/0-d arrays** in the `.npz`, which the Julia reader can't parse. Fix: strip string/scalar
  provenance to a sidecar `cube_*.provenance.json`, keep only `cell_seeds` (int64) in the npz —
  applied to the existing r2 cubes on Torch (data arrays untouched) and to the builder
  (`lhs_climate_v145_meta.py`, FaIRtoFrEDI `c5a7b84`). Re-ran (job 10848541): all 9 COMPLETED, ~2 min/arm.
- **Validated:** 9 CSVs × 10000 rows, fully paired. Unweighted per-unit marginal medians (cm):
  | version | CO2/GtCO2 @2100 | @2300 | CH4/Tg @2100 | @2300 |
  |---|---|---|---|---|
  | pre93  | 1.15e-2 | 3.11e-2 | 7.27e-4 | 5.94e-4 |
  | brick2 | 5.07e-3 | 1.00e-2 | 3.07e-4 | 1.74e-4 |
  | mengel | 4.69e-3 | 1.15e-2 | 2.80e-4 | 2.12e-4 |
  pre-#93 CO2→SLR ≈ 2.3–3× post-#93 (GIS pathology, as expected); CH4@2300 resolvable (1Tg fix worked).
- **Weighting (Marcus 2026-06-15):** primary BRICK-Mengel = EQUAL-weighted; pre93+brick2 = Wong-weighted.
- **Next:** Step 5 Wong (pre93/brick2) → Step 6 weighted marginals (co2 ÷0.01, ch4 ÷1.0; mengel plain) → Step 7 figure.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: Step-4 prep (P4) + Mengel l_B (P3)

Launch-readiness work while P1's cubes build (Marcus: P4 first, P3 second). Stops short of submitting.
- **P4 DONE** — synced BRICK drivers (`run_mimibrick_pulse_versioned.jl` + the 3 includes),
  the 3 posteriors + medoid central row, and the BRICK metadata to Torch `/scratch`. Wrote the
  9-task production array `slurm/submit_pulse3brick.sh` (idx = version*3 + arm; pre93→julia_v121,
  brick2/mengel→julia_v2; baseline arm `--save-trajs` for Wong; CO2 0.01Gt ÷0.01, CH4 1Tg ÷1.0;
  same `--seed 2026` for pairing) — STAGED, NOT submitted. Torch BRICK smoke (10 cells × 3 versions)
  all pass: closure resid 0.0, and totals **bit-identical to the local smokes** (pre93 5.3789, brick2
  3.2256, mengel 4.4536 m @2300) — cross-platform determinism confirmed.
- **P3 DONE (mechanics)** — `julia/compute_lB_per_post_mengel.jl`: per-member l_B vs Dangendorf for
  the 28-col mengel posterior (build_brick_mengel + medoid + 18 free params; uses `sd_dang`/`rho_dang`
  since the posterior has no `sd_gmsl`). Validated (5 members, finite l_B). ⚠ **OPEN Step-5 decision**
  flagged in the script: the Mengel posterior is already Dangendorf-calibrated, so whether to Wong-weight
  the mengel arm at all (vs equal-weight) is unresolved — await Marcus.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: prerequisites P1+P2 executed

Executing the two Step-4 blockers from the pre-launch review (Marcus: go ahead with P1+P2).
- **P2 DONE** — `julia_v2` (v2.0.0) + `julia_v121` (v1.2.1) instantiated + precompiled on
  Torch via `slurm/precompile_julia_envs.sbatch` (compute node; login-node instantiate was
  stalling/precompiling — SIGKILL risk). Both verified: `get_model`+`run` OK (v2 SLR2100=102.1,
  v121 99.0 cm). Plots/GR/Qt precompile-fails are benign (headless, unused by the BRICK driver).
- **P1 IN PROGRESS** — paired r2 triplet (baseline + co2-0.01Gt + ch4-**1Tg**) built on Torch
  via `slurm/submit_triplet_r2.sh` (array job, one arm each). Moved to Torch after the local
  background build died untraced; Torch calibration sha256 matches local
  (`03b0368…`) so the realization equals the locally-validated smoke. Cubes land on `/scratch`
  with embedded seed provenance (`cell_seeds` etc.). Tag `_flat2015_r2`.
- The 0.01 Tg CH4 cube is float32-corrupted (see prior entry); CO2 stays 0.01 Gt.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR, 3 BRICK versions: foundations (runbook Steps 0–3)

Built the prerequisites for the CO2 & CH4 pulse→SLR marginal study across three
BRICK calibration versions (pre-#93 v1.2.1 / BRICK 2.0 / BRICK-Mengel), on the
FaIR-v1.4.5 × RFF-SP LHS-10k ensemble. Stopped before the 90k-run Torch launch
(Marcus: foundations-only this pass). Runbook:
`notes/handoff_2026-06-14_co2ch4_pulse_3brick_NEXT-SESSION.md`.

### Added
- **`julia_v121/` — a real MimiBRICK v1.2.1 env** for the pre-#93 arm (the
  `brick-v1.2-vehicle` Manifest pins 1.0.1, so this is a build, not a checkout).
  Pins MimiBRICK git `repo-rev v1.2.1` (sha `94ceca2`) under Julia 1.12; smoke
  passes (build→run 1850–2300, closure 4.4e-16 m). `julia_v121/build_v121_env.jl`.
- **`julia/run_mimibrick_pulse_versioned.jl` — ONE version-aware flat-cube driver
  for all THREE versions** (`--brick-version pre93|brick2|mengel`), one output
  schema (per-component + total SLR at 2100/2150/2300, optional GMSL history for
  Wong). Supersedes the schema-limited `run_mimibrick_flatcube_v121.jl` (components
  at 2100 only) — unified to remove the cross-arm schema-drift risk. pre93 runs in
  `julia_v121` (precip_log=false); brick2/mengel in `julia_v2` (precip_log=true);
  mengel applies the 28-col posterior as 18 free params over the medoid central row
  (mirrors `project_ssps_2100_mengel.jl`). Added NPZ to `julia_v2`.
- **`python/scripts/sanity_battery_pulse3brick.py`** + smoke metadata
  `outputs/smoke25_lhs10k_metadata.csv`. 5-test gate (zero-pulse/cross-process
  determinism, sign-flip, ×magnitude, first-principles, closure) on a 25-cell
  lhs10k-proxy smoke per version → **ALL PASS, gate OPEN**
  (`outputs/sanity_battery_pulse3brick_smoke.txt`). Smoke reproduces the pre-#93
  GIS pathology (dGIS@2100 ≈ 8.1e-3 cm/GtCO2 vs ~4–5e-4 for brick2/mengel; pre93
  total ~3× larger @2300), ×magnitude linear to ~1% (no AIS tipping at 0.01 Gt),
  CH4:CO2 per-unit ratio ~0.055–0.063.

### Corrected (vs the runbook's assumptions)
- **MimiBRICK v1.2.1 already uses `get_model(ssprcp_scenario=…)`**, NOT
  `rcp_scenario=` as the runbook claimed; it ships both RCP- and ssp-named SNEASY
  forcing files (no date suffix) and uses LINEAR precip0 (`precip_log=false`). The
  real v1.2.1→v2.0.0 differences are the date-suffixed forcing files + the
  precip_log reparam. (Forcing is overridden by the cube's GMST/OHC anyway.)
- **The Mengel 28-col posterior cannot be applied via `update_brick_params!`** (it
  lacks the full AIS/glacier/thermal_s0 columns). Canonical path = medoid central
  row for fixed params, then the 18 free params per draw, per `project_ssps_2100_mengel.jl`.
- **`brick_mengel.jl` must be include()d at module scope**, not lazily in a
  function — Mimi's `run(m)` otherwise hits a world-age MethodError on
  `run_timestep_glaciers_mengel`. Loading it is harmless for pre93/brick2 (the
  Mengel component is defined but only instantiated for `--brick-version mengel`).

### Pre-launch review (2026-06-14) — 3 prerequisites before Step 4
Verified sound: lhs10ks cell layout == metadata (incl. seeds); pairing (pre-2030
dGMST=0, @2000=0 → rebaseline cancels); cross-process paired determinism exact;
CO2 0.01 Gt well-resolved (15–30× float32 ULP, ×magnitude ~1%); posteriors all
10000 rows (no off-by-one); closure ~1e-11.
- **P1 — CH4 0.01 Tg cube is float32-corrupted → regenerate at 1 Tg** (Marcus
  2026-06-14). CH4 dGMST decays below the float32 ULP (~2.4e-7 °C) after ~2060
  (nonzero cells: 72%@2075, 34%@2100, 8%@2300); CH4 SLR marginal ratio
  (0.01-cube/1-cube) = 0.97@2100, 1.20@2150, 0.51@2300, **TE@2300 → 0**. 1 Tg CH4
  is ~10× smaller dGMST than CO2-1Gt → well below AIS tipping. Build
  `cube_v145_lhs10ks_pulse_ch4_pos_1tg_flat2015.npz` (FaIR driver, paired seeds),
  marginal ÷1.0; CO2 stays 0.01 Gt ÷0.01.
- **P2 — Torch envs missing.** Only the v1.0.1 `julia` env is on Torch; build
  `julia_v2` (brick2/mengel) + `julia_v121` (pre93) there (instantiate + precompile).
- **P3 — Mengel Wong-`l_B` path missing** for Step 5 (`compute_lB_per_post*` assume
  the 35-col posterior; mengel 28-col needs medoid + 18-free).

### Pending (next session — Step 4 after P1/P2)
- Torch: 3 versions × 3 arms {baseline, co2_pos_001gt ÷0.01, ch4_pos_**1tg** ÷1.0}
  × 10k = 90k runs, partition `cs`. Then per-version Wong weights (own `l_B`) +
  paired marginals + headline figure.

## [unreleased] — 2026-06-13 — BRICK-Mengel post-2018 multi-component extension

### Added
- **Extended ALL calibration targets past Frederikse 2020's 2018 end** with
  reconciled modern products and re-fit, to test the post-2020 Antarctic pause +
  (Marcus's expansion) Greenland / thermal-expansion / glaciers.
  - Data: GRACE-FO JPL mascon AIS+GIS (→2026), GlaMBIE 2025 glaciers (→2023),
    NOAA NCEI thermosteric (→2025), NOAA STAR total (→2024); IMBIE 2023 AIS+GIS
    cross-check (agrees with GRACE splices <0.07cm). `raw/README_modern_extensions.md`.
  - `python/prep_recalib_targets_ext.py` → `outputs/recalib_targets_ext.csv`
    (offset-match splice onto Frederikse over GRACE/obs overlap; per-component end yrs).
  - `julia/calibrate_mcmc_ext.jl` + `run_mcmc_ext_local.sh` + `postprocess_mcmc_ext.jl`:
    per-series AR(1) windows; **dropped IMBIE+Dyurgerov point terms**; total extended
    w/ NOAA STAR (Marcus decisions). 4×500k → 27/28 R̂<1.05.
  - Obs check `julia/posterior_predictive_ext.jl` + `python/plot_postpred_components_ext.py`.
  - High-T glacier melt verification `python/verify_mengel_hightemp_melt.py` (Marcus:
    confirm Mengel melts MOST glaciers at high T) — PASS (99% committed @4°C).
  - Projection A/B `python/plot_ssp_projections_ext_compare.py`; `project_ssps_2100_mengel.jl`
    gained an optional TAG arg (baseline default byte-identical).

### Result
- Extending barely moves the physics (ais_ocean_temperature₀ +0.013); GMSL@2100
  LOWER by 0.8–3.2cm, ~entirely via AIS; high-forcing overshoot vs AR6 persists
  (MICI-threshold-driven, unconstrainable by ~7yr). TE overshoot NOT resolved by
  NOAA steric (+0.51cm@2025). AIS pause not reproduced (warming-driven model).

### Tried / noted
- 4×**100k** with the baseline proposal covariance did NOT converge (25/26 R̂>1.05;
  per-chain logpost spread 6–138 = slow burn-in from a mismatched proposal, NOT a
  bug). Fixed by seeding the 500k from the ext-tuned `adapted_cov_ext.csv`.
- `.gitignore`: exclude the 276MB×4 MCMC chain files (regenerable).

## [unreleased] — 2026-05-30 — Rennels 7-panel SSP2-4.5 SLR + pulse figure

### Added
- **7-panel SLR figure for Lisa Rennels** confirming emission-pulse + BRICK
  results under SSP2-4.5. Left: total GMSLR rel 2005 (median + 75%/90% bands,
  unweighted spread over 841 v1.4.5 configs × 8 BRICK post-PR#93 posteriors).
  Right 2×3: SLR impulse response to a 2020 CO₂ pulse, decomposed into
  TE/GSIC/GIS/AIS/LWS/Total, with BOTH a +0.01 GtC and a +1e-4 GtC arm overlaid.
  - Driver: `python/scripts/rennels/rennels_build_ssp245_cubes.py` — FaIR v2.2.4
    (v1.4.5 cal) SSP2-4.5 baseline + 4 pulse arms (±0.01, +0.02, +1e-4 GtC at
    2020.5, CO₂ FFI), emits **GMST + OHC flat-cubes** (float64 — float32 destroys
    the 1e-4 GtC signal, ~1e-7 °C on ~2.5 °C). Pulse in GtC→GtCO₂ ×44/12.
  - Figure: `python/scripts/rennels/rennels_7panel_figure.py`.
  - Outputs: `outputs/rennels/slr_7panel_ssp245.{png,pdf}`,
    `rennels_pulse_response_summary.csv`, 5 cubes + metadata, BRICK CSVs.
- **Result:** 1e-4 GtC pulse IS resolvable through BRICK in float64; the two arms
  agree to <0.2% at 2150 (linear). Per-GtCO₂ total marginal @2150 = 0.0073
  cm/GtCO₂ (matches memory ~0.0074). TE dominates; LWS ≈ 0 (pre-2019 calib).
- **Sanity:** all 5 paired-pulse tests pass at FaIR level (zero/sign-flip 0.02% /
  doubling 2.0002 / linearity 0.02% / first-principles 0.415 m°C/GtCO₂) AND BRICK
  level (repro bit-identical / sign-flip anti-sym / doubling 2.0000 / linearity
  0.29% / closure Σcomp=total to 1.4e-13 m).
- **Caveat flagged on-figure:** unweighted SSP2-4.5 median runs above AR6
  (69 vs ~50 cm @2100; 132 vs ~68 cm @2150) — consistent with this project's
  hot BRICK posterior (RFF-SP gives ~93 cm @2100), not a bug; per user's
  explicit "unweighted climate+BRICK spread" choice (no Wong importance weights).
- **Absolute-units variant** `slr_7panel_ssp245_abs1em4.{png,pdf}`: right panels
  in metres of SLR per literal +1e-4 GtC pulse (TE ~2e-8 m @2300; direct-1e-4 vs
  0.01÷100 agree <0.2%). For comparison with Rennels' own per-1e-4-GtC numbers.

### Fixed / corrected
- **AIS get_model seed-bug note in CLAUDE.md was overstated** ("uniformly
  non-negative once seeded"). Measured: matched-seed AIS median is slightly
  NEGATIVE at 2050 and 34–56% of draws are negative at all horizons — the true
  small-pulse AIS signal straddles zero. A negative *median* alone is not proof
  of the bug. Demonstrated the actual bug signature: seed-mismatch zero-pert
  (2026 vs 1234) injects a systematic AIS offset (median −5e-4 cm, 100% negative)
  ~100× the true ~5e-6 cm signal. Diagnostic tests added to the note.

## [v2.1] — 2026-05-29 — finalized substack + poster (Group-Sobol H-S)

### Changed
- **Group-Sobol is now the canonical SLR Hawkins-Sutton method** (replaces the
  earlier TreeSHAP/Shapley attribution, which under-counted the emissions axis
  ~3× — 8.6% vs ~27-29% at 2150 — because collinear cumulative-emissions
  features dilute per-feature Shapley credit). Sobol decomposes *grouped* variance
  directly, immune to within-group collinearity, and is importance-weighted.
  Module: `python/scripts/substack/group_sobol_hs.py`; renderers
  `render_hybrid_tipping_split.py`, `paired_figures_hs.py`,
  `poster/hawkins_sutton_panels.py`.
- **Independent model-free cross-check:** a 324,000-run balanced-factorial ANOVA
  (`anova_hs_decomp.py`) reproduces the Sobol emissions/climate/internal shares
  to within ~2 pp at 2150 (emissions 27.0% ANOVA vs 28.9% Sobol), confirming the
  attribution is not a surrogate artifact. Overlay figure `anova_vs_sobol_overlay.py`
  → `outputs/substack/anova_vs_sobol_total_slr.{png,pdf}`.
- **Terminology:** reader-facing figures/captions now say "importance weighted"
  rather than "Wong-weighted" (provenance comments keep "Wong").
- **Pulse SLR figure:** removed the ensemble-mean line from the pulse-SLR panel
  (tipping-corrupted, not pulse-size-invariant); median + 5-95% band retained.
  Pulse GMST keeps its mean (no tipping pathology).
- **Exceedance table caption** corrected to "FaIR v2.2.4 (v1.4.5 calibration)"
  — distinguishes the model version from the calibration posterior.

### Notes
- Superseded TreeSHAP-era H-S outputs quarantined under
  `outputs/quarantine/20260528_treeshap_slr_underattribution/`.
- Decided to keep Sobol canonical and ANOVA as validator; no pulse ANOVA (the
  cross-check's motivation was the emissions axis, which is ~1% / uncontroversial
  for the pulse). See `notes/handoff_2026-05-28b_group_sobol_hs.md`.

## [Unreleased] — v145 end-to-end pipeline

### Added
- **Hybrid total_slr H-S decomposition with augmentation-based V_BRICK + V_seed** (2026-05-27).
  Pure-Shapley failed for SLR: even high-capacity surrogate + p99 outlier clip left
  OOF V_residual at 25-32%, factor 6-47× the pure-seed gold standard. Diagnosed as
  cfg×post interactions + AIS tipping nonlinearity that HistGradientBoosting can't
  capture. Replaced V_BRICK and V_seed in the SLR figure with model-free estimates:
  - V_BRICK: within-cell variance across 10 BRICK posts per cell (90,000 augmentation
    runs: 10,000 v5 cells × 9 extra post_idx via LHS-stratified sampling).
  - V_seed: within-cell variance across 10 seeds per (rff, cfg, post) group (200
    parent cells × 9 extra seeds = 1800 new FaIR runs + paired BRICK).
  Result: V_internal_SLR now declines from 4.6% (2025) to 0.5% (2150), matching
  physical expectation. BRICK is the dominant axis (~42-59%) across all years. A
  residual wedge (20-37%) is labeled as "cfg×post interactions + tipping" since
  those interactions can't be uniquely attributed.
  Files: `python/scripts/substack/hybrid_hs_total_slr.py`,
  `outputs/substack/shapley_hs_total_slr_hybrid.{png,pdf}`,
  `outputs/substack/v5_hybrid_decomp_diagnostic.csv`.

- **v5 noise-isolated H-S figures landed** (2026-05-27).
  Re-ran `shapley_hawkins_sutton.py` against the new LHS-10k_s cubes
  (`cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt}_flat2015.npz`) and
  the post-PR#93 BRICK posterior. Headline:
  - total_gmst V_internal at 2021 = **97.5%** (canonical H-S near-term
    recovered; v4 had ~0% because LHS-10k was single-seeded).
  - total_slr at 2050: emi 2% / climate 38% / brick 40% / internal 20%
    (first time all 4 axes nonzero — v4 internal was misallocated to
    surrogate fit gap).
  - pulse_gmst: ~100% climate response (matched-seed cancels internal).
  - pulse_slr: BRICK 35-50% of variance across 2050-2150.
  Companion BRICK metadata `outputs/lhs10ks_brick_metadata.csv` LHS-samples
  `post_idx ∈ {0..9999}` (one unique BRICK posterior member per cell);
  the previous `lhs10k_metadata_v145.csv` only used 3 unique post_idx
  across all 10,000 cells, which had been silently under-sampling BRICK
  uncertainty across the entire v4 family of plots.
  Caveat carried forward: TreeSHAP under-attributes BRICK; Owen-Shapley
  re-render (~40 hr Torch) still pending.

### Fixed
- **Hawkins-Sutton nested-ANOVA finite-replication bias** (2026-05-26).
  The variance-decomposition functions in `python/hawkins_sutton.py`
  (`decompose_slr_4way`, `decompose_gmst`) and the substack-side
  reimplementation in `updated_hawkins_sutton.py` were using `ddof=0`
  population variance at every level and were not subtracting the
  propagated within-cell sampling-noise term from each outer-level
  variance. With only 3 seeds × 3 posts per (rff, cfg) cell, the
  ddof=0 estimator was biased down by (n−1)/n = 2/3 at the inner
  level, and the cfg-means carried σ²_seed/n_seed sampling noise that
  was being absorbed into V_climate. Result: total-GMST early-year
  f_internal showed as 65% (canonical Hawkins-Sutton expectation:
  ~100%) and the substack/poster Panel C / D fractions were
  systematically tilted away from V_internal and toward V_climate.
  Fix: unbiased ddof=1 variances at every level via the
  `n_eff/(n_eff − 1)` Bessel correction (handles weighted variance via
  the effective sample size), plus subtract the propagated noise from
  each outer level (V_internal/n_seed off V_climate; V_climate/n_cfg
  plus V_internal/(n_cfg × n_seed) off V_emissions; analogous 4-way
  formulae with V_brick at the bottom). Clipped to ≥0 since
  finite-sample bias-corrected estimates can go slightly negative when
  the true variance is below the noise floor. Affected outputs: every
  Hawkins-Sutton figure in the substack and poster. Substantive
  changes: total-GMST f_internal at 2030 went 62% → 80%; Panel C
  fractions at 2100 went f_clim/f_emi/f_brick/f_int = 80/3/13/3% →
  54/23/23/0%; Panel D at 2100 went 17/3/45/35% → 1/1/81/16%. The
  Panel C/D PDFs in the IEc handoff are regenerated, and the
  discussion paragraph in poster_text.txt has been updated to reflect
  the new fractions.

### Tried and abandoned
- **Lemoine-Traeger tipping-decomposition framing for pulse-marginal SLR
  figures** (2026-05-26). Three active sites used L-T classifiers with
  inconsistent methodology: `gaussian_vs_empirical_slr.py` used a
  pulse-outcome classifier (per-year marginal > 0.3 cm; pulse-size
  sensitive); `extract_lhs10k_smallpulse_summary.py` used a baseline-state
  classifier (`ais_2100_cm > 20 cm`) but it was silently dead because the
  slim CSV didn't carry `ais_2100_cm`; `lemoine_traeger_decomposition.py`
  used baseline-state but had no callers. We initially standardized on
  baseline-state at 20 cm; that revealed that v1.4.5 + post-PR#93 BRICK +
  Wong weighting leaves 88% of cells classified as tipping-prone, so the
  "L-T linear baseline" was a 12%-subset mean (small slice; the L-T
  premium framing was more informative under v1.4.1 where tipping was the
  minority state). Decision: empirical importance-weighted p5/p50/p95
  quantiles satisfy "accurately reflect likely impact + uncertainty"
  while being both threshold-invariant AND pulse-size-invariant.
  `gaussian_vs_empirical_slr.py` + outputs retired to
  `outputs/quarantine/20260526_lt_to_empirical/`. Tipping-conditional
  columns dropped from `extract_lhs10k_smallpulse_summary.py` output.
  `lemoine_traeger_decomposition.py` library kept as a diagnostic
  utility (marked as such in its docstring) for any future revisit of
  the decomposition framework.

### Added
- **v1.4.5 FaIR pipeline end-to-end**: 18 v1.4.5 cubes (9 LHS-10k + 9 ANOVA-18k;
  baseline + 8 pulse arms each) on Torch; new BRICK driver
  `julia/run_mimibrick_flatcube.jl` adapted to the flat
  `(n_cells, n_year)` cube schema. 270× compute reduction vs. the rectangular
  layout that was used in the v1.4.1 era.
- **`run_mimibrick_flatcube.jl`** flat-cube driver with paired closure check
  (Σ components ≡ total SLR to 1e-10 m on the first row).
- **`python/scripts/run_wong_pipeline_v145.py`** end-to-end Wong-weighting
  pipeline matched to the new schema: l_FB from per-arm BRICK CSVs,
  l_B from post-PR#93 posterior, per-arm baseline-weighted CSVs + envelope
  summaries + paired marginal envelopes.
- **`python/scripts/emit_slim_legacy_csvs_v145.py`** writes slim,
  legacy-schema CSVs (bare-year SLR columns + keys + w_norm) so downstream
  plot scripts (`gaussian_vs_empirical_slr`, `slr_band`, `run_4way_slr_decomp`,
  `run_pulse_4way_slr_decomp`) work unchanged on the v145 outputs.
- **Tony component overlay**: added an LWS panel (BRICK ≡ 0 by design
  through the hindcast — Wong et al. 2017 calibration target had LWS
  removed — plus Frederikse 2020 Terrestrial Water Storage overlay).
  Added Frederikse 2020 overlays to the AIS and GSIC panels so the
  20th-century component biases that cancel into matching GMSL are
  visible: BRICK AIS overshoots Frederikse by ~3.3 cm at 1900 (1900-2000
  rise of +3.95 cm vs Frederikse +0.6 cm), GSIC undershoots by ~4 cm at
  1900, GMSL net agreement is within ~0.2 cm — diagnosed bias cancellation.
- **`fair_vs_obs_gmst_ohc.py`** new substack diagnostic figure: v1.4.5
  ensemble-mean GMST vs IGCC 2024 (4-dataset mean), and FaIR v1.4.5
  ensemble-mean OHC vs spliced Zanna 2019 + IGCC 2024.

### Changed
- **BRICK posterior**: swapped pre-PR#93 (`b > v0` in 97.6% of draws) for
  post-PR#93 (`b > v0` in 0%). The new posterior matches Frederikse 2020
  GIS back to 1900. Old posterior moved to
  `data/MimiBRICK/quarantine/20260524_pre_pr93/` with a README.
- **CITATION / .zenodo.json**: updated calibration source from FaIR v1.4.1
  to v1.4.5 and BRICK posterior provenance from v1.0.1 to post-PR#93 joint.

### Quarantined (pre-fix outputs, kept for postmortem)
- `outputs/quarantine/20260524_pre_v145_e2e/` — v1.4.1-era weighted CSVs
  superseded by v1.4.5 outputs:
  - `brick_lhs10k_baseline_to2300_weighted.csv` (LHS-10k baseline, v1.4.1 era)
  - `brick_lhs10k_pulse0p01gtc_to2300_weighted.csv`
  - `brick_lhs10k_pulse_to2300_weighted.csv` (1-GtC pulse)
  - `brick_anova_long_2300_weighted.csv` (13,500-row ANOVA, v1.4.1 era)
  - `brick_anova_long_2300.csv`, `brick_anova_pulse_long_2300.csv`,
    `brick_anova_marginal_long_2300_weighted.csv`
- `data/MimiBRICK/quarantine/20260524_pre_pr93/parameters_subsample_brick.csv`
  — pre-PR#93 posterior (97.6% b > v0).

### Diagnosed but not fixed (deliberate documentation)
- BRICK 20th-century **AIS overshoots Frederikse 2020 by ~3.3 cm at 1900**;
  cancels against GSIC undershoot. PR#93 only added Frederikse GIS to
  calibration; TE / AIS / GSIC still calibrated to Wong et al. 2017 targets
  (pre-ARGO Gouretski 2007 OHC and a less complete antarctic obs basis).
  Fix would require a future PR adding Frederikse AIS/GSIC to the
  calibration target set. Documented in memory
  `project_brick_component_biases_vs_frederikse`.

## [v1.0-poster-agu-chapman] — 2026-05-06
- Initial v1.4.1-era pipeline + AGU Chapman SLR conference poster artifacts.
- LHS-10k conditional-BRICK ensemble (ESS = 7,037).
- Hawkins-Sutton 4-way decomposition of total SLR and pulse-marginal SLR.
- Zenodo DOI: 10.5281/zenodo.20312325.
