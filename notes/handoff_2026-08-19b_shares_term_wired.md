# Handoff — the sector shares term is WIRED; the open item is chain tuning

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `f577fdc`. Predecessor:
`notes/handoff_2026-08-19_calibrator_sector_shares.md` (the HOW-to-wire-it doc;
this one is what happened when it was wired).

**Bottom line: the term is built, gated, and committed, and all four of Marcus's
decisions are implemented. Three things the predecessor did not anticipate.
(1) `--gis-check` — the acceptance gate the whole plan rests on — has been
reporting STALE STATE for the entire L12 line; repaired, and it now reads
0.0000 on all four gates. (2) The reduced parameterisation contains a PROVABLY
FLAT direction, so it is two sampled parameters, not three. (3) Acceptance on a
3000-iteration smoke is 0.017 against a control's 0.268, which is WARM-UP, not a
broken layout — the 40k tuning chain reaches 0.233 by 14k and closes the
question. Nothing is blocking; no production chain has been run and no headline
has moved yet.**

---

## 1. MARCUS'S FOUR DECISIONS (2026-08-19), AS IMPLEMENTED

| decision | as built |
|---|---|
| **Reduced parameterisation**, k_b fixed, s_b free, no tap | `julia/greenland_3basin_component.jl`; k_b = Mouginot volume shares, FIXED. **But see §3 — it is 2 free knobs, not 3.** |
| **Driver switch deferred** to its own commit | untouched: `GIS_ZONE` is still `"south"`. Not a one-line change — `GIS_AMP` 1.92→2.347 and the amp prior N(1.92,0.32) on [1.51,2.28] move with it. |
| **Two modern windows, level shares, score south+mid** | `GISB_WINS` = (2002-2011), (2012-2018); `GISB_SCORED` = (south, mid); σ = 0.05. high follows by sum-to-one. |
| **Rebuild the starts for the new layout** | NOT yet possible, and that is a sequencing fact, not an oversight — see §6. |

---

## 2. `--gis-check` WAS INERT FOR THE WHOLE L12 LINE — the most important finding

The predecessor makes `--gis-check` the acceptance gate for this work, so it was
run first. **It failed all four gates on untouched HEAD**, and the control
reproduces that byte-for-byte, so it is not a regression from the restructure.

**Two independent silent defects:**

1. `GIS_OFFLINE_G0` is keyed on the NATIVE names `gis_alpha_s` / `gis_beta_s`,
   which **do not exist in `FREE` under `GIS_REPARAM`**. Both overrides were
   silently skipped, so θchk kept whatever slow channel θ0 carried. Under
   `--gis-ordered`, θ0's slow channel is deliberately overwritten with the L11
   ORD-half medians — giving `r_s = 0.00526` against the offline `0.01389`, a
   factor **2.6**, which is the entire four-gate failure.
2. The offline reference vector legitimately has `alpha_s > alpha_f` (it predates
   the ordering convention), so the wedge — a hard rejection evaluated BEFORE
   `run(m)` — rejected it, `run(m)` never happened, and the diagnostic read the
   PREVIOUS call's model state. It reported θ0's Mouginot share of 0.8699 as
   though it were the reference vector's.

**Why it went unnoticed:** without `--gis-ordered` it PASSED, because θ0's MAP
happened to sit near the offline slow channel. The defect was masked in exactly
the configuration that ships — `--gis-ordered` is the L12 canonical setting.

**Repaired** (all in `logposterior` / the `--gis-check` block): the offline slow
pair is mapped into (ell, w); `WEDGE_OFF` bypasses the wedge for this ONE fixed
reference vector; `logposterior(θchk)` must be finite or it errors; and **no
offline key may match zero parameters** without erroring. After the repair all
four gates read **|diff| = 0.0000** — *tighter* than the unordered run that
"passed" (0.0017/0.0031/0.0002/0.0005), which is how you can tell θchk is now
genuinely the reference vector. The no-silent-skip guard was **mutation-tested**
with a bogus key and fires.

**No published result is affected** (it is a diagnostic, not a model path), but
**every "GIS WIRING OK" printed under `--gis-ordered` should be treated as
unverified.** The L12 line never printed one.

---

## 3. THE REDUCED FORM HAS A PROVABLY FLAT DIRECTION — 2 knobs, not 3

