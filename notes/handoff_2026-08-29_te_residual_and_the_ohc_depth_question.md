# Handoff — the TE modern residual: cap the noise FIRST, then re-test the depth split. Both are diagnostics, neither is a shipped change yet.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, in sync with origin.
Written 2026-08-29 to be picked up cold. **L21 IS CHAMPION** (promoted 2026-08-28, all six
modules) — see `CHANGELOG` [DECIDED] 2026-08-28 and memory `l21_champion_calib160`.

---

## 0. THE ONE-PARAGRAPH STATE

The calib 1.6.0 + CMIP7 migration is **done**; L21 (L14's config on the new drivers) is champion and
the model document is regenerated against it. One thing came out of the migration that is **not
resolved**: **thermal expansion is now 17σ high at 2025** against the best-observed part of the
record, while every other component and the (out-of-sample) total sit near zero. Three hypotheses
were raised. Two are **already tested and the results are counter-intuitive** — read §2 before
running anything, because the obvious explanation is the one that failed. What is left is a
three-step diagnostic, in a fixed order, and **step 1 changes what steps 2 and 3 mean.**

---

## 1. ⇒ THE THREE TASKS, IN THIS ORDER

### TASK 1 — CAP THE STERIC NOISE AND REFIT. This is the load-bearing run.

**Why.** The likelihood can buy off the modern misfit. `hetero_logl_ar1`
(`calibrate_mcmc_ext.jl:130`) builds

```
Σ = σ²/(1−ρ²) · ρ^|i−j|  +  diag(ε²)
```

so the AR(1) process sits **on top of** the observational variance ε², with a **free** σ (`sd_steric`)
and a **free** ρ (`rho_steric`). Fitted values:

| | `sd_steric` | `rho_steric` | **AR(1) marginal sd** |
|---|---|---|---|
| L14 | 0.0666 | 0.9572 | 0.230 cm |
| **L21** | **0.0718** | **0.9630** | **0.266 cm** |

The modern observational ε is **≈0.049 cm**. So the model's own noise term is **5.4× the
observational sigma** — a persistent modern offset costs the likelihood almost nothing.

**⚠⚠ THE TRAP THAT WILL MAKE A NAIVE CAP DO NOTHING.** Capping `sd_steric` at the observational
sigma **does not bind**, because ρ inflates it by `1/√(1−ρ²) = 3.71×`. σ = 0.0718 *looks*
comparable to ε = 0.049; the marginal it implies is 0.266. **The cap must bind the MARGINAL
`σ/√(1−ρ²)`, or ρ must be capped alongside σ.** Capping σ alone leaves ~all of the absorption in
place and the arm will look like a null result when it never tested anything (`no_power_null`).

**What to run.** An arm identical to L21 except for the steric noise bound. Tag **L22**. Copy
`run_mcmc_L21.sh`; the only change is the steric noise prior/bound. Everything else — amp
N(0.95, 0.10), `adapted_cov_L14tune_seed2026.csv`, `--overdisperse` on the canonical starts,
`--gis-ordered --gis-basins2`, 4×2M — stays L21's.

**REGISTER BEFORE RUNNING:**
* If the modern TE residual **collapses toward ~2σ**, the 17σ was the noise model, **not** the
  functional form, and the fix is a likelihood constraint. Then TASK 2 is about the *projection*,
  not the fit.
* If it **stays large**, something else holds TE and the depth split becomes the live candidate.
* ⚠ Expect the hindcast to look **worse** on some other axis — that is the cap working, not a
  regression. Report what moved.

### TASK 2 — RE-TEST THE DEPTH SPLIT (option 1) UNDER THE CAP

**Why re-test.** The offline result below was obtained with weights = the target's own sigma and
**no free noise scale** — i.e. it is *already* the capped case, but on a WLS fit rather than the
full posterior. Under the cap, the two-coefficient form's advantage may be larger or smaller than
the offline number; that is exactly what TASK 1 makes measurable.

**What option 1 is.** BRICK's `thermal_expansion` already takes `ocean_heat_mixed` and
`ocean_heat_interior` as separate inputs and **sums them in the first line of the equation**
(`thermal_expansion_component.jl`). Worse, MimiBRICK sets `ocean_heat_mixed` to **`zeros(...)`**
(`MimiBRICK.jl:126`) and Ladrillo never overrides it (`brick_mengel.jl:93` sets only
`ocean_heat_interior`), so **the split is 0 : everything.** Option 1 = feed FaIR layer 0 as
`mixed`, layers 1–2 as `interior`, and give BRICK **two** expansion coefficients.

**Measured offline (WLS on the ensemble-mean driver, weighted by the target's own sigma):**

| window | 1-coeff | 2-coeff |
|---|---|---|
| 1900–1950 | 1.90σ | 1.76σ |
| 1951–1992 | 1.09σ | 1.04σ |
| **1993–2025** | **2.15σ** | **1.96σ** |

`α_mixed / α_interior = 1.70×` — the right sign and roughly the right size for the temperature
dependence of seawater expansion, so the mechanism is real.

**⚠ THE HISTORICAL GAIN IS 8% AND THAT IS NOT THE ARGUMENT. The argument is the PROJECTION:**

| year | 1-coeff | 2-coeff | diff | surface share |
|---|---|---|---|---|
| 2025 | 3.31 | 3.30 | **−0.01** | 0.132 |
| 2100 | 17.72 | 17.12 | −0.60 | 0.081 |
| **2300** | **40.29** | **38.11** | **−2.18 cm (5.4%)** | 0.046 |

Identical where they were fitted, diverging monotonically as the surface share collapses. The
one-coefficient form **overstates** long-run TE because it keeps crediting deep heat at an
efficiency calibrated when heat was shallower. ~1% of total 2300 GMSL at ssp245 — one-directional,
accumulating, not noise.

### TASK 3 — IS FaIR's 3-BOX SPLIT A DEFENSIBLE MAPPING? (do this BEFORE shipping option 1)

FaIR's boxes are an **energy-balance abstraction**, not observed ocean layers. Mapping layer 0 →
"mixed" and layers 1–2 → "interior" is an assumption that has **not** been justified. Ways to test
it, cheapest first:

1. **Does the implied α ratio match seawater physics?** The offline fit gives 1.70×. Check that
   against the actual temperature dependence of the thermal expansion coefficient between a
   mixed-layer temperature and a deep-ocean temperature. If physics says ~2–3× and the fit says
   1.70×, the mapping is roughly right; if it says 1.0× or 6×, it is not.
2. **Compare the layer split to an observed depth-resolved OHC product** (e.g. 0–700 m /
   700–2000 m / >2000 m). If FaIR's layer-0 share tracks the observed 0–700 m share over
   1993–2025, the mapping has empirical support. ⚠ `README_modern_extensions.md` records that NOAA
   steric is **0–2000 m only**, so the deep term needs a separate source.
3. **Effective depths.** `ocean_heat_capacity[0..2]` implies a layer thickness via
   `C = ρ·c_p·h`. Check whether the implied h for box 0 is plausibly a mixed layer (tens of m) or
   is really a few hundred m — that alone may settle it.

---

## 2. ⚠⚠ READ THIS BEFORE RUNNING ANYTHING — TWO HYPOTHESES ARE ALREADY DEAD

**(a) "TE is worse because the driver got worse." NO — the driver got BETTER.** OHC RMSE vs
Zanna/IGCC improved **44%** (6.80 → 3.83). The gain is **early-record**; the new OHC driver is
~8.6e22 J *lower* post-1950, with the change concentrated in 1900–1950 and flat after. `thermal_alpha`
rose **7.0%** (0.1595 → 0.1708, +1.34 sd) to recover the early rise the driver no longer supplies,
and then overshoots the modern era. **A scale parameter absorbing a shape change.**

**(b) "The one-coefficient FORM cannot fit the modern data." NO — IT CAN.** A plain WLS of the
*current* one-coefficient form lands at **2.15σ** in 1993–2025, not 17σ. **So the structure was
never the binding constraint.** This is why TASK 1 comes first and why I was wrong when I first
diagnosed this as structural. Do not re-derive it.

**(c) The likelihood-weighting is NOT missing.** `hetero_logl_ar1` does use the per-year ε, and the
steric target genuinely tightens **5.1×** (early mean σ 0.509 cm → modern 0.0998 cm). The weights
are right; the free noise term is what neutralises them.

---

## 3. THE RESIDUAL, FOR REFERENCE

L21 TE bias in units of **the target's own sigma**:

| year | bias (cm) | target 1σ | **σ** |
|---|---|---|---|
| 1900 | −0.116 | 0.613 | −0.19 |
| 1950 | +0.113 | 0.457 | +0.25 |
| 2000 | +0.232 | 0.110 | +2.11 |
| 2018 | +0.683 | 0.095 | +7.23 |
| **2025** | **+0.847** | **0.049** | **+17.29** |

Near-perfect where the data are weakest, 17σ off where they are strongest. **`total` is
`in_sample = False`** (the D1 "drop the total" change) — so the total agreeing well is an
*out-of-sample* success while TE, which *is* fit, is the one drifting. Components partly cancel: at
2018 TE is +0.683 but AIS −0.122, glaciers −0.069, GIS −0.004, so the total lands at +0.364.
`d2_steric_1` (the discrepancy basis) **more than doubled** at the migration, 0.1168 → 0.2549.

---

## 4. TRAPS — ALL THREE BIT SOMETHING THIS WEEK

* **⚠ SMALL DENOMINATORS. This bit THREE separate analyses in two days.** The glacier early/modern
  through-origin fit (z = 3.5/4.4 that vanished to <1σ with a free intercept); the Coulon selector
  MAX; and the layer-sum gate below. **Any ratio whose denominator crosses zero near a baseline is
  meaningless there.** Compare in absolute terms, or restrict to where the denominator is real.
* **The layer decomposition IS correct** — `Σ_k C_k·ΔT_k` reproduces FaIR's own
  `ocean_heat_content_change` to **0.7–3.9%** wherever |OHC| > 5e22 J. The gate's first version
  reported "ratio 0.22–8.19, decomposition WRONG" purely from baseline-crossing years. Do not
  re-derive that scare.
* **A gate must not read a path its own script writes** (cost the FaIR session a silent pass).
* **`fair_mean_*_ssp245harm.csv` ≠ `fair_mean_*_ssp245.csv`** — harmonized vs RCMIP-native. The
  calibration reads `FORCING_TAG = "ssp245harm"` (`calibrate_mcmc_ext.jl:148`). Substituting them
  is worth ~0.1 K and has bitten twice.

---

## 5. COMMANDS

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
uptime; sysctl -n vm.swapusage          # ⚠ eta_in_days_is_not_a_slow_run: check FIRST
bash run_mcmc_L22.sh                    # after copying run_mcmc_L21.sh + the noise cap
bash run_l21_postprocess.sh             # retarget T=L22
```
Read the meter's ETA at ~5 min. **ETA in DAYS = kill and requeue**, do not wait.

**The layer series already exists** and does not need regenerating:
`FaIRtoFrEDI/fair_outputs/diag_fair_ohc_layers_full.csv` (year, H0, H1, H2, ohc_fair, 1e22 J,
ensemble mean, ssp245harm on calib 1.6.0), produced by
`FaIRtoFrEDI/diag_fair_ohc_layer_share.py`.

---

## 6. STATE AND OPEN ITEMS

* **L21 is champion**; `benchmark/reference/L14/` is frozen and L14 stays reproducible against its
  own drivers. Pre-migration outputs: `outputs/quarantine/20260828_calib160_migration/`.
* **Model document**: `deliverables/ladrillo_model_document_DRAFT.md`, regenerated against L21.
  ⚠ **C7 currently says TE is worse than BRICK 2.0 (1.236) and calls it OPEN.** If TASK 1 resolves
  it, C7 must be rewritten — it is the concern most likely to move.
* **Coulon arms** are integral-centred on **our own** ensemble, not matched to Coulon's own
  integral. The FaIR session was fetching post-2100 ESGF extensions for UKESM1-0-LL,
  IPSL-CM6A-LR, CESM2-WACCM, MRI-ESM2-0 (**8 of 8 cells exist**; 2 of 4 landed in
  `data/cmip6_coulon/`). ⚠ **UKESM extended only `r4i1p1f2` while our series is `r1i1p1f2`** — a
  member change *inside* the integration window. **Marcus's call, not yet made.**
* **Not attributable**: the Coulon width moves (tant12 0.71→0.65×, tant14 1.01→0.96×) confound
  L14→L21 **and** the endpoint→integral selector change. An integral-centred L14 run would
  separate them; not run.
* **`pai_series.py` guard asymmetry** — `model_series_files()` raises only on *missing* columns, so
  a correctly-schema'd stray `tas_series_*.csv` is added as a MODEL **silently**. It was built to
  catch a *dropped* model and is blind to an *added* one. Not patched; a naive "expected count"
  assert would be worse than none.
