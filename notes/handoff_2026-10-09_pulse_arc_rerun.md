# Handoff 2026-10-09: the van Vuuren PULSE ARC re-run (downstream of the 10-08 cubes)

Follows `handoff_2026-10-08c_vv_zenodo_rerun.md`; its open item 3 ("the pulse arc's downstream is stale") is this job.
Read `memory/INDEX_cmp_pulse.md` + `INDEX_cmp_pulse_dur.md` for what the arc IS before touching it.

## 1. Marcus's rulings (2026-10-09)

1. **Posterior L27 = "Ladrillo v1.2"**, not the arc's old L24. The paper's version label is v1.2, tagged `v1.2.0`
   in Ladrillo.jl on 10-08.
2. **Record conditioning on the Ladrillo FaIR pulse arm**: own-config drop, the 10-08 level-arm rule.
3. **The MAGICC-climate Ladrillo arm runs 2,000 draws, paired with the FaIR arm.** It had run 8,000 unpaired draws:
   `julia/run_pulse_vv_magiccclim.sh` passed 2000 PER CHAIN. That runner is now guarded as SUPERSEDED.
4. **FACTS deconto21 non-causal re-pick: treat as BLIND** (see §3).
5. Write this handoff and keep going.

Earlier, same session (10-08 evening):
- the climate swap moved to the COMMON draw set;
- the swap committed in e567ea7 was mixed-vintage and is quarantined;
- Ladrillo v1.2.0 is tagged;
- the MAGICC history-gap reader is fixed;
- FaIRtoFrEDI stays unpushed (Marcus).

All of this is in SLR CHANGELOG 10-08l/m. (The 10-09 entries are NOT written yet; see §5.)

## 2. What the arc was, and the bug

- Every live pulse product dated 09-04..09-07 and was built on the Smith-history + harmonized-tail vv cubes.
- The 10-02 CMIP7 rebuild and the 10-08 Zenodo rebuild both re-made the 112 pulse cubes, and **nothing downstream
  was re-run**. `run_vv_cmip7_rerun_20261007.sh` claimed to cover every `fair_*_vv*` reader and missed the arc.
- MAGICC's pulse scenarios came from the 08-31 harmonized `slr_vv_and_ssps.csv`; FACTS's pulse climate came from the
  Smith cubes.
- vvML baseline GMST at 2300 moved 0.55 → 1.39 K.
- The full dependency map is from an Explore agent; its key facts are captured in the two runners' headers.

## 3. Done so far (all gates pass unless stated)

| step | where | state |
|---|---|---|
| quarantine `20261009_vv_pulse_smith_harmonized` | SLR outputs/, FTF processed/quarantine/, MAGICC data/quarantine/, facts quarantine/ | done, README + SHA256SUMS in each (443/136/42/609 files) |
| Ladrillo pulse driver port (`julia/scope_slr_pulse_vv.jl`) | SLR f2819c8 | done; see below |
| downstream L24→L27 (`LADRILLO_TAG` in `pulse_stats.py`), `vv_pulse_wide_20261009` | FTF d147217 | done |
| FACTS stage 5 (21 experiments) + extract | facts; FTF 617e00c | done, with the deconto21 rule |
| MAGICC stage 4 (14 runs, n600, 6 workers) | MAGICC data/processed/PULSEVV_*_2026_10_09_*; FTF processed/pulse_magicc_* | RUNNING, ~10 min/run, 3 of 14 done at 06:41 |
| BRICK 2.0 stage 3 (14 runs) | SLR outputs/pulse_brick2_*_spliced_B20.csv | RUNNING |
| Ladrillo FaIR arms (14, two at a time) | SLR outputs/pulse_ladrillo_*_spliced_L27_tap…csv | RUNNING, 6 of 14 done, all 8 gate lines PASS, 2 dropped each |

**The port** (`scope_slr_pulse_vv.jl`).
- Draws come from the 10k subsample with the v1.1 single paleo rule, as `scope_slr_fair_uncertainty.jl` reads them,
  so the FaIR pulse arm's BASELINE IS the level vv joint arm. Record conditioning is ported from the same driver.
- The MAGICC arm takes the COMMON draw set from the FaIR arm's gates file, so the FaIR arm runs first.
- Statistics are computed on kept draws. The Rao-Blackwellised P(fired) carries the same pair rejection. A
  `provenance` column is added.
- New gates, each mutation-tested on vvH CO2:
  - **[LEVEL-MATCH]** — the baseline is bit-identical to the level arm on 35,964 cells; the SPLICE_YEAR mutation gives
    24,089 mismatches;
  - **[TRIGGER-PORT]** per arm;
  - **[ONSET-ARMS]**;
  - **[PAIR-REJECT-PORT]**;
  - **[COMMON-DRAWS]** — magicc mode; its failure path is a plain missing-file or mismatch check, not mutation-tested.
- vvH CO2 test: the cross-product kept 1,680,782 of 1,682,000 pairings; P(fired) z ≤ 0.23.

**FACTS deconto21, ruled BLIND.** At vvVL, member 23 of 200 re-picks its whole deconto21 Antarctic path under EITHER
pulse: −0.9 mm in 2020, +182 mm at 2300. [PREPULSE-EXACT] failed 4 of 182 checks, with the climate inputs identical
before 2030 (0.000).
- Rule: the discrete-pick modules {deconto21, bamber19} are made BLIND on a pre-pulse failure, and the module's
  per-member difference is subtracted from its workflow totals.
