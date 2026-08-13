# Handoff 2026-08-13 — Ladrillo 1.0 step 5 is DONE and the posterior is accepted; the amp law is decided; `ais_iceflow0` is the open wound

**Self-contained pickup:** this note + the `CHANGELOG.md` entry for 2026-08-13. It
supersedes `notes/handoff_2026-08-12c_ladrillo_step5_stage1_done_stage2_next.md` on
stages 2 and 3 (both now complete); that note remains the record of the step-5 build.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip **`6d73349`**.
**Run `./run_ladrillo_tests.sh` first — six suites, all passed at `304f99e`.**

---

## 0. STATE IN ONE PARAGRAPH

Stages 2 and 3 are done. Four production chains (tag **`L10`**, 4 × 2M, seeds 2026–2029,
`--overdisperse`) ran in 2h15m and the canonical posterior
`data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv` (10 000 draws) is written and
**ACCEPTED ON DELIVERABLE**. Nineteen parameter marginals are NOT converged, led by
`ais_iceflow0` at R̂ 2.359 — §3 is entirely about that, because it is worse than a large
R̂ and it constrains what the posterior may be used for. Marcus has decided the Greenland
amplification law: **observed level + CMIP6 shape** (§2). The next substantive task is to
implement that law and recompute the 2100 GIS spread on this posterior (§4).

---

## 1. WHAT LANDED

### Stage 2 — `overdispersed_starts.csv` rebuilt (commit `2ddb971`)
The file on disk was the **52-param extC vintage** (`greenland_a/b/alpha/beta/v0` where
the 8 Ladrillo `gis_*` belong), so `--overdisperse` hard-errored. Rebuilt from the 2nd
half of `chain_L10tune2_seed2026_n2000000.csv` at `ais_iceflow0` quantiles
**0.02 / 0.35 / 0.65 / 0.98**, in seed order `[2026, 2027, 2028, 2029]`. The extC file is
preserved as `outputs/mcmc/overdispersed_starts_extC52.csv` — its working copy differed
from BOTH HEAD (39 cols) and `.pre_extc_bak`, so it was the only copy of that vintage.

**Gate worth reusing elsewhere.** The recomputed logposteriors reproduced the chain's
stored `log_post` **to the digit** (42.20 / 44.79 / 46.02 / 45.84). That is an exact
round-trip through the calibrator's own likelihood. A bare "is it finite" check — which is
all the calibrator itself does — would have passed a *permutation* of same-scale
parameters. If you ever rebuild a starts file again, check the round-trip, not finiteness.

### Stage 3 — production (run complete; recipe in `304f99e`)
Acceptance **0.236–0.237** (stage-1 tuning: 0.238). All four seeded from
`adapted_cov_L10tune2_seed2026.csv` **as-is, with no "name-mapped" fallback line** — the
check the previous handoff asked for. Each from its own start row.

**A 4.8× launch bug, now documented in the calibrator header.** The naive launch reported
ETA ~11h. Stage 1's *solo* chain did the same 2M in 2h25m, so that was treated as
contention rather than cost. Julia defaults to `BLAS.get_num_threads() == 4`, and this box
is an **Apple M4 with only FOUR performance cores** (`hw.perflevel0.physicalcpu` = 4; the
other 6 are efficiency cores). Four chains therefore put **16 BLAS threads on 4 P-cores**,
each process burning ~200% CPU of which about half was OpenBLAS spin-wait.

```
for s in 2026 2027 2028 2029; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 2000000 $s \
    --tag=L10 --overdisperse &
done; wait
```

ETA 11:01 → **2:17**; the run finished in ~2h15m, i.e. four chains at full single-chain
speed. Threaded BLAS was never buying anything here — the RAM sampler's per-iteration work
is a **55×55 Cholesky update**, far below where threading pays. On Apple Silicon size
parallelism off `hw.perflevel0.physicalcpu`, not `hw.physicalcpu`; E-cores do not
substitute.

