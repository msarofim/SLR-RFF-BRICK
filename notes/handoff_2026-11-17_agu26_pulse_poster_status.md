# Handoff 2026-11-17: AGU26 GC092 "Slow Seas, Fast Gas", poster status for review

Predecessors: `handoff_2026-11-13_agu26_pulse_poster.md` (start; §6 lists the GMD session's files) and
`handoff_2026-11-13b_agu26_poster_fredi.md` (FrEDI pulse damages). Marcus will review the poster's status in the next
session. Read this file, then `FaIRtoFrEDI/magicc_comparison/poster_agu26/claims_and_layout.md` (status table at the
top, claims vs evidence in §1, layout in §3) and memory `agu26_pulse_poster_rulings`.

## 1. Where things are

- Poster: GC092, Wednesday 9 December 2026, 14:15-17:45 PST, 44 x 44 in maximum.
- Code and products: `FaIRtoFrEDI/magicc_comparison/poster_agu26/`
  - `make_panels_agu26.py` draws B, C, D, F, G, H, I, J into `panels/` (pdf + png). It also writes
    `panel_numbers_agu26.csv`, every plotted number with provenance, and `panel_manifest_agu26.csv`, the inputs with
    hashes.
  - `samples/` holds the J samples (a-d) and the claim-10 2500 sample. These are not poster panels.
  - Interval inputs live in `magicc_comparison/processed/`:
    - `diag_slr_per_gt_intervals_vv_2030.csv` (G)
    - `diag_exchange_rate_intervals_vv_2030.csv` (H)
    - `diag_slr_ratio_2300_2150_vv_2030.csv` (D)
    - `diag_slr_pulse_year_lag_vv.csv` (the 2500 extension)
- A different poster, SY047 (state damages), is run by another session. Its commits interleave on FaIRtoFrEDI
  `heat-ed-morbidity`, and it also writes the CHANGELOG. Its handoff is
  `FaIRtoFrEDI/notes/handoff_2026-11-17_sy047_layout.md`.

## 2. Panel state

| panel | state |
|---|---|
| A model chain schematic | not drawn |
| B pulse GMST per GtCO2e, CO2 vs CH4, FaIR and MAGICC | built |
| C pulse SLR per GtCO2e, five series | built |
| D claim 10: response relative to 2150, CO2 vs CH4, 2300:2150 ratio with paired-bootstrap intervals | built 11-17 (2030 pulse, to 2300) |
| E t50 | dropped 11-15 |
| F component shares at 2100 and 2300; FACTS at 2100 only (wf1f's Antarctic share is negative, drawn left of 0) | built 11-17 |
| G SLR per GtCO2e by model, 2100 and 2300, bootstrap interval of the ensemble mean | built 11-15 |
| H CH4:CO2e exchange rate, 2100 and 2300 | built; resampling fixed 11-17 (bounds moved <= 0.012) |
| I FrEDI coastal damages NPV per tCO2e (2020$) | built 11-13; bias caveat in the status table |
| J per-draw response beside model means (sample option b) | built 11-17 |

- **Layout:** the GC092 layout is only the ASCII proposal in `claims_and_layout.md` §3. It has not been assembled, and it
  predates three rulings: E was dropped, J is now built, and F/G changed form.
- **Text:** every text box is Marcus's. Claude supplies panels, numbers, captions and layout only.

## 3. Rulings so far (Marcus)

- **11-13:**
  - van Vuuren backbone, with RFF-SP as the next step.
  - FrEDI coastal damages on the IEc 1.0.0 build.
  - All four SLR models.
  - Median central path; HTF elder mortality dropped.
  - 2020$ via the BEA deflator, citing EPA's method.
  - Say "scenarios", not "markers".
- **11-15:**
  - E dropped; F at 2100 and 2300.
  - G may differ from the paper's figure.
- **11-17:**
  - FACTS appears in F at 2100 only; J is option b.
  - Claim 10 is tested with the 2300:2150 ratio.
  - Claim 10 concerns permanent SLR from CH4 emissions, not damages.
  - H's resampling is fixed.
  - Then: a second pulse in 2080, and the 2030 pulse re-run to 2500. CMIP7 forcing after 2300; FACTS left out; cube
    rounding acceptable; pulse sizes kept.
  - Compare pulse years at a fixed number of years after the pulse, and report both mean and median.
  - **Last ruling:** the 2500 numbers inform the discussion only, with no diagram. Panel D stays as it is.

## 4. Numbers Marcus may want for the text (all in CSVs with provenance)

- **G, SLR per GtCO2e (mm), mean of six scenarios:**
  - CO2 at 2100: Ladrillo 0.151, BRICK 2.0 0.153, MAGICC 0.146; FACTS 0.063 / 0.088.
  - CO2 at 2300: 0.381 / 0.373 / 0.479.
  - CH4 at 2300: 0.335 / 0.306 / 0.268.
- **H, exchange rate:**
  - 2100: 2.12 / 1.97 / 1.47.
  - 2300: 0.89 [0.78, 1.01] / 0.87 [0.75, 0.99] / 0.64 [0.61, 0.67].
- **D, 2300:2150, 2030 pulse:**
  - CO2: 1.59 / 1.65 / 1.91.
  - CH4: 0.99 [0.92, 1.07] / 0.95 [0.90, 1.04] / 1.15 [1.14, 1.17].
  - CO2 - CH4 > 0 in every model and scenario.
- **2500 extension, response 420 yr after the pulse / 120 yr after, mean / median over draws:**

  | CH4 | Ladrillo | BRICK 2.0 | MAGICC |
  |---|---|---|---|
  | 2030 pulse | 0.95 / 0.65 | 0.91 / 0.40 | 1.18 / 1.14 |
  | 2080 pulse | 0.92 / 0.69 | 0.91 / 0.42 | 1.06 / 1.03 |

  - CO2 is 1.5-2.5 in every model.
  - The DAIS models' CH4 mean is near flat only because threshold draws rise; the typical draw falls.
  - Pulse year (2080 / 2030 per GtCO2e at +120 yr): CH4 1.09-1.23 on the mean and 1.03-1.15 on the median; CO2 0.89-1.00.
  - Mechanism (CH4): thermal expansion falls to about a third of its +120 yr value (DAIS; 0.71 in MAGICC), as FaIR's ocean heat
    does; glaciers fall back on the median draw.
  - Details: CHANGELOG 2026-11-17 (f), memory `ch4_slr_step_to_2500`, the claim-10 row in `claims_and_layout.md`.

## 5. Open for the review session

1. Panel review. The latest renders are all in `panels/`.
2. A, the schematic. Its content is fixed by the rulings and it can be drawn now.
3. Assemble the GC092 layout. The §3 proposal needs updating: E is gone, J is built, D/F/G are in their new forms. Keep
   the text placeholders for Marcus.
4. The abstract still says "SLR-driven damages may scale with cumulative CH4", and names RFF-SP and HTF elder mortality.
   The rulings replace these, and the poster text is Marcus's.
5. The panel I caption caveat: the median-path shortcut's bias is in the status table.

## 6. Non-obvious state

- **Interpreters:**
  - Render panels with `~/miniforge3/envs/slr-refresh-2025/bin/python` (matplotlib 3.8.4). `~/climate-env`
    antialiases text differently.
  - FaIR drivers use `~/climate-env`.
- **Render discipline:**
  - Commit scripts first, so the stamp carries a clean hash.
  - Run twice and require byte identity.
  - Pixel-diff the panels that should not change.
- **2500 runs (claim-10 extension only; memory `end_year_2300` records the exception):**
  - New names everywhere: `spliced_ext_zenodo2500/`, `calibration_v160_prod/to2500/`, FaIR cubes
    `*_<YEAR>_to2500_raw.csv`, Ladrillo/BRICK outputs `pulse_*_<YEAR>_to2500_*`, MAGICC
    `PULSEVV_*_headlinepos_p<YEAR>_to2500_n600_*.csv` (24 x ~130 MB in `MAGICC/slr-refresh/data/processed/`).
  - Runners: `run_vv_pulse2500_{fair,slr,magicc}_20261117.sh` (this repo).
  - `julia/mimibrick_get_model_ext.jl` (`brick_get_model`) extends MimiBRICK past 2300. `brick_mengel.jl` and the BRICK
    2.0 pulse driver call it; it behaves exactly like `get_model` for end years <= 2300.
  - The Ladrillo/BRICK outputs stamp `93f4c72-dirty`: the runs started before `b9761eb` was committed, and the frozen
    drivers they ran equal the committed code.
  - `processed/pulse2500_paths_vv.csv` (26 MB) is not committed; `diag_slr_pulse_year_lag_vv.py` regenerates it in 2 min.
- **Branches:**
  - FaIRtoFrEDI `heat-ed-morbidity` pushed.
  - SLR-RFF-BRICK `ladrillo-dev` pushed.
  - MAGICC `slr-refresh` `vv-slr-runs` has local commit `24fbb11` (build_vv_scenarios `--to2500`, notebook 302e), not
    pushed: the remote is the members-only GitLab.
- **Seen in passing, not fixed:**
  - `diag_exchange_rate_paired_se.py` (the 2300-only original) still resamples the intersection of draw ids. It is
    kept as the `[REPRODUCE-2300]` fixture for H.
- **Do not touch** (GMD session): `SLR-RFF-BRICK/deliverables/GMD*`, `deliverables/redline/`, `figures/paper/`,
  `python/ladrillo_figs.py`, `python/plot_vv_*`, and the Ladrillo.jl repo.

## 7. Update, 2026-11-17 evening: A drawn, layout assembled

Done by a follow-on session (FaIRtoFrEDI `heat-ed-morbidity`, commits 74bbdba to c538388, not pushed; CHANGELOG
2026-11-17 (h)). Items 2 and 3 of section 5 are done; items 1, 4 and 5 remain Marcus's.

- **Panel A** is `panels/A_model_chain.*`, drawn by `make_panels_agu26.py`. Ensemble sizes are read from the products and
  gated ([A-COUNTS], [A-PULSE], [A-PANELS], [A-FIT]; `AGU26_MUTATE=...` trips each one).
- **The other panels** were re-rendered at 74bbdba. Only their stamp line changed.
- **Layout:** `make_layout_agu26.py` writes `layout/gc092_layout_44in.pdf`, 44 x 44 in, with the vector panels merged by
  pypdf, plus a 60-dpi preview PNG.
  - Run it with `~/climate-env/bin/python`, which has pypdf. The panels still render with the slr-refresh-2025
    interpreter.
  - The column order is the `COLUMNS` constant: C, F, D in column 2 and G, J, H in column 3 (F and J moved from the
    11-13 proposal).
  - Text room is about 1,120 words at 28 pt. Claims file section 3 has the details.
- **Commit order:**
  1. Commit `make_panels_agu26.py`, render, commit `panels/` and the two CSVs.
  2. Commit `make_layout_agu26.py`, render, commit `layout/`.
  - The layout's [PROV] gate stops if any panel PDF comes from a different render than `panel_numbers_agu26.csv`.
- **New questions for the review:**
  1. Panel I's subtitle states the 2100 shortcut bias (-32 to +20 %). It does not state the 2300 bias (-28 to +179 %)
     that applies to the hollow diamonds. Should the subtitle state it?
  2. Panel text prints at 13.6-19 pt (1.045x). SY047's panels were enlarged 1.5x (Marcus 11-17). Doing the same here
     means drawing the panels about 7 in wide and re-placing each panel's hand-set labels. There is room: the layout
     has more text space than SY047's.
  3. The header uses the working title, shortened affiliations, and slots for a QR code and logos.

## 8. 2026-11-19, second round (FaIRtoFrEDI CHANGELOG 2026-11-19 (h))

- **Ruled (Marcus):** GWP100 27.9; MAGICC CH4 pulse biogenic (`MAGICC_CH4_FOSSFRAC=0`); medians shown beside means; TCRE;
  Claude may suggest edits to his wording, in red until he approves.
- **Done:** all MAGICC CH4 runs and every downstream product redone by `FaIRtoFrEDI/magicc_comparison/run_ch4_biogenic_rerun_20261119.sh`
  (old products quarantined in three repos, READMEs). Panels C (dotted median paths) and D (CH4 mean + median paths,
  ratio of medians) redrawn; layout re-rendered with 29 suggested edits in red (`poster_agu26/layout/gc092_text_edits.md`).
  Answers: `poster_agu26/answers/answers_2026-11-19.md` (rewritten).
- **Open for Marcus:** approve/reject the red edits (then set `DRAFT_MARKS = False` for print); whether to run the MAGICC
  CO2 arm biogenic too (removes a 0.3-12 cm baseline mismatch); whether to exclude MAGICC's two to-2500 runaway members
  (vvML 2030 #530, vvL 2080 #435) from the claim-10 tables; the panel I 2300 caveat.
- **Known defects, not fixed:** MAGICC Greenland-SMB outlier members (1-15 per run, both gases) make MAGICC's
  per-scenario means noisy by up to ~25 %; `build_pulse_doc_tables.py` not rebuilt.
