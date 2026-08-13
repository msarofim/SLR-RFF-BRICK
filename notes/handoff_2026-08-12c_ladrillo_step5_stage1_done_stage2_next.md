# Handoff 2026-08-12c — Ladrillo 1.0 step 5: the build is done, stage 1 has run twice, **stage 2 is the first thing to do**

**Self-contained pickup:** this note + the `CHANGELOG.md` entries for 2026-08-12 (there
are five) + `notes/note_2026-08-12_noise_model_stream_dependence_and_grip.md`. The earlier
`notes/handoff_2026-08-12b_...md` is superseded on step 5 (it says step 5 is a build; the
build is now done) but is still the record of how the four prerequisites were cleared.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip **`8dcc6c3`**.
**Run `./run_ladrillo_tests.sh` first — SIX suites now, all pass.**

---

## 0. START HERE — stage 2, then stage 3

The production launch is a **three-stage** process (the calibrator's own header documents
it; a one-stage launch fails immediately). Stage 1 is **done**. Stage 2 is next and is
quick.

### Stage 2 — build the over-dispersed starts (~15 min)
`--overdisperse` needs `outputs/mcmc/overdispersed_starts.csv` to carry **one column per
sampled parameter, all 55**, and it hard-errors listing the missing ones if not. The file
on disk is a **52-param extC artifact** and must be rebuilt:

- Source: `outputs/mcmc/chain_L10tune2_seed2026_n2000000.csv` (2nd half).
- **4 rows, drawn at `ais_iceflow0` quantiles 0.02 / 0.35 / 0.65 / 0.98** — these are REAL
  posterior draws, one per production seed in the order `[2026, 2027, 2028, 2029]`.
  **Not random jitter**: the calibrator's comment records that jittering the MAP gave a
  non-finite logposterior in 200/200 draws, because a jointly-perturbed geometry vector
  leaves the feasible region even when every marginal is inside its bounds.
- Columns must be `pn0` order (the 55 sampled names, then the 10 AR(1) noise entries are
  already inside that count — `pn0[1:NP]` plus `sd_*`/`rho_*`).
- **The existing file is tracked and dirty in `git status`.** Move it aside rather than
  overwriting blind — it is the extC-vintage artifact and is the only copy.
- Sanity gate before stage 3: each row must give a finite `logposterior`. The calibrator
  checks this itself and errors, but check it deliberately rather than discovering it
  four chains in.

### Stage 3 — production (~3 h wall clock, 4 chains in parallel)
```
for s in 2026 2027 2028 2029; do
  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 2000000 $s --tag=L10 --overdisperse &
done; wait
```
~2.2 GB per chain, 8.8 GB total; 448 GB free at the time of writing. `--overdisperse`
matters: R̂ is only valid with over-dispersed starts, and the 8 Greenland parameters have
never been sampled by four independent chains, so a common start would make R̂
anti-conservative exactly where we know least.

**The covariance is already right.** `ADCOV` prefers `adapted_cov_L10tune2_seed2026.csv`,
which is 55×55 and matches `NK` exactly, so it is used **as-is** — every parameter
including `gis_amp` is already Ladrillo-shaped. Confirm the run log says
`(seeding proposal from adapted covariance adapted_cov_L10tune2_seed2026.csv)` and **not**
a "name-mapped" line; a name-mapped line means it fell back to an older vintage.

---

## 1. MARCUS'S DIRECTIVE, 2026-08-12 — the Greenland amplification must become GMST-dependent

**For projections, impose a relationship between Greenland amplification and global
temperature that is consistent with CMIP6 models.** Ladrillo 1.0 currently applies a
**constant** amplification, `gis_amp`, sampled from the observed historical value
N(1.92, 0.32) truncated to [1.51, 2.28]. That is almost certainly wrong for the future,
and two independent lines say so:

- **The observed amplification is already falling.** From `outputs/gis_amp_prior.csv`,
  southern Greenland: **early 3.604 ± 0.689, full-window 1.922 ± 0.318, modern
  1.792 ± 0.303.** We used the full-window value.
- **CMIP6 polar amplification collapses with warming level** — memory
  `project_pai_cmip6_time_diagnostic`, which records that the amplification index falls as
  the warming level rises and that Xie's 0.95 is a CAP metric. That diagnostic already
  exists in this programme and is the natural source for the functional form.

**Why this matters quantitatively.** The amplification is the *dominant* control on the
2100 projection. Measured on the stage-1 posterior:

| amp | 2100 GIS scenario spread |
|---|---|
| 1.51 (prior p05) | 7.43 cm |
| 1.79 (modern window) | 9.22 cm |
| **1.92 (full window, in use)** | **10.08 cm** |
| 2.28 (prior p95) | 12.61 cm |

