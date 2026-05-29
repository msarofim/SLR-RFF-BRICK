# Figure inventory — SLR-RFF-BRICK (poster + Substack)

**Compiled:** 2026-05-29. Single source of truth mapping every deliverable
figure → generating script → output path → status.

**Provenance / confidence:**
- ✅ **Verified this session** (statuses current as of 2026-05-29): all
  Hawkins-Sutton / Group-Sobol figures, poster panels C & D, the CH4 pulse panel,
  and the ANOVA cross-check.
- 🔎 **Repo-scan-derived** (script→output mapping from a code scan + the parent
  handoff `handoff_2026-05-28_v5_hs_poster.md`; statuses NOT re-verified this
  session — confirm before relying): the obs-overlay, component-overlay,
  crossing-year, and non-H-S poster panels.

Paths are relative to `/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK`
unless noted. Poster scripts live in `python/scripts/poster/`, Substack scripts in
`python/scripts/substack/`.

---

## A. POSTER (AGU Chapman) — panels A–J

Canonical deliverables: `outputs/poster/iec_graphics_handoff/panels/*.pdf`.
Captions: `outputs/poster/iec_graphics_handoff/poster_text.txt`.

| Panel | Title | Output (panels/) | Generating script | Status |
|---|---|---|---|---|
| A | Pipeline | `A_pipeline.pdf` | 🔎 `pipeline_schematic.py` (or hand-composed) — verify | supporting |
| B | Probabilistic SLR | `B_probabilistic_slr.pdf` | 🔎 `slr_band.py` (or hand-composed) — verify | supporting |
| **C** | **Total ΔSLR — sources of uncertainty** | `C_total_slr_hawkins_sutton.pdf` | ✅ `poster/hawkins_sutton_panels.py` | **Group-Sobol, normalized, 11-yr smoothed (CURRENT, re-rendered 2026-05-28)** |
| **D** | **Pulse ΔSLR — sources of uncertainty** | `D_pulse_slr.pdf` | ✅ `poster/hawkins_sutton_panels.py` | **Group-Sobol (CURRENT, re-rendered 2026-05-28)** |
| F | Damage-function methodology | `F_damage_function_methodology.pdf` | 🔎 `sweet_scenarios.py` (FrEDI LHS-10k_s) — verify | v5 LHS-10k_s FrEDI |
| G | Adaptation (Lorie 2020) | `G_adaptation_lorie.pdf` | 🔎 `lorie_panel.py` | supporting |
| H | Coastal property + HTF damages | `H_coastal_property_and_htf_damages.pdf` | 🔎 `htf_transport_table.py` | v5 LHS-10k_s FrEDI |
| I | Damages by state | `I_state_damages_map.pdf` | 🔎 `plot_state_damages_2100.py` | v5 LHS-10k_s FrEDI (LA≫FL>MA>VA>NJ) |
| J | HTF elder mortality (Sheahan 2025) | `J_htf_elder_mortality.pdf` | 🔎 `sheahan_table.py` or hand-made — verify | NOT v5-updated (Marcus's figure) |

Source-of-truth for C/D data: `outputs/substack/v5_hybrid_decomp_{total,pulse}_{clip,unclip}.csv`
(written by `substack/group_sobol_hs.py`). poster_text.txt C/D captions + the
Discussion numbers were updated to Group-Sobol wording 2026-05-28 (Discussion
prose flagged for Marcus's voice review).

---

## B. SUBSTACK (Saraph Report SLR post)

### B1. Hawkins-Sutton variance decomposition — ✅ CURRENT (Group-Sobol, this session)

| Figure | Output (`outputs/substack/`) | Script | Notes |
|---|---|---|---|
| Total GMST H-S | `shapley_hs_total_gmst.{png,pdf}` | `group_sobol_hs.py` (renders + writes per-axis CSV) | R²≈0.97; internal 100%→3%, emissions overtakes climate ~2090 |
| Pulse GMST H-S | `shapley_hs_pulse_gmst.{png,pdf}` | `group_sobol_hs.py` | climate-dominated 89–99% |
| Total SLR H-S | `shapley_hs_total_slr_hybrid_tipping.{png,pdf}` | `render_hybrid_tipping_split.py` (reads group_sobol decomp CSVs) | emissions **29%** @2150 (was 8.6% TreeSHAP); +interactions+tipping wedges |
| Pulse SLR H-S | `shapley_hs_pulse_slr_hybrid_tipping.{png,pdf}` | `render_hybrid_tipping_split.py` | emissions ~0 (scenario-independent), climate 34%, brick 22%, tipping 20% |
| Paired GMST | `paired_gmst.{png,pdf}` | `paired_figures_hs.py` | projection band (top) + H-S (bottom) |
| Paired SLR | `paired_slr.{png,pdf}` | `paired_figures_hs.py` | reads `shapley_hs_per_axis_total_slr_hybrid_tipping.csv` |
| Paired pulse (2×2) | `paired_pulse.{png,pdf}` | `paired_figures_hs.py` | pulse GMST+SLR response + their H-S |

Per-axis CSVs: `shapley_hs_per_axis_{total,pulse}_gmst.csv`,
`shapley_hs_per_axis_{total,pulse}_slr_hybrid_tipping.csv`. 11-yr display
smoothing applied in the renderers (raw decomp CSVs unsmoothed).

### B2. Pulse responses — ✅ CURRENT (CH4 left as-is per Marcus 2026-05-29)

| Figure | Output | Script | Notes |
|---|---|---|---|
| Multi-gas pulse response (CO₂/CH₄ GMST+SLR) | `pulse_responses_clean.{png,pdf}` | `pulse_responses_clean.py` | CH4 SLR panel still on old single-post summary; brick-averaging de-noising was a null result (NOT shipped) |

### B3. ANOVA model-free cross-check — ✅ DONE (2026-05-29) — VALIDATES Sobol

| Figure/output | Output | Script | Notes |
|---|---|---|---|
| ANOVA total SLR per-axis | `shapley_hs_per_axis_total_slr_anova324k.csv` | `anova_hs_decomp.py --tag 324k` | model-free LoTV decomp of the 324k balanced factorial (rff300×cfg60×seed3→324k BRICK). @2150: emissions 27.0% (Sobol 28.9%), climate 26.9% (27.3%), internal 0.5% (0.6%) — agree ≤2pp; ANOVA brick 35.9% ≈ Sobol brick+interactions+tipping 43.1% (same total, different split). Confirms emissions ~27% is not a surrogate artifact (TreeSHAP was 8.6%). |
| ANOVA-vs-Sobol overlay | `anova_vs_sobol_total_slr.{png,pdf}` | `anova_vs_sobol_overlay.py` | paired stacked bars at 2050/2100/2150; same colors/labels as the H-S figures. Methods-section / supplementary cross-check figure. |

### B4. Obs overlays & components — 🔎 repo-scan (verify status)

| Figure | Output | Script |
|---|---|---|
| FaIR GMST + BRICK SLR vs obs | `fair_brick_vs_obs_gmst_gmsl.{png,pdf}` | `fair_brick_vs_obs_gmst_gmsl.py` (IGCC ensemble + Dangendorf 2024) |
| FaIR GMST + OHC vs obs | `fair_vs_obs_gmst_ohc.{png,pdf}` | `fair_vs_obs_gmst_ohc.py` (Gouretski 2007 + Cheng IAPv4.2) |
| BRICK SLR vs obs | `obs_overlay_slr.{png,pdf}` | `obs_overlay_slr.py` (Dangendorf 2024) |
| GMST hindcast overlay | `obs_overlay.{png,pdf}`, `obs_overlay_recent.{png,pdf}` | `obs_overlay.py`, `obs_overlay_recent.py` (older LHS pilot) |
| SLR components (Tony-style) | `component_overlay_tony_style_extended.{png,pdf}` | `component_overlay_tony_style_extended.py` |
| SLR components (obs-driven combos) | `component_overlay_obsdriven.{png,pdf}` | `component_overlay_obsdriven.py` |
| BRICK vs Grinsted TSLS | `brick_vs_grinsted_tsls_components.{png,pdf}` | `brick_vs_grinsted_tsls_components.py` |
| OHC: Gouretski vs Cheng | `gouretski_vs_cheng_ohc.{png,pdf}` | `gouretski_vs_cheng_ohc.py` |

### B5. Crossing years / thresholds — 🔎 repo-scan (verify status)

| Figure | Output | Script |
|---|---|---|
| Median crossing year | `median_crossing_year.{png,pdf}` | `median_crossing_year.py` |
| Exceedance crossing year | `exceedance_crossing_year.{png,pdf}` | `exceedance_crossing_year.py` |
| Exceedance table | `exceedance_table.{png,pdf}` | `exceedance_table.py` |

### B6. Superseded / quarantined (do NOT use)

- Pre-Sobol TreeSHAP / model-free-hybrid H-S figures + CSVs →
  `outputs/quarantine/20260528_treeshap_slr_underattribution/` (43 files + README).
  These are the OLD `shapley_hs_*` and `v5_hybrid_decomp_*` outputs that
  under-attributed emissions ~5×.
- Legacy TreeSHAP pulse-detail figures still present but secondary:
  `shapley_hs_lhs10k_pulse_4axis.{png,pdf}`, `..._top2_per_axis.{png,pdf}`
  (`shapley_hawkins_sutton_pulse.py`).

---

## Status legend
- **CURRENT** = the canonical deliverable as of 2026-05-29.
- 🔎 = script→output mapping from repo scan; re-verify the science status before use.
- Quarantined = superseded, kept for postmortem only.

## Related notes
- Group-Sobol build + decisions: `notes/handoff_2026-05-28b_group_sobol_hs.md`
- Parent poster/H-S context: `notes/handoff_2026-05-28_v5_hs_poster.md`
- ANOVA cross-check design: `notes/design_2026-05-28_anova_factorial.md`
- Ensemble scoping: `notes/memo_2026-05-28_hs_ensemble_scoping.md`
