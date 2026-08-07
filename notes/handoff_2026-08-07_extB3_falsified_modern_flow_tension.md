# Handoff 2026-08-07 (evening) — extB3/b/c tuning all FALSIFIED; the binding tension is MODERN flow vs the GlacierMIP3 ladder, not the Marzeion segment

**Self-contained pickup:** this note + `handoff_2026-08-07_extB3_ready_to_launch.md` (the design
that was tested) + memory `project_brick_mengel_vnext_recalib`. Branch `brick-mengel-vnext`.
Nothing is running. extA108 remains canonical; pulse arms stay parked. **A structural decision
(§5) is required before any further tuning — do not launch more arms without it.**

## 1. What was run (all 500k RAM tuning, seed 2026, ~36 min each — the 4 h estimate was compile-dominated; true ~4.3 ms/iter)

| arm | GSIC pre-1940 σ×2 | dang_sig | accept | gates (joint) | S1900 med | inv z med | spread med | P(ν<.05) |
|---|---|---|---|---|---|---|---|---|
| extB3  | no  | old (Fred sd) | 0.237 | **0/4** | 44.9 mm | −1.19 | 1.56 cm | 0.24 |
| extB3b | yes | old (Fred sd) | 0.239 | **0/4** | 37.8 | −1.04 | 1.41 | 0.26 |
| extB3c | yes | new (Dang v2 SE) | 0.239 | **0/4** | 34.4 | −0.68 (PASS) | 1.25 | 0.24 |

All three camp on the same mode: **ν ≈ 0.10–0.12, T_off ≈ −1.8, a ≈ 0.33, b ≈ 0.35** — deep
offset partially back (committed@1850 ≈ 0.15 m), ladder over-committed (63/70/78/89% at extB3c),
scenario spread dead. Gate machinery: `python/eval_chain_gates.py` (self-tests vs the d0_final
C_nu1.0 row; ladder/spread at amp 1.8; full-maxlag Geyer ESS). Chains + eval CSVs + figures in
`outputs/{mcmc,}/`; per-arm caliblogs beside the chains. NB tuning-chain ESS is poor
(gic_b ~67–130, log_post ~100–240) — fine for mode identification, not for posterior claims.

## 2. Dangendorf v2 (same day, folded in)

