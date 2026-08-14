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

### 8.3 GlaMBIE — CHECKED. Not obsolete, but its sum both duplicates AND conflicts with the gsic target

`ll += logpdf(Normal(GLAMBIE_RATE[b], GLAMBIE_SD[b]), mrate)` scores the
**2000-2024 mean rate** of `gsic_slowp` and `gsic_fast` separately, while the gsic
component channel already scores their sum annually over **1900-2023**. Measured:

| quantity | value |
|---|---|
| GlaMBIE SLOWP + FAST, implied constraint on the SUM | **0.6063 ± 0.0476** mm/yr |
| gsic channel's own grip on the same window's mean rate | σ = **0.0587** mm/yr |
| ratio (GlaMBIE σ / channel σ) | **0.81** |
| gsic TARGET (Frederikse-derived) implied rate | **+0.7292** mm/yr |
| **discrepancy** | **+0.1230 mm/yr = 2.59 GlaMBIE-σ** |
| L10 model's own 2000-2023 rate | **+0.6911** mm/yr |

Three readings, in order of importance:

1. **It is NOT obsolete.** GlaMBIE is the only term that separates SLOWP from
   FAST in the modern era; the aggregate gsic channel is blind to the partition.
   Delete it and the modern SLOWP/FAST split loses its only constraint.
2. **But its SUM component is a genuine duplicate — of comparable weight.** The
   GlaMBIE-implied σ on the sum (0.0476) is *tighter* than the channel's own grip
   on the same quantity (0.0587). The modern aggregate rate is constrained twice,
   at roughly equal strength.
3. **And the two datasets DISAGREE by 2.59 σ.** The model sits **between** them,
   69% of the way from GlaMBIE to Frederikse — the signature of a likelihood
   splitting the difference between two conflicting constraints. This is
   structurally the gate-3.1 total-vs-components conflict again, one level down.

**Consequence for D2, and it is a sequencing constraint.** `gsic` is one of the
two streams D2 puts a discrepancy term on, and it is "under load" (resid/band
1.06, BIC white − AR(1) +18.7). Part of that load may be **this target conflict
rather than model error**. A δ(t) term would absorb it and hide it — precisely
the failure mode that let Greenland's mid-century miss survive as ρ = 0.985 until
A+B exposed it. **Settle GlaMBIE before designing D2's term on gsic, not after.**

Recommended fix, and it is the move Tony already used on the conditional
weighting: re-express GlaMBIE as a constraint on the **partition** (the
SLOWP/FAST share, or their ratio) instead of two absolute rates, so it
contributes only the information the aggregate channel lacks and the sum is
constrained once. Then the Frederikse-vs-GlaMBIE level disagreement is a target
question to settle on its merits rather than something the sampler splits.

### 8.3b The covariance was checked — and it RETRACTS the 2.59 σ conflict

GlaMBIE as archived (`data/observations/raw/glambie_data.zip`, 20 per-region
calendar-year files) publishes **only** `combined_gt_errors`, a per-region
per-year σ. **There is no covariance matrix at any level** — not across years,
not across regions. So the correlation cannot be retrieved, only bracketed.

`glambie_block_stats` in `python/ladrillo_data.py` sums those errors in
**quadrature**, i.e. assumes serial independence across all 24 years and across
regions. Relaxing that:

| assumption | σ_SLOWP | σ_FAST | σ on the sum | discrepancy |
|---|---|---|---|---|
| independent years + regions (**as coded**) | 0.0165 | 0.0446 | 0.0476 | **2.58 σ** |
| correlated years within region | 0.0780 | 0.2142 | 0.2279 | **0.54 σ** |
| fully correlated | 0.1503 | 0.4697 | 0.4931 | 0.25 σ |

The inflation is **×4.72 (SLOWP) and ×4.80 (FAST)** against √24 = 4.90 — the
entire ratio is the quadrature-over-years assumption, nothing else.
`GLAMBIE_ERR_INFLATE = 1.5` covers about a third of it.

**So the 2.59 σ Frederikse-vs-GlaMBIE conflict flagged in §8.3 is RETRACTED.** It
is 0.54 σ once the errors are allowed to correlate at all, which they must. There
is no target conflict to settle — and therefore **no sequencing constraint on D2
from this**: the gsic channel's "under load" status is not explained by a
GlaMBIE-vs-Frederikse disagreement. (§8.3's other two findings stand: the sum is
duplicated, and the split is the information only GlaMBIE has.)

What replaces the conflict is a plainer defect: **the GlaMBIE absolute-rate σ was
too tight by ~4.7×**, so those two terms were over-constraining the modern
glacier rate on top of the channel that already scores it.

### 8.3c IMPLEMENTED — GlaMBIE is now a partition constraint

`calibrate_mcmc_ext.jl`: the two absolute-rate terms are replaced by **one term on
the SLOWP/FAST share**, leaving the aggregate modern rate to the gsic component
channel.

    FAST share of (SLOWP+FAST) = 0.6876 ± 0.0500

The share is the right quantity for both reasons at once — it is exactly what the
aggregate channel cannot see, and it is the combination in which the correlated
common-mode error **cancels**, so it does not inherit the σ that could not be
trusted. Same construction as the existing Mouginot surface-share term, including
its vanishing-denominator guard.

> **‼ METHODOLOGICAL CHOICE, flagged not settled — `GLAMBIE_SHARE_SD = 0.05`.**
> Propagating from the per-block σ gives **0.0296** (as-coded independent σ,
> ρ_block = 0) and **0.0493** (serially-correlated σ, ρ_block = 0.9). Those are
> the two *internally consistent* corners — errors correlated in time are
> correlated in space too — and 0.05 is the conservative end of that pair. The
> (correlated-in-time, ρ_block = 0) corner gives 0.14 but is not self-consistent,
> so it is not used. Marcus's call if he wants a different value.

**Verified.** `--glambie-absolute` restores the two-term form and reproduces the
pre-change likelihood **bit-identically** (max|diff| = 0 over all 57 chain
columns, 2000 iterations, seed 2026), so the shipped L10 configuration stays
exactly reproducible. The share form shifts `log_post` by **+5.51** at the shared
start — the intended change, not a bug.

**Consequence to state when this calibration is reported:** the modern aggregate
glacier rate is now constrained by the gsic component channel alone. That is the
de-duplication, and it is deliberate.

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
