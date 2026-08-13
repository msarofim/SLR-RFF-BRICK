# Handoff 2026-08-13c — the AIS ridge hypothesis is falsified, the axis does not reach the deliverable, and threads 4 and 5 are what is left

**Self-contained pickup:** `LADRILLO.md` (the baseline definition) + this note.
It continues `handoff_2026-08-13b_amp_law_implemented.md`, which remains the
record of the amp law and the L10 deliverables.

Repo `SLR-RFF-BRICK`, branch `brick-mengel-vnext`, tip **`4ebd578`**, baseline
tag **`ladrillo-1.0`**. All six suites pass.

---

## 0. STATE IN ONE PARAGRAPH

Marcus's six questions from the review-board pass are answered except 4 and 5.
Sub-choice 1 is settled by measurement (the flat-hold is what the data support).
The `gis_beta_f` question is answered (re-bounding buys nothing; keep it free).
Thread 3 is finished and it **overturned its own premise twice**: there is no AIS
ridge to reparameterise, and the axis that fails to converge does not reach the
projection at all. What is left is thread 4 (design the next calibration) and
thread 5 (what replaces proportional relaxation at high warming).

---

## 1. WHAT THREAD 3 FOUND, and why the standing plan was wrong

### The method that mattered
Stop looking at within-chain covariance. A chain with ESS 12 on an axis **has not
moved along it**, so its own covariance describes the slice it is stuck in, not
the problem. The object that names the problem is the generalised eigenproblem
`B v = λ W v` — between-chain over within-chain covariance on z-scores — whose top
eigenvector is the direction the sampler fails to mix. `python/diag_block_ridge.py`.

### AIS: there is no ridge (commit `7c42573`)
- worst-mixing direction = **`ais_iceflow0 +1.00`**, every other loading ≤ 0.06,
  **98%** of all between-chain variance. A coordinate, not a combination.
- geometry-block within-chain correlation: **condition number 8**, spectrum
  26/17/15/14/13/11/3%, **no pair with |r| ≥ 0.8**. Nothing to rotate.
- what it IS: pooled marginal 0.65 of the prior, within-chain sd 0.49 of pooled,
  chain intervals barely overlapping, traces wandering without dwell-and-jump, and
  chain-mean `log_post` spanning **0.67 against a within-chain sd of 4.67**. A
  weakly identified, nearly flat axis, diffused along at τ ≈ 3.3e5.

**So the `ais_runoff_Ton` precedent does not apply.** The handoff plan —
"reparameterise the AIS geometry along the ridge" — was addressing a ridge that
is not there.

### And it does not reach the deliverable (commit `4f76635`)
`julia/diag_iceflow0_propagation.jl`, 400 draws/chain to 2300:

| comp | year | ratio@p50 | ratio@p95 | r with `ais_iceflow0` |
|---|---|---|---|---|
| total | 2100 | 0.009 | 0.209 | −0.004 |
| total | 2150 | 0.137 | 0.159 | −0.013 |
| total | 2300 | 0.051 | 0.095 | −0.005 |

R² < 0.001 at every horizon, and the chains agree even at **p95** — the statistic
R̂ cannot see, where the bimodal tipping tail would show if it were going to.

**Alignment control** (`julia/diag_ais_param_sensitivity.jl`), because r ≈ 0 for a
grounding-line flux coefficient is presumptively a misalignment bug:
`antarctic_temp_threshold` −0.59/−0.66/−0.65 and `ais_gmst_amp`
+0.41/+0.46/+0.47, i.e. **20× the axis**, with physically correct signs. The
kernel does resolve parameter→projection dependence. The ~0 is physics: **the AIS
projection is governed by WHEN it tips, not by how fast ice flows once it does.**

**Bonus:** 2300 checked across chains for the first time, and it is **better than
2150** (0.051/0.095 vs 0.137/0.159) — by 2300 most draws have tipped and the
distributions re-converge. `LADRILLO.md` §2 and §5.2 now say 2150 is the worst
horizon rather than the start of a worsening trend.

### Greenland: a different, milder, and fixable disease
Worst-mixing direction `gis_alpha_s +0.70, gis_beta_s +0.65` — same sign, i.e. the
LEVEL of `rate_s(T) = α_s·T + β_s`. But the widths say the chains OVERLAP:

| param | pooled/prior | within/pooled | reading |
|---|---|---|---|
| `ais_iceflow0` | 0.65 | **0.49** | chains in different places, weakly identified |
| `gis_f` | 0.30 | **0.81** | well constrained, chains overlap — just slow |
| `gis_alpha_s` | 0.19 | **0.88** | same |

