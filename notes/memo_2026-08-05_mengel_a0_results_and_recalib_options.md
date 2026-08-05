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
  includes peripheries (~19% of the modern loss rate; GlaMBIE 2025: −273 ± 16 Gt/yr total,
  periphery −53 ± 11), while the Frederikse segment excludes them.

### 2d. GlacierMIP3 (Zekollari 2025, Science, DOI 10.1126/science.adu4675) — the discriminating diagnostic

Committed loss of 2020 glacier mass at sustained warming: **+1.2 °C (present): 39% [15–55];
+1.5: 47% [20–64]; +2: 63% [43–76]; +3: 77% [60–85]**; sensitivity ≈ +85 mm SLE committed
between +1.5 and +3 °C. Checked against the candidate parameter sets (`a0` outputs + inline calc):

| candidate | committed@2K (% matched inv.) | sens 1.5→3K (mm) | verdict |
|---|---|---|---|
| current posterior (a .352, b .891, T_lia −.965) | 52% | **+29** | ladder 3× too FLAT (the spread bug) |
| scope-matched crossing (a .380, b .737, T_lia −1.012) | 81% | +40 | still too saturated |
| full-RGI crossing (a .486, b .464, T_lia −1.140) | **65%** | **+72** | **in family on every rung** |
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

1. **Inventory scope (drives V):** (a) *Frederikse-consistent*: V = 0.221 ± 0.057 AND correct
   the GlaMBIE tail of the GSIC target down by the periphery share (~19% of post-2000 rate);
   (b) *full-RGI*: V = 0.324 ± 0.084 and accept (or correct) the Frederikse segment's missing
   peripheries. **(b) is what makes the solution land on Mengel's published (a, b) and pass
   GlacierMIP3 as-is, but (a) is the internally-consistent cheap option.** My lean: (b) done
   properly — add a periphery-glacier estimate to the Frederikse segment — but that's real work;
   (b)-lazy (scope-mixed, as now) is defensible given σ_V ≈ 0.08 swamps the mix.
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
- **B2 (projections)** — BRICK-AM per-component bands to 2300 done
  (`julia/project_ssps_components_2300.jl` → `outputs/ssps_components_2300_extA108.csv`);
  FACTS ssp126/ssp585 n200 runs in progress (the native-FaIR climate step needed `fair==1.6.4`
  baked into the image — fixed); comparison machinery ready
  (`python/b2_component_comparison.py`, `facts/extract_facts_components.py`).
  Early signals vs FACTS-ssp245 + AR6 Table 9.9 (all medians, cm, ~2005 baseline):
  - **Glaciers:** BRICK-AM 6.4/6.8/7.2 @2100 (SSP1-2.6/2-4.5/5-8.5) vs AR6 9/12/18 — low
    everywhere, scenario spread 0.8 cm vs AR6's 9 cm. The Workstream-A bug, quantified.
  - **AIS:** in family @2100 under SSP2-4.5 (13.9 vs AR6 11), then runs away: @2150 58.6 vs
    FACTS 11–30; @2300 199 (SSP2-4.5) / 316 (SSP5-8.5) — at/above the AR6 assessed-range top.
    SSP1-2.6 @2100 is LOW (4.9 vs AR6 11).
  - **GIS:** low, esp. at high forcing @2100 (7.9 vs AR6 13).
  - **TE:** levels in family (16.8 vs AR6 20 @2100 SSP2-4.5); band conspicuously narrow.
  - **Totals:** 32.9 / 47.5 / 89.3 @2100 vs AR6 44 / 56 / 77 — low / ok / high, i.e. BRICK-AM's
    scenario sensitivity of the TOTAL is too strong (AIS-driven) while its glacier sensitivity
    is too weak.
  - **Band-width caveat:** BRICK-AM bands are parameter-only on mean forcing; FACTS/AR6 bands
    include climate-ensemble spread. Medians comparable; widths not like-for-like.

**Figure/CSV pointers:** `figures/a0_mengel_profile.png`, `outputs/b1_component_hindcast_stats.csv`,
`outputs/ssps_components_2300_extA108.csv`, `outputs/facts_components_n200.csv` (ssp245 so far).
