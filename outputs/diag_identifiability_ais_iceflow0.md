# Is `ais_iceflow0` a ridge, a multimodality, or unidentified?

- commit `76bbc0a`; tag `L10`; 4 chains, first 50% burned, thinned 1-in-50
- `diag_block_ridge.py` already ruled out RIDGE: the worst-mixing direction is `ais_iceflow0 +1.00`, every other loading <= 0.06, block correlation condition number 8.

## 1-2. Widths — is the pool the prior, and is each chain narrower?

| quantity | value |
|---|---|
| prior sd | 0.3410 |
| pooled posterior sd | 0.2233 |
| mean WITHIN-chain sd | 0.1086 |
| pooled / prior | **0.65** |
| within / pooled | **0.49** |
| prior mean, range | 1.237, [0.600, 1.800] |

| chain | p05 | p50 | p95 | sd |
|---|---|---|---|---|
| seed2026 | 0.717 | 0.861 | 1.010 | 0.084 |
| seed2027 | 0.922 | 1.106 | 1.232 | 0.102 |
| seed2028 | 1.181 | 1.337 | 1.462 | 0.082 |
| seed2029 | 1.075 | 1.277 | 1.665 | 0.166 |
| POOLED | 0.781 | 1.177 | 1.464 | 0.223 |

## 3. Trace shape — drift (diffusion) or jumps (modes)?

Decile means across the post-burn half, per chain. A monotone walk is diffusion; a step between levels with dwell time is a mode change.

| chain | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | monotone? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seed2026 | 0.88 | 0.89 | 0.94 | 0.99 | 0.79 | 0.77 | 0.81 | 0.85 | 0.84 | 0.81 | no |
| seed2027 | 1.17 | 1.20 | 1.19 | 1.21 | 1.13 | 1.08 | 1.00 | 0.94 | 1.03 | 0.98 | no |
| seed2028 | 1.29 | 1.37 | 1.45 | 1.42 | 1.30 | 1.21 | 1.35 | 1.37 | 1.35 | 1.26 | no |
| seed2029 | 1.26 | 1.24 | 1.08 | 1.12 | 1.27 | 1.46 | 1.34 | 1.28 | 1.35 | 1.65 | no |

## 4. Likelihood grip — do the chains differ in log-posterior?

| chain | corr(param, log_post) | mean log_post | sd log_post |
|---|---|---|---|
| seed2026 | +0.064 | 38.95 | 4.80 |
| seed2027 | +0.049 | 40.42 | 4.68 |
| seed2028 | -0.224 | 39.20 | 4.75 |
| seed2029 | -0.107 | 40.38 | 4.44 |

Spread of chain-mean log_post: **0.67** against a within-chain sd of 4.67 (range 38.95 to 40.42).

## VERDICT

**Not cleanly separated by these tests.** Read the tables above rather than a label: widths, trace shape and log-posterior spread point different ways, which usually means more than one thing is happening.

