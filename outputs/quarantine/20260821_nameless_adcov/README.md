# Quarantine 2026-08-21 — NAMELESS adapted covariances at canonical names

## The hazard

Both files carry the placeholder header `x1..xN` instead of parameter names, and both
sat at a **canonical-looking path** (`outputs/mcmc/adapted_cov_<TAG>.csv`) whose size
**collides with a live layout**:

| file | rows | collides with |
|---|---|---|
| `adapted_cov_L13.csv` | 59 | L13 layout, NK = 59 |
| `adapted_cov_L14.csv` | 58 | **L14 layout, NK = 58 — the CANONICAL vintage** |

`calibrate_mcmc_ext.jl` dispatches a nameless covariance on SIZE. The branch is

```julia
elseif size(old,1) == NK && !(GIS_REPARAM && basename(ADCOV) == "adapted_cov_L11tune_seed2026.csv")
    cov0 = old        # taken AS-IS, row order assumed to equal the current FREE order
```

so `--adcov=outputs/mcmc/adapted_cov_L14.csv` under the L14 layout would have been
accepted as-is, with the row order **assumed** rather than checked. The file's own
header cannot confirm it, and neither file appears in any vintage name list
(`L11_VINTAGE_ADCOV`, `L10_NAMES`, `OLD54_NAMES`, ...), so nothing else would catch a
permutation either.

That is exactly the failure in memory `nameless_matrix_order`: **a permuted matrix is
still a valid matrix**. It does not error — a parameter silently receives its
neighbour's proposal scale. The precedent in this repo is the `ais_c` / `ais_slope`
row shift, which froze a parameter from iteration 1 while acceptance looked healthy at
0.245 and cost an entire L13 line (see `l13_wrong_model_frozen_aisc`).

## Why quarantined rather than deleted or fixed in place

Nothing reads either file — no script, no run script, no note references them as an
input. They are byproducts, not provenance for any shipped number. The danger is
purely that the **canonical path** invites a future `--adcov=` at them. Moving them out
of `outputs/mcmc/` removes the hazard without destroying anything, per the standing
quarantine convention.

They are NOT renamed or edited: if a row order is ever recovered for one of them, the
file is intact and can be re-headed with `pn0` and returned.

## The canonical replacements — USE THESE

Per-seed covariances, which **name their own rows** (written as `DataFrame(covout, pn0)`
at `calibrate_mcmc_ext.jl:2206`, so they need no vintage entry ever):

* L14 (canonical): `outputs/mcmc/adapted_cov_L14_seed2026.csv` — named, 58 rows
* L13 (fallback):  `outputs/mcmc/adapted_cov_L13_seed2026.csv` — named, 59 rows

A named file takes the `adcov_named` branch and is embedded BY NAME via `embed_cov!`,
which is the only path that cannot permute.

## Still open, deliberately not changed here

The `size(old,1) == NK` as-is branch still accepts ANY nameless covariance whose size
matches, guarded only by one hardcoded filename exception. Quarantining these two
removes today's hazard but not the branch. A general fix — refusing an unrecognised
nameless file, or gating its diagonal against the prior scales — touches the hot path
of every calibration and was left for a change that can be run-tested. Flagged in
`notes/handoff_2026-08-21_*`.
