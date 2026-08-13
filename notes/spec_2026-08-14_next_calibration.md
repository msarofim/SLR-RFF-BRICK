# Spec 2026-08-14 — the next Ladrillo calibration, as ONE change set

Thread 4 of `handoff_2026-08-13d_threads_4_and_5.md`. Written after item 1.0
(re-measurement on L10) closed, because two of the three design axes moved once
the numbers were current — see `note_2026-08-14_thread4_item10_l10_remeasure.md`
and the CHANGELOG entry for 2026-08-14.

**Why one spec.** Each change below invalidates the posterior. Shipping them
separately means three calibrations. Nothing here is started piecemeal.

**Status: NOT STARTED.** This is the design. One decision (§4, `T̄`) is still
open and blocks §4 only.

---

## 1. Decisions on record

| # | decision | who / when |
|---|---|---|
| D1 | **Drop the total stream** from the likelihood | Marcus, 2026-08-14 |
| D2 | Discrepancy term on **gsic and steric only**; ais/gis/dang stay on the incumbent AR(1) | Marcus, 2026-08-14 |
| D3 | Target sigmas: **measure the closure-sigma double-count before deciding** | Marcus, 2026-08-14 |
| D4 | `gis_amp` keeps being sampled, and the spec says why | handoff §1.4 |
| D5 | AIS discharge constraint is **OUT** of this pass | handoff §1.3 |

---

## 2. D1 — drop the total stream

### What it is
`calibrate_mcmc_ext.jl` line 749: `hetero_logl_ar1(tot_full[S.dang.myi] .+
lws_dang .- S.dang.obs, σn[5], ρn[5], S.dang.ϵ)`. Delete that term and the
`sd_dang`/`rho_dang` parameters with it.

### Why it is defensible
The tie to the components is **exact per draw**, not approximate:
`tot_full = ais + gsic_tot + gis + te` scored with observed LWS added, against a
gsic COMPONENT channel that scores `gsic_flow` (hindcast scope). So
`total_model − Σ(component_models) = gsic_tot − gsic_flow` = the R19 seam,
exactly. The stream contributes one model term, the observed LWS, and its own
likelihood weight — and §E of the noise diagnostic shows it is the **loosest
constraint in every window** (σ on a window-mean offset 0.232-0.565 cm, against
0.014-0.062 cm for ais and gis on L10).

**The "56% redundant" figure is retired.** It was a p50-level statistic
(55.9% on extC, −322% on L10, algebra unchanged) contaminated by median
non-additivity. Do not quote it.

### Three consequences, all of them wanted

1. **The budget-closure sigma disappears with it, and D3 becomes moot.**
   `closure_sigma(ri)` is referenced *only* in the `isdang=true` branch of
   `make_series` (line 273-276). Drop the total channel and the gate-3.1 closure
   inflation has nowhere to apply. The Frederikse +0.74 cm non-closure over
   1950-1980 stops being represented as uncertainty because the conflict it
   described — components vs independent total — no longer has a channel.
   **D3's measurement should therefore be run as a check on this reasoning, not
   as an input to a sigma re-derivation**: if the closure sigma turns out to be
   doing work somewhere else, that invalidates this paragraph.

