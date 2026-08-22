# Step-back — what the Greenland evidence actually says, and what functional form could meet it

Written 2026-08-22 (repo `SLR-RFF-BRICK`, branch `ladrillo-dev`), on top of
`handoff_2026-08-21e_retarget_done_shape_next.md`. **Nothing in the repo was
changed by this note** — every number below comes from read-only scripts run in
a scratchpad against committed artefacts. Reproduce with the snippets named in §6.

**One line.** The defect is not the tap, not the relaxation rate, and not a
scale along the commitment ridge — it is that **`L_eq(T)` is LINEAR in `T`**. A
linear commitment law is *adequate* below 3 K and **arithmetically incapable**
of reaching the warm arms even at full equilibration, and its linearity is also
what forces the model's single fixed relaxation timescale. Fixing the shape of
`L_eq(T)` fixes both the level and the shape at once. **But the same data cannot
identify that curve** — see §4, which is the constraint on how to proceed.

---

## 1. THE ARITHMETIC DEATH CERTIFICATE FOR THE LINEAR COMMITMENT LAW

Set every rate to infinity, i.e. let the model fully equilibrate (φ = 1) at each
arm's own 2300 driver, and ask what it can deliver. This is a pre-check, not a
scan; it bounds **every** rate-side knob at once.

| arm | GSAT@2300 | φ=1 CEILING | PROTECT median | shortfall |
|---|---|---|---|---|
| SSP5-8.5 x2300 | 13.63 K | 96.8 cm | 233.6 cm | **2.41×** |
| SSP5-8.5 r2300 | 5.61 K | 37.1 cm | 71.5 cm | **1.93×** |
| SSP2-4.5 r2300 | 2.98 K | 18.3 cm | 15.4 cm | 0.84× (adequate) |
| SSP1-2.6 x2300 | 2.44 K | 12.9 cm | 9.8 cm | 0.76× (adequate) |
| SSP1-2.6 r2300 | 1.95 K | 11.1 cm | 11.1 cm | 1.00× (exactly at it) |

**No rate law reaches the warm arms.** γ was killed by the `1/φ` bound
(2026-08-21j); this is the same bound stated once for the whole rate side, and
it also explains why the ridge scale `k` is not the answer: `k` multiplies the
cool ceilings by the same factor, and the cool arms are already **at** theirs.

**The design spec that falls out, quantified:** the commitment law must be
**≈2× larger at 5.6 K and ≈2.4× larger at 13.6 K than linear, while unchanged
or slightly smaller at ≤3 K.** That is a convexity requirement with numbers on
it, derived without fitting anything.

## 2. THE SHAPE EVIDENCE, AND WHY IT IS THE SAME FINDING

The three `r2300` arms HOLD GSAT constant after 2100. In a first-order
relaxation the *rate* decays as `exp(-t/tau)` **independently of the commitment
size**, so on those arms the rate decay is a commitment-free estimator of `tau`.

Rate of loss, cm SLE / century, per 50-yr window, arm median — **PROTECT / ours (L14, k=1)**:

| arm | 2050-2100 | 2100-2150 | 2150-2200 | 2200-2250 | 2250-2300 |
|---|---|---|---|---|---|
| 5.61 K held | 25.9 / **31.2** | 30.2 / 16.8 | 27.9 / 7.6 | 27.0 / 4.6 | 26.5 / **2.9** |
| 2.98 K held | 8.5 / 12.3 | 6.4 / 7.3 | 4.8 / 4.1 | 3.9 / 2.7 | 3.5 / 1.9 |
| 1.95 K held | 5.8 / 6.5 | 4.4 / 3.8 | 3.5 / 2.4 | 2.8 / 1.7 | 2.3 / 1.3 |
| 13.63 K rising | 19.9 / 32.1 | 68.5 / 50.6 | 107.5 / 44.1 | 128.9 / 29.2 | 139.7 / 16.6 |

**Ladrillo is front-loaded and then exhausts**: 20-45 % too FAST before 2100 on
the warm/mid arms, 9× too SLOW by 2250-2300 at 5.6 K. Under held forcing PROTECT
loses mass at an almost constant 26-30 cm/century for 200 years; we decay away.

Effective timescales, from the same decay (successive windows):

| arm | PROTECT | OURS |
|---|---|---|
| 5.61 K held | 629, 1518, 2889 yr | 63, 98, 111 yr |
| 2.98 K held | 168, 248, 439 yr | 86, 120, 141 yr |
| 1.95 K held | 201, 233, 260 yr | 115, 148, 167 yr |

**PROTECT's `tau_eff` RISES with temperature; ours FALLS** (because `r = alpha*T + beta`
with `alpha > 0`). That is a sign disagreement, not a magnitude one. Per-run
check, to rule out the artefact of medianing a spread of exponentials: `tau_eff`
grows with elapsed time in **35/35**, **15/15** and **9/10** runs respectively.

