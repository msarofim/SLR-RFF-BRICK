# Pre-fix BRICK outputs — quarantine

## Bug

`MimiBRICK.get_model()` is non-deterministic: each fresh call produces ~1e-5 m
variation in AIS_2100 from an un-seeded internal RNG. For *paired* analyses
(e.g. SLR_pulse − SLR_baseline) across separate script invocations, the
non-determinism produces ~0.1 cm noise per draw — large enough to flip the
sign of marginal pulse responses and produce uniformly-anti-physical paired
diffs.

**Fix** (May 14 2026, ~06:53 EDT): seed Julia's global RNG immediately before
`MimiBRICK.get_model()` in `julia/run_mimibrick_paired_seeded.jl` and
`julia/run_mimibrick_paired_explicit.jl`:

```julia
using Random
Random.seed!(args["seed"])
m = MimiBRICK.get_model(...)
```

See `~/.claude/skills/mimibrick-quirks/SKILL.md` and project CLAUDE.md §4 for
the full diagnosis.

## Quarantine policy

Per user-level CLAUDE.md "Quarantine bugged outputs; don't delete":
- Pre-fix outputs are **moved** here, not deleted.
- The canonical paths now hold post-fix replacements.
- Files here remain available for:
  - Postmortem (how big a difference does the bug make?)
  - Regression-testing the fix
  - Reviewer questions about prior-result lineage

## Contents of `quarantine/20260513_get_model_nondeterminism/`

Six Phase C SSP2-4.5 paired BRICK outputs from May 13 2026, all PRE-fix:

| File | Generated | Note |
|---|---|---|
| `brick_paired_ssp245_baseline_to2300.csv` | 2026-05-13 21:33 | unweighted paired BRICK |
| `brick_paired_ssp245_pulse_to2300.csv` | 2026-05-13 21:33 | unweighted; 1 GtCO₂ pulse @ 2030 |
| `brick_paired_ssp245_vehicle_to2300.csv` | 2026-05-13 21:33 | unweighted; vehicle scenario A |
| `brick_paired_ssp245_baseline_to2300_weighted.csv` | 2026-05-13 21:40 | Wong-weighted version of above |
| `brick_paired_ssp245_pulse_to2300_weighted.csv` | 2026-05-13 21:40 | Wong-weighted; would over/under-state SC-CO₂-SLR |
| `brick_paired_ssp245_vehicle_to2300_weighted.csv` | 2026-05-13 21:41 | Wong-weighted vehicle |

**Replacement status (2026-05-15):** The Phase C SSP2-4.5 paired BRICK runs
have been **regenerated** with the seed-fixed Julia driver. Phase D array
job 8833629 tasks 3-5 produced post-fix replacements:
- `outputs/brick_paired_ssp245_baseline_to2300.csv` (May 15 16:44)
- `outputs/brick_paired_ssp245_pulse_to2300.csv`    (May 15 16:44)
- `outputs/brick_paired_ssp245_vehicle_to2300.csv`  (May 15 16:44)

Wong-weighted versions are being produced by job 8834642
(`slurm/submit_phase_D_wong.sh`). When that finishes, the canonical
`*_to2300_weighted.csv` paths hold post-fix replacements and these
quarantined files are kept solely for postmortem / regression-testing.

## NOT quarantined (but pre-fix)

The Phase A baseline-only N=2000 BRICK outputs:
- `outputs/brick_paired_N2000.csv` (May 13 07:45)
- `outputs/brick_paired_N2000_weighted.csv` (May 13 12:22)

These are PRE-fix but the bug is *immaterial* for them: they are a baseline-
only ensemble (no pulse pairing), so the get_model() ~1e-5 m noise is
~0.001 cm against a ~65 cm baseline — completely negligible for percentile
bands, exceedance tables, or the GMST/SLR Hawkins-Sutton decompositions
that use them. Left at canonical paths intentionally.

## Recovery script (if needed)

The unweighted SSP CSVs were produced by `slurm/submit_phase_C.sh` (or
similar). To recreate with the fix:

```bash
ssh torch
cd /scratch/ms17839/SLR-RFF-BRICK
sbatch slurm/submit_phase_C.sh   # check the script first for SSP-mode flags
```

Then apply Wong importance weighting:

```bash
for SCEN in baseline pulse vehicle; do
  python python/apply_wong_weights.py \
    --paired outputs/brick_paired_ssp245_${SCEN}_to2300.csv \
    --posterior data/MimiBRICK/parameters_subsample_brick.csv \
    --lB outputs/brick_lB_per_post.csv \
    --output outputs/brick_paired_ssp245_${SCEN}_to2300_weighted.csv
done
```
