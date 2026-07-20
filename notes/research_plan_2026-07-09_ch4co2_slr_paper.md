# Research Plan — Relative sea-level-rise impact of CH₄ vs CO₂ emission pulses

**A reduced-complexity climate + sea-level analysis, doubling as the BRICK-FM introduction paper**

Author: Marcus C. Sarofim (NYU Marron Institute). Date: 2026-07-09.
Supersedes/expands: `handoff_2026-07-09_ch4co2_slr_paper_plan.md` (same directory).
Division of labor (standing convention): **Marcus drafts all main text**; Claude produces
figures, tables, methods sections, captions, reference compilation, verified numbers, and the
structural outline in this document.

> **Status of all numbers below.** Every headline SLR value quoted here is a **placeholder** from
> the completed studies on the *pre-BRICK-FM* Mengel posterior (FaIR 2.2.4 (calib1.4.5) × RFF-SP, archived
> `brick-mengel` branch) and the Phase-1 SSP2-4.5 MAGICC run. The paper's production numbers are
> regenerated on the **BRICK-FM v-next** posterior after recalibration (§5, §11). Numbers are used
> here to size the argument and design the figures, not as final results.

>MCS NOTE: The FaIR model version is NOT 1.4.5, that's the calibration version. 
>MCS NOTE: Do we publish BRICK-FM as a separate JOSS paper to complement the pulse paper?

---

## 1. Thesis and contributions

**Core scientific question:** *How much sea-level rise does a tonne of CH₄ cause relative to a tonne
of CO₂, over multi-century horizons, and how much does that answer depend on the sea-level emulator?*

Four contributions, in decreasing order of novelty:

1. **Gas-resolved pulse→SLR marginals with a modern constrained emulator.** CH₄-vs-CO₂ pulse
   sea-level marginals computed with a fair-calibrate-constrained FaIR posterior driving a
   component-resolving semi-empirical SLR model, on a probabilistic emissions ensemble. The only
   per-gas pulse-SLR prior art (Sterner, Johansson & Azar 2014; Zickfeld et al. 2017) is
   thermosteric-only, deterministic-background, and pre-modern-calibration. **This is the paper's
   primary novelty claim** — the physical, per-actual-tonne, component-resolved framing, not
   "first CH₄ pulse through an SLR model" (SC-CH₄ IAMs already do the latter monetized).

2. **Level and marginal SLR signals are governed by different parts of the same response — and
   disagree across emulators.** BRICK-FM's Antarctic contribution runs ~3.8× **higher** than MAGICC
   at scenario *level* (43.1 vs 11.2 cm AIS @2100, SSP2-4.5) yet MAGICC's AIS pulse *marginal*
   T-sensitivity is ~5.8× **higher** (6.9×10⁻³ vs 1.2×10⁻³ cm/GtCO₂ @2100). **Frame this as a
   mechanism decomposition, not a paradoxical "inversion"** (a reviewer would rightly call a bare
   inversion "expected behavior of a threshold model"): both emulators are *convex* in d(AIS)/dT
   (no ordering flip in the sensitivity itself); the level gap is the time-integral of BRICK's AIS
   tipping under sustained large forcing, while the marginal is the local slope of a small 2030 pulse
   that never approaches the threshold. The defensible, still-novel claim is that a single emulator's
   **scenario alarm** and its **marginal (SC-GHG-relevant) signal** are set by different operating
   points on one convex curve, and that cross-model agreement on *marginals* — the quantity that sets
   the social cost of GHGs — is **operating-point-dependent** and, to our knowledge, unexamined in the
   SLR literature. **Disambiguating test to run (§6):** compute the BRICK marginal at a high baseline
   forcing (SSP5-8.5, or a large cumulative pulse just below the DAIS break); if it climbs toward
   MAGICC's as the baseline nears the threshold, that proves operating-point (not a true cross-model
   inversion). Policy framing that survives either result: **the scariest scenario projection is not
   the highest social cost.**

3. **BRICK-FM as a documented, reusable model.** A FaIR-driven, Mengel-glacier, recalibrated fork
   of MimiBRICK with a posterior that is **scenario-independent in forcing pathway** — calibrated to
   the FaIR ensemble-*mean* historical GMST+OHC rather than a single SSP, hence transferable to any
   FaIR-driven ensemble (EPA SC-GHG, RFF-SP, GIVE), with per-config conditioning applied at
   projection (or via optional importance weighting, §5 item 5). (This is transferability, not
   full uncertainty propagation into the calibration.) No published recalibrated descendant of Wong
   2017 / MimiBRICK 2022 exists.

4. **A CH₄→CO₂ oxidation-harmonisation protocol** for cross-model pulse comparison: MAGICC
   oxidizes fossil CH₄ to CO₂ internally (~76% of its CH₄ GMST marginal @2100 is induced CO₂); FaIR
   v2.2.4 has **no explicit CH₄→CO₂ oxidation term** (matrix commented out) — a +300 Tg CH₄ test
   moves CO₂ only ~5% of the full-oxidation amount, all of it climate-carbon feedback already
   captured by GWP for both bases (`test_ch4_pulse_co2_response.py`). The biogenic/fossil 4-arm
   harmonisation makes the comparison apples-to-apples and is itself a transferable methods
   contribution.

**Headline finding (short-lived-forcer signature, robust across all three BRICK lineages):** per
tonne CO₂-equivalent (AR6 GWP-100 = 27), CH₄ drives **~2.2–2.3× more SLR than CO₂ at 2100, ~1.4× at
2150, and ~0.6–0.7× by 2300** — a clean crossover as the front-loaded CH₄ forcing is "cashed in"
early while CO₂'s long-memory integral keeps accruing. The paper's recommended **primary framing is
per-actual-tonne (no-GWP)** — a basis-*independent* physical result and the real contribution. The
CO₂e crossover is the policy-facing secondary framing but its **crossover horizon is a metric-choice
artifact**: GWP-20 (=79.7) pushes CH₄ below CO₂ even at 2100, GWP-100 defers the crossover to
~2150–2200. Report the crossover as an explicit function of GWP basis (20/100, biogenic/fossil) — a
first-class result, not a footnote — which pre-empts the "artifact of your metric choice" objection
on Sarofim's own metrics home turf.

