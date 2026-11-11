# Handoff 2026-11-11b: GMD decisions answered, IGCC 2025 numbers, Ladrillo.jl v1.0.0 with figure scripts

Session `9fd81c9e` (launched from FaIRtoFrEDI, worked in SLR-RFF-BRICK and Ladrillo), 2026-11-11 13:25 onward.
Previous: `notes/handoff_2026-11-11_gmd_next_pass.md` (its §6 summarises this session too; this note supersedes it).
Task list for the pass: the "Claude's next pass" table in `notes/ladrillo_guidance_2026-11-11.md`.

## 1. What we were working on

Preparing the next Claude pass on the Ladrillo GMD draft (figures, notation, references) and the code release it
describes. The draft itself was NOT edited: Marcus is making his hand edits from the 11-11 guidance first.

- Draft: `deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx`. At 13:25 it was still the 10:19 save; Marcus
  closed Word without saving. **Before the pass, `ls -t deliverables/` and re-extract the newest save** with
  `python/docx_review_extract.py <copy.docx> <outdir>` (run on a copy).
- Repos: SLR-RFF-BRICK `ladrillo-dev` at e78ad64 (pushed). Ladrillo.jl `main` at aaed555 (pushed to
  `msarofim/Ladrillo.jl`, private), local checkout `~/Documents/2026/CodeProjects/Ladrillo` (not `Ladrillo.jl`).

## 2. Decisions (Marcus, 11-11, AskUserQuestion) and why

| # | question | answer | consequence |
|---|---|---|---|
| scope | pass now on the 10:19 save? | **wait for his hand edits** | no draft edit until a newer save exists |
| 1 | paper version | **v1.0, rename the internal tags** | done locally, see §3 |
| 1b | the old "v1.0" options (they reproduce the first build) | **flag `--v0.1`, version-free option names** | `paleo=:per_selection`, `lws_anchor=:obs_at_first_year` |
| 1c | GitHub | **push commits, hold tags**; later "go ahead and push when the identity gate passes" | commits pushed; remote tags still v1.0.0–v1.3.0 |
| 2 | IGCC edition for the heat-inventory numbers | **2025 indicators** (Forster et al. 2026, already in the references) | five numbers change, §4 |
| 3 | Code availability claims every figure and table script | **port the figure scripts** | done, §3 |

