# Handoff — 2026-05-19 — Substack post & poster (AGU Chapman SLR conference)

Picks up from `notes/handoff_2026-05-18_substack.md`. The intervening session
finished the AR6 bias-correction sweep, switched the observational anchors,
resolved the pulse-size sensitivity question, and rebuilt the substack figure
set. This note carries forward everything needed to (a) finish the substack
post and (b) rebuild the poster cleanly if reviewers request changes ahead
of the AGU Chapman SLR conference. IEc is providing graphics polish on the
near-final poster before print.

---

## 1. Methodological decisions locked in this session

### 1.1 GMST observational anchor: IGCC 2024 consensus (NOT Berkeley Earth alone)
- FaIR-v1.4.1 was calibrated to IGCC; we now use IGCC as the primary obs.
- 2015–2024 mean rel 1850–1900 = **+1.254 °C** (4-dataset consensus:
  HadCRUT5 + Berkeley Earth + GISTEMP + NOAAGlobalTemp).
- Replaces the earlier BE-only anchor of +1.323 °C.
- Encoded as constant `OBS_RECENT_REL_PI = 1.254` in every script that frames
  warming rel preindustrial. Search the repo for that string before changing.

### 1.2 AR6 bias correction (applied everywhere "rel PI" appears)
Each FaIR trajectory is rebaselined at its OWN 2015–2024 mean and then shifted
to the IGCC observed anchor:
```
cube_pi = cube - traj_recent[:, :, None] + OBS_RECENT_REL_PI
```
This respects observed present-day warming. FaIR ensemble-median modelled
2015–2024 is +1.04 °C rel PI vs IGCC +1.254 → ~0.21 °C bias.

### 1.3 IGCC line source: **Trewin's raw 4-dataset average**, not Walsh's fitted p50
- File: `data/observations/igcc2024_gmst_4dataset_mean.csv` (Trewin, raw).
- Walsh's `total_p50` in `igcc2024_gmst_with_uncertainty.csv` is the
  attribution-method regression fit — ENSO is absorbed into the residual term,
  so the 2024 peak is smoothed away.
- We use Walsh's band WIDTH (p95−p05 about p50) centered on Trewin's raw value
  → honest annual obs uncertainty around the actual observed mean.

### 1.4 SLR observational anchor: NOAA STAR for recent, Dangendorf 2024 for history
- Replaces CSIRO/AVISO across figures and importance weighting.
- Dangendorf et al. 2024 (ESSD, Zenodo `10.5281/zenodo.10621070`) for
  pre-altimeter historical GMSL reconstruction.
- NOAA STAR satellite altimetry (1993–2024) for recent observations.
- 2015–2024 anchor for SLR (poster Panel B): **+6.38 cm rel 2000** (NOAA STAR).
- `apply_wong_weights.py` and `julia/compute_lB_per_post.jl` default to
  `--obs dangendorf`. CSIRO retained as fallback flag.
- Known inconsistency to flag in any methods text: importance weights on
  Torch were re-run with Dangendorf, but if you find any older artifact
  paths still reading CSIRO, they are stale.

### 1.5 Pulse-size convergence — CO2 marginal SLR
- 1 GtC pulse triggers AIS tipping in ~5% of paired draws (one outlier,
  row 201 with baseline `ais_2100 = 29.6 cm`, tips at any non-zero pulse).
- **Median is pulse-size invariant** (~0.064 cm/GtC at 2150 across 0.01,
  0.1, 1.0 GtC pulses); **mean is contaminated** by tipping at the larger
  pulse sizes.
- For linear SC-SLR sensitivity → use **median** from the 0.01 GtC pulse.
- CH4 is fully linear at 1 Tg already (all pulse sizes give same median &
  p95).
- AIS tipping classifier: baseline `ais_2100 > 20 cm` → tipping-prone.

### 1.6 Units convention — everywhere
- **All SC-GHG figures and tables are per tonne CO2** (not per tonne C).
- Conversion: `GTC_TO_GTCO2 = 44.0/12.0 = 3.667`. CO2 marginal in cm/GtC →
  divide by 3.667 to get cm/GtCO2.
