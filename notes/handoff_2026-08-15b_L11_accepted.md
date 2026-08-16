# Handoff 2026-08-15b — L11 is ACCEPTED; the R19 alarm is retracted

**Pickup document.** Supersedes `handoff_2026-08-15_L11_change_set.md` for
everything in its §4 and §5.1. That document remains the authority on the change
set's DESIGN (§2), the five bugs (§3), and threads 4/5 — do not re-derive those.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**. All six suites pass.
**Nothing pushed.**

---

## 0. WHERE THINGS STAND

| item | state |
|---|---|
| `L11tune3` (shipped-D2-basis tuning) | **DONE** — acceptance 0.239 |
| `overdispersed_starts.csv` rebuilt, 57 cols | **DONE** |
| Production 4 × 2M seeds 2026-29 | **DONE** — acceptance 0.236-0.238 |
| SLR convergence diagnostic | **DONE** — R̂ 1.002/1.005 |
| `postprocess --accept-slr` | **DONE** — canonical L11 posterior written |
| R19 re-measurement (the §5.1 question) | **DONE — the alarm is RETRACTED** |
| Thread 5 (Greenland 2300) | untouched, still the one confirmed structural failure |
| L10-vs-L11 hindcast scorecard | **DONE** — see §1b |
| Deliverable FIGURES on L11 | **NOT STARTED** |

**The deliverable is `data/MimiBRICK/parameters_subsample_brick_mengel_L11.csv`**
— 10k-member subsample of 4M pooled draws, plus `outputs/mcmc/adapted_cov_L11.csv`.

---

## 1. THE HEADLINE: R19 did NOT overcorrect

The previous handoff's §5.1 said the change set pushed R19's modern rate from
~3× too high to **~9× too LOW**, and concluded the constraint pair was
unbalanced — that the rung tightening might need to be less aggressive for R19,
or GlaMBIE given more weight. **That conclusion is withdrawn.**

| posterior | R19 modern rate 2000-2024 | vs GlaMBIE |
|---|---|---|
| L10, before | 0.1490 [0.0544, 0.2300] | **+0.86σ**, 3.03× |
| D2chk3 (200k, single common-start, NOT converged) | 0.0057 [0.0000, 0.0755] | −0.38σ, 0.12× |
| **L11 production, pooled 4×2M** | **0.0229 [0.0002, 0.1298]** | **−0.23σ**, 0.46× |

0.46× is about **2.2× too low, not 9×**, and −0.23σ against L10's +0.86σ is an
improvement on both sides. **Do not do the remedial retuning §5.1 contemplated.**

Per-chain: 0.0172 / 0.0231 / 0.0235 / 0.0309 → −0.16σ to −0.28σ. **All four
chains agree**, so this is not a pooled median hiding a split — which mattered to
check, because R19 is weakly identified and `ais_iceflow0` shows exactly that
pathology in the same posterior. Cross-checked through a second code path: the
canonical 10k subsample gives 0.0242, −0.22σ, 0.49×.

**What still holds from §5.1:** the 5-95% lower bound is 0.0002 — near-zero
modern R19 melt is still admitted by the posterior.

**The lesson, worth carrying:** an unconverged 200k single chain was ~4× off on
a weakly-identified parameter, in the direction that would have triggered
unnecessary work. Its own caveat was load-bearing; obey those.

### Measure it with the committed script, not ad hoc
`julia/diag_r19_modern_rate.jl` (`e263032`). **Always pass `--check-l10`**: the
anchor asserts the L10 posterior reproduces its recorded 0.1490 [0.0544, 0.2300]
/ 3.03× at the same 400 draws, and it is the guard against the trap below.

```bash
julia --project=julia_v2 julia/diag_r19_modern_rate.jl --check-l10 --chain-glob=L11 400
```

**THE UNIT TRAP.** `ladrillo_series` returns **CENTIMETRES** (`ladrillo_rebase`
multiplies metres by 100); the calibrator's formula reads raw metres and
multiplies by 1000. From the harness the factor is **10, not 1000**. Copying the
calibrator's constant gives 14.73 mm/yr — 100× wrong, and still reads as a
plausible melt rate to anyone not checking. The rebase subtraction cancels in a
difference, so re-referencing does not enter.

---

## 1b. THE SCORECARD — D2 works; D1 has a measured price

`python/scope_l10_vs_l11_scorecard.py` → `outputs/scope_l10_vs_l11_scorecard.csv`.
Both arms from `posterior_predictive_ladrillo.jl --tag=`, same forcing, baseline,
targets, 2000 draws, noise seed. Bias = model p50 − obs (cm); coverage = 90%
PARAMETER band.

