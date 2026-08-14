# Spec 2026-08-14 — the next Ladrillo calibration, as ONE change set

Thread 4 of `handoff_2026-08-13d_threads_4_and_5.md`. Written after item 1.0
(re-measurement on L10) closed, because two of the three design axes moved once
the numbers were current — see `note_2026-08-14_thread4_item10_l10_remeasure.md`
and the CHANGELOG entry for 2026-08-14.

**Why one spec.** Each change below invalidates the posterior. Shipping them
separately means three calibrations. Nothing here is started piecemeal.

**Status: NOT STARTED.** This is the design. Every decision is now settled — §4's
T̄ was measured and chosen on 2026-08-14.

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

Sample `(log r_s(T̄), w)` instead of `(α_s, β_s)`, where
`rate_s(T) = α_s·T + β_s`, `r_s(T̄)` is the rate at the reference anomaly (the
*level*), and `w = α_s·T̄ / r_s(T̄)` is the share of that level carried by
temperature (the *tilt*). Inverse: `α_s = w·e^ℓ/T̄`, `β_s = (1−w)·e^ℓ`, which
keeps both non-negative for `w ∈ [0,1]`.

**What it buys, stated as measured rather than as motivated:** it puts the
measured non-mixing direction — the level of the slow rate — on its own
unbounded coordinate, and that halves the within-chain correlation (0.578 →
0.139). It does **not** move any rail out to infinity; see the two corrections
below. The handoff's framing of this item was wrong on the rail and right on the
level.

- Priors are currently written on `(α_s, β_s)` in `calibrate_mcmc_ext.jl`.
  Transform them exactly, using
  `MimiBRICK.jl/calibration/compute_paleo_geo_prior_ton.jl` as the template — it
  did this when `(h0, c)` became `(T_on, c)`.
- The FAST channel converges fine; leave it alone unless there is a reason.
- Labels and filenames derive from the `T̄` constant, per the house rule.

### SETTLED 2026-08-14 — `T̄` = the 2015-2024 anchor, tilt = `w`
Marcus asked for both candidates compared offline first. Done:
`python/diag_gis_slow_reparam.py`.

The two candidates, on the same driver (`t_gis_zones.csv`, zone `south`, vs
1850-1900): **hindcast mean 1900-2025 = 1.1692 K**, **2015-2024 anchor =
1.9631 K**.

**Conditioning — within chain, never pooled** (mean |corr| between the two
sampled coordinates across the four L10 chains):

| coordinates | mean \|corr\| | pooled |
|---|---|---|
| `(α_s, β_s)` as sampled | **0.578** | 0.319 |
| `(log r_s, w)`, T̄ = 1.169 | 0.282 | 0.173 |
| `(log r_s, α_s)`, T̄ = 1.169 | 0.251 | 0.423 |
| **`(log r_s, w)`, T̄ = 1.963** | **0.139** | 0.137 |
| `(log r_s, α_s)`, T̄ = 1.963 | 0.575 | 0.655 |

A T̄ scan puts the minimum at **0.135 at T̄ = 1.900 K**, so the anchor is
essentially AT the optimum (0.141) and the hindcast mean is twice as correlated.
**The tilt choice matters more than T̄:** `tilt = α_s` at the anchor scores 0.575,
i.e. no better than the coordinates we already have.

Note the pooled value for the as-sampled pair (0.319) is *half* the within-chain
value (0.578) — pooling a non-converged block hides exactly the ridge the
reparameterisation is meant to remove. Thread 3's trap, live again.

**Refit gate — PASS.** Every reparameterised arm reaches the native optimum's
nlp to four decimals (17.8559), optimising over the same feasible set. The
transform is correct.

### Two corrections to this item's premise, both measured
1. **The rail is `β_s`, not `α_s`.** The offline `A+B` optimum on record sits at
   `α_s = 0.00708, β_s = 1e-6` — it rails **`β_s`**. In the L10 posterior, draws
   within 1e-4 of the `α_s = 0` bound are 0.36-1.61% per chain, and draws at the
   `β_s` rail are 0.00-0.01%. The handoff's "hard rail at α_s = 0, and a
   random-walk proposal against a boundary is what sticks" does not describe
   either object.
2. **The reparameterisation does NOT un-rail anything.** `α_s = 0` maps to
   `w = 0` and `β_s = 0` maps to `w = 1`, so both bounds move into the tilt
   rather than disappearing; and in the refit every arm still rails `β_s`
   (i.e. `w ≈ 1`). What it buys is the LEVEL — `ℓ` is unbounded, and the level is
   the direction the chains do not mix along. Claim the conditioning gain, not
   rail removal.

### One thing to settle when the priors are written
The induced prior runs the OTHER way from the posterior: transforming the current
`(α_s, β_s)` priors gives |corr(ℓ, w)| = **0.102** at the hindcast mean but
**0.315** at the anchor. Posterior conditioning should win — the priors are
documented as "wide enough to be effectively uninformative" — but this is a
reason to **specify the prior directly in `(ℓ, w)` rather than inherit it through
the transform**. Supporting fact: only **33.2%** of draws from the current
priors fall inside the native bounds, so what is actually in force today is a
pair of heavily truncated half-normals, not the N(μ, σ) the code appears to
state. Do not carry that shape across by accident.

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

## 8. Obsolete-constraint audit (Marcus, 2026-08-14)

