# The van Vuuren pulse arc, re-run 2026-10-09: what moved

**Old** = the products quarantined in `20261009_vv_pulse_smith_harmonized`:
- Ladrillo **L24**;
- every model on the Smith-history + harmonized-tail vv pulse cubes;
- MAGICC's pulse scenarios from the 08-31 harmonized file.

**New** = the canonical products of this re-run:
- Ladrillo **L27 = "Ladrillo v1.2"**, with the FaIR arm record-conditioned (2 draws dropped per marker);
- the MAGICC-climate arm on the common draw set (2,000 draws; it had been 8,000 unpaired);
- every model on the 10-08 CMIP7 + published-Zenodo cubes.

⚠ **Ladrillo moved on TWO axes at once** (the cubes, and L24 → L27). BRICK 2.0, MAGICC-SLR and FACTS moved on the inputs
only. This note reports the moves; it does not attribute Ladrillo's between the two axes.

**Source**
- Script: `FaIRtoFrEDI/magicc_comparison/diag_pulse_rerun_diff_20261009.py`.
- Every number: `FaIRtoFrEDI/magicc_comparison/processed/pulse_rerun_diff_20261009.csv`.
- MC intervals and the iGMST ratio: `SLR-RFF-BRICK/outputs/log_vvp_downstream.txt`.

**Gates**
- [OLD-REPRODUCES-SHIPPED] 5 / 5: the old files give 0.913 / 0.637 / 1.024 and the 25 % / 16 % totals through the
  diff's own arithmetic.
- [NEW-IS-NOT-OLD] 7 / 7.
- [ROWCOUNT] 5 / 5.
- Self-test (old against old): [NEW-IS-NOT-OLD] fails 7 / 7, as it should.

## 0. Run status

| phase | result |
|---|---|
| MAGICC stage 4 (14), FACTS stage 5 (21), BRICK 2.0 stage 3 (14) | 0 failures. vvLN is NOT REPORTABLE at 2300 (99.5 % of baselines sub-pre-industrial), as before. **vvML is now reportable at 2300** (0 % sub-PI; it was 372/600 degraded). |
| Ladrillo FaIR arms (14) | 0 failures; 16 / 16 gate lines PASS in every log, [LEVEL-MATCH] included (vvH re-checked after the production overwrite). |
| magiccclim (28 Ladrillo + 28 BRICK 2.0) | 0 failures |
| downstream (11 steps) | 10 OK. ⛔ **The doc tables did NOT build** (§8a). |

## 1. Total response per Gt (paired mean ÷ nominal Gt, cm), range over the 7 markers

| model | gas | 2100 old → new | 2300 old → new | new/old, median over markers |
|---|---|---|---|---|
| Ladrillo | CO2 | 0.0124–0.0219 → 0.0122–0.0171 | 0.0253–0.0485 → 0.0268–0.0466 | 0.92 / 0.89 |
| Ladrillo | CH4 | 0.80–1.28 → 0.70–1.15 | 0.71–1.26 → 0.73–1.18 | 0.96 / 0.96 |
| BRICK 2.0 | CO2 | 0.0129–0.0190 → 0.0123–0.0223 | 0.0246–0.0491 → 0.0268–0.0604 | 1.13 / 1.19 |
| BRICK 2.0 | CH4 | 0.67–1.61 → 0.87–1.33 | 0.61–1.39 → 0.88–1.51 | 1.14 / 1.10 |
| MAGICC-SLR | CO2 | 0.0122–0.0164 → 0.0125–0.0173 | 0.0244–0.0868 → 0.0254–0.0877 | 0.97 / 0.98 |
| MAGICC-SLR | CH4 | 0.55–0.70 → 0.61–0.70 | 0.59–1.13 → 0.67–1.12 | 1.00 / 0.99 |
| FACTS wf1f–wf4 | both | | | 0.991–0.999 |

**BRICK 2.0 rises about 14 % on its inputs alone.** The rise is all Antarctic, and almost all of it is the threshold
premium:
- p_fired rises (vvML CO2 0.035 → 0.045);
- the smooth term, thermal expansion, Greenland and glaciers move ≤ 2 %;
- the median per Gt does not move.

