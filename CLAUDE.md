# SLR-RFF-BRICK — Project Context for Claude Code

> **Universal Marcus-Sarofim conventions** (the three debugging disciplines,
> NYU Torch HPC reference, sanity-test framework for paired experiments,
> FaIR/BRICK/FrEDI gotchas catalog, methodological principles) live at
> `~/.claude/CLAUDE.md` and auto-load for every Claude Code session.
> The file below adds SLR-RFF-BRICK-specific content.

---

## What this project does

US **coastal climate damages** under the **RFF Socioeconomic Projections (RFF-SP)** via:

1. **FaIR 2.2.4** with v1.4.1 calibration (841 configs, Zenodo 10566813)
   driven by RFF-SP-derived emissions → GMST + OHC trajectories
2. **MimiBRICK** v1.0.1 (10,000-member posterior subsample) driven by
   FaIR's GMST/OHC → SLR trajectories
3. (Future) **FrEDI** with SLR + RFF-SP socioeconomics → coastal damages

Compute lives on NYU Torch under project account `torch_pr_1041_general`
(SC-GHG, PI Kevin Cromar). Working directory on Torch:
`/scratch/ms17839/SLR-RFF-BRICK/`.

---

## Pipeline phases

### Phase A (complete, 1850-2100)

- N=2000 LHS RFFs × 841 FaIR cfgs × 10 stochastic seeds
- FaIR cubes: `outputs/lhs_pilot_full_N2000{.npz, _gmst.npy, _ohc.npy, _years.npy, _rffs.npy}`
- Paired BRICK weighted: `outputs/brick_paired_N2000_weighted.csv` (20,000 draws)
- Hawkins-Sutton + observations overlay: `outputs/plots/hawkins_sutton_*.png`

### Phase C (complete, 1850-2300)

6 cubes — 3 RFF scenarios × 2 baselines:
- RFF-SP × {baseline, +1 GtC pulse @ 2030, vehicle-removal @ 2027+}
- SSP2-4.5 deterministic × same 3 scenarios

Cubes: `outputs/{rff,ssp245}_{baseline,pulse,vehicle}_*_to2300.npz`
Paired BRICK: `outputs/brick_paired_{rff,ssp245}_{baseline,pulse,vehicle}_to2300_weighted.csv`

### Wong importance weighting

- `python/apply_wong_weights.py` with O(N) Kalman AR(1) likelihood
  (~5 sec for 20k draws)
- Uses CSIRO Recons observations from MimiBRICK's calibration data
- Adds `l_FB, l_B, log_w, w_norm` columns to each weighted CSV
- `c` annealing constant auto-tuned to ESS ≈ 50%; for our GMSL-only
  likelihood, c ≈ 0.2 for both N=20k (Phase A) and N=500 (Phase C)

---

## Physical conventions

- GMST: °C anomaly relative to PI mean (1850-1900)
- OHC: cumulative ocean heat content anomaly from FaIR's 1750 start, in 10²² J
- SLR: trajectory year columns store `100 × (gmsl[t] − gmsl[2000])` in cm
  — delta relative to year 2000, all components and total alike
- BRICK `post_idx`: 1-indexed (Julia convention); subtract 1 when slicing
  the posterior DataFrame in Python

---

## Sanity tests (REQUIRED before paired headline numbers)

Per user-level CLAUDE.md §2, all paired analysis must pass the standard
test suite. For this project the wrapper is:

```bash
sbatch slurm/submit_sanity_tests.sh
```

Generates 6 small FaIR cubes (N=20, ~5 min each), runs paired BRICK on
each, then runs `python/scripts/sanity_tests.py` to check:

1. Zero-perturbation gives bit-identical paired diff
2. Sign-flip symmetry (+X vs -X gives anti-symmetric responses)
3. Magnitude doubling (+2X gives ~2× the +X response)
4. Reproducibility (same experiment twice gives bit-identical output)

PASS/FAIL summary at `outputs/sanity_test_summary.csv`. Non-zero exit code
if any test FAILED. Catches the kinds of bugs we've actually hit in this
project (FaIR `gas_partitions` state carryover, MimiBRICK `get_model()`
non-determinism).

---

## Reportable threshold sets

- SLR (cm rel 2000): 30, 50, 75, 100, 150, 200, 300
- GMST (°C above PI): 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0
- RF (W/m²): 3, 4, 5, 6, 7, 8
- Years: 2050, 2100, 2150 (and 2300 for Phase C)

Reported as Wong-importance-weighted probabilities per
`python/exceedance_tables.py`.

---

## Project layout (on Torch)

