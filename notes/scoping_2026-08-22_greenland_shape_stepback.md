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
