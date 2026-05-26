# Handoff — FrEDI multi-decade SC-CO₂ mortality for IPI

**Created:** 2026-05-26
**Owner:** Marcus C. Sarofim
**Deliverable target:** Peter Howard (Institute for Policy Integrity, IPI)
**Estimated effort:** 3–4 hr if v1.4.5 outputs already on disk; 6–8 hr from cold start.

## What the deliverable is

A table (and 1–2 figures) of social-cost-of-CO₂ mortality NPV per tonne
CO₂, computed for pulse years 2020 / 2030 / 2040 / 2050 / 2060 / 2080,
at 2% and 3% Ramsey discount rates, through 2300. Sectors included:
ATS Temperature-Related Mortality (Cromar 2022, Mean variant — the
deaths-relevant ATS sector, **not** "Extreme Temperature" which is the
older Mills & Schwartz formulation), Climate-Driven Air Quality
(2011-Emissions variant, restricted GCM averaging — only CCSM4 and
GFDL-CM3 produce nonzero AQ mortality), Vibriosis.

This work is the v1.4.5 calibration update of the deliverable described
in earlier correspondence with Peter (2025-12 sequence) — the previous
$28.21 / tCO₂ figure was wrong (used the Mills & Schwartz "Extreme
Temperature" sector and a wrong baseline). The v1.4.1 central was
$15.50 / tCO₂ at 3% through 2300 for a 2030 pulse; v1.4.5 should land
in that neighborhood with small shifts.

## Where the code lives

All in `~/Documents/2026/CodeProjects/FaIRtoFrEDI/`:

| File | Role |
|---|---|
| `compute_pulse_temps_multidecade_v145.py` | Generates per-pulse-year FaIR baseline + pulse temperature CSVs. Reads from the v1.4.5 splice (Smith 2024 historical 1750–2020 + RFF-SP draw #08113 2021–2300). Outputs to `fair_outputs/temp_pulse_*_v145.csv`. |
| `sc_co2_mortality_multidecade_v145.R` | Reads the FaIR pulse temperatures, applies the 0.5545 °C baseline subtraction (1986–2005 mean), feeds GMST into FrEDI with explicit-temperature mode, accumulates annual deaths and dollar damages by sector, computes NPV at 2% and 3%. |

The corresponding v1.4.1-era files (`*_multidecade.R`, `*_multidecade_cc.R`) are kept for diffing; do not modify them.

## Quick start (assuming v1.4.5 FaIR pulse CSVs already exist)

```bash
cd ~/Documents/2026/CodeProjects/FaIRtoFrEDI
ls fair_outputs/temp_pulse_*_v145.csv   # confirm pulse CSVs are present
```

```bash
source ~/climate-env/bin/activate
Rscript sc_co2_mortality_multidecade_v145.R 2>&1 | tee runs/multidecade_v145_$(date +%Y%m%d_%H%M%S).log
```

Expected runtime: ~30–45 min for all 6 pulse years × 3 sectors × full 1986–2300 horizon (FrEDI re-runs per sector to avoid the 16 GB RAM ceiling per `fredi-quirks`).

## If pulse temperature CSVs are stale or missing

Regenerate from the v1.4.5 FaIR pipeline:

```bash
cd ~/Documents/2026/CodeProjects/FaIRtoFrEDI
source ~/climate-env/bin/activate
python compute_pulse_temps_multidecade_v145.py
```

This builds the 6 paired baseline/pulse CSV pairs in `fair_outputs/`.
Each pulse is **1 GtCO₂** (not per-tonne) — see floating-point note below.
Runtime ~5 min.

## Sanity tests (apply ALL before sharing numbers)

Per `~/.claude/skills/climate-modeling` and the SLR-RFF-BRICK paired-pulse experience: every pulse experiment gets these 5 tests before headline numbers.

1. **Zero-pulse test.** Run with pulse magnitude = 0; result must be bit-identical to baseline (deaths_diff = 0 at every year, every sector).
2. **Sign-flip symmetry.** Run with −1 GtCO₂ pulse; result should be ≈ −1 × the +1 GtCO₂ case to within ~1% (small nonlinearity acceptable).
3. **Magnitude doubling.** Run with +2 GtCO₂ pulse; result should be ≈ 2× the +1 GtCO₂ case to within ~1% (linearity).
4. **Bit-identical baseline.** The baseline-arm temperatures should be bit-identical across all 6 pulse-year runs (they don't depend on pulse year). Check with `diff` or md5sum on the baseline CSV columns.
5. **First-principles magnitude.** ATS @ 2100: 1 GtCO₂ pulse at 2030 → ~20 deaths/yr at 2100 per v1.4.5 memory (`project_v145_sccco2_central_results.md`). If you see > 100 or < 1, something is wrong.

The v1.4.5 single-pulse driver passed all 5 tests on 2026-05-22 per
`project_v145_pulse_sanity_passed.md`. The multidecade port passed at
PULSE_YEAR=2050 per `project_v145_multidecade_sanity_passed.md`. Repeat for
any year the deliverable will quote.

## Critical methodological details (don't re-derive — these were hard-won)

From `~/.claude/skills/fredi-quirks` and the FaIRtoFrEDI/CLAUDE.md:

1. **Temperature baseline.** FrEDI damage functions are calibrated to a 1986–2005 reference. FaIR outputs are relative to 1850–1900. **Subtract 0.5545 °C** from every FaIR-derived temperature before passing to FrEDI. The v145 multidecade driver does this already; verify it stays in if you refactor.

2. **Correct mortality sector.** Use `"ATS Temperature-Related Mortality"` (Cromar 2022, Mean variant) — **NOT** `"Extreme Temperature"` which is the older Mills & Schwartz sector. The ATS sector uses `impactType == "N/A"`. The Mills & Schwartz mistake was the v1.4.1-era $28.21 error.

3. **FrEDI aggregation.** `aggLevels = c("national", "modelaverage", "impactyear")`, then filter `impactYear == "Interpolation"` and `model == "Average"` (for non-AQ sectors). For AQ: filter to `model %in% c("CCSM4", "GFDL-CM3")`, average per state, then sum states. The other 6 GCMs are zero for AQ and must NOT be averaged in.

4. **Physical vs dollar.** `annual_impacts` = VSL-weighted dollars. `physical_impacts` = deaths (confirmed for ATS and AQ; Vibriosis physical_impacts units are uncertain — report Vibriosis only as NPV dollars, never as deaths/year). For deaths-per-tonne: subtract physical_impacts between pulse and baseline.

5. **1 GtCO₂ pulse, not per-tonne.** Stay above floating-point noise by running at 1 GtCO₂ scale. **Divide the damage difference by 1e9 only at the very final per-tCO₂ reporting step.**

6. **Population pre-loading.** Pass `popfile = file.path(system.file(package="FrEDI"), "extdata/scenarios/State ICLUS Population.csv")` to `import_inputs()` to reduce per-call time from ~35 sec to ~6 sec. Critical for 6 pulse years × 3 sectors = 18 FrEDI runs.

7. **One sector at a time.** FrEDI's `run_fredi()` is memory-hungry; loop sector-by-sector to stay under the 16 GB RAM ceiling on the local Mac.

## Discount-rate framing for IPI

Per `feedback_discount_rates.md`:
- **3% Ramsey** is the current-EPA-relevant rate. Use 3% as the headline.
- **2% Ramsey** is for academic comparability with the Trump-era EPA "modernization" (which the current EPA reverted away from). Include as a secondary column.
- **Don't call 2% "EPA's current federal rate"** — that's stale framing.

For IPI's downstream use, Peter has historically wanted both rates so he can compare to the literature (Rennert 2022, Kopits 2025, etc.). Provide both.

## Expected output table (v1.4.1 reference + v1.4.5 update)

Per `project_v145_sccco2_central_results.md`:

| Pulse year | v1.4.1 NPV @ 3% ($/tCO₂) | v1.4.5 NPV @ 3% ($/tCO₂) |
|---|---|---|
| 2020 | — | $13.4 |
| 2030 | $15.50 (Cromar central) | ≈ $15.5 (bit-identical to v141 in the headline number; small shifts from v145 ECS) |
| 2040 | — | $17–18 |
| 2050 | — | $19–20 |
| 2060 | — | $20–21 |
| 2080 | — | $22.7 |

These v1.4.5 numbers escalate roughly as `~$0.5 / tCO₂ per decade earlier` (consistent with deepening damage convexity over time — the same pulse fired earlier accumulates more discounted damages because they fall in higher-population higher-warming years).

## Open methodological questions for Peter / IPI

These should be resolved before publication or formal submission to IPI:

1. **Discount rate scheme.** Pure 3% constant rate, or Ramsey with declining schedule (Rennert 2022 style)? The v1.4.1 numbers used flat 3%. Peter may want Ramsey-Newell-Pizer formulation; if so the script needs an update.

2. **End year.** Through 2300 is the current standard. Some IWG / EPA work uses 2200 only. Document the choice in the deliverable.

3. **AQ sector inclusion.** The 2011-emissions variant of FrEDI's AQ sector contributes ~$2 / tCO₂ to the SC at 3%. Some IPI workflows have historically used air quality damages separately. Confirm with Peter whether to bundle or break out.

4. **Vibriosis sector.** Tiny contribution (~$0.02 / tCO₂) but in the same Cromar / FrEDI family. Include for completeness but note the small magnitude.

5. **Uncertainty propagation.** The current multidecade pipeline uses the CENTRAL v1.4.5 FaIR run (RFF-SP draw #08113 splice). Full uncertainty propagation would re-run across all 10,000 RFF draws × FaIR cfgs — that's the `sc_uncertainty_all_sectors_cc.R` workstream which is pending. For IPI's immediate deliverable, central estimates are fine; flag the absence of uncertainty bars.

6. **Coastal-property and HTF interaction.** This deliverable is mortality-only. Peter's broader SC-GHG work also includes coastal damages — those come from the SLR-RFF-BRICK side (`run_fredi_slr_phaseC_baseline_v145.R`). Coordinate with the SLR pipeline before claiming "the SC-CO₂ is" — this analysis covers mortality only.

## Files to deliver to Peter / IPI

1. **Headline CSV:**
   `~/Documents/2026/CodeProjects/FaIRtoFrEDI/fredi_outputs/multidecade_npv_v145.csv`
   Columns: `pulse_year, sector, discount_rate, npv_per_tco2_usd, annual_deaths_at_2100_per_gtco2`

2. **Per-year deaths table:**
   `~/Documents/2026/CodeProjects/FaIRtoFrEDI/fredi_outputs/multidecade_annual_deaths_v145.csv`
   Columns: `pulse_year, sector, year, deaths_per_gtco2`

3. **Methods PDF or memo** referencing this handoff doc and citing:
   - Rennert et al. 2022 (DSCIM-USA reference SC-CO₂)
   - Cromar et al. 2022 (ATS Temperature-Related Mortality)
   - Sheahan et al. 2025 (VSL inflation convention)
   - Kopits et al. 2025 (EPA NCEE WP 25-01; FrEDI-to-FrEDI benchmark gives $33–36/t at 2% Ramsey for 2030 pulse — directly compatible numbers)
   - Smith et al. 2024 (FaIR-calibrate v1.4.1; the v145 release is an update of this calibration framework)

## Known limitations to caveat

1. **No probabilistic uncertainty bars** — central run only. Full uncertainty deliverable would be a separate workstream (~1 week of compute on Torch).
2. **FrEDI sector coverage limited** to mortality channels. Other SC-CO₂ damage categories (agriculture, labor productivity, electricity demand, etc.) are present in FrEDI but not in this mortality-focused deliverable.
3. **VSL inflation choice** matters. The Sheahan 2025 convention uses $7.9M (1990$) → 2023$. Different VSL conventions can shift the dollar headline by ±15%.
4. **Temperature mapping assumption.** Linear temperature-mortality response (Cromar 2022 calibration). Adaptation / acclimatization not modeled.
5. **v1.4.5 vs v1.4.1.** v145 is the canonical calibration as of this handoff. If a v1.5 or v2 fair-calibrate release lands, headline numbers will shift again.

## Cross-references

- Memory: `project_v145_sccco2_central_results.md` — v145 headline numbers + 6-pulse-year escalation
- Memory: `project_v145_multidecade_sanity_passed.md` — 5-test sanity pass at PULSE_YEAR=2050
- Memory: `project_v145_pulse_sanity_passed.md` — single-pulse v145 driver verification
- Skill: `~/.claude/skills/fredi-quirks` — FrEDI conventions
- Skill: `~/.claude/skills/climate-modeling` — paired-pulse 5-test framework
- `~/Documents/2026/CodeProjects/FaIRtoFrEDI/CLAUDE.md` — project-specific FrEDI methodology

## Contact

Peter Howard (IPI): peter.howard@nyu.edu (per Marcus' notes)
Kevin Cromar (NYU, mortality methodology supervisor): kevin.cromar@nyulangone.org

Marcus is the canonical contact for this analysis; in his absence, refer questions to either of the above per their respective expertise.
