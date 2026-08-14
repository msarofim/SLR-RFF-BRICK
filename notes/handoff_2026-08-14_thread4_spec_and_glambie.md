# Handoff 2026-08-14 — thread 4 is SPECIFIED and partly built; thread 5 has a number on it

**This is the pickup document for the next session.** Read it with
`notes/spec_2026-08-14_next_calibration.md`, which is the actual work order —
this file says how we got there and what is still open. For evidence, read the
CHANGELOG entry for 2026-08-14; do not re-derive it.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip **`7604849`**, baseline
tag `ladrillo-1.0`. **All six suites pass (102 assertions). Nothing is pushed**
(161 commits ahead of origin — unchanged posture from 13d, not new).

---

## 0. WHERE THINGS STAND

Handoff 13d left threads 4 and 5. Thread 4's prerequisite is closed, its spec is
written with every decision settled, and two of its items are already implemented
in the calibrator. Thread 5's first step is done and found something.

| item | state |
|---|---|
| Thread 4 §1.0 — re-measure on L10 | **DONE** (`4093dde`) |
| Thread 4 §1.1 — the three design axes | **DECIDED by Marcus** (`6856795`) |
| Thread 4 §1.2 — Greenland slow-channel reparam | **T̄ measured and chosen** (`3fd5e61`); code change NOT written |
| Thread 4 §8 — obsolete-constraint audit | **DONE**, 3 findings (`bb3d658`, `2c5465b`) |
| GlaMBIE restructure | **IMPLEMENTED + verified** (`7604849`) |
| Thread 5 — first step | **DONE**, and it is a real problem (`9665014`) |
| Thread 4 D1 + D2 — the calibrator changes | **NOT STARTED** |

---

## 1. DECISIONS ON RECORD

| # | decision | who |
|---|---|---|
| D1 | **Drop the total (`dang`) stream** from the likelihood | Marcus 2026-08-14 |
| D2 | Discrepancy term on **gsic and steric ONLY**; ais/gis keep AR(1) | Marcus 2026-08-14 |
| D3 | Measure the closure-sigma double-count first | Marcus 2026-08-14 → **moot**, see §3 |
| — | Greenland slow channel → `(log r_s(T̄), w)` at **T̄ = 1.963 K** (2015-2024 anchor) | measured, §4 |
| — | GlaMBIE → a **partition** constraint | Marcus 2026-08-14, implemented |
| — | `GLAMBIE_SHARE_SD = 0.05` | **my choice, FLAGGED not settled** — §6 |

---

## 2. FOUR THINGS THAT WERE WRONG AND ARE NOW RETRACTED

Carry these forward; they are all things a previous handoff or I asserted and the
measurement overturned.

1. **"The total stream is 56% algebraically redundant."** It is **100%** redundant.
   The 56% was a p50-level statistic contaminated by median non-additivity (it read
   −322% on L10 with the algebra unchanged). Per draw the tie is exact:
   `total_model − Σ(component_models) = gsic_tot − gsic_flow` = the R19 seam.
   **Never quote the 56%.**
2. **"A hard rail at `gis_alpha_s` = 0."** The rail is **`β_s`**. The offline A+B
   optimum sits at `α_s = 0.00708, β_s = 1e-6`; posterior draws near the `α_s`
   bound are 0.36-1.61% per chain, at the `β_s` bound 0.00-0.01%. And the
   reparameterisation **un-rails nothing** — both bounds move into the tilt.
3. **"Dropping the total breaks a live deliverable pipeline."** Mine, and wrong.
   All three `sd_dang` consumers are retired paths. I grepped for symbol
   *references*, which is not the same question as what still runs.
4. **"GlaMBIE and Frederikse conflict at 2.59 σ."** Also mine, also wrong. It is
   **0.54 σ** once the errors are allowed to correlate at all. **This removes the
   sequencing constraint I put on D2** — gsic's "under load" status is NOT
   explained by a target conflict.

---

## 3. THREAD 4 — what §1.0 changed about the spec

The prerequisite re-measurement moved two of the three design axes.

**Greenland's noise pathology was the MODULE, not the noise model.** With A+B in
the joint likelihood: `rho_gis` 0.985 → **0.789**, n_eff 0.93 → **14.85**, noise
stationary sd 0.318 → **0.025 cm**, and the cost of a 0.65 cm step over 1942-82
goes 27.7 → **311.8 logl**. The gis residual over that window is **+0.008 cm**
(was −0.822). The mechanism `diag_gis_likelihood_leverage.py` identified is no
longer loaded on the shipped model.

**Only two streams put the noise specification under load.** New discriminator
`resid sd / mean band σ` on L10: ais 0.17, **gsic 1.06**, gis 0.33 (was 1.84),
**steric 0.95**, dang 0.12. Ljung-Box still rejects every AR(1)-family member on
every stream, so the misspecification finding stands — but BIC now prefers *white*
on ais/gis/dang. Hence D2's scope.

**D3 is moot given D1.** `closure_sigma()` is referenced only in the `isdang`
branch of `make_series`, so dropping the total removes the gate-3.1 closure
inflation outright. Verified repo-wide; no other consumer.

