# Handoff 2026-10-08: Ladrillo v1.1 built, rerun and certified; two decisions to ask Marcus

Follows `handoff_2026-10-07c_ladrillo_v11.md`, whose §2 decisions were all ruled and whose §4 build plan is done (§3).

## 1. ⛔ FIRST THING NEXT SESSION: ask Marcus decisions 2 and 4, each with the recommendation below

Marcus's own instruction (10-08): *"ask me about 2 & 4 with recommendations in the next session."*

Use AskUserQuestion, put the recommendation first, and state the evidence. Do not act on either before he rules.

### Decision 2: condition the propagated paleo draws on "no fast dynamics before the record ends"?

**Facts** (CHANGELOG 10-08 finding 2 and 10-08c; memory `paleo_tcrit_crosses_in_hindcast`):
- 4 of the 10,000 draws start DAIS fast dynamics in 2021–2026: rows 4182, 4588, 4618 and 9713 of
  `parameters_subsample_brick_mengel_L27.csv`, single assignment, T_crit −16.37 to −16.93 °C.
- They add 0.31–1.59 cm of Antarctic sea level by 2026. Their 2021–26 Antarctic rate is 0.10–0.30 cm/yr, against
  0.035–0.040 for the same draws without fast dynamics.
- **None of the 4 is among the 2,000 projection rows (1:5:10000)**, so no reported projection contains one.
- Table 5 uses all 10,000 draws but takes the MAXIMUM likelihood, so these poorly fitting draws cannot set it.
  Every quoted hindcast number is unchanged.
- The draft's 2.2.3 says λ / T_crit are "likelihood-flat over the 1900–2025 record". That holds for the calibration,
  which uses the paleo medians and never crosses the threshold, not for every propagated draw.

**Recommendation: no change to the method or the numbers for the paper.**
- Conditioning changes no reported number, and it would be a new methodological step to describe and defend.
- Optionally the paper could carry a short qualifier (0.04% of draws, none in the reported projections), but drafting
  that prose is Marcus's.
- Offer conditioning as a documented OPTION for package users who take all 10,000 draws (e.g.
  `posterior(; drop_hindcast_collapse=true)`), for v1.2, not v1.1.

**Alternatives to offer:**
- (b) Condition now: reject or resample those draws. Principled, because the 2021–25 record shows no such rate, but
  it costs another rerun round for no reported change.
- (c) Truncate the paleo T_crit prior. Not recommended: it changes the prior for everyone, to fix four draws.

### Decision 4: the SSP2-4.5 tap number in 2.2.2

The draft quotes the tap as a difference of total medians: "36.5 cm at SSP5-8.5, nothing at SSP1-2.6 and 0.3 cm at
SSP2-4.5". v1.1 gives 34.7 / 0.0 / 0. The tap is identical in v1.1: Greenland is bit-identical. "0.3 → 0.0" is the
median of the total moving because of the paleo change.

Paired per-draw numbers (tapped − untapped, same draws and configs, 2300; CHANGELOG 10-08c):

| scenario | fires in | total, paired mean | total, paired median | difference of the total medians |
|---|---|---|---|---|
| SSP5-8.5 | 96% of draws | +35.0 cm | +39.2 | 34.7 |
| SSP2-4.5 | 11% | +1.5 cm | 0 | 0.0 |
| SSP1-2.6 | 0.3% | 0.0 | 0 | 0 |

**Recommendation: quote the PAIRED statistics, the share of draws in which the tap fires and its mean
contribution** (96% / +35 cm; 11% / +1.5 cm; essentially never). They are stable against resampling, additive, and
say what the tap does. A difference of two medians of the total is not a contribution: it went 0.3 → 0.0 with no
change to the tap.

**Alternative:** keep the difference of medians and update it to 34.7 / 0 / 0, which says "nothing" at SSP2-4.5 even
though the tap fires in 11% of draws. The prose is his.

## 2. Rulings this session (all recorded in memory `ladrillo_clean_repo_decisions`)

| # | ruling (Marcus 10-08) | done |
|---|---|---|
| 1 | The paper moves to v1.1 NOW, in the same round as the vv CMIP7 numbers | rerun complete |
| 2 | The RESEARCH drivers produce the numbers; the package is re-certified against them | yes |
| 3 | Tag the package v1.0.0, then 1.1.0, keeping both v1.0 behaviours as options | tag `v1.0.0` = a2bb3b0; 1.1.0 = 78b03c6 |
| 4 | Table A2 → the 10k subsample | `outputs/ladrillo_table_a2_L27_sub10k.md` (2 display cells flip) |
| — | The paper's label becomes "Ladrillo v1.1" | **docx pass** (not done) |
| — | Re-freeze the benchmark champion on v1.1 | done at 2884b17; the v1.0 reference is quarantined |

## 3. State (committed)

