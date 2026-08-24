# Handoff — the Antarctic phase is open, and the 2300 band is one prior

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through the commits below.
Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24_greenland_closed_ais_next.md`, whose §7 items **2 and 3 are now
CLOSED** and whose item **1 has its first two measurements**. Everything in that handoff's
§1, §2, §5 and §6 is unchanged; its §3 is superseded (see §2 below) and its §4 numbers
still stand.

---

## 0. THE ONE-PARAGRAPH VERSION

Antarctica has been priced. **The ssp585 AIS 2300 spread — 252 cm, 55% of the whole total
— is 78% ONE parameter, `antarctic_lambda`, the DAIS fast-dynamics disintegration rate,
and that parameter's posterior sits 0.027 prior sd from its paleo prior mean.** It is a
prior sample by construction: the calibrator's own comment says the fast-dynamics
parameters are observationally unidentified because Antarctic temperature never crosses
the threshold over the historical window. So the AIS band is a **prior**, not an
inference — which relocates the leverage from the sampler and from stock-vs-custom DAIS
to the DAISfastdyn paleo prior, and because λ is exactly likelihood-inert, a revision is
prior-propagatable with **no refit**. The block also has its first L14 convergence
certificate (`ais_iceflow0` R̂ **2.244**; 9 of 17 fail), and the two results cross well:
the top-3 movers in both scenarios are the block's best-mixed parameters. Separately,
`data/cmip6_pai` turned out to be corrupt for **seven** files across three reductions and
three models — not two — with the **AIS numerator wrong as well as the denominator; the
A6 fit survives the repair, but the matched-warming cells that motivated it do not.**

---

## 1. THE ANTARCTIC RESULT — `julia/diag_ais_block_propagation.jl`

`outputs/diag_ais_block_propagation_L14.csv`, `outputs/log_ais_block_propagation_L14.txt`.
2000 draws (500/chain × 4), L14, ssp245 + ssp585, horizons 2100/2150/2300, AIS component.

### 1.1 The ranking is a different parameter in each scenario

Ranked by **decile contrast** = median(top decile) − median(bottom decile), as a fraction
of the projection's own p05–p95. **Use this, not Pearson r** — AIS is bimodal in
tipped/not-tipped and r understates a parameter that moves the mixture weight (same
parameter, ssp245@2300: r = 0.364, contrast = 0.563).

| rank | ssp245 @2300 | | ssp585 @2300 | |
|---|---|---|---|---|
| 1 | `antarctic_temp_threshold` | **−0.68** | `antarctic_lambda` | **+0.92** (R² **0.78**) |
| 2 | `ais_gmst_amp` | +0.67 | `ais_gmst_amp` | +0.30 |
| 3 | `antarctic_lambda` | +0.56 | `ais_c` | +0.26 |
| 4 | `ais_runoff_Ton` | +0.55 | `ais_mu` | −0.23 |
| 5 | `antarctic_alpha` | +0.21 | `ais_slope` | −0.21 |

⚠ **`antarctic_temp_threshold` is rank 1 at ssp245 and rank 10 (−0.070) at ssp585.** Not
noise — mechanism. λ is fired by a hard annual step `if T_ant > temperature_threshold`
(`antarctic_icesheet_component.jl:180`). At ssp245 the binding question is *whether* a
draw tips; at ssp585 essentially all of them do, *whether* stops discriminating, and *how
fast* takes over. **An AIS parameter sensitivity quoted without its scenario is
meaningless.** This is also the mechanism behind the bimodality the previous handoff §4
flagged.

### 1.2 The dominant parameter is a prior sample — construction AND measurement

`calibrate_mcmc_ext.jl:1093`, in its own words: the fast-dynamics parameters *"are
observationally unidentified over the historical window (T_ant never crosses
temperature_threshold), so their marginals will simply sample the prior. That is the
point."* Against `outputs/param_priors.csv` (the DAISfastdyn paleo marginals):

| param | posterior median | prior mean | displacement |
|---|---|---|---|
| `antarctic_lambda` | 0.01050 | 0.01040 | **+0.027 prior sd** |
| `antarctic_temp_threshold` | −15.583 | −15.606 | **+0.053 prior sd** |
| `antarctic_gamma` | 2.741 | 2.794 | −0.058 sd |
| `antarctic_kappa` | 0.05897 | 0.06560 | −0.490 sd |

⇒ **the 252 cm ssp585 band is a prior on the fast-dynamics rate.** This makes the red
team's "the AIS tail is prior- rather than data-driven" precise and quantified.

**What this means for where to spend effort.** Not the sampler. Not replacing stock DAIS
(that asymmetry with GSIC/Greenland is real but is not what sets the band). **The
DAISfastdyn paleo prior on λ is the band.** And λ is exactly likelihood-inert — the same
status as `gis_amp` and the Greenland tap onset — so a revision is **prior-propagatable at
projection time with no refit**, exactly as the Greenland tap was.

---

## 2. WHAT IS CLOSED FROM THE PREVIOUS HANDOFF

### 2.1 §7 item 2 — `ais_iceflow0` R̂ at L14: **2.244**

`julia/diag_ais_block_convergence.jl`, `outputs/mcmc/ais_block_convergence_L14.csv`.
2.359 at L10, 2.449 at L11, **2.244 at L14** — drifting down, still the block's worst
(ESS 12.0, chain medians spanning 3.56 within-chain sd).

| block | fail / total | worst R̂ |
|---|---|---|
| Greenland | 3 / 9 | 1.075 |
| **Antarctic** | **9 / 17** | **2.244** |

geometry 4/7 · dynamics 2/6 (worst `antarctic_alpha` 1.777) · **ocean 3/3, the whole ANTO
sub-block** · driver 0/1. `rho_ais` (1.257) fails too but is the AR(1) nuisance layer.

**The cross with §1, and the two caveats it carries.** The top 3 in both scenarios are the
block's best-mixed parameters: λ R̂ 1.000 / ESS 7836, threshold 1.002 / 6692, `ais_gmst_amp`
1.007 / 2612, `ais_c` 1.003 / 2652. So the 9-of-17 failure rate is largely in parameters
that do not reach the deliverable. **But:** `ais_runoff_Ton` is rank 4 at ssp245 (0.55)
with R̂ 1.092, and `antarctic_alpha` rank 5 (0.21) with R̂ **1.777**. And `ais_iceflow0`'s
"does not reach the deliverable" verdict was measured on **ssp245 alone** — at ssp585 its
R² is **12× larger** (0.0031 → 0.0391; contrast 38.5 cm = 0.152 of the spread). The
reporting-caveat verdict survives, but quote it with the scenario attached.

### 2.2 §7 item 3 — the PAI repair, and it was bigger and differently-shaped

⚠ **The previous handoff's §3 is superseded on both scope and recipe.**

* **Mechanism, measured** (`python/reduce_cmip6_tas_pai_fix_mpi.py`,
  `outputs/diag_pai_mpi_repair.md`): `xarray`'s `.weighted()` aligns on coordinate values
  with an inner join. Three reducers build the global weight **and the AIS mask** once
  from `sftlf`. `sftlf.lat` differs from `tas.lat` by **1.4e-14 deg**, so only **56 of 96
  latitudes** survived on MPI-ESM1-2-LR (120/192 on -HR). `lon` matched exactly.
* **The AIS numerator was wrong too**, so "re-derive with the corrected globals" would
  have been a half-fix: `tas_ais` moves **+0.574 K (LR)** and **−0.125 K (HR)** — opposite
  signs. The published value looked fine because it sat inside the ensemble range; that is
  not evidence, because a retained subset that makes a global mean 7 K cold is skewed
  toward exactly the cold cells Antarctica is made of.
* **Seven files, three reductions, three models** — the DECK set also caught
  `MPI-ESM-1-2-HAM`, invisible from the scenario reduction.
* **The fix is in the reducers**, via new `python/pai_series.py` (`align_sftlf_to`, gated
  on shape and float-noise-only drift; `assert_global_plausible`). All seven are back at
  canonical paths. Pre-fix files + full write-up:
  `outputs/quarantine/20260824_cmip6_pai_mpi_lat_align/`.
* **A6 verdict: the fit survives, the motivating cells do not.** The level-vs-rate
  decomposition does not move — **c = −0.643 [−1.062, 0.072] → −0.645 [−1.066, 0.040]**,
  same 0.017 RMSE gain — and ensemble medians move **< 0.1 σ**. But the SSP2-4.5-above-
  SSP5-8.5 margin at 2.0 K goes **+0.026 → +0.009 (2.9× smaller)** and the trend-ratio
  level-2.0 cell **inverts**. ⇒ **quote the fit, not the cells.**

---

## 3. NON-OBVIOUS STATE

* **`python/pai_series.py` now owns the "which files are model series" list** for
  `diag_pai_cmip6_{time,rate}.py` and `diag_pai_denominator.py`, with a **schema gate that
  raises rather than skipping**. Three inline copies had drifted, and
  `diag_pai_cmip6_time.py` had been **dying outright** on `KeyError: tas_global` since the
  OHC reduction landed in `data/cmip6_pai`. Add a new sibling's prefix there, not inline.
* **`GLOBAL_PLAUSIBLE_K` was first written (283, 293) K and would have rejected FOUR REAL
  series.** Resized to **(283, 302)** against the realised 285.69–297.82 K per-experiment
  spread. If you tighten it, re-check all 306 series first — `tolerance_scaled_to_spread`.
* **`diag_ais_block_convergence.jl` deliberately does NOT reuse the Greenland file's
  spread ratio.** Two AIS parameters are strictly negative over their whole support, where
  max/min inverts (`ratio_needs_native_scale`). Headline is the chain-median range over
  the pooled within-chain sd; the ratio is gated on a common sign with the sign in its own
  column.
* **`--maxrows=N`** on that file is a smoke mode: it writes to a `_SMOKE` filename and
  stamps every line. Use it before any full run — the chains are 9.3 GB and a full read is
  ~5 minutes before the first line of real output appears (Julia block-buffers to a file,
  so an in-progress run looks stalled; check `%CPU`, not the log).
* **`diag_ais_block_propagation.jl` reads the chains ONCE** and reuses them across
  scenarios. Do not move the read back inside the scenario loop — it doubles a cost that
  dominates the runtime.
* `outputs/diag_pai_mpi_repair_series/` holds the measurement script's own two series. It
  is deliberately **not** under `data/`: a partial second copy of two of the seven
  repaired files beside the canonical directory is the stale-retrieval trap.
* Every trap in `handoff_2026-08-24` §5, `handoff_2026-08-23f` §5 and `handoff_2026-08-23e`
  §7 still applies.

---

## 4. FILES

**New:** `julia/diag_ais_block_convergence.jl`, `julia/diag_ais_block_propagation.jl`,
`python/pai_series.py`, `python/reduce_cmip6_tas_pai_fix_mpi.py`,
`outputs/mcmc/ais_block_convergence_L14.csv`,
`outputs/diag_ais_block_propagation_L14.csv`, `outputs/diag_pai_mpi_repair.{csv,md}`,
`outputs/diag_pai_mpi_repair_series/`,
`outputs/quarantine/20260824_cmip6_pai_mpi_lat_align/`.
**Modified:** `python/reduce_cmip6_tas_pai{,_deck,_ext}.py`,
`python/diag_pai_cmip6_{time,rate}.py`, `python/diag_pai_denominator.py`,
7 files in `data/cmip6_pai/`, all `outputs/diag_pai_*` deliverables, `CHANGELOG.md`.

Memories: `ais_spread_is_lambda_prior`, `ais_l14_block_certified`,
`cmip6_pai_mpi_corrupt` (rewritten from open question to closed result). `INDEX_slr.md`
gains an **Antarctica** section.

---

## 5. OPEN, IN PRIORITY ORDER

1. **The DAISfastdyn paleo prior on `antarctic_lambda`** — it *is* the ssp585 2300 band.
   Where does `outputs/param_priors.csv` come from, is it still the best available
   constraint, and what does the band do under a defensible alternative? λ is exactly
   likelihood-inert ⇒ prior-propagatable, **no refit**. This is now priority 1, replacing
   the previous handoff's generic "Antarctica".
2. **`ais_runoff_Ton` (R̂ 1.092, rank 4 at ssp245) and `antarctic_alpha` (R̂ 1.777, rank
   5)** — the two parameters that both fail to mix AND reach the deliverable. These, not
   `ais_iceflow0`, are what a sampler-side effort should target if one is spent.
3. **Re-price at 2100 and 2150** — §1 quotes 2300. The CSV has all three horizons and the
   ordering already differs at 2100 (`antarctic_lambda` is not in the ssp245 top 3 there);
   the scenario-inversion caveat may compound with a horizon one.
4. **The cool arms' separation residual** (ssp126 0.90×, ssp245 1.19×) — unchanged from
   the previous handoff §7 item 4.
5. **The amp-law estimator** — unchanged, the one live thread on a closed question.
6. **Marcus's prose** for module-memo §1 and §9, and the `2.0` tag decision.
