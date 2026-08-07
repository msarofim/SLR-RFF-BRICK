# Handoff 2026-08-07 (late night 2) — D1 multi-reservoir cell EXECUTED: pre-registered criterion FAILS (0/10), but the anchored 2-block structure is the first ever to pass all 4 gates; residual tension isolated to the pre-2000 century integral, carried by ν itself

**Self-contained pickup:** this note + `notes/handoff_2026-08-07_t5a_multireservoir_lead.md`
(the spec) + `notes/memo_2026-08-07_glacier_constraint_anatomy.md` (the why) + memory
`project_brick_mengel_vnext_recalib`. Branch `brick-mengel-vnext`. Nothing running.
extA108 remains canonical; pulse arms parked. **Structural decision (T5c vs T5b+T5d vs
data-side options, §6 below) AWAITS MARCUS.**

Script: `python/d1_multireservoir_cell.py` (D0-exec pattern; output paths set after exec).
Outputs: `outputs/d1_multireservoir_cell.csv` (12 pre-registered + 2 post-hoc rows),
`outputs/d1_multireservoir_blocks.csv` (anchor table), `figures/d1_multireservoir_cell.png`
(T1-pattern frontier + block-resolved hindcast + ladders), caches
`outputs/d1_gmip3_steady_cache.nc` (71 KB, replaces the 1.47 GB nc read) +
`outputs/d1_block_ladder_cache.csv`. Commit tag in every output. Sanity battery 3/3 PASS
(blocks-sum identity 2.8e-17; ν=0 Mengel nesting exact; reproducibility). The sx2
pathological reference reproduces T1's 52.82 **exactly** — machinery self-validates.

## 1. Pre-registered verdict

**0/10 pre-registered configs feasible** (4/4 gates AND 1980–2023 flow logL within 5 of
the pathological free-single-N optimum). ANCH deficits 11.5–22.6 (all ≫ tol 5); FREE
never reaches 4/4 (spread dies at ν→0). Per §3.4 of the spec, the strict falsification
conjunction is met on its first clause (ANCH ≫ 5); the second clause fails *differently
than predicted* — FREE does **not** collapse the blocks (κ_F/κ_S stays ≈ 4.1, no P2
signature); it fails by railing ν→0 (the familiar D0/extB3 single-reservoir signature).
T5a **as specced does not pass the offline cell** → the §3.4 fallback menu is live.

## 2. What is NEW (and why this is not a T1-style dead end)

1. **ANCH passes ALL 4 aggregate gates in every variant/partition/split** — inventory
   (z 0.7–1.0), S(1900) (10–20 mm), ladder (in-band at every rung), spread (6.5–6.9 cm)
   — with **zero hindcast-fitted transient parameters** (κ_b, ν_b from GlacierMIP3
   response times; a_b, b_b, T_off_b from data partitions + the block's own two-rung
   composite ladder). No structure has ever passed all 4, let alone out-of-sample with
   ν ≥ 1.35. The modern rate is right for the first time: 0.85 vs target-derived 0.81
   mm/yr (the one-reservoir fit-history branch overshot 1.67×).
2. **The tension is now a LEVEL problem, localized pre-2000.** Era mean rates (mm/yr),
   ANCH/t250 (obs / model): 1900–19 0.89/0.23, 1920–49 0.96/0.34, 1950–79 0.52/0.21,
   1980–99 0.54/0.33, **2000–23 0.73/0.70**. Model S(2020) = 57 mm vs target 107 mm —
   GlacierMIP3's own committed ladders + response times, mapped through the per-block
   Mengel-exponential + Nauels form, only permit ~57 mm of melt since 1850. The missing
   ~50 mm is the entire residual misfit (the fitted AR(1) rails ρ at the 0.99 bound to
   absorb it as a smooth level error).
3. **MID post-hoc diagnostic (labeled, NOT pre-registered): the κ anchors are innocent.**
   Freeing κ_b (log-prior 1/τ50_b, block GlaMBIE rate terms on) with ν_b HELD at the
   anchored values moves the deficit 20.7→20.4 (sx2) / 11.5→11.9 (t5d) and the fitted
   κ's land next to the anchored ones (0.00127/0.0037 vs 0.00102/0.0032). **The deficit
   is carried by ν ≥ 1.35 itself — the same dial that buys the spread gate.** The block
   split relocated the ν-coupling to far better terms (4/4 gates now attainable) but did
   not break it: spread and pre-2000 flow still trade against each other through ν.
