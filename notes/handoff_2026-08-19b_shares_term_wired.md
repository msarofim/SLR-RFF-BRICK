# Handoff — L13 shipped but is NOT certified, and the next question is splitting AIS

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**, pushed and
in sync. Predecessor: `notes/handoff_2026-08-19_calibrator_sector_shares.md`.

**Bottom line. The 3-basin Greenland + per-sector shares term is BUILT, GATED and
COMMITTED, and it does what it was designed to do (partition reproduced to 1.08σ
on level). Production ran clean — 4 × 2M, accept 0.245-0.247 — and then BOTH
convergence gates refused. No SLR@2100 number may be quoted; L12's 45.53 cm
remains canonical. The blocking question is not Greenland: every unconverged
offender is in the AIS block, and why L12 passed the SLR gate while L13 fails it
is UNRESOLVED. Marcus's next question is whether to split AIS into East and West
Antarctica, as GSIC and Greenland were split — §1 is written to answer it.**

---

## 1. THE NEXT QUESTION: would splitting AIS into EAIS / WAIS help?

### 1.1 What the two prior splits ACTUALLY bought — the mechanism matters

The premise "splitting GSIC and Greenland was helpful" is true, but **the thing
that made them work was DATA, not structure**, and that is decisive for AIS.

| split | pieces | per-piece DRIVER | per-piece LIKELIHOOD |
|---|---|---|---|
| **GSIC** | R19 / SLOWP / FAST | `t_glac_blocks.csv` | GlaMBIE per-block rates + partition share |
| **Greenland** | south / mid / high | `t_gis_zones.csv` | Mouginot sectors, `greenland_partition_mouginot2019.csv` |
| **AIS (proposed)** | EAIS / WAIS | **does not exist** | **does not exist** |

Both existing splits were scored against a per-piece observational product that
was already local. The Greenland handoff states the principle outright: the mid
basin is worth keeping separate *"for exactly one reason: the likelihood"* — a
lumped basin has nothing to score, and with a shared driver a third channel on
the same forcing is otherwise just a re-parameterised multi-exponential.

**In this calibrator, `grep -ci 'imbie|otosaka|eais|wais|apis'` returns 1, and
`data/observations/` contains no Antarctic regional product at all.** The AIS
likelihood today scores exactly two whole-sheet things: the `S.ais` sea-level
series (1900-2025, from `recalib_targets_ext.csv`) and the SMB anchor
(`SMB_TARGET_GT = 1863.4` Gt/yr, area-scaled Rignot).

**⇒ A split done today would add parameters with NOTHING to identify them.** That
is the exact failure mode the Greenland design avoided.

### 1.2 What you would need first

1. **A per-region mass-balance product.** IMBIE-3 / Otosaka et al. 2023 gives
   EAIS / WAIS / APIS mass balance 1992-2020 — the direct analogue of Mouginot
   for Greenland. **NOT local; must be fetched.** Check
   `~/Documents/2026/ClaudeDocs/Papers/` first (memory `claudedocs_papers_folder`).
2. **A decision on the driver**, and Greenland's answer probably transfers: ONE
   shared driver, geometry living in the likelihood. Greenland showed a single
   amplification was acceptable and avoided a whole per-zone driver build.
   Note the AIS driver is not a surface-temperature amplification anyway — it is
   the `antarctic_ocean` (anto) sub-model plus `ais_gmst_amp`.
3. **A shares-vs-absolute decision.** Greenland's answer — SHARES ONLY,
   scale-free, orthogonal to the total — was forced by a **1.227×** disagreement
   between Mouginot's sector sum and the calibration total. Expect the same class
   of inter-product disagreement for Antarctica and plan for shares.

### 1.3 The structural obstacle, and why AIS is NOT cheap the way Greenland was

Greenland's split cost **two** sampled parameters, because a reduction existed:
commitment scaled by a FIXED volume share `k_b`, one free rate scale `s_b` per
basin, everything else shared. That worked because the A+B Greenland model is a
lumped commitment-relaxation with no spatial geometry.

**DAIS is not.** It is a single axisymmetric ice sheet with ONE radius and ONE
grounding line — `ais_mu` is *"the ice-profile constant (sets volume per radius)"*,
and `ais_iceflow0` is a *grounding-line flux coefficient*
(`julia/diag_ais_param_sensitivity.jl`). Its 7 geometry parameters
(`GEO_NAMES` = `ais_mu, ais_bedheight0, ais_slope, ais_iceflow0, ais_precip0_LOG,
ais_runoff_Ton, ais_c`) are sampled **jointly under an MvNormal paleo-covariance
prior** (`paleo_geo_prior_ton.csv`, Strategy B), with a further 8 params
(`antarctic_alpha/nu/lambda/gamma/kappa/temp_threshold`, `anto_alpha/beta`).

