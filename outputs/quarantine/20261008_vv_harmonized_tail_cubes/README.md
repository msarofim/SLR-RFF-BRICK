# Quarantine 2026-10-08: the van Vuuren FaIR cubes on the `harmonized` emissions

## 1. The bug
The vv cubes were built 2026-10-02 from `FaIRtoFrEDI/calibration_v160_prod/emissions_v160_cmip7harm_vv<M>.csv`, which
used the `harmonized` variant: the IIASA prerelease for 2024–2100, then the published Zenodo v1.1.1 extension ADDED at
the prerelease 2100 level for CO₂.
- For Medium-to-Low the two differ by 10.49 GtCO₂/yr at 2100. The whole tail sat low:
  - −2,098 GtCO₂ of extra removal over 2101–2300;
  - CO₂ below pre-industrial by 2300;
  - GMST 0.73 K [0.51, 1.18] too cold at 2300.
- L and LN carry −167 and −112 Gt; H, HL, M and VL are within 27 Gt.
- The 2024–2100 block of every marker is the superseded prerelease.

CHANGELOG 2026-10-08j; `python/diag_vv_zenodo_ab/`.

## 2. What is here (on disk only; the CSVs are gitignored, as in the 10-02 quarantine)
`data_observations/` holds:
- the 28 base files `fair_{cube,mean}_{gmst,ohc}_vv<M>{_raw,}.csv`. They were tracked; their pre-fix bytes are also in
  git at 10b06ec.
- the 112 pulse cubes `fair_cube_*_vv<M>_{pulse,pulsebase}_<TAG>_raw.csv`. These were untracked, so this is the only
  copy.

sha256 values are in `SHA256SUMS`.

## 3. Replacement
The same paths in `data/observations/`, rebuilt 2026-10-08 by `run_vv_zenodo_rerun_20261008.sh cubes` from the
`zenodo` emissions (FaIRtoFrEDI 202eb74): the CMIP7 1.6.0 history verbatim, plus the published 2024–2300 scenario
scaled per species at 2023.5.

Gates (log `outputs/log_vv_zenodo_rerun_20261008.txt`):
- [VV-ZENODO-BASIS]: every cube is identical to its predecessor through 2023 and moves after; vvML is BYTE-identical to
  the a-vs-b arm `b`; the power check passed.
- [VV-BASIS] passes.

⚠ The pulse cubes are rebuilt, but the pulse ARC downstream of them (Julia pulse drivers, FACTS and MAGICC pulse runs)
is NOT re-run (Marcus 10-08). Everything it produced before 2026-10-08 rests on these quarantined cubes.