4. **T5d (Roe discrepancy term) absorbs about half the deficit** (20.7→11.5) at fitted
   δ = +0.69 mm/yr on 1900–1960 = **2.3σ of the Roe-motivated prior** (sd 0.30). I.e.
   the anchored structure "wants" ~75% of the observed pre-1960 flow to be
   Marzeion-2015 artifact. With δ at its fitted value the early obs and model nearly
   agree (see figure panel B); the remaining in-window gap is mid-century
   (1950–79 obs 0.52 vs model 0.21 — where the discrepancy term has tapered out).
5. **Per-block drivers contribute ≈ nothing to aggregate flow** (driver-swap control:
   deficit 20.0 vs 20.7) — the D0 Gobs-control lesson repeated. The payoff of T5a is in
   the per-block S_eq frames + anchored transients, not the regional driver shapes. The
   drivers DO improve the block-level rate split (S/F 0.20/0.52 vs control 0.15/0.59;
   GlaMBIE 0.24/0.42).
6. **Robustness:** τ*=200 (r04→SLOW) and hist-split 0.25/0.50 move deficits by ≤2 —
   no partition or melt-split choice rescues or breaks anything.

## 3. Block anchors (τ*=250 default; full table in d1_multireservoir_blocks.csv)

| block | regions | a_b (m) | b_b | T_off_b (glac-K) | amp_b | com@1.2/1.5/2/3K | κ_anch | ν_anch | τ50 tgt (ach) |
|---|---|---|---|---|---|---|---|---|---|
| SLOW | 19/03/09/07/06 | 0.241 | 0.478 | **+0.465** | 1.44 | 35/46/63/74 | 0.00102 | 1.35 | 665/159 (exact) |
| FAST | 01/04/17/13/14/02/15/08/10-12/16/18 | 0.142 | 0.414 | −1.526 | 1.23 | 45/51/63/79 | 0.00321 | 1.60 | 130/37 (exact) |

- The SLOW two-rung solve puts **T_off at +0.465 glacier-K**: the slow stock was in
  (or above) equilibrium preindustrially — zero committed at 1850 — and only crossed
  its melt threshold in the ~1990s. That is *why* the anchored structure cannot make
  historical melt: the physics GlacierMIP3 implies for r19/r03/r09/r07/r06 is
  late-onset. Composite committed@1850 = 67 mm (FAST only), vs the D0 SC point's
  87–92 mm. NB +0.465 is **outside the calibrator's T_off bounds (−2.00, −0.10)** —
  any extC surgery needs per-block bounds.
- Both anchored (κ, ν) solves are EXACT (τ50 matched to <2%); ν_SLOW=1.35, ν_FAST=1.60
  is the response-time-collapse mechanism working as designed.
- Ladder-basis nuance: at the DATA S(2020) basis the aggregate com@1.2K is 37.4% — on
  the adopted central by construction. The CSV's model-basis com@1.2K ≈ 47% (still
  in-band) is the century under-melt showing up in the denominator, not an anchor error.

## 4. Sub-decisions as run (spec §5; defaults, none silently resolved)

- **A** τ*=250 (scan 200/250/300; 250≡300, 200 moves r04 — immaterial).
- **B** GlaMBIE-year-2000-area driver weighting; amp_b = area-wt regchar
  `median_reg_vs_glob_temp_ch_1.5_3.0` per the spec. **FLAG: the regchar (ISIMIP3)
  ratios are systematically low** — area-wt aggregate 1.34 vs the calibrator amp_g=1.8
  convention and the obs through-origin fit 1.59 (per-block obs fits: SLOW 1.76 vs
  regchar 1.44; FAST 1.40 vs 1.23). Internally consistent as used (same amp_b in
  ladder solve, splice, projections, response-time forcing), but an obs-amp arm would
  shift anchors and spread — untested, listed in §6.
