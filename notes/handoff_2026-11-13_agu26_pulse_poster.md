# Handoff 2026-11-13: start the AGU26 sea-level pulse poster

Written by the Ladrillo GMD session, which stays on the paper. This file starts a separate session for the poster.
Read it cold, then the files in §3. **Do not touch the GMD paper's files (§6).**

## 1. The poster

- **Meeting:** AGU26 Fall Meeting, San Francisco, 6–11 December 2026 (registration PDF:
  `~/Documents/2026/AGUFallMeeting/Sarofim.AGU26RegistrationConfirmation.pdf`). That leaves about three weeks,
  including print lead time. **The presentation day and slot are not on disk; ask Marcus.**
- **Abstract:** session GC092, *MultiSector Dynamics: Uncertainty Characterization*. Working title "Slow Seas, Fast
  Gas: Coastal Damages from CO2 and CH4". Authors MC Sarofim, T Wong, V Srikrishnan, F Errickson, L Rennels. The text is
  the 08-03 draft in `~/Documents/2026/AGUFallMeeting/AGU26 Abstract Drafts.docx` (second entry). **The submitted
  version may differ; ask Marcus for it.**
- **Your role (`~/.claude/CLAUDE.md`, "Writing prose"):** produce the figure set and headline numbers, propose the layout,
  and leave text boxes as placeholders. Marcus writes the poster text. Affiliation on a poster: "Marcus C. Sarofim (NYU
  Marron Institute)".
- **Earlier poster workflow** (AGU Chapman, May 2026): a layout mock-up plus separate panel PDFs, handed to IEc for
  graphic polish only. See `SLR-RFF-BRICK/notes/poster_iec_handoff.md` and `handoff_2026-05-28_v5_hs_poster.md`.

## 2. What the abstract promises vs what exists

The abstract promises more than the pulse arc has built. **Your first deliverable is a table that maps each claim in
the abstract to an existing figure or number, or marks it as a gap.** Then take the gaps to Marcus. Do not close a gap
by choosing a method yourself (CLAUDE.md, "Methodological choices are explicit").

| abstract promise | state as found 11-13 (verify) |
|---|---|
| RFF-SP emissions and socioeconomics | The pulse arc runs on the **six van Vuuren CMIP7 markers** (vvVL, vvL, vvML, vvM, vvHL, vvH), not on RFF-SPs. A 07-09 plan proposed RFF-SP as primary; the 10-09 paper rulings moved to van Vuuren. **Which one backs the poster is Marcus's decision.** |
| FaIR and MAGICC climate | Present. The `/magiccclim` arms swap MAGICC's climate into the FaIR-driven SLR models. |
| BRICK, FACTS, MAGICC sea level | Present: Ladrillo L27 (v1.2), BRICK 2.0 (Zenodo v2.0.0 joint posterior since 10-15), MAGICC-SLR v7.5.3, FACTS v1.1.4 (wf1f + wf2f, annual output). The abstract says "BRICK"; whether to show Ladrillo, BRICK 2.0 or both is Marcus's call. |
| FrEDI coastal damages (properties, high-tide-flooding traffic delays, high-tide elder mortality) | **I found no pulse-arc FrEDI damage run.** The FrEDI SLR damage functions have known problems: non-monotonic by-level damages (`FaIRtoFrEDI/notes/call_prep_2026-10-12_slr_damage_functions.md`, Issue 1 parked by Marcus 10-12); an HTF error in the IEc build that overstates LA/MD/ME above 50 cm (FaIRtoFrEDI CHANGELOG 2026-10-12 (c); quarantine `outputs/quarantine/20261012_htf_200cm_zeroed/`); and a DE 50→100 cm drop that flips a marginal pulse's sign. Whether damages are in scope for AGU, and on which FrEDI build, needs Marcus. |
| Parametric vs structural uncertainty | The arc has per-draw intervals and between-model spreads, but I found no formal partition of variance. |
| SC-GHG implications | Not built for coastal damages. |
| "SLR damages may scale with cumulative CH4 emissions"; "cumulative CO2 commits continued SLR after temperatures stabilise" | Check against the duration results (`INDEX_cmp_pulse_dur.md`): CO2's pulse response has not peaked by 2300 in any model, and the duration t50 values are there. Whether the CH4 sentence is supported needs a test. |

## 3. Read before acting

1. `~/.claude/CLAUDE.md` (auto-loads): word choice, labels from constants, provenance labels, seeds recorded in the
   artifact, quarantine rule.