> ⚠ The all-same-sign uniformity is exactly the pattern `[[climate-modeling]]`
> says to distrust. It survives the per-run check, but it has NOT been checked
> against control drift, against the ocean forcing (which `r2300` does not hold),
> or with an error bar. Treat the DIRECTION as established and the MAGNITUDE as
> provisional.

**These two sections are one finding.** In a relaxation toward `L_eq(T)` driven
by a melt flux, `tau_eff = L_eq'(T) / c`. A LINEAR `L_eq` has constant `L_eq'`,
hence one fixed `tau` — the model's fixed timescale is a *consequence* of the
linearity, not an independent assumption. A sigmoidal `L_eq` gives a short `tau`
where the curve is flat (cool), a long `tau` on the steep limb (5-6 K), and short
again once it saturates — which is the non-monotone pattern the arms show
(218 yr at 2-3 K, ~1000 yr at 5.6 K, and **≤350 yr** at 13.6 K, where the
observed 140 cm/century against at most 7.42 m remaining bounds `tau` from above).

## 3. THE CANDIDATE FORM

Relax in **temperature space** rather than volume space:

```
dL/dt = c * ( T(t) - Theta(L) )_+ ,    Theta = L_eq^{-1},
L_eq(T) = V0 * (1 - exp(-(T/Tc)^q))
```

Three parameters (`c`, `Tc`, `q`) replacing the current commitment+two-channel
block. It **strictly nests the shipped model**: with `L_eq = c1*T + c0`,
`Theta(L) = (L-c0)/c1` and the equation collapses to `dL/dt = (c/c1)(L_eq - L)`,
a fixed-`tau` relaxation with `tau = c1/c`. So the shipped model is the
linear-`L_eq` special case and the nesting gate is exact, as for `gamma`.

Fitted to all five arms' median annual trajectories 2015-2300 on each arm's own
GSAT: `c = 0.0954 cm/yr/K`, `Tc = 8.08 K`, `q = 3.28`. Predicted `tau_eff(T)`
**130 / 318 / 1015 / 41 yr** at 2 / 3 / 5.6 / 13.6 K — the measured non-monotone
pattern, from three parameters that were not told about it.

**The out-of-sample consistency worth noting.** While `L` is small `Theta ~ 0`
and the history reads directly as `c = dL / integral(T dt)` — one division, no
fit: 5.78 cm / 54.2 K·yr = **0.107 cm/yr/K**. The two *warm* arms, 4-10× hotter
than anything in the record, independently want **0.115** and **0.145**
(1.08× and 1.36×). The cool arms scatter 0.064-0.212 — as expected, since with
~10 cm of loss and a small `(T - Theta)` excess they barely constrain `c`.

**Where it does not fit.** 30 % misfits remain: 59 vs 71 cm (5.6 K held, 2300),
155 vs 234 (13.6 K), 6.5 vs 11.1 (1.95 K held), 18.3 vs 15.4 (2.98 K held).
`ssp126 r2300` and `ssp126 x2300` — the *same scenario*, different family — want
`c` 3.3× apart. That is very likely the GCM panel differing between families
(`r2300` = CESM2 + MPI-ESM1-2-HR, `x2300` = CESM2-WACCM) and hence the
Arctic amplification differing, which the fit above ignores by driving on GSAT
instead of the repo's regional `gis_amp` driver. **Rerun on the regional driver
before reading anything into the residual.**

## 4. THE CONSTRAINT THAT GOVERNS EVERYTHING ELSE: `L_eq` IS NOT IDENTIFIED

Profile `(Tc, q)` with `c` refit at every node. Near-equal-misfit nodes imply
committed fractions at 5 K of **3 % to 100 % of the ice sheet**:

| misfit / committed-at-5K | q=2 | q=2.5 | q=3 | q=4 |
|---|---|---|---|---|
| Tc = 4 K | 70.4 / 79 % | 65.8 / 83 % | 60.5 / 86 % | 48.7 / 91 % |
| Tc = 6 K | 67.2 / 50 % | 59.3 / 47 % | 49.4 / 44 % | **32.2 / 38 %** |
| Tc = 8 K | 63.7 / 32 % | 51.6 / 27 % | 36.5 / 22 % | 75.7 / 14 % |
| Tc = 12 K | 55.6 / 16 % | **34.9 / 11 %** | 66.7 / 7 % | 264.7 / 3 % |

The same ridge appears one level down: fitting **one** exponential per held arm
and profiling `tau` gives, at 5.61 K, `L_inf` from 100 cm (`tau`=218) to 1457 cm
(`tau`=5000) with every misfit far below the arm's own p05-p95 spread of 78.9 cm.
What IS tightly determined there is the **product** `L_inf/tau ≈ 30 cm/century`
and a lower bound `tau ≳ 300 yr`. On the two cool arms `tau` **is** identified
and sharp — **218 yr on both**, with `L_inf` = 2.1 % and 2.9 % of the sheet.

