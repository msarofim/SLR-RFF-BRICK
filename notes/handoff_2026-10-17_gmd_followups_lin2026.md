# Handoff 2026-10-17: GMD TW2 follow-ups measured; the Lin et al. 2026 comparison

Follows `handoff_2026-10-15b_brick20_swap_tw2_pass.md`. Start cold from this file, then read:
- `notes/gmd_tw2_followups_2026-10-15h.md`: every number below, with its receipt and the choices still open;
- SLR CHANGELOG 2026-10-15h, 2026-10-17, 10-17b, 10-17c; Ladrillo CHANGELOG 2026-10-15c;
- memory `te_alpha_matched_scope`, `ais_post2002_rate_below_target`, `lin2026_ais_2100_is_fast_dynamics`
  (routed from `INDEX_slr_post.md`, `INDEX_ais_imbie.md` and `INDEX_ais.md`).

## 1. What this session did

Measured the items the 10-15 TW2 edit pass left open, with committed receipts. No paper prose was written and the docx was
not touched.

1. **Table 5's reading text.** `python/ic_ladrillo_vs_brick20.py`, in this repo and in Ladrillo, had two hard-coded
   sentences that were false: the steric row "a tie by construction" (it is +7.2 / −0.8 / −2.3 at ρ ≤ 0.99 / 0.95 / 0.90)
   and "every BRICK 2.0 series at the ρ bound". Both are now computed. Ladrillo's table label was a literal "Ladrillo
   v1.0" and now comes from `Project.toml`. Re-run at all three ρ bounds in both repos: every CSV is byte-identical and
   Ladrillo identity gate 5 passes. Only the .md files changed.
2. **Fig. 5 regrowth (inventory U02).** `python/verify_magicc_regrowth_attribution.py --arm=fixed`: Low-to-Negative
   0.0526 cm, 0 elsewhere. The `_magiccclim` files' fixed arm is the FaIR-mean control by design
   (`scope_slr_fair_uncertainty.jl:449-452`), so the fixed mode reports no climate split ([FIXED-CONTROL] gate).
3. **Queued item 4, α "within 4 %".** `python/diag_te_alpha_matched_scope.py`. α multiplies FaIR's OHC, which is
   Earth's total heat uptake. Ladrillo α ÷ observation-implied α over 1993–2020 is 0.974 per 0–2000 m ocean heat (the
   draft's basis), 1.079 per full-depth ocean and 1.183 per total Earth heat (matched). The matched obs-implied 0.141 is
   below the posterior 5–95 % (0.148–0.186). There is no formal error bar.
4. **Queued item 7, the Antarctic rate from 2002.** `python/diag_ais_rate_2002_per_draw.py`. Per draw, 2002–2021: L27
   0.294 (0.248–0.331) mm/yr against the target's 0.423 and IMBIE 2026's 0.524. Every draw is below the target through
   2021 and 2023, and 99.5 % through 2025. The gap shrinks with the end year. The item came from Claude's 10-02 reading of
   Lin et al. 2026 (session transcript only), not from a reviewer.
5. **Queued item 7, the Lin et al. 2026 comparison.** `julia/diag_ais_2100_vs_lin2026.jl`, run with
   `--project=<Ladrillo checkout>`. It rebuilds the paper's joint arm per draw, puts it on Lin's basis (change since
   2015), and re-runs each draw with `antarctic_lambda = 0`. Against Lin's drift-corrected posterior (cm, median [5–95]):

   | | SSP2-4.5 | SSP5-8.5 |
   |---|---|---|
   | Lin, drift-corrected | 5.2 [1.2–9.7] | 7.7 [1.9–16.2] |
   | Ladrillo L27 | 10.0 [3.8–57.2] | 36.3 [6.9–69.3] |
   | Ladrillo L27, λ = 0 | 5.4 [3.6–8.8] | 7.5 [4.6–12.9] |
   | BRICK 2.0 | 22.0 [0.8–66.6] | 37.6 [13.7–78.4] |

   Fast dynamics are 46 / 80 % of Ladrillo's median change. Ladrillo's FaIR warming is below AR6 SPM.1 (SSP5-8.5
   2081–2100: 3.75 vs 4.4 K), so warming does not explain the excess.
6. **Checked:** Sect. 4.2's "same pairing" holds draw by draw on the 998 shared draws (U10). The Zenodo record (v4)
   describes the posterior as supporting MimiBRICK v2.0.0's calibration code but names no datasets (U03). The paper cites
   nothing from the products still on the May-22 BRICK 2.0 file.