**Identified but slow**, with a concrete mechanism: `gis_alpha_s` has a hard rail
at 0 and chain p05 values of 0.001 / 0.000 / 0.001 / 0.000. A random-walk proposal
against a boundary is what sticks.

### Thread 2, answered as a by-product
`gis_beta_f`'s posterior is **0.05 of its prior width** and it loads 0.10 on the
worst-mixing direction; the direction it does load on is the fast channel, which
converges. It is NOT riding a ridge with `gis_f`. **Re-bounding its prior would
change essentially nothing** — keep it free, now on measurement.

---

## 2. REVISED RECOMMENDATIONS

| was | now |
|---|---|
| reparameterise the AIS geometry block | **do nothing to the AIS sampler.** No ridge, and the axis does not reach the projection. R̂ 2.359 is a REPORTING CAVEAT. |
| (AIS, if you want it identified) | the only fix that makes it *identified* is an observational constraint on grounding-line **discharge** — the physical partner to the A5 SMB anchor. Thread 4, and optional. |
| reparameterise the Greenland slow block | **yes, but for the rail, not the ridge**: sample `(log r_s(T̄), tilt)` instead of `(α_s, β_s)`, which moves the boundary to infinity and puts the unmixed direction on its own coordinate. |
| `gis_beta_f` prior re-bounding | not worth doing. |

---

## 3. WHAT IS LEFT

### Thread 4 — design the next calibration (now the main event)
It should collect, in ONE spec so the changes do not invalidate each other:
1. **An explicit discrepancy term.** The per-series AR(1) is misspecified on all
   five streams and the total stream is **56% algebraically redundant** with the
   components *and* the loosest constraint in every window. This is now the
   highest-value change, because thread 3 removed the AIS sampler work that was
   competing for the slot.
2. The Greenland slow-channel reparameterisation (§2).
3. Optionally the discharge constraint, if AIS parameter-level inference is
   wanted — it is not needed for the deliverable.
4. Re-run `python/diag_noise_model_and_grip.py` and
   `python/diag_gis_likelihood_leverage.py` on the **L10 chains** first; both are
   currently pinned to the extC vintage and their conclusions predate A+B.

### Thread 5 — through 2300, and alternatives to proportional relaxation
Report with the `LADRILLO.md` §5 caveats (unchanged). The investigation now has a
sharper starting point than it did this morning: **the slow channel carrying the
multi-millennial commitment is exactly the one the 1900–2024 record cannot
identify**, which is the numerical fingerprint of the option-C criticism. First
concrete step: re-run `python/scope_greenland_bochow2026.py` against A+B rather
than the stock-SIMPLE Greenland it was written for (it is pinned to the extC
quarantine and says so).

### Carried, unchanged
ν sensitivity once; refit with the four glacier set-asides at prior centres; the
etymology sentence (**Marcus drafts prose**); and the branch is still named
`brick-mengel-vnext`, which no longer describes what is on it.

---

## 4. NON-OBVIOUS STATE

- **Julia SOFT SCOPE cost two runs.** A top-level `for` makes an accumulator
  assigned inside it a NEW LOCAL; `ctlmax` was then undefined at the verdict line
  and the script died right after printing its first row. I blamed memory
  pressure from a `pkill` race for two runs — plausible, because the box really
  does swap on these 2.2 GB reads, which is exactly why it went unexamined.
  Declare `global` in top-level loops.
- **Do not read the chains when a cheaper object answers the question.** The
  alignment control was re-scoped from the 4 × 2.2 GB chains to the 10 MB
  posterior subsample and ran in **8 seconds** instead of ~40 minutes.
- **Killing a redirected Julia run pollutes the log**: the dying process dumps a
  backtrace, and if a replacement truncates the same file the two interleave.
  Use a fresh log name per launch.
- `python/diag_block_ridge.py` reads 24 columns from all four chains (~5 min);
  `diag_iceflow0_propagation.jl` reads the full kernel column set (~40 min).
  Both are one-shot diagnostics, not part of any suite.
- Everything from this session is committed; nothing is pushed; `ladrillo-1.0` is
  a local tag.

---

## 5. COMMITS THIS SESSION (thread 3 portion)

| commit | what |
|---|---|
| `f98a78d` | sub-choice 1 settled; Greenland block convergence measured |
| `76bbc0a` | the Ladrillo 1.0 baseline (`LADRILLO.md`, quarantines, certificate) |
| `7c42573` | ridge hypothesis falsified; the two blocks have different diseases |
| `4f76635` | the unmixed axis does not reach the deliverable + alignment control |
| `4ebd578` | align the 2150 caveat across `LADRILLO.md` |
