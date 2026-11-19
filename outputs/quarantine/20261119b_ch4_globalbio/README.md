# Quarantined 2026-11-19 (later): Ladrillo / BRICK 2.0 CH4 arms on the global-switch biogenic MAGICC climate

The `*_vv*_CH4_*_magiccclim*` products were driven by MAGICC CH4 pulse runs with `MAGICC_CH4_FOSSFRAC=0`, which also moved
MAGICC's baseline (the setting applies to all CH4). They were re-run on the split-input MAGICC climate (pulse in the
AFOLU column, default baseline) by `FaIRtoFrEDI/magicc_comparison/run_ch4_split_rerun_20261119.sh` (phase magiccclim,
frozen drivers `julia/_frozen_scope_slr_pulse_vv{,_brick2}_20261119c.jl`, whose regress phase reproduced the shipped vvM
CO2 MAGICC-climate arms value for value). Copies identical to the re-run outputs were pruned; `SHA256SUMS` hashes what
was kept. FaIRtoFrEDI CHANGELOG 2026-11-19 (k).
