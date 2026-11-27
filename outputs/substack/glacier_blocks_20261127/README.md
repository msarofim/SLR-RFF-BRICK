# Glacier-block graphics for a Substack post (2026-11-27)

Made by `python/substack_glacier_blocks.py` (run from the repo root with `~/climate-env/bin/python`). Marcus asked for
a map of the glacier regions colored by Ladrillo's glacier blocks, and a graph of global mean temperature with the
temperature of each block.

| File | What it is |
|---|---|
| `glacier_blocks_map.{png,pdf}` | GTN-G (2023) first-order glacier regions, colored by Ladrillo block; Robinson projection |
| `glacier_blocks_temperature.{png,pdf}` | HadCRUT5 temperature over each block and the global mean, 1850-2024, relative to 1850-1900 |
| `glacier_blocks_temperature_series.csv` | The plotted series: annual and 11-year centered values; provenance in the first row's `provenance` cell |
| `world_land_rmaps.gpkg` | Land outline exported from R's `maps` package; a cache the script rebuilds if missing (not committed) |

## Blocks

Membership is read from Ladrillo v1.0.0 `data/constants/glacier_block_constants.csv`:

- Slow-responding Arctic (SLOWG): RGI 03, 06, 07, 09
- Faster-responding (FASTG): RGI 01, 02, 04, 08, 10, 11, 12, 13, 14, 15, 16, 17, 18
- Antarctic and Subantarctic (R19): RGI 19
- In no block, hatched gray: 05, the Greenland periphery (modeled with the Greenland ice sheet), and 20, the Antarctic
  mainland. GTN-G 2023 splits RGI 6's region 19 into 19 (islands and the coastal ring) and 20 (the mainland, which is
  the ice sheet and holds no RGI 6 glaciers).

## Choices to confirm

- Global mean is HadCRUT5's own global series (the same product and baseline as the block series), not IGCC.
- Baseline 1850-1900, the frame of Ladrillo's glacier drivers; the script asserts the inputs are already on it.
- 11-year centered running mean, with no partial windows, so the thick lines end at 2019; thin lines are annual.
- Before 1898 some region-years are filled from the global series in the source extraction: Arctic Canada North in 46
  of the 48 years 1850-1897, South Asia West and East in 22 and 18 years before 1875, New Zealand 1850-1854, Alaska
  1855. Checked by finding the years that lie exactly on one line against the global series.
- GTN-G draws region 16 (Low Latitudes) as one box across the tropics, so the map shows it that way.

## Numbers in the figures (11-year means centered on 2019, degC relative to 1850-1900)

Slow-responding Arctic 3.14, Faster-responding 1.74, Antarctic and Subantarctic 0.70, global 1.24. Ratios to global:
2.53, 1.41, 0.57 (Ladrillo's HadCRUT5 regression amplifications over 1901-2024: 2.48, 1.40, 0.61).
