# Handoff — 7-panel SLR figure for Lisa Rennels (2026-05-30)

**Requestor:** Lisa Rennels (UC Berkeley / GIVE / Mimi-MimiFAIR-BRICK lineage;
authored the AR6 emissions file — see FaIRtoFrEDI/CLAUDE.md). 
**Owner:** Marcus C. Sarofim.
**Self-contained for a cold start:** read this + project `CLAUDE.md` + the
`mimibrick-quirks`, `fair-quirks`, and `climate-modeling` skills.

---

## The deliverable (Marcus's spec, verbatim intent)

A **7-panel figure**:

- **LEFT panel (1):** SLR projection under **SSP2-4.5**, plotted **relative to
  2005**, with **90% and 75% probability bounds** (i.e. 5–95% and 12.5–87.5%
  bands) + median.
- **RIGHT cluster (6 panels):** sea-level-rise **impulse response to a
  1e-4 GtC CO₂ pulse in 2020**, decomposed into the six series:
  **TE, GSIC, GIS, AIS, landwater storage (LWS), and Total GMSLR.**
  (Impulse response = pulse-minus-baseline SLR per the pulse, one panel each.)

Layout suggestion: left panel ~⅓ width full height; right six as a 2×3 or 3×2
grid. Confirm orientation with Marcus before finalizing.

---

## ⚠️ THREE methodology decisions to confirm with Marcus BEFORE building

These are genuine forks, not defaults — flag and await direction
(project CLAUDE.md: "Methodological choices are explicit").

