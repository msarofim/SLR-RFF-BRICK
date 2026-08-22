# Handoff — the Greenland diagnosis survives; every CELL chosen against these bands does not; and the binding constraint is that the post-2100 target set is one ice-sheet model

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, pushed through `7e6ce4c`.
Written 2026-08-22, to be picked up cold.

**Supersedes** `handoff_2026-08-22_greenland_flux_deliverable.md` for its **§1.2 ranking**
and its **§5 stage-1a/1b entries**. Its §1.1, §1.3, §1.4, §2, §3 and §7 are **unchanged**
— and §1.1 and §1.3 are now *confirmed*, with their domains measured rather than asserted.

**Read with** `notes/addendum_2026-08-22c_amp_and_rate_rank.md` (§4b–§4g), which is the
detailed record. This handoff is the executive layer.

---

## 0. THE ONE-PARAGRAPH VERSION

The step-back's **diagnosis** holds and is GCM-robust: the linear `L_eq` is the defect
(§1.1), no fixed-V reservoir can ever match `x2300` (§3.1, 0/1080 and band-independent),
and the flux ψ ≈ 0.28 cm/yr is invariant to the amplification law (1.01× across a 1.48×
amp spread). What does **not** hold is **any cell chosen against these bands** — shipped,
A and B alike: **two single GCMs each void the entire admissible set**, CESM2 through the
ssp245 matched band and MPI-ESM1-2-HR through ssp585. Chasing that down showed the raw
bands were never too *wide*, they were arbitrarily **placed** and **spuriously precise**:
our own drive route explains **R² = 0.95** of the across-GCM spread, and once sampling
error is respected the honest **cool bands are 3–9× WIDER than shipped** — so the cool
arms **cannot constrain k at all**, and the k = 2–3 vs k ≤ 1.0 tension is a disagreement
of **preferences**, not a box. **The binding constraint on everything is that every
post-2100 anchor is NORCE-CISM with 1–5 GCMs per arm.** Three independent sources are now
on disk to break that; none is wired in.

---

## 1. WHAT SURVIVES, AND WHAT DOES NOT

**Survives** — every one of these compares to a **median**, or is band-independent:

| finding | evidence |
|---|---|
| §1.1 the commitment-law defect | φ=1 ceiling 1.93×/2.41× short on the warm arms, vs their own medians; holds 1.93–3.81× under all four amp laws |
| §3.1 no fixed-V reservoir matches `x2300` | 0/1080 grid-wide, and **band-independent**: grid best 81.3 vs the single slowest run 122.2 |
| ψ ≈ 0.28 cm/yr | 0.279–0.282 across four amp laws spanning 1.652 → 1.114 effective amplification |
| the amp law above 2.75 K is **exactly hindcast-inert** | bisected rate scale identical to all digits, spread 1.000000× |
| §1.3 the ψ degeneracy | ≤1.011× (median 1.003×) at τ≥800 with w fixed, grouped by (ψ, **onset**) |
| the k **preference** | cool arms' rms argmin vs medians = 0.75–1.0, robust **8/8** GCM drops |

**Does not survive:**

* **Every cell selection.** CESM2 → 0/1080; MPI-ESM1-2-HR → 135/33/0. Different
  mechanisms: CESM2 collapses the **ssp245** matched band to 10.1–12.3 so our base 18.3
  falls out and — the reservoir being inert below onset — **no cell can repair a cool-band
  failure**; MPI raises the **ssp585** floor 42.9 → 77.6.
* **The cool-arm exclusion of k ≥ 1.5.**
* **Anything resting on a post-2100 band EDGE.**

---

## 2. THE FOUR THINGS THAT CHANGED THE PICTURE

### 2.1 Most of the GCM spread is local temperature we already track
On ssp585 r2300 (n=5, after fetching UKESM1-0-LL) our **own production GMST route**
explains **R² = 0.95**, rank r 0.90, and only **23 %** of the band width survives it.
Adding the arm's *largest* member improved the fit (0.92 → 0.95). Cool arms (n=2) give
**0.49× / 0.78×** of the pairwise gap as guidance.

