# Scoping — does IMBIE 2026 warrant a STRUCTURAL change to DAIS? (2026-09-21, while L28 runs)

**Question (Marcus):** with the reconciled ice-sheet record (Otosaka et al. 2026, Sci Data 13:1301; AIS 1979–2023 with an
SMB / dynamics split, WAIS / EAIS / AP), is the Antarctic hindcast deficit a parameter problem (the refit fixes it) or a
structure problem (DAIS cannot produce what is observed)?

**Receipts:** `python/diag_imbie2026_vs_targets.py --tag=L27` (CHANGELOG 09-21f), `julia/diag_ais_flux_split_vs_imbie.jl
--tag=L27 1000` (DAIS's own β_total / ice_flux per draw on the calibration span; outputs
`diag_ais_flux_split_vs_imbie{,_draws}_L27.csv`), the IMBIE Gt files, `fair_mean_gmst_ssp245harm.csv`.

## 1. What the observed record is made of (IMBIE 2026, Gt/yr, ice-mass sign)

| window | AIS net | SMB anom. | dynamics anom. | WAIS dyn | EAIS dyn | AP dyn | GMST (K) |
|---|---|---|---|---|---|---|---|
| 1979–1991 | −47 | +14 | −62 | −34 | −24 | −5 | 0.456 |
| 1992–2002 | −79 | −7 | −73 | −56 | −7 | −11 | 0.580 |
| 2003–2010 | −158 | −1 | −157 | −118 | +2 | −45 | 0.862 |
| 2011–2017 | −200 | −21 | −179 | −159 | +5 | −28 | 1.033 |
| 2018–2023 | −104 | **+144** | −249 | −192 | −8 | −21 | 1.206 |

- The loss is **dynamics** (84 % of 1979–2023) and it is **WAIS** (−34 → −192); EAIS is in balance; the Peninsula is small.
- The dynamics anomaly is **near-linear in GMST**: on 11-yr means, −232 Gt/yr per K with residual sd 22 Gt/yr and no
  window residual above 14; a quadratic term buys 2 Gt/yr of residual. **No lag is visible** (the fit needs none).
- The 2018–2023 slowdown is **entirely SMB** (+144 Gt/yr; the record EAIS snowfall) — dynamics kept accelerating.
- SMB interannual sd is 123 Gt/yr (0.034 cm/yr); a 7-yr window mean carries an se of ~45 Gt/yr.

## 2. What DAIS does on the same span (L27 posterior, 1000 draws, medians; Gt/yr)

| window | SMB | discharge | net | dyn anomaly vs 1979–2008 | level rate (cm/yr) | IMBIE rate |
|---|---|---|---|---|---|---|
| 1979–1991 | 1845 | −1889 | −46 | +23 | 0.011 | 0.013 |
| 1992–2002 | 1847 | −1909 | −64 | +1 | 0.015 | 0.022 |
| 2003–2010 | 1854 | −1960 | −107 | −54 | 0.026 | 0.044 |
| 2011–2017 | 1864 | −1991 | −128 | −85 | 0.031 [0.026, 0.034] | 0.056 |
| 2018–2023 | 1874 | −2026 | −151 | −121 | 0.036 | 0.029 |

