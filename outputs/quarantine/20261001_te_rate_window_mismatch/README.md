# Quarantine 2026-10-01: `diag_te_rate_attribution` compared rates over different spans

**Bug.** `python/diag_te_rate_attribution.py` took every rate over `WIN = (1993, 2026)`, masking each series
separately with `np.isfinite`. The model TE, BRICK 2.0 TE and FaIR OHC run through 2026. The steric target and the
Cheng OHC product stop in 2025, and IGCC stops in 2024. So every ratio in blocks [A]–[C] divided a 1993–2026 model
rate by an observed rate over a span one or two years shorter.

**Fix (2026-10-01).** `WIN = (1993, 2025)`, the last year with thermal-expansion, Antarctic and Greenland
observations (Marcus 10-01: "update to 2025"). A new `common_win()` clips each ratio to the years where all of its
series are finite, and the window used is written into each row's `note`.

**Files here** (pre-fix; produced by the same driver):
`diag_te_rate_attribution_{L14,L21,L24,L27,L28}.csv`. Only L27 is cited in the paper. The others are older lineage
and were not regenerated.

**Canonical replacement:** `outputs/diag_te_rate_attribution_L27.csv`
(`python python/diag_te_rate_attribution.py --tag=L27`).

| quantity | pre-fix | post-fix (span) |
|---|---|---|
| Ladrillo TE / steric target | 1.234 | 1.223 (1993–2025) |
| BRICK 2.0 TE / steric target | 1.172 | 1.162 (1993–2025) |
| FaIR OHC / Zanna+Cheng 0–2000 m | 1.285 | 1.274 (1993–2025) |
| FaIR OHC / Zanna+IGCC 0–2000 m | 1.236 | 1.215 (1993–2024) |
| α model / obs-implied (Cheng) | 0.960 | 0.960 (1993–2025) |
| α model / obs-implied (IGCC) | 0.998 | 1.006 (1993–2024) |
| [D] IGCC full-depth / 0–2000 m | 1.102 | 1.102 (unchanged; already 1993–2024) |

**Size of the bug.** It moved the paper's ratios by 0.01–0.02: 1.23× → 1.22×, 1.17× → 1.16×, and
1.24–1.29× → 1.21–1.27×. The post-fix FaIR/IGCC ratio, 1.215, now agrees with the paper's 1.10 × 1.10 = 1.21
decomposition, which the pre-fix 1.24 did not.
