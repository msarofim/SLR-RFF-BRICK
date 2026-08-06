# Mengel glacier recalibration — A0 results, new evidence, and the decision menu

**Session 2026-08-05 (continuation of `handoff_2026-08-05_mengel_recalib_and_component_review.md`).**
Everything here is computed/verified this session; scripts and outputs committed on
`brick-mengel-vnext`. Workstream A0 is DONE; A1-as-specified is **falsified by its own
citation test**; the structural picture changed enough that A5's spec needs your §5 calls
before any MCMC. Workstream B status at the end.

---

## 1. A0 — the offline profile CONFIRMED the handoff §1 diagnosis (all three predictions)

`python/a0_mengel_profile.py` → `outputs/a0_mengel_profile.csv`, `figures/a0_mengel_profile.png`.

- **P1 (algebraic):** holding the two historically-identified combinations at their posterior
  medians (slope@0 = 0.1330 m/K, committed = 0.1999 m) and sweeping `T_lia`, the (a, b) curve
  is single-valued and well-behaved, and crosses full-RGI inventory-consistency at
  **T_lia = −1.140 (a = 0.486, b = 0.464)** — the handoff predicted −1.1 to −1.2 / 0.479 / 0.476.
  No algebraic solution exists for T_lia ≤ −1.503.
- **P2 (profile likelihood):** the full-window GSIC likelihood **improves monotonically past the
  −1.00 floor** (the box, not the data, stops the sampler; ΔlogL ≈ 1.5 left on the table by the
  grid edge), with committed melt pinned at 0.196 m. **Removing the pre-1950 target years
  flattens the profile** (range 0.95 vs 12.80 logL units) and the committed-melt demand collapses
  to 0.102 m → the early-20th-century fit drives the railing, as predicted.
- **P3 (A4 quick test, `gic_sl0` freed):** an initial-disequilibrium state absorbs the demand
  entirely (optimum sl0 = −0.24 m, committed → 0.015 m, T_lia profile flat) **but drives (a, b)
  to the degenerate linear limit (a → ∞, b → 0)** — if sl0 is ever freed, the A2 inventory
  likelihood is mandatory for identifiability. (And see §3: sl0-alone fails GlacierMIP3.)

Handoff cross-checks: slope/committed medians reproduce exactly; the §1 railing percentages
reproduce at tolerance 0.01–0.02 (the handoff mixed tolerances; medians a 0.352 / b 0.891 /
T_lia −0.965 match exactly).

## 2. New evidence (three research sweeps, all with receipts)

### 2a. The LIA reconstruction does NOT support widening the T_lia bound (A1 falsified)

- PAGES 2k 2019 (Neukom, DOI 10.1038/s41561-019-0400-0; computed from the archived ensemble,
  April–March GMST, converted to 1850–1900 ref): LIA global mean **−0.03 to −0.14 °C** central
  (1450–1850 mean −0.05; coldest 51-yr window −0.11 [−0.44, −0.04] 95% CI). The extreme tail is
  ~−0.45 — the current prior MEAN.
- Glacier-region/seasonal amplification is real (~4–6×: Arctic annual coldest-31yr −0.62,
  European JJA −0.64, HMA JJA −0.60, all rel own 1850–1900) but even amplified minima are
  **−0.5 to −0.65**, not −1.1. The ~1 °C figures in the ELA literature are LIA-vs-PRESENT
  (they include industrial warming) — that's the trap.
- **Conclusion: −1.13 is indefensible as a temperature.** Widening the bound "because the fit
  wants it" would be exactly the fitting-the-prior-to-the-result move the handoff warned against.

### 2b. Mengel 2016 never had a T_lia — the parameter is our re-invention

