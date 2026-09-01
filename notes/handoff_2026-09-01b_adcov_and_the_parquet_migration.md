# Handoff — the glacier law is inert in the likelihood, L23 lost `--adcov`, and the bulk is Parquet

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD **`5308fca`**, **PUSHED** (37.6 MB,
fast-forward). Written 2026-09-01, continuing `handoff_2026-09-01_l23_l24_and_ais_identifiability.md`.

**⭐ FIRST THING NEXT SESSION: read the L25 result.** It was still running when this was written
(~1h50m left) and it decides whether the current champion's reasoning survives. See §1.

⚠ **The other repo:** `FaIRtoFrEDI` has 9 unpushed commits on `heat-ed-morbidity` (calib 1.6.0 /
van Vuuren work) and **2 unpushed on `magicc-comparison`** (`8f882b1`, `f81b71f` — the MAGICC
wide-CSV builder and the ZJ docstring, cherry-picked off `heat-ed-morbidity` where they had landed
by accident, blobs verified byte-identical, then dropped from that branch). Neither is pushed;
Marcus has not ruled on pushing them.

---

## 1. ⭐ THE OPEN QUESTION — L25, running when this was written

`outputs/mcmc/chain_L25_seed{2026,2027,2028,2029}_n2000000.csv`, 4 chains, 2M iterations,
acceptance 0.238-0.239 against a 0.234 target, all four tracking together.

**L25 = L23's configuration with L21/L22's proposal covariance. ONE variable.**

    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 2000000 <seed> \
      --tag=L25 --gis-ordered --gis-basins2 --overdisperse \
      --amp-sigma=0.10 --adcov=adapted_cov_L14tune_seed2026.csv

⚠ **`--amp-sigma=0.10` is load-bearing.** HEAD defaults to 0.180 since `165a860`, so without it
this would be an L24 arm, not an L23 one.

**Read `ais_gmst_amp` against two reference points:** L21 **0.9455** (old covariance, old glacier
law) and L23 **1.0865** (L11tune3 covariance, new law).

* **Returns toward 0.945** ⇒ the shift was the PROPOSAL COVARIANCE. The glacier-law attribution
  quoted verbatim in all six `champions.json` entries is wrong and must be rewritten, and the
  L23 promotion needs revisiting.
* **Stays near 1.0865** ⇒ the covariance is exonerated too. Since §2 below already rules out the
  likelihood route, something THIRD is moving it and the 2x2 must be reopened from scratch.

Then: `diag_slr_convergence_by_chain_ladrillo.jl --tag=L25` BEFORE `postprocess` (which needs
`--accept-slr`). 17-19 marginals fail R-hat on every vintage; that is the documented ridge.

---

## 2. THE GLACIER LAW IS INERT IN THE LIKELIHOOD (§7.4 of the predecessor, answered)

`julia/scope_amp_likelihood_tilt.jl` + `python/scope_amp_likelihood_tilt_fit.py`, commit `f12b0b2`.

Conditional `ll(amp)` profiles at fixed theta, 41 grid points x 9 draws, under a 2x2 on the law
itself (regrowth cap R x FLOOR). **The OLD law is exactly `R=Inf` AND `FLOOR=0`** — old
`exc = max(T-T_eq,0)` zeroes the cooling step precisely as `mult /= Inf` does, and old `S_eq` was
unfloored. (R alone is NOT the old law; that was my first guess and it is wrong.)

**Result: the old and new laws differ in calibration log-likelihood by at most 7.3e-5**
(L23-region draws) **and 2.9e-5** (L21-region). **The null has power** — on the same theta a 1%
perturbation of one glacier parameter moves `ll` by up to **1.86**, and 1% of amp by **11.4**.
Four to five orders of magnitude of headroom.

⇒ The glacier law CANNOT have moved `ais_gmst_amp` through the likelihood. Structurally consistent:
D1 drops the total series, so glaciers and AIS have SEPARATE likelihood terms with no shared
channel, and over 1850-2024 the two laws are near-identical by construction.

**Dead ends — do not re-run.** (a) The TILT hypothesis (a likelihood linear in amp shifts a Gaussian
mean without sharpening it) is moot, not confirmed: there is no shift by this route. (b) The glacier
PRIOR-shift route: `gic_a/b/T_off` centres come from `outputs/extc_block_constants.csv`, NOT the
`d0_glacier_shootout.csv` that `a0155bf` did change, and it was untouched across the L21->L23 range.