Sönke's corrected `KalmanSmootherHR_Global.nc` → `data/observations/raw/
dangendorf2024_KalmanSmootherHR_Global_v2.nc`. Old file's GMSL/SE slots held BARYSTATIC (old
GMSLHR ≡ v2 GBSLHR); v2 fixes slots; **SE units are METERS** ("3 mm in 2021, not 0.3 mm" —
SE(2021)=0.00268 m). Our Fields-derived `dangendorf2024_gmsl_annual.csv` validates against v2
GMSLHR **bit-exactly** (demeaned 0.0000 mm; constant 53.45 mm baseline offset). The
"Frederikse-sd is conservative" σ rationale was FALSIFIED (true SE 1.3–2× larger 1900–2010,
smaller post-2015) → **Marcus adopted the native v2 SE** → `prep_recalib_targets_ext.py`
updated (units assert), targets rebuilt (only dang_sig/lo/hi changed, 1900–2021), committed.
This is now the standing likelihood regardless of what §5 decides.

## 3. The diagnosis that changes the plan

`julia/diag_pathology_terms.jl` (includes the calibrator setup; per-term posterior at the chain's
best 2nd-half draw vs the same draw with the glacier block at the D0 SC ν=1 point, gsic+dang
AR(1) noise re-optimized per variant). extB3c numbers (extB3b nearly identical):

| term | Δ(SC − pathological) |
|---|---|
| flow_gsic | **−24.6** |
| flow_dang | −6.0 |
| prior_gic (incl ν prior) | +3.6 |
| lec_A2b | +1.2 |
| inv_A2 | +0.2 |
| everything else | ~0 |

**The GSIC flow term alone buys the pathology.** And the AR(1)-whitened per-ERA attribution
(python, matches the Julia total to 0.02): with the pre-1940 σ×2 active, 1900–1919 costs only
−1.5; **the price is −17.8 in 2000–2023 and −5.2 in 1980–1999.**

Physical mechanism, verified analytically: the ladder gate demands a committed-but-unmelted gap
S_eq(T_now) − S(now) ≈ 0.105 m; at ν=1 (κ=.00607 from the D0 fit) the transient law converts
that gap to dS/dt = κ·exc·gap ≈ **1.1 mm/yr at 2020 vs observed (GlaMBIE-scope) ≈ 0.6 —
a ~1.7× modern-rate overshoot** (SC cumulative model−obs +1.2 cm over 2000–2023, z up to 11 on
per-year ε; the pathological draw tracks the same years to 0.03 cm by shrinking the gap).
The memo §3e claim "the missing melt is entirely 1900–1940" was computed under UNINFLATED early
ε (and at the ν=2 corner); with the early segment properly cheapened, the real binding tension
is **GlacierMIP3-committed ladder ⟺ observed modern melt rate, mediated by the single-reservoir
transient law**. The Roe/Marzeion data-trust question is RESOLVED (σ×2 did its job); this one is
structural and data-vs-projection-model.

## 4. Machinery added today (all committed)

- `python/eval_chain_gates.py` — per-draw gate evaluation for any chain (self-testing).
- `--gsic-early-sigma-x2` flag in `calibrate_mcmc_ext.jl` (extB3 stays bit-reproducible).
- `julia/diag_pathology_terms.jl` — per-term decomposition chain-draw vs SC point.
- Dangendorf v2 file + README provenance + rebuilt targets.
- Stale-comment fix (A2 header 2020→2000).
- CHANGELOG entries; caliblogs for all three arms in `outputs/mcmc/`.

## 5. Decision menu (Marcus — do not resolve silently)

**T1. Transient-law surgery (two-reservoir ν / rate-limited committed pool).** The single
reservoir cannot hold 0.105 m committed at low modern outflow AND deliver ν-driven scenario
spread. A slow/fast split (Nauels-ν on the fast pool; long-τ slow pool holding most committed
ice) or an explicit rate cap decouples ladder from modern rate. NB extB3 removed the 2-τ split
as "onset-faking" — this evidence suggests its load-bearing job was committed-ice retention,
not onset. **Test first (offline D0-style cell, no Julia surgery):** {2-reservoir-ν × Tglac}
at SC S_eq — does any config pass all 4 gates AND fit 1980–2023 flow within ~5 logL of the
pathological optimum? The D0 machinery + `d0e_nu_kappa_map` pattern extends directly.

**T2. Ladder-anchor scope correction.** GlacierMIP3 committed %s are FULL-RGI; our stock is
excl-r5-incl-r19 (~20% of global stock differs). If the excluded/included peripheries have
above-average committed fractions, the scope-matched anchor at +1.2K is LOWER than 39% →
smaller demanded gap → smaller modern overshoot. **Test:** Zekollari 2025 per-region committed
data → recompute the anchor + likely ranges for OUR scope. Cheap, pure data work, zero model
change; could shrink the tension before any structural surgery.

**T3. Inflate/structure modern GSIC ε (discrepancy term).** Rejectable on principle — it
down-weights the best-measured segment (GlaMBIE) to save a projection-ensemble anchor. Listed
for completeness.

**T4. Accept ν≈0 as what the data say.** Calibrate at the hindcast optimum (Mengel-like,
ν→0), report scenario spread as structurally under-dispersed, and carry ν only as a labeled
projection-informed sensitivity arm. Honest but abandons the 4/4-gate design goal; the
glacier spread deliverable reverts to ~1.3 cm.

My read (flagged, not decided): T2 first (cheap, might shrink the gap), then T1 if the tension
survives; T1's offline test is a half-day. T3 rejected; T4 is the fallback if T1 fails offline.

## 6. Traps / state for the next session

- Targets on disk = NEW dang_sig (v2 SE). Any likelihood comparison against pre-2026-08-07
  chains must account for it (extB3 and extB3b ran on OLD dang_sig).
- extB3bsmoke/extB3csmoke junk deleted; extB3/b/c chains RETAINED as falsification evidence.
- `adapted_cov_extB3c_seed2026.csv` exists (38-param native) — if a future arm wants it as
  proposal seed, ADCOV currently still prefers extB2's name-mapped cov; edit deliberately.
- eval_chain_gates hindcast driver = calibrator convention (obs + 1.8×GMST splice); its
  exec of the shootout re-reads the CURRENT targets file for the flow obs/ε (uninflated —
  gates don't use the flow term, so the σ×2 flag doesn't affect gate numbers).
- postprocess_mcmc_ext.jl + projection drivers still expect OLD glacier param names (unchanged
  today; irrelevant until a tuning arm is accepted).
- Shell cwd resets between calls — `git -C` / absolute paths.