The basin rate is `clip(s_b * (alpha*T + beta), 1e-9, 1)`. Scaling **every** s_b
by c while scaling the shared shape rates (`alpha_f`, `beta_f`, and `r_s` through
`ell`) by 1/c leaves the model **exactly** invariant.

**Measured, not argued:** `max|diff| = 0.0` for c in {0.25, 0.5, 2, 4}, and
1.1e-16 at c = 10 (pure roundoff), against a Greenland signal of 0.2279 m.

So the common mode of the three `log s_b` is a perfectly flat likelihood
direction, broken only by the priors. **Only the RATIOS carry information —
exactly what the shares term can identify (two independent shares per window).**
`GISB_REF = :south` is pinned at s = 1; mid and high are sampled and read as
"rate relative to the south basin". The overall level stays where it already
lived, in the shipped shape parameters.

Reproduce with the scratch driver pattern in §8 (the degeneracy script).

---

## 4. THE OPEN ITEM: acceptance, and why it is probably NOT a design problem

| run | shares term | 3000-iter accept |
|---|---|---|
| `GISB0CTRL` — no basins | — | **0.268** |
| `GISBNOSH` — basins, term OFF | off | 0.014 |
| `GISB1` — basins, term ON, 3 knobs | on | 0.012 |
| `GISB2` — basins, term ON, 2 knobs (ref pinned) | on | **0.017** |

**Two things are settled by this table.** The **shares term is innocent** — 0.014
with it OFF vs 0.012 ON, so the collapse comes from the added DIMENSIONS, not the
likelihood. And **the degeneracy was not the main driver** — pinning the flat
direction moved acceptance only 0.012 → 0.017. (It is kept anyway, on
identifiability grounds: a provably flat direction should not be sampled.)

**What the TRACE says, and this is the actual diagnosis.** Sample the running
acceptance rather than the final number:

- control: `0.5 → 0.44 → 0.32 → 0.259 → 0.261 → 0.262 → 0.268` — **plateaus by
  ~40% through.**
- basins:  `0.0 → 0.0024 → 0.0051 → 0.0067 → 0.0081 → 0.0088 → 0.0102 → 0.0105
  → 0.0117 → 0.0145 → 0.0156` — **starts at exactly 0.0 and is still climbing
  monotonically at the end.**

The control's covariance matches `NK` and is used AS-IS; the basins run
name-maps 57 rows and adapts the rest from a poor start. **3000 iterations is
too short for the enlarged layout** — the adaptation has not converged, so the
final number is not a property of the layout.

**CONFIRMED — the 40k tuning chain (`--tag=GISBTUNE`, seed 2026) settles it.**
Acceptance climbs `0.017 @3k → 0.0997 @8k → 0.233 @14k`, i.e. essentially the
control's 0.268. **The layout is fine; 3000 iterations was simply warm-up.** No
redesign is needed and the proposal-width suspicion below was never required.

Left on the record as the test that was NOT needed: had it plateaued near 0.02,
the next suspect was the initial proposal width on the new dims — `prop` gives
them `0.1*min(σ, (hi-lo)/4) = 0.05` dex against a smoke posterior sd of ~0.01
dex, and `GEO_PROP_SCALE = 0.02` is the precedent for a dedicated scale
(0.02 × 0.5 = 0.01, which matches).

**FINAL: the 40k chain finished at accept 0.319** — ABOVE the control's 0.268.
The layout is sound and the question is closed.

**Do not read the smoke posteriors as results.** `GISB1`'s 2nd half held only
**32 unique values in 1500 rows** — the chain had barely moved.

---

## 5. TRAP 1 IN A NEW DRESS, caught before it bit

`L11_NAMES` / `L10_NAMES` / `L11A_NAMES` are derived from the **live** `FREE`, so
the new rows lengthened them 57 → 60 and the `size(old,1) == length(L11_NAMES)`
dispatch MISSED the L12 covariance entirely. Fails safe (warning → fresh
diagonal) but throws away the tuned proposal shape. Fixed by filtering the basin
names out of the file-layout tables — the same principle the `ALL_SERIES` comment
already states. Verified in the log: *"name-mapped 57 of 57 rows of
adapted_cov_L11tune3_seed2026.csv"*.

**The lesson generalises: any table that describes a FILE's layout must not be
built from the live parameter set.** There are three such tables and all three
had the bug.

