# Handoff 2026-10-09b: the CH4-vs-CO2 pulse paper — next job is adding FACTS to the pulse analysis

Follows `handoff_2026-10-09_pulse_arc_rerun.md`. That handoff's work is DONE: re-run, diff, CHANGELOG, memory, commits.
Start cold from this file, then read:
- memory `ch4_co2_pulse_paper` and `pulse_arc_rerun_20261009`;
- `INDEX_cmp_pulse.md` and `INDEX_cmp_pulse_dur.md`;
- `notes/pulse_rerun_diff_2026-10-09.md`.

## 1. What this session did

1. **Ladrillo.jl readiness for Tony.**
   - The repo was already private on GitHub (`msarofim/Ladrillo.jl`, v1.2.0).
   - A fresh clone from GitHub passes: 90 + 2 skipped (BRICK 2.0 posterior), exact.
   - Stale labels fixed (bfaefd7, pushed): "v1.0" banners, and a comment saying the paper does not condition.
   - **Marcus added Tony and emailed him on 10-09**, asking which BRICK posterior to compare against and for a citable
     link. Our file: the 05-22 post-PR#93 `parameters_subsample_sneasybrick.csv`, BRICK columns only.
   - **Awaiting Tony.** Then set the URL in `tools/fetch_brick20_posterior.sh`, or rerun the BRICK 2.0 arm if he
     points to a different posterior.
   - The pre-public list is in Ladrillo CHANGELOG 2026-10-09.
2. **Pulse-arc re-run finished.** MAGICC 14, FACTS 21, BRICK 2.0 14, Ladrillo 14, magiccclim 56, downstream: all
   gates pass.
   - Old-vs-new diff: `notes/pulse_rerun_diff_2026-10-09.md` and `FaIRtoFrEDI/.../pulse_rerun_diff_20261009.csv`.
3. **[SAME-STATISTIC] was pandas' float PARSER**, not summation noise (my first diagnosis was wrong).
   - Fixed with `pulse_stats.read_csv_exact` (`float_precision="round_trip"`); the gate is EXACT again.
   - The doc tables now build.
   - ⚠ Other ulp-level gates that read CSVs back may carry the same trap. Not audited.
4. **Paired se of the CH4:CO2e exchange rate** (`diag_exchange_rate_paired_se.py`, a joint bootstrap over draws).
   - Ladrillo 0.893 ± 0.058, BRICK 2.0 0.936 ± 0.058, difference −0.043 ± 0.082: NOT resolved.
   - MAGICC 0.637 is ~4σ below both.
   - Per-marker DAIS-model rates carry ±25 % and their scatter is noise; MAGICC's scenario dependence is real.
5. **Six-marker set** adopted and implemented. **iGMST**: prediction stripped; metric and decompositions kept.

## 2. Marcus's rulings (2026-10-09), with the reasons

| ruling | reason / note |
|---|---|
| The pulse work is the core of a **new paper on CH4 vs CO2 pulses** | Aim: which features of the SLR pulse response are **consistent across models** and which are not. Showing one model differs is NOT the goal, though a real difference is valuable. |
| **Six markers**: vvVL, vvL, vvML, vvM, vvHL, vvH | vvLN is out by a DOMAIN rule: by 2300 its baseline is near or below pre-industrial in both climates (FaIR median 0.36 K, 5/841 configs < 0; MAGICC 99.5 %). vvML's old exclusion was the prerelease-tail artifact. One definition: `pulse_stats.VV_MARKERS`, gated by [VV-SET]. |
| **No precision re-run for now** | The lever would be 10k draws (~2.2× tighter per-marker intervals). |
| **No iGMST prediction** | Model output is deterministic; a fixed definition is the protection. The metric is kept as a decomposition. |
| **Add FACTS to the pulse analysis** | THE NEXT JOB (§4). |
| Lay out the tables from a shared function | Done as the shared exact READER (the tables never differed). |

## 3. Live numbers (6 markers, per-marker statistic)

- **CH4:CO2e exchange rate @2300** (total, GWP100): MAGICC 0.637, Ladrillo 0.893, BRICK 2.0 0.936.
- **iGMST ratio** R(FaIR) / R(MAGICC) = 1.3118 [1.2883, 1.3359].
  - Integrated warming carries **98 % [91, 104]** of Ladrillo's climate-swap change in the rate, and **82 % [76, 87]**
    of BRICK 2.0's.
  - Swapping the climate closes 84.6 % (Ladrillo) and 88.5 % (BRICK 2.0) of the gap to MAGICC-SLR.
- **Consistent across models so far:**
  - duration: t50 of the 2030–2300 integral is CO2 2203–2210 and CH4 2175–2181 across 5 arms;
  - CO2 has not peaked by 2300 anywhere;
  - te tracks its climate's ocean heat (1.6e-3);
  - the CH4 long tail is Antarctic.
- **Not consistent:**
  - the threshold tail (the DAIS-lineage models read threshold, MAGICC and FACTS read smooth);
  - MAGICC's ~30 % lower exchange rate;
  - the H/VL scenario split (MAGICC 3.45× vs Ladrillo 0.74× / BRICK 2.0 0.69×), which is Antarctic.
- ⚠ **These are the readings; the paper's prose is Marcus's.** Claude produces figures, tables, methods and numbers.

## 4. NEXT: add FACTS to the pulse time-path analyses (decisions needed FIRST)