Mengel's glacier equilibrium is **zero at preindustrial by construction** (E₀ = a(1−e^{bT})).
They handled post-LIA natural melt by **subtracting the natural fraction from the calibration
data** using Marzeion et al. 2014 (75 ± 35% of 1851–2010 glacier loss natural). That attribution
is directly contested: **Roe et al. 2021** (TC 15:1889) finds ~100% anthropogenic and attributes
Marzeion's result to initialization/response-time artifacts. MimiBRICK v2.0.0's own `gsic_teq`
precedent is −0.15 °C. So `gic_T_lia` is an **effective committed-melt knob**, not a
reconstruction-constrained temperature, and its defensible value depends on contested science.

### 2c. Inventory scope (A2): the calibration target and the 0.32 floor are scope-INCONSISTENT

Verified from Frederikse's production code + Hock et al. 2023 (JoG 69:204) reconciliation:

- **Frederikse 2020's glacier series EXCLUDES both peripheries** (RGI regions 5+19; region 5 is
  counted in his Greenland term). The scope-matched present inventory is **0.221 ± 0.057 m SLE**
  (Farinotti 2019 excl. 5+19; Millan 2022 matched-scope 0.223 ± 0.073 — the two agree once
  Millan's domain redefinition is undone).
- Full-RGI (incl. peripheries): **0.324 ± 0.084 m** — this is what the current `gic_a` floor
  (0.32) encodes.
- **Our own spliced GSIC target is internally scope-mixed:** the GlaMBIE tail (2000–2023)
  includes peripheries (19.5% of the 2000–2023 loss, computed from the per-region files in our
  local `glambie_data.zip`: r5 13.0% / −35 Gt/yr, r19 6.5% / −18 Gt/yr), while the Frederikse
  segment excludes them. Offset-matching absorbs the level; the 2019–2023 extension years carry
  the ~19% rate excess (~0.07 cm cumulative).
- **Component-ownership verification (second agent sweep, 2026-08-05 evening):**
  - *Region 5 is in the GIS target across the whole window:* Frederikse GrIS = Kjeldsen+Mouginot
    incl. peripheral GICs (his code deletes r5 from the glacier sum), and the GRACE-FO JPL mascon
    Greenland splice tail ALSO includes r5 — peripheral GICs are ~16% of the raw GRACE Greenland
    signal (NOAA Arctic Report Card 2025 scales by 0.84 to remove them, citing Colgan 2015;
    IMBIE-3: gravimetry "not sufficient to separate" the peripherals, GIC = 4.1% of GrIS
    gravimetry loss). → **putting region 5 in GSIC would double-count against the GIS component.**
  - *Region 19 in Frederikse — DOUBLE-CHECKED at code level (Marcus challenge 2026-08-05 eve,
    read directly from `compute_indiv_glaciers`/`compute_indiv_ice`):* the glacier column is
    regions 1–18-minus-5 BY CONSTRUCTION — the Zemp branch's loop selects region files
    `reg+1 ∈ 1..18` while Zemp 2019's region-19 file exists in the dataset (deliberate, not a
    data limitation; plausibly a quality call — Zemp 2019 Table 1 r19 = **−14 ± 108 Gt/yr (95% CI)**,
    the largest error bar of any region on the least-negative specific rate (−0.11 ± 0.87 m w.e./yr),
    contributing >50% of the global-total variance; Zemp themselves headline a "Total, excl. GRL and
    ANT" row = the exact cut Frederikse takes. NB r19 is the LARGEST region by volume, 46,801 km³ —
    poor evidence + small trend, not small mass); the Marzeion array is allocated 18 rows (and
    Marzeion 2012 states its model
    cannot simulate r19: "not covered by the CRU data sets"). For region 5 the reassignment is
    EXPLICIT: `Kjeldsen_P = Kjeldsen + marzeion_parkes_GRL` (ice sheet + r5 glaciers). **There is
    NO analogous r19 addition anywhere in the AIS column** (= IMBIE-2018 + Bamber-2018, both
    1992+, + the GRD/GRACE ensemble). r19 enters only incidentally: Bamber-2018's WAIS/EAIS
    numbers include PGIC by that paper's own statement (ERL 13:063008), and mascon-era gravimetry
    can't separate near-coast PGIC (~3.3%, IMBIE-3). Pre-1992, r19 melt is in NEITHER column —
    a real (small, ≲0.05 mm/yr modern, less earlier) hole in his budget, tolerable within his
    uncertainties; the Zenodo README flags only the Greenland exclusion ("Glaciers (excluding
    Greenland periphery)"), never the Antarctic one.
  - *Mengel's published a ≈ 0.47 is FULL-scope:* both sensitivity sources include regions 5+19
    (Marzeion 2012: "we include ice caps, and peripheral glaciers in Greenland and Antarctica",
    though its r19 is a global-mean-rate upscale with "no estimate of their volume"; Radić 2014
    models both directly). Mengel's 0.47 and GlacierMIP3's percentages are full-periphery
    quantities — comparing them to an excl-scope calibration mixes scope.
  - *BRICK-generation note:* BRICK 2.0's GSIC target (Dyurgerov & Meier 2005 "all systems",
    785,000 km²) was periphery-INCLUSIVE — the two BRICK generations calibrate GSIC to
    different physical objects.