>MCS NOTE: Use 100 and 150 years from the emission point as the key variable, NOT the years 2100 and 2150
>(this is different from much of my other work, but consistent with the GWP-100 framing)

---

## 2. Literature positioning and novelty

**Direct ancestors (must cite and differentiate):**
- **Sterner, Johansson & Azar 2014** (Climatic Change) — the closest methodological ancestor:
  defines Global Sea-level-rise Potential (GSP / iGSP), pulse-based CH₄-vs-CO₂ SLR metrics, using
  an upwelling-diffusion EBM + a semi-empirical total-SLR model. **Position the paper as updating
  GSP with modern constrained calibration, component-resolved ice/glacier physics, and
  emissions-ensemble uncertainty.**
- **Zickfeld, Solomon & Gilford 2017** (PNAS) — centuries of *thermosteric* SLR from short-lived
  GHGs; EMIC-based, no ice sheets/glaciers, no ensemble. Defines exactly what BRICK-FM adds.

**Nearest threats (check before claiming novelty in print):**
- **Nauels et al. 2025** (Nat. Clim. Change) — MAGICC-based multi-century SLR *commitments* from
  cumulative 21st-century emissions. Same "delayed SLR from near-term emissions" message and the
  same MAGICC SLR module used here for cross-validation. **Scenario/commitment-level, not per-gas.
  Read the methods to confirm they do not separate CH₄ vs CO₂ before claiming that gap in print.**
- **Couplet et al. 2025, SURFER v3.0** (GMD) — a fast CO₂+CH₄→SLR emulator with ice-sheet tipping,
  built for exactly this class of long-horizon pulse question. The competing experiment is "one
  script away" for that group. Cite and monitor.
- **Wong 2026 arXiv:2604.13446** — Tony Wong's own preprint using the *identical* FaIR→BRICK
  pipeline for marginal SLR of U.S. vehicle emissions (no CH₄/CO₂ split). This paper's contribution
  is delineated as **per-gas + cross-emulator + probabilistic**, vs Wong's single-application,
  single-pipeline study. But this is a **strategic dependency, not a citation courtesy** (§9.10, §12
  step 1): Wong is simultaneously (a) the BRICK author whose model this forks, (b) author of the
  nearest-pipeline preprint, (c) the collaborator reviewing PR1/PR2 whose timeline gates the v-next
  recalibration, and (d) a Rennert-2022/RFF-SP co-author. The gas split is the smallest possible
  increment from his published pipeline — he could get there first. Resolve scope/co-authorship/
  sequencing with him **as a pre-submission gate**, not a deferred courtesy.
- **Errickson et al. 2021 / GIVE (Rennert et al. 2022)** — CH₄ pulses through calibrated SCMs, but
  monetized via IAM damage functions, no physical per-tonne SLR reporting. Differentiate on the
  physical-SLR framing.
  
>MCS NOTE: I will definitley be collaborating with Wong and Errickson on this project,
>and maybe Nauels as well. 

**Novelty verdict (from a July-2026 web sweep — not a systematic Scopus/WoS search):** we found **no
published instance** of gas-specific CH₄-vs-CO₂ pulse SLR marginals with a modern calibrated emulator
on a probabilistic ensemble, nor of a level-vs-marginal cross-model SLR comparison. (Phrase it "we
found no published instance," not "entirely unstudied," until a systematic search backs the stronger
claim.) The novelty rests on an *exact combination* (constrained-posterior emulator + component-
resolving SLR + probabilistic ensemble + per-gas), so **differentiate by demonstrated consequence,
not by a feature list the ancestors lack.** Concretely: show that at least one added ingredient
changes the metric — e.g., component resolution reveals the CH₄-TE-led vs CO₂-AIS-led split that a
thermosteric-only GSP/Zickfeld calculation cannot see, or the crossover horizon shifts relative to a
thermosteric-only estimate. "They didn't have modern calibration" is weak unless the calibration
demonstrably moves the per-gas answer. **Residual literature diligence before submission** (§11 risk
R7): (a) read paywalled methods of Nauels 2025 and Darnell 2025 to confirm no per-gas attribution;
(b) sweep AGU/EGU 2025–26 abstracts for in-progress competitors; (c) confirm the SURFER group has not
posted a pulse-SLR result.

---

## 3. Scenario backbone decision — RFF-SP vs SSP *(flagged; recommendation, awaiting Marcus)*

This is the methodological decision the request called out. Per the "methodological choices are
explicit" discipline I do **not** silently resolve it; below is the evidence and a recommendation.

**Recommendation: use both, with clearly separated roles — RFF-SP as the primary (headline +
uncertainty band) backbone; SSP2-4.5/1-2.6/5-8.5 as the validation/comparability layer.**

Rationale:

- **RFF-SP earns "primary" because it is the pulse-relevant, defensible-band choice.** It is the
  SC-GHG canonical socioeconomic/emissions ensemble (Rennert 2022), internally consistent with every
  other project headline (IPI SC-CO₂, LHS-10k SLR bands, H-S decomposition), and Marcus already
  designated it the publication basis (2026-06-18). Both required pieces exist: the FaIR→BRICK
  reference arm is **complete** on RFF-SP (3-BRICK study), and the MAGICC RFF-SP machinery is
  **built and smoke-tested** (commit ed1910d, 2k-draw stride-5 design locked). A pulse *is* a
  marginal-damage question; RFF-SP is its natural home.