**Consequence for how to proceed.** 285 years of transient constrains a
*product*, never an equilibrium. This is the same ridge that produced 86/216
admissible reservoir cells, one abstraction up — so a bigger scan will not
resolve it. **The equilibrium curve has to come from the equilibrium
literature** (Robinson 2012 / Bochow 2023 / Van Breedam 2020 class), with
PROTECT supplying `c` and the transient. Fit that way the problem is
well-posed; fit jointly it is not.

## 5. WHAT THIS RE-RANKS

* **The tap / option-3 reservoir is the right SHAPE of fix in the wrong
  coordinates.** A threshold reservoir that opens above ~4.7 K with `tau ~800 yr`
  is a one-rung discretisation of exactly the convex `L_eq` above. That is why it
  cleared 86 cells — and its non-identification is §4, not a grid problem.
* **`gamma`'s death certificate generalises.** §1 kills the entire rate side in
  one table, including any `r(T)` re-shaping, without a scan.
* **The `k` ridge tension dissolves.** ssp585 wanting `k=2-3` and the cool bands
  wanting `k<=1.0` is one law being asked to be steep at 6 K and flat at 2 K. A
  scale cannot; curvature can. Nothing has to be traded off.
* **A 2100 defect is now visible and is NOT the same defect.** We run 20-45 %
  fast before 2100 on the warm/mid arms. Consistent with the recorded
  "2100 over-prediction is ridge-INVARIANT (separate defect)".

## 6. REPRODUCE

Read-only scratchpad scripts, `/private/tmp/.../scratchpad/`:
`tau_ours.py` (our `tau_eff` on the five arms), `fit_held.py` + `profile_held.py`
(§4 one-exponential fits and profiles), `tspace.py` (§3 fit + §4 grid),
`hist_c.py` and `c_by_arm.py` (the `c` consistency), `ceiling.py` (§1),
`diag_fig.py` (the 4-panel diagnosis figure).

## 7. WHAT IS NOT SETTLED

* Every anchor past 2100 is **NORCE-CISM** — ONE ice-sheet model. The spread is
  climate-forcing spread, not structural spread. This note inherits that caveat
  in full and it is *more* binding here, because §3 reads a functional form off
  the shape of those runs.
* The §3 fit drives on **GSAT**, not the repo's regional `gis_amp` driver, and
  fits arm **medians** with no weighting by `n` (6 to 35) and no account of
  within-GCM dependence among SMB percentile members.
* `tau_eff` has **no error bar** anywhere in this note.
* Nothing here is calibration-inert. Unlike the threshold reservoir, a curved
  `L_eq` acts in the hindcast, so it is a **refit**, not a prior-propagation.
  §4's split (literature `L_eq`, PROTECT `c`, history as a check) is the proposal
  for containing that cost — it has not been priced.

---

# ADDENDUM (same day) — two results that sharpen §3 and one that partly refutes it

## 8. A COMMON-`tau` LADDER IS EXACTLY ONE RESERVOIR WITH A SHAPED RAMP

Measured, not argued (code review, 2026-08-22): for a linear system driven through
one LTI kernel, summation commutes with relaxation, so

```
sum_theta v(theta) * relax_tau( ramp(T; theta) )  ==  relax_tau( sum_theta v(theta) * ramp(T; theta) )
```

N=25 rungs, `tau`=400 yr, 451 yr: **max |difference| 3.3e-16**. Disperse `tau`
log-uniformly over 100-3200 and they separate by 9.2 % of the reservoir's range.

**So a "ladder of threshold reservoirs" decomposes into exactly two halves:** its
`v(theta)` half **is** the `RAMP_W_K` constant in `scope_gis_reservoir_offline.py:75`
— **pinned at 1.0 and never scanned** — and only `tau(theta)` dispersion is new,
worth ~9 %. **Scan `RAMP_W_K` before proposing any ladder.** It is an afternoon
against a scan that already runs in seconds, and a flat response would retire three
of four proposed parameters.

This does NOT apply to §3's form, which is a NONLINEAR ODE — `Theta(L)` makes the
LTI argument fail. It applies to the ladder framing, and it is a reason to prefer
§3's form over a ladder: the ladder's extra parameters are mostly already reachable.

## 9. THE LITERATURE EQUILIBRIUM CURVE AND THE 1900-2025 RECORD ARE INCOMPATIBLE UNDER ANY ONE-CHANNEL LAW