### 2d. GlacierMIP3 (Zekollari 2025, Science, DOI 10.1126/science.adu4675) — the discriminating diagnostic

Committed loss of 2020 glacier mass at sustained warming: **+1.2 °C (present): 39% [15–55];
+1.5: 47% [20–64]; +2: 63% [43–76]; +3: 77% [60–85]**; sensitivity ≈ +85 mm SLE committed
between +1.5 and +3 °C. Checked against the candidate parameter sets (`a0` outputs + inline calc):

| candidate | committed@2K (% matched inv.) | sens 1.5→3K (mm) | verdict |
|---|---|---|---|
| current posterior (a .352, b .891, T_lia −.965) | 52% | **+29** | ladder 3× too FLAT (the spread bug) |
| Frederikse-scope V=.221 (a .380, b .737, T_lia −1.012) | 81% | +40 | still too saturated |
| excl-5-incl-19 V=.290 (a .452, b .529, T_lia −1.106) | **70%** | **+62** | **in family every rung; lands on Mengel's 0.47/0.52** |
| full-RGI V=.324 (a .486, b .464, T_lia −1.140) | 65% | +72 | in family BUT double-counts r5 vs GIS |
| sl0-free + physical T_lia (≈ −0.15, b ≈ 0.35) | ~19% (S_eq(1.2K) < S(2020)!) | — | FAILS: no committed melt left |

Two structural readings, and GlacierMIP3 adjudicates: the large equilibrium offset encodes real
physics (glaciers deeply out of equilibrium with the PRESENT climate — 39% already committed),
which a pure initial-condition fix (sl0) cannot represent. **The value ≈ −1.1 is right; the LIA
label is wrong.**

## 3. What A5 should look like — my recommendation, pending your calls

**Recommended package:** A2 inventory likelihood + T_lia reinterpreted (rename to
`gic_T_eq_offset`, "effective glacier-equilibrium temperature offset"), bound widened to
~[−2.0, −0.1] with a WEAK prior (e.g. N(−1.0, 0.5)) justified as an effective-disequilibrium
parameter — citing Mengel's natural-melt subtraction + Marzeion-vs-Roe as the reason it cannot
be pinned by PAGES 2k, and GlacierMIP3's 39%-committed-at-present as the physics it encodes.
The inventory term `gic_a − S_model(2020) ~ N(V, σ_V)` then closes the third direction with
data, and b becomes identified (A0 P1 shows the profile is well-conditioned).

### Open choices — need your direction before A5 (updated §5)

