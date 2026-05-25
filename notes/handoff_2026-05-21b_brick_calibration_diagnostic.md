# Handoff — 2026-05-21 — BRICK calibration mismatch diagnostic (Tony Wong follow-up, deep dive)

This handoff captures a substantial 200+-call diagnostic session triggered
by Marcus's question "why is LWS zero until 2018?" on the previous-session
Tony-figure deliverable. The session converged on a published-paper-grade
finding about BRICK's calibration assumptions and produced three figures, two
Julia diagnostics, a verified set of memory entries, and the framework for a
Tony email. A fresh session should be able to pick up cold by reading this
note plus `~/.claude/CLAUDE.md`, the project `CLAUDE.md`, and the auto-memory
at `~/.claude/projects/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/memory/`.

The two parent handoffs in the same project arc:
- `notes/handoff_2026-05-20_tony_wong_followup.md` — original Tony email/scope.
- `notes/handoff_2026-05-21_julia_per_component_done.md` — Julia per-component
  + obs-driven driver work that landed yesterday.

## 1. Headline finding (worth a paper-section)

BRICK's `te_α` thermal-expansion coefficient was calibrated end-to-end
against **Gouretski & Koltermann 2007** OHC (`data/calibration_data/ocean_heat_gouretski_3000m.csv`,
1953-1996, 0-3000m). The modern **Cheng IAPv4.2** reanalysis shows OHC ~2×
smaller than Gouretski over the same window:

| Source | ΔOHC 1953-1996 | Trend |
|---|---:|---:|
| Gouretski 2007 (BRICK calibration target) | **+26.67 × 10²² J** | +0.439 ZJ/yr |
| Cheng IAPv4.2 (modern reanalysis) | +13.50 × 10²² J | +0.289 ZJ/yr |
| SNEASY MAP RCP45 (BRICK internal) | +33.04 × 10²² J | +0.587 ZJ/yr |

**Implication:** When BRICK is driven by modern obs OHC (or any externally
supplied trajectory close to Cheng-magnitude), `te_α` (tuned for Gouretski-
scale ΔOHC) produces a TE response that is ~2× too small. The entire
SLR-RFF-BRICK external-input pipeline has this issue. Tony's pipeline doesn't
because he runs BRICK with SNEASY internal (Gouretski-consistent OHC).

This is the **dominant** explanation for the obs-vs-model gap, not the small
GMST effect that originally motivated the Tony email.

## 2. Verified TE decomposition (all from actual BRICK runs)