- **SSP earns "validation layer" because it is the only path to published benchmarks and to the
  curvature figure.** AR6 / SROCC / Nauels 2025 / FACTS SLR numbers are all SSP-framed — the MAGICC
  AR6 drawnset reproduces AR6 on SSP2-4.5 (GMST@2100 2.71 °C; SLR 53 cm vs AR6 ~56 cm), giving an
  external sanity check no RFF-SP run can provide. The **AIS d(SLR)/dT curvature figure requires
  discrete forcing levels** (SSP1-2.6/2-4.5/5-8.5) that a probabilistic cloud cannot separate. And
  the FACTS leg (§7) is SSP-native in its scoped configuration.

- **The CO₂ pulse marginal is nearly scenario-insensitive:** SSP2-4.5 FaIR→BRICK-Mengel CO₂ @2100 =
  5.08×10⁻³ vs RFF-SP 4.69×10⁻³ cm/GtCO₂ (~8%). For **CO₂**, the backbone changes the uncertainty
  band and framing, not the median — reporting both is nearly free and the ~8% agreement is itself a
  reportable robustness result. **This is a CO₂ cross-check and does NOT transfer to CH₄** (see the
  caveat below).
  
>MCS NOTE: Yes, the RFF-SPs should be the primary result, but the SSPs provide a nice clean way to
>look at how the pulse response changes with scenario. 

**CH₄-specific blocker to clear before trusting the RFF-SP CH₄ baseline (not just a caveat):** RFF-SP
**under-projects CH₄ growth** — realized CH₄ (2021–24) rose ~3× faster than the RFF median and sits
at/above RFF p95, while RFF SO₂ splices ~30% hot at 2021 and RFF central runs +0.14 °C (2050) /
+0.23 °C (2100) warmer than EPA's SSP2-4.5. Because CH₄ forcing is concentration-dependent (log-ish),
the operating point matters *more* for the CH₄ marginal than for the per-tonne CO₂ case, and the ~8%
CO₂ number above is **not** evidence the CH₄ marginal is scenario-robust. **Required test (§6, §9.6):**
compute the CH₄ pulse-SLR marginal on (i) RFF median and (ii) a high-CH₄/obs-anchored-CH₄ backbone,
and report the delta. If <~10%, the dismissal is *earned* and the paper should cite *that* number,
not the CO₂ one; if larger, the CH₄ headline needs the corrected baseline or an explicit sensitivity
band. Include the obs-vs-RFF ensemble figure (`fair_outputs/..._baselined2015-2019.png`) as SI either
way.

**Comparison-architecture consequence (settle before the FACTS install, §7):** the backbones
*fragment* across legs — FaIR→BRICK and MAGICC production sit on RFF-SP, but FACTS is SSP-native and
the AIS-curvature figure *requires* discrete SSP forcing levels. So a single-backbone 3-way pulse
comparison is not deliverable. Resolve by assigning backbones to jobs: **SSP2-4.5 = the shared
cross-model panel backbone** (all legs incl. FACTS + curvature co-exist; AR6 benchmarks exist);
**RFF-SP = the CH₄-vs-CO₂ gas headline + uncertainty band** (2 legs: FaIR→BRICK and MAGICC). Do not
let the abstract promise a shared-backbone 3-way pulse comparison until FACTS feasibility (R8)
resolves.

*Residual sub-decision for Marcus:* whether SSP2-4.5 results appear in the **main text** (for AR6
comparability + curvature + the cross-model panel) or SI. Recommendation: curvature + AR6-anchor +
cross-model panel in main text, remaining SSP detail in SI.

---

## 4. What is already in hand (asset inventory)

| Asset | Backbone | State | Location |
|---|---|---|---|
| FaIR→BRICK 3-lineage CO₂+CH₄ pulse marginals | RFF-SP (LHS-10k) | **Complete** | `outputs/pulse3brick_v145/` (archived `brick-mengel`) |
| CH₄-as-CO₂e headline table + figure | RFF-SP | **Complete** | `headline_table_co2eq.md`, `pulse3brick_marginals.png` |
| Fossil-CH₄ superposition sensitivity | RFF-SP | **Complete** | `headline_table_fossil_ch4.md` |
| MAGICC-native vs FaIR→BRICK CO₂+CH₄ pulses | SSP2-4.5 | **Complete (Phase 1)** | `magicc_comparison/processed/`, `figures/` |
| AIS d(SLR)/dT curvature (3 SSPs) | SSP1-2.6/2-4.5/5-8.5 | **Complete** | `curvature_ais_dT.csv`, `ais_curvature_*.png` |
| Oxidation harmonisation (biogenic/fossil 4-arm) | SSP2-4.5 | **Complete** | `pulse_ch4_ssp245_both_table.md` |
| MAGICC RFF-SP pulse builder + runner | RFF-SP | **Smoke-tested (N=5)**; production pending | `build_pulse_scenarios_rff.py`, `302c_...py` |
| BRICK-FM fork (PR2) + shipped Mengel posterior | — | **Ready for Tony's review** | `MimiBRICK.jl` fork, branch `brick-fm` @ 30948fa |
| BRICK-FM docs (changes/rationale, obs-discrepancies, calibration guide) | — | **Complete** — near-direct methods text | `MimiBRICK.jl/docs/` |
| FACTS install | SSP-native | **Not installed**; spec ready | `handoff_2026-06-21_facts_install_scoping.md` |

**Placeholder headline numbers** (pre-BRICK-FM-v-next; regenerate before publication):

- CO₂ total SLR marginal (cm/GtCO₂, weighted median, RFF-SP): pre-#93 1.15×10⁻² @2100 / 3.10×10⁻²
  @2300; BRICK 2.0 5.36×10⁻³ / 1.07×10⁻²; **Mengel 4.69×10⁻³ / 1.15×10⁻²**.
