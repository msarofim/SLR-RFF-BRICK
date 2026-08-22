# Handoff — the Greenland defect is the LINEAR commitment law; the deliverable is a FLUX, not a (V, tau); and two cheap checks come before any model change

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Written 2026-08-22, to be picked up cold.

**Supersedes** `handoff_2026-08-21e_retarget_done_shape_next.md` for its §3 and §4
item 3 — the reservoir is no longer "clears offline, wire it next"; what it clears is
now understood, and the cell it selected is the wrong point on the right ray.
**Its §1, §2 and §5 (the re-target, the `gis_targets` mechanics, the file list) are
UNCHANGED and still the reference.**

**Read with:** `notes/scoping_2026-08-22_greenland_shape_stepback.md` — the full
evidence, 23 numbered sections, with every correction attached to the claim it
corrects rather than silently patched. **This handoff is the executive layer; that
note is the record.**

Commits this handoff closes over: `efcfe5d` `ba58113` `37d6132` `3bea7b4` + the
script promotion below.

---

## 0. THE ONE-PARAGRAPH VERSION

Set every rate to infinity and let the model fully equilibrate: the **linear
commitment law `L_eq = c1*T + c0` falls 1.93x and 2.41x short of the two warm arms'
own 2300 medians, and is at-or-above all three cool ones.** That one table kills the
entire rate side — `gamma`, a longer `tau`, any re-shaped `r(T)` — without a scan, and
it dissolves the `k = 2-3` vs `k <= 1.0` tension as one law being asked to be steep at
6 K and flat at 2 K. **The fix must add commitment ABOVE ~3 K and nothing below.**
Scoring the **RATE** at 2250-2300 (which no tap or reservoir cell has ever been scored
on) separates the candidates: the shipped offline optimum `V=1/tau=800` gets the 2300
LEVEL right and the rate **2.2x wrong**, so it would be wrong again by 2400;
`V=6/tau=2200` gets **both** (26.0 vs PROTECT's 26.5 cm/century, our ssp585 at 99.1 cm
against the matched p50 of 98.5), at exactly zero cost to 2100 and to the cool
scenarios. **But `V` and `tau` are NOT identified and never will be** — only
`psi = V/tau ~ 0.27 cm/yr` is. **⇒ The deliverable is a sustained flux opening above
~4.7 K, with (V, tau) chosen by prior on the equilibrium literature.**

---

## 1. WHAT IS ESTABLISHED

### 1.1 The arithmetic death certificate (`python/diag_gis_stepback_ceiling.py`)

| arm | GSAT@2300 | φ=1 CEILING | PROTECT median | shortfall |
|---|---|---|---|---|
| SSP5-8.5 x2300 | 13.63 K | 96.8 cm | 233.6 cm | **2.41×** |
| SSP5-8.5 r2300 | 5.61 K | 37.1 cm | 71.5 cm | **1.93×** |
| SSP2-4.5 r2300 | 2.98 K | 18.3 cm | 15.4 cm | 0.84× |
| SSP1-2.6 x2300 | 2.44 K | 12.9 cm | 9.8 cm | 0.76× |
| SSP1-2.6 r2300 | 1.95 K | 11.1 cm | 11.1 cm | 1.00× |

**Robust to the amplification question in the direction that matters** — a LOWER
melt-relevant amp at high T shrinks the driver, shrinks the ceiling, and makes the
shortfall WORSE (§4.2).

### 1.2 The rate criterion, and what it selects (`python/diag_gis_stepback_rate_crit.py`)

Rate at 2250-2300, cm/century, per arm at matched forcing:

| cell | 8.5 r2300 | 8.5 x2300 | our ssp585 @2300 | Δ2100 | ssp245 dev |
|---|---|---|---|---|---|
| **PROTECT (target)** | **26.5** | **139.7** | p50 98.5 | — | — |
| base | 2.9 | 16.6 | 49.9 | 0 | 0 |
| **A** V=1.0, onset 4.69, τ=800 — *the shipped offline optimum* | 12.0 | 26.4 | 70.9 | +0.0000 | +0.000 |
| **B** V=6.0, onset 4.69, τ=2200 | **26.0** | 41.6 | **99.1** | +0.0000 | +0.000 |
| B' V=3.0, onset 4.69, τ=1100 | 24.1 | 39.5 | 97.1 | +0.0000 | +0.000 |

