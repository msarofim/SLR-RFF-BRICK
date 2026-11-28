# Handoff 2026-11-27b: why the SLR models order as they do on the pulses, and CH4 forcing in FaIR vs MAGICC

Session b18d2ca8 (launched from FaIRtoFrEDI; code in `FaIRtoFrEDI/magicc_comparison/poster_agu26/` and
`MAGICC/slr-refresh/`). It picked up from `handoff_2026-11-27_gmd_swhid_and_rising_seas.md` (session 6596ba3b).
Read with `~/.claude/CLAUDE.md`, the FaIRtoFrEDI CHANGELOG entries 2026-11-27 (c), (d) and (e), and the memories
`pulse_model_ordering_2100`, `facts_blind_modules_expected_response` and `ch4_gwp_samebg_fair_vs_magicc` (all three
are linked from `INDEX_cmp_pulse_dur.md`). Units below: mm of sea level per GtCO2e at 2100 (GWP100 27.9), paired mean,
mean of the six van Vuuren scenarios, poster basis, unless stated.

## 1. What was worked on

**A. Why the models order as they do at 2100** (Marcus: "Can we explain why FACTS is lower than all the other models
for the CO2 pulse, and why FACTS and MAGICC are lower than BRICK and Ladrillo for the CH4 pulse?").
`diag_pulse_ordering_2100_agu26.py` → `answers/ordering_2026-11-27/` (158 gates).
- CO2: Ladrillo 0.156, BRICK 2.0 0.165, MAGICC-SLR 0.146, FACTS wf2f (LARMIP) 0.088, wf1f (AR5) 0.063.
  The gap is Antarctic (0.094, 0.113, 0.068 vs 0.018 and −0.007). Outside Antarctica all five are 0.053–0.077.
- The DAIS Antarctic mean is mostly the fast-dynamics threshold premium (Ladrillo 0.90 of it; BRICK 2.0 at or above
  the whole mean). Without it, the DAIS pulse response is at or below LARMIP's.
- CH4: Ladrillo 0.343, BRICK 2.0 0.371, MAGICC-SLR 0.218, LARMIP 0.216, AR5 0.139. FACTS is low for the same Antarctic
  reason. MAGICC is low because of its climate: Ladrillo and BRICK 2.0 on MAGICC's climate give 0.233 and 0.205.
- MAGICC has no fast dynamics; its Antarctic response is state-dependent discharge. The scenario pattern depends on
  the horizon: at 2300 MAGICC is above both DAIS models in vvM and vvH; at 2100 only in vvH.

**B. Would other FACTS workflows differ?** `diag_facts_blind_expected_pulse_agu26.py` →
`answers/facts_workflows_2026-11-27/` (69 gates). deconto21 and bamber19 pick a sample set at random with a
probability linear in integrated 2000–2099 GSAT, so a pulse changes almost no picks at n=200 (expected flips
0.03–0.10 per cell) but has a nonzero expected response. Implied wf3f 0.119 (CO2) / 0.282 (CH4), wf4 0.133 / 0.310,
against wf2f 0.088 / 0.216.

**C. Same-background CH4 GWP, FaIR vs MAGICC.** `diag_ch4_gwp_samebg_agu26.py`; MAGICC reruns by
`run_gwp_samebg_magicc_20261127.sh` (12 runs, 61 min) → `answers/ch4_gwp_2026-11-27/`. GWP100 49.9 vs 34.7; CH4
effective lifetime 17.2 vs 13.8 yr; ozone ERF per ppb 2.2x MAGICC's. Forcing carries 71 % [68, 74] of the FaIR/MAGICC
gap in the 2100 CH4:CO2 warming ratio (1.70).

**D. CO2 airborne split** (checking the footnote's carbon-cycle sentence). `diag_co2_airborne_agu26.py` →
`answers/ch4_gwp_2026-11-27/co2_airborne_fair_vs_magicc.csv`. MAGICC keeps 19 % more CO2 airborne over 100 years
(7.63 vs 6.42 ppm yr per GtCO2) with 7 % less ERF per ppm (11.4 vs 12.3 mW), so its CO2-only forcing is 10 % higher.

**E. MAGICC's CH4 lifetime temperature feedback switched off** (Marcus: "run the MAGICC test with the temperature
feedback off", then "Can we do a shorter test than a full hour?"). `run_ch4tfoff_magicc_20261127.sh` (first 100
members, vvVL/vvL/vvH, CH4 pulse only, 4 min) and `diag_ch4_tfoff_agu26.py` (51/51 gates). Off ÷ on, same members:

| | VL | L | H |
|---|---|---|---|
| Pulse lifetime over 100 yr | 1.19 | 1.18 | 1.24 |
| AGWP100 | 1.15 | 1.13 | 1.16 |
| Warming at 2100 | 1.39 | 1.31 | 1.45 |
| Sea level at 2100 | 1.22 | 1.23 | 1.23 |

- Closes 58 % (VL) and 75 % (H) of the FaIR-MAGICC lifetime gap and 32–47 % of the AGWP100 gap; ozone is most of the
  rest. In L, FaIR is already at or below MAGICC (high NOx), so switching off overshoots.
- With the feedback off, MAGICC's vvH background lifetime rises 13.6 → 17.1 yr by 2100, as FaIR's does.
- NOx still matters: in vvVL (NOx 113 → 21 Mt/yr, 2030 → 2060) MAGICC's lifetime with the feedback off goes
  14.0 → 14.3 while FaIR's goes 12.5 → 18.3.

**F. Writing support** (Marcus's prose; Claude suggested edits when asked):
- Fact-check of the Rising Seas pulse paragraph and footnote 1. Paragraph fixes suggested: name the year (the scenario
  pattern holds at 2300, not 2100); MAGICC's Antarctic response is state-dependent discharge, not fast dynamics;
  "DeConto" spelling and their expected values (CO2 0.12/0.13 is "closer to", CH4 0.28/0.31 is "comparably high");
  "smaller climate response to CH4".
- Footnote, last suggested wording (21:07 UTC), after Marcus asked whether to drop NOx (answer: keep it):
  > FaIR's CH4 pulse produces more forcing than MAGICC's, for two reasons. First, the CH4 lasts longer in FaIR. Both
  > models use the same projected decline in NOx emissions, but FaIR's CH4 lifetime lengthens much more in response,
  > and MAGICC's lifetime also shortens as the climate warms, which FaIR's does not. Second, FaIR produces more than
  > twice as much ozone per unit of CH4.
- Substack note plus Facebook, Bluesky and LinkedIn versions. After Marcus's "I don't want to overpromise", Facebook
  and LinkedIn no longer say sea level rise added to this year's flooding. No affiliation (informal output).
- Bob Kopp: a short explanation of why the FACTS runs end in 2100, then a review of Marcus's reply email (typos;
  "picks scenario sets at random, with odds based on warming, so small pulses usually yield no changes"). Whether
  the email was sent is not confirmed here.

## 2. Decisions and rationale

- **Short feedback-off test** (Marcus asked for less than an hour): 100 members × 3 scenarios. The first 100 members
  warm about 10 % less at 2100 than all 600, so results are PAIRED off ÷ on ratios applied to the 600-member values.
  The first gap-closure shares mixed 100- and 600-member levels and were replaced.
- **Gates changed, with reasons in each docstring and the CHANGELOG:** [AGWP-MATCH] compares at the reference's
  printed precision (`%.6g`); [PRE-SWITCH-CH4] replaced a pre-2015 GMST identity gate that failed at 5e-7 K, because
  MAGICC scales halocarbon lifetimes by the OH lifetime (FGAS/MHALO_USE_TAUOH_VAR=1) and their regional RF split
  depends on them. Mutations `agwp`, `pre` and `zero` each fail their gate.
- **Correction made during the session:** the AR6 drawnset does NOT set CH4_TAUTEMPSENSITIVITY per member; all 600
  use the default 0.07. The per-member claim came from an AR5-FOD drawnset file we do not run.
- **AR5-FOD config files not used** (Marcus: "Should we be using the CH4 config files for MAGICC uncertainty runs? If
  so, add a note to the MAGICC memory file"). Answer was no: they are whole members of a different 2019 parameter set
  (318 of 600 present, climate sensitivity drawn jointly), so grafting by index has no basis. No "use them" note was
  added; the facts went into `ch4_gwp_samebg_fair_vs_magicc` so nobody grafts them later.
- **Neither model samples CH4 lifetime uncertainty** (FaIR 1.6.0 pulse lifetime is identical across all 841 configs;
  MAGICC's ±5 % comes only from member warming). Explained, not a bug. Marcus has not ruled on an arm for it.

## 3. Files

- **FaIRtoFrEDI `heat-ed-morbidity`, committed and pushed:** af22476, 43644f1, 9872608, db2671c, b278f75, be781a3,
  28e9bbe. Scripts in `magicc_comparison/poster_agu26/`: `diag_pulse_ordering_2100_agu26.py`,
  `diag_facts_blind_expected_pulse_agu26.py`, `diag_ch4_gwp_samebg_agu26.py`, `diag_co2_airborne_agu26.py`,
  `diag_ch4_tfoff_agu26.py`, `run_gwp_samebg_magicc_20261127.sh`, `run_ch4tfoff_magicc_20261127.sh`. Answers in
  `answers/{ordering,facts_workflows,ch4_gwp}_2026-11-27/`, each with a README (the ch4_gwp README has the CO2 and
  feedback-off addenda).
- **MAGICC `slr-refresh` (local only, never push; branch `vv-slr-runs`; `data/` and the frozen copies are untracked
  like earlier frozen copies):** `notebooks/_frozen_302e_gwp_20261127.py`, `notebooks/_frozen_302e_ch4tfoff_20261127.py`;
  logs `gwp_samebg_run_20261127.log`, `ch4tfoff_run_20261127.log`; outputs `data/processed/gwp_samebg_20261127/`
  (GWPSAMEBG_ prefix) and `data/processed/ch4_tfoff_20261127/` (CH4TFOFF_ prefix). The prefixes keep the poster's
  PULSEVV one-match globs from seeing these files.
- **Memory:** `pulse_model_ordering_2100`, `facts_blind_modules_expected_response`, `ch4_gwp_samebg_fair_vs_magicc`
  (new or extended this session); `facts_version_plan` (Bob Kopp exchange, added with this handoff); the
  `INDEX_cmp_pulse_dur.md` pointer line.
- **Rising Seas local files predate Marcus's 11-27 afternoon paragraph.** `RisingSeas_substack.html` and
  `RisingSeas.captions.docx` were last written 12:26 and do not contain the paragraph he pasted (no "Bamber"). He is
  editing elsewhere; do not rebuild the HTML from the local docx without asking.
- Scratch only: `co2_airborne_check.py` in this session's scratchpad, superseded by `diag_co2_airborne_agu26.py`.

## 4. Open items and next steps

1. **Marcus:** settle the pulse paragraph and footnote in the post, and post the social versions.
2. **Marcus:** the Bob Kopp email (sent status unknown). Post-AGU, collaborate with Bob and/or Kelly McCusker on the
   two FACTS pulse issues (FittedISMIP's post-2100 rate extension; DeConto/Bamber's random sample-set pick).
   Computing the DeConto/Bamber expected response directly is already scripted (item B).
3. **Offered, not accepted:** a ~4-minute MAGICC rerun with the feedback off and the starting lifetime retuned so the
   2020 lifetime matches the feedback-on run. This would separate the 8.5 % level shift from the trend. Which config
   parameter to retune has not been checked.
4. **Marcus to rule:** whether to add a CH4 lifetime-uncertainty sensitivity arm in both models, and from which
   published range (same range in both).
5. **Not separated:** MAGICC's weaker NOx response vs its stronger CH4 self-feedback (exponent ~0.39 vs FaIR's ~0.23,
   read from the formulas, unmeasured).
6. **Not attempted:** a constant-background MAGICC GWP (needs per-member inverse emissions). Never compare the
   same-background 49.9 / 34.7 with AR6's 27.9 or FaIR's constant-2019 36.7.
7. The poster itself runs in its own session (`agu26-pulse-poster`). Nothing in this session changed poster panels.

## 5. Non-obvious state

- `diag_co2_airborne_agu26.py` patches `diag_ch4_gwp_samebg_agu26.run_fair`'s source via `inspect`/`exec`; if
  `run_fair` changes, it exits with "patch points not found exactly once" rather than running stale code.
- The MAGICC run scripts call the frozen copies. Never edit a frozen copy while a run is using it.
- MAGICC CH4 lifetime source: `METHANE` in `MAGICC7.f90`; defaults in `magiccv.7.5.3/run/MAGCFG_DEFAULTALL.CFG`
  (CH4_INCLUDE_TEMPFEEDBACK=1, CH4_TAUTEMPSENSITIVITY=0.07). The AR6 drawnset sets neither.
- The CO2-airborne and feedback-off outputs were each run twice and found byte-identical before commit (b278f75,
  28e9bbe); their provenance columns carry the script commit. The other answer folders were not re-checked this way.
- SLR-RFF-BRICK `ladrillo-dev` had one unpushed commit from session 6596ba3b (5970c9d, its handoff); it was pushed
  with this handoff. The repo's other uncommitted files (`INPUTS.manifest.json`, the vvHL `fair_cube_gmst_*` CSVs)
  are not from this session and were left alone.