- CH₄ biogenic total SLR marginal (cm/Tg, Mengel): 2.80×10⁻⁴ @2100 / 2.12×10⁻⁴ @2300.
- MAGICC-native vs FaIR→BRICK CO₂ (SSP2-4.5): 0.0154 vs 0.00508 cm/GtCO₂ @2100 (3.0×), 4.5× @2300;
  GMST marginal differs only 1.16× → **~86% of the SLR gap is the emulator, ~14% the forcing.**
- CH₄ temporal-shape disagreement (SSP2-4.5, cm/Tg): MAGICC grows monotonically (6.08×10⁻⁴ @2100 →
  8.50×10⁻⁴ @2300); BRICK peaks ~2100 then recedes (3.11×10⁻⁴ → 2.46×10⁻⁴).

---

## 5. BRICK-FM v-next — the pre-paper model update

BRICK-FM's seven departures from upstream MimiBRICK (Wong 2022): (1) Mengel-2016 two-timescale
glacier emulator; (2) Dangendorf-2024 GMSL target; (3) Frederikse-2020 closed-budget component
targets; (4) post-2018 obs extension (GRACE-FO / GlaMBIE / NOAA); (5) FaIR v2.2-mean GMST+OHC
calibration forcing (replaces SNEASY) → **scenario-independent, FaIR-transferable posterior**;
(6) deterministic `lws=:central` (0.3 mm/yr); (7) freed `ais_ocean_temperature₀`. Calibration = 28
free params (18 physical + 10 AR(1) noise), RAM-MCMC on Torch.

**v-next changes, priority-ordered, with the gate items first:**

1. **[GATE — decide before recalibrating] Reconcile the IMBIE/Dyurgerov point terms.** The fork's
   `calibrate_mcmc_mengel.jl` includes both Gaussian point constraints *unconditionally*, but the
   ext refit that produced the *shipped* posterior **dropped both**. Re-running the fork script
   as-is will **not** reproduce the shipped posterior. Also `IMBIE_SIG = 0.156` is ~2.5× too tight
   vs Otosaka-2023 (2720±1390 Gt → σ≈0.38 cm). **Decision required: drop (match ext) vs
   keep-with-corrected-σ.** (Open decision §9.3.)

2. **Smith-2024 observed-emissions splice for the calibration forcing.** Re-run the FaIR v2.2 mean
   with Smith-2024 observed historical emissions spliced to scenario at 2021 (same splice already
   standard in the v1.4.5 pipeline), regenerate `data/observations/fair_mean_{gmst,ohc}.csv`,
   re-run the MCMC. Closes the ~0.1 °C-cool near-history gap and the GIS undershoot. No model-code
   change. **Highest value-per-effort.** *Before quoting the GIS undershoot in a table/figure,
   reconcile the source inconsistency:* the obs doc labels it "at 1900: ~0.53 vs 2.1 cm (Frederikse)
   / 1.45 (IGCC)" while the rationale doc attributes the same numbers to 2024 as "~0.5–1 cm," and a
   1900 label sits oddly against the 1995–2005 reference period. Pin the year and reference period
   first (this feeds Figure 1 / the obs-discrepancy table).

3. **Free AIS geometry parameters** (slope, bed height, flow₀, precip₀, runoff height₀, c, μ),
   currently fixed at prior medoids, with an identifiability strategy (informative FM-posterior-
   centered priors / Bedmap regularization / reparameterization to identifiable combinations).
   Highest science value for the AIS-led pulse tail. (Open decision §9.2.)

4. **Residual TE overshoot** (+0.51 cm vs NOAA steric @2025; te_α 0.164 vs Wong 0.057, ~3×). Extend
   the OHC calibration target pre-1971 via a Zanna-2019 splice (pattern exists,
   `ohc_spliced_zanna_igcc.csv`). May partly self-resolve with item 2.

5. **FaIR-config-aware calibration.** Current calibration conditions on the FaIR *mean*; the
   841-config spread enters only at projection. Ascending-cost options: **(a) Tony-style post-run
   importance weighting** — reweight each posterior draw by its likelihood under each FaIR config's
   historical trajectory (N_post × 841 BRICK runs ≈ hours; likely near-uniform → cheap to test
   first); (b) per-config MCMCs on a stratified ~50–100-config subset, IW back to 841; (c) full 841
   per-config MCMCs (~8.4k core-hours, SLURM array). Key simplification: FaIR has no feedback from
   BRICK, so all 841 historical trajectories are pre-computed **once**; per-config cost is
   BRICK-only. **Recommend (a) as a scoping test; escalate only if weights are far from uniform.**
   (Open decision §9.1.)

6. **Small items:** GSIC 1900 undershoot (~4 cm; 3rd timescale / LIA budget — structural, likely
   defer to future work); MICI (highest effort, promotable if a reviewer demands upper-tail AIS);
   LWS uncertainty propagation (low priority). DOECLIM `heat_interior` plumbing bug already fixed in
   the fork — flag upstream to Tony (also in raddleverse BRICK 2.0; harmless to standard entry
   points). Production posterior = full MCMC subsample, **never MAP**.

**Methods material to extract for the paper (near-ready):** the three `docs/brick_fm_*.md` files
already read as change+rationale prose, an obs-discrepancy table, data-source tables, and a 28-param
calibration-setup table. **Missing for methods:** the *achieved* convergence diagnostics (R̂/ESS) and
the actual chain count/iterations for the shipped posterior — the docs give only targets (R̂<1.05,
ESS>400) and recommended run sizes; memory records 27/28 R̂<1.05 with `rho_ais` the straggler. Pull
the real numbers from the shipped chains for the methods section (risk R6).

---

## 6. Pulse-experiment design

**Model chain:** FaIR v2.2.x (fair-calibrate constrained posterior) → BRICK-FM (component-resolved
semi-empirical SLR). Paired baseline/pulse per ensemble member.

**Experiment matrix (recommended):**

