# Plan: stochastic FaIR ensemble for Greene N=2000 run

## Why stochastic FaIR

Currently we run FaIR with `stochastic_run=False`, then add an *empirical* internal-variability prior (σ ≈ 0.12 °C/yr from Berkeley Earth detrended residuals) post-hoc as a constant variance term. This is a hack:
- Internal variability magnitude is the *same* across configs (it's a constant prior we tack on)
- It doesn't propagate through MimiBRICK to SLR
- The σ choice is tied to observations, not to FaIR's calibration

Turning on `stochastic_run=True` lets each FaIR config use its own calibrated `sigma_eta` (surface-layer forcing noise) and `sigma_xi` (deep-layer forcing noise) parameters from the v1.4.1 posterior. The resulting GMST trajectories include FaIR's internally-consistent stochastic variability, which then propagates naturally into MimiBRICK SLR via temperature input.

## Sampling strategy: 3-way ANOVA-friendly

To decompose variance into emissions / climate-response / internal-variability, we use **multiple stochastic seeds per (RFF, FaIR-config) pair**:

```
For each (RFF_i, cfg_j) pair:
  For seed_k in [seed_1, ..., seed_N_seed]:
    run FaIR with stochastic_run=True, seed=seed_k
    save GMST trajectory
```

ANOVA decomposition:
- `V_internal = E_{i,j}[ Var_seed[T(i,j,seed)] ]` — average within-pair variance across seeds
- `V_climate  = E_i[ Var_j[ E_seed[T(i,j,seed)] ] ]` — variance across configs of seed-mean
- `V_emissions = Var_i[ E_{j,seed}[T(i,j,seed)] ]` — variance across RFFs of (cfg, seed)-mean

All three estimable from one dataset.

## Two parallel datasets on Greene

### Dataset A — "Headline ensemble" for damages and uncertainty quantification

- N=2000 LHS pairs (RFF_i, cfg_i) — each a single (rff, cfg) tuple
- **N_seed=10 stochastic realizations per pair**
- Total: 2000 × 10 = **20,000 FaIR runs**
- Then MimiBRICK on each (with one BRICK posterior member per FaIR draw, sampled): 20,000 BRICK runs
- Then FrEDI on each: 20,000 FrEDI runs (after data.table refactor: ~17 hr serial; ~1 hr in 16-job array)

This dataset is for: percentile bands on damages, exceedance probabilities, paired-draw social cost calculations.

### Dataset B — "Cross-product for Figure 4" for variance decomposition

- N_RFF = 50 (random sample from 10000 RFFs)
- N_cfg = 50 (random sample from 841)
- **N_seed = 10 stochastic realizations per (RFF, cfg) pair**
- Total: 50 × 50 × 10 = **25,000 FaIR runs**
- Then MimiBRICK on each: 25,000 BRICK runs (with same BRICK posterior member sampled per RFF, cfg, seed combo, OR include BRICK posterior dimension)
- For 4-way ANOVA add: 50 × 50 × 10 × 50 BRICK posterior = 1.25M BRICK runs (~2 hr at 178/s)

This dataset is for: Figure 4 variance decomposition with all four sources (FaIR stochastic, RFF-SP, FaIR parameters, BRICK posterior).

## Compute estimates

Per FaIR run with `stochastic_run=True` and 1 RFF/cfg/seed: ~3 sec (similar to deterministic since the work is dominated by time integration).

| Dataset | FaIR runs | FaIR wall-time | MimiBRICK runs | MimiBRICK wall-time |
|---|--:|--:|--:|--:|
| A (headline) | 20,000 | ~17 hr serial → 1 hr in 20-job array | 20,000 | 2 min |
| B (cross-product) | 25,000 | ~21 hr serial → 1 hr in 20-job array | 25,000 (or 1.25M with BRICK dim) | 2 min – 2 hr |

Total FaIR compute on Greene with 20-way array parallelism: **~2 hours wall time**.

## Code changes needed

### `python/lhs_climate_pilot.py` (or a new `lhs_climate_stochastic.py`)

```python
# In configure_fair_instance, change:
fill(f.climate_configs["stochastic_run"], False, config=cfg)
# to:
fill(f.climate_configs["stochastic_run"], True, config=cfg)
# and pass a per-realization seed:
fill(f.climate_configs["seed"], current_seed, config=cfg)
```

The current code already fills `seed` from the calibration CSV. For stochastic, we'd vary the seed across realizations:

```python
for seed_k in range(N_SEED):
    for cfg in configs:
        # Use a deterministic seed scheme: 1000*seed_k + calibration_seed
        fill(f.climate_configs["seed"], 1000 * seed_k + int(row["seed"]), config=cfg)
    f.run()
    # save trajectories indexed by (rff_idx, cfg_idx, seed_k)
```

Add a `--n-seeds` CLI flag and an outer seed loop. Output cube grows from
(n_rff, n_cfg, n_yr) to (n_rff, n_cfg, n_seed, n_yr).

### `julia/run_mimibrick_cross.jl`

No change needed — the seed dimension just adds rows to the input.

### Storage

Per-trajectory storage: 451 yr × 4 bytes = 1.8 KB.
Headline dataset (20k trajectories): ~36 MB in float32. Easy.
Cross-product dataset (25k trajectories, plus BRICK posterior dim if 4-way): up to 1.25M trajectories × 1.8 KB = 2.3 GB. Manageable.

## Variance decomposition with 3-way (or 4-way) ANOVA

The Python `figure4_slr_components.py` script already handles 3-way decomposition
implicitly (treats each (rff, cfg, post) row independently). For the new
stochastic data with seed dimension, modify the variance functions to:

```python
# 4 nested ANOVA terms:
def variance_by_source_4way(df_anom, yr_cols):
    arr = df_anom[yr_cols].values.astype(np.float64)
    var_total = arr.var(axis=0)

    # V_emissions = Var_rff[E_{cfg,seed,post}[X]]
    var_emi = (df_anom.groupby("rff_idx")[yr_cols].mean()).values.var(axis=0)

    # V_climate = E_rff[Var_cfg[E_{seed,post}[X]]]
    grp_cfg = df_anom.groupby(["rff_idx", "fair_cfg_idx"])[yr_cols].mean()
    var_clim = grp_cfg.groupby(level="rff_idx").var().mean().values

    # V_internal = E_{rff,cfg}[Var_seed[E_post[X]]]
    grp_seed = df_anom.groupby(["rff_idx","fair_cfg_idx","seed_idx"])[yr_cols].mean()
    var_int = grp_seed.groupby(level=["rff_idx","fair_cfg_idx"]).var().mean().values

    # V_brick = E_{rff,cfg,seed}[Var_post[X]]
    grp_full = df_anom.groupby(["rff_idx","fair_cfg_idx","seed_idx","post_idx"])[yr_cols].first()
    var_brk = grp_full.groupby(level=["rff_idx","fair_cfg_idx","seed_idx"]).var().mean().values

    return var_total, var_emi, var_clim, var_int, var_brk
```

## Validation

Before running the full Greene job:
1. Run a small (5×5×5 stochastic = 125 trajectories) batch locally with `stochastic_run=True`
2. Verify FaIR's stochastic σ at year 2025 (pre-divergence) ≈ 0.10–0.15 °C/yr
3. Compare to historical Berkeley Earth detrended residual σ ≈ 0.12 °C/yr
4. If FaIR's σ is way off, re-examine sigma_eta / sigma_xi calibration

## State carry-over bug (debugged 2026-05-07)

**Critical**: `f.gas_partitions` (CO2 distributed across 4 carbon-cycle pools,
shape `(n_scenarios, n_configs, n_species, n_pools)` -- **no time
dimension**) retains its end-of-run state across `f.run()` calls. With
multi-seed loops, the carbon cycle inherits the previous run's gas-pool state,
biasing each subsequent run upward.

Symptom (before fix): OHC at year 2020 grows monotonically with seed_idx
(e.g. 61, 106, 172, 218, 246, 292, 309, 351, 370, 419 × 10²² J for 10 seeds,
vs the correct ~50-70 × 10²² J for any single seed).

**Important subtlety**: `initialise(f.gas_partitions, 0)` only resets
`gas_partitions[0, ...]` -- the FIRST scenario's data. In any setup with
n_scenarios > 1 (which the LHS pilot uses with `batch_size=2`), this leaves
scenarios 1+ untouched and the bug persists.

**Correct fix**: reset the full array, not just the first slot:

```python
for seed_idx in range(n_seeds):
    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)
    initialise(f.toa_imbalance, 0)
    f.gas_partitions.values[:] = 0     # full array, not just [0, ...]
    fill(f.climate_configs["seed"], 1000*seed_idx + cal_seed, ...)
    f.run(progress=False)
```

Verified by deterministic-replay test (multi-scenario, multi-config setup):
4 consecutive runs with same seeds produce identical OHC + temperature
trajectories after this fix. OHC mean across scen+cfg at 2020 ≈ 480 ZJ,
matching Cheng et al. observations.

## Open questions

- **N_seed**: 10 is plenty for variance estimation; could go to 5 to halve cost.
- **Seed scheme**: deterministic seed = `1000 * seed_index + config_seed` is reproducible. Or use a simple counter `seed_idx`.
- **BRICK posterior dim in cross-product**: include for 4-way ANOVA, or pair-sample to keep size manageable?
- **Per-config seed_eta/seed_xi**: FaIR documentation suggests just `seed` is enough; both noise streams come from the same seed.
