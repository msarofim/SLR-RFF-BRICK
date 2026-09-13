# Handoff — L24 documentation: 09-11 → 09-13 arc closed; NEXT = SLEIP Table 2 categories for Ladrillo, then back to the pulse analysis

**Start here.** Continues `handoff_2026-09-11b_four_tasks_done.md` (its four tasks are done and
superseded by everything below). **Read this note, `INDEX_cmp.md` and `INDEX_cmp_magicc.md` before
touching the deliverable, the comparison figures or FACTS.** CHANGELOG entries 09-11c → 09-12g are
the primary record; this note is the map.

**STATUS:** `SLR-RFF-BRICK` `ladrillo-dev` clean at e078504, **NOT PUSHED**; `facts`
`slr-comparison-arm` clean at 2f007423 (modified `.gitignore` only). ⚠ **A concurrent SLEIP-review
session commits to the same branch** (c1be6c4, 8174c26 on 09-12 — see §4): run
`git -C ~/Documents/2026/CodeProjects/SLR-RFF-BRICK log --format='%h %s' origin/ladrillo-dev..HEAD`
and check authorship before pushing. Do not type a commit count.
**TORCH VERDICT:** every job in this arc was local and under a minute (FACTS 1 min/experiment,
BRICK postpred 42 s, BRICK-on-MAGICC 25 s/marker). Nothing here belongs on Torch.

---

## 1. ⭐ THE NEXT DOCUMENTATION TASK (Marcus, 09-13)

**SLEIP Table 2 classifies each emulator's component parametrisations** (type 1 empirical / type 2
physical parametrisation / type 3 physical model / SEJ, plus Regional-output and RSL columns). Its
BRICK row is **TE 2, glaciers 2, GIS 2, AIS 3, LWS —, regional +, RSL −**. The task: go through
Ladrillo's changes and decide, component by component, whether any of BRICK's categories change,
and add the result to the deliverable (a Ladrillo row for Table 2 — the attribute Table 2 already
has an "Antarctic ice sheet (SLEIP type)" row; this would generalise it, or become a sentence).
- The SLEIP text is extracted at the scratchpad `sleip.txt` of the 09-12 session (regenerate with
  `pypdf` from `~/Documents/2026/ClaudeDocs/Papers/SLEIP.egusphere-2026-3874.pdf`; the type
  definitions are in the Table 2 caption, ~line 150 of the paper).
- Things to decide, not assume: glaciers — Mengel-style `S_eq` + Nauels-ν transient on three
  regional reservoirs is still a physical parametrisation (type 2) unless the regional split
  counts as a model; Greenland — two channels × two basins with an amplification law and the
  SICOPOLIS-informed tap: type 2 with a process-model-informed element (SLEIP has no "calibrated
  to process models" flag; the tap is what departs from BRICK's obs-only philosophy); AIS — DAIS,
  type 3 unchanged; TE — ∝ OHC, type 2 unchanged; LWS — Ladrillo carries the OBSERVED series
  (hindcast) and BRICK's stochastic module (projections): BRICK's Table 2 entry is "—", which
  SLEIP's own §3.1 contradicts (memory `sleip2026_emulator_intercomparison` flags that as a likely
  error in their Table 2); regional/RSL — unchanged (no / no).
- Every category call needs a receipt from the SLEIP definition text, not from taste.

**After that: back to the pulse analysis** → `INDEX_cmp_pulse.md` (stage state, tap ruling, the
OPEN cross-model figure design) and `INDEX_cmp_pulse_dur.md`. ⚠ The 09-12c FACTS rule
(`ladrillo_figs.FACTS_CLIMATE_DRIVEN`) bears on any pulse-stage figure that draws FACTS past 2100:
[[facts_blind_to_a_pulse]] already retired FACTS's pulse response, and the new rule says its
Greenland/AIS modules do not see post-2100 climate at all. The responsiveness figure's per-K
numbers (`outputs/vv_responsiveness_L24.csv`) are the like-for-like input Marcus flagged for the
pulse work.

## 2. WHAT CHANGED IN THE DELIVERABLE, 09-11c → 09-13 (all in the .docx; CHANGELOG has the numbers)
- **FIG 1** carries MAGICC-SLR on the Greenland panel from 1991 and a hatched TE band = the most the
  >2000 m ocean could add (IGCC deep heat × observed upper-ocean α; +0.30 cm by 2024 vs Ladrillo's
  +0.81 excess). IGCC's level-σ shading dropped. In-figure captions everywhere cut to essentials.
- **FIGs 2–4, 8–9:** FACTS Total panel is ONE bracket over the workflow medians at 2100 (Option A);
  **past 2100 only climate-driven FACTS modules are drawn** (2150: larmip, ar5glaciers, tlm, lws;
  2300: ar5glaciers, tlm, lws; no totals) — Marcus's rule, `ladrillo_figs.FACTS_CLIMATE_DRIVEN`,
  applied in the two table builders so figures and benchmark inherit it.