- CH4 → CO2-equivalent via **AR6 GWP100 = 27.9** (midpoint of fossil 29.8 and
  non-fossil 27.0). `TG_CH4_PER_GTCO2EQ = 1000 / 27.9 = 35.84`.
- Constants live at the top of `pulse_responses_clean.py`. Do not duplicate.

---

## 2. Substack post — figure inventory

All under `outputs/substack/`. Re-run scripts under
`python/scripts/substack/`. Captions cite IGCC 2024 anchor and FaIR ensemble
size (398 RFFs × 841 configs = 334,718 trajectories per year) consistently.

| Figure | Script | What it shows |
|---|---|---|
| `obs_overlay.png` (2-panel) | `obs_overlay.py` | FaIR band vs IGCC + BE, rel 1850–1900 and rel 2015–2024 |
| `obs_overlay_recent.png` | `obs_overlay_recent.py` | Single-panel rel 2015–2024, secondary axis = rel PI |
| `updated_hawkins_sutton.png` | `updated_hawkins_sutton.py` | GMST 3-way H-S decomposition (emissions/climate/internal) |
| `updated_hawkins_sutton_slr.png` | `updated_hawkins_sutton_slr.py` | 4-way SLR H-S (adds BRICK posterior) through 2150 |
| `obs_overlay_slr.png` | `obs_overlay_slr.py` | FaIR×BRICK band vs Dangendorf + NOAA STAR, rel year 2000 |
| `exceedance_table.png` | `exceedance_table.py` | P(GMST > T) at 2050/2100/2150 |
| `exceedance_crossing_year.py` | `exceedance_crossing_year.py` | p5 / median / p95 crossing year per threshold |
| `median_crossing_year.png` | `median_crossing_year.py` | Just the median crossing year |
| `pulse_responses_clean.png` | `pulse_responses_clean.py` | 2×2 grid CO2/CH4 × GMST/SLR, median + 5–95% |
| `pulse_convergence.png` | `pulse_convergence.py` | Multi-pulse-size convergence diagnostic |

**Table styling** (all three table scripts):
- Single-line header: `"Threshold (°C rel. preindustrial)"`
- No `fig.suptitle` — table dominates the PDF.
- Caption: `va="bottom"`, explicit `\n` for 2-line wrap, 8.5 pt italic grey.
- Layout: `fig.tight_layout(rect=[0, 0.10, 1, 1.00])` (or 0.14 for median).
- Header font: 10 pt (set per-cell in the styling loop).
- Figsize: 9.0 × 4.0 for 4-col tables, 7.5 × dynamic for median_crossing.

**Key numbers for the post body:**
- Median GMST crossing years (rel PI, IGCC anchor): see
  `outputs/substack/median_crossing_year.csv` — refresh before copying into
  the draft prose.
- 2050 99th-percentile *lower* bound (cold tail): pull from the cube; if I
  don't see it in a CSV, recompute via
  `np.quantile(cube_pi[:,:,iy].ravel(), 0.01)` at iy=2050.
- BRICK uncertainty interpretation (last user observation): climate-response
  uncertainty dominates (~50%) because AIS tipping is *gated* by whether
  emissions+climate cross the threshold; the threshold value itself is
  tightly constrained by Wong importance weighting against observed GMSL.
  BRICK share starts ~21–28% and decreases to ~14% by 2150.

---

## 3. Poster — current state & rebuild recipe (AGU Chapman SLR conference)

### 3.1 Layout
`layout_mockup.pdf` in repo root. Four-panel: A (overview), B (FaIR vs obs
GMSL), C (H-S), D (pulse responses with inset).

### 3.2 Panel D inset — REPLACED this session
- Old: 1 GtC pulse marginal with heavy right tail from AIS tipping.
- New: 0.01 GtC small-pulse **median + 5–95%**, in **cm per GtCO2**
  (Y-axis label: `"ΔSLR (cm per GtCO₂)"`).
- Script: `python/scripts/run_pulse_4way_slr_decomp.py`.

### 3.3 Panel B obs anchor — UPDATED
- Anchor: +6.38 cm rel 2000 (NOAA STAR).
- Historical pre-1993: Dangendorf 2024.
- Helper: `observed_gmsl_recent_rel_2000()` in `poster/slr_band.py` reads
  `data/observations/nasa_gmsl_annual.csv` directly.