1. **SSP2-4.5 vs RFF-SP for the LEFT panel.** Our entire production pipeline
   (poster Panel B `slr_band.py`, LHS-10k ensemble) is **RFF-SP**, NOT SSP2-4.5.
   Lisa asked for SSP2-4.5. We DO have SSP245 infrastructure (see "Assets"
   below: `ssp245_validation_cube.npz` = GMST/OHC for 841 cfgs under SSP245,
   plus per-component BRICK validation CSVs `cross_ssp245_validation_{te,gsic,
   gis,ais,gmsl}.csv`). **But that validation cube has only 1 emissions draw ×
   841 cfgs** — so the only uncertainty axis present is the FaIR-config (climate)
   + BRICK-posterior spread, NOT emissions. For a single deterministic SSP2-4.5
   emissions scenario that is exactly right (SSP scenarios are deterministic;
   the band = climate + ice-sheet uncertainty). CONFIRM: is the band meant to be
   climate+BRICK uncertainty around the fixed SSP2-4.5 pathway? (Almost
   certainly yes — that's the standard AR6-style SSP band.)

2. **Pulse size / regime.** Lisa specified **1e-4 GtC** (= 1e-4 × 44/12
   = 3.667e-4 GtCO₂). That is FAR below our existing small-pulse arm (0.01 GtC).
   Going this small is GOOD for a clean linear impulse-response (well below the
   AIS-tipping contamination that corrupts the 1-GtC mean — see
   `mimibrick-quirks` §11 and memory `project_pulse_size_findings`), BUT:
   - At 1e-4 GtC the per-component SLR response at 2100 is ~1e-4 × the
     per-GtC sensitivity ≈ **sub-micron to micron SLR** — likely BELOW BRICK's
     numeric/float resolution per cell. **This will need either (a) a larger
     pulse run divided down (exploit linearity — we've verified 1/0.1/0.01 GtC
     convergence in `pulse_convergence.py`), or (b) careful float64 + a
     baseline-subtraction that stays above noise.** Recommend: run the pulse at
     a size that's numerically safe (e.g. 0.01 GtC, already built), verify
     linearity, then REPORT scaled to 1e-4 GtC. Confirm with Marcus that
     "impulse response to 1e-4 GtC" can be presented as (response at 0.01 GtC)
     × (1e-4 / 0.01). This is the per-CLAUDE.md "implausible result = bug"
     guard — do NOT run 1e-4 GtC directly and trust sub-resolution differences.
   - **Pulse YEAR is 2020** (Lisa's spec), NOT our usual 2030. The pulse drivers
     default to 2030; the multidecade driver
     `FaIRtoFrEDI/compute_pulse_temps_multidecade_v145.py` already covers
     2020/2030/2040/2050/2060/2080 — USE THE 2020 ARM.

3. **Specie units.** Lisa said **GtC** (carbon mass). FaIR v1.4.5 CO2 FFI
   `input_unit` is **GtCO2**, not GtC (memory
   `project_fair_v145_co2ffi_is_gtco2`; this exact unit error bit several
   scripts and is literally the "Lisa Rennels unit error" reproduced in
   `FaIRtoFrEDI/fair_wrong_units_test.py`). **1e-4 GtC = 3.667e-4 GtCO₂.**
   Be explicit in the driver and the figure caption which unit the pulse is in.
   Given the requestor, get this unambiguously right and state it on the figure.

---

## Assets that already exist (don't rebuild from scratch)

| Asset | Path | What it gives you |
|---|---|---|
| SSP245 GMST/OHC cube | `outputs/ssp245_validation_cube.npz` | keys `years`(1850-2100), `gmst_traj_rff`(1×841×251), `ohc_traj_rff` — the FaIR side of SSP2-4.5 for all 841 v1.4.x cfgs (1 emissions draw). Built by `python/lhs_climate_pilot.py` / `run_fair_rff.py` (grep "ssp245"). |
| SSP245 per-component BRICK | `outputs/cross_ssp245_validation_{te,gsic,gis,ais,gmsl}.csv` | per-(rff,cfg,post) yearly component SLR 1850-2100 under SSP245. **Verify these are current (post-PR#93 posterior) before use** — they may predate the PR#93 BRICK install (memory `project_brick_post_pr93_posterior_installed`). If stale, regenerate. |
| BRICK driver w/ component output | `julia/run_mimibrick_flatcube.jl` | `--save-component-trajs true` writes per-year `te_<y>, ais_<y>, gis_<y>, gsic_<y>, lws_<y>` + total `slr_<y>`. This is THE tool for the 6-component decomposition. Total GMSLR = sum of the 5 (incl. LWS — memory `project_brick_five_components`). |
| Pulse driver (2020 arm) | `FaIRtoFrEDI/compute_pulse_temps_multidecade_v145.py` | produces baseline + pulse GMST/OHC at PULSE_YEAR ∈ {2020,…}; feed both arms' GMST+OHC into BRICK for paired SLR. |
| Small-pulse summary pattern | `python/scripts/extract_lhs10k_smallpulse_summary.py` | template for per-year median/percentile extraction of a pulse marginal. |
| Convergence check | `python/scripts/substack/pulse_convergence.py` | confirms 1/0.1/0.01 GtC linearity — the justification for scaling down to 1e-4. |
| Existing SLR band fig | `python/scripts/poster/slr_band.py` | styling template for the LEFT panel (bands, percentile fills, anchor rebaselining) — but it's RFF-SP; swap the input to the SSP245 cube + rebaseline to 2005. |

---

## Build plan (after the 3 confirmations)

**LEFT panel — SSP2-4.5 SLR rel 2005, 90% + 75% bands**
1. Run BRICK over the SSP245 GMST/OHC cube (841 cfg × N BRICK posts) via
   `run_mimibrick_flatcube.jl`, total SLR only (SAVE_COMP not needed here).
   If `cross_ssp245_validation_gmsl.csv` is confirmed current/post-PR#93, you
   can reuse it directly — check the posterior vintage first.
2. Rebaseline every trajectory to its **2005** value (subtract SLR_2005 per
   draw). NB our cubes store SLR rel 2000; rebaselining to 2005 is a
   per-draw subtraction, not a re-run.
3. Importance weighting: SSP2-4.5 is a FIXED scenario, so there are NO RFF
   importance weights here — the band is the **unweighted** spread over
   (cfg × BRICK post). Do NOT apply Wong/importance weights (those are
   conditional on RFF draws). Confirm with Marcus, but this is the correct
   default for a single-scenario SSP band.
4. Plot median + **5–95% (90%)** + **12.5–87.5% (75%)** bands, x from 2005.
   Empirical percentiles, not Gaussian (climate-modeling skill; tipping tail).

**RIGHT 6 panels — impulse response to (scaled) 1e-4 GtC pulse at 2020**
1. Generate baseline + pulse GMST/OHC at PULSE_YEAR=2020 using the multidecade
   v145 driver at a numerically-safe size (recommend 0.01 GtC ≡ 0.03667 GtCO₂).
   Apply all 5 paired-experiment sanity tests (climate-modeling /
   `feedback_apply_sanity_tests_for_pulses`): zero-pulse bit-identical,
   sign-flip symmetry, magnitude-doubling ratio=2, first-principles magnitude,
   reproducibility. Generate the ±pulse pair at design time.
2. Run BRICK paired (baseline + pulse) with `--save-component-trajs true` →
   per-year te/ais/gis/gsic/lws + total, for both arms.
3. Marginal component_i(t) = [pulse_i(t) − baseline_i(t)] **× (1e-4 / pulse_GtC)**
   to scale to the requested 1e-4 GtC (linearity-justified). Total GMSLR
   marginal = sum of the 5 component marginals (cross-check vs the driver's
   total column — should match to float tol).
4. Six panels: TE, GSIC, GIS, AIS, LWS, Total. Median + (optionally) the 5–95%
   band per component. Use the MEDIAN, not mean, for the central line — the
   mean is AIS-tipping-corrupted even at small pulse for the AIS/Total panels
   (memory `project_pulse_size_findings`; mimibrick-quirks §11). At 1e-4 GtC
   tipping should be absent, but median is the safe, pulse-size-invariant
   choice and keeps all 6 panels consistent.
5. Units on each y-axis: SLR per 1e-4 GtC (state the GtC↔GtCO₂ conversion in
   the caption). Consider mm or µm rather than cm given the tiny magnitudes.

---

## Suggested new script locations
- `python/scripts/rennels_ssp245_slr_band.py` (left panel)
- `python/scripts/rennels_pulse_component_response.py` (right 6 panels)
- `python/scripts/rennels_7panel_figure.py` (composes the 7-panel layout;
  mirror the matplotlib gridspec style of `poster/layout_mockup.py`)
- Output: `outputs/rennels/slr_7panel_ssp245.{png,pdf}`

## Sanity / review gate before sending to Lisa
- Run the 5 paired-pulse sanity tests; paste results in the script's stdout.
- First-principles magnitude check: per-GtC total SLR @2100 from memory is
  ~0.0074 cm/GtCO₂ @2150 (small-pulse) — verify the scaled 1e-4 GtC total lands
  at ~1e-4/3.667e-4 of the per-GtCO₂ number. If off by >2-3×, dig (CLAUDE.md
  quantitative pre-check).
- Confirm Total = TE+GSIC+GIS+AIS+LWS exactly (LWS inclusion is a known
  recurring omission — `project_brick_five_components`).
- LWS caveat: BRICK LWS = 0 before ~2019 by calibration design
  (`project_brick_lws_calibration_convention`); for a 2020 pulse the LWS
  marginal response may be ~0 or tiny — note this on the LWS panel so it
  doesn't read as a bug.

## Collaborator note
Lisa Rennels authored the AR6 emissions file and was the origin of the
solar/volcanic + GtC/GtCO₂ unit-error thread — she will scrutinize units and
provenance. Label the FaIR version as **FaIR v2.2.4 (v1.4.5 calibration)**, the
BRICK posterior as **post-PR#93 (Wong 2026)**, and state the pulse unit
explicitly. See memory `project_fair_version_distinction`,
`project_brick_post_pr93_posterior_installed`.