### The deliverable gate had to be built (commit `322387a`)
`diag_slr_convergence_by_chain.jl` and `..._extc.jl` are hard-wired to `greenland_a` and
die on L10 chains (`ArgumentError: column name :greenland_a not found`). Same class as the
hard-wired-to-stock-SIMPLE projection kernel the previous handoff caught. New
**`julia/diag_slr_convergence_by_chain_ladrillo.jl`** **delegates** the draw→BRICK mapping
to `ladrillo_projection.jl` instead of re-implementing it inline — inline duplication is
precisely how the kernel drifted onto the wrong Greenland before, and delegating means the
diagnostic cannot certify a model different from the one the projections use. It reads the
Greenland variant from the chains' own headers **before** `ladrillo_setup`, because
`ladrillo_setup(gis_ab=)` decides which Greenland slot the model carries.

```
julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl 400 --tag=L10
```

| horizon | R̂ | ESS | sd(medians) | mean(sd within-chain) | ratio |
|---|---|---|---|---|---|
| SLR@2100 | **1.000** | 1588 | 0.122 cm | 12.487 | 0.010 |
| SLR@2150 | **1.000** | 1680 | 4.415 cm | 33.867 | 0.130 |

Pooled SLR@2100 q05/q50/q95 = **43.57 / 46.59 / 79.19 cm**; @2150 = **64.74 / 74.23 /
161.12** (cm, rel 1995–2014, ssp245).

