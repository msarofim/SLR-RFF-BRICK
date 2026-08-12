# Gate 3.2 verdict — the 28 cm shift is entirely Antarctic, and it is a tipping-probability shift

2026-08-11. Answers the second gated diagnostic in
`notes/handoff_2026-08-11_greenland_pass1_complete.md` §3.2.

Script: `python/diag_mengel_to_brickf_attribution.py`.
Outputs: `outputs/diag_mengel_to_brickf_attribution{,_summary.md}.csv`,
`figures/diag_mengel_to_brickf_attribution.png`.

**Verdict: the expectation on record is confirmed — it is the Antarctic — but
the shift must not be reported as "BRICK-F\* is 28 cm lower". See §3.**

---

## 1. Why the proposed experiment was not run

The handoff proposed a parameter-block swap: run the extC kernel with the AIS
block held at BRICK-Mengel posterior medians. **That experiment is ill-posed**
and would have produced an uninterpretable number:

- BRICK-Mengel sampled **6** AIS-related parameters (`ais_ocean_temperature₀`,
  `antarctic_alpha`, `antarctic_nu`, `antarctic_temp_threshold`, `anto_alpha`,
  `anto_beta`). extC samples those 6 **plus 11 more** (`ais_bedheight0`,
  `ais_c`, `ais_gmst_amp`, `ais_iceflow0`, `ais_mu`, `ais_precip0_LOG`,
  `ais_runoff_Ton`, `ais_slope`, `antarctic_gamma`, `antarctic_kappa`,
  `antarctic_lambda`). **Those 11 are the re-parameterisation.** Holding 6 at
  Mengel values while 11 stay at extC values describes no model that was ever
  calibrated.
- The glacier structures also differ (2-τ single reservoir vs 3-reservoir), so
  no single kernel runs both posteriors.

The well-posed version is a **component decomposition of the two projections**,
which answers the actual question — which component moved, and by how much.

**Comparability, checked before differencing** (the script refuses otherwise):
both vintages use the same forcing files
(`data/observations/fair_mean_{gmst,ohc}_<ssp>.csv`), the same **FaIR mean**
climate treatment (parameter spread only), and the same 1995–2014 baseline.
`outputs/proj_matched_ssp245_mengel_timeseries.csv` is **not** usable here — it
pairs each draw with a FaIR ensemble member, so it carries climate spread too.

---

## 2. The attribution — medians at 2100 (cm)

| component | BRICK-Mengel | BRICK-F\* | shift |
|---|---|---|---|
| **Antarctic** | 43.05 | 11.74 | **−31.32** |
| Glaciers | 6.27 | 10.56 | +4.29 |
| Thermal expansion | 18.45 | 17.27 | −1.18 |
| Greenland | 7.42 | 7.27 | −0.15 |
| Land water storage | 2.60 | 2.60 | 0.00 |
| **TOTAL** | **78.02** | **49.48** | **−28.54** |

SSP2-4.5. Median non-additivity 0.18 cm — the decomposition closes.

**The Antarctic accounts for 110% of the shift**; glaciers push back +4.3 cm and
everything else is noise. Greenland moves −0.15 cm, i.e. the Greenland module
had nothing to do with it. The expectation on record is confirmed.

Note the memory figure of 77.7 cm should read **78.02 cm**
(`outputs/proj_ssps_mengel_summary.csv`, SSP2-4.5 p50 @2100).

---

## 3. The correction that matters: it is not a level shift

The shift is wildly scenario-dependent — **−0.01 cm at SSP1-2.6**, −28.54 at
SSP2-4.5, −19.09 at SSP5-8.5. A uniform reduction in Antarctic mass loss cannot
do that. The Antarctic quantiles explain it:

| ssp | quantile | BRICK-Mengel | BRICK-F\* | shift |
|---|---|---|---|---|
| SSP1-2.6 | p05 | 5.81 | 3.94 | −1.87 |
| SSP1-2.6 | p50 | 6.31 | 4.89 | −1.43 |
| SSP1-2.6 | p95 | **46.29** | **6.12** | **−40.16** |
| SSP2-4.5 | p05 | 7.36 | 4.76 | −2.59 |
| SSP2-4.5 | p50 | **43.05** | **11.74** | **−31.32** |
| SSP2-4.5 | p95 | 73.21 | 59.06 | −14.15 |
| SSP5-8.5 | p05 | **54.14** | **21.98** | **−32.16** |
| SSP5-8.5 | p50 | 70.77 | 45.78 | −24.99 |
| SSP5-8.5 | p95 | 86.20 | 80.15 | −6.05 |

The large shift sits at a *different quantile in every scenario*, and it is
always the quantile nearest that scenario's tipping fraction. The Antarctic
distribution is **bimodal** — marine ice sheet tipped vs not tipped by 2100 —
and what the recalibration changed is **the probability of tipping by 2100**,
not how much ice is lost conditional on tipping:

- **SSP1-2.6**: Mengel had tipping above the 5% level (p95 = 46.3 cm); BRICK-F\*
  has none in the upper 5% (p95 = 6.1 cm).
- **SSP2-4.5**: Mengel tipped in **more** than half of draws (median on the
  tipped branch, 43.1 cm); BRICK-F\* tips in **less** than half (median 11.7 cm,
  sitting in the sparse gap, with p83 = 41.0 cm still on the tipped branch).
- **SSP5-8.5**: both tip in the majority; the conditional amounts are close
  (p95 86.2 vs 80.2).

**Reporting consequence.** "BRICK-F\* is 28 cm lower than BRICK-Mengel at
SSP2-4.5 2100" is a misleading sentence — it describes the 50th percentile
crossing a gap between two branches, and the same recalibration produces a
0.0 cm shift at SSP1-2.6 and −6.0 cm at the SSP5-8.5 p95. The defensible
statement is: *the recalibration lowered the probability of Antarctic
marine-ice-sheet tipping by 2100 in every scenario; conditional on tipping, the
contribution is similar.* Quote a distribution, not a median, wherever this
comparison appears.

**And it is substantially prior-driven.** The red team
(`notes/redteam_2026-08-11_brickf.md`) records that the eight non-converged AIS
marginals are all in the block that sets the tail, and that the SSP2-4.5
p83 = 41.0 cm is prior-driven rather than data-driven. The tipping fraction *is*
that quantity. So the largest single movement in the programme is a movement in
the least data-constrained part of the posterior, and must be presented with
that caveat rather than as a recalibration result the observations demanded.

---

## 4. Consequences

- **Quarantine.** Any deliverable built on the 78.02 cm (or "77.7 cm") vintage
  needs the standing treatment: move to `outputs/quarantine/YYYYMMDD_<tag>/`
  with a README naming the vintage, the files, and the canonical replacement —
  not deleted, not silently overwritten. Not done here; it needs the list of
  affected deliverables, which is a separate sweep.
- **This is a vintage difference, not a bug**, so the quarantine README should
  say so explicitly. Nothing here indicates either posterior was computed wrongly.
- **Pass 1 is untouched by this.** Greenland moves −0.15 cm between the
  vintages; the Greenland work neither caused nor is affected by the shift.