**Every one of its 28 total and ais cells is within 2 se** (|z| ≤ 1.9, median z +0.66). So the rise is a consistent
upward tilt in a premium-dominated mean, consistent with a baseline nearer its DAIS threshold. That reading is
plausible, NOT established.

Thermal expansion moves by small amounts that ARE resolved:
- Ladrillo −2.7 % (24 / 28 cells beyond 2 se), on two axes;
- BRICK 2.0 −0.2 %.

**Shipped readings:**
- "@2100 the three agree": still true. The CO2 ranges overlap: MAGICC 0.0125–0.0173, Ladrillo 0.0122–0.0171,
  BRICK 2.0 0.0123–0.0223.
- "@2300 MAGICC runs hot on the warm markers": stronger. vvH is MAGICC 0.0877 vs Ladrillo 0.0305 / BRICK 2.0 0.0268,
  i.e. **2.9–3.3×** (was 2.4–3.1×). MAGICC's vvML 2300 cell (0.0360) is newly reportable.

## 2. Tail share of the total (top 5 % of members)

CO2 @2100, range over markers:

| model | old | new |
|---|---|---|
| Ladrillo | 0.415–0.673 | 0.440–0.602 |
| BRICK 2.0 | 0.595–0.733 | 0.572–0.771 |
| MAGICC-SLR | 0.117–0.157 | 0.114–0.163 |
| FACTS (4 workflows) | 0.074–0.097 | 0.074–0.097 |

**The classification survives:** the two DAIS-lineage models read THRESHOLD and the two independent ones read SMOOTH.
The MC reference bands are 0.542 and 0.106. Ruling 4 ("the premium is a one-lineage column; do not re-run 20×")
stands.

## 3. Duration (t50 / t90 of the 2030–2300 integral; median per arm)

| | old | new |
|---|---|---|
| CO2 t50, 5 arms | 2201–2210 | **2203–2210** |
| CH4 t50, 5 arms | 2175–2183 | **2175–2181** |
| t90 CO2 / CH4 (3 models) | 2283 / 2275–2277 | 2283–2284 / 2275–2276.5 |
| CH4 t90 by LEVEL: SLR models vs MAGICC | 2072–2074 vs **2137** | 2071–2079 vs **2119** |

"Within a decade across a climate model and two SLR models" **survives**. The level-versus-integral disagreement for
CH4 persists, narrower. CO2 still has not peaked by 2300 in any arm (end/peak 1.000).

## 4. CH4 : CO2e sea-level exchange rate (total @2300, GWP100, the 5 shipped headline markers)

| model | median, old → new | per-marker, old → new |
|---|---|---|
| MAGICC-SLR | 0.637 → **0.667** | 0.618 → **0.640** |
| Ladrillo | 0.913 → **0.780** ⚠ mixed markers (vvL / vvM) | 0.820 → **0.893** |
| BRICK 2.0 | 1.024 → **0.902** | 1.088 → **0.943** |
| cross-model spread (max/min) | 1.61× → **1.35×** | 1.76× → **1.47×** |

- **The ordering MAGICC < Ladrillo < BRICK 2.0 survives on both aggregations.**
- The spread narrows by about a sixth.
- ⚠ Ladrillo's per-species median moved −15 % while its per-marker rate moved +9 %. The median is still a mixed-marker
  statistic (memory `exchange_rate_median_mixes_markers`), so **quote per-marker.**
- **Share of the exchange-rate gap the climate swap closes:**
  - per-marker: Ladrillo 107 % → **74 %**, BRICK 2.0 71 % → **85 %**;
  - median: 99 % → 76 % and 38 % → 118 %.
  - On per-marker the two modules now agree more closely than before.

## 5. The H/VL scenario split (total @2300, CO2, paired mean)

| | old | new |
|---|---|---|
| Ladrillo (FaIR) | 1.01× | **0.74×** |
| BRICK 2.0 (FaIR) | 0.86× | **0.69×** |
| FACTS wf1f / wf2f | 0.52× / 0.67× | 0.52× / 0.67× |
| MAGICC-SLR (own climate) | 3.55× | **3.45×** |

