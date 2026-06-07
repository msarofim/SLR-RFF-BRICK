# DEFERRED: remake 2 SLR figures with the new MimiBRICK version (peer-review-paper time)

**Status:** DEFERRED by Marcus 2026-06-04. **Do NOT do now.** The AGU-Chapman poster is already
printed and the substack is already posted, so there is no live dependency. Remake these only when
we write a peer-reviewed paper for this material.

## Context
The pipeline currently runs **MimiBRICK v1.0.1**. Tony Wong's vehicle-SLR work (and EPA) use
**v1.2.0**; newest is **v1.2.1** (LWS-projection bug fix + OHC ref-period + projection-forcing
updates). Reproduction validated 2026-06-04 (see FaIRtoFrEDI memory `project_wong_slr_reproduction`).
Isolated Julia envs built locally (`FaIRtoFrEDI/external/wong_slr_repro/`) and on Torch
(`/scratch/ms17839/FaIRtoFrEDI/wong_slr_repro/{env_v121,env_v120}`).

## Figures to remake (with the NEW BRICK version)
1. **Historical component-comparison figure** — BRICK SLR components vs observations (historical).
   - Script: `python/scripts/substack/component_overlay_tony_style_extended.py`
     (alternates: `component_overlay_obsdriven.py`, `component_overlay_tony_style.py`).
   - Why version matters: v1.2.1's LWS-projection fix + OHC ref-period change shift the
     component (esp. LWS / GIS / TE) trajectories.
2. **Rennels SSP2-4.5 7-panel future-components figure**.
   - Scripts: `python/scripts/rennels/rennels_7panel_figure.py`; rebuild cubes first via
     `python/scripts/rennels/rennels_build_ssp245_cubes.py`.
   - See `notes/handoff_2026-05-30_rennels_slr_7panel.md` + FaIRtoFrEDI memory `project_rennels_ssp245_7panel`.

## Version choice (decide at paper time)
Use **v1.2.1** (newest) unless matching EPA rule-timing, in which case **v1.2.0**. Both are
published. The BRICK driver pipeline (`julia/Manifest.toml`) would need re-pinning to the chosen
rev (currently v1.0.1) and the conditional-BRICK cubes / posterior re-run on that version.