A constant historical amp applied out to 2100 therefore **overstates** future regional
warming and inflates the scenario spread — which is the most likely explanation for
Ladrillo 1.0 sitting above the comparison band (§3).

**This does NOT block stages 2 and 3.** `gis_amp` is likelihood-inert and its posterior
correlates with every other parameter at **|r| ≤ 0.05**, so it is effectively independent
and **its treatment can be revised at projection time without re-running the chains.**
Do the production run; fix the amplification law before the deliverable projections.

**Implementation sketch when you get to it.** `ladrillo_gis_driver(bf, amp)` in
`julia/ladrillo_projection.jl` currently does a constant-amp anchor-preserving splice. It
becomes `amp(GMST_t)` — the splice keeps its 11-year anchor but the multiplier declines
with the warming level. The calibrator's `GIS_AMP` stays a constant (it only builds the
historical driver, where the observed record *is* the amplification), so this is a
projection-side change. **Suite step 6 asserts constant parity between
`LADRILLO_GIS_AMP` and the calibrator's `GIS_AMP`** — that assertion will need rethinking
when the projector's amp becomes a function rather than a scalar. Do not simply delete it;
it is what stops the two files drifting onto different models.

---

## 2. What was built (commits `0e53c2d`, `3b4650b`, `663143d`, `c730cef`, `8dcc6c3`)

**The calibrator.** `build_brick_nu3_gis` puts `greenland_ab` in the Greenland slot.
`--stock-gis` reverts and reproduces extC *exactly* (52 params, `logpost(θ0) = −849.24`).
The regional driver is built **inside** the calibrator from `t_gis_zones.csv` with the same
anchor-preserving splice the glacier blocks use, so **the external interface stays
GMST + OHC only** — the drop-in property that separates Ladrillo from MAGICC-SLR.

**8 sampled Greenland parameters**: `gis_{c1,c0,f,alpha_f,beta_f,alpha_s,beta_s}` plus
`gis_amp`; `gis_g` FIXED at 0 (item 4.1) and `gis_v0` structural. Prior centres are the
converged offline fit **at g = 0** — never the g = 0.917 fit, since `(c0, g)` is a flat
manifold and `c0` moves 4.04 → 61.99 cm along it at identical nlp.

**The Mouginot 2019 partition is in the joint likelihood.** The offline cell is explicit
that this is what makes the two-channel split identifiable; without it `f` floats.

**Priors signed off** (Marcus, 2026-08-12) over flat (σ = 1e3) and 10×-wider variants,
**with the caveat on record: the offline fit used the same gis target the joint likelihood
scores**, so the centres re-use data the likelihood already uses. The σ's are wide enough
that this is a starting point rather than information. **Any methods section must say so.**

**Two new gates**, and both caught real errors in the code they were written to check:
- **suite 5/6, `calibrate_mcmc_ext.jl --gis-check`** — runs the calibrator at the exact
  offline g = 0 vector and matches the offline cell to **0.0000** on RMSE 0.0617,
  1942–1982 bias +0.0146 cm, 2003–2018 rate 0.7749 mm/yr, Mouginot share 0.7351. It caught
  `gis_f` centred on the Mouginot share (which would have counted Mouginot in **both** the
  prior and the likelihood) and a bias sign flip.
- **suite 6/6, `julia/validate_gis_projection_ab.jl`** — the projection kernel was
  hard-wired to stock SIMPLE and **could not have consumed the posterior at all**; worse,
  it loaded a Ladrillo 1.0 posterior *without complaint* because CSV.jl's `select=`
  silently returns only the columns it finds. Now: variant detected from the posterior's
  own columns with no default and no fallback, all required columns demanded, and a
  **mutation check** that two draws differing only in `gis_amp` actually move the 2100
  projection (13.80 → 17.32 → 20.58 cm) — because "applied per draw" is exactly the kind
  of claim that passes every other test while being inert.

---

## 3. Stage-1 results — read these before reading the production posterior

Two tuning runs, both 2M iterations, seed 2026, common start:

| | L10tune (54 par) | **L10tune2 (55 par, canonical)** |
|---|---|---|
| wall clock / acceptance | 2h25m / 0.239 | 2h25m / **0.238** |
| logpost start → 2nd-half median | −845.2 → **+39.7** | −844.5 → **+40.0** |
| ρ_gis | 0.985 → **0.159** | 0.985 → **0.243** |
| sd_gis | 0.054 → 0.010 | 0.054 → **0.011** |
| rails | none | **none** |

