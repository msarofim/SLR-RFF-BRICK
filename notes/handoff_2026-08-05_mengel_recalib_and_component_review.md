# Handoff 2026-08-05 — Mengel glacier recalibration + a component-level review of BRICK-AM

**Self-contained pickup:** this + `CLAUDE.md` + memories `reference_mengel2016_glacier_model`,
`project_brick_mengel_vnext_recalib`, `project_facts_install_scoping`.
Branch `brick-mengel-vnext`. Two workstreams, A and B; A gates the glacier part of B.

---

## 0. Why we are stopping to do this

Marcus found (2026-08-05) that the BRICK-AM posterior's glacier module has median `gic_b = 0.89`
and produces an implausibly compressed future scenario spread — SSP1-1.9→SSP5-8.5 differ by only
**3.6 cm @2300**, against GlacierMIP/AR6 spreads of ~5–9 cm **by 2100 alone**. `b = 0.52`
(Mengel's published multi-model median) looks much better.

**That reading is right about the symptom, and the fix is one layer deeper than "set b = 0.52".**
The analysis below is new this session and refines the memory entry.

---

## 1. WHAT IS ACTUALLY WRONG — the T_lia floor, not the b ceiling

### 1.1 Three parameters rail simultaneously

`data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv`, n = 10,000:

| param | prior | bounds | posterior median | railing |
|---|---|---|---|---|
| `gic_a` | N(0.45, 0.08) | [0.32, 0.55] | **0.352** | 18.7% at the 0.32 **floor** |
| `gic_b` | N(0.52, 0.25) | [0.25, 1.00] | **0.891** | 5.5% at the 1.00 **ceiling** |
| `gic_T_lia` | N(−0.45, 0.30) | [−1.00, −0.10] | **−0.965** | 31.8% at the −1.00 **floor** |

Coordinated railing of three parameters is a degenerate direction being pushed against the box,
not three independent prior misspecifications.

### 1.2 The historically identifiable quantities are NOT `a·b`

With `T_lia ≠ 0` the model's response to history is governed by two combinations, both tight:

| quantity | expression | posterior median | CV |
|---|---|---|---|
| slope at present-day baseline | `a·b·exp(b·T_lia)` | 0.1329 m/K | **11.2%** |
| committed melt already at T=0 | `a·(1 − exp(b·T_lia))` | 0.1999 m | **12.0%** |
| (naive "slope") | `a·b` | 0.3131 | 14.5% |

Two constraints, three parameters → exactly one unidentified direction. History cannot close it.

### 1.3 The binding constraint is the committed-melt demand

The fit needs **~0.20 m of committed (disequilibrium) melt** at 1850 to reproduce the
early-20th-century glacier contribution. At the prior means (a = 0.45, b = 0.52, T_lia = −0.45)
the model can only deliver **0.094 m — short by 2.1×**. It cannot get there anywhere near the
centre of its own box.

Blocked at `T_lia = −1.00`, the sampler buys the missing commitment the only other way available:
shrink `a` toward its floor and inflate `b` toward its ceiling. **The inflated `b` is a
side-effect, not the disease.**

### 1.4 Solving all three constraints jointly

Pin `a` to inventory self-consistency (see §1.5) and solve for the rest:

```
a     = 0.479 m      (vs posterior 0.352;  Mengel published median 0.47)
b     = 0.476 /K     (vs posterior 0.891;  Mengel published median 0.52)
T_lia = -1.134 K     (vs posterior -0.965; CURRENT LOWER BOUND IS -1.00)
```
Reproduces both historical constraints exactly (slope 0.1329, committed 0.1999).
**The self-consistent solution sits just outside the `T_lia` floor.** Widen that one bound and
`a` and `b` should relax to near their published values on their own — no hand-set `b`.

Saturation of `S_eq` (the thing that wrecked the spread):

| ΔT | posterior (a .35, b .89, T_lia −.97) | self-consistent |
|---|---|---|
| 1.3 K | 86.7% | 68.6% |
| 2.0 K | 92.9% | 77.5% |
| 3.0 K | 97.1% | 86.0% |
| 5.0 K | 99.5% | 94.6% |

### 1.5 An independent check that `a` is too small — the inventory test

Forward-integrating the 2-τ module on the posterior draws (SSP2-4.5) gives cumulative glacier
SLE since 1850 of **S(2020) = 0.159 m [0.140, 0.184]**. So implied *remaining* glacier ice is
`a − S(2020)` = **0.192 m**, while the module's own `gic_a` floor of 0.32 m is *the Farinotti 2019
present-day inventory*. **98.6% of posterior draws have already spent ice they should still have.**

Self-consistency requires `a ≈ S(2020) + present-day inventory ≈ 0.159 + 0.32 = 0.479 m` — which
is where §1.4's solution came from, and is essentially Mengel's published `a = 0.47`.

### 1.6 The `b = 0.52` counterfactual is a valid DEMO but NOT a valid calibration

The side session's arm held each draw's `a·b` and set `b = 0.52`. Because `T_lia ≠ 0`, holding
`a·b` does **not** hold the historical fit: it raises the true slope@0 by **+42%** and committed
melt by **+17%**, and drives `a` to 0.60 m — above both the 0.55 bound and Mengel's own 0.546 max
(74% of draws). Keep `outputs/ssps_gsic_2300_mengel_b052.csv` as the sensitivity demonstration
that the spread is b-driven; **do not adopt it as a posterior.**

---

## 2. WORKSTREAM A — recommended approach to Mengel calibration

Ordered cheapest-first; each step is a decision point, not a foregone conclusion.

### A0. Confirm the diagnosis before recalibrating (~1 h, no MCMC)

Offline in python on the existing posterior — no BRICK runs needed:
1. Profile the likelihood along the degenerate direction: fix `(slope@0, committed)` at their
   posterior medians, sweep `T_lia ∈ [−2.5, −0.1]`, and at each point solve for `(a, b)`. Plot
   the implied `a`, `b`, and the inventory residual. **Prediction: a single well-behaved curve
   crossing inventory-consistency near T_lia ≈ −1.1 to −1.2.** If instead it is flat or
   multi-valued, the story in §1 is wrong and stop.
2. Re-run the same profile with the *early-20th-century* target removed. **Prediction: the
   committed-melt demand collapses and the railing disappears** — which would confirm that the
   early-20th-c fit is what drives everything.

### A1. Widen the `T_lia` prior — the primary fix

The bound, not the data, is binding. `T_lia` is the *glacier-equilibrium* (LIA) temperature in
**global-mean** units, so −1.13 global-mean encodes glacier-relevant LIA cooling ~3× the global
mean. That is physically arguable (mountains/seasonal amplification, and the memory already flags
"a GLOBAL-mean LIA offset may understate the regional/seasonal-amplified glacier-relevant LIA
cooling") **but it needs a citation, not an assertion.** Action: pull an actual LIA
reconstruction (PAGES 2k global; a glacier-region composite if one exists) and set the prior from
it. **Do not simply widen the bound to whatever admits the answer we want** — that is fitting the
prior to the result.

### A2. Add the missing external constraint on `a` — the principled fix

Memory already records: *"Total Mengel glacier ice has NO external likelihood constraint."* That
is the actual hole. Add a likelihood term

```
a − S_model(t_obs)  ~  N(V_inventory, σ_inventory)
```

with Farinotti 2019 global glacier volume and its stated uncertainty (**look up the number and
its exclusions — peripheral Greenland/Antarctic glaciers in or out — do not reuse 0.32 from
memory without checking what it covers**). This closes the third constraint *with data* rather
than with a prior guess, and it is the step that makes `b` identified rather than assumed.

**Recommendation: do A1 and A2 together.** A2 alone still leaves `T_lia` railed; A1 alone leaves
`a` unconstrained by anything external.

### A3. Consider a high-warming anchor — only as a check, initially

The deeper problem is that history samples only ΔT ∈ [0, 2] K, where the model is near-linear, so
curvature is unconstrained by construction. A GlacierMIP2/3 anchor (glacier loss at 2100 under a
high scenario, or GlacierMIP3 committed/equilibrium loss at fixed warming levels) would constrain
`b` directly.

**Methodological choice — flagging, not resolving.** Using projections as *likelihood* changes
what BRICK-AM is: it stops being a purely historically-constrained model and inherits GlacierMIP's
structural assumptions. Marcus's framing ("BRICK is meant to be mainly a historically constrained
model with good physics, but we can use projections comparisons to figure out where we need to add
additional physics") points to using it as a **diagnostic**, not a constraint. My recommendation
is to keep A3 out of the likelihood and use it in Workstream B as the evaluation target — but this
is your call and it materially changes the product.

### A4. Structural alternative if A1+A2 fail

If the committed-melt demand still cannot be met with physical `(a, b, T_lia)`, the honest reading
is that a single LIA-offset equilibrium is the wrong device for early-20th-century disequilibrium
melt, and the ~0.20 m is absorbing missing physics. Candidates: an explicit initial-disequilibrium
state `S(1850) ≠ 0` decoupled from `S_eq` (i.e. free `gic_sl0`, currently **fixed at 0.0** and not
sampled), or a glacier-area/volume feedback so the reservoir shrinks as it melts. Free `gic_sl0`
is the cheap first test and is worth running even in A0.

### A5. Re-run and re-accept

`calibrate_mcmc_ext.jl` with the revised priors; 4 chains over-dispersed; gate on the deliverable
(SLR R̂ @2100/@2150) per the standing rule, not on nuisance marginals; pass `maxlag=size(arr,1)`
to `ess()`. Then regenerate the glacier projection figure and re-check the spread. **Everything
downstream of the posterior must be re-run and the old posterior quarantined** — including the
CH₄/CO₂ pulse arms finished this week, which use `extA108`.

---

## 3. WORKSTREAM B — component-level review of BRICK-AM

Two axes, as Marcus framed it: components vs **history** (does it fit what we know) and components
vs **other projections** (where does it need more physics). The glacier finding above is exactly
what this review is for, found by accident; the point of B is to do it systematically for AIS,
GIS, TE and LWS too.

### B1. Historical, component by component

Machinery exists: `julia/diag_component_hindcast.jl`, `python/plot_component_hindcast.py`,
targets in `outputs/recalib_targets_ext.csv` (AIS/GIS Frederikse+GRACE-FO; GSIC Frederikse+GlaMBIE;
steric Frederikse+NOAA NCEI; total Dangendorf+STAR). Refresh on the **current** extA108 posterior
and report per component: bias, trend bias over 1900–1950 / 1950–1993 / 1993–present, and whether
the posterior band covers the obs band. Known open items to re-check rather than rediscover:
AIS overshoot at 1900, GSIC H1/H2 undershoot, TE −1.64 cm at 2018 (see the component-bias memories).

### B2. Projections, component by component — the new work

Compare BRICK-AM per-component projections at 2100 / 2150 / 2300 for SSP1-2.6 / 2-4.5 / 5-8.5
against, per component:

| component | comparison targets |
|---|---|
| Glaciers | GlacierMIP2 (Marzeion 2020), GlacierMIP3 (committed), AR6 Ch9 |
| GrIS | ISMIP6 (Goelzer 2020), AR6 Ch9 |
| AIS | ISMIP6 (Seroussi 2020), LARMIP-2, AR6 Ch9 (incl. the low-confidence branch) |
| Thermosteric | CMIP6 / AR6 Ch9 |
| Total | AR6 Ch9, FACTS, and our existing MAGICC comparison |

**FACTS is the highest-leverage target** — it is already installed and engine-validated on the M4
(Colima, arm64, 272 MB global-only module data; memory `project_facts_install_scoping`, next step
recorded as `global.coupling.ssp245`). It emits AR6-consistent **component-resolved** distributions,
so it gives all five rows in one consistent framework rather than five separate literature digs.
Suggested first move: run `global.coupling.ssp245`, then the SSP1-2.6 and SSP5-8.5 equivalents.

Report per component: median and 17–83% at each horizon, ours vs theirs, plus the **scenario
spread** (the diagnostic that caught the glacier bug — a compressed spread is the signature of a
saturated or otherwise insensitive module).

### B3. Turning findings into physics

The output of B2 should be a ranked list of where BRICK-AM is out of family and *why*, e.g.
"glacier spread compressed → equilibrium saturates too early → `b`/`T_lia`/inventory (Workstream A)",
"AIS median below ISMIP6 under high forcing → check the amplification secant and the tip channel".
Only then decide what physics to add. Resist adding physics to close a gap before the gap is
attributed.

---

## 4. Sequencing, and what it costs downstream

1. **A0** (offline profile, ~1 h) — cheap, and it can falsify §1 before any MCMC.
2. **A1 + A2** (priors + inventory likelihood) → **A5** re-run. This produces a **new posterior**.
3. **B1** on the new posterior; **B2** can start now on extA108 in parallel, since the non-glacier
   components are unaffected by the glacier fix.

**Downstream cost of a new posterior — decide before launching A5.** `extA108` is the basis for
this week's completed CH₄/CO₂ pulse work (all six arms, the headline metric table, the
`_pr` outputs) and for the MAGICC/FACTS cross-model artifact. A glacier-only change should barely
move the *pulse marginals* (glaciers are ~1–1.5% of the marginal — AIS is ~80%), but it will move
the *levels* and the glacier component everywhere. **Recommendation: re-run the pulse arms only
after A5 lands, and quantify the delta rather than assuming it — the CH₄/CO₂ headline is a
ratio of marginals and is likely robust, but that should be measured, not asserted.**

---

## 5. Open choices — do NOT resolve silently

1. **A3: are projections allowed into the likelihood?** (§A3) — changes what BRICK-AM *is*.
   My recommendation: no; use them as the evaluation target in B2.
2. **The `T_lia` prior source** (§A1) — needs a real LIA reconstruction, and the global-mean vs
   glacier-relevant amplification is a modelling decision.
3. **Farinotti inventory scope** (§A2) — peripheral Greenland/Antarctic glaciers in or out; this
   shifts the target by a non-trivial amount and must match what the module's `a` represents.
4. **Free `gic_sl0`?** (§A4) — currently fixed at 0.0. Freeing it changes the meaning of the
   committed-melt term.
5. **Carried over, still open:** the tip-classifier threshold and the GWP basis for per-gas levels
   (from `handoff_2026-08-03`).

---

## 6. State at handoff

- Working tree `brick-mengel-vnext`: the side-session glacier scripts are **uncommitted** —
  `julia/project_ssps_gsic_2300{,_mengel}.jl`, `python/plot_ssps_gsic_wr_vs_mengel.py`,
  `figures/ssps_gsic_wr_vs_mengel_2300.png`, `outputs/ssps_gsic_2300*.csv`. Commit them before
  starting A, so the counterfactual demo is reproducible.
- CH₄/CO₂ pulse work from 2026-08-03 is complete and committed; nothing is running.
- The §1 numbers here were computed this session from the extA108 posterior; the profiling in A0
  is the check that they generalize beyond the medians.