So a split means: **two geometries, two grounding lines, and a decision about how
to split a JOINT PALEO PRIOR that was constructed for one ice sheet.** There is no
`k_b × s_b` reduction here that preserves the physics — which is exactly the
point below.

### 1.4 The physical argument FOR, which is genuinely strong

EAIS and WAIS are not two halves of one object. WAIS is marine-based on a
**retrograde** bed and carries the MICI/collapse behaviour; EAIS is largely
terrestrial and far more stable. A single axisymmetric bed profile cannot
represent both, and the shipped model applies ONE grounding-line law to their sum.
That is a stronger physical case than the Greenland split had.

**But note the tension:** the strength of the physical case and the cost of the
change come from the same fact. Cheap splits are cheap because the pieces are
dynamically similar; EAIS/WAIS are not, which is why it is worth doing and why it
cannot be a reduced-form knob.

### 1.5 The premise check — "helpful" in WHICH sense?

Be precise about what the Greenland split demonstrably bought, because this run
is the evidence:

- **Realism / partition: YES.** The observed sector split is now reproduced
  (worst scored |z| = 1.08σ) against an `s=1` null that was ~3σ off.
- **Convergence: NO — it got WORSE.** 37 flagged params vs L12's 16, and the SLR
  gate went from PASS (R̂ 1.002) to FAIL (R̂ 1.057).
- **Trend: NO.** The partition is reproduced in LEVEL only; the model's split is
  static while the observations show mid gaining and high losing share (§2.3).

**So "splitting has been helpful" should not be carried into the AIS decision as
"splitting improves convergence."** It has not, here. AIS is ALREADY the
worst-mixing block in the model (τ = 190k-330k, ≈3-5 effective samples per chain
over 1M post-burn draws). Adding parameters to it is at least as likely to
worsen mixing as to improve it, and a badly-mixing block is precisely where extra
freedom hurts most.

### 1.6 Recommendation

**Do not split AIS yet — settle §3 first.** The one unresolved failure in this run
lives inside the AIS block. Restructuring it now would confound the diagnosis:
if the split were done and SLR still failed to converge, there would be no way to
tell whether the split caused it, fixed something else, or was irrelevant.

**Order of operations:**
1. Resolve why L13 fails the SLR gate where L12 passed (§3). Cheap; no new model.
2. Fetch IMBIE-3 / Otosaka 2023 and check the EAIS/WAIS partition is stable on
   modern windows — the exact `diag_gis_basin_lit_check.py` block-1c treatment
   that saved the Greenland term from a vanishing denominator. **This is the step
   that decides whether the split is even scorable**, and it is offline, cheap,
   and independent of everything else. It can start immediately and in parallel.
3. Only then price the structural change.

**Reusable as-is if it goes ahead:** the shares-term pattern (`GISB_*` constants,
the guarded ratio in `logposterior`), the nesting-gate pattern
(`test_greenland_3basin_nesting.jl` — collapse / additivity / partition
invariance), and the lesson in §5 about file-layout name tables.

---

## 2. WHAT SHIPPED, AND WHAT IT DOES

### 2.1 The component and the term

`julia/greenland_3basin_component.jl` — Mouginot sectors south{SW,CW,CE,SE} /
mid{NW} / high{NO,NE} on ONE shared driver; geometry lives entirely in the
likelihood. Commitment scaled by the FIXED volume share `k_b`, clamped
**per basin** to `[0, k_b*v0]` (Marcus 2026-08-19). That clamp is also the form
that keeps the partition exact: `min(max(k*x,0), k*v0) == k*min(max(x,0), v0)`,
so `eq_b == k_b * eq_whole` identically, saturated or not.

`greenland_ab` is UNTOUCHED, so the nesting gate is a genuine A-vs-B run:

| gate | result |
|---|---|
| [1] collapse, k=(1,0,0), s=1 → reproduces `greenland_ab` | 0.0 |
| [2] additivity at production shares | 2.2e-16 |
| [3] partition invariance, Mouginot k, s=1 → total does not move | 4.4e-16 |

The term: shares-only, guarded, scoring **south and mid** over **2002-2011** and
**2012-2018** at σ=0.05; high follows by sum-to-one. `--gis-basins` turns the
state on, `--no-gis-shares` runs it with the term off.

### 2.2 Only TWO sampled parameters, because the third is provably flat

`rate_b = clip(s_b*(alpha*T+beta))`, so scaling every `s_b` by `c` while scaling
the shared shape rates by `1/c` is EXACTLY invariant — measured `max|diff| = 0.0`
for c ∈ {0.25, 0.5, 2, 4}, 1.1e-16 at c=10, against a 0.2279 m signal. Only the
RATIOS are identifiable, which is exactly what the shares term constrains.
`GISB_REF = :south` is pinned at s=1; mid and high are sampled.

