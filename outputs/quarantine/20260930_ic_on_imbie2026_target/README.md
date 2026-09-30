# IC outputs scored on the IMBIE-2026 AIS target (moved 2026-09-30)

**Not a bug: a different comparison.** On 2026-09-23 (commit `e35396c`) L27's information-criterion
residuals were re-scored against the IMBIE-2026 AIS target (then the working-tree default), so that
L27 and L32 could be compared on one target. At ρ≤0.99 those outputs give ΔBIC(Ladrillo − BRICK 2.0)
= **+9.1**. That is right **only for the L27-vs-L32 comparison**, which is now closed (Marcus 09-24).

**Why moved.** Table 5 in the GMD paper is L27 against **its own** target (Frederikse to 2018 + GRACE,
`recalib_targets_ext.csv` md5 `070f74ab`). The 09-20 run (`3b5bbce`) gave ΔBIC +20.8 there. These
files sat at the canonical paths, where a regeneration of Table 5 from them would have quoted the
wrong target (the handoff 09-29b trap). On 2026-09-30 the working-tree target was restored to
Frederikse and made the prep script's default, and the IC was re-run with equal draw counts. See
CHANGELOG 2026-09-30.

**Files** (all written 2026-09-23 17:51–18:31 on target md5 `eb768cd9`, now kept as
`outputs/recalib_targets_ext_imbie2026.csv`):
- `ic_hindcast_obs_sigma.csv` (was tracked; the HEAD blob at `e35396c` is the same file)
- `ic_hindcast_residuals_brick20.csv`, `ic_hindcast_residuals_ladrillo_L27.csv` (untracked, large)
- `ic_ladrillo_vs_brick20_L27{,_rho0.95,_rho0.9}{.csv,.md,_perdraw.csv}`

`ic_hindcast_residuals_ladrillo_L32.csv` stays at its canonical path: it is only ever scored on IMBIE.
⚠ Re-scoring L32 now needs these obs/BRICK files swapped back in.

**Canonical replacement:** `outputs/ic_ladrillo_vs_brick20_L27*` as regenerated 2026-09-30.
