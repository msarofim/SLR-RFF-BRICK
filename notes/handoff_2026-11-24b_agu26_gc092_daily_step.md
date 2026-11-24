# Handoff 2026-11-24 (b): AGU26 GC092 poster, third and fourth rounds and the daily Antarctic step

Predecessor: `handoff_2026-11-24_agu26_gc092_tony_review.md` (this folder).

- **Poster:** "Slow Seas, Fast Gas: Coastal Damages from CO2 and CH4", AGU26 GC33I-0525 (session GC092), Wed 9 Dec 2026.
- **Print:** prints Thu 3 Dec; CCI's deadline is Fri 4 Dec, 17:00 PST.
- **Working folder:** `FaIRtoFrEDI/magicc_comparison/poster_agu26/`, branch `heat-ed-morbidity`.
- **State:** pushed at **542d486**; nothing unpushed.
- **Current review copy:** `layout/gc092_layout_44in.pdf`. Red marks are on, and one red suggestion is open (Methods).

## 1. What was done today, in order (CHANGELOG 2026-11-24 (ay) to (bb))

1. **Third round, (ay).**
   - The red Ladrillo "submitted" edits were approved, and the Next Steps Ladrillo sentence was deleted.
   - The results box became three bullets (option B: CH4 in BRICK 2.0 and Ladrillo; CH4 in MAGICC-SLR; CO2). Each bullet lead is a `{{=>>•}}` edit that the layout hangs; `--mutate bullet` checks this.
   - Parametric-uncertainty sentences went into Methods and Next Steps.
   - Panel B was retitled "Global temperature and heat uptake per GtCO2e".
   - Panel D's ratio axis is labelled 0, 1, 2, with minor ticks every 0.5.
2. **Clean copy, (az).** All red approved and `DRAFT_MARKS = False`, at 6eff7dd.
3. **Test 1, (ba).** Marcus asked whether monthly steps would raise the median draw.
   - `diag_ais_substep_agu26.jl` rebuilds each draw's T_ant in both arms (closed form, no model run). It charges the time above the Antarctic threshold annually, monthly, daily or continuously.
   - Monthly barely moves the median. Daily matches the continuous limit, and the CH4 D median ratio goes 0.754 -> 0.865 (Ladrillo) and 0.605 -> 0.821 (BRICK 2.0).
   - Memory: `median_draw_depends_on_threshold_step`.
4. **Daily step everywhere, (bb).** Marcus: "update as many panels as possible with the median fix". Ruled by question:
   - a DAILY step;
   - applied to means AND medians;
   - as a closed-form adjustment of the shipped runs, not a model re-run.
   - Panels C-H were re-rendered; the text numbers were redone and approved.
5. **Approval round.**
   - Marcus approved the daily-step red text.
   - Methods takes his wording, with one red edit on its last clause.
   - Methods went 23 -> 22 pt for fit.

## 2. Decisions and why

- **Daily step, means and medians, closed form (Marcus, by question).**
  - Daily rather than continuous: it is a real step, within about 1 % of the continuous limit.
  - Under the daily step, every six-scenario mean stays inside its annual 95 % interval, and the intervals narrow 2-4x. At these small pulses, integer / continuous time above threshold is 0.55-1.52 across runs (mixed signs), so the annual means were noisy, not biased.
  - The medians move outside their annual intervals, which is the intended fix.
