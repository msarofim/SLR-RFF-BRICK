# t_gis_zones provenance

Built by `python/build_t_gis.py` at commit `bed91d2`.

## What this is
The observed Greenland regional temperature driver for the BRICK-F\* Greenland
module (option A, `notes/scoping_2026-08-10_greenland_options.md` §4, §9).
Headline zone **south** (59-70 N);
pre-registered sensitivity arm **all** (59-84 N).

## Mask
Fractional overlap of each grid cell with **GTN-G 2023 first-order region
05 ("Greenland Periphery")** AND **Berkeley Earth 1-deg land
fraction**, sampled 5x5 per cell, then cos(lat) weighted. Land
fraction enters as a weight, not a threshold. The region polygon tiles Iceland
into region 06, Baffin into 04 and Ellesmere into 03; membership is asserted by
point test at build time.

Supersedes the lon/lat box used in `python/scope_greenland_zones.py`, which
(a) admitted Iceland into the southern band and Baffin/Ellesmere into the
northern ones, and (b) applied a land mask only to Berkeley Earth.

## Products, baselines
| product | grid | baseline | note |
|---|---|---|---|
| HadCRUT5.0.2.0 analysis | 5 deg | 1850-1900 | headline driver; land+ocean blend at 5 deg |
| Berkeley Earth Land+Ocean | 1 deg | 1850-1900 | genuine land mask, best resolved here |
| GISTEMP v4 (1200 km) | 2 deg | 1880-1900 | record starts 1880 |

Annual = calendar-year mean of 12 monthly values; a year is kept only with
>= 12 months (the Berkeley calendar-year parsing discipline).

## Amplification
Through-origin fit of the zone anomaly on the same product's global mean
anomaly. Headline window `full` = (1901, 2024),
matching `brickf_data.AMP_FIT_WIN` so the Greenland and glacier amplifications
are like-for-like.

Zone `south`, window `full`: mean **1.922**,
sd **0.318**, range 1.510-2.285 across the
three products.

**The windows disagree by about 2x and the disagreement is physical.** The
early window is a through-origin fit over decades when the global anomaly was
near zero while Greenland swung by +/-1 C (the early-twentieth-century warm
period), which inflates the ratio; the modern window describes the projection
era. Which window sets the amplification prior is a live methodological choice
recorded in the handoff, not something this script resolves.

## Units and conventions
Degrees C, anomalies relative to the stated baseline, full precision
(%.12f) because the Julia port validation compares at 1e-9.

## Outputs
- `data/observations/t_gis_zones.csv` -- headline HadCRUT5 driver, one column per zone
- `data/observations/t_gis_zones_allproducts.csv` -- every product x zone
- `outputs/gis_driver_constants.csv` -- amplification + melt-rate correlation
