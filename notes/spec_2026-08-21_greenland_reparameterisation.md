# SPEC — the Greenland block reparameterisation

**Status: DRAFT. Nothing implemented, no chain run.** Written 2026-08-21 at Marcus's
request. Read §1 before deciding whether to build it: the objective in handoff
20e §4 item 2 is not the one the data support.

---

## 1. THE OBJECTIVE IS NOT CONVERGENCE — measured, not assumed

Handoff 20e §4 calls this "the cheapest real win on convergence", against L14's
standing caveat that **20 parameter marginals are unconverged ⇒ projections only**.

Measured on the four L14 production chains (2 M each, post-warm-up half, split-free
R-hat over 60 sampled columns):

| threshold | count |
|---|---|
| R-hat > 1.01 | 21 (= the "20 marginals" + `accept_rate`) |
| R-hat > 1.05 | **9** |
| R-hat > 1.10 | 5 |

Worst offenders, in order: `ais_iceflow0` **1.777**, `antarctic_alpha` **1.602**,
`ais_slope` **1.478**, `rho_ais` 1.156, `anto_beta` 1.093, `ais_runoff_Ton` 1.080,
`ais_ocean_temperature0` 1.061, `ais_mu` 1.060, `rho_gsic` 1.045.

**The whole Greenland block:**

| param | R-hat |
|---|---|
| gis_c0 | 1.031 |
| gis_f | 1.028 |
| gis_slow_ell | 1.027 |
| gis_c1 | 1.019 |
| gis_beta_f | 1.005 |
| gis_alpha_f | 1.002 |
| gis_slow_w | 1.001 |
| gis_amp | 1.001 |
| gis_s_high | 1.001 |

Greenland's worst marginal ranks **10th overall at 1.031**, and NO Greenland parameter
exceeds 1.05. **A Greenland reparameterisation will not lift L14 out of
"projections only."** That status is gated by the AIS, which handoff 20e §3 closed:
the named fix is an observational grounding-line discharge constraint, not a better
sampler, and Marcus ruled it out of scope as decision D5 (2026-08-14).

**What it WOULD buy: sampling efficiency.** The block's correlation-matrix condition
number is 67 with a single direction carrying 40% of standardised variance, so the
sampler spends most proposals fighting a ridge. That is ESS per iteration — a cheaper
chain for the same answer — and it is a real but different prize. Build it for that
reason or not at all; do not build it expecting the caveat to lift.

---

## 2. WHAT THE RIDGE ACTUALLY IS

Two DIFFERENT directions appear in `outputs/diag_block_ridge_L14.md`, and 20e §4
quotes only the first. They must not be conflated.

**(a) Loosest within-chain direction — 40% of variance, the conditioning problem.**
Loadings `gis_slow_ell -0.49, gis_f -0.47, gis_c1 +0.46, gis_c0 +0.44`.
Chain-to-chain alignment |cos| = 0.959 / 0.988 / 0.976 — all four chains see the SAME
direction, which is the precondition a reparameterisation needs and the reason this is
well posed (unlike the AIS, where the four chains disagree at |cos| 0.583/0.625/0.857).

**(b) Worst-MIXING direction — 84% of all between-chain variance.**
Loadings `gis_c0 -0.79, gis_c1 -0.49, gis_slow_ell -0.22, gis_alpha_f -0.20`.
More concentrated on (c0, c1).

They overlap on {c0, c1, slow_ell} but are not the same axis. **Target (a)** — it is the
efficiency prize, it is what the four-chain alignment certifies, and (b) is small in
absolute terms here anyway given the block's R-hats.

### The measured correlation structure (4 L14 chains, post-warm-up)

|  | c1 | c0 | f | alpha_f | beta_f | slow_ell |
|---|---|---|---|---|---|---|
| **c1** | 1.00 | +0.42 | -0.62 | -0.32 | +0.34 | **-0.73** |
| **c0** | +0.42 | 1.00 | -0.64 | +0.09 | +0.39 | **-0.75** |
| **f** | -0.62 | -0.64 | 1.00 | -0.21 | -0.36 | **+0.71** |
| **slow_ell** | -0.73 | -0.75 | +0.71 | -0.00 | -0.27 | 1.00 |

**`gis_slow_ell` is the hub**, at |r| ~ 0.71-0.75 against all three of c0, c1, f.

### THE TRAP THIS KILLS

The obvious move on a `L_eq = c1*T + c0` pair is to CENTRE the predictor —
`L_eq = c1*(T - Tbar) + L_bar` — the standard slope/intercept decorrelation, and
idiomatic here since `GIS_ELL_MU`/`GIS_W_MU` already do exactly that at `GIS_TBAR`.

**It is the wrong fix and would waste a chain.** `r(c1, c0) = +0.42` only, and POSITIVE.
Slope and intercept are not the tight pair; each is tight against `slow_ell`. Centring
addresses a correlation that is not the problem.

### What the direction MEANS

Signs on (a): `c1 +, c0 +, f -, slow_ell -`. A **larger** committed loss, released
**more slowly**, through a **smaller** fast fraction, reproduces the same realised loss
over the observation window. This is the commitment-vs-rate degeneracy — over a finite
window you cannot separate how much is committed from how fast it is discharged. It is
the same object as memories `ladrillo_gis_commitment` and `ladrillo_leq_ridge_ceiling`
(the ridge ceiling that capped the 2300 separation), seen in parameter space.