| Axis | Recommendation | Notes / open items |
|---|---|---|
| Gases | CO₂ + CH₄ | Fossil-CH₄ as harmonised arm (§4, §9.5) |
| Pulse year | **2030** primary | SC-GHG convention; multidecade (2020/40/50/60/80) = extension, likely SI or future work (§9.4) |
| CO₂ pulse size | FaIR/BRICK **0.01 GtCO₂** (float64); MAGICC-RFF size **UNRESOLVED** | Report per GtCO₂. Phase-1 established MAGICC needs **≥0.1 GtCO₂** (float32 floor), but the shipped RFF builder injects **0.01**; not re-decided in writing. **Reconcile label to code constant before production (risk R3).** |
| CH₄ pulse size | **1 Tg CH₄** both arms | Float32-clean in MAGICC (front-loaded forcing); 0.01 Tg is corrupted |
| Backbone | RFF-SP primary (2k stride-5); SSP2-4.5 + SSP1-2.6/5-8.5 for validation/curvature | §3 |
| Horizons | 2100 / 2150 / 2300 | SLR is a long-memory integral — long horizon is where the story lives |
| Scenario-sensitivity tests | CH₄ marginal on RFF-median vs high/obs-CH₄ backbone (§3); BRICK CO₂ marginal at high baseline forcing (SSP5-8.5 / near-DAIS-break) | The first tests whether the RFF CH₄ under-projection matters; the second disambiguates the mechanism-decomposition claim (contribution 2) from a true cross-model inversion |
| Metric | Total + per-component (AIS/GSIC/GIS/TE/LWS), reported as **median** | Mean is AIS-tipping-contaminated (Mengel CO₂ mean ≫ median) |
| CH₄ framing | **Per-actual-tonne (no-GWP) primary**; CO₂e (GWP-100=27 biogenic / 29.8 fossil) secondary | GWP basis is an open reporting choice (§9.5); GWP-20=79.7 would push CH₄ below CO₂ even @2100 |

**Pulse discipline (mandatory carry-forward checklist):**
- Paired seeds mandatory — FaIR 2.2.4 (calib1.4.5) stochastic noise is ~200× the pulse signal.
- CO₂ input unit is **GtCO₂**, not GtC (recurring bug class).
- Full 5-test sanity battery per experiment: zero-pulse bit-identical, sign-flip (−1.000), ×2
  linearity (2.000), first-principles magnitude, paired-seed check (`climate-modeling` skill).
- float64 end-to-end through BRICK (float32 destroys small marginals).
- Report **medians** for CO₂ (pulse-induced AIS tipping contaminates the mean).
- LWS cancels in paired marginals — but **name the setting per arm**: the completed 3-BRICK study and
  MAGICC comparison locked `lws=:seeded` (LWS_SEED=2026); BRICK-FM v-next default is `lws=:central`.
  Both cancel in pairs; verify empirically per the checklist, don't assume.
- Weighting: Wong importance weights (ESS/N = 0.5) on pre-#93 and BRICK-2.0 arms; **Mengel/FM arm
  equal-weighted** (its posterior is already MCMC-calibrated to Dangendorf — Wong would double-count).
- BRICK DAIS breaks at |pulse| ≥ 100 GtCO₂; CH₄ 50–100 Tg shows genuine sub-linear forcing curvature.

**CH₄→CO₂ oxidation harmonisation:** biogenic (no oxidation, GWP-100 = 27) and fossil (oxidation,
GWP-100 = 29.8) arms reported side by side. FaIR fossil = co-emit **2.743 t CO₂/t CH₄** as a time
series following the CH₄ decay (half by ~2041), matching MAGICC's oxidation timing; MAGICC forced via
`MAGICC_CH4_FOSSFRAC`. (Methods should spell out the per-unit bases so the superposition constant
`0.27432·co2_marg` reconciles transparently with 2.7432 g CO₂/g CH₄ — the factor is per-Tg CH₄ vs
per-GtCO₂, different bases, not a 100× error.) **There is a documented doc-vs-lock contradiction on
the FaIR→BRICK fossil arm, resolved by arm (§9.5):** the MAGICC arm is superposition (locked in commit
ed1910d); the 2026-06-21 handoff instead called for a **real time-distributed FaIR fossil re-run**
(port the `--fossil` decay-companion to `run_fair_rff.py`) for the FaIR→BRICK reference arm. Decide
per arm — do not default the reference arm to superposition silently.

---

## 7. Cross-model comparison plan

**Comparison architecture (2×2 + reference):** MAGICC-native SLR module (Nauels 2017) vs
MAGICC→BRICK-FM hybrid (Track-C-style emulator-vs-forcing decomposition) vs FaIR→BRICK-FM reference,
optionally + FACTS (structural ice-sheet-uncertainty fan). The same FaIR temperature ensemble drives
BRICK-FM and (in principle) FACTS → apples-to-apples GMSL.

**MAGICC (Phase 2, RFF-SP) — production runs remaining:**
- Design **locked** (Marcus 2026-06-24): 2,000-draw stride-5 subsample (rff_idx 1,6,…,9996); 1:1 LHS
  member pairing (MAGICC member = (draw−1) % 600); fossil CH₄ by post-hoc superposition.
- **Before submission:** run the Torch SLURM array (CO₂ + CH₄ biogenic/fossil + sanity variants).
  **Gate items first:** (R2) confirm the RFF CSV CO₂ unit — the builder maps as Mt CO₂/yr and
  applies /1000 to Gt C; a memory note calls it GtCO₂/yr; a mismatch is a **1000× emissions error**.
  (R3) re-confirm the MAGICC CO₂ pulse size vs the float32 floor (0.01 injected vs ≥0.1 established).
  (§9) Decide whether the FaIR→BRICK RFF reference arm reuses the existing biogenic Mengel marginal
  or is re-run for exact member pairing.
- Deliverable: MAGICC vs BRICK-FM pulse marginals (CO₂ + CH₄) on a shared RFF-SP backbone — the
  level-vs-marginal inversion made quantitative on the publication ensemble.

