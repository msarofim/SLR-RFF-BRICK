# Quarantine — the SUPERSEDED pulse size (10 GtCO2 / 1 GtCH4), 2026-09-04

## 1. These outputs are NOT WRONG. They are a different, documented pulse size.

Nothing here was produced by a bug. Every gate passed when they were written, and the model path
that produced them is unchanged. What changed is **Marcus's spec**: on 2026-09-04 the pulse moved
from **10 GtCO2 / 1 GtCH4** to **1 GtCO2 / 0.01 GtCH4**, because the old sizes sit ABOVE the clean
regime's ceiling. They are quarantined so a downstream glob cannot mix two pulse sizes into one
figure or table — the `silent retrieval of stale results` hazard, here in its size form.

## 2. Why the size moved — three independent measurements

- **The L24 ladder** (`julia/diag_pulse_size_vv_ladder.jl`, 2026-09-03): 10 GtCO2 biases the
  paired MEDIAN **+20.6 % at 2300** (+1.8 % at 2100) through the threshold-crossing probability.
- **The MAGICC floor ladder** (`FaIRtoFrEDI/magicc_comparison/analyze_pulse_floor_vv.py`,
  2026-09-04, vvHL, 100 members): 10 GtCO2 puts **30/100 members >1 % off** the linear per-unit
  value at 2300 with **six SIGN-FLIPS** at 2100, ensemble median per-unit **0.834**; 1 GtCH4 puts
  **75/100** off, median **0.855**, and is the only rung where even GMST departs (1.3 %).
- **FaIR's own `[DOUBLING]` gate**: at the old sizes CH4 doubled at **2.0332** (1.66 % superlinear);
  at 0.01 GtCH4 it doubles at **2.0003-2.0004** (0.015 %). Cutting the pulse 100x cut the
  superlinearity ~100x, which is the scaling a quadratic term predicts.

## 3. What is here

Every `pulse_ladrillo_{cells,paths,gates,draws}_*_{CO2_10Gt,CH4_1Gt}_*` and every
`pulse_brick2_{cells,paths,gates,draws}_*` file, i.e. the complete stage-2 and stage-3 output at
the superseded size. `draws` files are gitignored and are moved but not tracked.

## 4. The canonical replacement

`outputs/pulse_{ladrillo,brick2}_{cells,paths,gates}_vv<M>_{CO2_1Gt,CH4_0p01Gt}_2030_spliced_*`,
regenerated 2026-09-04 by the same drivers with `--pulse-size=1` / `--pulse-size=0.01`.

## 5. Why keep them

They are the regression test for the size effect itself: the ratio of these numbers to the new ones
IS the measured size bias, and it is the only direct evidence of its magnitude in Ladrillo and
BRICK 2.0. Do not delete. Any result already circulated at the old size keeps its `10Gt`/`1Gt`
label and is never relabelled.