**But note the corollary, and do not mis-sell D1.** Because the Wong weights are
already off for this arm (§5), total GMSL currently enters **exactly once** —
inside the likelihood. There is no double-count to remove. D1 is a deliberate
discard of an independent observational constraint, justified because it is the
loosest constraint in every window (σ 0.232-0.565 cm on a window-mean offset
against 0.014-0.062 for ais/gis), not because it is duplicated.

---

## 4. ITEM 1.2 — T̄ settled, code not written

`python/diag_gis_slow_reparam.py`. Reparameterise `rate_s(T) = α_s·T + β_s` as
level `ℓ = log r_s(T̄)` and tilt `w = α_s·T̄ / r_s(T̄)`; inverse
`α_s = w·e^ℓ/T̄`, `β_s = (1−w)·e^ℓ`, which keeps both non-negative for `w ∈ [0,1]`.

Mean **within-chain** |corr| over the four L10 chains:

| coordinates | mean \|corr\| | pooled |
|---|---|---|
| `(α_s, β_s)` as sampled | **0.578** | 0.319 |
| `(ℓ, w)` at T̄ = 1.169 K (hindcast mean) | 0.282 | 0.173 |
| **`(ℓ, w)` at T̄ = 1.963 K (2015-2024 anchor)** | **0.139** | 0.137 |
| `(ℓ, α_s)` at the anchor | 0.575 | 0.655 |

Scan minimum 0.135 at T̄ = 1.900 K → **the anchor is essentially optimal**; the
hindcast mean is twice as correlated. **The tilt choice matters more than T̄.**
Refit gate passes (every arm reaches the native optimum nlp 17.8559 over the same
feasible set).

**Still to build:** the calibrator change itself. Transform the priors exactly,
using `MimiBRICK.jl/calibration/compute_paleo_geo_prior_ton.jl` as the template.
Note before writing them: only **33.2%** of draws from the current `(α_s, β_s)`
priors fall inside the native bounds, so what is in force is a pair of heavily
truncated half-normals, not the N(μ,σ) the code reads as — **specify the new prior
directly in `(ℓ, w)`**, do not inherit it through the transform.

---

## 5. THE OBSOLETE-CONSTRAINT AUDIT (spec §8)

**Stripped:**
- `--gsic-early-sigma-x2` (the extB3b pre-1940 GSIC σ×2 fallback) **removed**.
  Never passed to any shipped run, and its pathology cannot recur: the cause was a
  free `gic_nu`, now fixed and not sampled, and L10 sits at σ_gsic 0.0156 /
  ρ 0.649 against the 0.032 / 0.96 signature.
- `weight_brick_conditional_fair.jl`, `weight_and_project_brick_fair.jl`,
  `compute_lB_per_post_mengel.jl` **banner-marked RETIRED**, not deleted — they
  are the provenance for the coupling-is-immaterial finding, and banner-marking is
  the house convention for superseded drivers.

**Do not touch `compute_lB_per_post.jl` or `apply_wong_weights.py` — they are
LIVE.** The pre-#93 and BRICK-2.0 arms *are* Wong-weighted; only the Mengel/FM arm
is not, because only its posterior already carries a total-GMSL likelihood term.

**Inert sweep.** `gis_amp` calibrates the instrument: inert by design and reads
**0.997** against its *truncated* prior, so **ratio ≈ 1.00 means inert**.
Near-inert: `gic_b_R19` 0.95, `gic_u_pre` 0.83, `gic_s_r5` 0.80. Two posteriors
are **wider** than their priors — `gic_log10_kappa_SLOWP` **1.24**, `_R19` **1.15**
— mild prior-likelihood tension, worth one look, not yet looked at.

---

## 6. GLAMBIE — implemented, with one flagged choice

Two absolute-rate terms → **one term on the SLOWP/FAST share, 0.6876 ± 0.0500**,
leaving the aggregate modern rate to the gsic channel that already scores it.

Why the share is right twice over: it is exactly what the aggregate channel cannot
see, **and** it is the combination in which the correlated common-mode error
cancels, so it does not inherit a σ that could not be trusted. GlaMBIE as archived
publishes **no covariance at any level**; `glambie_block_stats` sums per-region
per-year errors in quadrature, and relaxing that to within-region serial
correlation inflates σ_SLOWP **×4.72** / σ_FAST **×4.80** against √24 = 4.90.

> **‼ OPEN — `GLAMBIE_SHARE_SD = 0.05` is my choice, not Marcus's.** The two
> *internally consistent* corners are 0.0296 (independent σ, ρ_block = 0) and
> 0.0493 (correlated σ, ρ_block = 0.9); 0.05 is the conservative end. The 0.14
> corner is correlated-in-time but independent-in-space, which is not
> self-consistent, so it was not used.

**`--glambie-absolute` restores the old two-term form and is verified
BIT-IDENTICAL** to the pre-change likelihood (max|diff| = 0 over all 57 chain
columns, 2000 iterations, seed 2026). The share form shifts `log_post` by +5.51 at
the shared start.