| repo | commit | pushed? |
|---|---|---|
| `SLR-RFF-BRICK` (`ladrillo-dev`) | 2884b17, plus this handoff's commit | 2884b17 pushed; the handoff commit is pushed with it (see the log) |
| `Ladrillo` (`main`) | 78b03c6 (v1.1.0); tag `v1.0.0` | **no remote yet** (decision: a private GitHub repo once the ports are done) |

**Code** (CHANGELOG 10-08):
- `LWS_OBS_ANCHOR = :zero_at_first_year` and `LADRILLO_PALEO_ASSIGNMENT = :single` are the defaults in both
  codebases.
- v1.0 is reachable by environment variables `LADRILLO_LWS_OBS_ANCHOR=v1_step LADRILLO_PALEO_ASSIGNMENT=v1` in research
  (outputs then carry `_paleov1_lwsv1_step`), and by `--v1.0` / `posterior(paleo=:v1)` /
  `LadrilloModel(lws_anchor=:v1_step)` in the package.
- The joint arm reads the 10k subsample (`--source=subsample`).
- [CONTROL-EXACT]: in each SSP joint arm the fixed arm must equal its panel exactly.

**The rerun:** `run_ladrillo_v11_rerun_20261008.sh` (phases regress / arms / downstream), 0 failures.
- Gates:
  - [V1-REGRESSION]: 16 files reproduced exactly;
  - [CONTROL-EXACT]: 15 arms;
  - [TABLE5-INPUT]: byte-identical;
  - the suite: 12/12.
- Quarantine: `outputs/quarantine/20261008_ladrillo_v10_superseded/` (README; SUPERSEDED, not bugged).
- Package re-certification: gates 1–4 and a new panel gate, all PASS. Use `test/identity/run_products.sh`, then
  `compare_all.sh <SLR outputs>`.

**For Marcus:** `notes/ladrillo_v11_paper_number_diff_2026-10-08.md` (+ `outputs/v11_paper_number_diff_20261008.csv`).
- ⛔ Tony's `GMD.Ladrillo.v1_forTonyreview_TW1.docx` still prints the PRE-CMIP7 vv numbers. The note gives printed →
  v1.0 file → v1.1, so both rounds go into ONE docx pass, made when Marcus says so.
- The docx has NOT been edited. Memory `question_is_not_an_edit_request` applies: he or Tony may have it open.
- **The docx pass will carry:**
  - the v1.1 and 10-07 numbers;
  - the label "Ladrillo v1.1";
  - Table A2 on the subsample;
  - the Intro glacier "1.3×" → "1.4×" (stale since 10-07);
  - decisions 2 and 4 once ruled;
  - the 8 wording fixes queued in `handoff_2026-10-01c_gmd_round.md` §1c.

## 4. Next steps after decisions 2 and 4

1. The docx pass, when Marcus green-lights it and has Tony's latest file. Use the redline tooling in
   `deliverables/redline/` and give the round its own `w:date`.
2. The remaining ports into Ladrillo.jl (manifest `handoff_2026-10-07_clean_l27_repo.md` §3):
   - the calibration code (the `calibrate_mcmc_ext.jl` L27 path plus `gate_calibrator_identity` on the renamed headers;
     port the code, do NOT re-run the 2M-iteration chains);
   - the FaIR builders (§3C);
   - the figures (§3E);
   - Table A2 (the research script is `--source=subsample` now);
   - tests, and a `runtests.jl` that works without the research repo;
   - the Manifest trim;
   - then the PRIVATE GitHub repo via `gh` (Marcus makes it public and adds Tony).
3. The suggested task chip "Fix L27 column read in the pulse and EGU drivers" (latent; they run on L24 only today).

## 5. Non-obvious state

- **Colima is still running.** FACTS is not needed for anything above; `colima stop` frees about 3.5 cores. That is
  Marcus's machine, so it is his call or one to ask about.
- **Regression evidence** (the v1.0 reproductions plus their log) is in `outputs/v11_regression_20261008/`
  (untracked).
- **Gate-1 references:**
  - The frozen v1.0 research-kernel dumps are in `Ladrillo/test/identity/out/v10_research_5d3add0/` with
    `SHA256SUMS` (gitignored, about 0.5 GB).
  - `dump_old.jl` now serves only the cases that match the research kernel's settings. Run it twice, once with the
    v1.0 environment variables and once without; the header says how.
- **`Ladrillo/test/identity/fix_effects.jl`** separates the two fixes and is mutation-tested. Its first version used
  the wrong land-water bound (0.012 cm; the measured effect is up to 0.049 cm at 2300) and failed. Memory
  `lws_frame_step_v1` is corrected.
- **Every arm's FIXED arm runs the FaIR mean, even under `--climate=magicc --forcing=raw`.** Check both arms before
  excluding one from a forcing rerun. Memory `fixed_arm_reads_fair_mean_any_climate`.
- **macOS `/bin/bash` is 3.2:** there is no `$BASHPID`, and under `set -u` it silently fails every step.
- **This session ran past 150 tool calls.** Start the next one cold from this file, the CHANGELOG top entries (10-08,
  10-08b, 10-08c) and `INDEX_slr_post.md`.
