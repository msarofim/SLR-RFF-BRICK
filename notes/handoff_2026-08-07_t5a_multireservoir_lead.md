# Handoff 2026-08-07 (late night) — T5a multi-reservoir (regional-block) glacier structure is the LEAD candidate; D1 offline feasibility cell specced

**Self-contained pickup:** this note + `notes/memo_2026-08-07_glacier_constraint_anatomy.md`
(the why) + `notes/handoff_2026-08-07_t2_scope_anchor_t1_two_reservoir.md` (T2/T1 evidence) +
memory `project_brick_mengel_vnext_recalib`. Branch `brick-mengel-vnext`. Nothing running.
extA108 remains canonical; pulse arms parked.

## 1. Standing decisions (Marcus, 2026-08-07)

1. **Scope-corrected GlacierMIP3 anchors ADOPTED** — now the gate constants in
   `d0_glacier_shootout.py` (com@1.2/1.5/2/3K = 37.4/46.3/63.0/75.5, likely [11.8,54.0]/
   [17.2,63.2]/[41.5,75.5]/[58.5,83.9], sens 95 mm; provenance comment preserves the published
   values; eval self-test 4/4). All downstream scripts inherit by exec.
2. **T4 REJECTED** (accepting ν≈0 + under-dispersed spread is off the menu).
3. **T5a — multiple glacial reservoirs with regional identity — is the LEAD candidate**
   (this handoff). T5b (κ(T) single reservoir), T5c (hindcast/projection hybrid), T5d
   (early-segment discrepancy term) remain on the menu as written in the memo §4 — proposed,
   not yet ruled on.
4. Prior session evidence this builds on: T1 falsified all frame-sharing pool splits (0/110;
   P2 collapsed to single-N for lack of per-pool data); the tension is a SHAPE mismatch (law
   demands 1.92× century flow acceleration, target shows 0.76× deceleration) that is
   anchor-insensitive (corner scan: ladder floor unreachable; overshoot 1.36–1.51 mm/yr at any
   solvable anchor).

## 2. The T5a idea in three sentences

The aggregate constraint set is mutually incompatible for ANY law that pushes one glacier stock
along one excess path; but it decomposes regionally: **fast, ETCW-forced regions carry the
historical flow shape; slow, high-committed regions carry the stock, the ladder gap, and — via
GlacierMIP3's response-time collapse under warming (stock-weighted τ50 513 yr @1.5 °C → 125 yr
@3 °C) — the scenario spread, while staying quiet in the hindcast.** Unlike the T1 pools, the
blocks are identified by per-region DATA already on disk: drivers, committed anchors, modern
flows, response times. T5a = 2–4 Nauels-ν reservoirs, one per region-block, each with its own
driver, S_eq, and transient, summing to the GSIC component.

## 3. D1 — the offline feasibility cell (do FIRST, no Julia surgery)

D0-successor pattern (`d0_glacier_shootout.py` exec-machinery; new script suggestion:
`python/d1_multireservoir_cell.py`). Pass/fail BEFORE any calibrator work.

### 3.1 Blocks (sub-decision A — recommended default: 2 blocks, threshold scan as sensitivity)

Assignment by GlacierMIP3 50%-response time at ~1.5 °C (S1a), threshold τ* = 250 yr:

| block | regions (our scope, excl r5) | mass share | committed@1.2K share | 2000–19 melt share | τ50 @1.5C (mass-wtd) | τ50 @3C |
|---|---|---|---|---|---|---|
| SLOW | r19, r03, r09, r07, r06 | ~72% | ~71% | ~36% | ~700 yr | ~170 yr |
| FAST | r01, r04*, r17, r13, r14, r02, r15, r08, r10–12, r16, r18 | ~28% | ~29% | ~64% | ~120 yr | ~35 yr |

(*r04 sits at τ=241 — near the threshold; scan τ* ∈ {200, 250, 300} and report block-assignment
sensitivity. A 3-block variant (SLOW / ARCTIC-FAST / LOWLAT-FAST) is the first extension if
2 blocks fail on the early-century flow shape — the ETCW lives in Arctic fast regions r01/r02/
r10, not in r11/r16–18.) Exact per-region numbers: `outputs/diag_constraint_anatomy_regions.csv`.