**Loose end:** `GLAMBIE_ERR_INFLATE = 1.5` in `python/ladrillo_data.py` now has an
unclear job. It presumably compensated part of the quadrature understatement,
which the share form handles properly — so it may now be double-compensating, and
it only affects the `--glambie-absolute` path. Not resolved.

---

## 7. THREAD 5 — A+B is FLATTER at 2300 than the module it replaced

`scope_greenland_bochow2026.py`, re-pointed from the extC quarantine to
`outputs/ssps_components_2300_L10.csv` (now READ, not three hardcoded numbers).

Greenland median, cm rel 1995-2014, **L10 minus extC (stock SIMPLE)**:

| year | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| 2100 | −0.45 | +0.90 | **+4.78** |
| 2300 | **−11.37 (−59%)** | **−11.13 (−43%)** | **−9.52 (−20%)** |

A+B was chosen on its 2100 scenario spread and delivers that, but by 2300 it sits
9.5-11.4 cm **below** stock SIMPLE on every scenario. **It is not the amp law** —
the law removes 6.9% of the driver at SSP1-2.6/2300 and 14.0% at SSP5-8.5/2300, so
its damping runs *opposite* to the effect and the least-damped scenario declines
most. Versus Bochow 2026, at 2300 we are **3.1× / 3.7× / 4.3×** low (7.8/14.6/39.1
vs 24.5/54.5/167.1 cm); under SSP1-2.6 the shipped model delivers 1.6 cm of
further Greenland loss between 2100 and 2300 against a Bochow committed loss of
3.0-3.6 m SLE. Bochow's own caveats (preprint, UQ and verification concerns, code
a placeholder, 2300 5-95% spanning 4.5-140.7 cm at SSP1-2.6) are unchanged and
still binding.

---

## 8. THE OPEN QUESTION MARCUS HAS NOT ANSWERED

**Sequencing: calibrate now, or resolve thread 5's structural question first?**
Raised, not answered. The same "one change set, because each item invalidates the
posterior" logic that bundles D1/D2/1.2 applies one level up: if thread 5 concludes
the slow channel's relaxation form must change, that invalidates the new posterior
too and the calibration gets spent twice. Against that, thread 5 is open-ended and
the 2100 deliverable already shipped on L10 and is unaffected. **This is the first
thing to settle next session.**

Also open, smaller: `GLAMBIE_SHARE_SD` (§6), `GLAMBIE_ERR_INFLATE` (§6), the two
κ ratios above 1 (§5), the D2 sub-choices (GP vs low-order basis; whether ais/gis
drop to white; the δ-vs-`thermal_alpha` identifiability risk), and the branch
rename carried over from 13d.

---

## 9. NON-OBVIOUS STATE

- **Chain reads are cheap the right way.** `pd.read_csv(chain, usecols=[2 cols])`
  on a 2.2 GB chain takes **5 s**. `cut -d, -f` takes 46 s. `awk -F,` on 55 fields
  does **not finish in 2 minutes** — do not use it. This is why the two
  diagnostics went from ~40 min to 2 s and 18 s.
- **The 10k posterior subsample IS the pooled posterior for marginals.**
  `postprocess_mcmc_ext.jl` writes it as a uniform stride over the pooled
  post-burn draws; verified against a stride-100 read of all four L10 chains,
  agreement **< 0.01 posterior sd on all 11 parameters**. Prefer it to the chains
  unless the question is about between-chain behaviour.
- **Both noise/leverage diagnostics are now `--vintage {L10,extC}`**, default L10,
  with the vintage in every output path and title. `--vintage extC` reproduces the
  recorded extC numbers (27.69 vs 27.71). Their eight extC-vintage outputs moved
  into `outputs/quarantine/20260813_extc_vintage/` (README §7).
- The extC quarantine README §6 was updated: those two are **no longer pinned**.
  `scope_greenland_options.py` still is.
- `figures/diag_gis_regional_driver.png` has an uncommitted modification that
  predates this session — not mine, left alone.
- Julia `--project=julia_v2`; Python `source ~/climate-env/bin/activate`; pin
  `OPENBLAS_NUM_THREADS=1` for parallel chains (4.8× on this M4).
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
  Dated `notes/` are frozen.
- Smoke chains from the GlaMBIE recovery test were deleted; `chain_L10tune_*`
  remains deletable (keep `L10tune2`, it is the provenance of the starts file).

---

## 10. THIS SESSION'S COMMITS

| commit | what |
|---|---|
| `4093dde` | thread 4 item 1.0 — both diagnostics re-measured on L10 |
| `9665014` | thread 5 first step — Bochow vs A+B; A+B flatter at 2300 |
| `6856795` | the spec — Marcus's three calls as one change set |
| `3fd5e61` | item 1.2 — T̄ measured and chosen |
| `bb3d658` | spec §8 — obsolete-constraint audit; the D1 blocker withdrawn |
| `2c5465b` | strip the obsolete material; GlaMBIE checked |
| `7604849` | GlaMBIE — covariance checked (2.59 σ retracted), partition implemented |
