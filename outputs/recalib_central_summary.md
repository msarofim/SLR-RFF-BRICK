# Quick central BRICK recalibration — result

Point recalibration from the post-#93 posterior central vector [MEDOID draw post_idx=5808 (the real posterior member closest to the ensemble-median trajectories)], FaIR-mean
GMST+OHC forcing, MimiBRICK v2.0.0 (precip_log shim). 5 knobs, coordinate-descent.
All cm rel 1995-2005; fit window 1900-2018.

## Calibrated knobs

| knob | before (central) | after | bound [lo, hi] | railed? |
|---|---:|---:|---|:--:|
| ais_ocean_temperature₀ | 0.72 | 0.912 | [0.72, 2] |  |
| ais_α | 0.1861 | 0.3512 | [0.01921, 0.6229] |  |
| anto_α | 0.1578 | 0.3651 | [0.01509, 0.5984] |  |
| anto_β | 0.5571 | 0.5275 | [0.09617, 1.821] |  |
| gsic_β₀ | 0.001029 | 0.00119 | [0.0007732, 0.00119] | **RAIL** |
| gsic_v₀ | 0.4999 | 0.3202 | [0.3202, 0.5176] | **RAIL** |
| gsic_teq | -0.15 | -0.4 | [-0.4, -0.15] | **RAIL** |
| gsic_n | 0.6419 | 0.9782 | [0.5734, 0.9782] | **RAIL** |
| gsic_s₀ | 0.07756 | 0.007885 | [-0.04571, 0.07339] |  |
| te_α | 0.1566 | 0.1679 | [0.1162, 0.2103] |  |

Objective (reduced weighted SSR): before = 34.882 → after = 1.036

## Per-component fit @1900 and RMSE over 1900-2018 (cm)

| component | target @1900 | before @1900 | after @1900 | RMSE before | RMSE after |
|---|---:|---:|---:|---:|---:|
| AIS | -0.63 | -3.96 | -0.73 | 1.63 | 0.05 |
| GSIC | -7.28 | -3.35 | -6.05 | 1.57 | 0.65 |
| Steric/TE | -3.61 | -3.99 | -4.28 | 0.34 | 0.27 |
| **Total vs Dangendorf** | -14.20 | -14.52 | -14.28 | 0.87 | 0.92 |

GIS is NOT adjusted (fixed by post-#93 calibration); LWS uses the Frederikse
TWS budget add-on (BRICK LWS is zero historically). The medoid central draw's AIS@1900
≈ the ensemble median (−3.96 vs −3.97), so the 'before' here represents central BRICK.

Modern AIS rate ΔAIS(1992-2017) cm: before 0.93 → after 0.71 (IMBIE target 0.72).

**Key reading (incl. the frozen equilibrium temperatures + anto ocean-sensitivity knobs):**
- AIS LEVEL *and* SHAPE are fixable, but only by freeing ais_ocean_temperature₀ JOINTLY with
  anto_α (global-T→Antarctic-ocean-temp sensitivity) and ais_α: anto_α carries the modern (IMBIE)
  acceleration so ais_ocean_temperature₀ stays near ~0.9 instead of railing to flatten the shape.
  Fitting AIS *level* alone (no modern-rate term, no anto_α) produces a front-loaded see-saw
  (too much 1900-1940 melt, too little post-2000) — Marcus flagged this; the modern term fixes it.
- **gsic_teq (the FROZEN glacier equilibrium temperature, GSIC analog of the AIS knob) is the key
  additional GSIC lever**: it takes GSIC@1900 from −3.4 (5-knob, stuck at ~half) toward the Frederikse
  loss. With a PHYSICAL floor at −0.4 °C it reaches ~−5.9 (RMSE 0.68); UNCONSTRAINED it rails at −1.0 °C
  for −6.64 — but −1.0 implies glaciers melting below the Little Ice Age, which is unphysical. So the
  residual ~1.3 cm GSIC undershoot is the irreducible structural shortfall under a physical teq.
- With GSIC supplying the historical melt, the total-vs-Dangendorf MATCHES (RMSE ~0.88) — the 5-knob
  degradation was error cancellation (too-negative AIS offsetting too-positive GSIC); now resolved.
- gsic_β₀ and gsic_n/gsic_s₀ also move/rail but are amplitude/shape knobs; gsic_teq does the real work.