| Setup | te_α | ΔOHC source | ΔTE (1900-2018) |
|---|---:|---:|---:|
| Default (no posterior, SNEASY internal) | 0.150 | SNEASY 75 ZJ | **+7.92 cm** |
| Posterior + SNEASY OHC (≡ Tony's setup) | 0.057 | SNEASY 75 ZJ | **+2.71 cm** |
| Posterior + obs OHC (our pipeline) | 0.057 | obs 45 ZJ | **+1.64 cm** |
| Frederikse 2020 Steric (truth) | — | — | **+5.68 cm** |

First-principles physics formula matches BRICK to within ~5% in every
verified case. **Even Tony's mode undershoots Frederikse Steric by 3 cm —
he just doesn't see it in his C&W-targeted comparisons because BRICK is
calibrated to C&W, which is LWS-removed and uses Gouretski OHC.**

## 3. AIS — our pipeline reproduces Tony's AIS to within 3 mm

Tony emailed AIS values: 1850 = −0.06 m, 1900 = −0.04 m, 2000 = 0, 2020 = +0.01 m.
Verified using Tony's 1992-2001 baseline (per his notebook, see § 6):

| year | Our obs_obs median (m) | Our 17-83% (m) | Tony (m) | Δ |
|---|---:|---:|---:|---:|
| 1850 | −0.0568 | (−0.094, −0.018) | −0.060 | +0.003 |
| 1900 | −0.0378 | (−0.050, −0.028) | −0.040 | +0.002 |
| 2000 | +0.0012 | (+0.001, +0.001) | 0.000 | +0.001 |
| 2020 | +0.0075 | (+0.006, +0.009) | +0.010 | −0.003 |

**No implementation difference between our AIS and Tony's.** The AIS
historical overshoot vs Frederikse (~3 cm at 1900) is a BRICK-wide
calibration property, not pipeline-specific. Default-mode BRICK shows
an AIS overshoot of −11.55 cm at 1900 — worse than the posterior — so
the overshoot is structural to the fast-dynamics module, partially
ameliorated by posterior calibration.

## 4. Component biases (full picture, vs Frederikse on 1961-1990 baseline)

At 1900 the discrepancy is multi-component and largely cancelling:

- AIS: BRICK overshoots by +3 cm (too much historical retreat)
- GSIC: BRICK undershoots by 4 cm
- GIS: BRICK undershoots by 4 cm
- TE: BRICK undershoots by 2 cm (Gouretski mismatch)
- LWS: BRICK = 0 by design pre-2019

The AIS overshoot partly cancels the others' undershoots, producing a
plausible-looking total even though no individual component matches obs.

## 5. Methodological side-findings (worth preserving)

- **BRICK's TE formula is dimensionally correct.** The `ρ²` in
  `te_sea_level[t] = te_sea_level[t-1] + Δoceanheat · te_α / (te_A · te_C · te_ρ²)`
  is right because `te_α` has units `kg m⁻³ °C⁻¹` (= α_standard · ρ in
  conventional notation). An earlier agent claim that this was a bug was
  **wrong** and verified-against. See `thermal_expansion_component.jl:12`.
- **The 8 "lost" posterior columns** (`sd_glaciers`, `rho_antarctic`, etc.)
  are **AR(1) observation-noise model parameters**, not model parameters.
  Used at `run_projections.jl:176-187` to simulate likelihood-side noise.
  NOT applying them to the forward model is correct.
- **LWS = 0 historical by design.** `landwater_storage_component.jl:25-39`
  sets `lws_sea_level[t] = 0.0` for `t < first_projection_year` (~2019 in
  default RCP45). Calibration target was C&W which had LWS removed.
- **Frederikse-merged Greenland calibration was already in v1.0.1.** Verified
  at `create_log_posterior_brick.jl:219` (`indices_greenland_data = ...
  calibration_data.merged_greenland_obs`).

## 6. Tony's notebook recipe (now known)

From `brick_v130_comparisons_to_data.ipynb`:
- Uses **sneasybrick** model config (SNEASY-coupled, not standalone BRICK).
- Loads precomputed projection CSVs from his local
  `~/.julia/dev/MimiBRICK/results/projections_csv/` (his runs).
- Baselines: **1961-1990 for GMSL/GIS/GSIC/TE/Total**, **1992-2001 for AIS**,
  1850-1900 for Temperature. Each ensemble member normalized to its own
  baseline-window mean.
- Band: **17-83%** (1σ-equivalent), not 5-95%.
- Obs sources:
  - `all_calibration_data_combined.csv` for gmsl, glaciers, antarctic_imbie,
    hadcrut, ocean_heat (Gouretski).
  - Frederikse 2020 `global_basin_timeseries.xlsx` to **replace** the
    `merged_greenland_obs` column. Sigma = (upper - lower) / 4.
  - No obs overlay for TE (trends-only in calibration data per his note).
- Layout: 5 panels stacked vertically with errorbar obs overlay.

## 7. Artifacts produced this session

### Code (committable)

- `julia/test_sneasy_default.jl` — BRICK default-mode (no posterior, no
  overrides) diagnostic. Runs in ~3 sec.
- `julia/test_sneasy_posterior.jl` — BRICK posterior + SNEASY internal
  (Tony-mode replication). `MAX_POST=100` runs in ~3 sec; full 10k
  available via env var override.
- `python/scripts/substack/gouretski_vs_cheng_ohc.py` — the headline
  calibration-mismatch figure.
- `python/scripts/substack/component_overlay_tony_style.py` — direct
  reproduction of Tony's figure recipe using our obs_obs data.
- `python/scripts/substack/component_overlay_obsdriven.py` — earlier 2×3
  per-component overlay with Frederikse + 2×2 attribution; updated with
  Gouretski caveat in titles and inset.

### Outputs

- `outputs/substack/gouretski_vs_cheng_ohc.{png,pdf}` — headline figure.
- `outputs/substack/component_overlay_obsdriven.{png,pdf}` — 2×3 per-component.
- `outputs/substack/component_overlay_tony_style.{png,pdf}` — Tony-style 5×1.
- `outputs/brick_sneasy_posterior_diagnostic.csv` — 100 posterior draws of
  Tony-mode at landmark years.

### Memory entries added (8 total this session)

- `project_brick_lws_calibration_convention.md`
- `project_brick_component_biases_vs_frederikse.md`
- `project_brick_calibration_input_mismatch.md` (with Tony-mode verification appended)
- `project_brick_gouretski_calibration_target.md` (headline finding)
- `project_tony_obs_vs_fair_attribution.md`
- `project_ohc_splice_provenance.md` (from previous session, referenced)

## 8. Where this leaves the work

### Immediate next steps (post-handoff)

1. **Marcus writes the email to Tony.** Outline + all verified numbers are
   in the session transcript and in the memory entries. Key asks for Tony:
   (a) resend his notebook (was missing from his reply, then sent separately),
   (b) share his FaIR-hook patch to `run_projections.jl` from his EDF work,
   (c) react to the Gouretski-vs-Cheng diagnosis.

2. **The recommended principled fix:** port Tony's MAGICC-pattern hook in
   raddleverse master `run_projections.jl` to a `fair_sampling::Bool` flag
   that swaps in FaIR-derived GMST + OHC through the same channel that
   SNEASY would otherwise populate. This lets BRICK's calibrated couplings
   (including the proper handling of ocean_heat_mixed + ocean_heat_interior)
   apply to FaIR-derived inputs, removing the te_α miscalibration that our
   current external-override approach hits. ~1-2 days of Julia work.

3. **Alternative quick fix (option 3 from earlier):** multiplicatively scale
   our spliced obs OHC by ~1.98× to match the Gouretski calibration scale.
   Crude but cheap; would push our TE response into the right ballpark
   without code changes. Useful as a sanity-check before committing to (2).

### Pending threads from BEFORE this diagnostic

- `notes/ensemble_design_proscons_2026-05-20.md` — D vs E decision on the
  new 3,000-RFF × 3-cfg ECS-stratified ensemble. Not blocked by this
  diagnostic, but its results (per-component LHS-10k bands, pulse experiments)
  will all carry the Gouretski calibration mismatch unless we fix it first.

- `handoff_2026-05-20_brick_julia_per_component.md` §5.1 — re-submit
  LHS-10k pipeline with `--save-component-trajs true`. Still useful;
  unaffected by this diagnostic.

- AGU Chapman SLR poster (deadline ~2026-06-01, memory
  `project_agu_chapman_poster.md`) — the per-component panel can now show
  the Tony-style Frederikse-overlay diagnostic, but should NOT silently
  rely on BRICK's TE without disclosing the Gouretski calibration caveat.

## 9. Reproducible commands

```bash
# Run BRICK in default mode (no posterior, SNEASY OHC + GMST internal)
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK/julia
julia --project=. test_sneasy_default.jl
```

```bash
# Run BRICK Tony-mode (posterior + SNEASY internal) — 100 members ~3s
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK/julia
julia --project=. test_sneasy_posterior.jl
# or full 10k posterior:
MAX_POST=10000 julia --project=. test_sneasy_posterior.jl
```

```bash
# Generate the Gouretski-vs-Cheng calibration mismatch figure
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
source ~/climate-env/bin/activate
python3 python/scripts/substack/gouretski_vs_cheng_ohc.py
```

```bash
# Reproduce Tony's figure with our obs-driven BRICK data
python3 python/scripts/substack/component_overlay_tony_style.py
```

```bash
# Refresh the 2x3 component overlay (Gouretski caveat in titles)
python3 python/scripts/substack/component_overlay_obsdriven.py
```

## 10. Things a fresh session should NOT do

- Don't re-derive any of the verified findings without checking the relevant
  memory entry first (`project_brick_*` files have the receipts).
- Don't propose adding historical-LWS corrections as a fix for the BRICK-vs-obs
  total gap without flagging the pre-1980 sign-flip issue documented in
  `project_brick_lws_calibration_convention.md`.
- Don't believe agent-reported claims about BRICK source code without
  verifying against the actual MimiBRICK source at
  `~/.julia/packages/MimiBRICK/bpCAF/`. This session caught two
  agent-reported "bugs" that were actually correct code.
- Don't treat the SNEASY/Gouretski/Cheng inputs as substitutable. The
  pipeline's behavior depends sensitively on which OHC source is fed where.

## 11. References for the email / paper-section writeup

- Gouretski, V. & Koltermann, K. P. 2007. "How much is the ocean really
  warming?" *Geophys. Res. Lett.* 34, doi:10.1029/2006GL027834.
- Cheng L. et al. 2024. "IAPv4 ocean temperature and ocean heat content
  gridded dataset." *Earth Syst. Sci. Data* 16:3517-3546.
  doi:10.5194/essd-16-3517-2024.
- Frederikse T. et al. 2020. "The causes of sea-level rise since 1900."
  *Nature* 584:393-397. doi:10.1038/s41586-020-2591-3.
- Wong T. E. et al. 2017. "BRICK v0.2..." *Geosci Model Dev*
  10:2741-2760. doi:10.5194/gmd-10-2741-2017 (calibration paper).
- Zanna L. et al. 2019. "Global reconstruction of historical ocean
  heat storage and transport." *PNAS* 116:1126-1131.
  doi:10.1073/pnas.1808838115 (not Nature; the parent handoff cited it
  as Nature, fixed during this work).