1. **Inventory scope (drives V) — now a THREE-way choice (§2c verification):**
   (a) *as-calibrated*: GSIC = regions 1–18 minus 5, V = 0.221 ± 0.057; GlaMBIE tail corrected
   to matching scope (global − r5 − r19, files on disk). Cheapest, internally consistent, but
   leaves region 19 orphaned (a real ~0.05 mm/yr budget gap vs the total target) and its
   solution (b = 0.74) still over-saturates vs GlacierMIP3.
   (b) *full-RGI*: V = 0.324 ± 0.084 — now the WEAKEST option: region 5 is demonstrably inside
   the GIS target (both segments), so a full-RGI GSIC double-counts ~3.4 cm of inventory and
   ~35 Gt/yr of modern loss against the Greenland component.
   (c) **RECOMMENDED: excl-5-incl-19, V ≈ 0.290 ± ~0.06** — region 5 stays with GIS (where its
   obs already live), region 19 moves into GSIC (nothing else models it; closes the budget gap).
   Its crossing (a 0.452, b 0.529, T_lia −1.106) lands on Mengel's published 0.47/0.52 and
   passes GlacierMIP3 every rung (70% @2K, +62 mm sens). Target work: GlaMBIE tail = global −
   r5 (files on disk); the Frederikse segment's missing r19 melt is small pre-2000 (Marzeion's
   r19 was an upscale; ~0.05 mm/yr today, less earlier) — accept as a known bias with a line in
   the provenance block, or add Marzeion-2015-style r19 back in if we want it exact.
2. **GlacierMIP3's role:** evaluation-only (your stated framing), or a soft prior on the derived
   committed@2K fraction? Using it as a prior edges toward A3-in-the-likelihood. My lean:
   evaluation-only; the inventory term already fixes identifiability, and §2d shows the
   full-RGI solution passes without being forced.
3. **sl0:** keep fixed at 0 (my lean — P3 + GlacierMIP3 show it's the wrong device alone, and
   freeing it alongside T_eq_offset re-opens a soft degeneracy), or free it with a tight prior
   as a robustness arm after the main chain.
4. **T_lia prior width** under the reinterpretation (N(−1.0, 0.5) proposed above — wide because
   the honest statement is "the data and inventory identify it; the label doesn't").
5. **Downstream (unchanged from handoff §4):** new posterior ⇒ quarantine extA108 outputs, re-run
   the CH4/CO2 pulse arms, measure the delta.

## 4. Workstream B status