**FACTS 2.0 — install now (mid-July window open):**
- **Decide the cross-model-panel backbone BEFORE the install** (§3): designate SSP2-4.5 as the shared
  panel backbone so FACTS, curvature, and AR6 benchmarks co-exist; keep RFF-SP for the gas headline.
  This makes §3's split load-bearing for the comparison architecture, not just framing.
- Docker-only on the M4 Mac (RADICAL is Linux-only); `global_only` data subset (12 files, ~modules
  map to BRICK components); expected native arm64 build; ~1–2 hrs hands-on + dummy experiment; Docker
  not yet installed (`brew install --cask docker`). Re-verify all pins against the live repo.
- **Load-bearing feasibility question to resolve during install:** whether the FACTS module chain
  supports **deterministic paired pulse/baseline seeding**, and whether a `config.yml` can ingest an
  **external FaIR temperature ensemble** (vs its bundled `fair_temperature` module). This gates
  whether FACTS is a *pulse* panel or a *scenario-level benchmark* only.
- **Scenario capability caveat:** FACTS is SSP-indexed in its scoped config; no evidence it accepts
  RFF-SP draws. If only SSP inputs work, the FACTS leg sits on an SSP backbone (consistent with §3's
  validation layer) — do **not** promise an RFF-SP FACTS pulse panel until this is resolved.
- **Fallback role:** scenario-level GMSL benchmark (@2100 SSP2-4.5: MAGICC-native 53 cm vs
  FaIR→BRICK-Mengel 78 cm), as the third leg of the level comparison, adding the structural
  ice-sheet fan (FittedISMIP / bamber19 / deconto21 / larmip) that BRICK's single emulator lacks.

---

## 8. Figure and table set (Claude-side deliverables)

**Figures (candidate set):**
1. **BRICK-FM hindcast vs obs, per component** (AIS/GSIC/GIS/TE/total vs Frederikse/Dangendorf +
   post-2018 obs) — the model-validation figure (`postpred_ext_*` pattern).
2. **Calibration-lineage pulse response** (pre-#93 → BRICK 2.0 → FM): "why the model version matters
   ~2.5×" — pre-#93 CO₂→SLR is 2.3–3× post-#93, driven by the #93 GIS posterior pathology.
3. **Cross-gas per-actual-tonne SLR, CH₄ vs CO₂** (no-GWP) — the paper centerpiece; total + component
   stack, 2100/2150/2300.
4. **CH₄-as-CO₂e crossover** (GWP-100 = 27): CH₄/CO₂ SLR ratio 2.2× → 1.4× → 0.7× across horizons —
   the short-lived-forcer signature (`pulse3brick_marginals.png` exists).
5. **MAGICC vs BRICK-FM: scenario level vs pulse marginal** (mechanism decomposition, not "inversion"
   — §1 contribution 2): AIS-focused, level vs marginal on the same convex response, with the
   ~14%-forcing/~86%-emulator attribution and the high-baseline-forcing disambiguation result.
6. **AIS d(SLR)/dT curvature** (both emulators convex; SSP1-2.6/2-4.5/5-8.5) — `curvature_ais_dT.csv`.
7. **CH₄ temporal-shape disagreement** (MAGICC monotonic vs BRICK peak-and-recede).
8. **FACTS benchmark panel** — *feasibility pending* (§7); scenario-level if pulses infeasible.
9. **SI:** RFF-SP-vs-obs realism (CH₄ ≥ p95 caveat); fossil-CH₄ premium sensitivity; oxidation
   harmonisation schematic.

**Tables:**
- Pulse marginals by gas × horizon × model (total + q05/q50/q95) — source-of-truth
  `marginals_summary.csv` (108 rows) + MAGICC processed CSVs.
- BRICK-FM free parameters + priors vs Wong et al. (28-param calibration-setup table).
- Convergence diagnostics (R̂/ESS per parameter) — **needs achieved values (R6)**.
- Cross-gas CO₂e ratios by horizon and GWP basis (biogenic/fossil).
- Data-sources / obs-products table (calibration targets by component and period).

---

## 9. Open methodological decisions *(flag — do NOT silently resolve)*

1. **FaIR-config calibration approach:** sequential (status quo) vs importance-weighting (a) vs
   per-config (b/c). *Recommend (a) as scoping test.*
2. **AIS geometry freeing strategy:** which params, which identifiability mechanism.
3. **IMBIE/Dyurgerov point terms:** drop vs keep-with-corrected-σ — **must decide before recalibration.**
4. **Pulse year(s):** 2030 only (recommended) vs multidecade.
5. **CH₄ framing:** per-actual-tonne (recommended primary) vs GWP-equivalent; biogenic vs fossil arms;
   fossil FaIR→BRICK by superposition vs real time-distributed run (**doc-vs-lock split by arm — §6**);
   GWP basis (20 vs 100, reported as a first-class function — §1).
6. **Scenario backbone:** §3 — recommend RFF-SP primary + SSP validation layer, with the cross-model
   panel on SSP2-4.5. **Includes the required CH₄-specific scenario-sensitivity test before the RFF-SP
   CH₄ baseline is trusted.**
7. **BRICK lineage members in the paper:** FM primary; BRICK 2.0 comparator; pre-#93 as cautionary
   appendix (drives figure 2) — decide, as it sets what must be regenerated/quarantined.
8. **PF-O3 CH₄ amplification** (GTP-100 +48%, memory `project_pf_o3_substack_figures`): in scope or
   cited as companion work? *Recommend: cite as companion; keep this paper's CH₄ forcing standard.*
9. **Journal target + single-paper vs two-paper split** (§10), and whether the BRICK-FM description
   is main text or appendix. **Sub-gate: commit to a public `MimiBRICK-FM` + Zenodo DOI timeline** —
   GMD requires public code/data at submission, and even ESD reviewers may demand code availability,
   so the "GMD in reserve" fallback is only real if the repo can go public on demand (gated on Tony's
   timeline).
10. **[NEW — reference-arm pairing gate]** Does the FaIR→BRICK RFF reference arm **reuse** the existing
    biogenic Mengel marginal (4.69×10⁻³ cm/GtCO₂) or **re-run** for exact 1:1 member pairing with the
    2k stride-5 MAGICC design? A re-run couples it to the v-next posterior (step 3) → it is **not**
    independent of the MAGICC Phase-2 production track. Decide before §12 step 4.
11. **[NEW — Wong coordination gate]** Confirm with Tony Wong, in writing and as a recorded decision
    (not an open item): (a) the CH₄-vs-CO₂ gas split is out of scope for his line of work, or agree
    co-authorship/sequencing; (b) who publishes the FaIR→BRICK marginal-SLR pipeline description first;
    (c) a date for his BRICK-FM review, since v-next (§5) is downstream of it.

---

## 10. Journal strategy

The paper is structurally two things — a **model-description** half (BRICK-FM) and a **cross-gas
pulse-science** half. No single venue is a perfect fit; three viable strategies:

- **Single paper — Earth System Dynamics (recommended default).** Best single-paper home for the
  combined product: ESD covers reduced-complexity models + emission metrics (Marcus's own Sarofim &
  Giordano 2018 GWP paper is ESD), accommodates substantial model documentation inside a science
  paper, and the no-GWP per-tonne framing is squarely a metrics contribution. Concern: modest
  visibility; reviewers may still nudge the model part toward GMD.
- **Single paper — Earth's Future.** Good for the policy-facing science half (probabilistic SLR,
  multi-model comparison, decision-relevance); BRICK-FM lives in SI. Concern: not a model-description
  venue.