FACTS is already in the cross-model cells (2100 / 2150 / 2300, `extract_pulse_vv_facts.py`). It is ABSENT from:
- the duration table and the figures;
- the exchange-rate per-marker table and the paired se;
- the component persistence;
- the TE/OHC mechanism;
- the doc tables (T3–T5 say "FACTS has no row").

**Decision 1, time resolution.** FACTS writes DECADAL output. Every experiment's `config.yml` has `pyear_start: 2020`,
`pyear_end: 2300`, `pyear_step: 10`: 29 points, while the others are annual. Options:
- (a) **Re-run the 21 FACTS pulse experiments with `pyear_step: 1`.** This is the most like-for-like.
  - Cost unmeasured: the 21 experiments took ~20 min at step 10.
  - Check that every module accepts step 1 for these experiments: emulandice is absent; check ar5, larmip, deconto21,
    bamber19, FittedISMIP, tlm, lws.
  - Runs in Docker via colima, which was running at 10:52.
- (b) **Duration metrics for ALL models on a common decadal grid.** No re-run, but t50 / t90 are resolved only to the
  decade, which is the size of the "agree within a decade" result.
- (c) **Interpolate FACTS to annual.** No re-run; it invents within-decade shape.
- Claude recommended **(a) if feasible, with (b) as a robustness check**. Marcus has not ruled.

**Decision 2, which FACTS rows count as "FACTS's total".**
- Recommended: **wf1f (AR5) and wf2f (LARMIP-2)**, the two whose ice sheets both see a pulse. Show components by
  module (ar5glaciers, tlm, FittedISMIP, ar5AIS, larmip).
- wf3f (deconto21 AIS blind, plus the non-causal vvVL re-pick rule) and wf4 (both ice sheets blind) appear only with an
  explicit "ice sheets absent" flag, or not at all ([[facts_blind_to_a_pulse]]).
- ⛔ Never average across FACTS workflows.

**Other FACTS facts:**
- n = 200 FaIR configs (a subset of the 841), on the same pulse cubes as Ladrillo / BRICK 2.0.
- Tail share ~0.08 (smooth), so n = 200 is likely adequate. Check its se like everything else.
- ar5AIS is NEGATIVE by construction (SMB nets dynamics); label it.

**Code that needs FACTS rows:**
- `pulse_duration_vv.py` (ARMS; `load_path` needs a FACTS branch reading the netCDFs or an extractor-written paths
  file);
- `fig_pulse_duration_vv.py`;
- `diag_te_ohc_mechanism_vv.py` (FACTS te = tlm, driven by OHC?);
- `build_pulse_doc_tables.py`;
- `diag_exchange_rate_paired_se.py` (FACTS per-member pairs live in the netCDFs).
- Cleanest route: extend `extract_pulse_vv_facts.py` to write `pulse_facts_paths_*` in the same schema as the MAGICC
  paths files, so the downstream reads one format.

## 5. Other open items

- **The L27 pulse doc section** (`deliverables/pulse_model_differences_L27_section.md`):
  - its tables are live;
  - its PROSE template still types ~15 numbers from 09-07, several stale (flagged in its header);
  - it was built for `LadrilloUpdateDescription_L24.docx`, but its home is now presumably the new paper. Marcus's call.
  - Offer: turn the typed prose numbers into generated placeholders (plumbing, not writing).
- **The GMD docx pass** (v1.1 + vv CMIP7 + v1.2 numbers + 8 wording fixes): still waits on Marcus's go-ahead and on
  Tony's latest file.
- `INDEX_cmp_pulse.md` is at 16,918 B of its 18,432 ceiling. **Split it before adding more** (paper vs arc mechanics).
- Stale and out of scope:
  - `SLR/python/plot_pulse_response_vv.py` (old sizes);
  - `FTF/scripts/pulse_calib_compare.py`;
  - `diag_magicc_glacier_regrowth_subpi.py`.

## 6. Non-obvious state

- **FaIRtoFrEDI is UNPUSHED, by Marcus's hold.** Branch `heat-ed-morbidity`, 400+ commits ahead.
  - This session's commits: 1ccba43, 65b8bed, 2a0543e, a7497d2, 966a50b, b55e9cc.
  - ⚠ **Another session is committing to FaIRtoFrEDI on the same branch** (E3a / E3b, `egu_physical_scenarios.py`,
    modified and NOT ours). Stage files explicitly; never `git add -A` there.
- **SLR-RFF-BRICK** (`ladrillo-dev`) is pushed through this handoff's commit. Ladrillo.jl is pushed (bfaefd7).
- **facts / MAGICC are local only** (others' remotes).
  - MAGICC's pulse driver `slr-refresh/notebooks/302d_run-magicc-pulse-vv.py` has never been committed. It is unchanged
    since 09-04; flagged, not acted on.
- `outputs/log_vvp_facts.txt` is the runner's PRE-rule FACTS pass and is deliberately NOT committed. The canonical
  FACTS gates CSV carries [NONCAUSAL-OMITTED].
- `diag_pulse_rerun_diff_20261009.py` is a HISTORICAL record (old 5 / 7 markers vs new). Do not re-run it as a live
  analysis: the duration table is now on 6.
- The per-draw pulse files (`outputs/pulse_{ladrillo,brick2}_draws_*.csv`) are gitignored by design and needed by the
  paired-se diagnostic.
- Frozen runner copies (`julia/_frozen_*_20261009.jl`, `_frozen_302d_20261009.py`) are gitignored. The runners are
  done; nothing is running.
- **The pandas parser trap:** any comparator at ulp level must read through `pulse_stats.read_csv_exact`.