⚠ Conditional at fixed theta, NOT marginal — magnitudes bound identification from ABOVE (predicted
sd ratio 0.399 vs measured 0.97 is exactly that gap). The old-vs-new comparison at identical theta
is the robust part. Measured in an INSTRUMENTED WORKTREE; the ENV-switch patch is committed at
`outputs/scope_amp_likelihood_tilt_INSTRUMENTATION.patch` so the run reproduces without editing
port-gated components.

---

## 3. WHAT ACTUALLY DIFFERED: L23 LOST THE `--adcov` FLAG

`python/diag_proposal_seed_by_vintage.py`, commits `9c2eef2` and `ab8de49`. Read out of the runs'
own `outputs/mcmc/seed_diag_<TAG>_seed<SEED>.txt`, not reconstructed.

| vintage | proposal covariance | mapping |
|---|---|---|
| L21, L22 | `adapted_cov_L14tune_seed2026.csv` | NAMED — from the FILE'S OWN header, **58 of 58** |
| L23, L23b, L24 | `adapted_cov_L11tune3_seed2026.csv` | `x1..x57` — NAMELESS, read via the hardcoded `L11_NAMES` literal, **57 of 57** |

`run_mcmc_L21.sh` and `run_mcmc_L22.sh` both pass `--adcov=...L14tune...`. **There is no
`run_mcmc_L23.sh` in the repo** — L23/L23b/L24 carry no `--adcov` and fall through to the default
list head. SECOND dropped-flag incident on this refit (§5.1 of the predecessor is the first).

**Measured consequence — the AIS-block proposal is 2.7-5.3x TIGHTER in L23/L24:** `ais_c`
3.216->0.6065 (5.30x), `ais_mu` 0.1946->0.05204 (3.74x), `ais_bedheight0` 2.90x, `ais_precip0_LOG`
2.69x; `gis_s_high` lands on its 0.05 floor, being the one live parameter with no entry in the
57-name list (L21's tuned value: 0.02699). With 17-19 marginals failing R-hat, that is a mechanism
for relocating a POOLED MEDIAN while leaving a width the PRIOR sets untouched — exactly the
shift-without-sharpening signature §7.4 asked about.

⚠ **L23b is BLIND to this.** The reproducibility replicate shares the same covariance and varied
only RNG, so its 0.0014 agreement measured noise INSIDE the defect, and the 4.93 cm between-refit
reproducibility figure inherits that.

⚠⚠ **A CORRECTION I HAD TO MAKE, and the lesson in it.** I first called this mapping "positional"
and said the L13 `ais_c` permutation had recurred. **It has not.** The `L11_NAMES` ordering bug was
FIXED in `57959ee` (2026-08-19): `d2_*` sits at rows 35-38 matching `FREE`, and the literal is
set-checked against the live layout. L23's mapping is ORDERING-CORRECT. I reached for the
permutation because this repo carries THREE adcov quarantines and L23's log line
(`name-mapped 57 of 57 rows ... dropped `) matches the quarantined signature verbatim — it matches
because a CORRECT post-fix mapping prints the same thing. **Check `L11_NAMES` against `FREE` before
alleging a permutation.** What survives is narrower: an OLDER tuning VINTAGE, plus one unmapped
parameter.

---

## 4. THE BULK IS PARQUET, AND THE OUTPUTS COMMIT IS RESULTS ONLY

**Policy (Marcus 2026-09-01): commit the code, the key results and the figures, not the
intermediates.**

| class | files | CSV | Parquet | ratio | CSVs deleted? |
|---|---|---|---|---|---|
| `wong_cond_pulse_pairs_*` | 18 | 13.21 GB | 2.73 GB | 4.8x | YES |
| `wong_cond_weights_full*` | 18 | 1.32 GB | 0.16 GB | 8.1x | YES |
| `scope_slr_fairunc_draws_*` | 96 | 0.80 GB | 0.10 GB | 8.2x | **NO** |

float32 is safe and MEASURED: max relative error 6.0e-08 per column, and the pulse deltas are
STORED rather than differenced at read time. Before deleting, the PRODUCTION statistic was compared
CSV-vs-Parquet across all 18 pulse arms (worst 1.12e-07) and `metric_horizon_table.py` was run end
to end on the Parquet. 14.53 GB reclaimed.

⚠ **REMAINING WORK: the draw-ensemble CSVs are KEPT because TWELVE scripts still read them** —
`bench_ladrillo.py`, `diag_ais_ssp126_tail_anatomy.py`, `diag_gis_width_anatomy.py`,
`diag_glacier_level_attribution.py`, `ladrillo_model_comparison.py`, `rank_uncertainty_contributors.py`,
`scope_ais_module_assessment.py`, `scope_gis_ssp126_acceptability.py`, `vv_model_comparison.py`,
`project_ssps_components_oldbrick.jl`, `scope_slr_fair_uncertainty.jl`, `scope_slr_fairunc_oldbrick.jl`.
Migrate those readers (the `pairs_path`/`pairs_read` pattern in `metric_horizon_table.py` is the
model), THEN delete. Not done mid-calibration.

**`d3fca9a` rewritten** (`fac85f3`): 741 files / 15.82 GB -> **542 files / 34.9 MB**, largest member
0.71 MB. 199 paths dropped, exactly those the current `.gitignore` matches; every kept file verified
BYTE-IDENTICAL; the 8 later commits replayed with messages and authorship preserved verbatim.
Done by PLUMBING (`read-tree`/`rm --cached`/`commit-tree` + `reset --soft`), **not rebase** — a
rebase would have deleted the still-needed draw CSVs and run logs off disk while chains were
running. Pre-rewrite tip preserved at `backup/pre-d3fca9a-rewrite-20260901`.

⚠ 113 chain CSVs >100 MB remain in `outputs/mcmc` (~148 GB). Already gitignored. A much larger
Parquet opportunity, needing its own decision — every postprocess/diagnostic reader would move.

---

## 5. STATE / GOTCHAS

* **L25 runs from a FROZEN WORKTREE** at `.../scratchpad/adcovwt` (detached at `eb606e6`), with
  `outputs/` and `data/` symlinked to the live repo. That is why the history rewrite above was safe
  to do mid-run. **Remove it when the chains finish:** `git worktree remove --force <path>`.
* **`--tag=AMPPROF` and `--tag=L25smoke`** left `seed_diag_*` and one 4000-row chain in
  `outputs/mcmc/`. The smoke is the §5.1 flag gate's evidence (60-column header diffed IDENTICAL to
  L23, 8 AIS scales matched L21) — keep it.