§4 concluded "take `L_eq` from the equilibrium literature". **That was run, and it
fails** — the Bochow-2023 ladder is already tracked at
`data/observations/greenland_equilibrium_bochow2023.csv` (Yelmo-REMBO and PISM-dEBM,
via the authors' own `GMT = f_conv/1.19 + 0.5`).

Pin `L_eq` to each ladder, fit only `c`:

| | `c` fitted to the 5 arms | hindcast 1900-2025 | ssp585 r2300 @2300 | ssp126 r2300 @2300 |
|---|---|---|---|---|
| PISM-dEBM | 0.0297 | **0.47 cm vs 5.78 obs (0.08×)** | 35.3 vs 71.5 | 11.4 vs 11.1 |
| Yelmo-REMBO | 0.0292 | **0.47 cm (0.08×)** | 34.2 vs 71.5 | 11.5 vs 11.1 |

The arms want `c = 0.030`; the history wants **0.107**. A **3.6× conflict**, and the
cool arms fit beautifully while the warm arms come out 2× low.

**The mechanism, and it is the same obstruction option C hit, mirrored.** Both
ladders are extremely sensitive at low `T` — PISM commits 85 % of the sheet by
2.6 K, Yelmo 66 % by 1.76 K — so `Theta(0) = 0.5 K` (Bochow's zero-forcing reference
is +0.5 K GMT, stated in their own figure code) and `max(T - Theta, 0)` is ZERO for
most of 1900-2025. `A+B+C` broke the hindcast by making the rate too BIG (proportional
relaxation, RMSE 1.675, 72 cm at 2100); the T-space form breaks it by making the rate
too SMALL. **Either way the Bochow equilibrium curve cannot carry the observed
historical loss on its own.**

> ⚠ And the ladders' transitions are **one grid interval wide in both models**
> (Yelmo 1.676→1.760 K, PISM 2.181→2.601 K), so the transition WIDTH is a sampling
> artefact. `[[ladrillo_ladder_arms]]` — carry both, never fit the width.

**What this implies for the design, and it narrows the change rather than widening
it.** The fast channel is doing real work that the threshold law cannot do: history
and 2100 are SMB-driven and respond to `T` directly, not to `(T - Theta)`. So the
structural change belongs on the **SLOW channel only** —

```
fast   dL_f/dt = ( f*L_eq_lin(T) - L_f ) * r_f(T)        UNCHANGED; carries history + 2100
slow   dL_s/dt = c_s * ( T - Theta(L_s) )_+              NEW; carries 2150-2300 at high T
```

which is contained, keeps every gate the fast channel already passes, and matches the
physical split the repo already uses (`gis_offline_cell.py`: f = surface mass balance,
1-f = dynamic discharge). **NOT YET RUN.** It is the next measurement, and it should
be run before anything is proposed to the calibrator.

## 10. THE §3 FIT'S `L_eq` IS NOT THE LITERATURE'S, AND THAT IS THE HONEST TENSION

§3's fitted curve gives 18.7 % of the sheet committed at 5 K; PISM gives 98.7 % and
Yelmo 98.4 %. The fit is not measuring the equilibrium — it is measuring a
**300-year effective commitment**, which is the only thing 285 years of transient can
see (§4). Do not present the §3 `L_eq` as an equilibrium curve. Two curves are in
play and they answer different questions:

* **`L_eq^{300yr}`** — what the arms identify, ~19 % at 5 K, sets the deliverable.
* **`L_eq^{eq}`** — Bochow, ~99 % at 5 K, sets the multi-millennial story and is
  **irrelevant to a 2300 deliverable** except as a ceiling.

The whole `k`-ridge / `gamma` / tap arc has been implicitly conflating them.

---

# ADDENDUM 2 — the Greenland-physics review, one correction to §2, and a cell that beats the shipped one

## 11. CORRECTION TO §2's GLOSS (the measurement stands, the prescription was wrong)

Two things in §2 were over-read.

**(a) "`tau_eff` grows with elapsed time" is nearly content-free.** For ANY
superposition of relaxation modes, `tau_eff(t)` rises monotonically toward the
slowest mode by construction. "35/35 runs" is what a two-mode system does
deterministically — it rules out the medianing artefact and nothing else. The
composition change behind it is real and documented (Aschwanden 2019: by 2300 under
RCP8.5 almost all NW outlets have gone land-terminating and discharge collapses), but
it is EXPECTED, not diagnostic. **Do not carry this as evidence.**

**(b) "`tau` is longer at higher T" is the wrong physical gloss and contradicts the
literature.** Drainage gets FASTER in a warmer world:

* Levermann & Winkelmann 2016 (TC 10, 1799): losing 10 % of Greenland takes
  **~3500 yr at 0.5 °C above threshold, ~500 yr at 5 °C**.
* Van Breedam, Goelzer & Huybrechts 2020 (ESD 11, 953): complete loss in **~2000 yr**
  at highest forcing vs **~10 000 yr at 2 °C**.

So **do not re-sign `r(T)`.** The right reading of the measurement is
**COMPOSITION**: `tau_i` rises with a reservoir's THRESHOLD (deep interior ice is
intrinsically slower than the marine periphery) while every `tau_i` FALLS with
ambient T. At 5.6 K the system is past every published bifurcation, so there is no
nearby equilibrium to relax toward and `tau_eff` → ∞ is a symptom of the commitment
being far away. **This is consistent with §1 and §3** — `tau_eff = L_eq'(T)/c` is a
composition statement, not a rate statement — but §2's phrasing invited the wrong fix
and is corrected here.