- **Two-paper split.** GMD "BRICK-FM v1.0" model-description + evaluation (requires public
  code/data with DOI at submission — the private `MimiBRICK-FM` repo must go public; model must be
  the focus), plus an ESD / Earth's Future / ERL science paper carrying the pulse comparison.
  Cleanest fit to each venue's norms but doubles the writing load and needs the code public.

**Recommendation:** default to a **single ESD paper** with a generous methods/appendix for BRICK-FM;
hold the **GMD split** in reserve if reviewers demand the model be documented separately. **Caveat
(R11):** the GMD fallback is only genuinely available if `MimiBRICK-FM` can go public with a Zenodo
DOI on demand — which is gated on Tony's timeline. **Commit to a public-code + Zenodo release date
regardless of venue** (ESD reviewers may themselves demand code availability), so a "split it to GMD"
request is answered with a code-release commitment, not a blocked resubmission. **ERL and npj CAS
require the two-paper split** (length / finding-led format) — pursue only if the model is documented
elsewhere first.

---

## 11. Risks and blockers

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **IMBIE/Dyurgerov point-term mismatch** — fork script won't reproduce shipped posterior | Recalibration blocked / wrong posterior | Decide §9.3 **before** any v-next MCMC; document choice |
| R2 | **RFF CSV CO₂ unit** — builder assumes Mt CO₂/yr (÷1000 to Gt C); memory says GtCO₂/yr | Silent **1000× emissions error** in MAGICC-RFF | Verify actual CSV unit before production run |
| R3 | **MAGICC float32 floor vs 0.01 GtCO₂ pulse** on RFF | ~1% low or corrupted CO₂ marginal | Re-confirm pulse size; Phase 1 used ≥0.1 GtCO₂ |
| R4 | **All headline numbers change on v-next posterior** | Every table/figure regenerates | Quarantine current outputs (never delete) → regenerate to canonical paths |
| R5 | **Pulse drivers live only on archived `brick-mengel` + Torch /scratch**, never extracted to the fork/`MimiBRICK-FM` | Reproducibility / provenance gap | Extract drivers to `MimiBRICK-FM`; pull 90k outputs off /scratch before retention purge |
| R6 | **Achieved convergence undocumented** — need R̂/ESS *per parameter*, *which* parameter failed (memory: `rho_ais` at 27/28), AND actual chains × iterations used for the shipped subsample (docs give only ≥4×500k targets) | Methods section incomplete | Pull all three from shipped chains |
| R7 | **Novelty check incomplete** — paywalled Nauels/Darnell methods unread; no AGU/EGU abstract sweep; differentiate by demonstrated consequence not feature list | Overclaim / incrementality rejection | Complete §2 diligence before submission |
| R8 | **FACTS pulse feasibility unknown** (paired seeding + external-FaIR ingestion + RFF-SP capability) | May not deliver a pulse panel; forces cross-model panel onto SSP | Resolve during install; fall back to scenario benchmark |
| R9 | **Mengel-posterior provenance thicket** — completed study used `parameters_subsample_brick_mengel_ext.csv`; fork ships a different `..._mengel.csv`; v-next is a third | Wrong-posterior figures | Pin exactly which posterior each figure uses; regenerate on one canonical v-next |
| R10 | **RFF sampling count ambiguous** — design docs say 490 RFF × 841 cfg; Phase-2 strides rff_idx 1–9996; memory attributes a 4× effect to a 3000→10000 inventory change | Wrong ensemble/band description in methods | Confirm how many *distinct* RFF draws `outputs/lhs10ks_brick_metadata.csv` samples before describing the band |
| R11 | **Public-code timeline** — GMD (and possibly ESD) require public code+DOI at submission; `MimiBRICK-FM` is private on Tony's timeline | "GMD in reserve" fallback not actually available | Commit to a Zenodo release date regardless of venue (§9.9) |

---

## 12. Work plan and sequencing

Dependency-ordered; ⟂ marks parallelizable tracks.

