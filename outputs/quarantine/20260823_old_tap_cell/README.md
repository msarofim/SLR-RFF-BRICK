# Quarantine — the SUPERSEDED first-order Greenland tap cell

Quarantined 2026-08-23, at commit `1246f2f` (the flip). Per the standing rule:
superseded outputs are moved, never deleted — they are needed to answer "how big was
the change" and to regression-test the replacement.

## 1. Which cell these files were produced with

| | quarantined cell | SHIPPED replacement |
|---|---|---|
| form | first-order (`stages = 1`) | **2-stage cascade** |
| V | 2.0 m | **6.0 m** |
| tau | 50 yr | **800 yr** |
| onset | 6.5 K GMT | **4.69 K GMT** |
| home | high basin (NO+NE), clamped to `k_high*v0` ~ 2.76 m | **whole sheet** |
| ramp width | 1.0 K | 1.0 K (unchanged) |

## 2. Why it was superseded — this is a REFUTATION, not a re-ranking

The first-order **form** is refuted, so no (V, tau, onset) of it could have been kept.
The joint constraint is ≤ 8.1 cm added at 2150 on the ssp585 x2300 arm and 48.6 cm
needed at 2300 to reach the matched p50 — a delivery ratio **R = 6.03**. A reservoir's
response to its ramp is an n-fold repeated integral, so in the long-tau limit (the most
back-loaded any n can be) **n=1 gives 2.82, n=2 gives 7.86, n=3 gives 21.71**; swept
over onsets 1.6–7.5 K, n=1 peaks at **2.89**. The same exact bound refutes every
completely monotone family (ladder, Prony, stretched-exponential, Mittag-Leffler,
power-law). A cascade is not completely monotone, so the bound does not reach it.

See `python/diag_gis_2150_band_veto.py` and
`notes/handoff_2026-08-23c_form_refuted_cascade.md`.

The quarantined cell also sat **1.59x over the top** of the matched ssp585 2300 band
once the bands were forcing-matched (2026-08-21g), and its ssp585 Greenland@2300 of
**230.3 cm** is ~2.3x the physics bracket.

## 3. What is in here

| file | what it is | canonical replacement |
|---|---|---|
| `ssps_components_2300_L14_tap6p5K_V2p0m_tau50.csv` | the tapped SSP deliverable | **`outputs/ssps_components_2300_L14_tap4p69K_V6p0m_tau800_n2_ws.csv`** |
| `ssps_components_2300_L14_tap6p5K_V2p0m_tau50_shapefullcurve.csv` | its `LADRILLO_GIS_SHAPE=gis_amp_shape_fullcurve` sensitivity arm | **`outputs/ssps_components_2300_L14_tap4p69K_V6p0m_tau800_n2_ws_shapefullcurve.csv`** |
| `log_project_ssps_L14_2300_tapped.txt` | its run log | `outputs/log_project_ssps_L14_2300_tapped_cascade.txt` |
| `ssps_components_2300_L14_tapset.csv` | the 25-cell ADMISSIBLE-SET arm | **none — see §5** |
| `ssps_components_2300_L14_tapset_envelope.csv` | its cell-choice envelope | **none — see §5** |
| `log_project_ssps_L14_tapset.txt` | its run log | — |

Untapped base (`outputs/ssps_components_2300_L14.csv`) is **unaffected and NOT
quarantined**: the tap is a projection-side prior switch, and the untapped arm never
carried it.

## 4. The size of the change (medians, cm)

Greenland, and the total, on the three scenarios:

| arm | gis ssp585 2100 / 2150 / 2300 | gis ssp245@2300 | gis 585/245 @2300 |
|---|---|---|---|
| untapped base | 13.9 / 28.2 / **50.0** | 18.3 | 2.73x |
| **quarantined cell** | 13.9 / 28.2 / **230.3** | 18.3 | 12.57x |
| **shipped cascade** | 13.9 / 30.8 / **98.7** | 18.3 | 5.39x |

| arm | total ssp585 2100 / 2150 / 2300 |
|---|---|
| untapped base | 94.7 / 198.6 / **467.6** |
| quarantined cell | 94.7 / 198.6 / **649.7** |
| shipped cascade | 94.7 / 201.2 / **516.7** |

Both cells are EXACTLY inert at 2100 and on the two cool scenarios (0.000e+00) — that
property is unchanged and is gated in `julia/test_gis_tap_wiring.jl`. What changed at
2150 is that the shipped cell moves it by **+2.59 cm = 22.5%** of Greenland's own
sampled p05–p95 width there (11.54 cm), where the quarantined cell moved it by exactly
zero. That is deliberate: SICOPOLIS became a physics-based source at 2150 (`166e1d2`)
and reads 0.61–0.89x, i.e. we are LOW there, not high.

## 5. The `--tap-set` arm has NO replacement, and that is the finding

The 25-cell admissible set was priced on the first-order form, which is now refuted at
every cell. `--tap-set` therefore has nothing valid to run: `project_ssps_components_
ladrillo.jl` errors on the shipped cell's absence from the set file, which is the
correct behaviour, and its message says so explicitly.

CONSEQUENCE FOR REPORTING: the **cell-choice band** those two files carried (1.180 m at
Greenland 2300, 4.4x the sampled p05–p95 of 0.268 m) is currently **unquantified** for
the cascade. Do not quote the quarantined envelope for the shipped cell — it is the
spread of a different, refuted family. Producing a cascade-priced admissible set is
open work.

## 6. Reproducing the quarantined arm

The component still supports it; the shipped cell just no longer is it.

```
ladrillo_set_tap!(bf; v = 2.0, onset = 6.5, tau = 50.0, stages = 1, wholesheet = false)
```

Both keywords must be passed explicitly — `ladrillo_set_tap!` now defaults to the
shipped cascade.