| component | Δbias full | Δcoverage full | reading |
|---|---|---|---|
| ais | +0.001 | +0.0 | untouched, as expected |
| glaciers | +0.013 | **+16.1 pts** (63.7→79.8; satellite era 35.5→**80.6**) | **D2 working** |
| gis | +0.003 | −2.4 | reparam was a conditioning fix; behaved like one |
| te | **−0.106** | +0.8 | early century much better, satellite era worse |
| total | **+0.425** | **−27.2** | **out-of-sample for L11 — this is D1's price** |

**D2 on gsic reshaped the band, not the median** — exactly what a mean-zero
discrepancy term should do (|Δbias| ≤ 0.05 cm in every window).

**D2 on steric traded eras**: 1900-1919 +0.418→+0.162, 1920-1949 +0.555→+0.348,
but 1993-2026 +0.133→**+0.216** with coverage 21.2%→15.2%. This is a second
symptom of the `thermal_alpha` = 0.16 open question (§5.2), not a new problem.

**D1's price is entirely PRE-1950.** Total bias by window, L10 → L11:
1900-1919 **+0.146 → +1.125**; 1920-1949 +0.201 → +0.918; 1950-1992 +0.300 →
+0.617; **1993-2026 +0.181 → +0.130 (IMPROVED, coverage 21.9→40.6%)**. Without
the total, nothing holds the component sum to the observed total and the sum
runs ~+1 cm high in the early record where the obs are weakest. Does NOT say D1
was wrong (its case was that the total pins R19 at a saturated state, `3a9e64b`);
it numbers the discard the spec flagged.

**TRAP, and I fell in it first:** glaciers must be scored against
`glaciers_obs_delta_corrected`, NOT the raw `glaciers_obs` — the gsic obs carry a
per-draw M15/Roe-2021 ramp on the OBS side over 1900-1959. The raw target
inflates the early-century glacier bias ~7× (+1.28 vs +0.20 cm over 1900-1919 on
L10) and reports a large spurious regression.

`posterior_predictive_ladrillo.jl` is now `--tag=`-driven; the default L10 path
reproduces its three outputs bit-identically. For an L11 posterior the total has
no calibrated error model (no `sd_dang`/`rho_dang`), so its predictive band is
NaN and `in_sample=false` is carried in the bias/coverage CSVs.

## 2. THE PRODUCTION RUN

`julia/run_l11_production.sh` — 4 × 2M, seeds 2026-29, ~2h46m each (L10 was
2h15m at 55 params; L11 samples 57 and D2 adds per-year work on gsic+steric),
acceptance **0.236-0.238**. No `--amp-mu`/`--amp-sigma`: L10 had none and the
file defaults (0.95/0.10) are canonical; extC's 1.08/0.15 is the A6 study's
prior and would silently shift the AIS amp prior, breaking the L11-vs-L10
comparison the R19 question needs. All thread vars pinned to 1 — four chains at
~98% CPU each, i.e. one core apiece.

**ACCEPTED ON DELIVERABLE**, the 2026-07-19 criterion:

- **18 marginals not converged** (L10 had 19), same compensating AIS-geometry
  ridge. `ais_iceflow0` R̂ **2.449** vs L10's 2.359.
- Projected SLR converges: **R̂ 1.002 @2100, 1.005 @2150**, ESS ~1300,
  sd(chain medians) / mean(within-chain sd) = **0.028 / 0.029**.

Pooled projected SLR, cm rel. 1995-2014:

| horizon | q05 | q50 | q95 |
|---|---|---|---|
| 2100 | 41.63 | **45.28** | 75.57 |
| 2150 | 62.64 | **70.78** | 155.29 |

**MAY / MAY NOT** — unchanged from L10 and it still applies: the posterior may be
used for projected SLR and anything derived from it; it may NOT be used for
parameter-level inference on the AIS-geometry block, whose pooled marginals are a
mixture of four chains that never merged.

---

## 3. THE BLOCKER I HIT, and why it would have hit you too

**L11's posterior could not be read by anything.** `postprocess_mcmc_ext.jl`
writes the canonical subsample with the CHAIN's column names, so an L11 posterior
carries the sampled `(gis_slow_ell, gis_slow_w)` and NO native `(gis_alpha_s,
gis_beta_s)` — and `ladrillo_gis_variant` rejects that header by design ("no
default and no fallback", which is correct: guessing would project Greenland at
whatever the model was initialised with). Every downstream consumer failed,
starting with `diag_slr_convergence_by_chain_ladrillo.jl` — **the diagnostic that
gates `postprocess --accept-slr`**. So L11 could not be accepted and no
deliverable could be projected from it.

