# Handoff — L24 documentation: shared-ready state (09-13 → 09-14); NEXT = Tony's feedback, then the pulse analysis

**Start here.** Continues `handoff_2026-09-13_l24_documentation.md` (its §1 task is done; its §4 traps
still apply). **Read this note, `INDEX_cmp.md` and `INDEX_cmp_magicc.md` before touching the
deliverable, the comparison figures or FACTS.** CHANGELOG 09-13 → 09-14d is the primary record.

**STATUS:** `SLR-RFF-BRICK` `ladrillo-dev` clean and PUSHED at db1e225. `facts`
`slr-comparison-arm` committed at 0010d49f — **no pushable remote** (origin is the
radical-collaboration upstream; no fork exists). `FaIRtoFrEDI` `heat-ed-morbidity` pushed.
**The deliverable was shared with Tony Wong and collaborators on the afternoon of 09-14** (Marcus).
**TORCH VERDICT:** everything in this arc was local and short (FACTS 5 min/experiment with
emulandice, projections 1 min, figure build 20 s). Nothing belongs on Torch.

---

## 1. ⭐ NEXT

1. **Tony Wong / collaborator feedback** on the shared .docx. Same drill as every comment round:
   read the comments file, apply what is technical, hand prose back to Marcus, CHANGELOG each item.
   `deliverables/Ladrillocomments.9.13.26.docx` is still **untracked and was EMPTY** every time it
   was read (3 KB `document.xml`); Marcus's 09-13/14 comments came verbally instead.
2. **The pulse analysis** — unchanged from the 09-13 handoff §1: `INDEX_cmp_pulse.md` (stage state,
   tap ruling, the OPEN cross-model figure design) and `INDEX_cmp_pulse_dur.md`. Inputs now on hand:
   `outputs/vv_responsiveness_L24.csv` (per-K numbers, now with the emulandice points at 2100);
   [[facts_blind_to_a_pulse]] and the 09-12c FACTS rule still govern any FACTS-past-2100 panel.
3. **Deferred code cleanups** (CHANGELOG 09-14d, none numerical): the 19 literal
   `tap4p69K_V5p64m_tau800` stems → `ladrillo_figs.joint_stem()`; the duplicated palette / label /
   `TAG_DESC` tables across the plot scripts; `calibrate_mcmc_ext.jl`'s 2400-line history (the
   A6-amp block, the adcov ladder, `OLD35/38/39` covariance branches); `dang` → `total` rename.
   **Block rename `SLOWP`/`FAST` → `SLOWG`/`FASTG` (Marcus 09-14; the G disambiguates from Greenland's
   fast/slow channels — the document already uses the new names with a code-name footnote).** Touches
   48 scripts and the column headers of 44 data files including the L24 posterior (`gic_*_SLOWP`), so it
   needs a name-map for every reader of an existing chain/subsample; do it with the L25 cleanup, never
   in place on shipped files.
4. **Prose items handed to Marcus, not applied** (agent review 09-14): the "**Sampler.**
   Over-dispersed chain starts." fragment; SLOWP/FAST/R19, joint/fixed arm, L24, R̂, "discrepancy
   bases" used before definition; the three longest paragraphs; Table 3's checksums/fetch dates.

## 2. WHAT CHANGED 09-13 → 09-14 (numbers in the CHANGELOG entries named)
- **FACTS emulandice on the seven van Vuuren scenarios at 2100** (09-14c). The 08-31 "per-SSP-trained,
  keyed on the Scenario label" reason was WRONG — the module tags every row `"FACTS"` and runs on the
  GSAT path; only the 2100 cap is real. `EMU_KEYS` (3 SSP + 7 vv base keys) gates
  `facts/build_shared_configs.py` and `extract_facts_shared_components.py`; 378 rows added to
  `outputs/facts_components_shared_n200.csv`, existing rows byte-identical. FIG 2 bracket now spans
  seven workflows; FIG 7 has emu points at 2100. `emuAIS` is scenario-invariant at 2100 (9.1–9.4 cm).
- **FACTS past 2100 re-confirmed** from the tables the figures draw: Greenland at 2100 only;
  Antarctica larmip-only at 2150, none at 2300; glaciers/TE/LWS everywhere; no totals past 2100.
- **Terminology:** "tap" → "above-threshold discharge channel" (document + user-visible strings;
  identifiers keep `tap`); "markers" → "scenarios" (Marcus did the prose; five figures re-emitted).