### 2.3 It reproduces the LEVEL, not the TREND — state it that way

Fitted (L13tune median): south 1.0 pinned, mid 0.9328, high **0.2554**.

| window | south | mid | high | target | worst scored |z| |
|---|---|---|---|---|---|
| 2002-2011 | 0.586 | 0.214 | 0.200 | 0.592/0.207/0.201 | 0.14 |
| 2012-2018 | 0.561 | 0.208 | 0.231 | 0.554/0.262/0.183 | **1.08** |

against an `s=1` null of 0.456/0.173/0.371. **But the partition does not evolve:**
observed mid rises 0.207→0.262 while the model is flat 0.214→0.208; observed high
falls 0.201→0.183 while the model RISES 0.200→0.231. Expected rather than wrong —
with one shared driver and fixed volume shares the only route to a time-varying
partition is differing nonlinear rate response, which is weak. Inside tolerance,
so the term is not violated. **No writeup may claim the trend.**

Reproduce: `julia/diag_l13_basin_shares.jl`.

---

## 3. THE BLOCKER: production is NOT certified, and the cause is UNRESOLVED

`L13tune` 1M (accept 0.246) → starts rebuilt → 4 × 2M production, accept
0.245/0.245/0.245/0.247. All four completed. **Both gates then refused.**

1. `postprocess_mcmc_ext.jl --tag=L13` → **37 params not converged** (L12: 16);
   refused to write the canonical posterior or the proposal seed.
2. `diag_slr_convergence_by_chain_ladrillo.jl --tag=L13` → **SLR@2100 R̂ = 1.057**
   (threshold 1.05); @2150 R̂ = 1.033 passes. VERDICT: not converged.

**THE HEADLINE MOVE IS NOT RESOLVABLE — do not quote 47.89 cm.**

| | R̂ | ESS | sd(medians) | per-chain SLR@2100 medians |
|---|---|---|---|---|
| L12 | 1.002 | 1445 | 0.228 | 45.24, 45.40, 45.72, 45.66 |
| L13 | 1.057 | 65.6 | 1.411 | 48.91, 47.39, 48.86, 45.94 |

Pooled L13 = 47.89 cm vs L12's 45.53, a **+2.36 cm** move — but the chains
disagree by **2.97 cm**, larger than the move. Direction is as predicted and may
be real; this run cannot show it. **L12 stays canonical at 45.53 cm.**

**What diverged (per-chain 2nd-half medians, measured):**

| param | across 4 chains | verdict |
|---|---|---|
| `ais_c` | 88.8091 ×4, identical to 4 dp | **FROZEN**, never left its start |
| `ais_iceflow0` | 0.955 → 1.211 | **genuine, 24%** |
| `gis_amp` | 1.957 → 1.834 | modest, ~0.38 prior-sd |
| `gis_s_mid` | s 0.937 → 0.918 | fine, 2% |
| `gis_s_high` | s 0.260 → 0.249 | fine, 4% |

**The restructure's own parameters are NOT the problem** — both are absent from
postprocess's flag list and agree to 2-4%.

**`ais_c`'s R̂ = 2.239 IS NOT INTERPRETABLE.** All four chains sit at 88.8091 with
τ = 327k against 1M post-burn draws. Between- and within-chain variance are both
≈0, so the ratio is numerical noise. It is frozen, not diverging. Do not read it
as "twice as bad as L12."