- **The partition matches**: DAIS puts the loss in the discharge, and its discharge anomaly tracks GMST like IMBIE's
  (change 1979–91 → 2011–17: model −108 Gt/yr, IMBIE −117 — **92 %**; ratio of modern to early net loss 2.8 vs
  IMBIE's dynamics ratio 2.9).
- **The gap in the acceleration window is more SMB than discharge.** 1992–2002 → 2011–2017: IMBIE net −121 (dyn −106,
  SMB −14); L27 net −64 (dyn −82, **SMB +17**). Discharge reaches 77 % of the observed change; DAIS's precipitation
  rises with warming (κ) while the RCM-based SMB anomaly fell 35 Gt/yr — a difference of ~31 Gt/yr that is **inside the
  SMB anomaly's own noise** (se ~45 for a window mean; the trend is not significant in the RCMs either).
- **The old posterior cannot reach the observed acceleration**: 2011–17 minus 1992–2002 rate is 0.015 cm/yr (max over
  1000 draws 0.033) against IMBIE's 0.034; the 2011–17 rate spans 0.026–0.034 across the posterior, IMBIE 0.056 ± 0.007.
  And **no single parameter controls it** (|Spearman| ≤ 0.16 for every AIS parameter) — the posterior sits on the
  compensating ridge the earlier work documented (Table A2). The sensitivity parameters are only partly identified
  (posterior / prior sd: anto_α 0.64, antarctic_α 0.71, T_oc,0 0.66), so the priors leave room for ~2× the sensitivity.
  Whether the likelihood takes it is what **L28 measures**.

## 3. Verdict on structure

**Not warranted by this information.** Every structural feature the reconciled record exhibits is one DAIS already has:
dynamics-dominated loss, discharge responding to (a linear map of) GMST with no visible lag, SMB as a noisy near-zero
anomaly. The deficit is a **magnitude** (77–92 % of the observed discharge response) and a **noise-scale SMB sign**, both
of which the refit can address with existing parameters. Structural candidates, ranked by what the data say:

1. **An ocean lag or basal-melt state variable** — not asked for: the dynamics anomaly is linear in contemporaneous GMST
   (residual sd 22 Gt/yr, no window structure). Adding one would add an unidentified timescale.
2. **A WAIS / EAIS split** — the loss is WAIS-only, but a single disc reproduces the global total's structure; a split would
   be motivated by PROJECTIONS (marine-based WAIS vs EAIS thresholds), which is the existing open Antarctic question, not
   something IMBIE changes. Cost: a Greenland-basins-scale build (weeks), new priors, no historical constraint on the
   EAIS half.
3. **Weaker precipitation–temperature coupling (κ) or an SMB trend term** — the observed 1979–2017 SMB decline is inside
   its own noise; the 2018–23 event is a 6-yr anomaly the AR(1) term absorbs (target σ 0.09–0.12 cm in those years).
   A parameter (κ's prior), not a structure.
4. **Stronger convexity in discharge (T_oc exponent, depth exponent γ)** — DAIS already has T_oc² × depth^γ; IMBIE's
   window pairs hint at convexity (−89 then −234 Gt/yr per K) but the smoothed regression does not (linear suffices).
   Revisit only if L28 lands with the early record fitted and the modern rate still short.

**The one test that would change this verdict:** if L28 — free to use the discharge-sensitivity parameters — still leaves
the 2011–2017 rate > 2σ below IMBIE (i.e. < ~0.042 cm/yr) while fitting the pre-1979 record, then something binds the
sensitivity from above: the near-flat 1900–1978 Frederikse AIS (a GMST-proportional discharge that is large in 2010
loses too much in 1940) or the paleo geometry prior. The discriminating pair of runs is then (a) L28 with the 1900–1978
AIS σ inflated ×3, (b) L28 with the geometry prior widened — which one moves the modern rate names the binding term.
Not launched; decide on L28's postpred.

## 4. L28 landed (17:17) — the pre-registered test, answered

**The threshold was not met.** L28's 2011–2017 AIS rate is **0.039 cm/yr** (p05–p95 0.032–0.045) against IMBIE's 0.056 —
−2.1σ with both bars — below the 0.042 that §3 set as the line. Cumulative 1979–2023 is fitted (1.22 vs 1.33 ± 0.14,
−0.8σ), the 1979–2002 windows are fitted (±0.2σ), and the model overshoots the 2018–23 SMB pause (+0.9σ, as it should).

**How the likelihood took the new target — not with the physics.** Every Antarctic parameter moved ≤ 0.8 L27-sd and the
sensitivity ones moved DOWN (anto_α 0.38 → 0.29, ice-flow₀ 1.20 → 1.06, antarctic_α 0.34 → 0.30; T_oc,0 up 0.94 → 1.03,
anto_β down 1.01 → 0.84). The move is in the noise model: `sd_ais` 0.0216 → 0.0139 (−4 sd), **`rho_ais` 0.89 → 0.97 with its
spread down to 0.35×, against the 0.99 bound** — the AR(1) term absorbs the acceleration as persistent noise (the same
"ρ bound absorbs a smooth bias" mechanism the IC test found in BRICK 2.0's hindcast, CHANGELOG 09-16d).

**What the fit did instead — a level, not a response** (per-draw split, `diag_ais_flux_split_vs_imbie_L28`): the
discharge anomaly over the acceleration window (1992–2002 → 2011–17) is **−50 Gt/yr, DOWN from L27's −82** (IMBIE −106);
SMB now falls (−24; L27 +17; IMBIE −14); the baseline net loss is larger everywhere (1979–2008 −87 vs L27 −64, IMBIE −78).
The cumulative was bought by losing more ice throughout the century: **1900–1978 loss −43 Gt/yr against the target's −20
(L27 −19)**, the 1935 level 0.31 cm below the target (1.4σ of the target's 0.22; benchmark 1920–49 bias −1.86 sd, cov90 0 %).
Projections follow: **SSP2-4.5 AIS 2100 12.6 → 8.1 cm, 2300 178 → 166; SSP5-8.5 38 → 36, 281 → 272; SSP1-2.6 unchanged;
p95s narrower** — fitting the reconciled record made DAIS LESS sensitive to warming, because the record's higher mean loss
was absorbed as a larger standing imbalance rather than a stronger response.

**Why a linear model cannot do it — the number.** Loss per unit GMST on the new target: 1900–78 **−113 Gt/yr K⁻¹**
(GMST 0.17 K), 1978–91 −98 (0.45 K), 1991–2002 −137, 2002–10 −186, 2010–17 **−198** (1.02 K). The ratio doubles across
0.45 → 1.0 K: local exponents 0.85 before 1978, 1.3–2.3 after. DAIS's discharge speed is (1−α) + α·r², r = (anto_α·GMST +
anto_β − T_f)/(T_oc,0 − T_f); at the fitted values r² = 0.87 + 0.19·GMST + 0.01·GMST² — **linear to 1 %**. A linear
response with the modern slope loses 2× too much in 1900–78; with the early slope it is 2× short in 2010–17. L28 split
the difference and let ρ carry the rest. (§1's "linear in GMST" reading was made on 1984–2018 only; the early century is
what breaks it.)

**Revised verdict.** The reconciled record asks for a discharge response that steepens above ~0.5 K of global warming —
convex or threshold-like — and DAIS's is linear over the historical range. That IS a structural gap, and L28 measures its
cost: −2σ on the modern rate, −1.9σ on the early century, ρ pinned, and projections that move the wrong way. The
candidates, now ordered by what the data say:
1. **A reachable steepening in the discharge** — either a free exponent on the ocean-temperature ratio (nests DAIS at 2; one
   parameter; the smallest change) or an onset temperature for the fast-dynamics term within the observed range (λ above
   T_crit already exists; its paleo prior puts T_crit far above present). ⚠ The second reads as "a marine instability
   already under way" and has large projection consequences; the first is a curvature, not a claim.
2. ~~Ocean lag~~ — makes the response smoother, the opposite of what is needed.
3. ~~WAIS/EAIS split~~ — unchanged: a projection motivation.

**The decisive test before any build (Marcus's call, ~4 h each):** L28 with `rho_ais` capped at 0.90 (a `--rho-max` flag; the
bound is the literal 0.99 at `calibrate_mcmc_ext.jl:1490`). If the physics can carry the shape, the sensitivity parameters
move up and the early-century misfit grows; if they cannot, the fit degrades everywhere — either way it names the binding
term. The 1900–78 σ ×3 and geometry-prior arms are second-order now: the early record is a 1.4σ constraint, not the cap.

## 5. L29 landed (09-22 01:05) — the ρ-cap test, answered: the cap bound and the physics did not move

**Setup.** `run_L29.sh` = L28 + `--rho-max=ais:0.90` (CHANGELOG 09-21i), everything else identical; chains 19:57–00:07 (acceptance
0.238, noise gate PASS, SLR R̂ 1.003, `--accept-slr`); postprocess, postpred, components, stage-2 diagnostics 00:10–01:05.

**The cap was active.** `rho_ais` median **0.885** (p05–p95 0.838–0.899, max < 0.90 in every chain) — the posterior sits pinned
against the new bound as L28's sat against 0.99 (0.966, p05 0.911). It cost the objective **~2–7 log-units** on the second-half
log-post median (L28 819.6–821.7 → L29 812.6–819.6; the Gaussian estimate from L28's ρ sd 0.025 and Δρ 0.08 is ~5).

**And nothing physical moved.** Every Antarctic parameter within **0.1 L28-sd** of L28 (anto_α 0.287 → 0.286, ice-flow₀ 1.064 →
1.063, antarctic_α 0.302 → 0.307, T_oc,0 1.026 → 1.026, amp 1.041 → 1.027) except `ais_c` (80.2 → 74.6, −0.3 sd); `sd_ais`
0.0139 → 0.0138. `diag_refit_precision` puts every L29 per-chain move inside ±0.5 L28-sd, i.e. inside the between-chain noise
of a same-objective refit. The SMB parameters' SPREAD widened (precip_u sd ×1.8, runoff_Ton ×2.2) — the cap loosened them
without moving their centres.

**What the fit did instead — the level again, by a little.** Model-only (per-draw, no noise) AIS p50, L28 → L29 vs IMBIE:
1979–2023 cumulative 1.226 → **1.300 cm** (IMBIE 1.328; z −0.76 → −0.21); 2011–17 rate 0.0391 → **0.0418 cm/yr** (IMBIE 0.0556;
z −2.10 → −1.79 — on the §3 line of 0.042, not over it); 1992–2020 z −1.84 → −1.34; 2018–23 overshoot +0.88 → +1.12σ; early
century essentially unchanged (1900–78 net −50.6 → −46.9 Gt/yr vs target −20; bench 1920–49 bias −1.86 → −1.82 sd). Benchmark
AIS hindcast RMSE 1.53 → 1.45σ, modern-rate z −1.03 → −0.56. **The discharge anomaly over the acceleration window (1992–2002 →
2011–17) is −52.0 Gt/yr — L28's −51.6, IMBIE −106.** The 0.003 cm/yr of modern rate the cap bought came from SMB (anomaly −23 →
−33 Gt/yr; IMBIE −14 — the model now over-steepens SMB, inside SMB's own window-mean se of ~45).

**Projections.** Medians ≈ L28: fixed-climate AIS SSP2-4.5 2100 8.1 → 8.5 cm, 2300 166 → 168; SSP5-8.5 36.1 → 36.6, 272 → 278;
SSP1-2.6 5.2 → 5.7. ⚠ The SSP1-2.6 **p95 fell 30.3 → 17.0 (2100), 50.4 → 30.5 (2300)** with the marginals unmoved — that is the
tipped SHARE crossing 5 %, not a sensitivity change: `diag_ais_tipped_share.jl` (new; per-draw AIS@2100 > 15 cm) gives L27 8.85 %
→ L28 7.60 % → **L29 5.25 %**; p83/p90 unchanged (6.5/7.2 → 6.9/7.5). SSP2-4.5's share 41.6 → 40.4 %. A 2.3-point move on 2000
draws is ~4 binomial se — real, small, and a step function on the p95 ([[ais_amp_leverage_is_a_threshold]]).

**Reading against the pre-registered pair.** Neither branch as written: the sensitivity parameters did NOT rise (branch a), and
the fit did NOT degrade everywhere (branch b) — it improved slightly on every IMBIE window while the noise term paid the cap.
What that says is sharper than either: **forbidding ρ from pricing the acceleration made the residual more expensive, and DAIS
answered with a LEVEL shift (SMB, `ais_c`), not a SHAPE, because there is no direction in its parameter space that produces the
acceleration** — the acceleration-window discharge anomaly is byte-for-byte where L28 left it. The binding term is the linear
discharge response, not the noise model. §4's verdict stands and is now measured from two sides: L28 (ρ free) absorbed the
shape as persistence; L29 (ρ capped) could not absorb it and could not fit it either.

**What follows.** (1) L29 is a diagnostic arm, NOT a candidate posterior — a truncated noise prior is not a modelling choice one
would ship, and it moves nothing the paper reports. (2) The steepening build is now the live question (§4's candidate 1: a free
exponent on the ocean-temperature ratio, nesting DAIS at 2; Marcus's call — a curvature, not a claim). (3) The 1900–78 σ ×3 and
geometry-prior arms remain second-order: the early record barely moved under the cap. (4) Which posterior the paper ships is
unchanged by L29: L27 (old target, consistent draft) vs L28 (new target, level not shape) vs post-structure.

## 6. The steepening build, scoped BEFORE building (09-22 morning): a power on the ocean-temperature ratio is INERT on the historical range, and the record's shape is a KINK, not a curvature

**The question.** §4 candidate 1: replace the literal `^2` in DAIS's discharge speed
(`antarctic_icesheet_magdep_component.jl:210`: speed = iceflow₀·[(1−α) + α·r²]·depth^γ/…, with
r = (T_oc − T_f)/(T_oc,0 − T_f) and T_oc = anto_α·GMST + anto_β from ANTO, whose logistic term is 1 + e^(−9) ≈ 1 at every
posterior draw) by a sampled exponent n, nesting DAIS at n = 2, prior on [1, 4]. Would the refit be able to meet the
pre-registered success line (2011–17 rate within 1σ of 0.056 without the early century worsening past −1.8σ)? Answered
by algebra before spending 4 h.

**What the exponent can do is fixed by r's RANGE, and r barely moves.** At the L29 posterior (anto_α 0.286, anto_β 0.83,
T_oc,0 1.026, T_f −1.8): r = 0.931 + 0.1016·GMST, so r(0.45 K) = 0.976 and r(1.0 K) = 1.032 — a 5.7 % span across the
window the record doubles over. The SHAPE of the discharge anomaly α·[rⁿ − r(0)ⁿ] in GMST is therefore near-linear for
any modest n whatever α does (α and iceflow₀ scale the magnitude only). Measured on the record's own statistic
(loss per unit GMST, i.e. the secant slope; IMBIE 0.45 → 1.02 K = **2.02×**, 0.17 → 0.45 K = **0.87×**):

| form | 0.45 → 1.02 K secant ratio | 0.17 → 0.45 K | speed factor (1−α)+α·rⁿ at 2 K / 4 K (α 0.307; stock 1.09 / 1.24) |
|---|---|---|---|
| n = 2 (stock) | 1.03 | 1.02 | 1.09 / 1.24 |
| n = 4 (prior top) | 1.10 | 1.05 | 1.20 / 1.67 |
| n = 8 | 1.25 | 1.11 | 1.53 / 3.80 |
| **n = 20.4 (the doubling)** | **2.02** | **1.38** | **4.63 / 113** |
| ANTO at its prior CORNER (anto_α 1, anto_β 0), n = 5.6 | 2.02 | 1.43 | 2.31 / 18.2 |

So: **(i) a prior on [1, 4] has no power** — the best it can produce is 1.10× against a required 2.02×; the refit would
return "n ≈ 4 against the bound, physics unmoved, ρ back on ITS bound" and the success line would be unreachable by
construction (the L29 no-power-mutation lesson, `mutation_test_gates`, applied to a prior). **(ii) The n that does
produce the doubling (~20 at the fitted ANTO; ~6 only if ANTO runs to the corner of its prior, T_oc = GMST − 1.8 °C)
is not "a curvature, not a claim"** — it is e^(n·0.109·GMST), an exponential in GMST with e-folding ~0.45 K, whose
extrapolation to 2–4 K multiplies the discharge speed by 5–100× (the mass-conservation floor and the disintegration
cap would bind; projections would be the FORM, exactly as the ssp585 2300 band is the λ prior — `ais_spread_is_lambda_prior`).
**(iii) Even at the doubling, the shape is wrong on the early side**: any power law that doubles 0.45 → 1.02 K also
raises 0.17 → 0.45 K by ~1.4×, where IMBIE+Frederikse give 0.87× — the record is FLAT in loss-per-K to ~0.5 K and then
doubles. That is a kink, an onset near 0.5 K of global warming, not a smooth convexity.

⚠ The early-century leg of that shape rests on the 1900–78 target (−20 Gt/yr over 0.17 K, a ratio on a small base;
the 1935 level's σ is 0.22 cm and the constraint is 1.4σ). Its mean is what makes the record flat-then-steep; its width
is what §3's "1900–78 σ ×3" arm would test. Even discarding it entirely, (i) and (ii) stand on 0.45 → 1.02 K alone.

**Where this leaves the candidates.**
1. ~~Free exponent on r, prior [1, 4]~~ — dead on the algebra. Not worth 4 h.
2. **Free exponent with a prior that reaches ~20** (log-uniform on [1, 30], say) — CAN fit the modern doubling, but
   (a) mis-shapes the early century by +1.4×, (b) puts the projection tail in the exponent's prior, (c) trades off
   against anto_α/anto_β (n ≈ 6 at the ANTO corner) so it is not one axis. A steepening THIS sharp is a threshold by
   another name.
3. **An onset inside the observed range** — the form the record's shape actually asks for, and the machinery already
   exists: the magdep component's fast-dynamics term, −λ·g·const with g = (excess/ref)^n_fd above T_crit (n_fd = 0 is
   the stock binary; n_fd = 1 is a linear ramp above onset). L27+ holds λ and T_crit at their paleo medians
   (`--cut-fastdyn`; T_crit's paleo prior fires at +2.84 °C T_ant [2.25, 3.55] — `ais_lambda_rests_on_lig`), i.e.
   far above the observed ~1.1 K of T_ant anomaly. The build would be: sample T_crit under a prior that ADMITS the
   observed range (a second component against the paleo prior, or a replacement of it), λ under its paleo prior,
   n_fd fixed at 1 (a ramp) — and the modern rate then identifies (T_crit, λ) jointly. ⚠ This is the reading Marcus
   flagged: "a marine instability under way since ~2000", with the fast-dynamics term LIVE in every projection from
   the start year. Its projection consequence is the whole point and is not a side effect.
4. The 1900–78 σ ×3 arm — now a TEST of the kink's early leg, not a second-order option: if the early loss/K is really
   unconstrained, a smooth steepening needs to fit 0.45 → 1.02 K only; but per (i)–(ii) that still needs n ≈ 20.

**A cheap test before any refit (minutes, no sampler, no model change for candidate 3).** Fixed-parameter forward runs
on the L29 posterior medians, sweeping (T_crit, λ) with n_fd = 1 (and, for candidate 2, n on a modified component with
default 2), reporting: 2011–17 rate, 1992–2002 rate, 1900–78 net, the acceleration-window discharge anomaly, and AIS
at 2100/2300 on SSP1-2.6 / 2-4.5 / 5-8.5. It answers "is 0.056 reachable at all, and at what projection cost" before a
4-h chain is spent, and would also give the start row and the prior range a refit needs. `scope_ais_fastdyn_shape.jl`
already propagates the magdep term over a posterior and gates [INERT]/[AFFINE]; the sweep is that script with T_crit
moved into the observed range and the hindcast windows added.

**Recommendation.** Do not build candidate 1 as scoped. Run the fixed-parameter sweep (candidate 3's parameters exist;
candidate 2 needs the one-line exponent parameter with default 2, gate-checked). Then decide between 2 and 3 on what
the sweep shows — and on whether the paper wants to make the onset claim at all, which is a scientific ruling, not a
fit statistic. Nothing launched; nothing in the component changed.

## 7. The onset sweep RAN (09-22 morning, `scope_ais_onset_sweep.jl`, 295 L29 draws, fixed parameters, ~90 s): a linear ramp above an onset at +0.6–0.75 K global reproduces every pre-pause IMBIE window at once

**What ran.** The magdep fast-dynamics term as a LINEAR RAMP — rate = −s·max(T_ant − T_crit, 0), n_fd = 1, ref 1 K, s in
m SLE yr⁻¹ K⁻¹ — with the onset swept in GLOBAL warming and mapped per draw through its own amp (T_crit = TANT0 + amp·G_on).
Grid G_on ∈ {0.30, 0.45, 0.60, 0.75} K (the ssp245harm driver crosses these in 1961 / 1982 / 1997 / 2001) × s ∈ {0.75, 1.5,
3, 6, 12}·10⁻⁴. The ramp REPLACES the paleo (λ, T_crit) pair (the component holds one term); `stock` keeps the pair, `none`
zeroes it. Every other parameter at its L29 draw value: no refit, so the ramp sits ON TOP of L29's fitted level. Hindcast
1850–2026 on ssp245harm as the calibrator sees it; projections on fixed FaIR-mean SSP1-2.6 / 2-4.5 / 5-8.5 to 2300.
Receipts `outputs/scope_ais_onset_sweep_{hindcast,hindcast_draws,proj}_L29.csv`, log `outputs/log_scope_ais_onset_sweep_L29.txt`.
`stock` reproduces L29 (2011–17 0.0411 vs the posterior's 0.0418; dyn-accel −48 vs −52; cum 1.30).

**Hindcast** (p50 window rate z-scores against IMBIE's own window σ; Σz² over the four pre-pause windows; dyn accel =
acceleration-window dynamics anomaly, Gt/yr, IMBIE −106):

| arm | 79–91 | 92–02 | 03–10 | 11–17 | 18–23 (pause) | Σz² (4) | cum 79–23 z | dyn accel |
|---|---|---|---|---|---|---|---|---|
| stock (= L29) | +0.20 | +0.02 | −0.96 | −1.99 | +1.13 | 4.9 | −0.23 | −48 |
| on 0.45 K, s 3e-4 | +0.34 | +0.67 | +0.66 | +0.09 | +2.45 | 1.0 | +2.27 | −98 |
| on 0.60 K, s 3e-4 | +0.20 | +0.22 | +0.04 | −0.47 | +2.18 | **0.3** | +1.44 | −91 |
| **on 0.75 K, s 6e-4** | +0.20 | +0.04 | −0.17 | −0.08 | +2.68 | **0.1** | +1.74 | **−109** |
| on 0.75 K, s 1.2e-3 | +0.20 | +0.06 | +0.63 | +1.83 | +4.26 | 3.8 | +3.76 | −170 |

- **Reachable, and with the right shape.** An onset at +0.60–0.75 K global with s = 3–6·10⁻⁴ m yr⁻¹ K⁻¹ puts all four
  pre-pause windows inside ±0.5σ simultaneously — 1979–91 and 1992–2002 untouched (the flat leg), 2003–10 and 2011–17 lifted
  onto IMBIE — and the acceleration-window dynamics anomaly at −109 against IMBIE's −106. Earlier onsets (0.30–0.45 K) spoil
  the flat leg (92–02 to +0.7σ) before they reach the modern rate: the record's kink really is at ~0.6–0.75 K, i.e. ~2000.
- **The success line is met on the modern windows without touching the early century** (1900–78 net −48 Gt/yr in every arm —
  the ramp is zero there by construction).
- **What it costs, as a fixed-parameter sweep:** the 1979–2023 cumulative overshoots (+1.4 to +1.7σ) because the ramp is added
  on top of L29's level; a refit would re-buy the level through SMB / `ais_c` as L28 and L29 did (expected, NOT verified here).
  The 2018–23 pause worsens (+1.1 → +2.2–2.7σ; σ 0.015 cm/yr): a monotone ramp cannot pause, and the pause is an SMB event
  the AR(1) term already carries.

**Projections (fixed climate, p50 cm; `stock` = the paleo binary at +2.8 °C T_ant; `none` = no fast-dynamics term):**

| arm | 126@2100 | 245@2100 | 585@2100 | 126@2300 | 245@2300 | 585@2300 |
|---|---|---|---|---|---|---|
| stock (= L29) | 5.7 | 8.2 | 36.9 | 17.7 | 166.6 | 278.9 |
| none | 5.6 | 6.4 | 8.2 | 17.6 | 27.8 | 79.1 |
| on 0.60 K, s 3e-4 | 8.3 | 9.7 | 12.7 | 26.4 | 43.9 | 113.1 |
| on 0.75 K, s 6e-4 | 10.3 | 12.3 | 16.4 | 33.0 | 58.2 | 146.1 |

- **The ramp itself is moderate**: on 0.75 / 6e-4 adds +4.7 / +5.9 / +8.2 cm at 2100 and +15 / +30 / +67 at 2300 over `none`
  (SSP1-2.6 / 2-4.5 / 5-8.5). Its slope in global terms is s·amp ≈ 6·10⁻⁴ m yr⁻¹ per K above 0.75 K — 0.06 cm/yr per K —
  against the paleo binary's λ ≈ 1 cm/yr once tipped. A linear ramp identified on 0.75–1.05 K extrapolates linearly, which is
  the mildest possible extrapolation; it is still an extrapolation.
- **The large moves at high forcing are the REMOVAL of the paleo term, not the ramp**: SSP2-4.5 2300 167 → 58 and SSP5-8.5
  2300 279 → 146 are `stock` → `none` (−139, −200) partly refilled by the ramp (+30, +67). The λ prior IS that band
  (`ais_spread_is_lambda_prior`); replacing it with an observationally identified term is the whole change.
  ⚠ **Whether the two terms COEXIST is a methodological choice the sweep did not make**: the component holds one threshold
  term. Kept alongside (a ramp in range PLUS the paleo binary at +2.8 °C), SSP5-8.5 2300 would sit near stock + ramp ≈ 350 cm
  (additive estimate, not run); replaced, 146. Low-forcing cells go UP either way (SSP1-2.6 2100 5.7 → 10.3, 2300 18 → 33).
- No draw hit the mass-conservation floor in any arm (floor years 0.0 everywhere).

**What the sweep does NOT establish.** It is one term added at fixed parameters: (i) whether a refit keeps the shape once the
level is re-bought (the L28/L29 lesson is that the likelihood buys level first — but here the ramp gives it a shape direction it
did not have); (ii) the (G_on, s) posterior width — the grid says the identifiable region is narrow in G_on (0.6–0.75) and about
a factor 2 in s at fixed G_on, with the two trading off (0.60/3e-4 ≈ 0.75/6e-4); (iii) any noise-model interaction
(ρ_ais would presumably fall off its bound once the shape is carried by physics — a prediction the refit can test).

**Recommendation for the refit, if Marcus makes the onset claim.** L30 = L28's recipe + the magdep component with n_fd = 1,
ref 1 K, sampling G_on (prior uniform on [0.3, 1.0] K global; T_crit derived per draw through amp — the identified coordinate)
and log s (log-uniform on [0.5, 20]·10⁻⁴ m yr⁻¹ K⁻¹), the paleo binary term DROPPED (the replacement form) as the primary
arm; start at (0.75, 6e-4). Identity gate: default n_fd = 0 with the paleo pair must reproduce the gate chain byte-for-byte.
Success line (pre-registered): 2011–17 within 1σ AND 1992–2002 within 1σ AND the cumulative within 1σ AND ρ_ais off its
bound (< 0.95) — the level re-bought and the shape carried by the ramp, not the noise. ~4 h Mac. The coexistence question
(keep the paleo term too) would be a second arm, L30b, needing a two-term component.

**§6/§7 erratum (09-22, on Marcus's question about the evidence).** §6's "kink near 0.5 K" over-read the secant ratios: the
0.17 → 0.45 K leg is the Frederikse-based 1900–78 NET loss and the 0.45 → 1.02 K leg is IMBIE's DYNAMICS anomaly — two
products and two quantities. On IMBIE 1979–2023 alone, §1's regression stands: the dynamics anomaly is LINEAR in GMST
(−232 Gt/yr K⁻¹, residual sd 22, no window residual above 14, zero-crossing near +0.15 K) — there is no kink at ~2000 in
the record itself. What §7's sweep located at 0.60–0.75 K is where DAIS's OWN fixed linear response starts to fall short of
that line (L29's dynamics anomaly is −48 of IMBIE's −107 by 2011–17), not a feature of the observations. The sweep's
finding is therefore "DAIS + a ramp from ~0.7 K matches the record's dynamics through 2018–23 (−167 vs IMBIE's −177 rel
1979–2008)"; an equally consistent reading is a steeper LINE from ~0.15 K, which the L28 refit did not take because the
1900–78 level forbids it. §6's algebra (the exponent is inert; n ≈ 20) is unaffected.

## 8. The evidence behind the 09-22 ruling, and what L30 is (and is not) claiming

**Marcus's three questions, answered before the build.**

1. **How strong is the evidence for increased discharge instability since 2000?** Strong for a steady, warming-tracking
   ACCELERATION; nil for an INSTABILITY in the self-sustaining sense; weak for a STEP at 2000. IMBIE 2026 (§1): the dynamics
   anomaly is WAIS-only (−34 → −192 Gt/yr, 1979–91 → 2018–23), 84 % of the loss, and LINEAR in GMST on 11-yr means
   (−232 Gt/yr K⁻¹, residual sd 22, no window residual above 14) — a forced-response signature, not a decoupled one.
   ⚠ **§6's "kink at ~0.5 K" was a product mix** (Frederikse NET loss on the early leg, IMBIE DYNAMICS on the late one); see the
   §6/§7 erratum. The "2000" in §7 is where DAIS's own fixed linear response starts to fall short, not a date in the record.
   External lines (Mouginot 2014 Amundsen discharge +77 %; Rignot 2019 PNAS; Rignot 2014 grounding-line retreat; Joughin 2014
   on Thwaites — a MODEL statement on a centuries timescale; against: Jenkins 2018 / Holland 2019 on decadal wind-driven
   Amundsen forcing) are recalled, NOT verified here — cite from the papers, not from this line.
2. **Has AIS stabilised recently?** Net loss halved (−200 → −104 Gt/yr) and the record attributes the whole slowdown to SMB
   (+144 Gt/yr, record EAIS snowfall) while dynamics kept accelerating (−179 → −249). NBC's coverage of Otosaka et al. quotes
   the authors to the same effect — weather, not trend, with the acceleration resumed after 2023. The sweep's arms reproduce
   exactly that: on 0.75 K / 6e-4 tracks IMBIE's 2018–23 DYNAMICS (−167 vs −177 rel 1979–2008) and its +2.7σ there is the
   missing SMB pulse. A 6-yr SMB event at ~3σ of the interannual sd is the AR(1) term's job, not the physics'.
3. **Replace or coexist?** COEXIST, ruled by Marcus. Replace buys one observationally identified term but discards the LIG
   constraint above 1.2 K and moves the paper's tail (SSP5-8.5 2300 279 → 146) on the strength of REMOVING a prior; coexist is
   nested (slope 0 = stock, bit for bit), keeps the paleo constraint, changes nothing historically, and its double-count is
   bounded (the ramp is ~12 % of λ at the paleo threshold, ~50 % at 8 K excess). A REPLACE arm stays available as L30b.

**What L30 claims.** That DAIS's discharge response to warming is steeper than one linear map allows, and that an additional
response above an onset is a form the data can identify. It does NOT claim a marine ice-sheet instability is under way: the
term is named "the additional discharge response" everywhere in the code and the outputs for that reason. If the refit puts the
onset firmly inside the observed range with a tight slope, that is a fitted curvature; calling it an instability would be a
mechanism claim the fit cannot make.
