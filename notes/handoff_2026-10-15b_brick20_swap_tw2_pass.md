# Handoff 2026-10-15b: BRICK 2.0 on the Zenodo posterior, Ladrillo v1.3.0, the TW2 edit pass

> **SUPERSEDED as the start point by `notes/handoff_2026-10-17_gmd_followups_lin2026.md`.**
> **Follow-ups done 10-15h:** items 4 and 7 measured, U02/U03/U10 checked, the Table 5 reading fixed. See
> `notes/gmd_tw2_followups_2026-10-15h.md` and CHANGELOG 2026-10-15h. Every Marcus call below is still open.

Follows `handoff_2026-10-15_tony_tw2_brick_posterior.md`, whose §2 decision is now made and whose §3 steps 1–3 are done.
Start cold from this file, then read:
- SLR CHANGELOG 2026-10-15b → 10-15g, and Ladrillo CHANGELOG 2026-10-15 and 10-15b;
- memory `brick20_zenodo_posterior_driver_scale` (decision record) and `ch4_co2_pulse_paper` (pulse numbers);
- `deliverables/redline/r1015/tw2_edit_inventory.md`: every edit with its source, plus NOT APPLIED and UNCERTAIN.

## 1. What this session did

1. **Diagnosed the posterior question** (CHANGELOG 10-15b, 10-15c).
   - The "2.9× ocean-heat driver scale" hypothesis is falsified: on the TE trend windows the ratio is 1.15–1.56.
   - The 10-08h "Zenodo TE is 3× low" test had compared Zenodo's STANDALONE `brick` file with our JOINT file's BRICK
     slice. Zenodo also publishes the joint `parameters_subsample_sneasybrick.csv`, which is close to ours.
2. **Marcus ruled: move the BRICK 2.0 arm to the Zenodo joint file** (CHANGELOG 10-15d).
   - Every BRICK 2.0 product was re-run in SLR-RFF-BRICK, the FaIRtoFrEDI pulse chain and Ladrillo.jl.
   - The May-22 products are quarantined in each repo with a README.
   - All gates pass. Ladrillo identity gates 2-5 are bit-identical.
3. **Marcus: "rebuild on the new file".** The benchmark's frozen comparators were re-frozen on the current files
   (10-15e). The Ladrillo champion was NOT re-frozen, because that is a separate call.
4. **Marcus: "update the version #".** Ladrillo.jl **v1.3.0** is tagged and pushed (Ladrillo CHANGELOG 10-15b).
   - A clean clone of the tag from GitHub passes 92/92.
   - `tools/fetch_brick20_posterior.sh` now downloads the posterior from Zenodo.
5. **Marcus: "apply this all in the edit pass on Tony's TW2 file … latest versions of everything"** (10-15f, 10-15g).
   - Output: `deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx`.
   - 99 tracked edits, 6 figure swaps and 2 flag comments, all by Claude. Tony's tracked changes and comments are
     untouched.
   - Table 2's glacier diagnostic was re-run first (37.7 → 37.4).

## 2. Decisions and their reasons

- **The arm reads the 35 BRICK columns of the 51-column joint file.** The SNEASY columns are unused because the arm is
  driven by FaIR or MAGICC climate.
  - Table 5 charges K = 27 + 8 as before.
  - The file's `antarctic_precip0` is a log, so the `precip_log` shim is off. A guard in both repos refuses a
    units/shim mismatch.
- **The BRICK panels now run ssp126/245/585 only.** The ssp119/370/460 inputs exist only as calib 1.4.5 `_pre160`
  files, and Ladrillo's panel already ran the same three.
- **Not re-run, still on the May-22 file:** the overshoot / matched-dT arms (09-02..09-04 vintage), `diag_gcrit` (L24),
  and the runtime sentence (timing under load is meaningless).
- **The conditioning rerun was already done** (10-08k, v1.2). The 10-15 handoff's "deferred" item was stale.
- **Edits in Marcus's prose** were limited to queued fixes, numbers, labels, captions and plain copyedits. Readings
  that changed are flagged with Word comments rather than rewritten.

## 3. Open for Marcus (all in `tw2_edit_inventory.md`)