### 3.4 If reviewers ask to change the obs anchor again
- All instances of the anchor are at the top of each script as a named
  constant. To switch obs source, change the constant + the caption string
  it interpolates into. The "labels derive from named constants" rule
  prevents silent drift.
- Touch-points for GMST anchor: `OBS_RECENT_REL_PI` in `exceedance_table.py`,
  `exceedance_crossing_year.py`, `median_crossing_year.py`,
  `updated_hawkins_sutton.py`, `obs_overlay_recent.py`,
  `python/figure4_gmst.py`, `python/halfdeg_exceedance.py`.
- Touch-points for SLR anchor: `poster/slr_band.py`, `obs_overlay_slr.py`,
  `apply_wong_weights.py`, `julia/compute_lB_per_post.jl`.

### 3.5 If reviewers ask about pulse-size sensitivity
- Answer: median is pulse-size invariant (we verified at 0.01, 0.1, 1.0 GtC
  pulses); mean diverges because of tipping at large pulses.
- Diagnostic figure: `outputs/substack/pulse_convergence.png`.
- Decomposition: a small population of baseline-AIS-tipping-prone draws
  (`ais_2100 > 20 cm`) drive the divergence; the Lemoine-style decomposition
  (linear sensitivity + tipping insurance premium) is sketched but not
  finalized — see optional follow-up below.

### 3.6 If reviewers challenge the BRICK uncertainty being small
- See §2 last bullet. BRICK posterior is tightly constrained because the
  Wong AR(1) importance weights penalize draws that mis-fit observed GMSL.
  The remaining BRICK spread is mostly *threshold value uncertainty*; the
  *gating* of tipping is dominated by climate-response uncertainty.

---

## 4. Pending / optional follow-ups

1. **Lemoine probabilistic decomposition** — linear sensitivity + tipping
   insurance premium. Sketched but not built into a standalone script. Worth
   doing if reviewers want to see the tipping contribution quantified separately
   from the linear marginal. Inputs already exist (the 1 GtC paired CSV with
   `ais_2100_cm` column).
2. **Legacy poster scripts** `pulse_response_split.py` and
   `co2_pulse_marginal.py` — still in old per-tCO2-vs-per-GtC mixed units.
   Not in the current poster layout, so deferred. Sweep to per-tCO2 if/when
   reactivated.
3. **`apply_wong_weights.py` obs alignment** — currently uses Dangendorf for
   SLR weights, which is consistent with our SLR obs choice but separate
   from the GMST IGCC choice. No action needed unless reviewers ask.

---

## 5. Non-obvious state to know

- **Torch HPC results staged**: importance-weighted runs against Dangendorf
  completed; if any artifact path still reads CSIRO, treat as stale.
- **Walsh `total_p50` is a fitted curve, not raw**: use Trewin's
  `igcc2024_gmst_4dataset_mean.csv` for the IGCC line; use Walsh only for
  the cross-dataset uncertainty band width.
- **Paired CSV includes `ais_2050_cm`, `ais_2150_cm`, `ais_2300_cm`** columns
  now (added in `julia/run_mimibrick_paired_seeded.jl`) — needed for the
  tipping classifier.
- **CLI flag rename**: `--be-recent-rel-pi` → `--obs-recent-rel-pi` in
  `figure4_gmst.py` and `halfdeg_exceedance.py`. Old flag kept as deprecated
  alias.
- **`.applymap` deprecated** in newer pandas → use `.map` element-wise.

---

## 6. Open question for Marcus (carried from last turn)

The user observation about BRICK uncertainty being small despite AIS being
important was correctly diagnosed: AIS tipping is *gated* by emissions +
climate sensitivity (large variance contributors), while the BRICK posterior
parameters governing the threshold value itself + post-tipping AIS dynamics
are tightly constrained by Wong importance weighting against observed
historical GMSL. The data supports the user's interpretation. No action
needed unless this becomes a methods-section talking point — in which case
the H-S SLR CSV (`outputs/plots/hawkins_sutton_slr_4way.csv`) has the
fractions to cite directly.
