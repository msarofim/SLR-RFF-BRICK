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

The chain was still running at handoff; let it finish, then §6 step 3.

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

**Flagged, not silently resolved:** the per-basin commitment is clamped to the
WHOLE-SHEET [0, v0] as the prototype's `ab_series()` does, not to `k_b*v0`. The
two agree at the nesting point and across the hindcast, and differ only for the
high basin late under SSP5-8.5. One-line change if wanted.

**Still true from the predecessor:** expect SLR@2100 = 45.53 cm to MOVE once a
production chain runs; say so before it surprises anyone. macOS has no `timeout`;
pin `OPENBLAS_NUM_THREADS=1`.