- **C** ANCH per-block ν (derived); FREE shared ν N(1.0,0.5) — as specced.
- **D** a_b partition = S3-2020-Gt shares of V=0.290 (Farinotti-SLE/BSL refinement
  still open; regchar 2000-volume alternative differs by ~2 pct-pts of share).
- **E** Zemp-2019 NOT fetched (was optional-ask; block split turned out not to bind).
- **F** both σ×2 and T5d run; T5d adoption is a Marcus call (it is doing real work:
  −9 logL of deficit, δ fitted at 2.3σ of its prior).
- **G** exact per-experiment composite estimator (moepy, reduced num_fits 300/1000).
- **H (NEW, not in the spec):** the 1850–2000 historical melt split between blocks is
  unconstrained on disk; default = Hugonnet 2000–19 melt shares (SLOW 0.354), scanned
  {0.25, 0.354, 0.50} — verdict-invariant. It enters a_b and the anchors, not the
  trajectory.

## 5. Traps / state for the next session

- ρ rails at its 0.99 bound in EVERY config (absorbing the smooth level misfit);
  σ 0.03–0.11. Same bound applies to the pathological reference, so deficits compare
  like-for-like — but the AR(1) is being used as a discrepancy model, which is itself
  diagnostic (the misfit is a level, not noise).
- The exec-rebind trap (OUT_CSV/OUT_FIG) handled — paths set after the shootout exec.
- Ladder/nc caches: delete `outputs/d1_gmip3_steady_cache.nc` +
  `d1_block_ladder_cache.csv` to force a full rebuild after any change to the steady
  window, model set, or scope. Re-run with caches ≈ 25 min (optimizer-dominated);
  first run ≈ 45 min (moepy-dominated).
- The regions table (`outputs/diag_constraint_anatomy_regions.csv`) is the block
  membership source; regenerating it via diag_constraint_anatomy.py after anchor
  changes re-derives τ50s from the same S1a/regchar columns.
- Figure panel B shows the FREE/t5d best-deficit config (lowest deficit overall);
  the ANCH era story is in §2.2's table and the CSV era columns.

## 6. Decision menu for Marcus (per spec §3.4 the fallback discussion is due)

The D1 evidence, compressed: *the anchored multi-reservoir gets every projection-side
demand right (all 4 gates, modern rate, no collapse) and fails only on ~50 mm of
pre-2000 melt that GlacierMIP3-consistent physics cannot produce; ν carries the
residual coupling; the early-segment data (LOW confidence, Marzeion-derived) absorb
half of it at 2.3σ of the Roe prior.*

- **T5c (hindcast/projection hybrid)** — D1 strengthens this: the ANCH arm *is* the
  projection half of a T5c already, and it now demonstrably satisfies every
  projection-side gate. The splice question reduces to "what carries the 1900–1990
  hindcast" (e.g. ν≈0 transient historically, anchored-ν for projections).
- **T5b+T5d** — D1 weakens this: FREE+T5d (the closest analogue run: ν→0 + fitted δ)
  still fails spread (1.2 cm), and MID shows κ(T)-style transient speedups alone won't
  restore the integral while ν holds the spread.
- **T5d-extended (data-side, NEW option from D1):** the fitted δ=+0.69 and the
  mid-century residual suggest the discrepancy window (1900–1960, prior sd 0.30) is
  both too tight in σ and possibly too short — the Frederikse GSIC is Marzeion-model-
  derived well past 1960. A wider/longer structured discrepancy (with an honest prior
  argued from Roe 2021 + Frederikse provenance) would make ANCH feasible AS IS:
  deficit 11.5 is within reach of a ~2-σ-wider prior. This is a claim about the
  TARGET's early-century trustworthiness, not about glacier physics — exactly the C3
  confidence question the anatomy memo flagged.
- **Accept-with-label** — adopt ANCH (4/4 gates, out-of-sample) and report the
  pre-2000 flow misfit as a known, quantified data-model discrepancy. Equivalent to
  T5d-extended without fitting the term.
- Orthogonal sensitivity worth one cell before extC surgery, whichever way: **amp_b
  from obs fits** (1.76/1.40) instead of regchar (1.44/1.23) — moves the ladder-anchor
  frame and the spread in opposite directions; cheap to run with the caches.

No calibrator surgery (extC) should start until this call is made (spec §4).