## 12. THE `r2300` ARM IS BIASED LOW, SO 26.5 cm/century IS A LOWER BOUND

Goelzer 2025's `r2300` holds not only GSAT but the **2100 retreat mask, constant**,
and the SMB forcing. So the post-2100 loss there is near-pure SMB drawdown plus
adjustment to an already-imposed retreat. Two consequences: the flat rate **cannot**
be attributed to runaway marine retreat (it is interior/ablation-zone drawdown), and
the arm **understates** the sustained-warming response. My §2 worry that `r2300`
"holds GSAT but not ocean forcing" is inverted — the ocean forcing is held more
rigidly than the atmosphere.

## 13. THE MISSING CRITERION, AND A CELL THAT PASSES IT

Every tap/reservoir cell to date was scored on LEVELS and on an RMS of log-levels.
**None was scored on the RATE at the last horizon** — so a cell can land on the 2300
level with the wrong slope and be wrong again by 2400. Adding the 2250-2300 rate per
arm at matched forcing:

| cell | 8.5 r2300 | 8.5 x2300 | 2.6 r2300 | 4.5 r2300 | our ssp585 @2300 | Δ2100 | ssp245 dev |
|---|---|---|---|---|---|---|---|
| **PROTECT (target)** | **26.5** | **139.7** | 2.3 | 3.5 | matched p50 98.5 | — | — |
| base, no reservoir | 2.9 | 16.6 | 1.3 | 1.9 | 49.9 | 0 | 0 |
| **A** V=1.0, onset 4.69, τ=800 (the shipped offline optimum) | 12.0 | 26.4 | 1.3 | 1.9 | 70.9 | +0.0000 | +0.000 |
| **B** V=6.0, onset 4.69, τ=2200 | **26.0** | 41.6 | 1.3 | 1.9 | **99.1** | +0.0000 | +0.000 |
| B' V=3.0, onset 4.69, τ=1100 | 24.1 | 39.5 | 1.3 | 1.9 | 97.1 | +0.0000 | +0.000 |

**Cell A matches the LEVEL and misses the RATE by 2.2×; cell B matches BOTH** — and
lands our own ssp585 at 99.1 cm against the matched p50 of 98.5. Both are exactly
inert at 2100 and on the cool scenarios. B is not a fitted stub: `V ≈ V0` on a
**2-3 kyr clock** is what the equilibrium literature says (Van Breedam ~2 kyr at high
forcing; Greve & Chambers 2022, SICOPOLIS under sustained late-21st-century climate,
**1.79 ± 0.80 m by 3000** ⇒ single-exponential τ ≈ 3300 yr).

**Two things cell B does NOT fix, and they must be said with it:**

* **`V = 6 m` EXCEEDS `V_MAX_M = 2.73 m`**, the NO+NE Mouginot inventory. Cell B
  cannot be the high-basin tap — it is a **whole-sheet** object. B' at V=3.0 is still
  over. Wiring it means re-deciding what the reservoir is charged against, and
  re-opening the capacity clamp.
* **The `x2300` arm stays 3.4× short** (41.6 vs 139.7). No FIXED-`V` reservoir can
  produce an accelerating rate at 13.6 K; that arm needs the commitment itself to
  keep growing with T — i.e. §3's sigmoid `L_eq`, not a reservoir. **The reservoir
  and the sigmoid are answering different arms.**

## 14. LITERATURE ANCHORS WORTH HAVING ON RECORD

Equilibrium committed loss vs sustained GMST — the curve is a **sigmoid**: small
offset at T=0, steep (in some models discontinuous) rise between **~1.5 and ~3.5 K**,
saturating near 7.4 m by **4-6 K**, with hysteresis and at least one intermediate
state.

| source | threshold (GMST above PI) | committed |
|---|---|---|
| Robinson, Calov & Ganopolski 2012, NCC 2, 429 | ~1.6 K (paper argues 1-2 K) | multiple stable states up to complete |
| Bochow et al. 2023, Nature 622, 528 | **1.7-2.3 K** | <1 m at 1.5 K; PISM 3 regimes, Yelmo 2 |
| Höning et al. 2023, GRL 2022GL101827 | ~0.6 and ~1.6 K | non-linear drop at each |
| Gregory, George & Smith 2020, TC 14, 4299 | **no sharp threshold** — monotonic | 3 K ⇒ >5 m lost; 5 K ⇒ >7 m lost |
| Zeitz et al. 2022, ESD 13, 1077 | irreversible at 3 K (lapse ≥6 K/km) | 61-93 % of present volume in the partial regime |
| Van Breedam et al. 2020, ESD 11, 953 | none — complete in all scenarios | ~7 m, 2 kyr (high) to 10 kyr (2 K) |