⚠ **Driving with the GCM's own regional T makes it WORSE** (R² 0.80). `c1` was calibrated
on the observed south driver and absorbs the level. **Do not "fix" this by swapping in
regional T.**

### 2.2 Width was never the problem — placement and precision were
The naive min/max residual band collapses ssp245 to **1.5 cm** and *excludes our own
base*. With a Student-t prediction interval:

| scenario | n | SHIPPED | t-PI | widths |
|---|---|---|---|---|
| SSP1-2.6 | 2 | 6.2–15.9 | −35.7–56.8 | 10 → **93** |
| SSP2-4.5 | 2 | 10.6–21.5 | 0.3–33.1 | 11 → **33** |
| SSP5-8.5 | 5 | 42.9–145.0 | 18.5–150.9 | 102 → 132 |

The **residual band is stable** where the raw one is not (741–763 over the 4 defined
drops, none zeroed, vs raw 750 → 126). ⚠ **No leave-one-out is defined on a 2-GCM arm** —
dropping one leaves a single model.

### 2.3 The cool arms cannot constrain k at all
On the residual basis the cool criterion is "is 0 inside the residual interval". With
n = 2 the half-width is exactly **11.0·|d₁−d₂|**, **non-monotone in k**, swinging 8× /
43×. **Do not report this as "the ceiling relaxes to k ≤ 50".** The test has no power.