---

## 3. TWO CANDIDATE TRANSFORMS

### Option A — fixed orthogonal rotation of the z-scored block (RECOMMENDED)

Take the unit loading vector of direction (a), `u = (c1 +0.46, c0 +0.44, f -0.47,
slow_ell -0.49)` over the z-scored coordinates, complete it to an orthonormal basis of
that 4-space (Gram-Schmidt / Householder), and sample in the rotated coordinates. The
first new coordinate IS the ridge; the other three are its complement.

* **Exactly invertible, closed form, no model solve.** Cheap and safe.
* `u` is FROZEN as a named constant from the L14 diagnostic — it must NOT be re-estimated
  per run, or the parameterisation moves with the posterior and nothing is comparable.
  State the vintage it came from in the constant's name, e.g. `GIS_ROT_U_L14`.
* Cost: the new coordinates are not physically interpretable, so every prior on
  c1/c0/f/ell must be re-expressed. With `gis_slow_w` flat and `gis_ell` at sd 1.0 this
  is tractable but must be done explicitly, not implicitly.
* Risk: a rotation is only as good as `u`. If the true ridge curves, a linear rotation
  straightens it only locally.

### Option B — make the constrained quantity an explicit coordinate

Replace `gis_c0` with `gis_Lhat`, the model's realised GIS loss over a reference window
(the G1 window 2003-2018, or the full 1900-2025 calibration window), and solve for `c0`
given (c1, f, ell, w, Lhat).

* More interpretable: the well-constrained direction becomes a coordinate with a prior
  that can be set from data.
* **Requires an implicit inversion**, which is a known trap here — memory
  `implicit_inversion_fixpoint`: iterate to a FIXED POINT and assert `f(x) = x`. The
  one-shot answer there was wrong by 11x the largest error bar it was defending against.
* Cost per likelihood evaluation rises by the solve. On a 2 M-iteration chain that is
  not free.

**Recommendation: Option A.** Option B is more elegant and more dangerous; take it only
if A underdelivers, and only with the fixed-point assertion in place from the first commit.

---

## 4. GATES — build these BEFORE any chain

Same discipline as `--gis-basins2` (handoff 20c Run A step 2).

1. **BIT-IDENTITY.** At the identity rotation (`u` replaced by the canonical basis) the
   sampler must reproduce the un-reparameterised model EXACTLY — same log-posterior for
   the same physical parameter vector, to floating point. This is the analogue of
   `greenland_3basin` at `k_mid = 0` nesting whole-sheet A+B.
2. **ROUND-TRIP.** `to_rotated(from_rotated(x)) == x` and its inverse, to ~1e-12, over
   random draws spanning the bounds. A rotation that is not exactly invertible silently
   biases the posterior.
3. **PRIOR-EQUIVALENCE.** The induced prior in rotated coordinates must integrate to the
   same measure as the original. If the priors are Gaussian in the original coordinates
   this is exact under an orthogonal map; assert it numerically rather than trusting it,
   because the BOUNDS are not rotation-invariant (`gis_f` in [0.02, 0.98], `gis_slow_w`
   in [0,1]) and a box does NOT map to a box. **This is the sharpest edge in the whole
   design** — decide explicitly whether bounds are enforced in original coordinates
   (rejecting proposals) or the box is replaced.
4. **MUTATION-TEST EVERY GATE** (memory `mutation_test_gates`): perturb `u` by one
   element and confirm gate 1 FAILS; break the inverse and confirm gate 2 FAILS. A gate
   that has only ever passed proves nothing.
5. **`--gis-check` still 0.0000. DO NOT WIDEN ITS TOLERANCE.**
6. **Layout change ⇒ `embed_cov!` BY NAME**, and extend the seed gate to the new
   coordinate names. This would be the FOURTH layout change in this arc and BOTH earlier
   ones bit (the ADCOV size collision → acceptance exactly 0.0; the `ais_c`/`ais_slope`
   four-row shift → a parameter frozen from iteration 1 while acceptance looked healthy).

## 5. HOW TO KNOW IT WORKED

Pre-register the success metric BEFORE running, or the result is unfalsifiable:

* **Primary: ESS per iteration on the Greenland block**, versus L14's values. That is the
  claimed prize.
* **Secondary: block condition number** recomputed by `python/diag_block_ridge.py --tag=<new>`;
  67 should fall substantially. If it does not, the rotation did not capture the ridge.
* **Guard: SLR@2100 must not move materially.** This is a reparameterisation, not a new
  model. A large shift means a prior was silently changed by the map — most likely
  through the bounds (gate 3).
* **NOT a metric: the Greenland R-hats.** They are already 1.00-1.03; there is no room
  to improve and any movement is noise.

## 6. RUN COST, if it proceeds

Mirrors Run A: re-tune (~1.4 h) then 4 x 2 M production (~5.5 h), seeded from
`adapted_cov_L14_seed2026.csv` **by name** (it is a NAMED file — do not use the
quarantined nameless aggregate). Then postprocess → `diag_slr_convergence_by_chain` →
postprocess again with `--accept-slr`, in that order.