2. Memory (store under the FaIRtoFrEDI key; sub-indexes are not auto-loaded):
   - `INDEX_cmp_pulse.md` and `INDEX_cmp_pulse_dur.md`, the pulse arc. ⛔ Read their warnings before quoting any number.
   - `ch4_co2_pulse_paper` (the paper's question: what is consistent across models), `pulse_arc_rerun_20261009`,
     `brick20_zenodo_posterior_driver_scale` (every BRICK 2.0 pulse number moved on 10-15).
   - `facts_version_plan` (FACTS 1.1.4 for this poster; FACTS 2.0 maybe for the later paper),
     `facts_post2100_module_audit`, `facts_blind_to_a_pulse`, `facts_fittedismip_step_dependent`.
   - `magicc_greenland_sub_preindustrial` before any MAGICC 2300 number; `ch4_magiccclim_no_power`.
   - `INDEX_fredi_vehicle.md` and the `fredi-quirks` skill before any FrEDI run.
   - `consider_torch_first`: say the Torch-or-laptop verdict out loud before any long run.
3. `SLR-RFF-BRICK/notes/handoff_2026-10-09b_pulse_paper_facts.md`, the last full pulse-arc handoff. Its §3 numbers predate the 10-15 BRICK 2.0
   swap; re-read them from the processed CSVs.

## 4. Where the pulse arc lives

- Code and products: `FaIRtoFrEDI/magicc_comparison/`.
  - `pulse_stats.py` holds `VV_MARKERS` and `read_csv_exact`. Any ulp-level comparison must read through
    `read_csv_exact`.
  - Scripts: `pulse_duration_vv.py`, `fig_pulse_duration_vv.py`, `extract_pulse_vv_facts.py`,
    `diag_exchange_rate_paired_se.py`, `diag_te_ohc_mechanism_vv.py`, `build_pulse_doc_tables.py`.
  - Products: `processed/pulse_*` and `figures/pulse_duration_q{1,2,3}_*`.
  - Many older figures in `figures/` (SSP2-4.5, `brickfm`) are from earlier arcs. Check a figure's inputs before reusing
    it.
- SLR runners: `SLR-RFF-BRICK/julia/scope_slr_pulse_vv{,_brick2}.jl`. Per-draw files `outputs/pulse_*_draws_*.csv` are
  gitignored.
- FACTS: local checkout `CodeProjects/facts` (branch `slr-comparison-arm`, eb38c539; runs in Docker via colima).
- Draft section: `SLR-RFF-BRICK/deliverables/pulse_model_differences_L27_section.md`. Its tables are live, but its prose
  carries numbers typed on 09-07.

**Standing rules for this arc:**
- Spec: 1 GtCO2 or 0.01 GtCH4, pulse year 2030.
- Report the Lemoine-Traeger pair, never a median alone.
- Never average across FACTS workflows. Past 2100, show only the climate-driven FACTS modules.
- BRICK 2.0's Antarctic pulse response differs by about 2× between two posteriors of the same model; say so wherever
  it appears.
- Label FaIR's calibration from the cube files' provenance; do not assume it.

## 5. Suggested first steps

1. Ask Marcus:
   - the submitted abstract text, the presentation slot and the poster size;
   - van Vuuren or RFF-SP as the backbone;
   - whether FrEDI coastal damages are in scope for AGU, and on which build;
   - which SLR models to show.
2. Write the claims-vs-evidence table (§2).
3. Propose a panel layout with text placeholders, built from figures that already exist where possible.
4. Render poster-resolution panels into a new directory, for example `FaIRtoFrEDI/magicc_comparison/figures/poster_agu26/`.
   Take every title and label from named constants and stamp provenance on each panel.

## 6. Repo hygiene and what not to touch

- **The GMD session owns:**
  - `SLR-RFF-BRICK/deliverables/GMD*`, `deliverables/redline/` and `figures/paper/`;
  - `python/ladrillo_figs.py` and `python/plot_vv_*`;
  - the Ladrillo.jl repo.
  These produce the paper's figures. If the poster needs a variant, copy the script under a new name.
- **FaIRtoFrEDI** (branch `heat-ed-morbidity`): other sessions commit there.
  - Stage files by name; never use `git add -A`.
  - As of 10-09, the branch was unpushed by Marcus's hold. Ask before pushing.
- **SLR-RFF-BRICK** (branch `ladrillo-dev`) is shared with the GMD session. Commit only your own files, and add your own
  CHANGELOG entries.
- Put handoffs in `SLR-RFF-BRICK/notes/`. Log what was tried and abandoned in the CHANGELOG of whichever repo holds the
  code.
