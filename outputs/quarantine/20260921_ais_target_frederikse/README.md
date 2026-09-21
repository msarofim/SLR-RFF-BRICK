# Superseded calibration target: AIS on Frederikse 2020 (to 2018) + GRACE-FO (2019–2026)

**Not a bug — a superseded input.** Kept here (per the quarantine rule) so every result fitted or scored
against it (L11 → L27, the GMD draft through r9) can be reproduced and the size of the change measured.

- `recalib_targets_ext.csv` — the target file as committed at `893bfaa` and used by every calibration through
  **L27** (md5 070f74abe11080da7b77a80b67c54033). AIS column = Frederikse 2020 1900–2018, GRACE-FO JPL mascons
  offset-matched over 2003–2018 for 2019–2026. GIS / GSIC / steric / LWS / total columns are UNCHANGED in the
  replacement.
- `recalib_targets_ext_sources.csv` — its sources sidecar.
- Replacement: `outputs/recalib_targets_ext.csv` rebuilt 2026-09-21 with `python/prep_recalib_targets_ext.py`
  (default `AIS_SOURCE = "imbie2026"`): IMBIE 2026 (Otosaka et al., Sci Data 13:1301) 1979–2023, Frederikse
  1900–1978 offset-matched over 1979–1988, GRACE 2024–2026 matched over 2003–2023. `--ais-frederikse`
  regenerates this file byte-for-byte.
- Why: `python/diag_imbie2026_vs_targets.py` — this target sat 22 % below the reconciled record on the
  1992–2020 Antarctic rate (−1.3σ with both bars), low in every window since 1979. CHANGELOG 09-21f/g.
- First calibration on the replacement: **L28**.