**Melt-elevation feedback: 0-20 % at 2300, not 7×.** My §1-era back-of-envelope of
~6 % was the right order but used a 2000 m mean thickness; BedMachine gives ~1670 m,
so 0.5 m SLE ⇒ ~112 m thinning ⇒ 0.73 K, and λ ≈ **1.5 K per m SLE** uniform,
plausibly 3-5 melt-weighted. Gregory 2020 measures **~20 % additional SMB decline by
centuries 2-3**; TC 19, 2289 (2025) finds fixed-lapse-rate runs **overestimate** loss
by 17.0 ± 0.4 % at 4×CO2, and Zeitz 2022 has isostasy offsetting ~⅓ of thinning. So
put it in the **threshold** (`theta_eff = theta - lambda*L`), not in the gain.

**Two flags on the target data itself:**
* **ssp126 `r2300` (7-17 cm at 1.95 K) is BELOW Box et al. 2022's already-committed
  274 ± 68 mm** from 2000-2019 climate alone. One low-sensitivity model should not
  set our low-end commitment.
* The ssp126 `x2300` / `r2300` **inversion** — the WARMER arm (2.44 K) gives LOWER
  and far narrower loss (10.3-11.2 vs 7.0-16.7) — is GCM composition, n=6 vs 10.
  **The cool arms are two loosely-constrained points, not a temperature-response
  slope.** This is the same signal as §3's 3.3× `c` disagreement between them.

## 15. TWO CLAIMS FROM THE REVIEW THAT DO **NOT** SURVIVE CHECKING

* **"The 6.5 K tap onset may be misattributed to Bochow."** It is not.
  `greenland_3basin_component.jl:112-129` derives it from a design principle — the tap
  must not move any horizon with independent validation — extended to 2150. No Bochow
  attribution appears anywhere near it. **No action.**
* **"Bochow's mapping is ΔGMT = 1.19 × ΔT_JJA + 0.5, so Greenland summer warms
  0.84 K per K GMST."** Inverted. `build_greenland_equilibrium_ladder.py` takes the
  authors' own `GMT = f_conv/1.19 + 0.5` from their figure code, and only that
  direction reproduces the paper's stated "~1.4 °C regional summer (1.7 °C GMT)":
  1.4/1.19 + 0.5 = 1.68. So Greenland **summer** warming is ~**1.17×** GMT.
  **The underlying concern survives even though the number was backwards**: our
  `gis_amp ≈ 1.9` is an ANNUAL-MEAN amplification, most Arctic amplification is
  winter, and winter warming does not drive melt. 1.9 vs a melt-relevant ~1.17 is a
  **1.6× extrapolation hazard** that `c1` absorbs at calibration temperatures and will
  not absorb at 10-14 K. **Worth a check; not yet run.**

---

# ADDENDUM 3 — the statistical review. One more correction to §2, and the honest deliverable

## 16. CORRECTION: "`tau_eff` IS A COMMITMENT-FREE ESTIMATOR" IS TRUE ONLY FOR A SINGLE EXPONENTIAL

§2 leaned on this and it is wrong for a mixture. On a held arm the rate is
`R(s) = INT a(theta) exp(-s/tau(theta)) d theta` with **`a(theta) = v(theta)(1-phi_theta(0))/tau(theta)`**
— the flux weight carries `(1-phi_theta(0))`, which depends on the whole ramp history
and hence on the commitment. Two models with identical `tau(theta)` and different
`v(theta)` give different `tau_eff`. **`tau_eff` is a functional of the spectrum AND
the commitment.** Everywhere §2 called it clean, it is not.

## 17. THE DELIVERABLE FROM CELL B IS A FLUX, NOT A `(V, tau)`

Exact degeneracy: for any component with `tau >>` the window, `phi ~ s/tau`, so both
the level and the rate depend only on **`psi = V/tau`**. The curvature separating them
is `O((s/tau)^2)`: a **3x change in `tau` at matched flux moves the 200-yr level by
6.3 %** — against the 5.61 K arm's own p05-p95 factor of **3.6**. So the 86/216 was
the correct answer, not a fitting failure, and no better optimiser or finer grid fixes it.