Decisions 4–6 of the guidance (Poinelli sentence, Table 2 note 7, Tony's "intermediate model" framing) are his hand
items and were not asked. Fig. 5 moves after the peak-and-decline paragraph unless he objects (guidance default).

## 3. Files

SLR-RFF-BRICK (`ladrillo-dev`):
- d2d112f: `--igcc=2024|2025` on `python/diag_fair_ohc_vs_earth_heat.py`, `diag_te_alpha_matched_scope.py`,
  `diag_te_rate_attribution.py`, `diag_te_driver_timing.py` and the splice builder `build_ohc_spliced_igcc.py`. 2024 is
  still the default and keeps the committed paths (regression: non-provenance columns equal, splice byte-identical).
  New: `data/observations/ohc_spliced_zanna_igcc_igcc2025.csv`, `outputs/*_igcc2025.csv` (four files). CHANGELOG 11-11b.
- e78ad64: §6 of the previous handoff.

Ladrillo.jl (`main`):
- c0a2be6: `python/figures/` = `figlib.py` (cut-down `ladrillo_figs.py`), `plot_hindcast_components.py` (Fig. 1),
  `vv_model_comparison.py` (table for Figs. 2, 3, 6), `plot_model_comparison_components.py` (Figs. 2, 3 and the 2150
  sibling), `plot_future_components.py` (Fig. 4), `plot_vv_gsic_ladrillo.py` (Fig. 5), `plot_vv_responsiveness.py`
  (Fig. 6), `check_figures_identity.py`, `mutation_result.txt`. `data/comparison/` (FACTS n200 components, MAGICC vv
  components and GMST, comparator classes, README; 4 MANIFEST rows). matplotlib 3.10.8 pinned in `requirements.txt`.
  README "Reproducing the figures". CHANGELOG 2026-11-11.
- aaed555: version 1.0.0 (Project.toml, CITATION.cff without `date-released`), the option renames (old names error),
  comments relabel internal builds v0.1–v0.4, README intro and *Versions* renumbered with a v1.0 entry,
  `test/identity/dump_old.jl` translates the package's names to the research kernel's (`RESEARCH_NAME`). CHANGELOG
  2026-11-11b with the tag table.

Memory: `gmd_1111_decisions` (new; pointer in `INDEX_slr_post`), `identity_gate_reference_stale_after_input_rebuild`
(new; pointer in `INDEX_diag`).

## 4. Next steps

1. **When Marcus saves his hand edits:** run the pass from the guidance table on a NEW output file (never overwrite
   the file he edits; toolkit in `deliverables/redline/r1015/`, see §5). Add these from this session:
   - Decision 2 numbers (`outputs/diag_*_igcc2025.csv`): Sect. 2.2.4 obs-implied α **0.141 → 0.139** (still below the
     posterior 5–95 % 0.148–0.186); Sect. 4.1 **1.24 = 1.11 × 1.10 × 1.02 → 1.22 = 1.106 × 1.095 × 1.006**; product range
     **1.21–1.27 → 1.19–1.27** (IGCC end 1.192, 1993–2024; Cheng 1.274 unchanged); era ratio "0.21 for observed 0–2000 m
     ocean heat" **→ 0.20**. Unchanged: about 91 %, about 11 %, roughly 9 %. ⚠ Rounded to two decimals the factors
     multiply to 1.23, so write three decimals or reword; the wording is Marcus's call.
   - Code availability: "Ladrillo v1.0 (Ladrillo.jl, git tag v1.0.0)"; title and Conclusions to v1.0.
2. **Open question for Marcus:** the Code availability sentence also claims (a) Table 4's script
   (`python/scope_ladrillo_vs_brick20_scorecard.py`, the RMSE-ratio scorecard) and (b) the calibration drivers and the
   target-building scripts. Ladrillo.jl ships neither (its README lists calibration as in progress). Offered: port
   Table 4 now by the figure method; for calibration, port before release or narrow the sentence.
3. **At release** (Marcus's go): delete the remote tags v1.0.0–v1.3.0, push v0.1.0–v0.4.0, tag v1.0.0 at the release
   commit, set `date-released` in CITATION.cff, then Zenodo.
4. Optional, still offered: seed provenance in the figure-input CSVs (memory `gmd_seed_claim_unsupported_by_figure_inputs`).

## 5. Non-obvious state

- **Local tags differ from GitHub.** Local: v0.1.0 a2bb3b0, v0.2.0 78b03c6, v0.3.0 c526331, v0.4.0 01462a8 (annotated,
  original message plus a rename note). Remote: v1.0.0–v1.3.0 at the same commits. A `git fetch` brings the old names
  back locally. `push.followTags` is unset, so `git push origin main` pushes no tags.
- **Figure byte-identity needs the pinned runtime** (`~/climate-env`: matplotlib 3.10.8, numpy 2.4.2, pandas 2.3.3).
  `python python/figures/check_figures_identity.py ~/Documents/2026/CodeProjects/SLR-RFF-BRICK` compares against the
  research `figures/paper/`. Ladrillo.jl `outputs/` is gitignored; its projection products were made on 10-08 and are
  equal to the research files (checked this session on every non-provenance column).
- **Identity gate references** live in Ladrillo `test/identity/out/` (gitignored). K4's were replaced this session; the
  stale pair is in `out/quarantine/20261111_k4_stale_vv_forcing/` with a README.
- **IGCC 2025 EEI file** ends in one row with no time stamp (0–700 m = 350 ZJ); the scripts drop it and never date it.
  The non-ocean terms still end in 2020 in both editions. The 2006–2020 window moves more (1.284 → 1.152) because the
  2025 edition revises 0–700 m heat in 2006–2012; the draft quotes nothing from that window.
- **Fig. 1 targets:** the research working-tree `outputs/recalib_targets_ext.csv` is the Frederikse build again (md5
  070f74ab, equal to Ladrillo's `data/observations/calibration_targets.csv`); the research script's own comment warns that
  this path held the IMBIE build for a while.
- **Research-script defects the ports found (not fixed):** the Fig. 2/3 caption sentence is garbled ("…scenarios ones")
  and kept verbatim in both repos so captions match; `plot_hindcast_components.py` hardcodes its y-label and has a stale
  glacier comment; `plot_vv_gsic_wr_vs_ladrillo.py` reads `outputs/vv_gsic_2300.csv` even with `--ladrillo-only`, has an
  L24 docstring, and rejects CHECK verdicts where `ladrillo_figs.gate_ladrillo` stamps them; the old fixed-arm
  `figures/paper/vv_gsic_ladrillo_L27_2300.png` still carries the title removed on 11-05.
- **Editing the draft:** `deliverables/redline/r1015/build.sh <fresh workdir> <out.docx>` with `trackedit.py`,
  `edlib.py`, `comments_lib.py` (`notes/handoff_2026-10-15b_brick20_swap_tw2_pass.md` §2). Never write docx XML with
  ElementTree; verify with an independent reader; comment ids change on every save, so refer to page and first words.
- Marcus's word-choice rules apply to any text put into the draft; he drafts main prose, and tracked edits by Claude are
  for fixes he asked for. Tony's tracked edits stay unless incorrect.
- Scratchpad is gone with this session.
