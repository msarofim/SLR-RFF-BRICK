# Handoff 2026-08-08 — D1c uncharted-ice cell EXECUTED: pre-registered prediction NOT confirmed (deficit 8.4–9.0 vs tol 5), but the gap is now fully literature-priced; U lands at the Frederikse central; residual localized to the 1980–2023 window

**Self-contained pickup:** this note + `notes/memo_2026-08-08_geometry_drift_literature.md`
(the literature basis) + `notes/handoff_2026-08-07_d1_multireservoir_verdict.md` (D1) +
`notes/note_2026-08-08_d1b_slow_split_verdict.md` (D1b) + memory
`project_brick_mengel_vnext_recalib`. Branch `brick-mengel-vnext`. Nothing running.
Script `python/d1c_uncharted_cell.py`; outputs `outputs/d1c_uncharted_cell.csv` (14 rows),
`d1c_blocks.csv`, `figures/d1c_uncharted_cell.png`. Sanity 3/3 (U=0 nesting; F endpoints;
post-1990 m_cm invariance); ANCH/repro reproduces D1 to |diff|=0.00 and the sx2 patho
reproduces 52.82. Pathological comparators re-fit per variant WITH matched U/δ freedom.

## 1. Verdict against the pre-registered prediction

Prediction (memo §4): ANCH/unc_t5d FEASIBLE (4/4 gates + flow-window deficit ≤ 5) with
|δ| ≤ ~1σ (0.30 mm/yr). **NOT CONFIRMED**: at the pre-registered constant-rate profile,
deficit 9.0 and δ = +0.37 (1.2σ) — fails both margins; at the taper profile sensitivity
(smooth landing, no 1990 step inside the criterion window) deficit 8.4, δ = +0.28 (0.9σ)
— passes the δ margin, still fails the deficit. 0/14 configs feasible. Gates: 4/4 in
every ANCH/MID arm, as throughout.

## 2. What the cell established anyway (the progress ledger)

| stage | ANCH deficit | δ (σ of original prior) | early-era logLs (1900-19/1920-49) |
|---|---|---|---|
| D1 sx2 | 20.7 | — | −43.5 / −37.8 |
| D1 t5d | 11.5 | 2.3σ | −17.7 / −18.1 |
| D1c unc_t5d | 9.0 | 1.2σ | −16.5 / −15.8 |
| D1c unc_t5d/taper | **8.4** | **0.9σ** | ~same |

- **U is not a free lunch that ran to its bound: it FITTED to 27.6 mm scope = 31.7 mm
  global (const) / 32.5 (taper) — essentially exactly the Frederikse-expected central
  (32.35, uniform-sampled [16.7, 48.0])**, from a flat prior that would have permitted
  14.5–41.8. Independent corroboration of the scope-mismatch mechanism.
- The early-century tension is effectively resolved: era logLs at the AR(1) noise floor
  with δ under 1σ of the ORIGINAL Roe prior. The D1-era "structure wants 75% of early
  flow to be artifact" is gone — the decomposition is now uncharted-ice (≈32 mm,
  literature-priced) + M15 bias (≈0.28 mm/yr on 1900–1960, sub-1σ Roe-priced).
- **FREE/unc_sx2 reaches deficit 0.55 at σ=0.005, ρ=0.08** — with U in place, free
  dynamics fit the whole century at noise level. The ONLY surviving tension anywhere in
  the system is the ν-spread coupling (FREE spread 1.6–3.2, still < 4.5; note it ROSE
  from 1.2 with U+δ — the pathological pull on ν weakens as the integral is explained).
- Profile ranking: taper (8.4) < const (9.0) << frontload (12.6) — the data prefer the
  physically-sensible smooth depletion.

## 3. Where the residual ~8 logL lives (all in 1980–2023, three identified candidates)

1. **The bookfix→anchor interpolation effect:** BOOK1 (uncharted subtraction from the
   melt-to-date partition) is conceptually required and preserves remaining-2020 stock
   EXACTLY (FAST a−S2020 = 0.074 before and after), but the two-rung exponential
   re-solve responds to the lower S2020 level by raising T_off (FAST −1.53→−1.28,
   SLOW +0.47→+0.59), cutting modern block rates ~10% (2015–23: 0.855→0.764 vs obs
   0.81; era-2000s 0.70→0.62). The book-only ablation (U=0) shows this costs +2.5
   deficit on its own. This is a structural sensitivity of the exponential S_eq
   interpolation between the two rungs — not obviously "right" or "wrong".
2. **The modern target seam:** the target's pre-2019 segment is Frederikse
   (r19 ≈ 0 by assumption + residual uncharted tail), spliced to GlaMBIE (r19 > 0,
   current-inventory) after — while the model blocks include r19's modern melt
   (~0.19–0.24 mm/yr). A scope-consistent modern-target arm (D1d candidate: harmonize
   r19 treatment across the seam using the on-disk GlaMBIE r19 series) would remove a
   knowable bias of roughly the observed residual's size.
3. Genuine late-century shape (the anchored ν≥1.35 acceleration timing vs obs) — the
   remainder after 1 and 2, currently not separable from them.

## 4. Decision points for Marcus

- **(a) D1d modern-seam cleanup** (target-side r19 harmonization + possibly re-examining
  the two-rung S2020-level sensitivity, e.g. anchoring the rungs at the remaining-stock
  coordinate instead of the cumulative-melt coordinate — a one-line change with the same
  data). Cheap (caches hit, no moepy). The last identified, priced, non-structural
  residual.
- **(b) Accept-with-label at the D1c state:** 4/4 gates out-of-sample; every discrepancy
  term literature-priced (U at the Frederikse central; δ = 0.9σ of the Roe prior); the
  8.4-logL flow-window deficit is measured against a fully-fitted 9-parameter
  pathological comparator, which is a demanding absolute bar for a structure with zero
  fitted physics parameters. Accepting means declaring the offline feasibility program
  complete and moving to extC calibrator surgery, where the MCMC weighs all terms
  jointly anyway.
- **(c) extC surgery directly** with the D1c structure (blocks + F_unch + δ as
  likelihood terms; per-block T_off bounds must be widened — SLOW T_off ≈ +0.6 is
  outside the current (−2.00, −0.10)).
- NOT proposed: further offline structural variants — D1/D1b/D1c have localized every
  remaining logL to priced, non-structural candidates.

## 5. Traps / state

- The pre-registered FLOW_TOL=5 criterion has now been missed by three successively
  better cells (20.7 → 11.5 → 8.4); if it is to be waived or revised, that is a Marcus
  call to make EXPLICITLY (the D1c prediction was mine and it failed as stated).
- Frontload profile is falsified as a shape (12.6); const's 1990 hard stop is a step
  artifact worth ~0.6 logL — use taper in anything downstream.
- BOOK arithmetic notes: Σa_b = INV_V + S2000_inv = 0.351; inventory gate unchanged
  (blocks-only); Leclercq/S1900 untouched by F (starts 1901).
- U enters ONLY the flow likelihood; projections/gates/spread are U-independent by
  construction (verified: post-1990 m_cm invariance sanity).
- All caches shared with D1 (`d1_gmip3_steady_cache.nc`, `d1_block_ladder_cache.csv`);
  D1c runs ~25 min cached, no moepy.
