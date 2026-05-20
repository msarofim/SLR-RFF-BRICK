# `data/MimiBRICK/` — external dependency, fetch on first run

The MimiBRICK release artifacts are too large to track in git.

**Required file for Tier 2 reproducibility:**

```
data/MimiBRICK/parameters_subsample_brick.csv
```

This is the 10,000-member posterior subsample over MimiBRICK's free
parameters (ice-sheet sensitivities, AIS tipping thresholds, thermal
expansion sensitivity, AR(1) likelihood nuisance parameters). It drives
the Wong (2026) importance weighting and the conditional-BRICK sampling
in the LHS-10k final ensemble.

## Where to get it

From the MimiBRICK release repository:
[github.com/raddleverse/MimiBRICK.jl](https://github.com/raddleverse/MimiBRICK.jl)

Place the CSV at `data/MimiBRICK/parameters_subsample_brick.csv`.

The Julia BRICK driver will additionally fetch the MimiBRICK Julia
package via `julia/Project.toml` on first run.