- **Conversion f.** One charged year adds lambda x 24.78e15 / V1850, not lambda, because the component writes sea level as 57 (1 - V/V1850).
  - Measured f (each draw's shipped response / the charge): median 0.82-0.88; 0.87-0.89 within 5 years of the charge; falls about 0.035 per century.
  - Each run uses its own median f. V1850 per draw was not computed.
- **Annual products are never overwritten.** Under `AGU26_AIS_STEP=daily`, every pipeline output gets an `_aisdaily` name. Other products (NCC figure, pulse paper) read the annual files.
- **Two gate changes, approved by Marcus.**
  - [PATH-MATCH-MED] in `diag_slr_ratio`: bound 1e-11 under daily only. The mirror's path medians come from the 12-significant-digit annual files.
  - [BOOT-BIAS] replaces [BOOT-CENTRE] in `diag_exchange_rate_intervals` in both steps. The ratio-of-means bias explained the one failing cell (0.103 vs 0.104 se). `--mutate boot` trips all 42 rows.
- **Text numbers come from `text_numbers_agu26.py`.** Under the annual step it reproduces all 12 printed annual values.
  - The old "29-43 %" turned out to be damages through 2100: median over scenarios, all three adaptation variants, both rates. The answers file had said "2 % rate".
  - The daily text kept that definition (43-59 %). Through 2300 it is 50-70 %.
- **Methods wording.**
  - Marcus's sentence is approved text.
  - My red edit changes only its last clause, because only the Antarctic fast-dynamics term is daily. FaIR and the emulators still run annually.

## 3. Files (all in `FaIRtoFrEDI/`, committed and pushed)

- **New scripts**
  - `magicc_comparison/poster_agu26/diag_ais_substep_agu26.jl`: the substep test; `--write-mirror` writes the daily mirror.
    - Gates: CONFIG-IDENTITY, FIRED-MATCH, STEP-SIGN, ANNUAL-MATCH, PATH-MED-MATCH, MIRROR-ARITH.
    - Mutations: seed, lag.
  - `run_aisdaily_pipeline_agu26.sh`: the eight daily steps in order. About 3 min; two runs byte-identical.
  - `text_numbers_agu26.py`: the text's Ladrillo/BRICK 2.0 numbers under either step.
- **Switch:** `magicc_comparison/pulse_stats.py`, with `AIS_STEP`, `AIS_STEP_SFX`, `SLR_OUTPUTS`, `DRAW_PATHS_DIR` and `stepped()`. Wired into:
  - `pulse_duration_vv`
  - `prep_fredi_pulse_inputs_agu26`
  - `diag_exchange_rate_paired_se`
  - `diag_exchange_rate_intervals_vv`
  - `diag_slr_per_gt_intervals_vv`
  - `diag_slr_ratio_2300_2150_vv`
  - `perdraw_fredi_agu26`
  - `make_panels_agu26` (`POSTER_AIS_STEP = "daily"`, [AIS-STEP] guard)
- **Mirror:** `poster_agu26/fredi_inputs/ais_daily/` is not committed; it is gitignored and regenerated by the runner.
- **Outputs**
  - Committed: `processed/*_aisdaily*`, the small `fredi_inputs/*_aisdaily*`, and `answers/substep_2026-11-24/` (README, horizons, paths, ratios, gates, fired, draws, text_numbers{,_aisdaily}).
  - Large `_aisdaily` inputs are gitignored.
- **Text and layout:** `text/gc092_poster_text.md` (header notes for every round); `make_layout_agu26.py` (bullets, `BULLET_LEAD`, Methods 22 pt, `DRAFT_MARKS = True`).
- **Memory:** `median_draw_depends_on_threshold_step` (new, in `INDEX_cmp_pulse`); `agu26_pulse_poster_rulings` (third round, daily step).
  - `INDEX_cmp_pulse.md` is at 17,642 of 18,432 bytes. Split it before adding more.

## 4. Open: Marcus's calls

1. **The one red Methods edit.**
   - His last clause: "so FaIR output and the sea level emulators are adjusted to work on a daily basis".
   - Red: "so FaIR temperatures are interpolated to daily values and the Antarctic fast-dynamics loss is recomputed daily".
   - The reviewer suggests "is charged per day" as more literal still.
2. **Findings of the independent review, verified, not yet applied.** I asked whether to apply 1-5 plus the style fixes as red suggestions; no answer yet.
   1. **Conclusion 3**, "by 2300, MAGICC-SLR's is about a quarter larger", holds only for the six-scenario mean, which M and H carry.
      - MAGICC-SLR at 2300 (mm per GtCO2): 0.72 in M and 0.88 in H; Ladrillo and BRICK 2.0 are 0.23-0.39 in those two scenarios.
      - MAGICC-SLR is below both models in VL, L, ML and HL. Panel C (median over scenarios) puts it lowest at 2300: 0.370 against 0.382 and 0.407.
      - MAGICC's runaway members may contribute (answers 11-19, item 2).
      - Suggested: "mean over the six scenarios is about a fifth larger, because of scenarios M and H". Bullet 3's 1.91 has the same pattern.
   2. **Conclusion 1**, "declines after about 50 years". BRICK 2.0 ML peaks at 77 years under daily. Suggested: "after 40-80 years". `text_numbers` [REPRODUCE] checks only the annual step.
   3. **Damage Caveats.** 43-59 % is through 2100; panel H's headline is through 2300 (50-70 %).
   4. **Bullet 1's "(panel D)".** The 56-65 % and 86-99 % are 2300/peak, which D does not show. Drop the pointer, or use D's 2300:2150 (0.67-0.74 and 0.89-1.06).
   5. **Methods.** "Ocean heat content" should be "heat uptake": FaIR's quantity is total Earth heat (panel B inset).
   6. **Optional**
      - Panel H's open diamonds mean "through 2100", while open markers mean the median in D and F.
      - The text cites only panels A, D and H.
      - VL...H are never spelled out.
      - "Median draw" and "median over draws" are both used.
      - Conclusion 1's +200-yr horizon is on no panel.
      - The Methods intervals sentence does not cover D's median intervals.
      - Style:
        - "tracks the time-integral" -> "increases with";
        - Motivation "which" -> "that";
        - bullet 3 "In contrast," -> "For CO2,";
        - "University of California, Berkeley".
      - Panel subtitles are about 13 pt; the Damage Caveats box is about 40 % empty.
3. **Possible upstream bug, not yet investigated.**
   - FaIR CH4 warming per GtCO2e at 2100 is 0.247 mK in vvL, against 0.336-0.388 in the other five (VL 0.388, L 0.247, ML 0.336). MAGICC's vvL is not low (0.258).
   - It feeds every FaIR-driven vvL CH4 number.
   - Check the vvL CH4 pulse cube (`SLR-RFF-BRICK/data/observations/fair_cube_gmst_vvL_{pulsebase,pulse}_CH4_0p01Gt_2030_raw.csv`) and its build before trusting vvL CH4.
4. **Carried over from before.**
   - QR code, once the iPoster URL exists (publish by 2 Dec); `HEADER_SLOTS`; add a decode check.
   - The CCI order.
   - Other coauthors' comments.
   - Marcus's reply to Tony.
   - The MAGICC Antarctic note for the Ladrillo paper.

## 5. Non-obvious state

- **Render order.**
  - Commit scripts and text.
  - If the mirror or pipeline inputs change: `magicc_comparison/poster_agu26/run_aisdaily_pipeline_agu26.sh` (runs the mirror plus seven Python steps under `AGU26_AIS_STEP=daily`).
  - Panels: `~/miniforge3/envs/slr-refresh-2025/bin/python make_panels_agu26.py` (defaults to daily; refuses `AGU26_AIS_STEP=annual`). Commit.
  - Layout: `~/climate-env/bin/python magicc_comparison/poster_agu26/make_layout_agu26.py`. Commit.
  - Render twice and compare (byte-identical all day). Run `--reject-red` for fit.
- **Fit.** Column 1 has about 0.6 in spare at Methods 22 pt. Column 4 is tight (about 0.3 in total). Conclusions is 15.56 / 15.65.
- **Mutations.**
  - Layout: 17, including `bullet`. Panels: 9. diag_ais_substep: `seed`, `lag`. Exchange-rate: `--mutate boot`.
  - Panel mutations write no panel files (verified by hash).
- **Comparing annual and daily tables:** join on the RATE (and variant). Missing it once produced a fake 3x damage change.
- **Not adjusted:** the MAGICC-climate arms of Ladrillo and BRICK 2.0 (bullets 2-3: 0.96-0.97, 1.35-1.49) and Ladrillo's Greenland threshold.
- **Shared branch:** `heat-ed-morbidity` is shared with other sessions. Check `git log origin/heat-ed-morbidity..HEAD` before pushing.
- **Marcus's source docs:** `layout/gc092.slr.notes2.docx` and `gc092slowseas.notes.docx` stay untracked; the layout reads them and never writes them.