## 2. Rulings (Marcus, 10-17)

- "Compare against the drift-corrected row." Lin's raw-simulation rows are not used. The comparator lives in named
  constants (`LIN_ROW`, `LIN_POST`, `LIN_HIGHEND`) and the receipt writes Lin's quantiles next to ours.
- "Drop SSP1-2.6 from the comparison." Lin runs SSP1-1.9, which Ladrillo's calib 1.6.0 forcing does not have; `SCEN` is
  SSP2-4.5 and SSP5-8.5.

## 3. Next step: the Antarctic writing pass (Marcus drafts the prose)

Recommended to Marcus 10-17. Four open items are one story, and every number is committed:
1. Conclusions: "reductions of up to 18 cm" holds in only 3 of 10 scenarios. Ladrillo's 2300 Antarctic median is above
   BRICK 2.0's in 7, by up to 47 cm (SSP5-8.5). Sect. 4.3 High's "sit together" now describes 427 vs 383 cm. Both carry
   a Claude comment in the 10-15 build.
2. Sect. 4.3: whether and how the Lin comparison goes in (table in the follow-up note).
3. Sect. 3.1: disclosing the post-2002 rate, per-draw rates for both windows.
4. Intro "equal sensitivity": Antarctica is now 1.14×, TE 1.07×; the 10-15 build says "similar (about 1.1×)".

Then a thermal-expansion pass:
- item 4's two α sentences (Sects. 2.2.4 and 4.1);
- item 8, the next-version direction;
- thanking Frank Errickson.

After that come Tony's comments (390, 347, 326, 367, 364 and his prose comments) and the next round to him, with the
U03 question about Wang et al. 2024. Still open from 10-15b: the repository URL and Ladrillo's Zenodo DOI (repo private),
the pulse-paper section template, a BRICK/SNEASY supplementary arm (not ruled), and re-freezing the benchmark champion.

Claude's role in this pass is numbers, tables, captions and methods text. Marcus writes the narrative.

## 4. Non-obvious state

- **The draft was saved after the build.** `deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx` is now md5
  `0cb0dcd7…`, saved 2026-10-17 15:56; the 10-15 build was `59381d85…`. Read it fresh before quoting it. Do not write
  to it while Marcus may have it open (memory `question_is_not_an_edit_request`). The build workdir and verify logic are
  in the 10-15b handoff, §5.
- **Commits, all pushed:**
  - SLR-RFF-BRICK `ladrillo-dev`, df07ccb..21be3d6: ba82407, 5c5cdff, 9baec70, 4108e55, d039f09, 28204a4, 14fbb64,
    03b4fbf, ecc98c4, 16908c5, a018508, 21be3d6.
  - Ladrillo.jl `main`, ea23473..6ecfc4d: 6674807, c964ccb, 6ecfc4d. The tag `v1.3.0` is unchanged, and the Table 5
    edits are post-tag.
  - FaIRtoFrEDI: nothing this session. Its `deliverables/egu_sprm/*.docx` modifications are another session's work.
- **Untracked by design:**
  - `outputs/diag_ais_2100_vs_lin2026_L27_draws.csv` (6.3 MB, ignored like the other draws files; byte-identical on
    rerun);
  - Ladrillo's `outputs/tables/ic_*` (regenerated locally with the new label).
- **Running the Lin receipt:** `julia --project=/Users/MarcusMarcus/Documents/2026/CodeProjects/Ladrillo
  julia/diag_ais_2100_vs_lin2026.jl` from this repo, about 1.5 min. It errors before writing if [IDENTITY] or
  [NOFD-INERT] fails.
- **Lin et al. 2026** is `~/Documents/2026/ClaudeDocs/Papers/s41561-026-02102-1.pdf`. Its 2100 values are relative to 2015.
  Lin's GMST is FaIR v1.x, "similar to AR6". It calibrates the emulated 2015–2021 rate against King et al. 2023's
  0.44 ± 0.04 mm/yr; Ladrillo's 2015–2021 rate is 0.341.
- **Superseded numbers:**
  - the 10-02 transcript's Lin comparison (SSP2-4.5 10.3, SSP5-8.5 36.4 cm, "BRICK 2.0 higher still"): it predates the
    record conditioning and the BRICK 2.0 posterior swap;
  - Table 5 .md files generated before 10-15h.
- **Load:** no jobs were left running. The Table 5 re-runs took about 15 min per ρ bound on the M4.
