# calibrator_300iter — the L24-objective identity reference (RE-FROZEN 2026-09-21)

`chain_L24_seed2026_n300.csv` and `adapted_cov_L24_seed2026.csv` are the 300-iteration, seed-2026 run of the L24
configuration (`scripts/gate_calibrator_identity.sh`) on the calibrator at commit `b94888c` + the seed_diag fix,
with the land-water convention **`LWS_MODE = :central`** (Marcus 2026-09-18, commit 4617723).

**Why re-frozen.** The 2026-09-16 reference (kept verbatim in `../calibrator_300iter_lws_seeded_20260916/`) was
produced under `LWS_MODE = :seeded`. The 09-18 switch to the constant 0.30 mm/yr land-water series changes the
calibration objective by ~1.1e-4 log-units at the start point (LWS enters the Antarctic component through the
sea-level feedback), which is enough to flip accept/reject decisions within 300 iterations. That is the ONLY
change: the current calibrator with `LWS_MODE = :seeded` reproduces the 09-16 reference byte-for-byte (proof run
2026-09-21 07:25, CHANGELOG 09-21c), so every L26/L27 flag is default-off as claimed.

**What this gate can and cannot say.** It certifies that the calibrator still defines the L24 objective under the
09-18 land-water convention. It does NOT certify byte-identity with the shipped L24 chains (those were run under
:seeded); the L24 posterior is unchanged and its reproduction gate is the archived reference.
Mutation test at re-freeze: `--amp-sigma=0.181` → chain differs (FAIL), as it must.
