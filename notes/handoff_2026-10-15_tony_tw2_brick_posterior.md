# Handoff 2026-10-15: Tony's TW2 draft and the BRICK 2.0 posterior question

> ⚠ **Superseded by `handoff_2026-10-15b_brick20_swap_tw2_pass.md`.** §2 is decided (the arm moved to the Zenodo joint
> file), §3 steps 1-3 are done, and the "deferred conditioning rerun" below was already done on 10-08k.

Follows `handoff_2026-10-09b_pulse_paper_facts.md`. That handoff's job (add FACTS to the pulse analysis) is done.

Start cold from this file, then read:
- memory `brick20_zenodo_posterior_driver_scale` and `ch4_co2_pulse_paper`;
- `notes/tony_tw2_triage_2026-10-15.md` (the comment-by-comment triage, with receipts);
- `INDEX_slr_post.md` (GMD draft state) and `INDEX_cmp_pulse_dur.md` (the FACTS pulse rulings).

## 1. What this session did

### 1a. FACTS added to the CH4-vs-CO2 pulse analysis (2026-10-09)

**Feasibility first** (SLR CHANGELOG 10-09f; FTF `magicc_comparison/diag_facts_pyear_step.py`):
- An annual FACTS run costs ~60 s per experiment, the same as decadal.
- FittedISMIP (FACTS's Greenland) is the only step-dependent module: it Euler-integrates its rate law at the output step.
- Under Marcus's 09-12c rule, most of FACTS's 2300 pulse total was not climate-driven.

**Marcus's three rulings (10-09):**
1. 09-12c binds the pulse arc.
   - FACTS enters with totals and every component through 2100.
   - LARMIP enters through 2150.
   - Thermal expansion (tlm) and glaciers (ar5glaciers) enter through 2300.
2. FACTS is re-run at annual output, and every FACTS pulse number comes from those runs.
3. wf1f and wf2f are FACTS's pulse response, never averaged.

**Done** (SLR CHANGELOG 10-09g; FTF CHANGELOG 10-09g):
- **Annual runs.** 21 experiments at `pyear_step: 1` (`facts/experiments/global.shared.<m>.<arm>.2300.step1.n200`).
  - bamber19 and wf4 are not run: bamber19 fails at step 1 and is blind to a pulse.
- **Extractor.** It applies 09-12c via the imported `ladrillo_figs.FACTS_CLIMATE_DRIVEN`.
  - Outside the rule, every pulse statistic is NaN, with a `climate_driven` column.
  - It writes per-year wf1f / wf2f paths.
- **Downstream.**
  - FACTS te and glaciers enter the duration table, Fig 2 (b)–(c) and T5.
  - The doc tables print `n/a (09-12c)` for FACTS beyond the rule.
- **Gates.** All pass; every new gate is mutation-tested.
  - Every non-FACTS row of the regenerated tables is identical to the quarantined copies.
  - Quarantine: `FaIRtoFrEDI/magicc_comparison/processed/quarantine/20261009_facts_pulse_decadal_unfiltered/`.
- **Retracted:** the FACTS 2300 exchange rates 0.817 / 0.686 and the FACTS H/VL "0.52x".

**Correction made in-session.** I first told Marcus the step effect on FACTS pulse totals was ~0.4 %. That came from one
CO2 arm. For CH4, FittedISMIP's 2100 pulse was 10–15 % low at step 10, which made wf1f totals 2.8–4.0 % low. The
corrected numbers are in the CHANGELOG, the quarantine README and memory `facts_fittedismip_step_dependent`.

**Readings for the pulse paper** (prose is Marcus's):
- Thermal expansion agrees across FACTS, Ladrillo and BRICK 2.0 on the FaIR climate: CH4 t50 2135–2141 and end/peak
  0.434–0.437 in all three.
- Glaciers do not agree: FACTS's AR5 glaciers decay more slowly (CH4 end/peak 0.65 vs 0.39–0.53).

### 1b. Tony's TW2 draft and his email (2026-10-15)

`deliverables/GMD.Ladrillo.v1_forTonyreview_TW2.docx` was read only, never edited.
- It holds TW1's 54 comments plus 24 new ones and 119 new tracked edits, through Results and Discussion.
- Triage: `notes/tony_tw2_triage_2026-10-15.md` (SLR `ad84c1f`).

Two flags:
- **Comments 362–363.** His suggested sentence for the 1.21x / 1.10x ocean-heat paragraph restates the attribution
  retracted on 10-01. Use the queued correction (`handoff_2026-10-01c_gmd_round.md` §1c item 1) instead.
- **2300 figure caption.** He rewrote it from the 2100 caption ("seven workflow totals"). At 2300 there are no "e"
  workflows and, under 09-12c, no FACTS totals.

## 2. The open decision: which BRICK 2.0 posterior (Marcus has not ruled)

**Tony's email (10-15):**
- The May-22 file we use was a work in progress.
- Cite the Zenodo MimiBRICK v2.0.0 set (10.5281/zenodo.20592337) instead; it "shouldn't be TOO far off".
- Likely differences: fixed seeds, explicit normalization periods, and perhaps Wang et al. (2024) GMSL.

**Our 10-08 measurement disagrees for thermal expansion** (SLR CHANGELOG 10-08h).
- On FaIR forcing, Zenodo gives SSP2-4.5 TE of 6.6 cm at 2100 against 19.4 cm with ours.
- The TE hindcast RMSE is 1.97 vs 0.52 cm. Other components agree within ~15 %.

**The signature.**
- The `thermal_alpha` median ratio (0.054 / 0.158 = 0.34) equals the TE ratio at both 2100 and 2300.
- TE = α × ΔOHC, and v2.0.0 calibrates BRICK coupled to SNEASY/DOECLIM. So α is plausibly fitted against DOECLIM ocean
  heat whose changes are ~2.9x FaIR's.
- Seeds and normalization periods cannot produce a proportional 3x.
- The code tagged `v2.0.0` calibrates GMSL to Church & White (no Wang file), so a Wang-calibrated posterior would come
  from later code.
- This is a hypothesis; nothing has tested it.

**Options:**
- (a) Tony publishes the May-22 file, so the paper's numbers stand.
- (b) Move the BRICK 2.0 arm to Zenodo: every BRICK 2.0 number in the GMD and pulse papers moves, and TE moves about 3x.
- (c) Settle first whether the Zenodo α is usable with FaIR ocean heat. Claude recommended (c).

**Tests for (c)** (not run; no Zenodo file is on disk):
1. Run the Zenodo draws in their own coupled SNEASY-BRICK hindcast and check TE against observations.
2. Compare DOECLIM's 1900–2020 ΔOHC under those draws with FaIR's; the hypothesis predicts ~2.9.
3. Or ask Tony which ocean-heat driver and units the v2.0.0 TE was fitted to.

Notes on the inputs:
- The 10-08 download sat in an old session scratchpad and is gone. Re-downloading needs Marcus's OK.
- The MimiBRICK source with the `v2.0.0` tag is local at `~/Documents/2026/CodeProjects/MimiBRICK.jl`.

**Why this comes first:** a switch to (b) changes every BRICK 2.0 number. The docx pass should wait for the ruling.

## 3. Next steps, in order

1. Marcus rules on §2 (and may email Tony the driver question).
2. **If (b):** rerun the BRICK 2.0 arm.
   - The deferred record-conditioning rerun rides with it (CHANGELOG 10-08g).
   - Also update `Ladrillo/tools/fetch_brick20_posterior.sh` (URL and sha256) and its header comment.
3. **The GMD docx pass, on Tony's TW2 file** (never an older build). It carries:
   - the `handoff_2026-10-01c_gmd_round.md` §1c items 1–8;
   - the `handoff_2026-10-08b_ladrillo_github.md` §3 item 3 list (v1.1 / v1.2 numbers, label, Table A2, Intro 1.4x,
     tap statistics, conditioning qualifier);
   - the factual answers in the triage note.

   Marcus decides the framing items:
   - 390: one ensemble throughout, and Fig 5's "Fixed arm";
   - 347: the independent-errors line;
   - 326: the LWS sentence;
   - 367: bars text into the caption.

   Build with the existing tracked-edit tooling (`redline/r1001f/trackedit.py`, which has the fixed `_in_tracked`).
   Never write docx XML with ElementTree.
4. **Pulse-paper prose flag (Marcus's).** `deliverables/pulse_model_differences_section.md` says wf1f and wf2f differ by
   about 2x at 2300. Under 09-12c there is no FACTS 2300 total. The template also still types ~15 numbers from 09-07.
5. **Memory hygiene.** `INDEX_cmp_pulse.md` is at ~16.9 KB of its 18.4 KB ceiling. Split it (paper vs arc mechanics)
   before adding to it.

## 4. Files

**Created this session:**
- SLR: `notes/tony_tw2_triage_2026-10-15.md`; CHANGELOG 10-09f, 10-09g, 10-15.
- FTF:
  - `magicc_comparison/diag_facts_pyear_step.py` → `processed/diag_facts_pyear_step_vvM.csv`;
  - 28 `processed/pulse_facts_paths_*_{wf1f,wf2f}.csv`;
  - the quarantine directory above;
  - CHANGELOG 10-09f, 10-09g.
- facts: `run_vv_pulse_facts_step1.sh`; 21 `.step1` experiment configs.

**Modified:**
- FTF `magicc_comparison/`: `extract_pulse_vv_facts.py`, `pulse_duration_vv.py`, `diag_te_ohc_mechanism_vv.py`,
  `build_stage4_crossmodel_table.py`, `build_pulse_doc_tables.py`, `fig_pulse_duration_vv.py`, and their outputs.
- facts: `build_pulse_climate_vv.py` (`--step=N`), `build_shared_configs.py` (reads `PyearStep`; drops bamber19 and wf4
  together).
- SLR: `deliverables/pulse_model_differences_tables.md`, `..._L27_section.md` (generated).

**Memory:**
- new: `facts_fittedismip_step_dependent`, `facts_pulse_2300_is_construction`,
  `brick20_zenodo_posterior_driver_scale`;
- updated: `ch4_co2_pulse_paper`, `scenario_split_is_antarctic`, `INDEX_cmp_pulse_dur`, `INDEX_cmp_pulse`,
  `INDEX_slr_post`.

## 5. Non-obvious state

- **Commits.**
  - SLR-RFF-BRICK `ladrillo-dev` at `ad84c1f`, pushed.
  - FaIRtoFrEDI `heat-ed-morbidity` is level with origin. My 10-09 commits (`108e5b2`, `db1f4f0`) are in it; another
    session pushed it since.
  - facts `slr-comparison-arm` at `eb38c539`, local only (its remote is upstream's).
  - Ladrillo (`~/Documents/2026/CodeProjects/Ladrillo`, `main`) at `bfaefd7`; unchanged this session.
- **Another session commits to FaIRtoFrEDI on the same branch** (CCX pulse / ZEC work on 10-12 to 10-15, EGU memo files).
  Stage files explicitly there.
- **facts `.gitignore` was already modified** before this session, by someone else. It is not staged; leave it.
- **Feasibility test dirs** `facts/experiments/steptest.vvM.{pbase,pco2}.2300.annual` are untracked on purpose:
  `diag_facts_pyear_step.py` reads them as its receipt.
- **The step-10 FACTS pulse experiments stay in place** as "FACTS as published" (AR6 runs step 10). They are not the
  pulse basis.
- **The pulse-paper downstream chain**, in order, run from `FaIRtoFrEDI/` with
  `~/miniforge3/envs/slr-refresh-2025/bin/python`:
  1. `build_stage4_crossmodel_table.py`
  2. `diag_scenario_dependence_2300.py`
  3. `diag_magiccclim_module_vs_climate.py` ×4
  4. `pulse_duration_vv.py`
  5. `fig_pulse_duration_vv.py`
  6. `diag_igmst_ordering_vv.py`
  7. `diag_te_ohc_mechanism_vv.py`
  8. `build_pulse_doc_tables.py`

  The FACTS extractor runs first, with `~/climate-env`.
- **One judgment call Marcus may revisit.** The 09-12c rule is stated at horizons only. Per-year cutoffs use the last
  horizon at which the rule keeps a module, which puts LARMIP at 2150. For a 2030 pulse its 200-yr kernel keeps the
  pulse's forcing until 2229. No table uses LARMIP past 2100 yet.
- **Tony's docx comment extraction scripts** are in the old session scratchpad (gone). They are short lxml readers:
  comments with anchors and replies, tracked insertions and deletions, and the accepted-text paragraph for a comment id.
