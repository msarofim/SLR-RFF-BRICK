# Handoff — the λ prior is priced, and MICI is outside what the model can represent

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commit `27a6229`.
Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24b_ais_phase_opened.md`, whose §5 item **1 is now CLOSED** —
all three of its sub-questions are answered. Everything in that handoff's §1, §2
and §3 is unchanged and still applies. Its §5 items 2–6 are untouched.

---

## 0. THE ONE-PARAGRAPH VERSION

The DAISfastdyn paleo prior on `antarctic_lambda` was priority 1 because it *is* the
ssp585 AIS 2300 band. It has now been taken apart three ways. **(1) Provenance is sound
but the file is not the evidence:** `param_priors.csv`'s λ row reproduces the 800,000-member
paleo ensemble's marginal to 0.018 prior sd, but as an *independent Gaussian truncated at
paleo percentile 99.10*, discarding a +0.711 skew, a deleted tail whose mean λ is 2.18× the
prior mean, and corr(λ, Tcrit) = +0.445. **(2) That functional-form error is worth ≤6% of
any band** — the parametric approximation is not where the uncertainty lives. **(3) The
*choice* of λ inside the paleo support is worth 2.18× the reported band and is one-sided
upward**, and because the response is linear in λ to 0.6 cm the question inverts exactly:
**the MICI branch needs λ 1.06–2.20× ABOVE the paleo maximum, so it is outside the
representable set, not merely outside the current band.** The open question was never the
fit; it is whether the paleo ensemble is the right evidence base at all — and that is a
methodological choice awaiting Marcus, because the between-study disagreement at 2300 is
11× our reported band.

---

## 1. WHAT WAS BUILT — `julia/scope_ais_lambda_prior.jl`

`outputs/scope_ais_lambda_prior_L14.csv`, `outputs/log_scope_ais_lambda_prior.txt`.
2000 draws (500/chain × 4), L14, ssp245 + ssp585, horizons 2100/2150/2300, AIS component,
**8 arms**. Runtime ≈ 15 min, of which ~12 is the chain read.

### 1.1 The swap is a monotone TRANSPORT, not a resample

Draw *i*'s λ becomes `Q_paleo(F_truncGauss(λ_i))`. Deterministic ⇒ **zero Monte Carlo
noise**, and every draw keeps its own value of every other parameter, so an arm-to-arm
difference is the prior change alone. A resample on 2000 draws would have confounded it
with sampling noise of the same order as the effect being measured. Tcrit's `joint` arm
uses the paleo distribution **conditional on the new λ** (nearest 2% window), reinstating
corr = **+0.4351** against the paleo **+0.4449**.

### 1.2 Three gates, all measured rather than assumed

* **[INERT]** posterior-vs-prior KS **0.0141** (λ), **0.0120** (Tcrit), 5% critical
  **0.0304** at n = 2000. The previous handoff's *"λ is exactly likelihood-inert"* was an
  inherited claim from a source-code comment; it is now a measurement, which is what
  licenses the whole no-refit route.
* **[INDEP]** max |corr(λ, any other used parameter)| = **0.047**.
  ⚠ The smoke run reported **0.618** — that is pre-burn-in and is exactly why `--maxrows`
  writes to a `_SMOKE` filename. Do not read a correlation off a smoke run.
* **[IDENT]** the control arm reproduces `diag_ais_block_propagation_L14.csv` at
  **rel 0.00e+00** on all six scenario × horizon cells.

---

## 2. THE THREE ANSWERS

### 2.1 Where `param_priors.csv` comes from — and what it is NOT

No generating script exists in this repo (one catch-up commit, `f2b0a8d`), so it was
re-derived against MimiBRICK's bundled
`data/calibration_data/DAISfastdyn_calibratedParameters_gamma_29Jan2017.nc` — 16 parameters
× 800,000 members, the **Ruckert et al. 2017** (PLoS ONE 12:e0170052) paleo calibration
under **uniform** priors on the physical parameters. Verified: `antarctic_lambda`
reproduces the marginal mean to **0.018 prior sd** and the sd to 2%; Tcrit, γ, μ, ν
likewise within 0.14 sd.

⚠ **`antarctic_kappa` (0.411 sd), `antarctic_alpha` (−0.332) and `anto_alpha` (−0.643) do
NOT match the full ensemble.** The file is therefore a **subsample**, and the statement
"these rows are the DAISfastdyn paleo marginals" is verified only for λ / Tcrit / γ / μ / ν.
**Do not extend it to the rest without re-checking** — the two-column extract at
`data/dais_paleo/` makes that cheap for λ and Tcrit only.

The prior actually sampled is `Normal(μ, σ)` **hard-truncated** to `[lo, hi]`
(`calibrate_mcmc_ext.jl:1507` for the density, `:1313` returns `-Inf` outside). It differs
from the evidence three ways — and the third one had a sign trap in it:

| | paleo evidence | shipped prior |
|---|---|---|
| λ shape | right-skewed **+0.711** | Gaussian; p99 **1.099×** low, p99.9 **1.242×** low |
| λ support | max 0.029524 | box top 0.020705 = pctile **99.10**; 7,167 members deleted, mean λ **2.18×** the prior mean |
| Tcrit location | median −15.667 | −15.591 — the fit is above the marginal at **77 of 99** percentiles ⇒ systematically *harder to tip* than the evidence |
| joint | corr(λ, Tcrit) = **+0.445** | independent |

MimiBRICK's own calibrator offers a truncated-**KDE** for exactly these rows, because
*"many of the marginal paleo pdfs are not normally distributed"*
(`create_log_posterior_brick.jl:20`). Using the empirical marginal is not a new prior; it
is the same evidence without the parametric detour.

⚠ **SIGN TRAP, and I got it wrong first.** Higher λ = faster once tipped (**+0.56** at
ssp245); higher Tcrit = **HARDER** to tip (**−0.68**). A **positive** parameter correlation
is therefore a **negative** response correlation, and reinstating it **narrows** the band
(×0.86–0.93 at 2100/2150). Reasoning from the parameter sign alone predicts the opposite.

### 2.2 The functional form is worth ≤6% — the fit is not the band

ssp585 @2300 (control median **281.19** cm, p05–p95 **252.36**):

| arm | median | spread | p99 |
|---|---|---|---|
| `lam_box` (shape only, inside the box) | −11.34 cm | ×1.003 | ×1.011 |
| `lam_full` (shape + the deleted tail) | −11.37 cm | **×1.057** | **×1.075** |
| `tcr_full` | +0.77 cm | ×1.002 | ×1.001 |
| `joint` | −11.32 cm | ×1.011 | ×1.055 |

ssp245 @2300 (control 131.35, spread 280.77): `tcr_full` **+13.58 cm (+10.3%)** — the
largest single effect anywhere — `lam_full` −5.94, `joint` spread **×0.928**.
**Nothing exceeds 6% of a band or 10.3% of a median.** If the form is fixed anyway, fix
**Tcrit first**, not λ.

⚠ **A reporting trap fell out of the envelope arms.** At **ssp245 @2100 the AIS median is
completely λ-blind** — **5.58 → 5.59 cm across the entire paleo support** — while the
spread moves **×0.198 to ×2.623**. Fewer than half the draws have tipped, so the median is
the untipped background and λ moves only the tail. A λ sensitivity read off a median at
that cell reports zero and is not zero. This is the same bimodality that made the previous
handoff use decile contrast instead of Pearson; it bites medians too.

### 2.3 The CHOICE of λ is worth 2.18× the band, and the law inverts exactly

Three **deterministic** envelope arms pin λ for every draw. They are not candidate priors —
they bound what *any* λ revision can do inside the paleo support. **ssp585 @2300 median:**

| λ | source | median |
|---|---|---|
| 0.001723 | paleo ensemble min | **104.73 cm** |
| 0.010567 | *posterior median (control)* | *281.19 cm* |
| 0.020705 | shipped prior box top | **479.20 cm** |
| 0.029524 | paleo ensemble max | **654.54 cm** |

**549.81 cm of envelope = 2.18× the reported 252.36 cm p05–p95**, and **one-sided about the
control** — down 176.5, up 373.4 (**2.12×**) — because the posterior median λ sits well
below the midpoint of its own support. Same shape as the Greenland `--tap-set` cell-choice
envelope: the larger uncertainty is the one that is not sampled, and a symmetric ± band on
it is wrong in both directions.

The response is **linear in λ to 0.6 cm over the whole support** (segment slopes 19728 and
19882 cm per unit λ, agreeing to 0.8%):

> **AIS₂₃₀₀(ssp585, median) ≈ 70.5 + 19769 · λ  cm**

Validated against the ensemble itself: inverting the control median gives λ = **0.01066**
vs the posterior median **0.01050** — 1.5%. The inversions below are a calculation, not an
extrapolation.

| AIS @2300 SSP5-8.5 | value | λ required | verdict |
|---|---|---|---|
| Coulon 2025 p05 (no MICI) | 73 cm | 0.00013 | **below** paleo min |
| our control median | 281 cm | 0.01066 | inside |
| Coulon 2025 p95 (no MICI) | 595 cm | 0.02653 | inside, near the top |
| MICI branch floor | 687 cm | 0.03119 | **1.06× above** paleo max |
| DeConto 2021 RCP8.5 @2300 = 9.6 m | 960 cm | 0.04500 | **1.52× above** |
| MICI branch top | 1355 cm | 0.06498 | **2.20× above** |

⇒ **No λ revision inside the DAISfastdyn paleo support can put this model's central
estimate into the MICI branch.** That is a structural property of the prior, not a tuning
question. Our control band **[168, 421] cm** sits inside Coulon's **[73, 595]**, displaced
high (p05 2.3× theirs, p95 0.71×) and **2.4× narrower**.

References: Coulon, Klose, Edwards, Turner, Pattyn & Winkelmann (2025) *Nat. Commun.*
**16**:10385, doi:10.1038/s41467-025-66178-w (Kori-ULB + PISM, 2×1400 runs, Bayesian
calibration on IMBIE 1992–2020, **no MICI**; it is also the source of the 687–1355 cm MICI
branch figure). DeConto et al. (2021) *Nature* **593**:83, doi:10.1038/s41586-021-03427-0.

⚠ **NOT like-for-like** (`like_for_like_forcing`): Coulon drives ice-sheet models with
CMIP6 GCM forcing on a different baseline; we drive BRICK-DAIS with FaIR-mean ssp585 on a
1995–2014 reference. **Treat that table as a placement, not a scorecard**, until the
forcing is matched.

---

## 3. THE ACTUAL OPEN QUESTION — METHODOLOGICAL, AWAITING MARCUS

**Is the DAISfastdyn paleo ensemble the right evidence base for a *future* fast-dynamics
rate?** Two things are true at once and neither settles it:

* **For it.** The paleo constraint is *independent* of the DP16 lineage — uniform priors,
  paleo data, calibrated before DP16's parameterisation entered assessment. And the
  MICI-sceptic literature cuts *toward* the low end our prior already occupies:
  Edwards et al. (2019) *Nature* **566**:58 finds MICI is not required to reproduce the
  Pliocene, the LIG or 1992–2017; Morlighem et al. (2024) *Sci. Adv.* **10**:eado7794 finds
  Thwaites would not retreat further this century under a physically-motivated calving law
  (zero calving below 135 m cliff height).
* **Against it.** The prior is being asked to represent a future MICI-style rate it was
  never fitted to, and the between-study disagreement at 2300 — **73 cm to 1355 cm** — is
  **5.2× our whole λ envelope and 11× our reported band.**

`~/.claude/CLAUDE.md` is explicit that ensemble-construction choices are not to be resolved
silently. **Options, not a recommendation:** (a) keep the paleo prior and report the
envelope alongside the band; (b) re-fit λ to a modern no-MICI target such as Coulon's
[73, 595] — note this needs λ *below* the paleo minimum to reach the p05, so it is not a
pure λ move; (c) add an explicit MICI branch as a separate, flagged deep-uncertainty arm,
since it cannot be reached by λ at all.

---

## 4. NON-OBVIOUS STATE

* **`data/dais_paleo/daisfastdyn_lambda_tcrit.csv`** (22 MB, 800k rows) is a two-column
  extract of the MimiBRICK NetCDF with the **source sha256 recorded in its README**, so the
  transport does not depend on a package-depot path that moves when MimiBRICK is
  re-resolved. Four copies of that NetCDF exist under `~/.julia/packages/MimiBRICK/*/`;
  they were not checked against each other.
* **`--maxrows=N` is a smoke mode** with `nb = 0`, i.e. it reads from iteration 1 and
  includes burn-in, and it writes to a `_SMOKE` filename. Its **[INDEP] number is
  meaningless** (0.618 vs the real 0.047). Use it to check the plumbing, never a result.
* The script **reads the chains once** and reuses them across all 8 arms and both
  scenarios, same as `diag_ais_block_propagation.jl`. Do not move the read inside a loop.
* `ARMS` is order-dependent only in that `chain` must be first ([IDENT] compares against
  it). The three envelope arms are appended, so adding a transported arm in the middle is
  safe.
* Every trap in `handoff_2026-08-24b` §3, `handoff_2026-08-24` §5, `handoff_2026-08-23f` §5
  and `handoff_2026-08-23e` §7 still applies.

---

## 5. FILES

**New:** `julia/scope_ais_lambda_prior.jl`, `outputs/scope_ais_lambda_prior_L14.csv`,
`outputs/log_scope_ais_lambda_prior.txt`,
`data/dais_paleo/{daisfastdyn_lambda_tcrit.csv,README.md}`.
**Modified:** `CHANGELOG.md`.
**Memory:** `ais_lambda_prior_envelope` (new); `INDEX_slr.md` Antarctica section and
`MEMORY.md` live-state line both updated.

---

## 6. OPEN, IN PRIORITY ORDER

1. **The methodological choice in §3** — the only thing blocking Antarctica from closing
   the way Greenland did. Needs Marcus, not more compute.
2. **`ais_runoff_Ton` (R̂ 1.092, rank 4 at ssp245) and `antarctic_alpha` (R̂ 1.777, rank 5)**
   — unchanged from `2026-08-24b` §5 item 2; still the two parameters that both fail to mix
   and reach the deliverable.
3. **Re-price at 2100 and 2150** — unchanged from `2026-08-24b` §5 item 3. §2.2's
   λ-blind-median finding at ssp245@2100 says the horizon caveat is real and compounds with
   the scenario one.
4. **The cool arms' separation residual** (ssp126 0.90×, ssp245 1.19×) — unchanged.
5. **The amp-law estimator** — unchanged.
6. **Marcus's prose** for module-memo §1 and §9, and the `2.0` tag decision — unchanged.
