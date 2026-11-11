# Handoff 2026-11-11: the GMD draft's next Claude pass (figures, notation, references)

Session `b988dbe6` (launched from FaIRtoFrEDI, worked in SLR-RFF-BRICK and Ladrillo.jl), 2026-10-17 → 11-11.
Previous handoff: `notes/handoff_2026-10-17_gmd_followups_lin2026.md`.

## 1. What we were working on

The Ladrillo GMD model-description paper. Marcus is making one more round of hand edits from
`notes/ladrillo_guidance_2026-11-11.md` (docx: `deliverables/ladrillo_guidance_2026-11-11.docx`). After that round he
will ask for **the next Claude pass**: "swap in the new figure versions as well as make notation and reference fixes".
The full task list for that pass is the "Claude's next pass" table in the 11-11 guidance. Six decisions in that guidance
change what the pass includes; wait for his answers.

- Draft: `deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx`, last saved 2026-11-11 10:19. Marcus edits this
  file directly; he will save a new state before the pass. **Re-extract before editing anything.**
- Repos: SLR-RFF-BRICK `ladrillo-dev` (HEAD after this note's commit); Ladrillo.jl `main` 6ecfc4d, tag `v1.3.0`,
  Project.toml 1.3.0, private repo `msarofim/Ladrillo.jl`.

## 2. Decisions made (with reasons)

- **Joint arm for every result** (Marcus 11-07, option b). The fixed arm stays only for the two Sect. 3.2 checks
  (projection R̂, refit comparison), where climate spread would hide chain differences. Fig. 5 re-rendered joint (1b8927d).
- **Poinelli et al. 2026** (Marcus 10-21): cite as a Thwaites analysis; no comparison with single-sheet Ladrillo. On
  11-11 Marcus's own draft added "this is suggestive that the increase from fast dynamics in Ladrillo are not
  unrealistic"; the guidance recommends his 10-21 wording instead (Decision 4). Memory `poinelli2026_thwaites_vs_committed_loss`.
- **Table A1 shows the four log₁₀-sampled rows in ln** (Marcus 11-10, "Option 1"). Code and posterior stay log₁₀;
  converting the code was rejected because exp(x ln 10) ≠ 10^x in the last bits for 67–100% of draws, which would move
  every projection at rounding level. Builder `python/ladrillo_prior_posterior_table.py` (b8d7fdf) writes the ln rows
  and footnote ᶜ into `outputs/ladrillo_prior_posterior_L27.md`; its CSV keeps log₁₀ because two AIS diagnostics read
  prior bounds from it. Gate [LN-DISPLAY], mutation-tested.
- **RGI 19 amplification prior stays 0.72.** No recorded derivation; re-centring on 0.68 moves glacier medians ≤ 0.03 cm
  (`outputs/diag_r19_amp_prior_reweight_L27.csv`, exact importance reweighting).
- **A_b enters the calibration** through the GlacierMIP3 term (amp × warming level) and κ's prior centre, but not through
  the drivers (built once at the prior centres because the glacier record ends before A_b matters). Corrected 3a93d94.
- **Glacier abstract numbers:** 9–14 cm (27–56%) less melt than BRICK 2.0 at 2300; High − Very Low range 47% larger
  (bootstrap 40.5–53.7%, `outputs/diag_glacier_range_bootstrap_L27.csv`). The inventory explains only 10–20% of the gap
  (`outputs/diag_glacier_inventory_ablation_L27.csv`).
- **Antarctic amplification, joint arm:** +1σ raises AIS at 2300 by 38.8 cm (SSP2-4.5, 15%) and 24.9 cm (SSP5-8.5, 5%);
  reverting to 1.196 adds 11 / 32 cm and 6 / 13 cm (`outputs/diag_ais_amp_joint_L27.csv`; identity gates pass; NOT
  re-run for byte identity because the machine was at load ~22).
- **Tony's tracked edits are not to be rewritten** unless incorrect (Marcus 11-11). None were found incorrect.

## 3. Files

Created or changed this session (all committed and pushed on `ladrillo-dev`):
- `notes/ladrillo_guidance_2026-11-07.md` (+ docx; the 11-07 docx is OLDER than its md because Word held it open on
  11-10) and `notes/ladrillo_guidance_2026-11-11.md` (+ docx). The 11-11 guidance supersedes the 11-07 one.
- `notes/gmd_draft_review_2026-11-05.md`.
- `python/docx_review_extract.py` (new 11-11): read-only extraction of paragraphs with page numbers, tracked changes,
  comments; `--author="Tony Wong"` lists his surviving insertions. Reproduces the session's extraction byte for byte.
- `python/ladrillo_prior_posterior_table.py`, `outputs/ladrillo_prior_posterior_L27.{md,csv}`.
- Diagnostics: `julia/diag_ais_constant_climate_vs_poinelli2026.jl`, `julia/diag_ais_amp_joint.jl`,
  `julia/diag_glacier_inventory_ablation.jl`, `python/diag_glacier_range_bootstrap.py`,
  `python/diag_r19_amp_prior_reweight.py`, `python/plot_vv_gsic_wr_vs_ladrillo.py` (`--arm=joint`), and the panel-letter
  helper `panel_title()` in `python/ladrillo_figs.py` used by the four figure builders.
- `CHANGELOG.md` entries 2026-10-21 through 2026-11-11.

Ready for the figure swap (`figures/paper/`, each with a `.caption.txt`): `hindcast_components_L27.png` (Fig. 1),
`model_comparison_components_vv_L27_2100.png` (Fig. 2), `model_comparison_components_vv_L27_2300.png` (Fig. 3),
`future_components_vv_L27_joint.png` (Fig. 4), `vv_gsic_ladrillo_L27_2300_joint.png` (Fig. 5),
`vv_responsiveness_L27.png` (Fig. 6).

## 4. Next steps (the pass), and what is open

Do these only after Marcus's hand-edit round and his answers to the six decisions in the 11-11 guidance:

1. **Version (Decision 1).** Recommended: v1.0. Ladrillo.jl already has tags `v1.0.0` (2026-10-08, older build),
   `v1.1.0`, `v1.2.0`, `v1.3.0`. Plan: rename them `v0.1.0`–`v0.4.0` (local and remote), set 1.0.0 in Project.toml,
   CITATION.cff and README, tag `v1.0.0` at the release commit, record the mapping in both CHANGELOGs. Tag renames on
   the remote are outward-facing: confirm with Marcus before pushing. Text: title, Conclusions, Code availability.
2. **IGCC edition (Decision 2).** Recommended: rerun `python/diag_fair_ohc_vs_earth_heat.py` on the 2025 indicators
   (`data/observations/raw/igcc2026/data-2026.06.02/data/earth_energy_imbalance/earth_energy_imbalance.csv`). The script
   fails on that file as is (`IntCastingNaNError` converting `timebound_lower` to int; the layout differs from the 2024
   file). Then update the 91%, α 0.141 (Sect. 2.2.4) and 1.11 / 1.10 / 1.02 (Sect. 4.1) in the text.
3. **Code availability (Decision 3).** Recommended: copy the figure scripts into Ladrillo.jl before release (it ships only
   the Table 5 script); otherwise narrow the sentence.
4. **The pass itself:** figures (and move Fig. 5 after the peak-and-decline paragraph if Marcus agrees), equations on
   separate lines, Table A1 ln rows + footnote + two description fixes, notation, dashes/units, references to add and
   fix, citation forms, runtime re-measure on the Zenodo BRICK 2.0 posterior. Exact list: the 11-11 guidance table.
5. **Optional, offered:** add seed provenance to the figure-input CSVs so the paper can again say seeds are recorded in
   the files each figure reads (memory `gmd_seed_claim_unsupported_by_figure_inputs`).

## 5. Non-obvious state

- **How to edit the draft.** The 10-15 pass built tracked edits with the toolkit in `deliverables/redline/r1015/`
  (`build.sh <fresh workdir> <out.docx>`, `trackedit.py`, `edlib.py`, `comments_lib.py`); see
  `notes/handoff_2026-10-15b_brick20_swap_tw2_pass.md` §2 and memories `docx_collaborator_ins_attrs`, `docx_ns_prefixes`,
  `marcus_edits_docx_directly`. Never write docx XML with ElementTree. Verify with an independent reader. Write a NEW
  output file; never overwrite the file Marcus has open (`lsof | grep <name>` showed Word holding the 11-07 guidance).
- **Comment ids change on every save.** Use page + first words (the guidance does).
- **The 11-11 guidance corrected two of my 11-07 suggestions** that are now in the draft: the seed-recording sentence
  (false; replacement given) and the Greenland amplification bound (2.28, not 2.29). Check Marcus adopted both.
- **Numbers rechecked 11-11** against `outputs/vv_model_comparison_L27.csv` (2300, Ladrillo − BRICK 2.0 medians):
  glaciers −9.2 to −14.1; Greenland −3.1 to −8.9 (six scenarios), +20.4 High; Antarctica within 7.2 except High-to-Low
  −18.2 and High +31.4; thermal expansion +0.8 to +5.9. FACTS is relative to baseyear 2005, the other models to
  1995–2014 (standing approximation).
- **Scratchpad is gone** with this session; everything needed is in the repo or the paths above.
- Marcus's word-choice rules (`~/.claude/CLAUDE.md`) apply to any text put into the draft: no em-dash asides, no ", not
  X" tags, no "own" as emphasis, no kickers, no absolutes. He drafts main prose; tracked edits by Claude are for fixes
  he has asked for.

## 6. Update, 2026-11-11 afternoon (continuing session)

**Marcus's answers (AskUserQuestion):** Decision 1 = v1.0 with the internal tags renamed; Decision 2 = IGCC 2025
indicators; Decision 3 = port the figure scripts. Pass scope = **wait for his hand edits** (the draft on disk was still
the 10:19 save). Decisions 4–6 are his hand items. Memory `gmd_1111_decisions`.

Done:
- **Decision 2 priced** (SLR d2d112f). `--igcc=2025` on `diag_fair_ohc_vs_earth_heat.py`, `diag_te_alpha_matched_scope.py`,
  `diag_te_rate_attribution.py`, `diag_te_driver_timing.py` and the splice builder `build_ohc_spliced_igcc.py`; 2024 stays
  the default and reproduces every committed output. Text changes for the pass: α_obs 0.141 → 0.139; Sect. 4.1
  1.24 = 1.11 × 1.10 × 1.02 → 1.22 = 1.106 × 1.095 × 1.006 (two-decimal factors give 1.23: use three decimals or
  rephrase); range 1.21–1.27 → 1.19–1.27; era ratio 0.21 → 0.20; 91 %, 11 %, 9 % unchanged. Outputs `*_igcc2025.csv`.
- **Decision 3** (Ladrillo.jl c0a2be6, pushed): `python/figures/` reproduces Figs. 1–6 byte-identical to `figures/paper/`
  (`check_figures_identity.py` 16/16, mutation-tested); FACTS/MAGICC data in `data/comparison/`.
- **Decision 1** (Ladrillo.jl aaed555, pushed): version 1.0.0; `--v1.0` → `--v0.1`, `paleo=:v1` → `:per_selection`,
  `lws_anchor=:v1_step` → `:obs_at_first_year` (Marcus). Tests 96/96; identity gate 1 bit-identical on 8 cases after the
  two K4 reference dumps, stale since the 10-08 vv forcing rebuild, were replaced (memory
  `identity_gate_reference_stale_after_input_rebuild`). Tags renamed v1.0.0–v1.3.0 → v0.1.0–v0.4.0 **in the local clone
  only**; GitHub keeps the old names until the release (Marcus: "push commits, hold tags"). At release: delete the
  four remote tags, push v0.1.0–v0.4.0, tag v1.0.0, set `date-released` in CITATION.cff.

Open:
- **The Code availability sentence also claims Table 4's script and the calibration drivers / target builders.**
  Ladrillo.jl ships neither (Table 4 = `scope_ladrillo_vs_brick20_scorecard.py`; calibration is "in progress" in its
  README). Ask Marcus: port, or narrow the sentence.
- In the pass, the Code availability text becomes "Ladrillo v1.0 (Ladrillo.jl, git tag v1.0.0)".
- Ports' notes on research-script defects (not fixed): garbled Fig. 2/3 caption sentence ("…scenarios ones");
  `plot_hindcast_components.py` y-label hardcoded and a stale glacier-trap comment; `plot_vv_gsic_wr_vs_ladrillo.py`
  needs `vv_gsic_2300.csv` even with `--ladrillo-only`, has an L24 docstring, and rejects CHECK verdicts where
  `ladrillo_figs.gate_ladrillo` stamps them; the old fixed-arm `figures/paper/vv_gsic_ladrillo_L27_2300.png` still has
  the title removed on 11-05.