1. **Collaborator + coordination gate** — Tony/Vivek review of PR1 (raddleverse #111) + PR2 (fork
   `brick-fm`); fold feedback into v-next scope. **Close the Wong coordination gate (§9.11) as a
   recorded decision:** gas-split scope, pipeline-description priority, and a BRICK-FM review date
   (v-next is downstream of it). Commit to a `MimiBRICK-FM` + Zenodo public-release date (§9.9, R11).
2. **Resolve gate decisions** — §9.1–9.3 (gate recalibration); §3 backbone **+ the SSP2-4.5
   cross-model-panel / RFF-SP gas-headline architecture split**; §9.7 lineage set; §9.10 reference-arm
   reuse-vs-re-run (couples the MAGICC track to step 3 if re-run).
3. **Build BRICK-FM v-next:** IMBIE/Dyurgerov reconciliation → Smith-2024 forcing splice →
   freed-AIS prior design → MCMC on Torch (≥4 seeds × ≥500k) → convergence + postpred vs obs (record
   achieved R̂/ESS + chains×iter, R6).
4. **In parallel** ⟂ (*note the step-3 coupling if the reference arm is re-run, §9.10*):
   - **MAGICC Phase 2 production** — **clear R2 (RFF CO₂ unit) and R3 (pulse size vs float32 floor)
     first**, then Torch SLURM array (2k draws × gases × variants).
   - **FACTS 2.0 install** — Docker → build → dummy → **pulse-feasibility test** (resolve R8) →
     external-FaIR-ensemble coupling test. Determines whether FACTS is a pulse panel or an SSP
     scenario-level benchmark (§7).
   - **FaIR-config IW scoping test** (§9.1 option a) — cheap; informs whether escalation is needed.
   - **Scenario-sensitivity tests** (§3, §6): CH₄ marginal RFF-median vs high-CH₄; BRICK CO₂ marginal
     at high baseline forcing (disambiguates contribution 2).
5. **Regenerate all pulse marginals** on the v-next posterior (quarantine current outputs per the
   standard discipline); rebuild marginals/tables/figures to canonical paths.
6. **Figures, tables, methods** (Claude) per §8; **Marcus drafts main text**; compile references
   (§13); complete §2 novelty diligence (R7).
7. **Provenance freeze:** extract drivers to `MimiBRICK-FM`, pull Torch /scratch outputs (R5), make
   the repo public + mint Zenodo DOI (R11) per the step-1 commitment.

---

## 13. References (compiled; verify starred items before submission)

Ancestors & core method:
- Sterner, E., Johansson, D. J. A., & Azar, C. (2014). Emission metrics and sea level rise.
  *Climatic Change* 127(2), 335–351. doi:10.1007/s10584-014-1258-1
- Zickfeld, K., Solomon, S., & Gilford, D. M. (2017). Centuries of thermal sea-level rise due to
  anthropogenic emissions of short-lived greenhouse gases. *PNAS* 114(4), 657–662.
  doi:10.1073/pnas.1612066114
- Mengel, M., et al. (2016). Future sea level rise constrained by observations and long-term
  commitment. *PNAS* 113(10), 2597–2602. doi:10.1073/pnas.1500515113

Model provenance chain:
- Wong, T. E., et al. (2017). BRICK v0.2 … *Geosci. Model Dev.* 10(7), 2741–2760.
  doi:10.5194/gmd-10-2741-2017
- Wong, T. E., Srikrishnan, V., et al. (2022). MimiBRICK.jl … *J. Open Source Softw.* 7(76), 4556.
  doi:10.21105/joss.04556  *(copy full author list from JOSS PDF)
- Nauels, A., et al. (2017). … the MAGICC sea level model v2.0. *Geosci. Model Dev.* 10(6),
  2495–2524. doi:10.5194/gmd-10-2495-2017
- Kopp, R. E., et al. (2023). The Framework for Assessing Changes To Sea-level (FACTS) v1.0 …
  *Geosci. Model Dev.* 16(24), 7461–7489. doi:10.5194/gmd-16-7461-2023

Climate model / calibration / ensemble:
- Smith, C., et al. (2024). fair-calibrate v1.4.1 … *Geosci. Model Dev.* 17(23), 8569–8592.
  doi:10.5194/gmd-17-8569-2024  *(copy full author list)
- Leach, N. J., et al. (2021). FaIRv2.0.0 … *Geosci. Model Dev.* 14(5), 3007–3036.
  doi:10.5194/gmd-14-3007-2021
- Rennert, K., et al. (2022). Comprehensive evidence implies a higher social cost of CO₂. *Nature*
  610(7933), 687–692. doi:10.1038/s41586-022-05224-9

Nearest neighbors / threats:
- Nauels, A., et al. (2025). Multi-century global and regional sea-level rise commitments … *Nat.
  Clim. Change* 15, 1198–1204. doi:10.1038/s41558-025-02452-5
- Couplet, V., Martínez Montero, M., & Crucifix, M. (2025). SURFER v3.0 … *Geosci. Model Dev.* 18,
  3081–3129. doi:10.5194/gmd-18-3081-2025
- Errickson, F. C., et al. (2021). Equity is more important for the social cost of methane than
  climate uncertainty. *Nature* 592, 564–570.* doi:10.1038/s41586-021-03386-6  *(confirm pages)
- Wong, T. E. (2026). Modeling the Sea-Level Change from U.S. Vehicle Emissions. arXiv:2604.13446.
- *Darnell et al. (2025). The interplay of future emissions and geophysical uncertainties for
  projections of sea-level rise. *Nat. Clim. Change* 15, ~1205. doi:10.1038/s41558-025-02457-0
  *(author list + pages unconfirmed)

Marcus's own:
- Sarofim, M. C., & Giordano, M. R. (2018). … GWP … *Earth Syst. Dyn.* 9, 1013. (venue precedent)

---

*End of research plan. Companion memory: `project_ch4co2_slr_paper_plan`. Cross-repo discipline:
BRICK/SLR handoffs live in `SLR-RFF-BRICK/notes/`.*
