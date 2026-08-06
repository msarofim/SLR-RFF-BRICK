# Handoff 2026-08-06 — glacier calibration: structural decision (Nauels-ν and/or ETCW driver fix)

**Self-contained pickup:** this + `notes/memo_2026-08-05_mengel_a0_results_and_recalib_options.md`
(the running evidence document — §§1–3d) + memory `project_brick_mengel_vnext_recalib` +
`CLAUDE.md`. Branch **`brick-mengel-vnext`** (~45 commits ahead of origin, unpushed).
Everything below happened 2026-08-05/06; nothing is running.

---

## 1. Where the glacier workstream stands (one paragraph)

A0 confirmed the T_lia-floor diagnosis; the scope review put region 5 in GIS and region 19 in
GSIC (V = 0.290 ± 0.060, Marcus-approved); two calibration attempts then ran and were honestly
falsified: **extB1** (inventory term alone) escaped through unobserved pre-1900 melt (13 cm,
absurd); **extB2** (+ Leclercq 19th-c term N(0.020, 0.009)) satisfies the inventory AND passes
the GlacierMIP3 ladder but still violates the Leclercq term at 4σ (S(1900) = 57 mm), and a
constrained test proved the residual misfit is STRUCTURAL — the data demand a quiet-then-fast
onset (LIA max ~1850 → rapid 1900–1930 melt) that a fixed-τ relaxation toward a concave S_eq
cannot produce (b rails at its ceiling when forced). Two receipt-heavy literature sweeps then
established: (i) the decadal melt shape is NOT a GMST shape — the dominant missing driver is
the **ETCW** (Arctic +1.7 °C by 1930–40, 3–4× global, on ~84% of glacier mass; aerosols are
secondary/contested; the 1850 maximum is volcanically forced); (ii) **S_eq should STAY
concave** (GlacierMIP3 fits Mengel's own exponential to its committed ladder) — the delay
belongs in the TRANSIENT; the published nested candidate is **MAGICC's glacier equation**
(Nauels 2017 Eq. 3). Details + all citations: memo §§3b–3d.

## 2. The decision menu for the next session (Marcus's call)

Two non-exclusive structural options, plus the fallback:

**Option ν — Nauels transient (memo §3d recommendation).**
`dS/dt = κ · (S_eq(T) − S) · (T − T_eq(S))₊^ν`, with `S_eq = a(1−e^{−b(T−T_lia)})` kept, and
analytic inverse `T_eq(S) = T_lia − ln(1 − S/a)/b` (guard S → a). ν = 0 recovers current
Mengel exactly (κ = 1/τ) → nested, likelihood-ratio testable. ν > 1 delivers the delayed
onset from GMST alone. Published pedigree (MAGICC, unchanged through v7.5.3).
Design questions the implementer must resolve:
  - single-(κ, ν) or keep the 2-τ fast/slow split (2-τ + ν may be over-parameterized; the
    fast/slow split existed to fix the SAME onset problem ν addresses — consider replacing
    the 2-τ structure entirely with single-reservoir ν, which is the literal Nauels form);
  - positive-part clamp on the temperature-excess term (Nauels's clamping convention was NOT
    verified — flagged in the survey);
  - priors for κ, ν (Nauels's calibrated values are in their supplement, unread — worth one
    fetch before choosing).

**Option D — glacier-relevant DRIVER correction for the calibration era (Marcus, 2026-08-06).**
Adjust the historical temperature series the glacier component sees, to carry the
higher-than-normal Arctic amplification of the early 20th century that GMST misses:
  - Build `T_glac(t)` for 1850–2026 = glacier-area-weighted observed temperature (RGI-area
    weights over Berkeley Earth / HadCRUT5 regional series; ~84% of mass is Arctic/subpolar,
    so a 60–90°N + Alaska/subpolar composite is a reasonable first cut).
  - Drive ONLY the glacier component with it historically; for projections, splice to
    `amp_g · GMST` with amp_g ≈ 1.8 (GlacierMIP3's glacier-area warming ratio) or fitted —
    directly analogous to the A6 AIS amplification treatment (anchor-preserving splice, same
    pattern as the forcing splice conventions).
  - Rationale: this is the literature's actual fix (Marzeion 2012 Fig 18-vs-20 — realized
    regional forcing reproduces the shape; forced-response does not). It addresses the CAUSE;
    ν addresses the SYMPTOM with a shape parameter.
  - Costs: breaks the GMST-only architecture for one component (document the splice year and
    convention); needs a data-prep step (new `data/observations/t_glac_*.csv` + provenance);
    the ETCW is internal variability, so the projection driver will not contain such pulses —
    that is correct behavior, but state it.
  - NB Option D may make ν unnecessary — or both may be needed. Do NOT fit both blindly.

**Fallback (memo §3c option 1):** accept the extB2-style compromise with the documented 4σ
tension. Only if both structural routes fail.

## 3. Recommended sequencing (falsify-cheap-first, per A0 discipline)

**D0 — offline shootout BEFORE any component surgery or MCMC (~half day).** The Python
machinery already exists (`python/a0_mengel_profile.py` + the extB2 diagnostic snippets in
the session log / memo §3c): a forward integrator + GSIC AR(1) likelihood + A2/A2b terms.
Extend it to run a 2×2:
  {current Mengel transient, Nauels-ν transient} × {GMST driver, T_glac driver}
optimizing each cell's parameters against flow + stock + Leclercq, reporting per cell:
best joint logL, S(1900), inventory residual, GlacierMIP3 ladder, and the implied scenario
spread (S_eq saturation at +1.5/2/3 K). Whichever cell(s) pass all gates go to Julia
implementation + a 500k tuning run (**next tag: extB3**; extB1/extB2 are burned). Building
T_glac(t) is a prerequisite for two cells — budget a data-prep hour with provenance labels.

Success gates (pre-registered, same as extB2's plus the new one): inventory residual on
0.290 ± 0.060; S(1900) within ~10–30 mm; GlacierMIP3 ladder inside likely ranges WITHOUT
being forced; b off any bound; scenario-spread at 2100 in the FACTS/AR6 family
(`python/plot_b2_component_comparison.py` regenerates the comparison).

## 4. State inventory

- **Calibrator** `julia/calibrate_mcmc_ext.jl`: currently carries A2 inventory @2000
  (N(0.290, 0.060)) + A2b Leclercq (N(0.020, 0.009)) + widened gic bounds + weak offset prior
  N(−1.0, 0.5) on [−2.0, −0.1]. gic_T_lia is documented as an effective equilibrium offset
  (code symbol unchanged). Smoke-test pattern: `julia --project=julia_v2
  julia/calibrate_mcmc_ext.jl 50 2026 --tag=<tag>smoke` (delete the junk chain after).
- **Targets** `outputs/recalib_targets_ext.csv`: REGENERATED 2026-08-06 — GSIC tail is now
  GlaMBIE global − r5 (r19 kept); only gsic 2019–2023 changed (max 0.14 cm).
  `data/observations/raw/glambie_r5_greenland_periphery.csv` added.
- **Evidence chains** (retained, not canonical): `outputs/mcmc/chain_extB{1,2}_seed2026_n500000.csv`
  (untracked — ~400 MB each), `adapted_cov_extB{1,2}_seed2026.csv` (tracked),
  `tuning_extB{1,2}_seed2026.log`. extA108 remains the canonical posterior; NOTHING has been
  quarantined or re-run downstream — the CH4/CO2 pulse arms still sit on extA108 and wait for
  the accepted new posterior (handoff-2026-08-05 §4 downstream plan unchanged).
- **B1/B2 component review** (complete, on extA108): `outputs/b1_component_hindcast_stats.csv`;
  `outputs/{ssps_components_2300_extA108,facts_components_n200,b2_component_comparison}.csv`;
  `figures/b2_component_comparison_{2100,2150}.png`. FACTS ssp126/ssp585 n200 ran (fair==1.6.4
  had to be baked into the `facts` docker image — neutered-pip had broken the native climate
  step). Next-biggest component finding: AIS too binary (spread 41 cm @2100 = 2× MICI; tips
  under SSP2-4.5 earlier than DeConto) — its own future workstream.
- **Non-obvious session mechanics:** shell cwd resets between calls (use `git -C` / absolute
  paths); pre-1992 AIS target = Frederikse's N(0.05, 0.04) mm/yr constant-rate prior (Adhikari
  2018 polar motion), so early-century AIS "fit" is fit-to-prior; Frederikse Methods PDF is at
  `~/Documents/2026/ClaudeDocs/Papers/Frederikse.2020.s41586-020-2591-3.pdf`.
- **Memory updated:** `project_brick_mengel_vnext_recalib` (top block carries the 08-05/08-06
  arc; MEMORY.md index line updated).

## 5. Open questions at next pickup

1. Option ν vs Option D vs both (D0 shootout answers this empirically — run it first).
2. If Option D: exact T_glac construction (region weights, dataset, splice year, amp_g fixed
   1.8 vs fitted) — methodological choices, flag before running.
3. τ-structure under ν (drop the 2-τ split?).
4. Production gating unchanged: 4 × 2M over-dispersed, R̂ on SLR@2100/2150 + glacier-spread
   deliverable, `ess(maxlag=size(arr,1))`; REBUILD overdispersed starts from the accepted
   tuning posterior (extA108-era starts sit in the old railed region).
5. After acceptance: quarantine extA108 per convention, regenerate levels/components, re-run
   CH4/CO2 pulse arms and MEASURE the delta (glaciers ~1–1.5% of the pulse marginal — the
   headline should be robust, but produce the number).