- [NONCAUSAL-OMITTED] checks the adjusted total to 4 float32 ulps: 4.8e-7 cm against a tolerance of 3.8e-6.
- Any other module's pre-pulse failure STOPS the extraction.
- Mutation-tested. Exactly 12 cells change. wf3f vvVL CO2 goes −0.003 → +0.0076 cm @2100 and 0.111 → 0.0194 @2300;
  wf1f is 0.0069 / 0.0167.
- ⚠ Memory `facts_blind_to_a_pulse` says "~4e-4 °C never flips the pick". On the new inputs it flipped once, at
  vvVL. The memory needs that nuance.

## 4. What runs next, in order

1. Wait for `run_vv_pulse_rerun_20261009.sh magicc` to finish (it ends by building `vv_pulse_wide_20261009/` +
   `gates_{CO2,CH4}.csv`), and for the `ladrillo` phase (all 14).
   - Watch `outputs/log_vv_pulse_rerun_20261009.txt` (FAILED / "phase done").
   - Check each MAGICC extract's [SUB-PREINDUSTRIAL]: vvML may now be reportable, while vvLN was −0.66 K at 2300.
2. `./run_vv_pulse_rerun_20261009_ladrillo.sh magiccclim`:
   - 28 Ladrillo runs (spliced+raw × 7 × 2 gases, 500 per chain, common draw set);
   - 28 BRICK 2.0 runs;
   - two at a time, ~1–1.5 h.
3. `./run_vv_pulse_rerun_20261009_ladrillo.sh downstream`: the cross-model table, scenario dependence,
   module-vs-climate ×4, duration (+figures), iGMST ordering, TE/OHC mechanism, doc tables. Minutes.
4. **Diff old vs new.** Old = the quarantine copies; new = the canonical files. Two axes moved at once (the cubes AND
   L24→L27 for Ladrillo); BRICK 2.0, MAGICC and FACTS moved on the inputs only. Report:
   - the per-Gt totals at 2100/2300;
   - the tail shares;
   - the duration t50/t90;
   - the CH4:CO2e exchange rates (0.913 / 0.637 / 1.024 shipped);
   - the H/VL scenario split;
   - the /magiccclim climate shares (25 % [12,35] Ladrillo, 16 % BRICK shipped).
5. SLR CHANGELOG 2026-10-09 (+ FTF CHANGELOG), quarantine READMEs are written; memory:
   - `INDEX_cmp_pulse(_dur)`: which numbers are superseded;
   - `facts_blind_to_a_pulse`: the vvVL flip;
   - the runner-inventory lesson: a "re-runs every reader" claim needs an inventory gate.
6. Commit. SLR is pushed. FTF / facts / MAGICC commit locally only (FTF held by Marcus; facts' and MAGICC's remotes
   are others' repos).

## 5. Open for Marcus

- **The iGMST pre-registered prediction.** `diag_igmst_ordering_vv.py` hard-codes PREDICTED = 1.4333 (= 0.913/0.637,
  the 09-07 exchange rates) and HEADLINE_MARKERS = five. Run as-is, it reports the new interval against the historical
  prediction. Alternatively re-derive the prediction (it would no longer be pre-registered).
- **Where the L27 doc section goes.** `build_pulse_doc_tables.py` now writes `pulse_model_differences_L27_section.md`.
  It used to be pasted into `LadrilloUpdateDescription_L24.docx`, which is a Marcus-edited source; never edit it.
- MAGICC's history is still Smith 2024 while FaIR is on CMIP7, by design (as in the level arm).
- `[SIZE-SPAN] CHECK` on the headline scenario builds is expected: that gate is for ladders.

## 6. Non-obvious state

- **Two runners are live** (bash reads incrementally: do NOT edit them while they run):
  - `run_vv_pulse_rerun_20261009.sh` — the magicc stream, then facts→brick;
  - `run_vv_pulse_rerun_20261009_ladrillo.sh ladrillo`.
- Frozen copies are `julia/_frozen_scope_slr_pulse_vv_20261009.jl`, `..._brick2_20261009.jl` and
  `MAGICC/slr-refresh/notebooks/_frozen_302d_20261009.py`. All gitignored.
- Another session's CCX R jobs (4 cores) share the machine; the load average reads 40–70, which is mostly MAGICC's
  spawned binaries.
- The vvH CO2 Ladrillo outputs were first written by the TEST run (identical code). The production run overwrites
  them; verify the H logs show [LEVEL-MATCH] PASS.
- MAGICC 302 on 10-08 exited rc=1 after writing its CSV (an scmdata plot KeyError). This is not logged in 10-08k.
- `SLR/python/plot_pulse_response_vv.py` and `figures/pulse_slr_response_*.png` are still on the pre-09-04 OLD sizes.
  They are out of scope, and stale.
- `FTF/scripts/pulse_calib_compare.py` still reads `spliced_ext_harmonized`, and
  `magicc_comparison/diag_magicc_glacier_regrowth_subpi.py` hard-codes a moved MAGICC CSV. Both are outside the arc
  and stale.
