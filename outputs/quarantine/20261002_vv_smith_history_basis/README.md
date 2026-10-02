# Quarantine 2026-10-02 — van Vuuren products built on SMITH 2024 history under calib 1.6.0

## 1. The bug

Every calib-1.6.0 van Vuuren driver read `FaIRtoFrEDI/data/vanvuuren/spliced_ext_harmonized/`,
whose 1750.5–2023.5 block is **Smith 2024 historical emissions**. Those files were built for
calib **1.4.5** and were never rebased when the project migrated to fair-calibrate **1.6.0** on
2026-08-28. The 1.6.0 posterior is conditioned on **CMIP7** historical emissions, so every
product here pairs the 1.6.0 parameters with v1.4.5 history: the rung-R1 input mismatch that
`FaIR-PF-O3/python/diag_calib160_rffsp_ladder.py` exists to measure, and the same silent
substitution that produced a retracted result in August 2026 (memory
`harmonized_vs_rcmip_native`).

`FaIRtoFrEDI/scripts/build_fair_cube_vv_v160.py` made it worse than undeclared: its provenance
string asserted **"CMIP7 historical 1750-2023"** while reading a Smith-2024 file. Any cube in
this directory carries that false claim.

Two secondary defects travelled with it:

- The spliced files **omit the 2021.5 and 2022.5 columns** (documented in
  `build_vanvuuren_extended_splice.py`: `SMITH_LAST_YEAR=2022` while Smith ends 2020.5). FaIR's
  `fill_from_csv` interpolates onto its own timepoints with `interp1d`, so those two years were
  a straight line drawn between a Smith-2020 value and a CMIP7-era 2023 value — a synthetic ramp
  across a three-year gap, not emissions.
- The **ERF cubes** `vanvuuren_ext_{harmonized,zenodo}_erf_cube_v160.npz` are the same basis and
  are quarantined alongside, in `FaIRtoFrEDI/fair_outputs/quarantine/20261002_vv_smith_history_basis/`.

## 2. What is in here

140 CSVs from `SLR-RFF-BRICK/data/observations/`, all seven markers (VL, LN, L, ML, M, HL, H):

- `fair_cube_{gmst,ohc}_vv<MARKER>_raw.csv` — the 841-config base cubes (28 files, the only
  git-TRACKED ones; moved with `git mv`, so the repo did not grow).
- `fair_mean_{gmst,ohc}_vv<MARKER>.csv` — their ensemble means.
- `fair_cube_{gmst,ohc}_vv<MARKER>_{pulse,pulsebase}_{CO2_10Gt,CO2_1Gt,CH4_1Gt,CH4_0p01Gt}_2030_raw.csv`
  — the paired pulse arms (112 files, never git-tracked).

Built 2026-08-30 (base) and 2026-09-03/04 (pulse).

## 3. ⛔ What the regeneration actually moved — and the claim retracted on the way

⛔ **RETRACTED, same day it was made:** "total ERF 2100 +0.116 W/m²" and
"P(ERF>8.5) @2150 marker H 45.42 % → 51.84 %". Both came from re-referencing
total ERF to each arm's own 1850–1900 mean before comparing it to 8.5 W/m². FaIR
already reports forcing relative to 1750 — median total ERF at 1750 is exactly
**0.00000** on both bases — so that double-references it, and the CMIP7 basis's
1850–1900 mean total ERF is **0.098 W/m² lower**, which the second referencing
injected as a shift that is not in the forcing. Read absolutely, as an 8.5 W/m²
threshold requires, **P(ERF>8.5) @2150 on marker H is 42.212 % on both bases —
zero change.** The same cubes read as anomalies reproduce the artifact at +6.06 pp.

⭐⭐ **The mechanism is a COOLER REFERENCE, not extra warming.** The CMIP7 basis
puts the model's own 1850–1900 mean GMST **0.065 K lower** (−0.1269 vs −0.0619 K).
That is why the 2015–2024 anomaly moves closer to IGCC — and since IGCC is itself
a 1850–1900 anomaly and that is the quantity fair-calibrate constrains, the
improvement is real. But the absolute warming level barely moves: 2100 GMST
**−0.010 K**, absolute total ERF ≤0.022 W/m² at every horizon.

### Ensemble-mean GMST, CMIP7 minus Smith (K, anomaly vs 1850–1900)

