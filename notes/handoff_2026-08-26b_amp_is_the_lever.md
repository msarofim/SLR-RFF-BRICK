# Handoff — L17 REJECTED. The lever is the AMP PRIOR + the START, not the proposal and not the modes.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, head **`45b66cd`**, **83 commits
ahead of `origin/ladrillo-dev` and deliberately unpushed — do not push without asking.**
Written 2026-08-26 to be picked up cold. **Continues** `handoff_2026-08-26_L17_and_the_ton_modes.md`
(read it for the L15/L16 arc; ⚠ one of its bullets is CORRECTED here and in-file — see §2).

**L14 IS STILL CHAMPION. `benchmark/champions.json` UNTOUCHED (mtime Aug 25 08:03).**
L15, L16, L17 are all unpromoted; L17 is now REJECTED. Working tree is CLEAN.

> ✅ **The EPERM read-block from the previous session is GONE.** `cat`, shell redirect and the
> file tools all read fine; cwd is intact; no `cd <abspath>` prefix needed. Every number in the
> predecessor handoff was checked against its file this session — none disagreed.

---

## 0. THE ONE-PARAGRAPH STATE

L17 (mode-local proposal) **failed and is rejected**: it made `T_on` mixing *worse*, not better.
Chasing why turned up a **correction that reframes the whole L15→L17 arc — L14 ran
`--overdisperse` and the challengers did not**, so champion and challengers were never
like-for-like. Then a cheap conditioning experiment measured what the modes are actually worth
downstream: **6.9%**. So the modes are a real phenomenon but a small lever. **What remains is the
amp prior, still confounded with the start.** The next run is a start-matched amp arm.

---

## 1. L17 IS REJECTED (commit `45ff538`)