- **New FIG 7** (responsiveness, vvH − vvVL per component × model × horizon) and **FIG 11** (the
  climate swap: Ladrillo and BRICK on FaIR and on MAGICC's climate vs MAGICC-SLR; BRICK-on-MAGICC
  was RUN for the 7 markers). Fig 9b dropped (duplicated FIG 8's Total panel).
- **Tables 1–2** (new): scope/calibration and component structure of the 7 SLEIP emulators +
  Ladrillo, 8 pt via `deliverables/shrink_attribute_tables.py` (a post-pandoc pass in the build
  script), terse cells + 12 footnotes, "n.d." = not documented in SLEIP. Glacier inventories on
  the **2000 basis**: BRICK 37.7 (own 1850→2000 melt 4.0 cm, measured by
  `julia/diag_brick_gsic_melt_1850_2000.jl`), MAGICC ≈26–36 (own 9.4 cm), FACTS 31.6, Ladrillo
  29.0 = Farinotti on its scope (excl. RGI 05 = 3.4 cm). Old tables are now 3 and 4.
- **Text:** intro paragraph rewritten around what each comparator cannot do (SLEIP receipts;
  Marcus then edited it — his version stands); units unified to **cm** (ocean depths stay m);
  TE paragraph's apparent contradiction resolved (two halves: depth scope 1.10× and FaIR's own
  1.10×; observed 0–2000 m OHC removes both); three false sentences fixed ("every ice component",
  "narrower than FACTS on every component", "separates upward from BRICK"); MAGICC's vvLN Greenland
  tail explained (sub-preindustrial SMB artefact, 597/600 members below PI); "17/9/4" verified;
  BRICK samples the same `antarctic_lambda` (0.0104 / 0.0036 in both); W&R initial volume is 40
  (2σ 30–50), not "assumed maximum 41".

## 3. RULINGS THIS ARC (Marcus)
1. Full benchmark re-freeze (09-11h), then re-frozen again under the FACTS rule (09-12c, 132
   literature rows). Champion L24 unchanged. Two AIS ssp245/2300 cells that went FAIL under the
   first re-freeze are the known threshold-artifact cell and reverted to WARN under the second.
2. Option A for FACTS totals (bracket, not fan).
3. **FACTS past 2100: drop any module and total whose components are not climate-driven (LWS
   exempt).** Tested first: FittedISMIP on the path is WORSE (fitted t² term: vvHL Greenland 46 → 112
   cm while cooling); LARMIP's 200-yr zero-padded RFs forget all pre-2100 forcing at 2300; a newer
   FACTS changes none of these modules; SLEIP's 2300 FACTS = the same extrapolations.
4. cm throughout; captions say what the figure does; "n.d."; rows that cut against Ladrillo stay.

## 4. ⚠ NON-OBVIOUS STATE / TRAPS
- **The .docx is canonical.** `python3 deliverables/sync_filled_from_docx.py --verify` before ANY
  edit; edit anchors go stale because Marcus edits between turns — twice this arc an edit script
  aborted on a reworded sentence, once AFTER the sync script's FIGS list had been extended, and the
  sync then refused (11 listed vs 10 embedded). Order: sync → edit FILLED.md → extend FIGS/build
  script → build → verify with python-docx. The build script now regenerates EVERY figure
  (FIG 1, vv set, FIG 5, 7, 11 included) and runs the table-font post-pass.
- **The concurrent SLEIP-review session** wrote CHANGELOG 09-12 "RGI 05 / RGI 19…" and commit
  8174c26 (W&R read in full). Its findings agree with Table 2's inventory row: MAGICC's glacier
  scope = Marzeion 2012 = RGI 05 IN, RGI 19 OUT; its present-day inventory 327 mm median (257–352)
  by its own hindcast; Ladrillo's ceiling reads against 291 mm (324 − 33.6). If you touch the
  inventory row, read that entry first (`diag_glacier_periphery_scope.py`).
- `benchmark/reference/_fixed/` is tracked; a `--freeze-fixed` re-snapshots EVERYTHING (incl. the
  BRICK hindcast arm) — deliberate only.
- `outputs/diag_brick_gsic_melt_1850_2000.csv`, `vv_climate_swap_L24.csv`, `vv_responsiveness_L24.csv`,
  `diag_magicc_gis_hindcast_L24.csv` are stamped (provenance column). `data/comparison/magicc_nauels_components.csv`
  is byte-identical to its frozen copy; the MAGICC hindcast/split files are separate products.
- Memory: `INDEX_cmp` split (`INDEX_cmp_magicc`), root and `INDEX_slr` trimmed 09-11; `INDEX_cmp`
  13.1 KB, `INDEX_slr` 15.2 KB; `INDEX_ccx` / `INDEX_cmp_pulse` sit ~17 KB and need a split before
  their next addition.

## 5. FILES (this arc, beyond the 09-11b list)
**New:** `python/plot_vv_climate_swap.py`, `run_brick2_vv_magiccclim.sh`, `julia/diag_brick_gsic_melt_1850_2000.jl`,
`deliverables/shrink_attribute_tables.py`, `figures/vv_climate_swap_L24_{2100,2150,2300}.png`,
`figures/vv_responsiveness_L24.png`, the outputs above. **Changed:** `python/ladrillo_figs.py`
(`FACTS_CLIMATE_DRIVEN`, `facts_module_ok`), `vv_model_comparison.py`, `ladrillo_model_comparison.py`,
`plot_model_comparison_components.py`, `plot_hindcast_components.py`, `plot_future_components.py`,
`plot_vv_responsiveness.py`, `plot_ladrillo_memo_figures.py`, `extract_magicc_components.py`,
`build_l24_deliverable_doc.sh`, `deliverables/sync_filled_from_docx.py`, the deliverable, `benchmark/reference/_fixed/`.
**Memory (new/updated):** `facts_workflows_differ_only_in_ais` (the 09-12 rule and tests), `magicc_gis_starts_1991`,
`facts_twin_extend_gate`, `vv_responsiveness_high_minus_verylow`, `INDEX_cmp`, `INDEX_cmp_magicc`.