```
/scratch/ms17839/SLR-RFF-BRICK/
├── data/
│   ├── RFF-SP-emissions/csv/            # 10,000 RFF emissions trajectories
│   ├── MimiBRICK/parameters_subsample_brick.csv  # 10k BRICK posterior members
│   ├── vehicle_scenarioA_emissions.csv  # Wong-style A scenario
│   ├── volcanic_solar_hist.csv
│   └── observations/                    # Berkeley Earth, AVISO, CSIRO Recons
├── python/                              # FaIR drivers, post-processing
│   ├── lhs_climate_pilot.py             # Phase A driver
│   ├── lhs_climate_pilot_ext.py         # Phase C driver (pulse, vehicle, SSP)
│   ├── apply_wong_weights.py            # importance weighting (Kalman AR(1))
│   ├── exceedance_tables.py             # threshold probability tables
│   ├── hawkins_sutton.py                # variance decomp + obs overlay
│   └── scripts/                         # cube converters, sanity tests
├── julia/
│   ├── run_mimibrick_paired_seeded.jl   # RFF paired BRICK
│   ├── run_mimibrick_ssp245.jl          # SSP single-scenario BRICK
│   └── compute_lB_per_post.jl           # baseline likelihoods for Wong
├── slurm/                               # SLURM submit scripts
└── outputs/                             # Generated cubes, CSVs, plots
```

---

## SLR-RFF-BRICK-specific gotchas

(Cross-project gotchas — FaIR `gas_partitions`, AR6 emissions units,
MimiBRICK `get_model()` non-determinism, NumPy/Julia byte-order, etc. —
live in `~/.claude/CLAUDE.md` §4. The items below are project-specific.)

### Phase C cube shape inconsistency

Phase A cubes are 4D `(n_rff, n_cfg, n_seed, n_year)`. Phase C RFF cubes
are 3D `(n_rff, n_cfg, n_year)` because they use a single seed and
`lhs_climate_pilot_ext.py` collapses the seed dim. For paired BRICK to
mmap them with the existing driver, expand to 4D first:

```bash
python python/scripts/expand_phaseC_to_4d.py outputs/rff_*_to2300.npz
```

This is wired into `slurm/submit_phase_D.sh` automatically.

### SSP2-4.5 cubes use a different paired-BRICK driver

`run_mimibrick_ssp245.jl` instead of `run_mimibrick_paired_seeded.jl`,
because there's only one RFF scenario (n_rff=1) and no LHS metadata to
pair against — pairing is instead 1-to-1 cfg ↔ posterior member.

### `.npz` cubes with numpy `<U` string keys

`lhs_climate_pilot_ext.py` saves scenario tags as numpy `<U6` /`<U8`
strings. NPZ.jl in Julia can't parse these — must strip with a Python
preprocessing step before Julia loads (`submit_phase_D.sh` handles this
for the SSP-side cubes automatically).

### Wong c-annealing constant

Wong's vehicle-SLR paper uses c=0.000128 for his 841-config ensemble with
full multi-component BRICK likelihood. For our setup using GMSL-only
likelihood, c is auto-tuned to ESS=50%; empirically c≈0.2 for both N=2000
(Phase A) and N=500 (Phase C). When extending or comparing to Wong's
work, note the c value can differ by orders of magnitude depending on
which channels of the likelihood are included.

---

## SCC interpretation note for AIS marginal response

After fixing `MimiBRICK.get_model()` non-determinism (May 2026), the
AIS pulse-vs-baseline paired diff is uniformly small-positive. Earlier
sessions reported a uniformly slightly-negative diff that was a bug,
NOT a snowfall-regime physics result. Don't re-introduce the snowfall
narrative — the real AIS marginal response is bimodal (small positive
default + occasional MICI-threshold-crossing tail) but uniformly
non-negative once the get_model RNG is seeded properly.

---

## Collaborators

- **Marcus Sarofim** (ms17839@nyu.edu) — PI
- **Kevin Cromar** (NYU Marron Institute) — Torch project sponsor
- **Peter Howard** (IPI) — uses SLR projections for litigation/advocacy
- **Lisa Rennels** (Stanford / RFF) — MimiBRICK.jl co-author and AR6
  emissions file author; natural reviewer
- **Tony Wong** (RIT) — original BRICK author; contact when MimiBRICK
  behaviour is unclear

---

## References

- BRICK: Wong et al. 2017 GMD; Wong-Bakker-Keller 2017 (Antarctic fast dynamics)
- MimiBRICK: Errickson et al.; Darnell et al. (SNEASY-BRICK)
- Wong vehicle SLR: Wong 2025/2026, arXiv 2604.13446v1
- RFF-SP: Rennert, Errickson, Prest et al. 2022 Nature
- FaIR: Smith et al. 2018 GMD; Leach et al. 2021
- BRICK calibration data on Torch: `/scratch/ms17839/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/`
- Paper PDFs (laptop only): `/Users/MarcusMarcus/Documents/2026/ClaudeDocs/Papers/`
