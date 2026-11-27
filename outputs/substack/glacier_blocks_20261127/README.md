# Glacier-block graphics for a Substack post (2026-11-27)

Made by `python/substack_glacier_blocks.py` (run from the repo root with `~/climate-env/bin/python`). Marcus asked for
a map of the glacier regions colored by Ladrillo's glacier blocks, and a graph of global mean temperature with the
temperature of each block; then (same day) for southern Greenland, a 1900 start, and an extension to 2050 on the van
Vuuren Medium scenario using Ladrillo's extrapolation method.

| File | What it is |
|---|---|
| `glacier_blocks_map.{png,pdf}` | GTN-G (2023) first-order glacier regions, colored by Ladrillo block; Robinson projection |
| `glacier_blocks_temperature.{png,pdf}` | Each block, southern Greenland and the global mean, 1900-2050, relative to 1850-1900 |
| `glacier_blocks_temperature_series.csv` | Every plotted series (observed annual and smoothed, continuation on the fixed arm, joint-arm median check), 1850-2050; provenance in the first row's `provenance` cell |
| `ladrillo_drivers_vvM_check.csv` | Ladrillo's own `glacier_driver`/`greenland_driver` output on the same inputs, written by `julia/substack_glacier_blocks_check.jl`; the script's gate |
| `world_land_rmaps.gpkg` | Land outline exported from R's `maps` package; a cache the script rebuilds if missing (not committed) |

Order of a rebuild: `julia --project=../Ladrillo julia/substack_glacier_blocks_check.jl vvM outputs/substack/glacier_blocks_20261127/ladrillo_drivers_vvM_check.csv`
(refuses to overwrite), then the Python script, which stops before drawing if its continuation differs from that file
by 1e-9 K or more.

## Blocks

Membership is read from Ladrillo v1.0.0 `data/constants/glacier_block_constants.csv`:

- Slow-responding Arctic (SLOWG): RGI 03, 06, 07, 09
- Faster-responding (FASTG): RGI 01, 02, 04, 08, 10, 11, 12, 13, 14, 15, 16, 17, 18
- Antarctic and Subantarctic (R19): RGI 19
- In no block, hatched on the map: 05, the Greenland periphery (modeled with the Greenland ice sheet), in yellow, the
  southern Greenland color of the temperature chart (Marcus 11-27); and 20, the Antarctic mainland, in gray. GTN-G
  2023 splits RGI 6's region 19 into 19 (islands and the coastal ring) and 20 (the mainland, which is the ice sheet
  and holds no RGI 6 glaciers). Yellow against orange is 13.7 on the dataviz normal-vision check, below its floor of
  15, and 05 borders orange 04, so the hatching, the region numbers and the legend carry the distinction too.
- Southern Greenland (temperature chart only) is the Greenland module's driver: HadCRUT5 over 59-70 N, weighted by
  overlap with RGI 05 and by land fraction. Yellow on both figures.

## The 2025-2050 continuation

Ladrillo's `src/model.jl`, re-implemented in Python and checked against the Julia functions (max difference 4e-15 K):

- block g: T_g(t) = mean_obs_g(2014-2024) + A_g (G(t) - mean G(2014-2024)), with G FaIR's GMST rebased to 1850-1900;
- southern Greenland: the same with A S(t) G(t), S the warming-level shape (table `gis_amp_shape.csv` on the 30-year
  centred running mean of G), anchored on mean(S G) over 2014-2024.

The gate was mutation-tested: a 10-year anchor window, a 31-year shape window and a 1851-1900 baseline each fail it.

## Choices to confirm

- Central lines use Ladrillo's fixed-climate arm: FaIR 2.2.4 (calib 1.6.0) ensemble-mean GMST for vvM, with each
  amplification at its median over the 2,000 projection draws (posterior rows 1:5:10000). The continuation is linear
  in the amplification, so this equals the median over draws on that climate. Amplifications: SLOWG 2.638, FASTG
  1.461, R19 0.727, Greenland 1.912.
- Joint-arm check (each draw paired with one FaIR config, spliced at 2014, median over pairs; a seeded numpy pairing,
  not Ladrillo's Julia one, and without its record conditioning, which concerns Antarctica): at 2050 the fixed arm is
  higher by 0.08 (slow Arctic), 0.03 (faster), 0.02 (Antarctic), 0.05 (Greenland) and 0.03 K (global).
- The global line after 2024 is FaIR's GMST as Ladrillo uses it, not anchored to observations. Over 2014-2024 the
  FaIR mean is 1.177 K and HadCRUT5 1.239 K, so the dashed global line starts about 0.06 K below where an
  observation-anchored line would. The regional lines are anchored to observations by construction.
- Global mean before 2025 is HadCRUT5's own global series (the same product and baseline as the regional series).
- Baseline 1850-1900, the frame of Ladrillo's drivers; the script asserts the inputs are already on it.
- 11-year centered running mean using only years after 1897, so no year filled from the global series in the source
  extraction enters a plotted value; thick lines therefore run 1903-2019, thin lines are annual from 1900.
- GTN-G draws region 16 (Low Latitudes) as one box across the tropics, so the map shows it that way.

## Numbers in the figure (K relative to 1850-1900)

| | 11-yr mean centered on 2019 | 2050, fixed arm | ratio to global at 2050 |
|---|---|---|---|
| Slow-responding Arctic | 3.14 | 5.13 | 2.66 |
| Faster-responding | 1.74 | 2.85 | 1.47 |
| Antarctic and Subantarctic | 0.70 | 1.25 | 0.65 |
| Southern Greenland | 1.99 | 3.16 | 1.63 |
| Global mean | 1.24 (HadCRUT5) | 1.93 (FaIR) | 1 |