### 1.3 The deliverable is `psi = V/tau`, and B vs B' PROVES it

For any component with `tau >>` the window, `phi ~ s/tau`, so **both the level and the
rate depend only on `psi = V/tau`**; the separating curvature is `O((s/tau)^2)`, i.e. a
**3× change in `tau` at matched flux moves the 200-yr level 6.3 %** — against the
5.61 K arm's own p05-p95 factor of **3.6**.

**Read the table with that.** A has `psi = 0.125 cm/yr`; **B and B' both have
`psi = 0.273`**. The A→B rate ratio 26.0/12.0 = 2.2 is exactly the flux ratio, and B vs
B' — a 2× change in `tau` at matched flux — differ by **7.9 %**, the predicted curvature
size. **The rate criterion identifies the flux. It does not identify `V` or `tau`.**

> **⇒ QUOTE IT AS: an added sustained flux `psi ~ 0.27 cm/yr` opening above ~4.7 K.**
> `V = 6 m / tau = 2200 yr` is a PRIOR choosing a point on an unidentified ray — chosen
> because the equilibrium literature says enter it near `V ~ V0` on a 2-3 kyr clock
> (Van Breedam 2020 ~2 kyr at high forcing; Greve & Chambers 2022 1.79 ± 0.80 m by 3000
> ⇒ τ ≈ 3300 yr). Same discipline as `greenland_3basin_component.jl:111`,
> *"IT IS A PRIOR SPECIFICATION, NOT A FIT."*

### 1.4 The 86/216 was the correct answer