**This reads §13's table correctly.** Cell A has `psi = 1.0/800 = 0.125 cm/yr`; cells B
and B' BOTH have `psi = 6/2200 = 3/1100 = 0.273 cm/yr`. The measured rates are 12.0 for
A and **26.0 / 24.1 for B and B'** — the 2.2x A→B ratio is exactly the flux ratio, and
B vs B' (a 2x change in `tau` at matched flux) differ by **7.9 %**, right at the
predicted curvature size. **The rate criterion identifies `psi`. It does not identify
`V` or `tau`, and it never will.**

> **So state the finding as: an additional sustained flux of `psi ~ 0.27 cm/yr` opening
> above ~4.7 K.** `V = 6 m / tau = 2200 yr` is one point on that ray, chosen because the
> equilibrium literature says the ray should be entered near `V ~ V0` on a 2-3 kyr clock.
> That is a PRIOR choosing a point on an unidentified line — exactly the tap's own
> "IT IS A PRIOR SPECIFICATION, NOT A FIT" discipline
> (`greenland_3basin_component.jl:111`). Say so wherever it is quoted.

## 18. WHOLE FAMILIES REFUTED BY AN EXACT BOUND

For **any** completely monotone response — every positive mixture of exponentials,
which includes the ladder, Prony series, stretched exponential, Mittag-Leffler /
fractional relaxation and every power-law memory kernel —

  **`d ln tau_eff / d ln s < 1`, always.**

(Stretched exponential: `tau_eff = t/[beta*u^beta - (beta-1)]`, numerical max of the
exponent over `beta` in (0.02,0.99) and `u` in [1e-4,1e3] is **0.9997**. Regular
variation with index `-p` gives `tau_eff ~ s/p`, exponent → 1.)

The warm arm gives **1.31** (elapsed time from the 2100 hold) or 3.31 (my earlier
convention). **Above 1 either way.** An exponent > 1 means `R(s)` is not decaying like
any power law — **it is approaching a PLATEAU.** A 2-term Prony reproduces
631/1525/2675 exactly as "one fast component that dies (40 yr) + a near-constant flux
(3871 yr carrying 95 % of the 2100-2150 rate)".

**That is the same statement as §17.** The warm arm is measuring a sustained flux, not
a long timescale. Stop looking for a timescale there.

**Also dropped:** a sigmoid `L_eq` with FIXED `tau` gives `tau_eff = tau` identically —
no growth in `s`, none in `T`. It is the right answer for the 2300 LEVELS (§3, and the
`x2300` arm of §13) and useless for the shape signature. **Two different constraints;
do not conflate them.** And the continuum ladder cannot deliver the within-arm half at
all: `a(theta)` carries `1/tau`, so short-`tau` bins are doubly weighted and
`tau_eff(0) → 2*tau_min` **independent of `tau_max`** (verified: `tau` log-uniform on
[50,3000] gives 98.4 yr, analytic 98.4). You cannot see a 2700-yr bin inside a 200-yr
window. A 5-parameter ladder fit drove its `tau(theta)` exponent to 0.5 and abandoned
the mechanism.

## 19. THE ONE FAMILY THAT WORKS MECHANISTICALLY — AND WHY THE PHYSICS KILLS IT

`L_eq = A(T + lambda*L)^q` with a single `tau` gives, in two lines,

  **`tau_eff = tau / (1 - g)`,  `g = lambda * dL_eq/dL`**

`g` rises with `L` (hence with elapsed time, for `q>1`) and with `T`. **Both halves of
the signature, and the exponent is UNBOUNDED as `g → 1`** — which is how it clears the
`< 1` ceiling that refutes every completely-monotone family. Best rms-per-parameter in
the sweep (4 params, 0.212). Note it needs the CONVEXITY: a linear feedback gives
`tau_eff = tau/(1-a*lambda)`, constant in `s`.

**But the two reviews falsify it against each other.** The fit needs
`lambda = 0.223 K/cm` = **22.3 K per m SLE**. §14's physical melt-elevation coefficient
is **~1.5 K/m uniform, 3-5 K/m melt-weighted**. **The fit requires 4.5-15x more
elevation feedback than the physics allows**, and it sits at `g = 0.94` — 94 % of the
way to runaway, where the `L_eq` clip stops being incidental and becomes load-bearing,
and a 10k-member ensemble will draw members with `g > 1`. **Do not adopt family C as
physics.** Its value is that it names the flat direction "distance to runaway", which
has an external prior; but `rho(ln lambda, ln tau) = -0.98` and condition number 1.07e5
— **its identifiability is no better.**

## 20. STAGE-0 IS CLOSED, AND THE HISTORY/ARMS CONFLICT IS NOW TWO-ROUTE

The statistical review named its highest-value check as: verify the ISM boundary
conditions are actually held after 2100, not just GSAT — because a common-mode drift
would produce growing `tau_eff` in every run and no per-run sign test could see it.
**§12 already closes it**: Goelzer's `r2300` holds the 2091-2100 forcing in randomised
order AND the **2100 retreat mask constant**. Residual risk is bedrock/GIA and the
ISM's own internal thermal adjustment, not ocean-forcing lag.