**The arm.** 4 × 2M, ~3h55m (14,022 s/chain), acceptance 0.234–0.239. Exactly one change vs L16:
`--adcov=adapted_cov_L16MID.csv` (L16's own post-burn draws restricted to the MID band). Amp prior
UNCHANGED at N(1.090, 0.180). The `nameless_matrix_order` gate passes **on the production run**:
the by-name proposal diagonal read back `ais_runoff_Ton 0.1422`, the MID-local value.

**The registered prediction resolved on its SECOND branch.** Registered: *"if it reproduces L16's
POOLED numbers (bias −0.022 sd, RMSE 0.0091 cm), the wander is NOT proposal-driven."*
**L17 POOLED: bias −0.094 sd, RMSE 0.0189 cm** — not MID, not L16-POOLED, **worse than both**.

**The proposal BACKFIRED.** `ais_runoff_Ton` R̂ **1.184 → 2.264** (ESS 12.2). Out-of-MID occupancy
**13.5% → 36.9%**; excursions ran FURTHER (LOW median −18.94 → −22.37, HIGH −16.41 → −10.79).
This inverts the handoff's own "a mode-local proposal makes staying EASIER by construction".

**⚠ It is TWO ABSORBED CHAINS, IN OPPOSITE DIRECTIONS — not diffuse wander.** A pooled "24% LOW"
cannot distinguish four chains wandering from one absorbed. `scripts/ton_band_by_chain.sh` (NEW;
raw CSV + awk, independent of the Julia path) splits it:

| arm | seed2026 | seed2027 | seed2028 | seed2029 |
|---|---|---|---|---|
| L16 | 80.2 MID / 19.8 HIGH | 99.2 MID | **29.9 LOW** / 69.3 MID | 98.9 MID |
| L17 | **97.8 LOW** (min −26.07) | 98.0 MID | **48.6 HIGH** (max −7.79) | 99.0 MID |

**L16's chains were HEALTHIER — none absorbed**; its worst crossed and came BACK. Hypothesis: the
tight proposal blocks **returns**, not exits. **UNTESTED** — the free discriminator is an
exit-rate vs return-rate count on the existing chains.

**Band-vs-arm reproduced on THREE arms.** Within a band the arm barely matters (MID RMSE: L14
0.0067 / L16 0.0080 / L17 0.0085; LOW bias: L16 −0.328 / L17 −0.334). L14 is 100% MID.

**⚠ Its convergence "pass" is denominator-driven.** R̂ 1.005 @2100 / 1.006 @2150, ESS 1333/1317 →
ACCEPTED ON DELIVERABLE. But sd(medians)/mean(within-chain sd) @2100 is **0.142, the WORST of the
four arms** (L14 0.051, L15 0.086, L16 0.105). **Never quote L17 as "converged."**

**Downstream was deliberately NOT run** — projections on a posterior 37% out-of-mode with two
absorbed chains would be quotable only with a caveat that negates them.

---

## 2. ⚠⚠ THE CORRECTION THAT MATTERS MOST (commit `fa1a467`)

The predecessor handoff said θ0 is a common MEDOID/MAP start, *"True of L14/L15/L16/L17 alike"*,
and concluded L14's `T_on` sd 0.09 is "unverified coverage". **The first half is FALSE.** Verified
across all 16 chain logs via the `logpost(θ0)` line:

| arm | start |
|---|---|
| **L14** | **FOUR DISTINCT real posterior draws** — 223.78 / 228.36 / 225.60 / 223.78, i.e. AT the typical set |
| L15 | one common medoid/MAP point, −643.92, all four seeds |
| L16 / L17 | one common medoid/MAP point, −644.51, all four seeds |

**L14 ran `--overdisperse`; L15/L16/L17 did not.** Two consequences:

1. **The champion-vs-challenger comparison was NEVER like-for-like.** The challengers began ~866
   log units BELOW the typical set and had to burn in from there. That is an uncontrolled
   difference sitting alongside the amp prior, so **the amp question has never been tested on
   equal footing.** (`like_for_like_forcing`.)
2. **L14's `--overdisperse` arm is already done** — the predecessor's proposed remedy is spent.

**⚠ BUT THE "UNVERIFIED COVERAGE" CONCLUSION SURVIVES, for a sharper reason.**
`build_overdispersed_starts.jl` disperses along **`ais_iceflow0`** quantiles (0.02/0.35/0.65/0.98)
— the badly-mixing axis as understood 2026-07-20, before `T_on` multimodality was found
(2026-08-26). **All four of L14's starts sit in MID**: −17.837 / −17.673 / −17.952 / −17.810.
(The `.pre_l14_bak` backup is likewise all-MID, so this is robust to which file was used; timing
confirms the current one — starts written 11:21, L14 ran 9235 s ending 13:56.)
**L14 is dispersed WITHIN the good mode.** Its 100% MID occupancy does NOT show that chains FIND
MID from elsewhere. `no_power_null`: **an overdispersed arm has power only along the AXIS IT WAS
DISPERSED ON.**

The false claim was also fixed in-place in `run_mcmc_L17.sh` and in the predecessor handoff
(commit `106194d`), so neither will re-seed the error.

---

## 3. HOW MUCH ARE THE MODES WORTH? 6.9%. (commit `45b66cd`)

**The question.** L14 beats L16 on 8 of 9 AIS cells, but that is confounded by mode contamination
AND by the start. If the modes explained it, the amp choice would be downstream-inert and settled
on provenance alone.

**The method — CONDITION, don't re-run.** Two additive, **default-off** flags on
`julia/scope_slr_fair_uncertainty.jl`:
* `--ton-band=LOW|MID|HIGH` — keep only post-burn draws in one KDE-valley band. Edges are named
  constants pointing at `scope_ais_ton_band_hindcast.jl` as the source of truth.
* `--chain-tag=<TAG>` — read chains from one tag, name outputs for another, so a derived arm
  cannot overwrite its parent and `[CONTROL]` compares against the derived arm's own
  `ssps_components_2300_<TAG>.csv`.

Run as `--tag=L16MID --chain-tag=L16 --ton-band=MID`. **No new chain.**

**AIS `median_vs_lit`, JOINT band (1.000 = on the literature median):**

| cell | L14 | L16 | L16MID | % gap closed |
|---|---|---|---|---|
| ssp126 @2100 / @2150 / @2300 | 0.480 / 0.364 / 1.455 | 0.535 / 0.409 / 1.637 | 0.530 / 0.402 / 1.625 | 9 / 14 / 6 |
| ssp245 @2100 / @2150 / @2300 | 0.531 / 0.406 / 0.949 | 0.865 / 1.710 / 1.974 | 0.815 / 1.601 / 1.908 | 15 / 8 / 6 |
| ssp585 @2100 / @2150 / @2300 | 2.430 / 0.964 / 1.016 | 3.009 / 1.084 / 1.126 | 3.002 / 1.084 / 1.122 | 1 / 0 / 4 |

**Aggregate 6.9%. NO verdict changes (9 of 9 identical.)** Smaller on the joint band than the
fixed-driver component projection suggested (13–20%), so the fixed-driver read was OPTIMISTIC
about how much the modes explain.

**⚠ Two disciplines this run enforced, worth copying:**
* **A default-off flag must be PROVEN inert.** Re-running `--tag=L16 --ssp=ssp126` with no band
  left the TRACKED `outputs/scope_slr_fairunc_cells_ssp126_spliced_L16.csv` **bit-identical**
  (`git diff` empty). `mutation_test_gates`.
* **Conditioning is NOT resampling.** This answers "what do L16's in-band draws project", not
  "what would a chain confined to MID find". In the script header.

**Third independent confirmation of occupancy:** the filter's own per-chain report over the full
1M post-burn draws (80.2 / 99.3 / 69.9 / 99.1% MID) matches the awk sweep (80.2 / 99.2 / 69.3 /
98.9) to rounding. L16's unconditioned column reproduces the committed `-25e` §2d table exactly.

---

## 4. ⇒ WHAT TO RUN NEXT — priority order

### PRIORITY 1 — the START-MATCHED AMP ARM. This is the load-bearing run.

**Why.** amp is unidentified (posterior sd ÷ truncated-prior sd = 0.989 = NO shrinkage), so its
posterior IS its prior and no run can identify it. But §3 shows the choice is **not** downstream-
inert: it moves ssp245@2150 from 0.406× the literature median to 1.710×. And §2 shows every arm
that used N(1.09, 0.180) **also** used the bad common start, so amp and burn-in are inseparable in
everything run so far. **This arm is the only way to split them.**

**What.** L16's prior (`--amp-sigma=0.180`, centre 1.09) + **L14's start protocol**
(`--overdisperse`). Everything else L16's. Copy `run_mcmc_L16.sh`, add `--overdisperse`.
⚠ `overdispersed_starts.csv` is currently L14's (all-MID, iceflow0-dispersed) — decide whether to
reuse it as-is (cleanest for isolating amp: identical starts, only the prior differs) or rebuild.
**Reusing it as-is is the recommendation** — it makes the amp comparison exactly controlled.

**Cost** ~2h34m (L14's runtime) + ~20 min downstream.

### PRIORITY 2 — the `T_on`-DISPERSED L14 ARM

**Why.** §2: L14's tight `T_on` (sd 0.09) is dispersed along the wrong axis and has no power on
the mode question. **Marcus's steer (2026-08-26): four L17/L16 off-mode draws, unless the old
results aren't sufficient as controls.** ⚠ **They are NOT sufficient** — commit `893bfaa` ("L15
calibration inputs: amp re-centred, LWS extended, closure sigma trend-extended") landed AFTER L14
ran, and moved `lws` 0.123 and `dang_closure_sig` 0.151 in the likelihood. A new run scores
against a different objective than the Aug-20 L14 run. **So spend one slot on a MID control**,
whose specific job is to distinguish "the modes are real and separated" from "MID is no longer
favoured under the current targets".

Proposed assignment — all four from **current-code** chains (L14's own draws predate the target change):

| seed | source | band |
|---|---|---|
| 2026 | L17 seed2026 | deep LOW (`T_on` ≈ −22) |
| 2027 | L16 seed2028 | mild LOW (≈ −19/−20) |
| 2028 | L17 seed2028 | HIGH (≈ −10/−14) |
| 2029 | L17 seed2029 | **MID control** |

`build_overdispersed_starts.jl` currently hardcodes `ais_iceflow0`; it needs a `--param=` axis
argument. Starts MUST be real draws — its header records that 200/200 random-jitter starts gave
non-finite logposterior.

### PRIORITY 3 — free, on existing chains
The **exit-rate vs return-rate count** (§1) that would test the trapping hypothesis. No new run.

### STILL OPEN — not a run
**The amp prior is a PROVENANCE call and is Marcus's, not yet made.** L14's N(0.95, 0.10) rests on
Xie's sliding-window TREND ratio under a polar-cap mask, on data corrupt in seven files; L16/L17's
N(1.09, 0.180) on two corrected CMIP6 secant ensembles (34-model 1.095 ± 0.180; 41-model DECK
1.097). **The benchmark scores fit, not provenance, and structurally cannot see this.** §3 raised
the stakes; it did not decide it.

---

## 5. NON-OBVIOUS STATE AND TRAPS

* ⚠ **`python/bench_ladrillo.py` and `ladrillo_model_comparison.py` need the venv** —
  `source ~/climate-env/bin/activate` (bare `python3` has no numpy). The Julia steps do not.
* ⚠ **`postprocess_mcmc_ext.jl` took 2h11m for L17 vs ≤51 min for L16 on identical data.** Not a
  hang: it is the `ess(arr; maxlag=200_000)` loop over ~59 params holding ~1.9 GB while the Mac
  was swap-bound (17.2 of 18.4 GB swap used; RSS only 124 MB ⇒ working set in compressed memory,
  which burns CPU and reads as compute-bound). **Budget 2–3 h and do not kill it.** The `maxlag`
  is load-bearing — the file records that the default 250 FLOORS ESS and that `maxlag = nmin`
  returns NaN, which silently PASSES the gate.
* ⚠ **Julia block-buffers redirected stdout.** An empty log is not a failed run. `tr '\r' '\n'`
  before grepping — the chain logs are progress-bar CRs.
* ⚠ **`scope_slr_fair_uncertainty.jl` reads RAW CHAINS, not the subsample**, and does its own
  thinning. A filtered `parameters_subsample_brick_mengel_<TAG>.csv` cannot reach the joint band —
  that is what `--chain-tag`/`--ton-band` exist for. (This cost a failed pipeline run this session.)
* ⚠ **`postprocess_mcmc_ext.jl` REFUSES to write** when marginals fail unless
  `outputs/mcmc/slr_convergence_<TAG>.csv` exists AND `--accept-slr` is passed. Documented gate,
  not a failure — run `diag_slr_convergence_by_chain_ladrillo.jl --tag=<TAG>` first.
* ⚠ **`git add -A outputs/` sweeps ~227 deliberately-untracked mcmc artifacts. Stage by name.**
  Chain CSVs are 2.3 GB each and gitignored.
* ⚠ **`data/MimiBRICK/parameters_subsample_brick_mengel_L16MID.csv` is gitignored and NOT
  committed** (L14/L15/L16's were force-added). Same for L17's. Deliberate: 11 MB each for a
  derived/rejected arm. Force-add if the lineage must be complete.
* ⚠ The AIS target column of `recalib_targets_ext.csv` is bit-identical pre/post the L15 rebuild,
  so L14/L15/L16/L17 **AIS hindcast** comparisons are like-for-like — but `lws` and
  `dang_closure_sig` DID move, which is what makes the Aug-20 L14 run unusable as a control for a
  NEW run (§4 Priority 2).
* Pin BLAS on every julia call: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`.

---

## 6. COMMANDS — the standard post-chain sequence

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=<TAG>
tr '\r' '\n' < outputs/mcmc/log_${T}_seed2026.txt | grep -m1 "A6 prior"     # verify the arm
tr '\r' '\n' < outputs/mcmc/log_${T}_seed2026.txt | grep -m1 "logpost(θ0)"  # verify the START
julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T   # REQUIRED first
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr        # 2-3 h, see §5
bash scripts/ton_band_by_chain.sh $T                                                # per-chain modes
julia --project=julia_v2 julia/scope_ais_ton_band_hindcast.jl 2000 --tags=L14,$T
julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl --tag=$T
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl --tag=$T
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl --tag=$T --no-tap
for s in ssp126 ssp245 ssp585; do julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s; done
source ~/climate-env/bin/activate
python python/ladrillo_model_comparison.py --tag=$T
python python/bench_ladrillo.py --tag=$T
```

---

## 7. FILES AND COMMITS THIS SESSION

**Commits** (all on `ladrillo-dev`, unpushed): `45ff538` L17 rejected · `fa1a467` the
`--overdisperse` correction · `106194d` fix the false claim in `run_mcmc_L17.sh` + predecessor
handoff · `45b66cd` modes worth 6.9%.

**New:** `scripts/ton_band_by_chain.sh`, `outputs/ton_band_by_chain_L16_L17.txt`,
`outputs/mcmc/slr_convergence_L17.csv`, `outputs/bench_ladrillo_L16MID.{csv,md}`,
`outputs/ladrillo_model_comparison_L16MID.csv`, `outputs/ssps_components_2300_L16MID.csv`,
`outputs/scope_slr_fairunc_cells_ssp{126,245,585}_spliced_L16MID.csv`.
**Modified:** `julia/scope_slr_fair_uncertainty.jl` (+`--ton-band`, `--chain-tag`), `CHANGELOG.md`,
`run_mcmc_L17.sh`, the predecessor handoff.

**Memory:** `ais_ton_multimodal` (NEW — the mode finding + its 6.9% downstream worth),
`mode_local_proposal_backfired` (NEW — the general sampling discipline). Both indexed in
`INDEX_ais.md` under "Convergence and identifiability"; the second also in `MEMORY.md`.
`INDEX_ais.md` LIVE STATE now records that L15/L16/L17 are unpromoted and the amp call is open.
