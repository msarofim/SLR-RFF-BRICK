# Handoff — 2026-05-20 — BRICK Julia driver: per-component hindcast output + obs-driven runs

This handoff is a Julia-side spinoff from the Tony Wong follow-up
(`FaIRtoFrEDI/notes/handoff_2026-05-20_tony_wong_followup.md`).
A fresh Claude session should be able to pick up cold by reading this
note plus the Tony Wong handoff, the project's `CLAUDE.md`, and the
auto-memory in
`~/.claude/projects/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/memory/`.

> The Python side of the Tony Wong follow-up is in flight in a separate
> session: spliced obs OHC is shipped (see § 4 below), and the ensemble
> design pro/con writeup is at `notes/ensemble_design_proscons_2026-05-20.md`.
> Do NOT block this Julia work on the new ensemble — the per-component
> hindcasts can run on the existing LHS-10k metadata first; the new
> ensemble layers in later.

## 1. Goal

Two related Julia/BRICK changes:

1. **Modify `julia/run_mimibrick_paired_explicit.jl` to save year-by-year
   per-component output** (AIS, GIS, GSIC, TE) instead of only total SLR
   by year plus 2100 snapshots. Then re-run on the existing LHS-10k
   metadata to generate component hindcasts for comparison to obs.

2. **Build an obs-driven BRICK driver** that consumes
   `(GMST_obs, OHC_obs)` as input instead of FaIR-cube outputs.
   Compare obs-driven BRICK to FaIR-driven BRICK component-by-component
   against observed SLR component time series. The spliced obs OHC is
   already built and ready to consume (see § 4).

The end product is a set of side-by-side BRICK-vs-obs plots for each
component (AIS, GIS, GSIC, TE) over 1900–2024, plus a sign-flip-symmetry
report and methodological updates to the substack post.

## 2. Repo / environment state

- **Repo:** `https://github.com/msarofim/SLR-RFF-BRICK`
- **Working dir:** `~/Documents/2026/CodeProjects/SLR-RFF-BRICK/`
- **Julia driver:** `julia/run_mimibrick_paired_explicit.jl`
- **Julia env:** `Project.toml` / `Manifest.toml` in `julia/`. MimiBRICK
  installed via `using MimiBRICK`. Check `Manifest.toml` for pinned version.
- **Where it runs:** NYU Torch HPC. SSH config via `ssh torch` proxy-jumping
  through `gw.hpc.nyu.edu`. SLURM template at
  `slurm/submit_lhs10k_brick_pipeline.sh`. See memory
  `reference_nyu_hpc.md` and the `nyu-torch-hpc` skill for partition cheat
  sheet, /scratch vs /home conventions, KEX-algorithm gotchas, etc.

## 3. Critical Julia-side conventions (from existing driver)

From `run_mimibrick_paired_explicit.jl`:

- BRICK consumes **two trajectories per cell**:
  - `:surface_temperature → :temperature`: GMST anomaly, °C
  - `:thermal_expansion → :ocean_heat_interior`: cumulative OHC, **10²² J**
- Input cubes are mmap'd `.npy` files (preferred) or `.npz` files with
  keys `gmst_traj_rff`, `ohc_traj_rff`, indexed as `(RFF, cfg, [seed,] year)`.
- The driver loops over `(RFF, cfg)` cells; per-component output is
  computed but currently aggregated to total SLR before saving.
- Year axis: 1850-2300 (451 years) — matches the FaIR cube layout
  (`years` key in `outputs/rff_baseline_stoch_to2300.npz`).
- BRICK posterior: drawn from the 10,000-member Wong calibration
  posterior. Currently 1 posterior draw per cell, paired-by-cell across
  baseline + pulse cubes (so paired marginals are clean).

## 4. What's already in place (Python side, do not redo)

