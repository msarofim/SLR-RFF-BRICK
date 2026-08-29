# NCEI / NOAA global ocean heat content, world ocean, by layer

Fetched 2026-08-29 for the OHC-partition robustness check (does the observed
decline in the above-700 m share survive a second product and a different
window?), which gates whether an "OHC aging module" is worth building to
replace FaIR's box→depth mapping.

Source directory:
  https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/

| file | layer | span | bytes |
|---|---|---|---|
| `h22-w0-700m.dat`  | 0–700 m, world ocean  | 1955.5–2025.5 | 4104 |
| `h22-w0-2000m.dat` | 0–2000 m, world ocean | 2005.5–2025.5 | 1254 |

Columns: `YEAR WO WOse NH NHse SH SHse`. Units 1e22 J (the "h22" in the
filename). `WO` = world ocean, `WOse` = its standard error. Anomalies are
relative to NCEI's own climatology, NOT to 1971 — so any share formed from
these must be REBASED to a common year first, and the same rebasing applied to
whatever it is compared against.

⚠ THE SPAN DIFFERENCE IS ITSELF A RESULT. NCEI publishes annual 0–700 m back to
1955 but annual 0–2000 m only from 2005 — the Argo era. The data provider does
not consider the annual 700–2000 m layer well enough observed before then.
IGCC's compilation does carry a 700–2000 m column back to 1971; that column is
a reconstruction over most of its length, and a partition trend fitted across
1993–2024 spans a change of observing system.

⚠ NOT INDEPENDENT OF IGCC. IGCC's `earth_energy_imbalance.csv` ocean columns are
a multi-product compilation (Palmer / von Schuckmann) that includes NCEI among
its inputs. Agreement is therefore a weak check; DISAGREEMENT would be the
informative outcome.
