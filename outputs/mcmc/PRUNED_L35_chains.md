# L35 raw chains — PRUNED 2026-09-29 (Marcus: "it's only a diagnostic")

L35 was a diagnostic arm in the closed L27-vs-L32 arc (held-out pre-1979 test: PARTIAL 1.18σ, AMBIGUOUS
by pre-registration; memory `ais_heldout_pre1979_fails_ambiguously`). Never a candidate. The four raw
4×2M chains were moved to the macOS Trash; everything derived from them is KEPT:

- `data/MimiBRICK/parameters_subsample_brick_mengel_L35.csv` (thinned posterior)
- `outputs/mcmc/{adapted_cov,seed_diag}_L35*` (tracked), `slr_convergence_L35.csv`, `log_L35_seed*.txt`
- `outputs/{postpred,ladrillo_prior_posterior,diag_ais_flux_split_vs_imbie,ssps_components_2300}_L35*`

Regenerate from the seeds in `seed_diag_L35_seed*.txt` + the adapted covariances if ever needed.

| file | bytes | md5 |
|---|---|---|
| chain_L35_seed2026_n2000000.csv | 2006670246 | 146570da63058de970e50b46f9b85666 |
| chain_L35_seed2027_n2000000.csv | 2008827454 | a330be0abf7315c925b33ffe311991bf |
| chain_L35_seed2028_n2000000.csv | 2008703074 | d98c199c3454deebec6a92a8e857700c |
| chain_L35_seed2029_n2000000.csv | 2006780189 | 6807cb5002d1993854d63b8d7386926d |