- **Spliced obs OHC** (Zanna 2019 PNAS + Cheng IAPv4.2):
  `data/observations/ohc_spliced_zanna_cheng.csv`
  - 1850–2025, units **10²² J**, cumulative since FaIR's 1750-zero.
  - Pre-1870: FaIR ensemble mean; 1870–1960: Zanna shifted to FaIR(1871);
    1961–2025: Cheng with 5-yr-windowed constant offset.
  - Provenance memory: `project_ohc_splice_provenance.md`.
  - Sensitivity figure: `outputs/ohc_splice_sensitivity.png`.
  - Reproducible builder: `python/build_ohc_spliced.py`.
- **IGCC observed GMST** (4-dataset mean):
  `data/observations/igcc2024_gmst_4dataset_mean.csv`. This is the canonical
  obs-GMST. Pair it with the spliced OHC when running obs-driven BRICK.
- **Existing LHS-10k metadata + FaIR baseline cube** for the
  component-hindcast workstream:
  - `outputs/lhs_pilot_metadata_*.csv`
  - `outputs/rff_baseline_stoch_to2300.npz` (490×841×451, GMST+OHC+ERF)
  - `outputs/rff_pulse_stoch_to2300.npz` (+1 GtC at 2030 pulse)
  - `outputs/rff_pulse0p01gtc_stoch_to2300.npz` (+0.01 GtC small pulse)
  - **CH₄ pulse + negative-pulse cubes do not yet exist** — defer to the
    new-ensemble work (handoff `FaIRtoFrEDI/notes/handoff_2026-05-20_tony_wong_followup.md`).

## 5. Suggested first steps

### Phase A — per-component output (do this first, no obs splice needed)

1. **Read the existing driver** to find where it currently computes per-
   component values (search for `:thermal_expansion`, `:antarctic_icesheet`,
   `:greenland_icesheet`, `:glaciers_small_icecaps`). Each component has its
   own Mimi sub-model that produces an annual time series — the driver
   currently sums them.

2. **Modify the save block** so each component is written to a separate
   CSV column (or a separate file per cell, if memory is a concern).
   Suggested schema for the output CSV per scenario:
   - `cell_id, year, slr_total_cm, slr_te_cm, slr_ais_cm, slr_gis_cm, slr_gsic_cm`
   - One row per (cell_id, year). Easy to filter in Python afterwards.