### Acceptance (commit `6d73349`)
`postprocess_mcmc_ext.jl --tag=L10 --accept-slr` (~41 min) wrote
`data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv` (10 000-member subsample of
4 000 000 pooled draws; **gitignored** under `data/MimiBRICK/*`, as extC's is) and
`outputs/mcmc/adapted_cov_L10.csv`. Verified 10 000 × 55, **8 `gis_*` and ZERO
`greenland_*`**, no duplicate rows.

---

## 2. DECIDED (Marcus, 2026-08-13) — the amp law is **observed level + CMIP6 shape**

Measured on **40 CMIP6 models**, `{historical, ssp126/245/585}`; ssp370 excluded as the
aerosol outlier exactly as in the Antarctic work. Commit `26914eb`.
`python/reduce_cmip6_tas_gis.py` **imports `build_t_gis`'s mask machinery** — same GTN-G
region-05 polygon, same subgrid point-in-polygon, same Berkeley land fraction, same
59–70 N southern zone — because otherwise the CMIP6-vs-observed comparison measures the
mask rather than the physics. Mask validated on a 192×288 grid: lat 58.9–70.2, lon
−55..−22.5, **Iceland weight exactly 0**.

**THE LAW.** `amp(ΔT) = OBS_AMP_FULL × S(ΔT)`, with the shape factor
`S(ΔT) = R_secant(ΔT) / R_secant(ΔT_anchor)` taken as a **PCHIP through the binned
medians** (not a parametric fit — interpolate the real data). With `OBS_AMP_FULL = 1.922`
and the anchor at the 1.25 K bin:

| ΔT (K) | CMIP6 secant | S(ΔT) | **amp** |
|---|---|---|---|
| 0.75 | 1.498 | 1.014 | 1.949 |
| **1.25 (anchor)** | **1.478** | **1.000** | **1.922** |
| 1.75 | 1.393 | 0.943 | 1.812 |
| 2.25 | 1.347 | 0.911 | 1.752 |
| 2.75 | 1.284 | 0.869 | 1.670 |

**Why the observed LEVEL is kept.** Observed full-window 1.922 is only **+0.52 sd** above
the CMIP6 full-window ensemble mean 1.604, with 15% of models exceeding it — high side but
comfortably inside the model spread, not an outlier. Adopting CMIP6's ~1.51 outright would
discard an observational constraint the models do not contradict. Keeping the level also
leaves present-day amplification at the value the hindcast was calibrated on, so `gis_amp`
stays likelihood-inert and **no chain re-run is needed**.

**Why only the SHAPE is taken.** The decline is real and significant: secant slope
**−0.0503/K [95% −0.0792, −0.0120]**, through-origin slope −0.0487/K. The two estimators
agree to 0.002/K, so the estimator choice does not drive it. On a **balanced panel of all
40 models** the median falls monotonically **1.498 → 1.284 over 0.75–2.75 K** (−14%).

**RETRACTED — do NOT cite the observed window sequence as evidence of decline.** The
previous handoff's §1 leaned on early 3.604 → full 1.922 → modern 1.792 (a factor 2.01).
Computing the *same* through-origin estimator on the *same* windows in CMIP6 gives early
1.380, full 1.509, modern 1.513 — ratio **0.91**. CMIP6 does not reproduce the observed
ordering at all, and the early window's CMIP6 span is **[0.247, 3.853]** (p05–p95): that
estimator is enormously **noisy, not biased high**, so the observed 3.604 is best read as
one noisy draw. The true decline is roughly **4× smaller** than that sequence implies.

**THE AMP LAW DOES NOT CLOSE THE 2100 GAP — expectation correction.** The previous handoff
expected the amplification law to be "most of the explanation" for Ladrillo sitting above
the 6.3–7.3 cm evaluation band. It is not. Anchored, amp → ~1.67 at 2.75 K; interpolating
the stage-1 amp→spread table (~6.7 cm per unit amp) puts the spread near **8.7 cm**, i.e.
roughly **40% of the gap**. Something else drives the excess. *This number is an
interpolation off a stage-1 table and must be recomputed on the production posterior —
see §4.*

### Two sub-choices this decision does NOT settle
1. **Behaviour above ~2.75 K.** The binned curve is non-monotone (a bump at 3.25 K:
   1.284 → 1.341) and this **survives the balanced panel**, so it is not model dropout. It
   is most likely **scenario composition** — a model only reaches 3.25 K under ssp585, so
   high bins are ssp585-weighted while low bins are ssp126/245-weighted; the balanced panel
   balances models but **not scenarios**. Recommendation: apply the PCHIP over 0.75–2.75 K
   and **hold `S` flat at its 2.75 K value above that**, which is conservative (it stops
   the amplification falling further on evidence we do not trust) and monotone. Flag it
   wherever high-warming or 2300 Greenland is reported — and note this compounds the
   existing option-C caveat that proportional relaxation cannot serve both a small
   historical loss and a huge post-threshold commitment.
2. **Where exactly to anchor.** The table above anchors at the 1.25 K bin, but the observed
   1.922 comes from a **through-origin fit over 1901–2024**, whose effective warming level
   is not 1.25 K. Because `amp = Σxy/Σx²` is an x²-weighted mean of the pointwise ratios,
   its effective anchor is **`ΔT_eff = Σx³/Σx²`** over the observed window. Computing that
   on the observed global series and anchoring there is a small, well-defined improvement
   over assuming 1.25 K; it will shift the whole curve slightly. Worth doing before the
   deliverable.

### Implementation notes (unchanged from the previous handoff, still true)
`ladrillo_gis_driver(bf, amp)` in `julia/ladrillo_projection.jl` does a constant-amp
anchor-preserving splice; it becomes `amp(GMST_t)`, keeping the 11-year anchor. The
calibrator's `GIS_AMP` stays a scalar — it only builds the HISTORICAL driver, where the
observed record *is* the amplification — so this is a **projection-side change only**.
**CAUTION:** suite step 6 (`julia/validate_gis_projection_ab.jl` check [1]) asserts
constant parity between `LADRILLO_GIS_AMP` and the calibrator's `GIS_AMP`. That assertion
needs **rethinking, not deleting**, when the projector's amp becomes a function — it is
what stops the two files drifting onto different models. Suggested replacement: assert
`amp(ΔT_anchor) == GIS_AMP` exactly, so the two still meet at the calibration point.

---

## 3. THE OPEN WOUND — `ais_iceflow0`

`postprocess_mcmc_ext.jl --tag=L10` reports **19 non-converged marginals**:

| param | R̂ | ESS | τ |
|---|---|---|---|
| **`ais_iceflow0`** | **2.359** | 12.0 | 334 529 |
| `antarctic_alpha` | 1.505 | 15.9 | 251 904 |
| `gis_f` | 1.335 | 21.4 | 186 595 |
| `ais_slope` | 1.288 | 22.5 | 177 427 |

### It is worse than a large R̂: the chains barely overlap
Post-burn (second 1M draws) per chain:

| chain | p05 | p50 | p95 | Q1→Q4 drift | its start |
|---|---|---|---|---|---|
| seed2026 | 0.717 | **0.861** | 1.010 | −0.054 | 0.695 |
| seed2027 | 0.922 | **1.106** | 1.232 | −0.193 | 0.844 |
| seed2028 | 1.181 | **1.337** | 1.462 | −0.037 | 0.905 |
| seed2029 | 1.076 | **1.277** | 1.666 | +0.236 | 0.992 |

Three things to read off this:

1. **seed2026's p95 (1.010) lies BELOW seed2028's p05 (1.181).** Those two chains have
   essentially disjoint support. This is not a marginal R̂; it is four chains sampling four
   different places.
2. **The chain medians track the ordering of their starts** (0.695→0.861, 0.844→1.106,
   0.905→1.337, 0.992→1.277). The chains have retained memory of where they began —
   exactly what τ ≈ 3.3e5 predicts, since a 1e6-draw post-burn half holds only
   **~3 effective samples** of this axis.
3. **They are still moving.** Q1→Q4 drifts of −0.193 (seed2027) and +0.236 (seed2029) are
   large next to the within-chain spread. These chains are in transient, not stationary.

### Why this is a REVEAL, not a regression
`overdispersed_starts.csv` is built by drawing at `ais_iceflow0` quantiles
0.02/0.35/0.65/0.98 — **the chains were deliberately dispersed along precisely this axis**,
which is why the failure is so stark here. The pathology is pre-existing:
`diag_slr_convergence_by_chain.jl`'s own header records `ais_iceflow0` at
**R̂ 1.320 / ESS 10.6** in the 35-param v-next calibration, and the calibrator's
`--overdisperse` comment predicts R̂ will look worse than a common start — *"that is the
diagnostic working, not a regression"*.

**The sharpest evidence:** seed2026's post-burn median is **0.861**, which reproduces the
stage-1 tuning posterior's **0.861 ± 0.084** exactly. Stage 1 was a single chain from a
common MAP start — so what it reported as a posterior was **one chain's local basin**, and
its quoted ±0.084 was a within-basin spread, not a credible interval. Over-dispersed starts
did not create this problem; they made a pre-existing one visible.

### Why the deliverable is nonetheless converged
The AIS geometry parameters are strongly correlated, so a poorly-identified **ridge** in
parameter space can still map onto a well-determined projection. That is exactly what
happens: `ais_iceflow0` chain medians span 0.861 → 1.337 (a 55% range) while the SLR@2100
chain medians agree to **0.122 cm against a within-chain sd of 12.487 cm** (ratio 0.010).
The chains disagree about *where on the ridge they sit* and agree about *what it projects*.

### CONSEQUENCE — what the accepted posterior may and may not be used for
- **MAY:** projected SLR and anything derived from it (the certified deliverable).
- **MAY NOT:** parameter-level inference. The pooled `ais_iceflow0` marginal
  (p50 **1.177** [0.78, 1.46]) is a **mixture of four chains that never merged**, not a
  posterior. Do not quote AIS-geometry credible intervals, do not plot AIS geometry
  scatter, and do not compare these marginals to extC's as if both were posteriors.
- **WATCH at 2150:** the median spread there is 13× the 2100 value relative to
  within-chain scatter (ratio **0.130** vs 0.010), consistent with the AIS tipping tail
  being the slowest-mixing feature. **R̂ is mean-based and reads 1.000 at 2150, so it does
  NOT surface this** — carry the caveat manually wherever 2150 is reported.

### If someone wants to actually fix it (not required for 1.0)
τ ≈ 3.3e5 means a properly mixed `ais_iceflow0` needs O(1e7–1e8) iterations at the current
proposal — not feasible by brute force. The productive directions are reparameterising the
AIS geometry along the ridge (the `(bedheight0, slope, iceflow0, c)` block is where the
correlation lives, cf. the `ais_runoff_Ton` reparam that already fixed the runoff line), or
accepting it permanently as a ridge and documenting the deliverable gate as the standing
acceptance criterion. **Do not simply run longer and hope.**

---

## 4. NEXT STEPS, in order

1. **Recompute the 2100 GIS scenario spread on the L10 posterior.** The 8.7 cm figure in
   §2 is interpolated off a stage-1 table and is the weakest number in this note. Replaces
   the pre-registered flag's headline.
2. **Settle sub-choice 2.2** (`ΔT_eff = Σx³/Σx²` anchor) — cheap, and it shifts the curve.
3. **Implement `amp(GMST_t)`** in `ladrillo_gis_driver`, with the suite-6 parity assertion
   replaced by `amp(ΔT_anchor) == GIS_AMP` rather than deleted.
4. **Re-run the six suites**, then the deliverable projections.
5. **Quarantine sweep** for deliverables on the 78.02 / 77.7 cm vintage — **vintage
   difference, not a bug**; say so in the quarantine README.

### Owed, not blocking (carried forward from 2026-08-12c)
- **4.4** ν sensitivity once. **4.5** refit with the four glacier set-asides at prior
  centres. **4.6** structural-uncertainty caveat wherever bands are compared to FACTS.
- `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` still says "brick_mengel"
  although extC has no Mengel glaciers. Wrong before the rename; kept separate.
- **After 1.0**, from the noise-model note §6: the total stream is 56% algebraically
  redundant with the components *and* the loosest constraint in every window; no AR(1)
  member whitens any stream, which argues for an explicit discrepancy term. **Not before
  1.0** — extC was calibrated under the current noise model.
- Etymology sentence for the sharing memo — **Marcus drafts prose**.
- Branch is still `brick-mengel-vnext`.

---

## 5. NON-OBVIOUS STATE

- **Chains are on disk and gitignored**, ~2.2 GB each:
  `chain_L10_seed{2026,2027,2028,2029}_n2000000.csv`. The two tuning chains
  (`chain_L10tune_*` 54-param superseded, `chain_L10tune2_*` 55-param, the stage-2 source)
  are also still present — **`L10tune` is now deletable**; keep `L10tune2` as the
  provenance of the starts file.
- **The accepted posterior is gitignored** (`data/MimiBRICK/*`). It exists only on this
  machine. Regenerate with
  `julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=L10 --accept-slr` (~41 min,
  needs `outputs/mcmc/slr_convergence_L10.csv`, which IS tracked).
- **`postprocess_mcmc_ext.jl` refuses by default** and only writes the canonical subsample
  with `--accept-slr`. That refusal is correct behaviour — do not reach for `--force`,
  which writes `_NOTCONVERGED`-suffixed files that deliberately miss the canonical paths.
- **Julia block-buffers stdout to a file** while ProgressMeter writes unbuffered to stderr,
  so a redirected run shows only the progress bar until it exits and a 0-byte log means
  nothing. Read with `tr -d '\000'`, `tr '\r' '\n'`, and strip `\x1b\[[0-9;]*[A-Za-z]`.
- **Do not wrap a long run in a shell wait-loop inside one tool call** — the call's timeout
  SIGTERMs the whole process group and kills the run. Launch with `nohup ... &` and poll in
  separate calls. `setsid` does not exist on macOS. This cost one 10-minute postprocess and
  briefly left two concurrent postprocess runs racing on the same output files.
- **`pgrep -f` did not reliably match these julia processes**; use
  `ps aux | grep "[p]ostprocess_mcmc_ext.jl"`.
- **40 CMIP6 models reduced** to `data/cmip6_gis/` (1.6 MB, committed). MCM-UA-1-0 dropped
  (nonstandard coord names — no `.lat`). Re-streaming is ~20 min and resumable.
- Python env `source ~/climate-env/bin/activate`; Julia `--project=julia_v2`.
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`, and
  **BRICK-FM is a different model**. Dated `notes/` are frozen.
- Greenland option C failed and is out of pass 1; the same criticism applies to A+B at high
  warming, where it is invisible rather than absent. **Flag it wherever 2300 or
  high-warming Greenland is reported** — and see §2 sub-choice 1, which compounds it.

---

## 6. COMMITS THIS SESSION

| commit | what |
|---|---|
| `2ddb971` | Stage 2: rebuild `overdispersed_starts.csv` for 55 params |
| `304f99e` | Document the parallel-launch BLAS pin (4.8×) |
| `26914eb` | CMIP6 Greenland amp(ΔT): decline real but ~4× smaller; keep observed level |
| `322387a` | Ladrillo deliverable-convergence diagnostic (the L10 acceptance gate) |
| `c9ec5ea` | CHANGELOG for the above |
| `6d73349` | Posterior ACCEPTED ON DELIVERABLE; acceptance record committed |
