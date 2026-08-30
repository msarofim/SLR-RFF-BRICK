# The Coulon comparison, reported as a bound on both averaging domains

**Status:** technical write-up of a DECIDED result. Delivered 2026-08-29.
**Interpretation and framing are Marcus's** — the placeholders below are deliberate.

## Provenance

| field | value |
|---|---|
| climate model | **FaIR 2.2.4 (calib 1.6.0)**, CMIP7-harmonised drivers |
| SLR model | **Ladrillo L21** (champion since 2026-08-28) |
| posterior | `parameters_subsample_brick_mengel_L21.csv` |
| forcing / scenario | **ssp585**, SPLICED convention, `fair_cube_gmst_ssp585_spliced.csv` |
| ensemble | 841 configs |
| comparator | Coulon et al., PMC12680641 (full text read, not a summarisation pass) |
| anomaly baseline | **1995–2014** mean |
| integral window | **2015–2299** |
| units | endpoint **K**; integral **°C-century** |
| build path | `build_coulon_allcells_series.py` → `data/cmip6_coulon_allcells/` (companion; `data/cmip6_coulon/` UNTOUCHED) |
| diagnostics | `python/diag_coulon_integral_bound.py`, `python/diag_coulon_domain_reachability.py` |
| commit | `d17f582` |

## Why a bound and not a number

**The paper never states its averaging domain.** This was verified against the PMC full
text, not inferred. Both defensible readings — a land proxy (`sftlf >= 50`) and an
all-cells average — are therefore carried, and the comparison is reported as a **bound
spanning them**. Marcus ruled option (c) on 2026-08-29: *report both domains, rebuild nothing*.

> ⚠ **The `ais_gmst_amp` frame precedent does NOT transfer.** There, frame ambiguity was a
> reason to prefer *fit* — but "fit" meant fit to our **own observational targets**. Here it
> would mean agreement with the very number being compared against, i.e. tuning to the
> comparator. That is why the domain is bounded rather than selected.

## Acceptance gate

The all-cells series is an independent build (it re-reduces the ≤2100 leg from the Pangeo
zarr rather than reusing the already-land-masked `data/cmip6_pai/` leg). It reproduces the
**published endpoint table to ±0.00 K on all four models and both domains**, tolerance
0.02 K. JOIN gates 0.009–0.156 K.

## Results

### Endpoint, T_ant at 2300 (K)

| model | land proxy (`sftlf>=50`) | all cells | amp needed (land) | amp needed (all cells) |
|---|---|---|---|---|
| MRI-ESM2-0 | 12.78 | 12.47 | 0.830 | 0.810 |
| UKESM1-0-LL | 15.49 | 13.90 | 1.006 | 0.903 |
| IPSL-CM6A-LR | 17.09 | 14.67 | 1.110 | 0.953 |
| CESM2-WACCM | 19.47 | 17.12 | 1.264 | 1.112 |

**Reachable at the median amp: 1 of 4 (land) | 2 of 4 (all cells).**
Reachable = MRI under land; MRI + **UKESM** under all cells.

### Integral, 2015–2299 (°C-century)

| model | land proxy | all cells | difference | amp needed (land) | amp needed (all cells) |
|---|---|---|---|---|---|
| MRI-ESM2-0 | 23.59 | 23.10 | −0.49 | 0.866 | 0.848 |
| IPSL-CM6A-LR | 29.58 | 25.59 | −3.98 | 1.086 | 0.939 |
| UKESM1-0-LL | 28.33 | 25.91 | −2.42 | 1.040 | 0.951 |
| CESM2-WACCM | 32.89 | 29.51 | −3.38 | 1.207 | 1.083 |

**THE BOUND: land proxy 23.59–32.89 | all cells 23.10–29.51 °C-century.**

Our ensemble: integral max **27.25**, median 12.39 °C-century; L21 median amp **0.9441**,
reaching **25.72** °C-century at the median amp.

**Reachable at the median amp: 1 of 4 (land) | 2 of 4 (all cells).**
Reachable = MRI under land; MRI + **IPSL** under all cells.

### The domain sensitivity is robust to the statistic; the model identity is not

The headline split is **the same on both statistics** — 1 of 4 under the land proxy, 2 of 4
under all cells — so *whether the comparison is domain-sensitive* does not depend on
choosing endpoint or integral.

> ⚠ **But WHICH model flips changes, and quoting one statistic's model list under the other
> is wrong.** UKESM1-0-LL flips on the endpoint and **not** on the integral (it needs amp
> 0.951, the 47.4th percentile, with **0 configs** at the median amp — it just misses).
> IPSL-CM6A-LR flips on the **integral** instead. MRI-ESM2-0 is reachable throughout;
> CESM2-WACCM never is.

## Settled upstream — do not re-raise

* **"One line in the reducer" is FALSE for 3 of 4 models.** `reduce_cmip6_tas_coulon.py`
  takes its ≤2100 leg from `data/cmip6_pai/`, already land-masked; flipping `SFTLF_MIN`
  would splice an all-cells tail onto a land-masked baseline. Hence the separate build.
* **UKESM `r4i1p1f2` is settled.**
* `sftgif`, the latitude cutoff, and post-processing are all **ruled out** upstream.

## Portability traps in the CMIP6 build

All of these **crash rather than mislead**, but they cost time:

* a `"YYYY-12-31"` slice bound is an **invalid date** on UKESM's 360-day calendar;
* Pangeo returns `numpy.datetime64` for MRI-ESM2-0 but **cftime** for the 360-day models —
  use `.dt.year`, never a comprehension;
* UKESM's **local historical** NetCDF filtered to `>2100` is an EMPTY frame that reaches the
  plausibility check as a nan and reports a bogus "coordinate mismatch".

## Reproduce

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
source ~/climate-env/bin/activate
python python/diag_coulon_integral_bound.py       # gate + both domains + the bound
python python/diag_coulon_domain_reachability.py  # the endpoint statistic
```

---

## [MARCUS — interpretation]

> **[One paragraph: what the bound licenses us to say about Ladrillo vs Coulon, given that
> the domain is unstated and the reachable set is 1–2 of 4 either way.]**

> **[One paragraph: whether the "just misses" cases (UKESM at the 47.4th amp percentile on
> the integral) should be reported as near-misses or as failures.]**