**MY FIRST DIAGNOSIS WAS WRONG — do not repeat it.** I blamed the starts:
`build_overdispersed_starts.jl` picks draws at `ais_iceflow0` quantiles from the
L13tune chain, which has τ≈300k in the AIS block, so the L13 starts ARE degenerate
there (`ais_c` spread **1.15e-05** vs the L12-vintage file's **30.92**). True, and
worth fixing on its own — R̂ requires over-dispersed starts to be valid at all.
**But it does NOT explain the SLR failure:** L12 started its chains FAR APART in
`ais_c` and still agreed to 0.48 cm, so AIS start dispersion evidently does not
control the SLR median. **Why L12 passes and L13 fails with the same AIS pathology
is UNRESOLVED.** Find the mechanism before re-running — a re-run that fails the
same way costs ~4 h.

**Candidates, untested, in the order I would test them:**
1. **`gis_amp` — check this first.** It spreads 0.123 across chains (~0.38
   prior-sd) and its own prior block documents it as the DOMINANT control on the
   2100 projection (2100 spread runs 7.4 → 12.6 cm across its prior).
2. Greenland via the TAIL, not the median. SLR@2100 is driven by the upper tail
   (q95 ≈ 81 cm); per-chain medians agreeing does not clear it. Compare tails.
3. The shares term interacting with `gis_amp`/`gis_f` to create a ridge that did
   not exist in L12.

---

## 4. `--gis-check` WAS INERT FOR THE WHOLE L12 LINE (repaired)

Run first because the plan made it the gate — **it failed all four gates on
untouched HEAD**, and the control reproduces that byte-for-byte. Two silent
defects: (1) `GIS_OFFLINE_G0` is keyed on `gis_alpha_s`/`gis_beta_s`, which do not
exist in `FREE` under `GIS_REPARAM`, so both overrides were silently skipped and
θchk kept θ0's slow channel — under `--gis-ordered` that is the L11 ORD-half
medians, `r_s = 0.00526` vs the offline `0.01389`, a factor **2.6**; (2) the
offline vector legitimately has `alpha_s > alpha_f`, so the wedge rejected it
BEFORE `run(m)` and the diagnostic read the previous call's model state.

It PASSED without `--gis-ordered` only because θ0's MAP sat near the offline slow
channel — **broken in exactly the configuration that ships.** Repaired: the slow
pair is mapped into (ell, w); `WEDGE_OFF` bypasses the wedge for that one fixed
reference vector; `logposterior(θchk)` must be finite or it errors; no offline key
may match zero parameters without erroring (mutation-tested); and θchk pins the
basin scales at s=1 so a future L13-derived θ0 cannot break it. All four gates now
read **|diff| = 0.0000**, tighter than the unordered run that "passed."

**No published result is affected** (it is a diagnostic), but every "GIS WIRING OK"
printed under `--gis-ordered` is unverified. Its real update trigger is the
`GIS_ZONE` `"south"` → `"all"` switch, which will fail it LEGITIMATELY —
regenerate the reference, do not widen the tolerance.

---

## 5. TRAPS AND CONVENTIONS WORTH CARRYING TO THE AIS WORK

1. **File-layout name tables must NOT be built from the live `FREE`.**
   `L11_NAMES`/`L10_NAMES`/`L11A_NAMES` were, so two new rows lengthened them
   57→60 and the size dispatch MISSED the L12 covariance. Fails safe (warning →
   fresh diagonal) but discards the tuned proposal. Fixed via `prelayout()`.
   **All three tables had it. An AIS split will hit this again.**
2. **Judge acceptance on the TRACE, not the final number.** A 3000-iteration
   smoke gave 0.017 and looked like the ADCOV trap; the same configuration
   reaches 0.319 by 40k. The control plateaus by ~40% through while a name-mapped
   run starts at exactly 0.0 and climbs monotonically. Short-run acceptance is
   not a property of the layout.
3. **Verify wiring quantitatively.** Basins-on vs control differed in logpost by
   exactly the first-principles prediction (shares term +0.841, three new priors
   −0.677 = +0.164; −633.94 → −633.78), and their `--gis-check` gates were
   byte-identical. That is partition invariance confirmed in the live calibrator.
4. **The starts file is provenance.** Rebuilt from `L13tune` and COMMITTED,
   because the production chains started from it. The unexplained Aug-17 version
   was retired to `outputs/quarantine/20260819_unexplained_starts/` (on disk only
   — `outputs/` is gitignored; rationale in commit `9ab499d`).
5. `figures/diag_gis_regional_driver.png` churns because the script stamps
   `git rev-parse HEAD` into the suptitle. Verified the science is unchanged
   (r05 +0.714 vs global +0.159, ETCW 5.5×, −1.81 °C/century, reproducing commit
   `f74d70c`). Do not regenerate it casually.
6. macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1`.

---

## 6. FILES, FLAGS, TIMINGS

**New:** `greenland_3basin_component.jl`, `test_greenland_3basin_nesting.jl`,
`diag_l13_basin_shares.jl`, `run_l13_production.sh`.
**Changed:** `calibrate_mcmc_ext.jl`, `brick_mengel.jl`
(`build_brick_nu3_gis3`, `update_gis3_shares!`), `CHANGELOG.md` (19b).

**Flags:** `--gis-basins`, `--no-gis-shares`, `--gis-check`, `--gis-ordered`.

**Logs:** `outputs/mcmc/log_{GISB0CTRL,GISBNOSH,GISB1,GISB2,GISBTUNE,L13tune,L13_seed*,postprocess_L13,slrconv_L13}.txt`.

**Measured timings (M4, `OPENBLAS_NUM_THREADS=1`):** 1M single chain ≈ 3 h 20 m;
4 × 2M in parallel ≈ 4 h 25 m (chains contend — the single-chain ETA understates
badly); postprocess over 8.8 GB ≈ 12 min; SLR diagnostic ≈ 3 min.

**Open decisions for Marcus:**
- the AIS split (§1) — recommendation: not yet; start the IMBIE-3 data check now
- `GIS_ZONE` `"south"` → `"all"`, still deferred; NOT one line
  (`GIS_AMP` 1.92→2.347 and the amp prior on [1.51, 2.28] move with it)
- whether to add the high-basin volume tap (deferred; only bites near 2300)