- **Framing (Marcus's intro edit, propagated 09-14):** ONE departure from BRICK's philosophy — the
  threshold channel; the Antarctic amplification is "updated from the paleo-equilibrium ratio to a
  CMIP6-based one"; Greenland and glacier amplifications are observation-fitted. Table 1 note 4,
  Table 3's CMIP6 role (had wrongly credited CMIP6 with the glacier amp priors), the Greenland
  "Amplification" line and the Antarctic-amp paragraph (identifiability, reversion cost, frame span)
  follow it. Draft with receipts: `deliverables/draft_2026-09-14_philosophy_reframe.md`.
- **Three BRICK-philosophy arms** (09-13j, `python/diag_brick_philosophy_arms.py`, fixed-driver):
  no channel −41 cm at ssp585-2300 only; constant Greenland amp +1–9 cm; **AIS amp fixed at stock
  1.196 +17 cm at ssp245-2100, +42 at 2300** (projection-side override; refit slope corroborates).
- **R19 amplification** (09-13e): projection-side only; CMIP6 future ratio 0.77 (no Southern-Ocean
  catch-up to 2100). **Berkeley glacier driver** (09-13f): scoped, REJECTED by Marcus, memory
  `berkeley_glacier_driver_rejected` — don't re-raise.
- **GSIC text:** per-block Farinotti volumes at 2000 (12.7 / 9.4 / 6.9 cm SLE); "bracketing
  Farinotti" retracted (MAGICC's Marzeion-2012 scope omits RGI 19); SLEIP-type row added then
  DROPPED by Marcus (classification survives in CHANGELOG 09-13b / memory only).
- **Tables 1–2 widths:** `balance_table_widths.py` gives nine-column tables measured word floors
  (Aptos, 8 pt) and a half-weighted attribute column. Unverified in Word itself.
- **Document accuracy pass** (09-14d): 59 checks; corrected 2.7 → 2.6 (no-channel Greenland ratio;
  2.7 was L14's), 19 → 22 cm (AIS-1.196 on ssp585-2300, total basis), 15–20 → 15–22 cm, λ prior
  values per model, "panel (e)", "BRICK2.0", FaIR label. The 35.1 / +0.04 cm channel figures ARE
  traceable (joint fairunc cells tap vs no-tap) — an agent said otherwise; it was wrong.
- **Code-cleanliness pass** (09-14d): comments/labels/usage/default-tag only; `LADRILLO_POSTERIOR_CSV`
  and eight Python defaults now L24. Proof of inertness: L24 re-projection byte-identical; full
  deliverable build → SSP table unchanged, 0 benchmark verdicts moved.

## 3. RULINGS THIS ARC (Marcus)
1. Berkeley glacier driver: disproven, stay with L24 as is.
2. No SLEIP parametrisation-type row; attribute column narrower.
3. "Above-threshold discharge channel" (closest published phrasing: FRISIA's "additional discharge
   above a GSAT anomaly threshold", SLEIP §3.3).
4. One departure from BRICK's philosophy (his intro wording stands everywhere).
5. Less detail on inventories: list the 2000 numbers + a "not every model covers all 19 RGI
   regions" caveat.
6. Run emulandice on the van Vuuren scenarios through 2100.

## 4. ⚠ NON-OBVIOUS STATE / TRAPS
- ⛔ **A Word buffer that predates a rebuild will REVERT the rebuild on its next save.** Happened
  TWICE on 09-13 (14:55 and 15:05): the W&R fix and the Table 2 row vanished, Marcus's edits landed.
  Detection: `python3 deliverables/sync_filled_from_docx.py --verify` then `git diff FILLED.md`
  against HEAD — a diff that REMOVES your last change is the clobber. Recovery: sync → re-apply →
  docx step. **Ask Marcus to close Word (or reopen the file) after every build**; check
  `ls deliverables | grep '^~'` for the `~$` lock before building.
- ⚠ **The sync overwrites uncommitted FILLED.md edits.** Order is sync → edit → build → commit,
  never edit → sync. (Caught 09-14: `cp` of the edited file saved it.)
- **Marcus edits between turns** — his 10:32 edits (FACTS post-2100 paragraph split, a MAGICC
  Low-to-Neg Greenland tail paragraph, "SSP comparisons" heading) are synced and committed at
  db1e225; the .docx is canonical and was NOT rebuilt after them (no need — the docx is the source).
- **Background Bash calls die at 10 min.** A 40-min FACTS runner launched through the tool was
  killed at the timeout; the in-flight docker container survived. Pattern that worked: kill the
  runner, launch a continuation with `nohup bash script.sh > log 2>&1 < /dev/null & disown` (no
  `setsid` on macOS), poll the log. Count outputs by a pattern that matches
  (`grep -c emulandice`, not `'^emu'` — filenames start with the experiment key).
- `facts` vv outputs pre-emulandice are backed up in the 09-14 session scratchpad only (untracked in
  git; `.nc` are gitignored). The seven vv `config.yml` are tracked and now carry the emu blocks.
- `outputs/facts_components_shared_n200.csv` no longer matches `benchmark/reference/_fixed/`'s copy
  (added vv rows only); bench prints "LITERATURE ARM MOVED" but scores the frozen SSP arm, which is
  unchanged. A `--freeze-fixed` is Marcus's call.
- `data/MimiBRICK/parameters_subsample_brick_mengel_L24aisamp1p196.csv` (10 MB, the AIS-1.196
  override posterior) is untracked; regeneration is in `diag_brick_philosophy_arms.py`'s header.
- `outputs/gis_amp_shape_const{,_meta}.csv` (S=1 arm) are tracked; `LADRILLO_GIS_SHAPE=gis_amp_shape_const`
  selects them — never for a deliverable.
- **Memory:** `berkeley_glacier_driver_rejected` (new), `sleip2026_emulator_intercomparison` (Ladrillo
  Table-2 types on record, row dropped), `facts_shared_climate_arm` (emulandice correction appended),
  `INDEX_slr` (one pointer line added). `INDEX_ccx` / `INDEX_cmp_pulse` still sit ~17 KB — split
  before the next addition.

## 5. FILES (this arc)
**New:** `python/diag_glac_amp_cmip6_future.py`, `python/diag_brick_philosophy_arms.py`,
`deliverables/draft_2026-09-14_philosophy_reframe.md`, `outputs/diag_glac_amp_cmip6_future.csv`,
`outputs/diag_brick_philosophy_arms.csv`, `outputs/gis_amp_shape_const{,_meta}.csv`,
`outputs/ssps_components_2300_L24{aisamp1p196,…_shapeconst}.csv`. **Changed:**
`deliverables/balance_table_widths.py` (word floors), the deliverable + FILLED.md, 14 figures,
`outputs/facts_components_shared_n200.csv`, `vv_model_comparison_L24.csv`, `vv_responsiveness_L24.csv`,
10 Julia + 12 Python files (comments/labels/defaults only), `facts/build_shared_configs.py`,
`facts/extract_facts_shared_components.py`, `facts/build_shared_climate_nc.py`, seven vv `config.yml`.
