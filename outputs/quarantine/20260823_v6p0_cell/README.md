# Quarantine — the V = 6.00 m cascade cell (shipped for part of 2026-08-23)

Quarantined 2026-08-23, same day it shipped. **This is a REFINEMENT within one family,
not a refutation** — unlike `../20260823_old_tap_cell/`, where the functional form
itself was ruled out. Everything about this cell except V is unchanged in the
replacement.

| | quarantined | SHIPPED replacement |
|---|---|---|
| stages | 2 (cascade) | 2 (cascade) |
| **V** | **6.00 m** | **5.64 m** |
| tau | 800 yr | 800 yr |
| onset | 4.69 K | 4.69 K |
| home | whole sheet | whole sheet |

## Why V moved

V = 6.00 was chosen to land our ssp585 Greenland@2300 exactly on the matched p50
(1.001×). It **missed the 2250–2300 melt-rate criterion at 1.055× the band top** — a
criterion that had never been evaluated at n = 2, because ψ = 100·V/τ is a first-order
parameterisation that does not exist on a cascade, so the flux had to be measured off
the trajectory instead.

Scored on a V ladder at fixed (onset, τ, stages) the replacement is not a compromise:

| V | 2100/ISMIP6 | 2300/Greve | 3001/Greve | w(6:3:1) | ssp585@2300 |
|---|---|---|---|---|---|
| 5.20 | 1.361 | 0.757 | 0.921 | 0.3268 | 91.7 |
| 5.40 | 1.363 | 0.767 | 0.953 | 0.3260 | 93.3 |
| **5.64** | 1.365 | 0.780 | **0.990** | **0.3258** ← min | 95.3 |
| 5.80 | 1.367 | 0.788 | 1.015 | 0.3260 | 96.6 |
| 6.00 | 1.369 | 0.798 | 1.046 | 0.3267 | 98.2 |

5.64 is the minimum under the 2100 > 2300 > 3001 weighting the evidence supports,
within 0.1% of the minimum under every other weight set, and **exactly the largest V
clearing the melt-rate band when that is solved in the component rather than the
offline emulator** (5.66 offline, 5.64 wired — a 0.4% port, but the cell sits ON the
boundary so 0.4% decides it). Two independent criteria 700 years apart — the 2250–2300
rate ceiling and the Greve/SICOPOLIS year-3001 commitment — land within 1% of each
other there.

## What it cost, and what it did not

Greenland ssp585@2300 **98.7 → 95.7 cm**, i.e. 0.999× → **0.969×** the matched p50 —
**2.6%**. Everything else improves or is unchanged:

| | V=6.00 | V=5.64 |
|---|---|---|
| 2250–2300 rate (r2300) | 44.0 — **OUT** (1.06× band top) | 41.5 — **IN** (at the top) |
| Greve @3001 | 1.046× | **0.990×** |
| ssp585/ssp126 separation (target 8.87×) | 9.88× (1.11) | **9.54× (1.08)** |
| ssp585/ssp245 separation (target 6.40×) | 5.38× (0.84) | 5.21× (0.81) |
| 2150 move | +2.59 cm (22.5% of spread) | +2.44 cm (21.1%) |
| 2100, cool scenarios | exactly inert | exactly inert |
| hindcast 1850–2025 | 0.000e+00 | 0.000e+00 |

**NOT fixed by either cell**: the 2100 ratio is ~1.365× at every V on the ladder (the
whole 5.2–6.0 range spans 0.6%). That is the amplification law, localised in
`python/diag_gis_2100_bias_decomp.py` — driven by each GCM's own Greenland temperature
our ice response lands on the ISMIP6 median (0.99×); driven through our amp law it
over-shoots 1.31×.

## Files

| file | replacement |
|---|---|
| `ssps_components_2300_L14_tap4p69K_V6p0m_tau800_n2_ws.csv` | `outputs/ssps_components_2300_L14_tap4p69K_V5p64m_tau800_n2_ws.csv` |
| `..._shapefullcurve.csv` | `outputs/ssps_components_2300_L14_tap4p69K_V5p64m_tau800_n2_ws_shapefullcurve.csv` |
| `log_project_ssps_L14_2300_tapped_cascade{,_shapefullcurve}.txt` | `outputs/log_project_ssps_L14_2300_tapped_v5p64{,_shapefullcurve}.txt` |

Reproduce: `ladrillo_set_tap!(bf; v = 6.0)` — every other keyword already defaults to
the shipped cell's value.