- **B1 (hindcast, extA108)** — `python/b1_component_hindcast_stats.py` →
  `outputs/b1_component_hindcast_stats.csv`. AIS is now clean (bias ≈ 0, band coverage 0.85 —
  the old 1900-overshoot item is RESOLVED in extA108). GIS and GSIC both undershoot mid-century
  (1950–1993 biases −0.68 / −0.35 cm; in-window coverage 0.00 / 0.05). TE overshoots the early
  century (+0.54 cm). (Coverage uses the physical posterior band only, no AR(1) noise — ranks
  components, not a likelihood test.)
  **AIS pre-1992 asterisk (2026-08-06, verified from Frederikse's `compute_grd_ensemble.py`):**
  his pre-satellite AIS is NOT data — each ensemble member holds a CONSTANT rate drawn from
  N(0.05, 0.04) mm SLE/yr (≈18 ± 14 Gt/yr; code comment credits "Adhikari", presumably the
  polar-motion constraint — inference, Methods paywalled) until Bamber/IMBIE begin in 1992.
  Our target's smooth pre-1992 ramp (+0.052 mm/yr, bands fanning to ±0.64 cm @1900) is that
  prior integrated. So 1900–1992 constrains only DAIS's mean 20th-c drift vs 0.05±0.04 mm/yr;
  the "clean" early-century coverage is fit-to-prior, not fit-to-obs. Real AIS obs start 1992 —
  exactly the window where coverage drops to 0.45. No region-19 content in the prior either.
- **B2 (projections) — COMPLETE.** BRICK-AM per-component bands to 2300
  (`julia/project_ssps_components_2300.jl`); FACTS `global.coupling.{ssp126,ssp245,ssp585}.n200`
  all run and extracted (the native-FaIR climate step needed `fair==1.6.4` baked into the image —
  the neutered-pip fix from the pulse PoC had broken it). Tables:
  `outputs/b2_component_comparison.csv`; figures `figures/b2_component_comparison_{2100,2150}.png`.
  **Band-width caveat throughout:** BRICK-AM bands are parameter-only on mean forcing; FACTS/AR6
  bands include climate-ensemble spread. Medians comparable; widths not like-for-like.

## 5. B3 — ranked out-of-family list (attribution before any new physics)

Medians, cm, ~2005 baseline; scenario order SSP1-2.6 / 2-4.5 / 5-8.5.

1. **AIS — response is too binary; the largest cm-errors in both directions.**
   @2100: 4.9 / 13.9 / 46.2 vs AR6 11 / 11 / 12 (FACTS non-MICI modules 6–23 across scenarios).
   Scenario spread @2100: **41 cm vs −2…+9 (non-MICI FACTS) and 20 (DeConto MICI)** — 2× even MICI.
   Under SSP2-4.5 @2150 BRICK-AM (58.6) is 2× the HIGHEST FACTS module incl. MICI (DeConto 30.3);
   under SSP5-8.5 @2150 it sits between non-MICI (~37) and MICI (199). @2300: 199 (2-4.5) / 316
   (5-8.5) — at/above the AR6 assessed top. **Attribution: the fixed-rate disintegration ramp
   tips median draws already under SSP2-4.5 — earlier than DeConto's MICI — while the
   below-threshold response undershoots (SSP1-2.6 low everywhere).** Levers: temperature_threshold
   / amp posterior placement, λ ramp rate, and the quasi-linear below-threshold response.
2. **Glaciers — the confirmed Workstream-A bug, now quantified.** 6.4 / 6.8 / 7.2 @2100 vs AR6
   9 / 12 / 18; scenario spread **0.8 cm vs 6.5–8.5 (FACTS) and 9 (AR6)** — ~10× compressed AND
   low at every scenario. @2150 spread 1.6 vs 16.4. Fix = Workstream A (§3).
3. **GIS — low with ~4× too-weak scenario sensitivity.** @2100: 6.1 / 6.6 / 7.9 vs AR6 6 / 8 / 13
   (FittedISMIP 7.7 / 10.2 / 13.9); spread 1.8 vs 6.3–7.3. @2150 SSP5-8.5: 15.5 vs FittedISMIP
   27.3. Compounding the B1 mid-century hindcast undershoot. Worth a targeted look at the SIMPLE
   Greenland component's T-sensitivity (greenland_* posterior vs Wong's).
4. **TE — in family, mildly low at high forcing (−10…−15%: 46.5 vs tlm 53.3 @2150 SSP5-8.5);**
   spread fine (12.4 vs 14.8 @2100). The conspicuously narrow band is mostly the parameter-only
   caveat, plus the B1 early-century overshoot. Low priority.
5. **LWS — fine (2.6 vs 3.0–3.1 @2100)** and deliberately degenerate across draws (seeded
   central path; uncertainty not propagated). No action; document.
6. **Total — errors do NOT cancel: scenario sensitivity ~2× AR6.** @2100: 32.9 / 47.5 / 89.3 vs
   AR6 44 / 56 / 77 (spread 56 vs 33; FACTS workflows 25–51). BRICK-AM is *below* the whole FACTS
   workflow family at SSP1-2.6 and *above* all but MICI at SSP5-8.5 — AIS-driven at the top,
   glacier+GIS+AIS undershoot at the bottom.

**Figure/CSV pointers:** `figures/a0_mengel_profile.png`, `figures/b2_component_comparison_{2100,2150}.png`,
`outputs/b1_component_hindcast_stats.csv`, `outputs/ssps_components_2300_extA108.csv`,
`outputs/facts_components_n200.csv`, `outputs/b2_component_comparison.csv`.