3. **Run on existing LHS-10k metadata** (don't regenerate the FaIR cube).
   Use `outputs/lhs_pilot_metadata_*.csv` + `rff_baseline_stoch_to2300.npz`.
   Single-scenario re-run; ~10–15 min on Torch.

4. **Validate**: total SLR computed by summing the new component columns
   must match the existing total-SLR output to ~1e-10 (it's just an
   accounting change, not a model change). This is a bit-identical check —
   do it before trusting any plots.

5. **Plot AIS/GIS/GSIC/TE component bands vs Wong-weighted observation
   data** (Tony will share specific obs sources; in the meantime use the
   existing obs sources in `data/observations/` as proxies).

### Phase B — obs-driven BRICK driver

6. **Build a parallel driver** (`julia/run_mimibrick_obs_driven.jl`) that:
   - Reads `data/observations/ohc_spliced_zanna_cheng.csv` (year, ohc_1e22J).
   - Reads `data/observations/igcc2024_gmst_4dataset_mean.csv` (year, gmst).
   - Reads a BRICK posterior CSV (existing Wong calibration posterior).
   - For each BRICK posterior draw, runs BRICK with `(obs_GMST, obs_OHC)`
     instead of `(FaIR_GMST, FaIR_OHC)`.
   - Saves year-by-year per-component output (same schema as Phase A).
   - **Historical period only** for now: extend post-obs (2024 onwards)
     after the historical comparison lands (Marcus's call per planning).
   - For pre-obs years (1850–1869) the spliced CSV uses the FaIR ensemble
     mean as a placeholder — that section is *not* obs, document this in
     plot captions.

7. **Run 3 combinations** per Tony's specific ask:
   - (FaIR GMST, FaIR OHC) — existing baseline
   - (obs GMST, FaIR OHC) — isolate surface-T contribution
   - (FaIR GMST, obs OHC) — isolate OHC contribution
   - (obs GMST, obs OHC) — fully observation-driven

8. **Plot component-by-component comparisons**: which combination matches
   each component obs best? This is the diagnostic Tony explicitly asked
   for.

### Phase C — sign-flip-symmetry report

9. **Component-by-component sign-flip** using the existing +0.01 GtC small
   pulse (`rff_pulse0p01gtc_stoch_to2300.npz`) and its negative counterpart
   (does NOT yet exist — generate it on Torch as a quick one-off if needed,
   or defer to the new-ensemble work which includes ±0.01 by design).
   - For each component, compare +Δ marginal to −Δ marginal in median + 5/95%.
   - Linear-regime expectation: antisymmetric within ~10%.
   - AIS expectation: +Δ has a fat tail (BRICK tips); −Δ does not.
     Flag clearly as a physical finding, not a bug.

## 6. Open questions before launch

- **Per-component output schema**: one-CSV-per-scenario (wide) vs
  one-CSV-per-component (long)? Wide is friendlier for plotting; long
  scales better if more components are added later.
- **Storage location**: keep component CSVs in `outputs/` next to the
  existing total-SLR CSVs, or carve out `outputs/components/`? Either is
  fine; pick one and be consistent.
- **Pre-1870 obs-driven runs**: spliced OHC uses FaIR mean for 1850–1869.
  Cleanest scientifically is to start the obs-driven run at 1870 and let
  BRICK spin up briefly. Alternative: run from 1850 using the FaIR-mean
  placeholder and document the caveat.
- **Tony's component obs sources**: not yet received. Until they land,
  use whatever component obs the literature gives (Frederikse 2020 for
  AIS/GIS/GSIC; CSIRO/AVISO/Dangendorf for total). Note in any plot what
  obs reference is being used.

## 7. Sanity tests (mandatory before headline figures)

Per `feedback_apply_sanity_tests_for_pulses.md` memory + user-level
`CLAUDE.md` §"Sanity tests for paired/marginal experiments":

1. **Zero-perturbation**: feed identical GMST/OHC to two BRICK runs with
   different seeds — paired diff must be bit-identical (1e-15).
2. **Component decomposition closure**: Σ components == total SLR to
   1e-10. (This is the Phase A validation step.)
3. **Sign-flip symmetry** (Phase C).
4. **First-principles magnitude**: 2100 thermosteric SLR ~7-15 cm for
   ~50 ZJ heat content gain — check the obs-driven TE component lands in
   the expected range.

If any of these fail, treat as bug, not physics, until disproven
(`Implausible result = bug` discipline).

## 8. Pointers

- `julia/run_mimibrick_paired_explicit.jl` — current driver to modify
- `julia/compute_lB_per_post.jl` — adjacent Julia utility, may have
  patterns for posterior-loop output writing
- `python/scripts/substack/obs_overlay_slr.py` — Python overlay code that
  will eventually plot Julia outputs against obs (don't modify, but
  understand its expected schema)
- `python/apply_wong_weights.py` — Wong-weighting machinery; unchanged
  for this work
- `BRICK_notes.md` — repo-level notes on BRICK structure
- `METHODS.md` — methods text that may need updates after this work

## 9. After this work lands

Two pending threads in the parent Tony Wong handoff that this work feeds:

- **Substack post correction**: replace "BRICK historical fit" framing
  with multi-obs framing once component comparisons exist.
- **AGU Chapman poster** (memory `project_agu_chapman_poster.md`): the
  per-component panel currently shows total SLR + obs; with this work
  it can be replaced with per-component fits if the obs comparison
  goes well. Deadline ~2026-06-01 for `v1.0-poster-agu-chapman` tag.

Both wait on this Julia work, not the new-ensemble work.