---

## 6. THE STARTS FILE — a sequencing fact, not an oversight

Marcus chose "rebuild for the new layout". **It cannot be done yet.** The loader
reads by column NAME and hard-errors on missing columns, so there is no
positional trap — but `build_overdispersed_starts.jl` picks REAL DRAWS from an
existing tuning chain, and no chain in existence contains `gis_s_mid` /
`gis_s_high`. The documented two-stage launch applies:

1. ✅ build the 3-basin state + shares term
2. ⏳ **common-start** tuning chain under the new layout (`GISBTUNE`, running)
3. rebuild `overdispersed_starts.csv` from THAT chain
4. production with `--overdisperse`

`outputs/mcmc/overdispersed_starts.csv` therefore stays modified-uncommitted and
simply **goes stale** — the new layout cannot load it at all (the guard refuses).
It still matters if anyone re-runs an L12-layout chain; flag it again then.

### The run is NAMED L13, and it is LAUNCHED

Marcus chose "match the L12 production configuration" (2026-08-19), so the layout
is **L13 = L12 + the 3-basin sector restructure**, and
`julia/run_l13_production.sh` mirrors `run_l12_production.sh` exactly — 4 × 2M,
seeds 2026-2029, `--gis-ordered --gis-basins --overdisperse` — with the
precondition checks adapted to assert the `gis_s_mid` / `gis_s_high` columns.

**`L13tune` (1,000,000 iterations, seed 2026) was LAUNCHED at 07:44 on
2026-08-19** and is the blocking step. Measured rate ≈ 3,000 iter/min, so:

| step | estimate |
|---|---|
| `L13tune`, 1M | **~5.5 h** |
| rebuild starts from it | seconds |
| `run_l13_production.sh`, 4 × 2M | **~11 h** (4 chains in parallel, 1 thread each) |

NB the L10 note in the production script reports 2M in 2h15m, which is ~5×
faster than the rate measured here. That discrepancy is NOT resolved — the
measured runs overlapped with other julia processes, so 3,000 iter/min may be
pessimistic. Re-measure from `L13tune` on a quiet machine before trusting the
11 h figure.

**Next session, in order:** check `L13tune` finished → rebuild the starts →
`./julia/run_l13_production.sh` (it refuses to run if any precondition fails) →
`postprocess_mcmc_ext.jl --tag=L13 --accept-slr`.

---

## 6a. THE TWO ARTEFACTS: both KEPT, the cruft around them retired (Marcus 2026-08-19)

**`--gis-check` — KEEP. It has coverage nothing else has.**
`validate_greenland_ab.jl` READS the driver from a CSV and feeds it in;
`--gis-check` runs the real `logposterior`, whose driver is built from
`t_gis_zones.csv[GIS_ZONE]` + the amp splice + the anchor offset. **The driver
construction, the splice, the calibrator frame and the `S.gis` index alignment
are tested by `--gis-check` and by nothing else** — exactly the class that broke
silently for the whole L12 line (§2).

*Hardened:* θchk now pins the basin scales at s = 1, because the 3-basin model
equals A+B only there. θ0 carries s = 1 today by accident (the basin params are
absent from the MAP/medoid CSVs and fall back to their prior centre), but once θ0
is rebuilt from an L13 posterior that accident ends and the gate would fail for a
reason unrelated to the wiring it tests.

*Its real update trigger* is the `GIS_ZONE` `"south"` → `"all"` switch: the
offline reference was fitted on the south driver, so it will fail LEGITIMATELY
then. Regenerate the reference — **do not widen the tolerance.**

**`overdispersed_starts.csv` — KEEP the file, RETIRE the modification.** It is
referenced by 10 files including every production script, and R̂ is only valid
with over-dispersed starts. What was retired is the uncommitted 2026-08-17
modification that rode along for six handoffs with no record of its provenance:
it is unusable going forward anyway (the loader reads by column NAME and
hard-errors, so the L13 layout cannot load it at all), committing it would have
silently changed what future chains start from, and leaving it in the tree
invited silent retrieval by any L12 re-run.

Preserved at `outputs/quarantine/20260819_unexplained_starts/` with a README
(**on disk only — `outputs/` is gitignored**, so the rationale lives in commit
`9ab499d` and here). Tree restored to committed HEAD = the L12-vintage starts the
canonical posterior actually used. `.pre_l12_bak` was deleted as **byte-identical
to HEAD** (md5 `1f3ce48…`) — git already held it. `.pre_extc_bak` is a genuinely
distinct earlier vintage and was left alone.

