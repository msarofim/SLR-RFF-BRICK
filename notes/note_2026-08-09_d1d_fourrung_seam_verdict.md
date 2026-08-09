# Note 2026-08-09 — D1d (4-rung fits + r19 seam) verdict: pre-registered bars NOT met, but the constraint landscape has flipped — every underlying datum is now satisfied within ~1.3σ and the offline program has converged

Script `python/d1d_fourrung_seam.py`; outputs `outputs/d1d_fourrung_seam.csv`,
`d1d_blocks.csv`, `figures/d1d_fourrung_seam.png`. Sanity 3/3 (obs_adj identity +
net r19 removal 0.38 mm; hindcast-sum identity; rung residuals bounded). Pathological
comparators per (variant, obs-mode) with matched U/δ freedom.

## 1. Bars

Pre-registered: minimal = C_both ANCH deficit ≤ 8.4 (D1c taper) with |δ| ≤ 1σ and 4/4
gates; strong = feasible (≤ 5). **Both NOT MET — 0/12 feasible.** Deficits improved
(A_4rung 7.3 / B_seam 8.0 / C_both 8.2, δ ≤ 1.0σ, U again ≈ the Frederikse central
29.3–33.1 mm) but the **S(1900) gate now fails low in every ANCH/MID arm**
(8.1–9.8 mm vs the 10–30 box), so npass = 3/4 throughout.

## 2. What the options did (attribution, ANCH/unc_t5d)

| change | deficit | S1900 | modern rate (hind, adj-obs ~0.81) |
|---|---|---|---|
| D1c taper (ref) | 8.4 | 10.1 | 0.76 |
| A: 4-rung fit only | 7.3 | 9.5 | 0.79 |
| B: seam+Farinotti basis only | 8.0 | 8.7 | 0.96 |
| C: both | 8.2 | 8.1 | 0.97 |

- **Option 1 (4-rung, band σ, corr 0.6, soft Farinotti a-prior) worked as intended:**
  all rung |z| ≤ 0.2, a-prior z ≈ 0 — the exponential holds all four rungs WELL inside
  their uncertainties (no overconstraint; Marcus's concern directly verified). T_offs
  relaxed downward (FAST −1.53→−1.06/−1.21; old-SLOW +0.59→+0.19), buying 1.1 logL.
- **Option 4 (seam + r19 BSL basis) costs, as predicted for honest accounting:** the
  obs_adj/hindcast-exclusion is roughly deficit-neutral to −0.9, and the Farinotti r19
  stock (0.069 vs Gt-share 0.097) removes ~1.4 mm of early r19 melt → S(1900) drops
  below the box floor. The BSL fix is physically right; the box was calibrated in the
  pre-uncharted, Gt-share world.
- ANCH now OVERSHOOTS modern (0.96–0.97) in the seam variants; MID (κ free, ν anchored)
  sits at 0.84–0.85 and deficit 5.1–6.6 — κ freedom worth ~1.5 logL as throughout.
- The λ-bridge diagnostic (interpolating two-rung↔four-rung frames) was considered and
  NOT run: both endpoints share the S1900 miss (8.1 vs 8.7), so no interpolation can
  recover the floor — stillborn, documented here so it isn't re-proposed.

## 3. The real result: the constraint landscape has flipped

Every underlying datum is now satisfied within its own uncertainty:
- **FREE arms fit the entire adjusted century at noise level** (deficits −0.4 to +0.9)
  — the data are fully consistent with the 3-reservoir + F_unch structure;
- deficit 7.3–8.2 is measured against a fully-fitted 9-param comparator (the
  unconstrained-frame advantage the program deliberately renounces);
- S(1900) = 8–10 mm vs Leclercq N(20, 9) is z ≈ −1.2σ — AND in the direction the scope
  argument predicts: Leclercq's length-record 20 mm is total-scope (it includes pre-1900
  melt of the later-uncharted small glaciers; F_unch starts 1901 per P&M's window), so
  an inventory-scope model SHOULD sit somewhat below it. The 10–30 hard box predates
  the uncharted-scope understanding;
- δ = +0.28–0.30 (≤1σ Roe); U = 29–33 mm ≈ Frederikse central; spread 6.2–6.7 in-band;
  ladder in-band; inventory z ≈ 0.55;
- the one genuine residual: the ANCH arm's modern overshoot (0.97 vs ~0.81 adj), which
  MID resolves with κ within its own log-prior.

**Conclusion: the offline point-optimization program has converged.** It is now
fighting pre-registered box EDGES while every constraint is met within ~1.3σ. Further
offline cells would be tuning, not learning. The produced assets are exactly what extC
needs: the 3-reservoir structure, rung covariances (band σ, corr 0.6), Farinotti
a-priors, U ~ flat[P&M] with taper profile, δ ~ N(0, 0.3) on 1900–1960, τ50 anchors as
priors (not hard constraints — the ANCH-vs-MID gap says the data want ~±30% κ freedom),
obs_adj target, and widened per-block T_off bounds. Whether the S(1900) box should be
re-derived for inventory scope (e.g., Leclercq minus a pre-1900 uncharted share) is a
Marcus call to make explicitly.

## 4. State

Branch `brick-mengel-vnext`; nothing running; extA108 still canonical; pulse arms
parked. The D1→D1d arc: handoff_2026-08-07_d1_multireservoir_verdict.md,
note_2026-08-08_d1b_slow_split_verdict.md, handoff_2026-08-08_d1c_uncharted_verdict.md,
memo_2026-08-08_geometry_drift_literature.md, this note.