**The three-direction split survives and widens**: MAGICC rises; the SLR models on FaIR are flat to falling.

## 6. The /magiccclim climate share (MC median [95 %], 200,000 draws)

**CO2 @2300:**

| component | Ladrillo old → new | BRICK 2.0 old → new |
|---|---|---|
| total | 25 % [12, 35] → **22 % [8, 41]** | 16 % [1, 32] → **11 % [−1, 25]** ⚠ now spans 0 |
| ais | 29 % [15, 43] → **18 % [5, 45]** | 24 % [4, 62] → **13 % [1, 34]** |
| gis | 10 % [5, 24] → **14 % [6, 33]** | 2 % [0, 5] → **2 % [0, 5]** |

- **MODULE-DOMINATED stands for both modules, and more strongly.**
- BRICK 2.0's total share no longer excludes zero (lower bound −1 %).
- Quote the intervals: the binary tag reads the same for both modules.

**CH4:**
- The total and ais shares still have no power (Ladrillo total 15 % [−110, 108]; BRICK 2.0 16 % [−359, 312]).
- What is resolved:
  - te OVERSHOOTS, 217 % / 216 % (was 230 % / 231 %);
  - glaciers −68 % / −40 % (was −54 % / −38 %);
  - BRICK 2.0 gis −36 % [−98, −16] (resolved negative, "Greenland opposed").
- Ladrillo's CH4 gis is now 67 % [50, 113], unresolved.

## 7. The pre-registered iGMST test

R(FaIR) / R(MAGICC) on the 5 headline markers:
- **1.3155 [1.2896, 1.3423]**, against 1.3241 [1.2980, 1.3509] shipped;
- all 7 markers: 1.3177 [1.2961, 1.3404].

Neither the prediction 1.433 nor the falsifier 1.0 is inside the interval: **same verdict**. The test was run as is,
against the historical prediction (handoff §5).

## 8. Open for Marcus

a. **The doc tables did not build.** `build_pulse_doc_tables.py` [SAME-STATISTIC] stops at **1.02×** its bound.
   - The worst cell is MAGICC vvVL CO2: the two tables differ by **25 ulps (3.4e-15 relative)**, against a bound of
     √600 ≈ 24.5 ulps.
   - All three cells above 0.5× the bound are MAGICC. The non-MAGICC cells differ by ≤ 1 ulp.
   - **This is summation-order noise.** A draw-set or denominator mismatch would show at ≥ 1e-4 relative; MAGICC's
     emissions quantum, for one, is 7.9e-5.
   - The bound is a one-sigma random-walk scale used as a hard maximum over 70 cells. The expected maximum of 70 such
     draws is about 2.5σ.
   - Per the standing rule, the gate is NOT edited. Options:
     - (i) re-derive the bound as a maximum over N cells, e.g. 4·√n ulps;
     - (ii) use the deterministic summation bound, n ulps;
     - (iii) compute both tables from one shared function so the identity is exact.
   - Recommendation: **(iii)**. It makes the gate an exact identity again rather than choosing a new tolerance.

b. **vvML is now reportable on MAGICC at 2300.**
   - The exchange rate and the iGMST test hold the shipped 5 headline markers (`HEADLINE_MARKERS`), so old and new are
     like for like.
   - Moving to 6 is a methodological choice: it changes the statistic, and iGMST would no longer be pre-registered.
   - Both are printed: all-reportable median / per-marker Ladrillo 0.813 / 0.897, MAGICC 0.647 / 0.637, BRICK 2.0
     0.902 / 0.967.

c. **[SHIPPED-EXCHANGE] 0 / 3** in `diag_igmst_ordering_vv.py`. This is expected: it checks the recomputation against
   the typed 09-07 constants, which this re-run supersedes. Update the constants (or relabel them "09-07") once you
   accept the new numbers.

d. **Where the L27 doc section goes.** Still open: `LadrilloUpdateDescription_L24.docx` is yours and is not edited.