### 3.2 Per-block ingredients (all sources on disk unless flagged)

- **Drivers T_b(t):** GlaMBIE-year-2000-AREA-weighted mean of member-region series from
  `data/observations/t_glac_regions_hadcrut5.csv` (area weighting = consistency with
  `build_t_glac.py`'s global composite; sub-decision B if mass-weighting preferred). Rebaseline
  1850–1900; projection splice per block: amp_b × GMST, anchor 2014–2024, with **amp_b from
  GlacierMIP3's own regional warming ratios**
  (`data/observations/raw/gmip3/climate_input_data/temp_ch_ipcc_ar6_isimip3b_glacier_regionally.csv`
  + regchar `median_reg_vs_glob_temp_ch_1.5_3.0`) — the per-block analogue of amp_g=1.8.
- **S_eq per block:** a_b = block share of the A2 inventory V=0.290 (first cut: Gt-share
  partition from S3 masses; FLAG: below-sea-level basis — straight Gt/361.8 gives 0.343 m for
  the scope vs Farinotti-SLE 0.290, and the BSL correction concentrates in r19/r03, so a
  Farinotti-2019 per-region SLE partition (Hock 2023 tables) is the refinement — data-prep item,
  not on disk). (b_b, T_off_b) from the block's OWN two-rung ladder: solve
  S_eq,b(amp_b·1.2) and S_eq,b(amp_b·2.0) = the block's per-experiment composite committed
  fractions — computable EXACTLY per block from the shifted netCDF with the T2 machinery
  (`t2_gmip3_scope_anchor.py` `composite_xy(scope=block)`; the nc is on disk). Two rungs → two
  equations → (b_b, T_off_b) given a_b. No global SC solve needed.
- **Transient per block:** Nauels-ν with per-block κ_b. **Anchored arm (the interesting one):
  set (κ_b, ν_b) from the block's TWO response times** — τ50 under constant amp_b·1.5 and
  amp_b·3.0 glacier-K forcing must reproduce the GlacierMIP3 values (two constraints → two
  params; integrate the block ODE to 50% committed loss). The hindcast then becomes an
  out-of-sample TEST, not a fit. **Free arm:** κ_b (log-prior from 1/τ_b) and shared ν
  N(1.0,0.5) — the extB3-style fallback. Sub-decision C: ν shared vs per-block (recommend:
  anchored arm derives per-block; free arm shares one ν).
- **Flow likelihood:** (i) the AGGREGATE 1900–2023 GSIC target as now (blocks sum; pre-1940
  σ×2 standing, or T5d switch below); (ii) NEW block-level modern terms: per-block 2000–23
  GlaMBIE flows (per-region files in `glambie_data.zip` — r5 already extracted, others unpack
  on first use). OPTIONAL (fetch): Zemp 2019 per-region annual balances 1962–2016 to discipline
  the mid-century block split — flag before fetching.
- **T5d switch (carry in the cell):** replace pre-1940 σ×2 with a fitted 1900–1960 bias term
  b_M15 ~ N(0, prior from the Roe-2021 critique) on the Marzeion-derived segment. Run the cell
  with σ×2 AND with the discrepancy term; report both.

### 3.3 Criteria (pre-registered, same standard as T1)

- The 4 aggregate gates on the ADOPTED scope-corrected constants: A2 inventory |z|<1; S(1900)
  10–30 mm; aggregate GlacierMIP3 ladder inside the likely bands (amp_g=1.8 on the aggregate,
  as in eval_chain_gates); SSP126→585 spread @2100 in 4.5–13.5 cm.
- Flow: 1980–2023 window logL within 5 of the pathological free-N optimum (recompute the
  reference in-script; T1 value was 52.82 — machinery in `t1_two_reservoir_offline.py`).
- NEW reports (not gates yet): per-block modern-rate split vs GlaMBIE block sums; per-block
  ladder vs the block's own GlacierMIP3 composite; block S(1900) shares.
- Sanity battery per `climate-modeling` skill: blocks-sum-to-aggregate identity vs a single-N
  run at matched parameters; ν=0/κ=1/τ nesting check per block; driver-swap A/B (block drivers
  vs global T_glac on the same structure) to isolate the driver contribution — the D0 Gobs
  lesson says ALWAYS run the control.

### 3.4 What would count as failure

If the anchored arm misses the flow window by ≫5 AND the free arm only passes by collapsing
the blocks (κ's converging, spread dying — the P2 signature), T5a is falsified offline too;
fall to T5c (hybrid) vs T5b+T5d discussion with Marcus. Report the same frontier plot as T1
(`figures/t1_two_reservoir_offline.png` pattern) so the comparison is direct.

## 4. If D1 passes — calibrator surgery scope (for planning, do not start without the D1 verdict)

- `glaciers_nu_component.jl` → vectorized per-block component (or N instances); driver param
  per block (`glacier_surface_temperature_b`); `build_brick_nu`/`set_glacier_forcing!` extended.
- calibrate_mcmc_ext: gic block 5 → ~4·N_blocks + shared (a_b can stay fixed at the inventory
  partition initially; free b_b/T_off_b/κ_b + shared ν ≈ 7–9 new params for 2 blocks); new
  per-block GlaMBIE likelihood terms; per-block driver plumbing + splices.
- Tag suggestion: **extC** family (extC1 = 2-block anchored, extC2 = free, …); keep extB3/b/c
  chains as falsification evidence per convention.
- Postprocess/projection drivers still expect old names (unchanged since extB3 — see the
  falsified-tension handoff §6); the repoint list grows with per-block drivers.

## 5. Sub-decisions flagged (do not resolve silently)

A. Block count / τ* threshold (default 2 blocks, τ*=250, scan 200–300; 3-block Arctic split
   is the pre-registered extension).
B. Driver weighting within block (default GlaMBIE area, = global-composite consistency).
C. ν shared vs per-block (default: anchored arm per-block-derived; free arm one shared ν).
D. Inventory partition basis (default Gt-share; Farinotti-SLE/BSL refinement as data-prep).
E. Zemp-2019 per-region fetch for mid-century block discipline (optional; ask first).
F. T5d discrepancy term vs σ×2 (cell runs both; adoption is a Marcus call).
G. Whether the per-block ladder composites should use the exact per-experiment estimator
   (recommended; nc on disk) or the S1a centrals (quick first pass).

## 6. Traps / state

- All gate evaluation now runs on the ADOPTED scope-corrected anchors — comparisons against
  pre-2026-08-07 gate numbers (extB3/b/c evals, D0 tables) mix anchor vintages; re-evaluate
  old chains with current constants before quoting side-by-side.
- Modern-rate basis: use the TARGET-derived 0.81 mm/yr (2015–23) for overshoot ratios, not the
  handoff-era 0.6 (GlaMBIE-2020 figure) — see memo §1 C2.
- `t_glac_regions_hadcrut5.csv` per-region series carry `fill_frac` (pre-1898 global infill) —
  propagate as an early-driver caveat for the Arctic-fast block.
- regchar regional warming is ISIMIP3a GSWP3-W5E5 (reanalysis-forced), NOT HadCRUT5 — fine for
  ratios/priors, don't mix with the HadCRUT5 driver series in a likelihood.
- The exec-rebind trap (`OUT_CSV`/`OUT_FIG` shadowed by the shootout import) bit again this
  session — set output paths AFTER the exec (fixed in `diag_constraint_anatomy.py`; pattern
  documented there and in `d0_final_selfconsistent.py`).
- The 1.47 GB GlacierMIP3 netCDF is untracked by design (gitignored; re-fetch recipe in
  `data/observations/raw/README_modern_extensions.md`).
- moepy is pip-installed in ~/climate-env (T2 needs it; D1 only if using the exact per-block
  ladder estimator).
- Shell cwd resets between calls — `git -C` / absolute paths.