**RESOLVED — `figures/diag_gis_regional_driver.png`, modified-uncommitted for
seven handoffs, was pure churn.** `python/diag_gis_regional_driver.py:92` stamps
`git rev-parse --short HEAD` into the figure's suptitle, so **any incidental
re-run dirties the PNG whether or not the science moved.** That is the whole
explanation for seven handoffs of noise. Tree restored to HEAD; do not regenerate
it casually.

**Verified, not assumed.** The byte delta was only 230 bytes (consistent with a
title string), but its main input `outputs/recalib_targets_ext.csv` was touched
2026-08-12, six days AFTER the figure was committed — so a cosmetic-only diff
could not be inferred. Re-ran the script: **r05 +0.714 vs global +0.159, ETCW
5.5x, 1940-1990 trend -1.81 C/century**, reproducing the numbers recorded in
commit `f74d70c` (+0.71 / +0.16 / 5.5x) exactly. The 08-12 target revision does
not touch the GIS column over 1900-2018.

**Keep the figure.** It is the evidence behind adopting the regional Greenland
driver — the foundation of the whole Greenland arc, and the reason
`GIS_ZONE`/`GIS_AMP` exist at all. It is a CLOSED diagnostic, though, not a live
one: it reads only the GIS target and two obs temperature series, and touches
NOTHING the L13 analysis produces, so there was never a reason to wait for the
chains. It is equally unaffected by the deferred `south` -> `all` switch.

---

## 7. NESTING — the gate that says the restructure adds nothing by itself

`julia/test_greenland_3basin_nesting.jl`, all pass:

| gate | result |
|---|---|
| [1] collapse, k=(1,0,0), s=1 → reproduces `greenland_ab` | 0.0 |
| [2] additivity at production shares | 2.2e-16 |
| [3] partition invariance, Mouginot k, s=1 → total does not move | 4.4e-16 |

[3] is the strong one: it fails on clamp / initial-condition / k wiring errors
that a single loaded basin would hide. **It was also confirmed inside the live
calibrator**, independently: the basins-on and control `--gis-check` A+B gates
are byte-identical, and the logpost difference is exactly the first-principles
prediction — shares term +0.841 (four z-scores from the volume-share null) plus
three new priors −0.677 = +0.164; observed −633.94 → −633.78.

At s = 1 the shares come out at the VOLUME shares exactly (0.456/0.173/0.371)
against observed 0.592/0.207/0.201. **That gap is what the calibration must
close, and it is the number to watch.**

---

## 8. FILES AND FLAGS

**New:** `julia/greenland_3basin_component.jl`,
`julia/test_greenland_3basin_nesting.jl`.
**Changed:** `julia/calibrate_mcmc_ext.jl`, `julia/brick_mengel.jl`
(`build_brick_nu3_gis3`, `update_gis3_shares!`), `CHANGELOG.md` (entry 19b).

**Flags:** `--gis-basins` (3-basin state on), `--no-gis-shares` (basins with the
term OFF — the handoff's step 2, and the diagnostic that exonerated the term).

**Logs:** `outputs/mcmc/log_{GISB0CTRL,GISBNOSH,GISB1,GISB2,GISBTUNE}_seed2026.txt`.

**RESOLVED (Marcus 2026-08-19): the commitment clamp is PER-BASIN**, `[0,
k_b*v0]`, not the prototype's whole-sheet `[0, v0]`. It is also the form that
keeps the partition exact — `min(max(k*x,0), k*v0) == k*min(max(x,0), v0)`, so
`eq_b == k_b * eq_whole` identically, saturated or not. The prototype's form
agrees over the hindcast (the cap never binds there, so its P1/P2/P3 stand) but
BREAKS additivity once the commitment exceeds v0. All three nesting gates
unchanged, which also proves the cap binds nowhere through 2300 under ssp245 —
so the tuning chain was unaffected by the change.

**Still true from the predecessor:** expect SLR@2100 = 45.53 cm to MOVE once a
production chain runs; say so before it surprises anyone. macOS has no `timeout`;
pin `OPENBLAS_NUM_THREADS=1`.
