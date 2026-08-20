# Quarantine — `L11_NAMES` was not in the file's row order (2026-08-19)

## 1. The bug

`julia/calibrate_mcmc_ext.jl` seeds the RAM proposal from a previously adapted
covariance. Those CSVs were written with `DataFrame(covout, :auto)`, so they carry the
placeholder header `x1..xN` and **name none of their rows**; the reader recovered the
row order from a hardcoded per-vintage name list.

The list for the L11 layout, `L11_NAMES`, was built as

```julia
[non-d2 physical...] ++ [d2_gsic_1, d2_gsic_2, d2_steric_1, d2_steric_2] ++ noise
```

i.e. it pulled the `d2_*` block out of its `FREE` position and re-appended it after the
AIS geometry block. But the `d2_*` params are pushed into `FREE` immediately after
`gic_s_r5` and **before** `antarctic_lambda`, so on disk they are rows 35–38 while that
literal placed them at 45–48. **Every row from 35 to 49 was shifted by four.**

The name *set* still matched, so `embed_cov!` reported `name-mapped 57 of 57 rows …
dropped ⟨nothing⟩` and the resulting matrix was a valid, positive-definite permutation
of a valid matrix. Nothing errored.

**Consequence.** Live `ais_c` was seeded with `ais_slope`'s proposal variance:

| live slot | got sd | true owner of that row | correct sd for the slot |
|---|---|---|---|
| `ais_c` | **8.005e-07** | `ais_slope` | 0.6065 (L11tune3) / 1.282 (L12) |
| `ais_runoff_Ton` | 0.5672 | `ais_bedheight0` | 0.01388 |
| `ais_precip0_LOG` | 0.05204 | `ais_mu` | 0.01629 |
| `d2_steric_2` | 0.6065 | `ais_c` | 0.02006 |

`ais_c`'s posterior spans ~95 units, so a proposal sd of 8e-07 freezes it outright.
RAM's update (`M = L(I + η(α−α*)uu'/|u|²)L'`) is multiplicative and rank-one along
`L·u`; a coordinate whose row of `L` is ~0 contributes ~0 to every proposal, so `α`
carries no information about it and it can never be re-inflated. **The seed is the only
chance the coordinate gets** — this was never an adaptation collapse, it was born dead.

Measured receipts:

* `chain_L13tune_seed2026`: `ais_c` moves 245,938 times in 1M iterations and spans
  **7.84e-05** (47.50 → 142.49, span 95, in the L12tune chain from the *same* θ0).
* `chain_L13_seed2026`: span 9.87e-05 over 2M.
* Global acceptance was **healthy throughout** — 0.246 (tune), 0.245 (production) — so
  no run-level diagnostic could see it.

## 2. Which runs are affected

The mis-ordered branch fires only when the ADCOV is L11-vintage **and** `NK ≠ 57`
(at `NK == 57` an earlier branch uses the matrix as-is, which is correct). From the
run logs, the runs that took it:

`L13tune`, `L13_seed{2026,2027,2028,2029}` (quarantined here), and — **not moved, but
equally affected** — `D2G_seed{2026..2029}`, `D2S_seed{2026..2029}`, `D2Sprobe`,
`GISB1`, `GISB2`, `GISBNOSH`, `GISBTUNE`.

**Unaffected, because they took the `size == NK` as-is branch:** `L11tune3`,
`L11_seed{2026..2029}`, `L12tune`, `L12_seed{2026..2029}`, `D2chk{,2,3}`, `GISB0CTRL`,
plus the `extC`/`ext`/`D1` lines (different vintage branches, no reordering).
**The canonical L12 posterior — SLR@2100 = 45.53 cm — is NOT affected.**

## 3. Files quarantined here

All L13-line outputs: the four production chains + tuning chain (`chain_L13*`), their
adapted covariances (`adapted_cov_L13*`), run logs (`log_L13*`), the postprocess /
convergence / projection-variant products (`slr_convergence_L13.csv`,
`projection_variant_L13.csv`, `projection_variant_draws_L13.csv`), and the
`overdispersed_starts.csv` that was rebuilt from the frozen tuning chain (its `ais_c`
dispersion was 1.15e-05 — a direct consequence of the freeze). The canonical
`outputs/mcmc/overdispersed_starts.csv` has been restored from
`overdispersed_starts.csv.pre_l13_bak`, the L12 vintage.

Everything here remains valid as evidence *of the bug* — `projection_variant_draws_L13.csv`
in particular is the 1600-draw dump behind the `gis_amp` refutation in
`notes/handoff_2026-08-19c`, and that refutation is a within-chain regression that does
not depend on `ais_c` mixing.

**None of it may be quoted as a result.** The corrected-projection figure 46.23 cm
@2100 from handoff 19c is likewise a diagnostic on chains that failed their gate.

## 4. Canonical replacement

There is none yet. L13 must be re-run from the top:

```bash
julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 1000000 2026 --tag=L13tune \
  --gis-ordered --gis-basins --adcov=adapted_cov_L12_seed2026.csv
```

then rebuild the starts from the new tuning chain and run `julia/run_l13_production.sh`.
Until that completes, **L12 remains canonical** (SLR@2100 45.53 cm).

## 5. The fix

`julia/calibrate_mcmc_ext.jl`:

1. `L11_NAMES` is now a **frozen literal transcribed from the header of
   `chain_L11tune3_seed2026_n1000000.csv`** (written in `pn0` order, i.e. exactly the
   order RAM wrote the covariance in), no longer re-derived from the live `FREE`.
2. Adapted covariances are now written with `DataFrame(covout, pn0)` — **the header is
   the parameter names**, so new files describe their own row order and need no vintage
   entry. The reader prefers a file's own header whenever it is not `x1..xN`.
3. A **geometry seed gate** prints `sqrt(diag(cov0))` for the seven `GEO_NAMES` and
   `error`s out before sampling if any is below a floor (`ais_c` ≥ 0.05). Receiving a
   neighbouring parameter's scale now fails loudly at second zero instead of silently
   costing 4 h 25 m.
4. `--adcov=<name-or-path>` overrides the seed-preference list explicitly.
5. The L12 covariances are added to `L11_VINTAGE_ADCOV` (verified: all six L11/L12 chain
   headers are identical, so they share the 57-row order).
