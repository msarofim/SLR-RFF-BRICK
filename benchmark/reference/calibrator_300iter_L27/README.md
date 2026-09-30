# Calibrator identity reference — L27 (frozen 2026-09-30)

`scripts/gate_calibrator_identity.sh` re-runs the **L27** objective (`run_mcmc_L27.sh`'s flags, starts
and proposal seed) for 300 iterations from seed 2026 and compares the output with the files here.

**`chain_L27prod_seed2026_first300.csv` — PRIMARY, taken from the PRODUCTION run, not from the code
under test.** These are the first 301 lines (header + 300 rows) of
`outputs/mcmc/chain_L27_seed2026_n2000000.csv` (md5 `13587007afe18c699f2eec3d886a8efd`, written
2026-09-20 17:37), the chain behind the shipped L27 posterior. The gate requires every field to
match exactly, **except `accept_rate`**: that column is the WHOLE-RUN acceptance rate stamped on every
row, so it depends on run length (0.23635 apart between 300 and 2M iterations) and says nothing about
the objective. On 2026-09-30 the calibrator at HEAD reproduced all 50 parameters and `log_post` on
all 300 rows, on the restored Frederikse target (md5 `070f74ab`).

**`adapted_cov_L27_seed2026_n300.csv` — SECONDARY (regression only).** This is the proposal
covariance after 300 iterations, from the 2026-09-30 HEAD run. The production run cannot supply it,
because it only wrote the covariance after 2M iterations. It is self-derived, so it detects CHANGE
but cannot certify correctness; the chain comparison is what certifies.

Mutation test at creation: `--amp-sigma=0.181` must make the chain comparison FAIL.

History: the previous gate certified **L24** only. Its references were `../calibrator_300iter/` (the
IMBIE-2026 target, 09-21 afternoon) and `../calibrator_300iter_ais_frederikse_20260921/` (the
Frederikse target). On 2026-09-30 the L24 flags on the restored Frederikse target reproduced the
Frederikse archive byte-for-byte, chain and covariance.
`scripts/gate_calibrator_identity_L24.sh` still runs that check.
