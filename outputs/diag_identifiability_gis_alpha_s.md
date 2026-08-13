# Is `gis_alpha_s` a ridge, a multimodality, or unidentified?

- commit `76bbc0a`; tag `L10`; 4 chains, first 50% burned, thinned 1-in-50
- `diag_block_ridge.py` already ruled out RIDGE: the worst-mixing direction is `gis_alpha_s +1.00`, every other loading <= 0.06, block correlation condition number 8.

## 1-2. Widths — is the pool the prior, and is each chain narrower?

| quantity | value |
|---|---|
| prior sd | 0.0200 |
| pooled posterior sd | 0.0039 |
| mean WITHIN-chain sd | 0.0034 |
| pooled / prior | **0.19** |
| within / pooled | **0.88** |
| prior mean, range | 0.007, [0.000, 0.200] |

| chain | p05 | p50 | p95 | sd |
|---|---|---|---|---|
| seed2026 | 0.001 | 0.007 | 0.014 | 0.004 |
| seed2027 | 0.000 | 0.003 | 0.008 | 0.002 |
| seed2028 | 0.001 | 0.008 | 0.015 | 0.004 |
| seed2029 | 0.000 | 0.004 | 0.011 | 0.003 |
| POOLED | 0.001 | 0.005 | 0.013 | 0.004 |

## 3. Trace shape — drift (diffusion) or jumps (modes)?

Decile means across the post-burn half, per chain. A monotone walk is diffusion; a step between levels with dwell time is a mode change.

| chain | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | monotone? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seed2026 | 0.01 | 0.01 | 0.01 | 0.01 | 0.00 | 0.01 | 0.00 | 0.01 | 0.01 | 0.01 | no |
| seed2027 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | no |
| seed2028 | 0.01 | 0.01 | 0.00 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | no |
| seed2029 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | no |

## 4. Likelihood grip — do the chains differ in log-posterior?

| chain | corr(param, log_post) | mean log_post | sd log_post |
|---|---|---|---|
| seed2026 | +0.005 | 38.95 | 4.80 |
| seed2027 | +0.020 | 40.42 | 4.68 |
| seed2028 | +0.081 | 39.20 | 4.75 |
| seed2029 | +0.082 | 40.38 | 4.44 |

Spread of chain-mean log_post: **0.67** against a within-chain sd of 4.67 (range 38.95 to 40.42).

## VERDICT

**Not cleanly separated by these tests.** Read the tables above rather than a label: widths, trace shape and log-posterior spread point different ways, which usually means more than one thing is happening.