Not a fitting failure, not a grid problem: it is the `V/tau` degeneracy, and a bigger
scan cannot resolve it. Two contributing reasons it *looked* worse than it is: a
**coordinate** grid samples a **curved** ridge as a blob (profile along the sloppy
eigendirections instead), and the scorecard asked a **feasibility** question ("does the
cell clear every criterion?") — feasibility sets are always fat. The evidence separating
the best long-τ from the best short-τ cell was a likelihood ratio of **1.016**, which is
nothing.

---

## 2. WHAT IS DEAD, AND WHY (do not re-propose)

| candidate | verdict | reason |
|---|---|---|
| any rate-side fix — `gamma`, longer `tau`, re-shaped `r(T)` | **DEAD** | §1.1: the φ=1 ceiling is below the warm arms |
| re-signing `r(T)` so the rate FALLS with T | **DEAD, and it would contradict the literature** | drainage gets FASTER when warmer: Levermann & Winkelmann 2016, 10 % of GrIS in ~3500 yr at 0.5 °C above threshold vs ~500 yr at 5 °C; Van Breedam 2020, ~2 kyr vs ~10 kyr. The measured `tau_eff` rise is **COMPOSITION** (slow reservoirs dominate the budget at high T), which is what `tau_eff = L_eq'(T)/c` already says |
| the ridge scale `k` | **DEAD** | scales the cool commitment equally; the cool arms are already AT their ceiling |
| continuum ladder of threshold reservoirs | **DEAD as a source of identification** | (a) with a common `tau` it is EXACTLY one reservoir with a shaped ramp (max diff **3.3e-16** over 451 yr, N=25) — so its `v(theta)` half IS `RAMP_W_K`, pinned at 1.0 in `scope_gis_reservoir_offline.py:75` and **never scanned**; (b) `a(theta)` carries `1/tau`, so `tau_eff(0) → 2*tau_min` **independent of `tau_max`** — you cannot see a 2700-yr bin in a 200-yr window; a 5-param ladder fit drove its `tau(theta)` exponent to 0.5 and abandoned the mechanism |
| stretched exponential, Mittag-Leffler / fractional, power-law memory kernel, Prony | **REFUTED by an exact bound** | for ANY completely monotone response `d ln tau_eff / d ln s < 1` always (numerical max **0.9997**); the warm arm gives **1.31**. An exponent > 1 means the rate approaches a **PLATEAU** — the same statement as §1.3 |
| sigmoid `L_eq` with a FIXED `tau` | **not for the shape** | gives `tau_eff = tau` identically. It IS the right answer for the 2300 LEVELS across arms and for the accelerating `x2300` arm. **Two different constraints; do not conflate** |
| `L_eq = A(T + lambda*L)^q` (convex commitment + melt-elevation feedback) | **works mechanically, DEAD as physics** | gives `tau_eff = tau/(1-g)`, `g = lambda*dL_eq/dL`, unbounded exponent as `g → 1` — the only family clearing the `< 1` ceiling, and best rms-per-parameter (4 params, 0.212). **But it needs `lambda = 22.3 K per m SLE` against a physical 1.5 (uniform) to 5 (melt-weighted): 4.5-15× too much feedback**, sitting at `g = 0.94`, where the `L_eq` clip becomes load-bearing and a 10k ensemble draws members with `g > 1` |
| pin `L_eq` to the Bochow-2023 equilibrium ladder, fit only `c` | **DEAD** | §3.2 |

---

## 3. THE TWO THINGS THAT ARE GENUINELY UNRESOLVED

### 3.1 The `x2300` arm needs something the reservoir cannot give

Cell B is **3.4× short** on `x2300` (41.6 vs 139.7 cm/century). **No fixed-`V`
reservoir can produce an ACCELERATING rate at 13.6 K** — that arm needs the commitment
itself to keep growing with T, i.e. a convex `L_eq`. **The reservoir and the sigmoid
answer different arms and both may be needed.** Nobody has priced them together.

### 3.2 The ensemble and the observed history disagree by a factor of several — TWO ROUTES

* Pin `L_eq` to either Bochow ladder, fit `c` to the arms → `c = 0.030` against the
  history's **0.107**, hindcast **0.47 cm vs 5.78 observed (0.08×)**
  (`python/diag_gis_stepback_lit_leq.py`).
* Fit `L_eq = A(T+λL)^q` to the arms with **NO** history information, run forward on
  1900-2025 → **~1.5 cm vs 5.78 (0.26×)**.

Different form, different fit, same direction. **This is a finding about the ISM
ensemble, not only about our emulator** — ISM ensembles under-reproducing recent
observed GrIS acceleration is a live concern — **and a JOINT fit would have split the
difference and hidden it.**

**⇒ Fit the ensemble first, check history second.** Condition for that being safe:
measure `corr(d(history)/dp, d(2300 rates)/dp)` at the optimum; two-stage holds only if
|ρ| < ~0.3, else joint with explicit documented weights and a weight sensitivity.

**The mechanism, and it is why the fast channel must stay.** Both Bochow ladders are
extremely sensitive at low T (PISM commits 85 % of the sheet by 2.6 K, Yelmo 66 % by
1.76 K) and their `Theta(0) = 0.5 K` — Bochow's zero-forcing reference is +0.5 K GMT,
stated in their own figure code — so `(T - Theta)_+` is ZERO through most of 1900-2025.
`A+B+C` broke the hindcast by making the rate too **BIG**; this breaks it by making the
rate too **SMALL**. History and 2100 are SMB-driven and respond to `T` **directly**, not
to `(T - Theta)`. **Any structural change belongs on the SLOW channel only.**

---

## 4. RUN THESE TWO BEFORE ANY MODEL CHANGE

### 4.1 NPV SENSITIVITY TO `tau` — this may retire the whole question

The entire warm-arm `tau` discrepancy is **2.6 % per rate** — below the best-fitting
model's own 14.4 % residual and far below the ensemble spread. It looks large only
because `tau_eff` amplifies it **58×**. And the 3 % discount factor is **0.024 at 2150,
0.0012 at 2250**.

**If this feeds SC-GHG, a 6 % difference in the 2300 level is worth essentially nothing
in NPV.** It matters for 2300-LEVEL and commitment statements per se, and for tail
statements — and those are exactly the uses where a BOUND should be quoted, not a
point estimate. **NOT YET COMPUTED. Cheap. Do it first.**

### 4.2 THE AMPLIFICATION LAW ABOVE 2.75 K — now blocking, not background

`S(dT)` **saturates at 0.8596 by 2.75 K and is FLAT to 13.63 K**, so the effective amp
is a constant **1.650** across every warm arm; the driver at 13.63 K is **22.5 K**.
Memory [[ladrillo_gis_amp]] item 4 already says *"Trust the shape over 0.75-2.75 K;
unresolved above."* **Every arm in this analysis except ssp126 sits in the unvalidated
region.** Independently flagged by both reviews: `gis_amp ~ 1.92` is an ANNUAL-MEAN
amplification, most Arctic amplification is winter, and winter warming does not drive
melt — melt-relevant Greenland SUMMER warming is ~**1.17×** GMT on Bochow's own
conversion.

**Direction check, already done:** a lower high-T amp makes §1.1's shortfall WORSE
(2.41× → ~3.4×), so **§1.1 is robust**. Nothing else at high T is.

---

## 5. THEN, IF STILL WORTH DOING — THE STAGED PLAN

**Stage 1a — scan `RAMP_W_K`. ~2 h, near-zero risk.** It is pinned at 1.0
(`scope_gis_reservoir_offline.py:75`) and by the §2 identity it **is** a ladder's
`v(theta)` half, exactly. Grid `w ∈ [0.5,1,2,4,8]` on the existing 216 cells → 1080,
still seconds (G-INERT). **Stop/go:** flat in `w` ⇒ the ladder's shape half is inert and
`N>1` cannot pay for itself.

**Stage 1b — add the RATE criterion to the shipped scorecards and re-rank.** The
2250-2300 rate is already implemented in `python/diag_gis_stepback_rate_crit.py`; fold
it into `scope_gis_reservoir_offline.py` as a pass criterion and re-run the 216 (or
1080) cells. This is the cheapest real advance and it **re-opens the shipped cell's
selection**, since A fails a criterion that did not exist when it was chosen.

**Stage 2 — price the reservoir and a convex slow-channel `L_eq` TOGETHER**, against
`x2300` (§3.1). Offline, default-off, bit-identical nesting gate (`ladder=None`, NOT a
numeric sentinel — `np.array_equal`, verified).

**Stage 3 — standalone Greenland refit in `python/gis_offline_cell.py`** only if
Stage 2 clears. Report `nlp` and hindcast RMSE **in the same table as `A+B+C`'s
563 / 0.844 against `A+B`'s 17.86 / 0.062**, so the comparison to the failed predecessor
is unavoidable.

**Stage 4 — the chain.** ~3-5 days + 6-8 h compute. ~10 edit sites in
`julia/calibrate_mcmc_ext.jl`, three of which (`SETP_SKIP` ~1005-1015, `prelayout` /
`GISB_PNAMES` ~1749-1751, `GEO_SEED_FLOOR` ~1943-1962) have each caused a silent,
result-voiding failure in this repo's history. **Starts and `adapted_cov` BY NAME**
[[nameless_matrix_order]].

---

## 6. FILES

**New, tracked this session** — `notes/scoping_2026-08-22_greenland_shape_stepback.md`
(the record; 23 sections), `outputs/greenland_shape_diagnosis.png` (4-panel), and ten
promoted diagnostics, all read-only, all deriving `REPO` from `__file__`:

| script | what it establishes |
|---|---|
| `python/diag_gis_stepback_ceiling.py` | **§1.1**, the φ=1 ceiling table |
| `python/diag_gis_stepback_rate_crit.py` | **§1.2/1.3**, the rate criterion and cells A/B/B' |
| `python/diag_gis_stepback_tau_ours.py` | our `tau_eff` on the five arms, same estimator as PROTECT |
| `python/diag_gis_stepback_fit_held.py` | one-exponential fit per held arm |
| `python/diag_gis_stepback_profile_held.py` | the `(L_inf, tau)` profile — the degeneracy, per arm |
| `python/diag_gis_stepback_tspace.py` | the T-space form + the `(Tc,q)` non-identification grid |
| `python/diag_gis_stepback_hist_c.py` | `c` from history by one division: **0.107 cm/yr/K** |
| `python/diag_gis_stepback_c_by_arm.py` | `c` per arm; the WARM arms give 0.115 / 0.145 |
| `python/diag_gis_stepback_lit_leq.py` | **§3.2**, the Bochow-pinned failure |
| `python/plot_gis_shape_stepback.py` | the 4-panel figure |

**Unchanged** — nothing in `python/scope_gis_*`, nothing in `julia/`. **No gate changed,
no cell moved, no chain started.** The D1-D5 change set
(`spec_2026-08-14_next_calibration.md`) is still NOT STARTED.

---

## 7. TRAPS

* **`tau_eff` is NOT a commitment-free estimator** except for a single exponential. For
  a mixture the flux weight is `a(theta) = v(theta)(1-phi_theta(0))/tau(theta)` and the
  `(1-phi_0)` factor depends on the whole ramp history. Wherever the scoping note's §2
  called that measurement clean, it is not (corrected in its §16).
* **Report `k = 1/tau`, never `tau`.** `dtau/tau = (tau/50)*d ln(R1/R2)` ⇒ noise
  amplified **57.8× at τ = 2890**. The 5.61 K arm's τ is **one-sided at every noise
  level** — even at 1 % noise the 95 % interval is [1306, ∞). Write *"τ > ~900 yr
  (95 %), point estimate not meaningful."*
* **"35/35 runs" is not p = 2^-35.** Cluster by GCM: **7/7, p ~ 0.008.** And growth in
  elapsed time is guaranteed by log-convexity for ANY positive mixture — it is a near
  tautology, not evidence.
* **The cross-arm `tau` claim rests on ONE arm.** 1.95 K and 2.98 K overlap and the
  FIRST window is non-monotone in T; the 13.63 K arm is rising and yields no τ.
* **`r2300` holds the 2100 RETREAT MASK and the SMB forcing**, not just GSAT ⇒
  26.5 cm/century is a **LOWER bound** and the flat rate is interior drawdown, not
  marine retreat. (This also CLOSES the "is it boundary-condition drift?" check.)
* **The cool arms are two loosely-constrained points, not a slope.** ssp126 `x2300`
  (2.44 K) gives LOWER and 8× narrower loss than ssp126 `r2300` (1.95 K) — GCM
  composition, n=6 vs 10. Same signal as the 3.3× `c` disagreement between them.
* **ssp126 `r2300` (7-17 cm at 1.95 K) sits BELOW Box et al. 2022's already-committed
  274 ± 68 mm.** One low-sensitivity model must not set our low-end commitment.
* **`V = 6 m` EXCEEDS `V_MAX_M = 2.73`** (NO+NE Mouginot) ⇒ cell B is a **whole-sheet**
  object, not the high-basin tap. Wiring it re-opens the capacity clamp.
* **Serial correlation.** 285 annual points without an AR(1)/GP noise model gives
  effective n ~ 5-6; every interval comes out ~7× too tight.
* **Check clip activation before ANY Hessian diagnostic** — `clip(alpha*T+beta,1e-9,1)`
  and `clip(L_eq,0,k*V0)` are non-smooth and invalidate gradients at a binding clip.
* **The Bochow conversion is `GMT = f_conv/1.19 + 0.5`** as the repo has it — only that
  direction reproduces the paper's "~1.4 °C regional summer (1.7 °C GMT)". A review
  asserted the inverse; it is wrong.
* **The 6.5 K tap onset is NOT a Bochow attribution.**
  `greenland_3basin_component.jl:112-129` derives it from a design principle. A review
  flagged it as possibly misattributed; checked, and it is clean. **No action.**

---

## 8. WHAT THIS DOES *NOT* SETTLE

* **Every anchor past 2100 is NORCE-CISM** — ONE ice-sheet model, so the p05-p95 is
  CLIMATE-forcing spread, not structural spread. This whole analysis inherits that, and
  it binds HARDER here than for a level target, because §1.2 reads a functional form off
  the SHAPE of those runs.
* **The 2100 over-prediction is a separate, still-open defect.** We run 20-45 % fast
  before 2100 on the warm/mid arms (`diag_gis_stepback_tau_ours.py`). Ridge-invariant,
  and untouched by anything here.
* **Nothing here is calibration-inert** except the reservoir cells. A curved `L_eq` acts
  in the hindcast ⇒ refit, not prior-propagation.
* **No error bar exists on any `tau_eff` in the record.** §7 says how to build one; it
  has not been built.
* **The real unconverged mass is still AIS**, and the 20 unconverged marginals mean L14
  supports **projections only, NOT parameter-level inference**.
