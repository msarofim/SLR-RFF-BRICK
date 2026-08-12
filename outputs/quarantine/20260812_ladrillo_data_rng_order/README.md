# Quarantine 2026-08-12 — pre-fix `extc_block_constants.csv` (RNG call-order dependence)

## 1. This is a reproducibility fix, NOT a bug fix

`python/ladrillo_data.py`'s `four_rung_fit()` drew its multi-start jitter from a
single module-level `default_rng(FIT_RNG_SEED)` shared by every call. The fitted
`(b, T_off)` therefore depended on **how many fits had already run**, so
`build_artifacts()` had to replay the development call sequence exactly —
including two two-block fits whose results were thrown away and existed only to
consume RNG draws. The file's own header flagged this and said to fix it at the
next recalibration. Item 4.7 of
`notes/handoff_2026-08-11_greenland_pass1_complete.md` §4. That is now.

**Measured before changing anything:** re-running the committed call sequence
under six different global seeds (2026, 1, 7, 12345, 99999, 2027) moved
`(a, b, T_off)` for all three reservoirs on both amplification bases by
**1e-10 to 3e-8**. That is multi-start convergence scatter — every seed finds the
same optimum. No seed switched local minima. So the order dependence never
threatened the science; it threatened reproducibility.

## 2. The fix

`block_rng(block)` derives a stream from `(FIT_RNG_SEED, block name, basis,
amp_b)` via SHA-256, so a fit's jitter depends only on **which** block is being
fitted. `amp_b` is in the key because each block is fitted twice, once per
amplification basis, and those two must not share a stream. The two discarded
RNG-parity fits are deleted from `build_artifacts()`.

## 3. What moved

| artifact | max abs change |
|---|---|
| `data/observations/t_glac_blocks.csv` | **0** (no fitted quantity in it) |
| `outputs/recalib_targets_ext_gsicadj.csv` | **0** (no fitted quantity in it) |
| `outputs/extc_block_constants.csv` | **1.69e-08**, in `T_off_fit_regchar` |

Only the one file changed, and only in the 8th decimal. It is the pre-fix copy
preserved here (last committed at `6771ed5`). The canonical replacement is at
`outputs/extc_block_constants.csv`.

**Order-independence verified:** building the artifacts with the reservoir
dictionary in reverse order now reproduces all three files at max|diff| = 0.0.
Before the fix that permutation would have changed the fitted constants.

## 4. Effect on the extC posterior — none, and it is not re-run for this

The accepted extC posterior was calibrated against the pre-fix
`extc_block_constants.csv`. A 1.7e-8 shift in one offset constant is far below
any MCMC sampling noise, so the posterior is not invalidated and is **not**
regenerated on account of this change. The next posterior (Greenland pass-1
step 5, which mints Ladrillo 1.0) will be calibrated against the post-fix file,
which is why the fix was landed before that run rather than after it.

## 5. Test coverage

`python/test_ladrillo_data.py` [1] previously asserted exact float identity
against the committed dev-chain artifacts. It now asserts three things:
exact identity against the canonical post-fix artifacts (the regression gate),
agreement with **this quarantined dev-chain copy** within a documented
tolerance (the provenance link the original test existed to hold), and
**order-independence** under a permuted build (the property the fix adds).
