# Handoff — v5 noise-isolated Hawkins-Sutton ensemble (2026-05-26)

## What this session accomplished

### v4 patch (committed): TreeSHAP H-S with ANOVA-18k V_internal

Replaced the v3 `V_internal = (1−R²)·V_total` formula (which was reporting
surrogate modeling error as if it were internal variability) with
V_internal interpolated from the v1.4.5 ANOVA-18k bias-corrected CSVs.

**Root cause diagnosed**: LHS-10k cube is **single-seeded by design** —
`seed_idx = 0` for all 10,000 cells, `stochastic_run = False` in the
driver. The cube has zero internal-variability content; its V_total is
purely cfg + RFF driven. The v3 attribution of `(1-R²)·V_total` to V_int
was reporting surrogate fit gap, not seed noise.

**v4 headline fractions** (TreeSHAP attribution):

| Year | total_gmst | total_slr | pulse_gmst | pulse_slr |
|---|---|---|---|---|
| 2021 | emi=0, clim=61, int=39 | brick stays under-attributed by TreeSHAP | n/a (linear) | n/a (linear) |
| 2050 | emi=15, clim=69, int=16 | (rendering tail) | emi=0, clim=100 | (rendering tail) |
| 2100 | emi=50, clim=48, int=2 | emi=30, clim=65, brick=5, int=0 | emi=2, clim=98 | TBD |
| 2150 | emi=54, clim=45, int=1 | emi=47, clim=51, brick=3, int=0 | emi=4, clim=96 | TBD |

(All four PNGs land in `outputs/substack/shapley_hs_*.png`.)

### Outstanding TreeSHAP under-attribution of BRICK

Shapley Owen diagnostic (`shapley_owen_diagnostic.csv`) at year 2100:
- total_slr: TreeSHAP brick=0.031 vs Owen brick=0.227 (7.3× under)
- pulse_slr: TreeSHAP brick=0.024 vs Owen brick=0.217 (9.0× under)

To fix BRICK attribution in the SLR figures we need to re-render
using Owen-Shapley instead of TreeSHAP. Probably worth doing after v5
ensemble is in place (avoid double work).

## v5 design (in flight)

### Concept

Marcus's first-principles intuition that V_internal-at-2021 should be ≈
A/(A+B) > 80% (A = seed spread, B = cfg-rate spread) didn't match the
ANOVA-18k 39% figure. Diagnosing: the cfg-driven 1-yr ΔT spread in
LHS-10k (B = 0.30 K, 5-95) is NOT pure climate-sensitivity response. It
is **deterministic cfg-modulated forced response to solar+volcanic forcing**.
Cfg 57 swings −0.30 K (2019→2020) then +0.50 K (2020→2021), reverting on
multi-year average to ~0.025 K/yr — characteristic Pinatubo-decay /
Hunga-Tonga-like response. Different cfgs amplify the same volcanic
forcing by different amounts.

v5 fixes this by:

1. **Holding solar + volcanic forcing constant from 2015 onward** at the
   1995-2014 climatology mean (Volcanic=0.1805 W/m², Solar=0.0252 W/m²).
   Removes the cfg-modulated forced wiggle.
2. **Enabling FaIR stochastic noise** by LHS-sampling `seed_idx` over
   {0..999} across the 10,000 cells. Provides real seed-driven variance.

Result: V_internal extractable as OOF residual of surrogate (since the
new cube actually has seed variance) without conflating with forced-
response artifacts. Expected: V_internal-at-2021 ≈ 80%+ matching
canonical H-S shape.

### Files created (local + Torch)

