# diag_vv_zenodo_ab — van Vuuren Medium-to-Low on three emissions bases (2026-10-08)

FaIR 2.2.4 (calib 1.6.0), 841 configs, `volcanic_solar_ML.csv`, `stochastic_run=False` (no RNG), marker ML only.

| arm | emissions |
|---|---|
| `live` | the production file `calibration_v160_prod/emissions_v160_cmip7harm_vvML.csv`: CMIP7 1.6.0 history + IIASA prerelease 2024–2100 + the `harmonized` post-2100 tail |
| `a` | the Zenodo v1.1.1 ML series WHOLE, its own history included (`build_variant_a.py`) |
| `b` | CMIP7 1.6.0 history + the Zenodo v1.1.1 future, per-species scale at 2023.5: Ladrillo `tools/forcing/build_emissions_v160_cmip7harm_vv.py --variant zenodo --markers ML`, with ONE edit, `MAX_ABS_SCALE_DEVIATION = float("inf")` |

**Regenerate** (inputs in FaIRtoFrEDI: `v160_cache/`, `data/vanvuuren/`, `calibration_v160_prod/`):
1. Copy Ladrillo `tools/forcing/{build_emissions_v160_cmip7harm_vv,fair_basis,fair_units,v145_species_maps,emissions_v145_utils}.py`
   into `tools/`, set `MAX_ABS_SCALE_DEVIATION = float("inf")`, and run it twice:
   - with `--variant harmonized`, it must reproduce the production vvML file byte for byte (it does);
   - with `--variant zenodo`, it writes arm `b`.
2. `python build_variant_a.py <zenodo_v111_emissions_1750-2500.csv> <b.csv> <a.csv>`. Its gate: `a`'s future ×
   the scale = `b`'s future, for every species.
3. `python run_ml_ab.py <calibration_v160_prod> <out> <Ladrillo/data/forcing> live=<…> a=<…> b=<…>`.
   - [IDENTITY]: the live arm's GMST and OHC cubes are BYTE-IDENTICAL to the shipped vvML cubes.
   - The a and b cubes DIFFER from them, which shows the gate can fail.
4. `python analyse.py <out>` → `result_ML_20261008.txt`.

The result and its reading are in the CHANGELOG, 2026-10-08j.