**The headline is the noise model, not the fit.** Replacing stock SIMPLE with A+B collapses
**ρ_gis from 0.985 to ~0.24** and sd_gis from 0.054 to 0.011. That is
`notes/note_2026-08-12_noise_model_stream_dependence_and_grip.md` confirmed from the
opposite direction: the near-unit-root AR(1) on the gis stream **was** absorbing systematic
model error, and once the model error is fixed the noise behaves like noise. The ~885-unit
logpost gain is dominated by that σ collapse, not by a better χ².

The joint likelihood independently bounds `beta_f` below 1e-2 (p95 = 0.0102), matching the
offline data support — Marcus's 4.2 "keep it free" ruling is vindicated; it is now partly
identified rather than prior-driven.

`gis_amp` posterior p50 **1.901 ± 0.199** is the *truncated* prior (N(1.92, 0.32) on
[1.51, 2.28] has sd ≈ 0.19), confirming it propagates rather than being estimated.

### The pre-registered flag that fired
**The 2100 GIS scenario spread did NOT come down.** Pre-registration said to watch it fall
from 10.44 cm toward the 6.3–7.3 evaluation band. It did not, and **nothing in the
calibration could have moved it**: G4 is evaluation-only, the hindcast does not see 2100,
and posterior `c1` (0.0340) barely moved from the offline 0.0328. With `gis_amp` sampled:

| 2100 GIS (cm) | p05 | p50 | p95 |
|---|---|---|---|
| ssp126 | 5.98 | 6.83 | 7.70 |
| ssp245 | 8.36 | 9.69 | 11.14 |
| ssp585 | 14.05 | 16.92 | 20.48 |
| **per-draw spread** | **7.89** | **10.07** | **12.83** |

Even p05 sits above the band (MAGICC-SLR 7.09, FACTS FittedISMIP 6.34, emuGrIS 7.26,
bamber19 7.23). **Report it as a property, not a defect** — and expect §1's
amplification law to be most of the explanation.

---

## 4. Owed, not blocking

- **Quarantine sweep** for deliverables on the 78.02 / 77.7 cm vintage. **Vintage
  difference, not a bug** — say so in the README.
- **4.4** ν sensitivity once. **4.5** refit with the four glacier set-asides at prior
  centres. **4.6** structural-uncertainty caveat wherever bands are compared to FACTS.
- `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` still says "brick_mengel"
  although extC has no Mengel glaciers. Wrong before the rename; kept separate.
- **After 1.0**, from the noise-model note §6: the total stream is **56% algebraically
  redundant** with the components *and* the loosest constraint in every window — two
  independent reasons to stop scoring it as a fifth independent observation. And no member
  of the AR(1) family whitens any stream, which argues for an explicit discrepancy term
  rather than a wider noise model. **Not before 1.0** — extC was calibrated under the
  current noise model and changing it now makes the two incomparable.
- Etymology sentence for the sharing memo — **Marcus drafts prose**.
- Branch is still `brick-mengel-vnext`.

---

## 5. Non-obvious state

- **Two tracked files are dirty and incidental**, and have been for three sessions:
  `figures/diag_gis_regional_driver.png`, `outputs/mcmc/overdispersed_starts.csv`. The
  second one is the stage-2 input — see §0 before touching it.
- **Both tuning chains are on disk and gitignored** (2.17 GB + 2.21 GB):
  `chain_L10tune_seed2026_n2000000.csv` (54 par, superseded — keep until stage 3 passes,
  then it is deletable) and `chain_L10tune2_seed2026_n2000000.csv` (55 par, **canonical
  tuning posterior**, the stage-2 source).
- Julia block-buffers stdout to a file while ProgressMeter writes unbuffered to stderr, so
  a redirected run shows only the progress bar until it exits. The header is not lost; it
  flushes at the end. Use `tr '\r' '\n'` and strip `\x1b\[[0-9;]*[A-Za-z]` to read the log.
- `--gis-check` runs at the offline vector, **not** at θ0, deliberately: two prior centres
  (`gis_beta_s` off its rail, `gis_f` weak) are not the offline optimum, so a θ0 comparison
  would test the prior table rather than the wiring.
- Python env `source ~/climate-env/bin/activate`; Julia `--project=julia_v2`.
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`, and
  **BRICK-FM is a different model** with ~130 references here. Dated `notes/` are frozen.
- Greenland option C failed and is out of pass 1; the same criticism (proportional
  relaxation cannot serve both a small historical loss and a huge post-threshold
  commitment) applies to A+B at high warming, where it is invisible rather than absent.
  **Flag it wherever 2300 or high-warming Greenland is reported.**
