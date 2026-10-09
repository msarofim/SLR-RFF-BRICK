# Quarantine 2026-10-08: arms and downstream products before the vv-zenodo + record-conditioning rerun

## 1. What changed, and why
`run_vv_zenodo_rerun_20261008.sh` (log `outputs/log_vv_zenodo_rerun_20261008.txt`) changed two things at once
(Marcus 10-08: "go with b and any pending fixes that can be done simultaneously"):

- **The van Vuuren emissions** moved to the published Zenodo v1.1.1 scenario (variant b).
  - The `harmonized` files ADDED the published post-2100 extension at the IIASA prerelease 2100 level. For
    Medium-to-Low that put the CO₂ tail 10.5 GtCO₂/yr low for 200 years: −2,098 GtCO₂, and 0.73 K too cold at 2300.
  - This is a BUG fix (CHANGELOG 2026-10-08j). Every vv arm moved: Ladrillo, BRICK 2.0, the MAGICC-climate arms
    (through MEAN_G), FACTS and MAGICC-SLR.
- **Record conditioning** (10-08g, "own-config, drop"). Ladrillo's FaIR-climate joint arms DROP the draws whose
  Antarctic fast dynamics fire by 2025 on their own config: SSP draws 229, 610, 1260; vv draws 187, 610.
  - This is a method change, not a bug; the v1.1 joint arm is SUPERSEDED.
  - Every Ladrillo FaIR joint arm moved, the SSP ones included.

## 2. What is here
The pre-rerun bytes of every snapshotted file that MOVED: 199 files. 397 unchanged copies were pruned.
- `.snapshot_list`: what was snapshotted.
- `.touched_not_snapshotted`: what changed without a snapshot. `facts_components_shared_n200.csv`'s pre-rerun copy is
  in `facts/quarantine/20261008_vv_harmonized_tail/`; the rest are logs and the diff itself.
- The downstream phase first failed on 5 steps: consumers that could not read the new gate rows, or that compared
  arms by position. They were fixed and the phase re-run. The prune of that first pass had already removed 412 copies
  whose canonical files still held their pre-rerun bytes; they were restored before the re-run, so this directory is
  complete.

Other quarantines of the same rerun:
- the cubes and MAGICC extracts: `../20261008_vv_harmonized_tail_cubes/`;
- the emissions: `FaIRtoFrEDI/outputs/quarantine/20261008_vv_harmonized_tail_offset/`;
- MAGICC-SLR: `MAGICC/slr-refresh/data/quarantine/20261008_vv_harmonized_tail/`;
- FACTS: `facts/quarantine/20261008_vv_harmonized_tail/`.

## 3. Replacements, and what moved
The canonical files in `outputs/`, `figures/` and `benchmark/`. The number-by-number diff is
`outputs/vvz_paper_number_diff_20261008.csv` (`python/vvz_paper_number_diff.py`); the summary is in CHANGELOG
2026-10-08k.

⚠ **NOT regenerated:** `figures/*climate_swap*` (`plot_vv_climate_swap.py`). Its [ARM-MATCH] gate correctly refuses
to compare the conditioned FaIR arm (1,998 draws) with the unconditioned MAGICC-climate arm (2,000). The fix is
Marcus's call; the effect on the quoted swap is ≤ 0.1 cm.
⛔ **CORRECTED 10-08m:** a MIXED-VINTAGE swap had been written by the 18:22 retry and committed; it is in
`../20261008_vv_climate_swap_mixed_vintage/`. Marcus chose the common draw set; the canonical swap is regenerated.
