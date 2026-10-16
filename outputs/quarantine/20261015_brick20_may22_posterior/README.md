# 20261015_brick20_may22_posterior — BRICK 2.0 products on the May-22 posterior (SUPERSEDED, not bugged)

**What changed.** On 2026-10-15 Marcus moved the BRICK 2.0 comparison arm from Tony Wong's May-22 posterior subsample
(`data/MimiBRICK/parameters_subsample_brick.csv`, sha256 `78247db8…`, linear-units `antarctic_precip0`) to the joint
SNEASY-BRICK subsample published with MimiBRICK v2.0.0 (Zenodo 10.5281/zenodo.20592337,
`parameters_subsample_sneasybrick.csv`, here `data/MimiBRICK/parameters_subsample_sneasybrick_zenodo20592337.csv`,
sha256 `d74577f6…`, log-space `antarctic_precip0`). The arm reads the file's 35 BRICK columns. CHANGELOG 2026-10-15c
measured the effect before the rerun: SSP2-4.5 BRICK 2.0 total about 4 % lower at 2100 and 2300.

**No bug applies.** These files are the BRICK 2.0 products that the GMD draft (through Tony's TW2) and the CH4/CO2
pulse analysis (10-09) were computed from. They are kept for the paper-number diff, for reviewers, and to measure the
size of the swap.

**How it was made.** `run_brick20_zenodo_swap_20261015.sh arms` copied every output a BRICK 2.0 change can reach
(`.snapshot_list`) before anything ran; `downstream` deleted each copy whose canonical file came back byte-identical.
What remains here is exactly the May-22 bytes of what moved. The `*oldbrick*.parquet` twins were MOVED here (no driver
rewrites them). `SHA256SUMS` lists every kept file.

**Canonical replacements.** The same paths under `outputs/`, `figures/`, `benchmark/` and `deliverables/`, regenerated
by the runner. The pulse chain's own quarantine is
`FaIRtoFrEDI/magicc_comparison/processed/quarantine/20261015_brick20_may22_posterior/`.

**Not re-run, so still on the May-22 file at canonical paths** (older vintages the 10-08 v1.1 rerun also left alone):
the overshoot / matched-dT arms (`*_ssp126_nomarker_*`, `*_ssp534over_nomarker_*`, `*_ssp534overMATCH_*`,
`*_ssp534over_spliced_oldbrick_magiccclim*`), `diag_gcrit_brick2_vs_ladrillo_L24.csv`, and the runtime sentence.