1. **The Conclusions' Antarctic sentence** (comment in the docx). "Reductions of up to 18 cm" now holds in only 3 of 10
   scenarios; Ladrillo's 2300 Antarctic median is above BRICK 2.0's in 7, by up to 47 cm (SSP5-8.5). Sect. 4.3 High's
   "sit together" (427 vs 383 cm) has the same issue.
2. **Intro "equal sensitivity"**, now "similar (about 1.1×)" (comment in the docx).
3. **Queued items not applied:**
   - item 4: the α "within 4 %" comparison needs re-deriving on matched scopes;
   - item 7: Lin et al. 2026, the 2002-2021 Antarctic rate deficit (per-draw rates first), and thanking Frank Errickson;
   - item 8: state the next-version thermal-expansion direction.
4. **Tony's framing comments** 390, 347, 326, 367 and 364, his prose comments, and his placeholders ("(REF?)" ×2,
   "(REF Wong et al 2017)", the equation-parameter text). The mid-sentence paragraph break in 4.1 ("We note that ¶").
5. **Code availability placeholders:** the repository URL and Ladrillo's Zenodo DOI (the repo is still PRIVATE).
6. **The pulse paper.** `deliverables/pulse_model_differences_tables.md` is regenerated. The hand-typed section template
   (`pulse_model_differences_section.md`) still carries 09-07 numbers and a FACTS-at-2300 sentence, which is his prose.
   The new BRICK pulse readings are in memory `ch4_co2_pulse_paper`; the Antarctic pulse response roughly halves.
7. **Whether to add BRICK/SNEASY** as a supplementary "as calibrated" arm (not ruled).
8. **Whether to re-freeze the benchmark champion** (`benchmark/reference/L27` is still the v1.0 copy).

## 4. Uncertain (from the inventory)

- Fig. 5's 0.05 cm regrowth comes from the fixed-arm path and has no committed receipt.
- BRICK 2.0's calibration-data descriptions (IMBIE 1992-2017, CSIRO GMSL) assume the Zenodo posterior came from the
  v2.0.0 code. Tony mentioned Wang et al. 2024; ask him.
- Rounding edges: ΔAIC 95.486 → "+95"; the Very Low width 166.499 → "166".
- `outputs/ic_ladrillo_vs_brick20_L27*.md` (and Ladrillo's) still says the steric row is "a tie by construction". The
  sentence is hard-coded in the script; on the Zenodo posterior that row is +7.2. Fix the text at the next Table 5 run.

## 5. Non-obvious state

- **Commits, all pushed:**
  - SLR-RFF-BRICK `ladrillo-dev` at 4c6d843;
  - FaIRtoFrEDI `heat-ed-morbidity` at 4949365 (another session also commits there, so stage explicitly);
  - Ladrillo.jl `main` at ea23473, tag `v1.3.0` at 01462a8.
- **The docx outputs are untracked** (repo convention). TW2's md5 is `38d235de…`; the build's is `59381d85…`.
  - Rebuild with `deliverables/redline/r1015/build.sh <fresh workdir> <out.docx>`. It refuses to overwrite.
  - Verify with the round's checks: nesting depth 1, "reject Claude == TW2 accepted text", and every new value present.
    The verify script is in this session's scratchpad (gone); its logic is in memory `docx_collaborator_ins_attrs`.
- **Posterior files:**
  - `SLR-RFF-BRICK/data/MimiBRICK/parameters_subsample_sneasybrick_zenodo20592337.csv` is gitignored;
  - Ladrillo's is at `data/brick20/parameters_subsample_sneasybrick.csv`, fetched;
  - the old `parameters_subsample_brick.csv` stays beside it for the regression path.
  - `BRICK20_POSTERIOR` / `BRICK20_PRECIP_LOG` override the SLR loader for regression runs only. The runner refuses to
    start with them set.
- **Quarantines:**
  - `SLR-RFF-BRICK/outputs/quarantine/20261015_brick20_may22_posterior/` (316 files + the glacier diag);
  - `FaIRtoFrEDI/magicc_comparison/processed/quarantine/20261015_brick20_may22_posterior/` (17);
  - `Ladrillo/outputs/quarantine/20261015_brick20_may22_posterior/` (45, local);
  - `benchmark/reference/_fixed_archive_20261015_may22_brick20/`.
- **Older SLR readers** not called by any live runner still read the May-22 file with its shim. That is a consistent
  pair, but do not cite their outputs as current.