| File | Local path | Torch path |
|---|---|---|
| Flattened forcing CSV | `~/Documents/2026/CodeProjects/FaIRtoFrEDI/calibration_v145/volcanic_solar_flat2015.csv` | `/scratch/ms17839/FaIRtoFrEDI/calibration_v145/volcanic_solar_flat2015.csv` |
| LHS-10k_s metadata (seed LHS over {0..999}) | `~/Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/metadata_v145/lhs10ks_metadata_v145.csv` | `/scratch/ms17839/FaIRtoFrEDI/fair_outputs/metadata_v145/lhs10ks_metadata_v145.csv` |
| Patched driver (`--forcing-file` CLI arg) | `~/Documents/2026/CodeProjects/FaIRtoFrEDI/lhs_climate_v145_meta.py` | `/scratch/ms17839/FaIRtoFrEDI/lhs_climate_v145_meta.py` |
| SLURM baseline | `~/Documents/2026/CodeProjects/FaIRtoFrEDI/slurm_v5_lhs10ks_baseline.sh` | same |
| SLURM pulse | `~/Documents/2026/CodeProjects/FaIRtoFrEDI/slurm_v5_lhs10ks_pulse.sh` | same |

### Torch jobs submitted (2026-05-26 ~18:50 ET)

```
JOBID    PARTITION   NAME              STATE
9663007  cpu_short   v5_lhs10ks_base   RUNNING  on cs601
9663078  cpu_short   v5_lhs10ks_pulse  PENDING
```

Both have 4-hour time limit. Expected to complete by ~23:00 ET.

Output cubes:
- `/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_baseline_flat2015.npz`
- `/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_pulse_co2_pos_001gt_flat2015.npz`

## Concrete next-step playbook (next session, cold start)

### 1. Verify Torch jobs completed

```bash
ssh ms17839@login.torch.hpc.nyu.edu "squeue -u ms17839; ls -la /scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_*.npz"
```

Expect two `cube_v145_lhs10ks_*.npz` files. If a partial checkpoint
(`*_partial.npz`) exists instead, the job timed out — diagnose log under
`/scratch/ms17839/FaIRtoFrEDI/logs/v5_lhs10ks_*_*.{out,err}`.

### 2. Pull cubes back to local

```bash
cd ~/Documents/2026/CodeProjects/FaIRtoFrEDI
rsync -avz ms17839@login.torch.hpc.nyu.edu:/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_*.npz fair_outputs/cubes_v145/
```

### 3. Sanity-check the new cubes

```bash
source ~/climate-env/bin/activate
python - <<'PY'
import numpy as np
c = np.load('fair_outputs/cubes_v145/cube_v145_lhs10ks_baseline_flat2015.npz', allow_pickle=True)
print('cells:', c['cells_meta'].shape, 'unique seeds:', len(np.unique(c['cells_meta'][:,2])))
# Expect: 10000 cells, ~1000 unique seeds
yrs = c['years']; i2020 = int(np.where(yrs==2020)[0][0]); i2021 = int(np.where(yrs==2021)[0][0])
g = c['gmst_traj']
dT = g[:, i2021] - g[:, i2020]
print(f'ΔT 2020→2021: mean={dT.mean():.4f}, std={dT.std():.4f}, 5-95={np.percentile(dT,95)-np.percentile(dT,5):.4f}')
# Expect: std significantly larger than the 0.092 K seen in deterministic LHS-10k,
# because seed noise now adds to (smaller, no-volcanic) cfg spread
PY
```

### 4. Run BRICK on the v5 cubes

The BRICK pipeline driver is `julia/run_mimibrick_flatcube.jl`. Need to
invoke it on both v5 cubes:

```bash
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
# Baseline
julia julia/run_mimibrick_flatcube.jl \
    --cube ~/Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_baseline_flat2015.npz \
    --output outputs/brick_v145_lhs10ks/brick_lhs10ks_baseline_flat2015.csv
# Pulse
julia julia/run_mimibrick_flatcube.jl \
    --cube ~/Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_pulse_co2_pos_001gt_flat2015.npz \
    --output outputs/brick_v145_lhs10ks/brick_lhs10ks_pulse_co2_pos_001gt_flat2015.csv
```

(Check the exact CLI args via `julia julia/run_mimibrick_flatcube.jl --help` —
this driver was used for the LHS-10k cube; should accept v5 cubes the same.)