* **macOS bash 3.2**: no `wait -n`, `pgrep -fc` is not a flag, no `timeout`, no `tac`. All bit me.
* **`git check-ignore` skips TRACKED paths** — use `--no-index` to test patterns against a commit's
  file list, or it silently reports almost nothing.
* **`awk 'BEGIN{RS="\\0"}'` enters PARAGRAPH mode** and eats every blank line; it silently mangled
  8 commit messages before I caught it. Use `"$(git log -1 --format=%B)"` — command substitution
  strips only trailing newlines.
* Untouched from the predecessor: the skewed-amp prior (see below), L24's pipeline/benchmark, the
  phantom `wf*e` FACTS files, the `ais@2300` CONTROL exceedance, `--gis-check`'s hardcoded REFs,
  and L21's two false provenance facts ("8 chains" where 4 exist; "20 marginals unconverged" where
  its own log says 18).

---

## 6. THE SKEWED PRIOR IS NO LONGER THE FIRST ITEM

The predecessor's ⭐ §7.1 was to scope a right-skewed `ais_gmst_amp` prior. **Measured, and the
asymmetry is NOT RESOLVED at n=34:** bootstrap 68% CI on the p83/p17 ratio **[1.06, 2.14]**, 90%
**[0.77, 2.67]**; **P(ratio >= 1.56 | Gaussian, n=34) = 0.123**; sample skewness **+0.224** against
a Gaussian null 90% band of **[-0.68, +0.65]**. A bimodality reading does not survive either — the
4.5x max-gap has P = 0.67 under the same null. The installed N(1.09, 0.180) is not distinguishable
from the 34-model empirical distribution.

The p83 understatement of 0.081 remains real as a POINT estimate and is worth ~31 cm at 2300; what
is absent is evidence for the FORM change. Model genealogy is untested and would cut the effective
n well below 34 (3 CNRM, CESM2/CESM2-WACCM/TaiESM1, both GISS, both INM all sit in the upper group).

Also noted, not fixed: `python/scope_ais_amp_law_form.py:65` still hardcodes
`CUR_MU, CUR_SIGMA = 0.95, 0.10` and prints it as "THE SHIPPED PRIOR" — stale since `165a860` made
it 1.09 / 0.180.
