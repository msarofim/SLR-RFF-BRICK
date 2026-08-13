# Is `gis_f` a ridge, a multimodality, or unidentified?

- commit `76bbc0a`; tag `L10`; 4 chains, first 50% burned, thinned 1-in-50
- `diag_block_ridge.py` already ruled out RIDGE: the worst-mixing direction is `gis_f +1.00`, every other loading <= 0.06, block correlation condition number 8.

## 1-2. Widths — is the pool the prior, and is each chain narrower?

| quantity | value |
|---|---|
| prior sd | 0.3000 |
| pooled posterior sd | 0.0913 |
| mean WITHIN-chain sd | 0.0737 |
| pooled / prior | **0.30** |
| within / pooled | **0.81** |
| prior mean, range | 0.783, [0.020, 0.980] |

| chain | p05 | p50 | p95 | sd |
|---|---|---|---|---|
| seed2026 | 0.680 | 0.818 | 0.897 | 0.068 |
| seed2027 | 0.522 | 0.722 | 0.837 | 0.096 |
| seed2028 | 0.746 | 0.847 | 0.916 | 0.053 |
| seed2029 | 0.611 | 0.765 | 0.866 | 0.079 |
| POOLED | 0.601 | 0.794 | 0.897 | 0.091 |

## 3. Trace shape — drift (diffusion) or jumps (modes)?

Decile means across the post-burn half, per chain. A monotone walk is diffusion; a step between levels with dwell time is a mode change.

| chain | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | monotone? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seed2026 | 0.88 | 0.82 | 0.80 | 0.80 | 0.80 | 0.83 | 0.71 | 0.79 | 0.87 | 0.80 | no |
| seed2027 | 0.80 | 0.75 | 0.64 | 0.67 | 0.66 | 0.76 | 0.67 | 0.76 | 0.61 | 0.73 | no |
| seed2028 | 0.84 | 0.88 | 0.85 | 0.86 | 0.84 | 0.84 | 0.78 | 0.80 | 0.85 | 0.86 | no |
| seed2029 | 0.78 | 0.81 | 0.83 | 0.81 | 0.78 | 0.73 | 0.73 | 0.70 | 0.68 | 0.69 | no |

## 4. Likelihood grip — do the chains differ in log-posterior?

| chain | corr(param, log_post) | mean log_post | sd log_post |
|---|---|---|---|
| seed2026 | -0.101 | 38.95 | 4.80 |
| seed2027 | +0.092 | 40.42 | 4.68 |
| seed2028 | -0.007 | 39.20 | 4.75 |
| seed2029 | +0.064 | 40.38 | 4.44 |

Spread of chain-mean log_post: **0.67** against a within-chain sd of 4.67 (range 38.95 to 40.42).

## VERDICT

**Not cleanly separated by these tests.** Read the tables above rather than a label: widths, trace shape and log-posterior spread point different ways, which usually means more than one thing is happening.

