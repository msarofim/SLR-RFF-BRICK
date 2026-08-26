# Handoff — L17 IN FLIGHT. The real finding is that `ais_runoff_Ton` IS MULTIMODAL and L15 NEVER FOUND THE MODE.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, head **`9d8b2c1`**. Written
2026-08-26 to be picked up cold. **Continues** `handoff_2026-08-25e_anchor_refuted.md`,
which continues `handoff_2026-08-25d_L15_amp_recalibration.md`.

**L14 IS STILL CHAMPION. `champions.json` UNTOUCHED.** L15 and L16 are unpromoted arms;
L17 is running. Nothing downstream has moved.

> ⚠ **ENVIRONMENT PROBLEM, ACTIVE AS OF 2026-08-26 11:40 EDT.** Partway through the session
> every **read** under this repo began failing with `EPERM: operation not permitted` — via
> `cat`, via shell redirect, and via the file-reading tool. **Writes, `ls`, `cd`, `git` and
> `ps` still work.** The shell also lost its cwd (`getcwd: cannot access parent directories`),
> so every command needs a `cd <abspath> 2>/dev/null;` prefix. Nothing in the session caused
> it; suspect a revoked macOS Full Disk Access for the terminal, or a changed sandbox policy.
> **This handoff was written from in-context values and could NOT be verified by re-reading
> the files.** Every number below is sourced to a commit — check them against the CSVs once
> reads work. If a number here disagrees with a file, THE FILE WINS.

---

## 0. THE ONE-PARAGRAPH STATE

L15 re-centred the DAIS amplification `amp` 0.945 → 1.09 and its AIS hindcast broke. The
proposed repair (free the pinned paleo anchor) was **refuted** before it was built. The
replacement arm L16 (amp σ 0.10 → 0.180) **repaired the hindcast** — but not for the reason
anyone expected, and it still does not beat L14. Chasing *why* it repaired turned up the
actual finding: **`ais_runoff_Ton` is multimodal, hindcast quality is a function of WHICH MODE
the posterior sits in, L14 and L16 sit in the same one, and L15 never found it at all.** L17
tests whether L16's residual 13% excursion out of that mode is a proposal artefact.

---

## 1. THE ANCHOR ARM IS REFUTED (commit `410f8fe`) — do not revive it

`-25d` §4 wanted `T_ant0` freed. Two cheap measurements killed it in ~15 min against a 4 h
chain. **A TRANSLATION CANNOT CANCEL A TILT:** `amp` multiplies GMST(t), `T_ant0` adds a
constant; Δamp = 0.145 tilts `T_ant` by **0.208 K across the calibration window** and the best
constant shift removes only its **0.057 K mean**, leaving a ramp. Shifting the anchor made the
hindcast **monotonically worse** (full-window bias/sd −0.139 → −0.262 at §4b's −0.077 →
−0.605 at −0.30) and the likelihood's own preferred shift is **−0.001 K**, with the L14
control passing at +0.001. Scripts: `julia/scope_ais_anchor_offline.jl`,
`julia/scope_ais_anchor_identification.jl` (the latter has `--axis=anchor|amp`).

⚠ Coverage rose 7% → 97% across that sweep **purely by band inflation** (band 0.082 → 0.426 cm)
while bias worsened. `rhat_denominator_forgives`, in the hindcast block. Both scripts now print
band width beside every coverage number. Memory: `level_cannot_cancel_slope`.

---

## 2. L16 — WHAT IT IS AND WHAT IT SHOWED (commits `d9aaff6`, `085a725`, `c65998e`)

**The change:** amp prior σ 0.10 → **0.180**, centre held at 1.09, bounds μ±3σ → [0.55, 1.63].
No source edit — `--amp-sigma=` already existed. Everything else is L15's, including
(⚠ see §4) the L15-pooled proposal. 4 × 2M, ~3h20m, acceptance 0.236–0.238.

### 2a. amp is NOT identified by the historical record

| arm | prior | post mean | shift/σ_prior | **sd / TRUNCATED-prior sd** |
|---|---|---|---|---|
| L14 | N(0.950, 0.100) | 0.9444 | −0.06 | 0.980 |
| L15 | N(1.090, 0.100) | 1.0898 | −0.00 | 0.997 |
| **L16** | N(1.090, **0.180**) | **1.0603** | **−0.17** | **0.989** |

⚠ **A PRE-REGISTERED CRITERION OF MINE WAS BADLY SPECIFIED AND IS CORRECTED HERE.** I wrote
"sd must exceed 0.10". That is mechanically guaranteed by widening the prior to 0.18 and
certifies nothing. The diagnostic quantity is sd against the **truncated** prior sd = **0.989,
i.e. NO SHRINKAGE**. Use that formulation in future.