**And the history/arms conflict now has two independent routes.** §9: pin `L_eq` to
Bochow, fit `c` to the arms → hindcast 0.47 cm vs 5.78 (0.08x). Statistical review:
fit family C to the arms with NO history information, run forward on 1900-2025 →
**~1.5 cm vs 5.78 (0.26x)**. Different form, different fit, same direction, several-fold.
**This is a finding about the ISM ensemble, not only about our emulator** — ISM
ensembles under-reproducing recent observed GrIS acceleration is a live concern, and a
JOINT fit would have converted it into a slightly-off parameter and hidden it.
**⇒ fit the ensemble first, check history second.** Condition: measure
`corr(d(history)/dp, d(2300 rates)/dp)` at the optimum; two-stage is safe only if
|rho| < ~0.3.

## 21. STATISTICS TO ADOPT

* **Report `k = 1/tau`, not `tau`.** `dtau/tau = (tau/50)*d ln(R1/R2)`, so noise is
  amplified **57.8x** at `tau = 2890`. The 5.61 K arm's `tau` is **one-sided at every
  noise level** — even at 1 % noise on the median rate ratio the 95 % interval is
  [1306, INF). Write "`tau` > ~900 yr (95 %), point estimate not meaningful."
  **Every `tau_eff` in §2 and §11 of this note should be re-read that way.**
* **35/35 is not p = 2^-35.** Cluster by GCM: 7 GCMs → **7/7, p ~ 0.008**. Still
  significant, four orders of magnitude weaker than it looks.
* **Serial correlation.** Fitting 285 annual points without an AR(1)/GP noise model
  gives effective n ~ 5-6, so every interval comes out ~7x too tight.
* **Profile along the SLOPPY EIGENDIRECTIONS, not the coordinate axes.** A coordinate
  grid samples a curved ridge as a blob — **that is probably why 216 cells looked like a
  fat admissible set.** Check clip activation first: `clip(alpha*T+beta, 1e-9, 1)` and
  `clip(L_eq, 0, k*V0)` are non-smooth and invalidate every Hessian diagnostic at a
  binding clip.
* **The cross-arm claim rests on ONE arm.** 1.95 K and 2.98 K overlap (218/224/254 vs
  174/241/462) and the FIRST window is non-monotone in T. The 13.63 K arm is rising and
  yields no `tau`. So "`tau_eff` grows with temperature" is the 5.61 K arm alone — the
  one whose `tau` is least measurable.

## 22. IS ANY OF THIS WORTH IDENTIFYING? — COMPUTE BEFORE SPENDING

Signature (E) is a **sub-noise target**: the warm arm's whole `tau` discrepancy is
**2.6 % per rate**, below the best-fitting model's own 14.4 % residual and far below
the ensemble spread. It looks big only because `tau_eff` amplifies it 58x. And the
downstream discount factor at 3 % is **0.024 at 2150, 0.0012 at 2250**.

**⇒ compute the NPV sensitivity to `tau` BEFORE spending anything more on identifying
it.** If this feeds SC-GHG, a 6 % difference in the 2300 level is worth essentially
nothing. It matters for 2300-LEVEL and commitment statements per se, and for tail
statements — and those are exactly the uses where a BOUND should be quoted rather than
a point estimate. **NOT YET COMPUTED. It should be the next thing run, ahead of any
model change.**

## 23. AMPLIFICATION — BOTH REVIEWS FLAGGED IT, IT IS ALREADY KNOWN-UNRESOLVED, AND THE DIRECTION HELPS §1

`gis_amp ~ 1.92` is an ANNUAL-MEAN amplification; most Arctic amplification is winter
and does not drive melt. Melt-relevant Greenland SUMMER warming is ~**1.17x** GMT
(Bochow's own conversion). The projection shape law `S(dT)` already handles part of
this — but **`S` saturates at 0.8596 by 2.75 K and is FLAT above it**, so the effective
amp is a constant **1.650** for every T from 2.75 K to 13.63 K, and memory
[[ladrillo_gis_amp]] item 4 already says *"Trust the shape over 0.75-2.75 K;
unresolved above."* **Every arm in this analysis except ssp126 sits in the unvalidated
region**, and at 13.63 K the driver is 22.5 K.

**Direction check, which matters.** If the melt-relevant amplification is LOWER at high
T than 1.650, the regional driver at 13.63 K falls by up to ~1.4x, `L_eq` is linear in
it, so the φ=1 ceiling falls too and §1's shortfall gets **worse** (2.41x → ~3.4x).
**§1's conclusion is robust to the amplification question in the direction that
matters.** But nothing else at high T is, and this is now a blocking check rather than
a background caveat.