Fixed in `d1fb9e4`, Marcus's call: **the transform derives at LOAD** in
`ladrillo_projection.jl`, so the posterior file keeps exactly the sampled
coordinates. Rejected alternatives: postprocess writing both coordinate sets (a
deliverable carrying derived columns invites someone perturbing `ell` without
recomputing `alpha_s`), or native only (loses the sampled coordinates, so you
could not check the mixing of the very reparameterisation that was adopted as a
conditioning fix).

- `ladrillo_native_greenland!` inverts the calibrator's map:
  `alpha_s = w·exp(ell)/Tbar`, `beta_s = (1−w)·exp(ell)`. Idempotent.
- `LADRILLO_GIS_TBAR` recomputed from the driver under the calibrator's own
  1.963 K assertion — the transform is wrong by exactly the ratio if they drift.
- Consumers that read chains themselves check `ladrillo_gis_needs_native(hdr)`
  and ask the file for the columns it HAS.
- **8 new gates** in `validate_gis_projection_ab.jl` §2, because all six suites
  passed throughout and never touched the new branch. The round-trip gate checks
  the map inverts to 1e-12 on θ₀'s own native pair (0.00707, 0.00100). Note the
  idempotence gate is the weak one — it can only catch a destructive
  implementation, since recomputing from unchanged (ℓ,w) gives the same values.

---

## 4. ORDERING — I got this wrong, so it is written down

`diag_slr_convergence_by_chain_ladrillo.jl` runs **BEFORE**
`postprocess_mcmc_ext.jl --accept-slr`, not after. `--accept-slr` READS
`outputs/mcmc/slr_convergence_<TAG>.csv` and refuses if absent. I ran postprocess
first; it correctly refused to write anything, which cost a full pass over 9 GB
of chains.

```bash
julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl 400 --tag=L11
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=L11 --accept-slr
```

---

## 5. OPEN QUESTIONS, in priority order

1. **Deliverable figures / the L10-vs-L11 scorecard have not been produced.**
   That is the natural next unit of work: `205f34c` built a Ladrillo-vs-BRICK 2.0
   hindcast scorecard; the L11 counterpart does not exist.
2. **`thermal_alpha` sits at 0.16** against L10's 0.150 and the
   precision-weighted steric optimum of 0.1395. D2 has NOT pulled it toward the
   steric optimum — unchanged from the tuning run, and the open question §5.2 of
   the previous handoff stands verbatim.
3. **Thread 5 — Greenland at 2300** is untouched and remains the one confirmed
   structural failure: commitment 19-24× below Bochow, unidentified along the
   φ·Leq ridge (14.6 → 58.3 cm at identical hindcast fit). Needs an external
   Leq(T) target, i.e. re-opening Option C.
4. **The glacier blocks over-commit and under-realise** (φ 0.61-0.81,
   commitments 16-76% above GlacierMIP3 in % terms though ≤0.66σ for
   SLOWP/FAST). Same shape as the Greenland ridge.
5. Branch rename, carried from handoff 13d.

---

## 6. NON-OBVIOUS STATE

- **Disk.** The four L11 production chains are **2.29 GB each (9.2 GB)**, on top
  of the 2.8 GB of superseded L11tune/D2chk chains the previous handoff flagged
  and the 8.8 GB of L10 chains. Nothing downstream reads any of them once the
  subsample and covariance exist. ~449 GB free at the time of writing, so no
  action was taken.
- `chain_L11tune3_seed2026_n1000000.csv` (1.14 GB) is the tuning chain the
  production covariance came from; `adapted_cov_L11tune3_seed2026.csv` is the
  durable part.
- The ADCOV preference chain now heads with `L11tune3`, and the nested ternary
  was replaced by an ordered candidate list (`3e5a790`).
- The L11 canonical posterior carries **`gis_slow_ell`/`gis_slow_w` only** — by
  design. Anything reading it must go through `ladrillo_posterior` or call
  `ladrillo_native_greenland!` itself.
- Julia `--project=julia_v2`; pin `OPENBLAS_NUM_THREADS=1` for parallel chains.
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
- Chains are seed-reproducible; `accept_rate`'s denominator depends on the
  requested N, so compare parameter columns only.

---

## 7. THIS SESSION'S COMMITS

| commit | what |
|---|---|
| `3e5a790` | L11tune3 tuned on the shipped D2 basis; starts rebuilt; production launched |
| `e263032` | `diag_r19_modern_rate.jl` — the R19 re-measurement, with the cm-vs-m guard |
| `d1fb9e4` | projection stack accepts the L11 (ℓ, w) coordinates; 8 new gates |
| _this_ | L11 accepted on deliverable; R19 alarm retracted; CHANGELOG + this handoff |