**And the −4.81 log units did not survive the refit.** Implied effective gradient from L16's
centre shift ≈ **−0.9 per unit amp**, against ≈ **−34** measured conditionally at L14's fixed
parameters: **the refit absorbs ~97%**. That is exactly the conditional-vs-marginal caveat in
`scope_ais_anchor_identification.jl`'s header, now quantified.

### 2b. Convergence — accepted on the deliverable, and the ratio is the WORST of the three

18 marginals fail (L15 18, L14 20). Deliverable gate passes and **that pass is
denominator-driven**:

| | | L14 | L15 | **L16** |
|---|---|---|---|---|
| @2100 | R̂ / sd(medians) cm / within-chain sd cm / **ratio** | 1.017 / 0.603 / 11.80 / **0.051** | 1.002 / 1.576 / 18.37 / **0.086** | 1.002 / 2.024 / 19.33 / **0.105** |
| @2150 | same | 1.015 / 3.053 / 32.35 / **0.094** | 1.002 / 1.025 / 38.49 / **0.027** | 1.003 / 4.919 / 40.89 / **0.120** |
| ESS | @2100 / @2150 | 953 / 967 | 1514 / 1466 | **937 / 961** |

**Never quote L16 as "converged as well as L15".** On the scale-free measure it is the worst
arm at both horizons.

### 2c. The hindcast IS repaired, and NOT by band inflation

AIS hindcast RMSE (cm) — L15 → **L16** → (L14): full 0.0631 → **0.0321** → (0.0308);
1920–49 0.0396 → **0.0097** → (0.0058); 1950–92 0.0611 → **0.0091** → (0.0067);
1993–2026 0.0806 → **0.0558** → (0.0544). 1950–92 bias **−0.340 → −0.022** target sd,
coverage **7% → 98%**. `[V] AIS vs champion` mean RMSE ratio **4.884 → 1.272**.
Bias, RMSE and coverage move together — the opposite of the anchor sweep.

### 2d. But L16 does NOT beat L14

AIS module: hindcast PASS / **projection FAIL** / vs champion **WORSE**. AIS projection medians
÷ literature median (1.000 = on it):

| cell | L14 | L15 | L16 |
|---|---|---|---|
| ssp126 @2100 / @2150 / @2300 | 0.480 / 0.364 / 1.455 | 0.602 / 0.463 / 1.844 | 0.535 / 0.409 / 1.637 |
| ssp245 @2100 / @2150 / @2300 | 0.531 / 0.406 / 0.949 | 1.368 / 2.048 / 2.239 | **0.865** / 1.710 / 1.974 |
| ssp585 @2100 / @2150 / @2300 | 2.430 / 0.964 / 1.016 | 3.343 / 1.217 / 1.268 | 3.009 / 1.084 / 1.126 |

**L14 is closer to the literature on 8 of 9.** L16 wins only ssp245@2100. Verdict changes
L15→L16 were few (2 improved, 3 degraded of 309 cells); the movement is in the continuous
values.

---

## 3. ⇒ THE REAL FINDING: `ais_runoff_Ton` IS MULTIMODAL (commit `dc77cdc`)

A 0.03 shift in the amp median cannot move RMSE by 2×, so the repair is not amp.
`julia/scope_ais_ton_band_hindcast.jl` scores **2 arms × 3 COMMON T_on bands**
(LOW ≤ −18.5, MID (−18.5, −17.4], HIGH > −17.4 — KDE valley floors, not round numbers).
Its POOLED rows **reproduce the committed benchmark exactly**.

**HINDCAST QUALITY TRACKS THE BAND, NOT THE ARM.** 1950–92 bias in target sd:

| | LOW | MID | HIGH |
|---|---|---|---|
| L15 | **−0.323** | (17 draws, skipped) | −0.395 |
| L16 | **−0.328** | **−0.003** | −0.339 |

L16's LOW draws carry amp 1.066 ≈ its MID 1.054 and still score like L15 ⇒ **not amp**.

**WHERE EACH ARM SITS**

| arm | T_on p50 | sd | LOW | MID | HIGH | KDE peaks |
|---|---|---|---|---|---|---|
| **L14** | **−17.84** | **0.09** | 0.0% | **100.0%** | 0.0% | −17.88 |
| L15 | −19.19 | 2.65 | 73.7% | 1.3% | 25.0% | −19.27, −16.20, −13.93 |
| **L16** | **−17.76** | 0.53 | 7.4% | **87.0%** | 5.6% | −17.76 |

