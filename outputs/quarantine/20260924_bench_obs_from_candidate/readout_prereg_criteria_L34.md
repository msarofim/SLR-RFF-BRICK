# Pre-registered criteria read-out -- `L34` against `L27*`

*readout_prereg_criteria.py, 2026-09-24. Thresholds are the constants at the top of this script, fixed 2026-09-24 before any L34 number existed.*

> NOT A CRITERION: sd_ais sitting on its bound -- TRUE BY CONSTRUCTION, never evidence

## PRIMARY -- FULL-PERIOD AIS RMSE (sigma), live target, one run, vs the frozen champion

| arm | AIS RMSE (cm) | **AIS RMSE (sigma)** | note |
|---|---|---|---|
| L34 **<-- candidate** | 0.0968 | **0.58** | bias -0.0797 cm = -0.48 sd; cov90 87%; n=126 |
| L27* (ruler) | 0.0931 | **0.56** | bias -0.0771 cm = -0.46 sd; cov90 83%; n=126 |
| BRICK 2.0 | 1.5740 | **9.40** | bias -1.1500 cm = -6.87 sd; cov90 25%; n=126 |

**L34 = 0.58 sigma** vs **L27* = 0.56**. Pre-registered: WIN <= 0.7, LOSS >= 0.8, 0.7-0.8 AMBIGUOUS.

### ==> PRIMARY VERDICT: **WIN**

## GUARD -- non-Antarctic components unchanged (within 0.02 sigma of L27*)

| module | L34 (sigma) | L27* (sigma) | delta | within tol |
|---|---|---|---|---|
| glaciers | 0.68 | 0.69 | -0.010 | yes |
| Greenland | 1.08 | 1.07 | +0.010 | yes |
| thermal exp. | 1.50 | 1.51 | -0.010 | yes |
| TOTAL | 0.26 | 0.26 | +0.000 | yes |

### ==> GUARD: **PASS** (largest non-Antarctic, non-TOTAL move 0.010 sigma; tol 0.02). TOTAL is a composite and is reported, not graded.

## AIS sub-window decomposition -- DESCRIPTIVE, NOT A CRITERION. Added 2026-09-24 08:30, BEFORE any candidate number existed.

| window | L34 | L27* | L32 (both changes) | reading |
|---|---|---|---|---|
| **full** | 0.58 | 0.56 | 0.88 | best = **L27** |
| 1920-1949 | 0.75 | 0.73 | 1.07 | best = **L27** |
| 1950-1992 | 0.52 | 0.48 | 0.47 | best = **L32** |
| 1993-2026 | 0.57 | 0.52 | 1.01 | best = **L27** |

⚠ `L32` is scored here out of its OWN bench file, which is a different run of the ruler; treat its column as indicative and re-score it in one run before quoting a L34-vs-L32 difference as a result.

**What this block can and cannot say.** If `L34` picks up the satellite era while keeping the full period, the noise fix alone bought `L32`'s win and the target swap was not needed. If it does not, the win was the target. Either way this is a DESCRIPTION of the decomposition, not a promotion criterion.

## COST A -- AIS hindcast bias at the anchor years -- REPORT EITHER WAY, not a gate

Like-for-like gate PASSED: `obs` identical at [1900, 1950, 2018, 2025] in both files (max |delta| < 1e-9), so the bias difference is a property of the ARM.

| year | obs (cm) | L34 bias | in90 | L27 bias | in90 | change |
|---|---|---|---|---|---|---|
| 1900 | -0.6341 | -0.0207 | yes | -0.0413 | yes | closer to obs (-0.0206) |
| 1950 | -0.3626 | -0.1259 | yes | -0.1167 | yes | further (+0.0092) |
| 2018 | +0.6964 | -0.2168 | **no** | -0.2030 | **no** | further (+0.0138) |
| 2025 | +0.7664 | -0.0258 | yes | -0.0106 | yes | further (+0.0152) |

### ==> COST A is REPORTED, not graded. A prediction about its direction is not a criterion.

## COST B -- SSP AIS p05-p95 -- a win that is ONLY a wider posterior is no win

Champion source: `benchmark/reference/L27/model_comparison.csv` -- FROZEN snapshot (same champion the PRIMARY ruler uses).

Band basis identical in both files: joint (posterior params x FaIR forcing). Written 2026-09-24 09:26 (`L34`) and 2026-09-21 06:55 (`L27`) -- separate runs.

⚠ The AIS component is NOT fully insulated from a re-run: between the frozen L27 snapshot and the live outputs/ file, all 9 Ladrillo AIS medians moved in the SAME direction (+0.004 to +0.008 cm, growing with horizon). Cause not established; <= 0.01% of band width, so immaterial to a width ratio. Quoted here so the uniformity is on the record rather than rediscovered.

| scenario | year | L34 med | L27 med | L34 p05-p95 | L27 p05-p95 | ratio |
|---|---|---|---|---|---|---|
| ssp126 | 2100 | 5.04 | 4.92 | 47.14 | 48.32 | **0.98x** |
| ssp126 | 2300 | 15.49 | 15.23 | 208.78 | 211.75 | **0.99x** |
| ssp245 | 2100 | 10.00 | 10.55 | 57.25 | 56.29 | **1.02x** |
| ssp245 | 2300 | 157.53 | 156.34 | 315.87 | 317.49 | **0.99x** |
| ssp585 | 2100 | 36.50 | 36.66 | 65.39 | 67.18 | **0.97x** |
| ssp585 | 2300 | 282.94 | 277.71 | 314.95 | 313.78 | **1.00x** |

### ==> COST B: width ratio 0.97x-1.02x. ⚠ If the PRIMARY is a win AND these are all >1, the win is bought with band width and is NOT a win on the pre-registered reading.

## MECHANISM -- 2018-23 dynamics anomaly (confirms the floor fired; does NOT decide promotion)

Not read from a product. Run, with the **IMBIE** target live:

```
julia --project=julia_v2 julia/diag_ais_channel_separation.jl 1000 --arms=L27,L34
```

and compare `dis_trend_anom` against L27's and IMBIE's. ⚠ The LEVEL channel in that script is evaluated at a COMMON (sigma, rho); read the arm-to-arm difference under BOTH settings, and remember a bounded sigma is not comparable to a free one.

---

## Provenance

| input | md5 |
|---|---|
| `benchmark/reference/L27/model_comparison.csv` | `307111ca4defa01d60b193db864813cd` |
| `outputs/bench_ladrillo_L34.md` | `f9ea8bdd435d568829066decd2513029` |
| `outputs/ladrillo_model_comparison_L34.csv` | `dfae8b64c52d2d424fa15b3dcdbfa2cb` |
| `outputs/postpred_L27_bias.csv` | `44dccdc980252712220ba1796e198e6e` |
| `outputs/postpred_L34_bias.csv` | `bdcabb856274419ba27aea0e2f997cf0` |

*readout_prereg_criteria.py | tag L34 | ref L27* | thresholds WIN<=0.7 LOSS>=0.8 GUARD=0.02sigma | 2026-09-24 09:26 | 0 ungraded criterion(a)*
