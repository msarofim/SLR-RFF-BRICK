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
| downstream (11 steps) | 10 OK; the doc tables first failed on a parser bug and now build (§8a). |

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
| cross-model spread (max/min) | 1.61× → **1.35×** | 1.76× → **1.475×** |

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

a. ✅ **RESOLVED 10-09 (Marcus: "compute the tables from a shared function"). ⛔ My first diagnosis was WRONG.**
   - The gate stopped at 1.02× its bound: MAGICC vvVL CO2 differed by 25 ulps. I called that summation-order noise.
   - **The real cause was pandas' DEFAULT float parser.** The duration CSV holds `0.025410746335901787` exactly, and
     `pd.read_csv` returns `0.0254107463359017`, 25 ulps away; `float_precision="round_trip"` reads it exactly.
     The two tables never differed. This is the trap the Ladrillo Table 5 comparator hit on 10-07.
   - **The shared function is the READER:** `pulse_stats.read_csv_exact`. Every read in `build_pulse_doc_tables.py`
     now goes through it.
   - **[SAME-STATISTIC] is back to EXACT** (bound 0): all 68 comparable cells are bit-identical, and 2 vvLN cells are
     skipped as NaN (not reportable).
   - **Mutation-tested:** one ulp on Ladrillo vvM CO2 `r_end_cm` FAILS, naming the cell.
   - The old √n-ulp bound had been introduced after earlier exact-bound failures ("1.1e-16", "24 ulps") that were
     very likely this same parser.
   - The doc tables and the assembled L27 section now BUILD. ⚠ The section's PROSE is stale (item d).

b. **vvML is now reportable on MAGICC at 2300.**
   - ⚠ **The scripts already disagree.**
     - `build_pulse_doc_tables.py` DERIVES its marker set from MAGICC's reportable flags (an edit of 10-09, d147217),
       so it moved to 6 markers by itself.
     - `diag_igmst_ordering_vv.py` and this note's §4 hold the typed 5.
   - Like-for-like numbers on the same set for all three models (per-marker / median):

     | set | MAGICC | Ladrillo | BRICK 2.0 | per-marker spread | gap closed (per-marker), Ladrillo / BRICK 2.0 |
     |---|---|---|---|---|---|
     | 5 (shipped set) | 0.640 / 0.667 | 0.893 / 0.780 | 0.943 / 0.902 | 1.475× | 74 % / 85 % |
     | 6 (+ vvML) | 0.637 / 0.647 | 0.893 / 0.836 | 0.936 / 0.830 | 1.469× | 85 % / 88 % |

   - (The "all-reportable" rows in §4 and in the CSV mix 7 markers for Ladrillo and BRICK 2.0 with 6 for MAGICC, so
     they are NOT like for like. Use this table.)

c. **[SHIPPED-EXCHANGE] 0 / 3** in `diag_igmst_ordering_vv.py`. This is expected: it checks the recomputation against
   the typed 09-07 constants, which this re-run supersedes. Update the constants (or relabel them "09-07") once you
   accept the new numbers.

d. **Where the L27 doc section goes, and its prose.**
   - The section ("Ladrillo Compared on a Pulse") was built 09-07 for `LadrilloUpdateDescription_L24.docx`.
   - Its tables are generated and live. Its PROSE template types ~15 numbers from the 09-07 run, and several moved.
   - A warning is now in the template's header comment, and it carries into the assembled file.
   - The .docx is yours and is not edited.