⚠ **A MID-SESSION READING OF MINE WAS WRONG AND IS RETRACTED.** From chain summary statistics
I said L16 had "dropped L15's second mode". It did not: **L16's main mode sits in L15's
VALLEY**, and the two posteriors are nearly disjoint (1.3% of L15 in L16's main-mode range,
7.4% of L16 in L15's). **L14 and L16 share a mode; L15 is the aberration.**

**median `log_post` by band** (L15↔L16 comparable up to a 0.59 amp-prior normalization that
runs AGAINST L16, so its gap is understated; L14↔L15 also carries L15's target changes):

| arm | LOW | MID | HIGH |
|---|---|---|---|
| L14 | — | **222.11** | — |
| L16 | 217.00 (−5.50) | **222.50** | 216.29 (−6.21) |
| L15 | 217.32 | 216.70 | 216.26 |

**Two consequences, both load-bearing:**
1. **L15's chains never found the high-posterior region at all** — ~5 units below everywhere.
   ⇒ `-25d` §3's "re-centring amp broke the hindcast" is **NOT ESTABLISHED**. "L15's chains
   failed" explains the hindcast, the overshoot and the bimodality together and is better
   supported. `-25d`'s headline ("right in direction and TOO LARGE") does not survive: L16
   reaches L14-comparable `log_post` at amp ≈ 1.05.
2. **L16's 13% LOW+HIGH tail is SAMPLER WANDER, not uncertainty** — 5.5–6.2 log units down,
   where it should carry ~0.4% weight. ⇒ "a wider band is more honest" holds for **amp**
   (unidentified, so prior width IS the uncertainty) and **fails for T_on**.

---

## 4. L17 — WHAT IS RUNNING (commit `9d8b2c1`)

`bash run_mcmc_L17.sh 2000000`, launched **2026-08-26 ~08:36 EDT**, 4 × 2M, seeds 2026–2029,
BLAS pinned. At 11:40 it was **3h03m elapsed with all four processes alive**; L16 took ~3h20m,
so it should have landed ~11:55. **It may already be done — check first.**

**EXACTLY ONE CHANGE vs L16: the proposal.** `--adcov` moves to **`adapted_cov_L16MID.csv`** =
the empirical covariance of L16's own post-burn-in draws **restricted to the MID band**
(348,411 of 400,000 sampled rows). **The amp prior is UNCHANGED at N(1.09, 0.180).**

⚠ **The motivation is sharper than "re-pool it":** L16 ran on
`adapted_cov_L15pool_seed2026.csv`, pooled from **L15's** chains — the arm we now know was
wandering. So L16's proposal was inflated by exactly the modes the likelihood disfavours.
`postprocess_mcmc_ext.jl`'s own comment names the mechanism.

**The deflation is surgical:** diagonal sd MID-local vs L16-pooled — `ais_runoff_Ton`
0.526 → **0.142** (ratio 0.271); `ais_gmst_amp` 0.985 (amp exploration NOT narrowed);
**median ratio over all 58 params = 1.000**. cond 3.20e12 vs pooled-L16 3.10e12 and the
L15pool file L16 actually used, 1.21e15. Positive definite.

**Gated against `nameless_matrix_order`** (the adcov format is headerless `x1..x58`): column
order was DERIVED from the chain header and asserted equal, never hardcoded; sidecar
`outputs/mcmc/adapted_cov_L16MID_columns.csv` records what row *i* is; and the smoke run's own
by-name diagonal print read back `ais_runoff_Ton 0.1422` — the MID-local value — proving the
matrix is not permuted on read. **Do that check on any future adcov.**

### ⚠ THE PREDICTION, REGISTERED BEFORE THE RUN — resolve it FIRST, in writing

> The AIS hindcast lands on L16's **MID band**: 1950–92 bias ≈ −0.00 target sd, RMSE ≈ **0.008
> cm** against L14's 0.0067; and the AIS projection cells move **partway back toward L14's**.
> **If it instead reproduces L16's POOLED numbers (bias −0.022, RMSE 0.0091), the wander is
> NOT proposal-driven** and the mode structure is a deeper problem than a seed.

### ⚠ WHAT L17 CANNOT DO
A mode-local proposal makes staying in the mode **easier**, so a tight `T_on` result is partly
**by construction** and is NOT evidence the other modes are negligible. The independent
evidence for that is the `log_post` gap measured on L16. **Report both or the result is
over-read.**

---

## 5. WHAT TO DO NEXT — exact sequence

```
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
# 0. is it done?  ps aux | grep calibrate_mcmc_ext ; ls -la outputs/mcmc/chain_L17_seed*.csv
# 1. verify the arm is what it claims (the setup prints flush LATE — see §6):
tr '\r' '\n' < outputs/mcmc/log_L17_seed2026.txt | grep -m1 "A6 prior"     # want N(1.090, 0.180)
# 2. deliverable convergence gate (writes outputs/mcmc/slr_convergence_L17.csv) -- REQUIRED
#    before postprocess will accept a run with failing marginals:
julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=L17
# 3. subsample + proposal seed:
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=L17 --accept-slr
# 4. THE PREDICTION, before anything else:
julia --project=julia_v2 julia/scope_ais_ton_band_hindcast.jl 2000 --tags=L16,L17
# 5. downstream (~15 min). ORDER MATTERS -- the --no-tap file is a REQUIRED INPUT to
#    scope_slr_fair_uncertainty.jl's [CONTROL] gate:
julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl --tag=L17
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl --tag=L17
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl --tag=L17 --no-tap
for s in ssp126 ssp245 ssp585; do julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl --tag=L17 --ssp=$s; done
python3 python/ladrillo_model_comparison.py --tag=L17
python3 python/bench_ladrillo.py --tag=L17
```
Pin BLAS on every julia call (`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`).
A ready-made runner for step 5 is at
`<scratchpad>/run_L16_downstream.sh` — copy it and swap L16→L17, or just paste the above.

---

## 6. NON-OBVIOUS STATE, TRAPS, AND OPEN QUESTIONS

* ⚠ **Reads under this repo are EPERM-blocked as of 11:40** (see the banner). Fix that first.
* ⚠ **Julia block-buffers a redirected stdout.** The chain logs OPEN with the progress bar;
  `A6 prior: ...` and the proposal-seed table appear **late** in the file. An empty-looking log
  is not a failed run. Always `tr '\r' '\n'` before grepping — the files are progress-bar CRs.
* ⚠ **`postprocess_mcmc_ext.jl` REFUSES to write** when marginals fail unless
  `outputs/mcmc/slr_convergence_<TAG>.csv` already exists AND `--accept-slr` is passed. That is
  the documented gate, not a failure. Run the convergence diagnostic first.
* ⚠ **θ0 is the MEDOID/MAP start and is COMMON ACROSS SEEDS** — the calibrator itself prints
  "R̂ is ANTI-CONSERVATIVE". True of L14/L15/L16/L17 alike. **Consequence: L14's `T_on`
  sd of 0.09 at R̂ 1.092 is UNVERIFIED COVERAGE, not established identification** — four
  chains from one start agreeing is weak evidence they covered the posterior
  (`no_power_null`). `--overdisperse` + `build_overdispersed_starts.jl` would test it; that
  is a SEPARATE arm and has not been run.
* ⚠ **`git add -A outputs/` sweeps in ~227 deliberately-untracked mcmc artifacts.** Stage by
  name. Chain CSVs are 2.3 GB each and gitignored.
* ⚠ The AIS target column of `recalib_targets_ext.csv` is **bit-identical** pre/post the L15
  target rebuild (checked: `ais`, `ais_lo`, `ais_hi` all max|diff| = 0; only `lws` 0.123 and
  `dang_closure_sig` 0.151 moved), so L14/L15/L16 AIS hindcast comparisons are like-for-like.
* ⚠ **The branch is ~80 commits ahead of `origin/ladrillo-dev` and was deliberately not
  pushed.** Do not push without asking.
* **OPEN — the amp prior decision.** amp is unidentified, so its posterior IS its prior and the
  choice is one of **provenance**: L14's N(0.95, 0.10) rests on the wrong statistic (Xie's
  sliding-window TREND ratio under a polar-cap mask, on data that was corrupt in seven files);
  L16/L17's N(1.09, 0.180) rests on two corrected CMIP6 secant ensembles (34-model 1.095 ±
  0.180; 41-model DECK 1.097). The benchmark scores fit, not provenance, and structurally
  cannot see this. **Marcus's call, not yet made.**
* **OPEN — is the MID mode the only one that matters?** The `log_post` gap says the others
  carry ~0.4% weight, so ignoring them is right to first order. But that gap was measured on
  ONE arm with a common start. An `--overdisperse` arm is the honest test.
* **STANDING RECOMMENDATION (2026-08-26):** keep L14 as champion; do NOT promote L16; decide
  the amp prior on provenance and re-run it with mode discipline — which is what L17 is.

## 7. FILES ADDED THIS SESSION

**New:** `julia/scope_ais_anchor_offline.jl`, `julia/scope_ais_anchor_identification.jl`,
`julia/scope_ais_ton_band_hindcast.jl`, `run_mcmc_L16.sh`, `run_mcmc_L17.sh`,
`outputs/mcmc/adapted_cov_L16MID.csv` + `_columns.csv`.
**Commits:** `410f8fe` (anchor refuted), `d9aaff6` (L16 launcher), `085a725` (handoff -25e),
`c65998e` (L16 result), `dc77cdc` (T_on band finding), `9d8b2c1` (L17 launcher).
**Memory:** `level_cannot_cancel_slope` (new, indexed in `INDEX_ais.md` under a new section
"The GMST->T_ant map"); `rhat_denominator_forgives` extended with the coverage instance.