| marker | d2024 | d2100 | d2300 | d2100 ÷ the ensemble's own p5–p95 |
|---|---|---|---|---|
| VL | +0.0427 | +0.0546 | +0.0701 | 0.037 |
| LN | +0.0427 | +0.0552 | +0.0716 | 0.041 |
| L  | +0.0427 | +0.0550 | +0.0706 | 0.038 |
| ML | +0.0427 | +0.0547 | +0.0718 | 0.032 |
| M  | +0.0427 | +0.0545 | +0.0692 | 0.029 |
| HL | +0.0427 | +0.0544 | +0.0708 | 0.026 |
| H  | +0.0427 | +0.0542 | +0.0673 | 0.026 |

d2024 is **identical to four decimals across all seven markers**, which is the
expected signature: the history block is common to every marker, so a
history-basis change must enter as a common-mode shift. The last column is the
only ruler that makes the size readable — the shift is **2.6–4.1 %** of the
ensemble's own p5–p95 GMST spread at 2100. Systematic, same sign everywhere,
and small against parametric uncertainty.

OHC moves +0.26 (2024) → +1.44–1.47 (2100) → +4.35–4.91 ×10²² J (2300).

### Pulse marginals — the quantity a reader assumes this cannot touch

dGMST @2100 (pulse − pulsebase), ensemble mean, % change vs the Smith basis:

| arm | change |
|---|---|
| CO₂ 10 Gt and 1 Gt | **−0.14 % to −0.20 %** |
| CH₄ 1 Gt and 0.01 Gt | **+0.26 % to +0.33 %** |

⭐ **The two species move in OPPOSITE directions**, which is why this reads as
physics rather than a code path: a warmer background makes the CO₂ pulse slightly
less effective and the CH₄ pulse slightly more. Had every arm moved the same way
by the same amount, the first suspicion would have been a shared code path
([[suspicious uniformity ≈ bug signal]]).

## 4. Canonical replacement

The same 140 paths in `SLR-RFF-BRICK/data/observations/`, regenerated 2026-10-02
from `calibration_v160_prod/emissions_v160_cmip7harm_vv<MARKER>.csv`. All 35
driver runs succeeded, **63 internal gates PASS, 0 FAIL**, and the regenerated
set matches this directory file-for-file. Rebuild:

```bash
python scripts/build_emissions_v160_cmip7harm_vv.py          # all 7 markers
for m in VL LN L ML M HL H; do
  python scripts/build_fair_cube_vv_v160.py  --marker $m
  python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CO2
  python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CO2 --pulse-size 1
  python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CH4
  python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CH4 --pulse-size 0.01
done
```

~26 s per run, ~15 min for the set, on the M4 with BLAS pinned to 4 threads.
Torch was considered and is the wrong venue — submission overhead alone exceeds
the runtime.

⚠ The drivers now DEFAULT to the CMIP7 basis. To reproduce anything in this
directory, pass **`--legacy-basis`**; without it the basis gate refuses the
(calib 1.6.0, Smith-history) pair outright.

## 5. Not quarantined, deliberately

`fair_outputs/vanvuuren_ext_zenodo_erf_cube_v160.npz` is the declared basis of
the Rennert / Raftery / Sarofim NCC Comment figure, which is in minor revisions.
It was moved in this sweep and then **restored**: its own
`PROVENANCE.txt` states the history basis in words ("Smith 2024 history"), so the
deliverable is honestly labelled, and quarantining a live figure's input would
break its reproducibility. See
`FaIRtoFrEDI/fair_outputs/quarantine/20261002_vv_smith_history_basis/README.md`
§3 for why the NCC figure was not retrofitted.

## 6. Where the bytes live

⚠ This repo gitignores quarantine payload (`.gitignore` lines 166-167, 217:
`outputs/quarantine/**/*.csv`, `**/*.npz`), so **the 140 CSVs in this directory
are on disk only** and this README is the only tracked record of them.

That is safe for the 28 base cubes, which WERE git-tracked at
`data/observations/fair_cube_{gmst,ohc}_vv<MARKER>_raw.csv` and
`fair_mean_{gmst,ohc}_vv<MARKER>.csv`: their pre-fix bytes are recoverable from
git history at the canonical path, e.g.

```bash
git show <commit-before-2026-10-02>:data/observations/fair_cube_gmst_vvM_raw.csv
```

The 112 pulse products were never tracked, so **this directory is their only
copy.** Do not clean it without reading §3 — they are the evidence for the size
of the basis effect on a pulse marginal, which is the measurement nobody would
think to redo.
