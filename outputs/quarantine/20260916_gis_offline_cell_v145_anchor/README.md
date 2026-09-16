# Quarantine 2026-09-16 — Greenland offline cell: calib-1.4.5 projections + mixed-vintage splice anchor

**Bug.** Two things, both confined to the G4 EVALUATION columns (`proj_SSP*`, `spread_2100_cm`)
and the projection series; the FITS (parameters, gates, nlp, ridges) are untouched by either.

1. The projections were computed on the **calib-1.4.5** SSP mean-GMST files
   (`data/observations/fair_mean_gmst_ssp{126,245,585}.csv`, Jun-12 vintage). Those files were
   regenerated on **FaIR 2.2.4 (calib 1.6.0) + CMIP7** on 2026-08-28 (`839a176`); the offline cell
   was not re-run, so `julia/validate_gis_projection_ab.jl` [3] (suite test 6) has compared a
   1.6.0 kernel against 1.4.5 reference constants since then (ssp126 +0.35, ssp585 −1.84 cm).
2. `project()` took the splice anchor (2014–2024 mean GMST) from `fair_mean_gmst.csv` — the
   1.4.5 RFF-cube mean, never regenerated — while the future came from the scenario file. The
   kernel (`ladrillo_setup`) anchors on the scenario's OWN history. The two histories differ by
   0.027 K over the anchor → 0.15–0.17 cm at 2100 on the g=0 A+B cell, above the 0.10 cm parity
   tolerance. Fixed in `python/gis_offline_cell.py::project` (2026-09-16).

**Files here (pre-fix, as committed):**
- `gis_offline_cell_fits.csv`, `gis_offline_cell_series.csv`, `gis_offline_cell_ridge.csv`,
  `gis_offline_cell.png` — `python/gis_offline_cell.py`, 2026-08-16 run (south zone).
- `gis_g_betaf_variants.csv`, `gis_g_betaf_profiles.csv`, `gis_g_betaf.png` —
  `python/diag_gis_g_betaf.py`, 2026-08-12 run. The `g=0` row of the variants file is the
  provenance of `GIS_OFFLINE_G0` and the five `gis_*` prior centres in `calibrate_mcmc_ext.jl`,
  and the reference `--gis-check` (test 5) and test 6 read. The PARAMETERS in that row are
  expected byte-identical after regeneration (the fit never sees a scenario file); the
  post-fix run's CHANGELOG entry records whether they were.

**Canonical replacements:** the same paths under `outputs/` and `figures/`, regenerated
2026-09-16 on the 1.6.0 drivers with the corrected anchor. Not quarantined: the `_all` zone
sensitivity arm (`*_all.csv`, 2026-08-20) — same stale projections, regenerate with `--zone=all`
if it is ever read again.