2. **R19 loses its only sea-level-timeseries constraint.** The R19 block is
   excluded from `HIND_BLOCKS`, so it has no gsic-component term and no GlaMBIE
   modern-rate term. After the drop it is constrained by its GlacierMIP3 rung
   likelihood, the A2 inventory term, and its priors — nothing else.
   **Measured, and it is cheap:** posterior sd / prior sd on the L10 subsample —

   | | `gic_a` | `gic_b` | `gic_T_off` | `gic_log10_kappa` | `gic_amp` |
   |---|---|---|---|---|---|
   | **R19** | 0.89 | **0.95** | 0.67 | 1.15 | 0.54 |
   | SLOWP | 0.86 | 0.25 | 0.79 | 1.24 | 0.77 |
   | FAST | 0.78 | **0.09** | 0.32 | 0.89 | 0.61 |

   R19 is already prior-and-rung dominated (`gic_b_R19` ratio 0.95 against
   FAST's 0.09), so the total channel was contributing little to it.
   **Caveat, stated because the statistic cannot separate the two readings:**
   a width ratio cannot distinguish "the total constrains R19 weakly" from "rung
   + inventory already do it and the total adds nothing on top". Both support
   the drop; neither proves it. The decisive test is in §7.

3. **`sd_dang` / `rho_dang` leave the parameter vector.** 54 → 52 sampled
   parameters. The starts file and `adapted_cov_*` seed must be rebuilt, not
   sliced by position — the positional-index trap is already on record.

---

## 3. D2 — a discrepancy term on gsic and steric only

### The evidence for the scope
The misspecification finding is unchanged on L10: Ljung-Box rejects **every**
member of the AR(1) family on **every** stream (p = 0.0000 throughout, against
p = 0.84 on the machinery's own self-test). But the streams differ completely in
whether the noise model is doing any work. Residual sd over mean band σ, L10:

| stream | ratio | BIC: white − AR(1) |
|---|---|---|
| ais | 0.17 | −4.2 |
| **gsic** | **1.06** | **+18.7** |
| gis | 0.33 (was 1.84 on extC) | −2.5 |
| **steric** | **0.95** | **+108.0** |
| dang | 0.12 | −3.8 (dropped anyway, §2) |

Only gsic and steric have residuals that approach their own observation bands.
On the other three the likelihood is band-dominated, white is marginally
*preferred* to AR(1), and a δ(t) with its own covariance would add parameters the
data barely see.

**Greenland is off this list because the module fixed it, not the noise model.**
`rho_gis` 0.985 → 0.789, n_eff 0.93 → 14.85, noise stationary sd 0.318 → 0.025
cm, and the cost of a 0.65 cm systematic step over 1942-1982 went 27.7 → 311.8
logl. The mechanism `diag_gis_likelihood_leverage.py` identified is no longer
loaded on the shipped model.

### Open sub-choices inside D2
1. **Functional form** — GP with a stationary kernel, or a low-order basis
   (polynomial / spline in time). The basis is cheaper and its dof are countable;
   the GP is the standard answer and does not require choosing a knot count.
   *Recommendation: fit both on the two streams offline before committing, the
   way the glacier cells were settled offline before the sampler saw them.*
2. **What happens to the existing per-year band σ.** δ(t) must be added to, not
   replace, `diag(ε²)` — the band is a genuine observation error. Watch for the
   δ term simply re-absorbing what AR(1) used to.
3. **Do ais and gis keep a sampled AR(1) at all,** or drop to white? BIC says
   white is marginally better on both. Dropping two σ/ρ pairs is a further
   simplification, but it is a change we do not have to make and it is not
   forced. *Recommendation: keep AR(1) on them; changing it buys nothing
   measurable and costs comparability.*
4. **Identifiability against the model parameters.** A discrepancy term on steric
   competes directly with `thermal_alpha`, which currently sits at 0.0986 cm per
   10²² J against 0.1043 observed — i.e. slightly low, with a `+0.281 cm` mean
   steric residual. δ(t) could absorb exactly that level offset and leave
   `thermal_alpha` free to wander. **This is the main risk in D2 and needs a
   prior on δ that is centred and tight enough not to swallow a level offset,
   or an explicit `thermal_s0`.**

---

## 4. Item 1.2 — Greenland slow-channel reparameterisation

Sample `(log r_s(T̄), tilt)` instead of `(α_s, β_s)`, where
`rate_s(T) = α_s·T + β_s`. Two things at once: it moves the hard rail at
`α_s = 0` (chain p05 values are 0.000-0.001, and a random-walk proposal against a
boundary is what sticks) out to infinity, and it puts the measured non-mixing
direction — the *level* of the slow rate — on its own coordinate.

- Priors are currently written on `(α_s, β_s)` in `calibrate_mcmc_ext.jl`.
  Transform them exactly, using
  `MimiBRICK.jl/calibration/compute_paleo_geo_prior_ton.jl` as the template — it
  did this when `(h0, c)` became `(T_on, c)`.
- The FAST channel converges fine; leave it alone unless there is a reason.
- Labels and filenames derive from the `T̄` constant, per the house rule.

> **OPEN DECISION — blocks this section only.** `T̄` must be chosen explicitly:
> the **hindcast-mean regional anomaly**, or the **2015-2024 anchor**. They are
> not equivalent — the anchor sits far above the hindcast mean, so it changes
> what "the level of the slow rate" means and therefore what the prior on
> `log r_s(T̄)` is asserting.

---

## 5. D4 — `gis_amp` stays sampled, and here is why

`gis_amp` is **likelihood-inert**: the calibrator runs to 2026 and the amp law is
inert over the observed years (asserted in the test suite). Yet it is sampled.
That is correct and deliberate: it is the dominant control on the 2100 Greenland
projection (the posterior's spread-vs-amp slope is 4.89 cm per unit with the law
on) and its prior N(1.92, 0.32) is the honest uncertainty. Sampling an inert
parameter propagates that prior into the projection instead of freezing it.
Stated here so it is never "fixed" as an apparent redundancy.

---

## 6. Owed, and folded into this pass

- **ν sensitivity, once.** Owed since the extC glacier block was specified with
  ν fixed at the anchored value.
- **The refit with the four glacier set-asides at prior centres.** Owed.

---

## 7. Verification, before any production chains

1. **Rebuild, don't slice.** New starts file and `adapted_cov` seed from names,
   not positions.
2. **The decisive R19 test for §2.** A short chain with the total dropped, and
   compare the R19 marginals against L10's. If they move materially, the width
   ratios in §2 were the wrong reading and the drop needs an R19 replacement
   term before production.
3. **D3's measurement**, run as the check described in §2.1.
4. **Mutation-test the new gates.** A δ(t) term with no effect would look exactly
   like a δ(t) term that is working. Perturb it and require the likelihood to
   move.
5. **The six suites** (`./run_ladrillo_tests.sh`) at every step.
6. **Convergence on the deliverable**, per the accepted-on-deliverable criterion.
   `ais_iceflow0` will still fail its marginal R̂ and that is a reporting caveat,
   not a blocker — thread 3 established it explains R² < 0.001 of the projection.

---

## 8. NOT in this spec

- The AIS grounding-line discharge constraint (D5). It would make `ais_iceflow0`
  identified but buys nothing for the deliverable, and the area convention that
  bit the SMB anchor (12.295e6 km² grounded vs DAIS's 10.92e6 km² disc, factor
  0.888) applies again.
- **Anything about what replaces proportional relaxation at high warming.** That
  is thread 5, it is now a live problem with a number on it — A+B sits 9.5-11.4
  cm *below* the stock SIMPLE it replaced at 2300 — and it is a MODEL-STRUCTURE
  question, not a calibration one. Do not let it leak into this change set.