Each BRICK run is roughly 1 hr local. Could push back to Torch if needed.

### 5. Update Shapley pipeline to point at v5 cubes

Edit `python/scripts/substack/shapley_hawkins_sutton.py`:
- `CUBE_BASE`: switch from `cube_v145_lhs10k_baseline.npz` →
  `cube_v145_lhs10ks_baseline_flat2015.npz`
- `CUBE_PULSE`: switch to `cube_v145_lhs10ks_pulse_co2_pos_001gt_flat2015.npz`
- BRICK CSVs: switch to `brick_lhs10ks_*` paths in `FULL_BASE_CSV` / `FULL_PULSE_CSV`
- **CRUCIAL methodology change**: V_internal now legitimately comes from
  the LHS-10k_s residual (because the cube actually has seed variation).
  Revert the v4 fix for TOTAL targets — set
  `pivot["internal"] = v_residual` instead of `v_internal_anova` for the
  v5 cube. For pulse targets V_internal still stays 0 (matched-seed
  marginal cancels seed by construction).

### 6. Re-render and inspect

```bash
source ~/climate-env/bin/activate
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
python python/scripts/substack/shapley_hawkins_sutton.py
```

Expect:
- `total_gmst` 2021: V_int ≈ 80%+ (canonical H-S near-term).
- `total_gmst` 2150: V_int fraction tiny (~0.5%), V_climate ~45%, V_emi ~55%.
- `total_slr`: BRICK still under-attributed by TreeSHAP (~3-5%); to fix,
  switch to Owen-Shapley (see step 7).
- `pulse_*`: linear-regime fractions unchanged from v4 (seed cancellation).

### 7. (Optional) Owen-Shapley for BRICK figures

`python/scripts/substack/shapley_owen_diagnostic.py` already validated
that Owen gives BRICK ≈ 22-23% (vs TreeSHAP ~3%). Extending it to be a
production renderer (instead of just a diagnostic CSV) would require
generalizing from per-year landmark output to full 131-year output.

Castro-Gomez parameter cost: M=30 × N_outer=60 × N_inner=30 = 54k
predictions/year. 131 years × 4 targets × ~5 min/year = ~40 hrs single-
thread. Need to push this to Torch and parallelize over years.

## Open questions for Marcus

1. After v5 re-render lands: is the V_internal-at-2021 ≈ 80% prediction
   confirmed? If far off, hypothesis: residual ENSO/AMO from FaIR's
   stochastic model is still cfg-modulated and might not be cleanly seed-
   driven. (Test: at 2021, OOF R² should be quite low; if it's still
   0.5+, the surrogate is picking up cfg×seed interactions.)
2. Owen-Shapley re-render: worth ~40 hrs of Torch compute to fix BRICK
   attribution in the figures? Or stick with TreeSHAP + caveat that
   BRICK is conservatively attributed?
3. Pulse figures: with v5 + matched seed cancellation, R² should be
   essentially perfect. Pulse_gmst is currently 100% climate; is that
   the final answer or do we want a different decomposition for the
   pulse axes?

## Files modified / created in this session

```
Modified:
  python/scripts/substack/shapley_hawkins_sutton.py
    - V_internal now reads from ANOVA-18k CSV (was: LHS residual)
    - pulse axes_order strips "internal"
    - Docstring updated
  lhs_climate_v145_meta.py  (FaIRtoFrEDI repo)
    - Added --forcing-file CLI arg

Created:
  calibration_v145/volcanic_solar_flat2015.csv
    - 1995-2014 climatology held constant from 2015 onward
  fair_outputs/metadata_v145/lhs10ks_metadata_v145.csv
    - Same cfg+RFF as LHS-10k, seed_idx LHS-sampled ∈ {0..999}
  slurm_v5_lhs10ks_baseline.sh, slurm_v5_lhs10ks_pulse.sh
  notes/handoff_2026-05-26_v5_noise_isolated_hs.md  (this file)
```