### 8.1 D1 has no live downstream consumer — a raised blocker, withdrawn
`sd_dang`/`rho_dang` are referenced by three scripts
(`weight_brick_conditional_fair.jl`, `weight_and_project_brick_fair.jl`,
`compute_lB_per_post_mengel.jl`), and this was briefly raised as a blocker on D1.
**It is not.** All three are retired paths for this lineage:

- The **conditional FaIR↔BRICK weighting** was measured immaterial on levels
  (COUPLED 46.68 vs INDEP 46.38 cm total@2100) *and* on pulse marginals (mean
  ratio 1.003-1.009, TE 1.000). On record: "Independent pipeline stands
  everywhere; conditional weighting closes as a documented consistency check."
- The **Wong importance weights** are already OFF for this arm.
  `research_plan_2026-07-09_ch4co2_slr_paper.md` §weighting: "Mengel/FM arm
  equal-weighted (its posterior is already MCMC-calibrated to Dangendorf — Wong
  would double-count)", and `handoff_2026-08-01_brick_fair_consistency.md`:
  "Tony excluded the Mengel arm from global Wong-weighting for this reason."

Lesson for the next audit: grepping for symbol *references* finds call sites, not
live paths. Both must be checked.

**But note what this implies for D1, and state it deliberately.** Because the
Wong weights are already off, total GMSL currently enters the Ladrillo lineage
**exactly once** — inside the likelihood. There is no double-count to remove.
D1 therefore leaves total GMSL constrained *only* through the components summing.
That is defensible (it is the loosest constraint in every window, and the
components determine the total exactly up to the R19 seam and observed LWS) but
it is a deliberate discard of an independent observational constraint, not a
tidy-up. Do not justify D1 as "removing a double-count".

### 8.2 `--gsic-early-sigma-x2` (the extB3b fallback) is obsolete — remove it
L10 was launched as `calibrate_mcmc_ext.jl 2000000 $s --tag=L10 --overdisperse`,
so the flag was never passed. It was the documented remedy for the extB3
wiggle-tracking pathology (σ_gsic → 0.032 cm with ρ 0.96, `gic_nu` piled at 0,
0/4 evaluation gates). That pathology's cause was removed a different way: **`ν`
is now FIXED at the anchored value and is not sampled at all** (no `gic_nu` column
in the chain header), and L10's gsic noise is σ 0.0156 / ρ 0.649 — not the
pathology signature. The σ-inflation remedy is dead code guarding a condition
that can no longer arise. Delete it, or mark it superseded with this reasoning.

### 8.3 The GlaMBIE modern-rate term overlaps the gsic component channel — CHECK
`ll += logpdf(Normal(GLAMBIE_RATE[b], GLAMBIE_SD[b]), mrate)` scores the
**2000-2024 mean rate** of `gsic_slowp`/`gsic_fast`, while the gsic component
channel already scores those same model series annually over **1900-2023**. The
datasets differ (GlaMBIE vs the Frederikse-derived component target) but the
observable and 24 years of window are shared, and the underlying glaciological
and gravimetric records overlap. This is structurally the same issue D1 addresses
for the total. **Not asserted as a double-count** — it needs the same materiality
check, and it belongs in this pass because it also touches the gsic channel that
D2 puts a discrepancy term on.

### 8.4 Inert and near-inert parameters
Posterior sd / prior sd on the L10 subsample. `gis_amp` calibrates the scale: it
is inert BY DESIGN (D4) and reads **0.997** against its *truncated* prior
(posterior sd 0.2007 vs 0.2013; means 1.9048 vs 1.9049), so **ratio ≈ 1.00 means
inert**.

| parameter | ratio | reading |
|---|---|---|
| `gis_amp` | **1.00** | inert by design — the D4 decision, now with a number |
| `gic_b_R19` | 0.95 | near-inert; see §2.2 |
| `gic_u_pre` | 0.83 | weakly identified (Option-D ledger scope) |
| `gic_s_r5` | 0.80 | weakly identified (Option-D ledger scope) |
| `gic_u_unch` | 0.65 | moderate |
| `gis_c0` / `gis_c1` / `gis_beta_f` | 0.08 / 0.12 / 0.05 | strongly constrained |

Two parameters have a posterior **wider** than their prior —
`gic_log10_kappa_SLOWP` **1.24** and `gic_log10_kappa_R19` **1.15**. That is mild
prior-likelihood tension (the κ prior is the τ50-as-prior at σ = 0.114, inside
bounds ±1.0), worth one look in this pass rather than a separate thread.

The Option-D ledger scope parameters (`gic_u_pre`, `gic_s_r5`, `gic_u_unch`) are
`likelihood_only` and may be weakly identified *by design*, the way `gis_amp` is
— that is the question to settle, not their ratios.

## 9. NOT in this spec

- The AIS grounding-line discharge constraint (D5). It would make `ais_iceflow0`
  identified but buys nothing for the deliverable, and the area convention that
  bit the SMB anchor (12.295e6 km² grounded vs DAIS's 10.92e6 km² disc, factor
  0.888) applies again.
- **Anything about what replaces proportional relaxation at high warming.** That
  is thread 5, it is now a live problem with a number on it — A+B sits 9.5-11.4
  cm *below* the stock SIMPLE it replaced at 2300 — and it is a MODEL-STRUCTURE
  question, not a calibration one. Do not let it leak into this change set.
