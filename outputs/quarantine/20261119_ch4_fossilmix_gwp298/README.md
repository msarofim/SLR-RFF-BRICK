# Quarantined 2026-11-19: Ladrillo / BRICK 2.0 CH4 pulse arms on MAGICC's fossil-mix CH4 climate

The `*_vv*_CH4_*_magiccclim*` products (and their logs) were driven by MAGICC CH4 pulse runs that used MAGICC's
internal fossil fraction. Marcus ruled 2026-11-19 that the MAGICC CH4 pulse is biogenic (`MAGICC_CH4_FOSSFRAC=0`) and
that CH4 is converted with GWP100 = 27.9. The 28 CH4 arms (7 markers x Ladrillo L27 / BRICK 2.0 x spliced / raw) were
re-run on the biogenic climate by `FaIRtoFrEDI/magicc_comparison/run_ch4_biogenic_rerun_20261119.sh` (phase
magiccclim), from `julia/_frozen_scope_slr_pulse_vv{,_brick2}_20261119.jl`. Before that, its regress phase re-ran the
unchanged vvM CO2 spliced arms of both models with the same frozen drivers and reproduced the shipped files value for
value (`python/gate_v11_regression.py`, 8 files); those copies are here too. Copies identical to the re-run outputs
were pruned; `SHA256SUMS` hashes what was kept. Replacements: the same names in `outputs/`. Log: FaIRtoFrEDI CHANGELOG
2026-11-19 (h).