### 2.4 The 2100 over-prediction is model-side, not driver-side
The "we apply a north-sized amp to a south driver" reading was **WRONG**: 1.33×
decomposes as **1.2864×** (`obs_amp_full/r_anchor` — memory `ladrillo_gis_amp` item 3,
"KEEP THE OBSERVED LEVEL", a design choice) × ~1.04× flat-hold. A like-for-like driver
**worsens both horizons** (2100 |log| 0.313 → 0.340; 2300 0.430 → 0.782) ⇒ **refuted**.
The by-product is the lead: the shipped 2100 error is **systematic** (all 9 GCM-cases
fast, median 1.39, independently reproducing §8's "20-45 % fast"), while like-for-like
*scatters* it. **Systematic ⇒ model-side ⇒ correctable. Look there.**

**There is no refit to do and none available:** `c1`/`c0` are fixed by the historical fit,
whose driver is observed through 2024; `gis_offline_cell.py`'s objective is history-only
(`PROJ_*` is "G4 EVALUATION ONLY, never in the objective", line 206). Anything that would
respond has to be the MCMC chain.

---

## 3. THE SCORECARD IS NOW STATED ON MEDIANS

`python/scope_gis_median_scorecard.py`. LOSS = weighted mean of |log(ours / PROTECT
median)| over the four horizons **plus the 2250-2300 rate**, RMS over arms. p05/p95 are
never read. **It emits no admissible set, deliberately** — a band would reintroduce the
edge dependence being removed. Best cell unchanged under **6/8** drops, ψ 0.500-1.000, and
it never goes to zero. Cell A ranks 43/775; the untapped base 771.

⚠ **The rate term is not optional.** Without it the ranking re-selects the wide-ramp w=8
cell that stage 1a rejected for trading the rate away.

---

## 4. NEW DATA ON DISK — `data/gis_post2100/`, 4.9 GB, NOTHING WIRED IN

| dir | size | what | first use |
|---|---|---|---|
| `ismip6_scalars/` | 2.1 MB | **16 ice-sheet models at 2100** + per-GCM atmosphere and **ocean thermal** forcing | the §2.4 systematic 2100 bias — and 2100 is the only horizon with independent evaluation |
| `greve_chambers_2022/` | 4.6 GB | **SICOPOLIS to year 3000**, independent of CISM | test the τ prior in `greenland_3basin_component.jl`, which cites this very paper and is "A PRIOR SPECIFICATION, NOT A FIT" |
| `climberx_10kyr/` | 256 MB | CLIMBER-X coupled 10 kyr, `V_sle.nc`/`tg.nc` already scalars, + `eqco2` branches | the φ=1 commitment ceiling (§1.1), the conclusion that survived everything |

Archives are **gitignored**; README + PROVENANCE.txt are tracked and carry the DOIs.
⚠ Greve is 4.6 GB of full output for what we need as a scalar series — **fetch
selectively next time**. Greve and CLIMBER-X are each **single-model**: they break the
one-model limitation post-2100 but do **not** supply structural spread.

Also new: `data/cmip6_gis_extra/tas_series_gis_UKESM1-0-LL.csv`. It was never missing —
`reduce_cmip6_tas_gis.py` caps at **40 models alphabetically** and stops at NorESM2-MM.
⚠ It is in a **separate directory on purpose**: `diag_gis_amp_cmip6.py` **globs**
`data/cmip6_gis/` (line 275), so a 41st file there would silently change
`gis_amp_shape.csv` on any re-derivation.

---

## 5. WHAT TO DO NEXT

1. **ISMIP6's 16 models vs our 2100 over-prediction.** Cheapest, uses the smallest file,
   and attacks a *systematic* well-conditioned defect at the only horizon with
   independent evaluation. This is the recommended start.
2. **Greve's year-3000 runs vs the τ prior.** Directly tests a shipped prior against its
   own cited source.
3. **CLIMBER-X `eqco2` vs the φ=1 ceiling.**
4. **§3.2's two-stage gate** — `corr(d(history)/dp, d(2300 rates)/dp)`; still the stated
   precondition for "fit the ensemble first".
5. **§4.1 the NPV sensitivity to τ** — still unrun; deprioritised by Marcus, not closed.
6. **Stage 2 only after** the target set can support it.

**Two choices still FLAGGED, not resolved:** `RESID_FORM` (additive vs multiplicative)
and `RESID_INTERVAL` (minmax vs t-PI); both computed and printed. Promoting the rate
criterion into `scope_gis_reservoir_offline.py` also remains a separate call — it moves
a cell, and would overwrite the provenance for 86/216.

---

## 6. TRAPS ADDED THIS SESSION

* **A band built from clustered runs inherits the clustering, and its EDGE is where one
  cluster shows up.** The r2300 rate band's p05 *is* the lowest per-GCM median.
* **Group by every axis the claim holds fixed**, not just the one it is about — grouping
  the ψ degeneracy by ψ alone folded in the onset spread and *understated* it.
* **`r.name` on a pandas row is the INDEX**, not the `name` column.
* **A leave-one-out is undefined on a 2-GCM arm**; min==max silently yields a zero-width
  band that reads as "load-bearing GCM".
* **Spreads do not add** — a max-min "decomposition" gave residual/total > 1. Use
  explained variance.
* **Rank on the criterion that binds**: stage 1a returns GO on `rms_all` (a LEVEL score)
  while the RATE pass count goes to zero.
* **Derive targets from `gis_targets`**, never a literal — a hardcoded 98.5 goes stale.

## 7. FILES

**New this session** — `python/`: `diag_gis_amp_above_275.py`,
`scope_gis_reservoir_rate_rank.py`, `diag_gis_scorecard_logo.py`,
`diag_gis_gcm_tdecomp.py`, `reduce_cmip6_tas_gis_extra.py`,
`diag_gis_residual_band.py`, `diag_gis_k_vs_residual.py`,
`diag_gis_amp_likeforlike_2100.py`, `scope_gis_median_scorecard.py`.
All read-only, all with their own CSV + log in `outputs/`.

**Unchanged** — nothing in `julia/`, **no gate changed, no cell moved, no chain started**,
and `scope_gis_reservoir_offline.py` + its CSV are untouched so 86/216 still reproduces.
The D1-D5 change set (`spec_2026-08-14_next_calibration.md`) is still NOT STARTED.
