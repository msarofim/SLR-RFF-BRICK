# Handoff — L24 memo shipped, Tony on board, GMD paper starting (09-14 → 09-16)

**Start here.** Continues `handoff_2026-09-14_l24_share_ready.md` (its §4 traps still apply — the
Word-buffer clobber, sync-before-edit, the 10-min background-Bash death). CHANGELOG 09-14e → 09-16 is
the primary record. **Read `INDEX_slr.md` and `INDEX_cmp.md` before touching the deliverable or the
comparison figures.**

**STATUS (09-16):** `SLR-RFF-BRICK` `ladrillo-dev` clean and pushed. `facts` `slr-comparison-arm`
still has **no remote** (54 untracked experiment outputs — the FIG 2–4/7–9/12 inputs). `MimiBRICK-FM`
(private) is STALE (last commit 06-17, old Mengel component) — the live Ladrillo code is
`SLR-RFF-BRICK/julia/` on upstream `MimiBRICK.jl v2.0.0` (Manifest `repo-rev = "v2.0.0"`).
**Marcus is drafting the GMD model-description paper.** Tony Wong (09-15) is in: fine with MIP/expert
constraints, wants double-counting/correlation nipped in the bud, asked if still Mimi (yes).
**TORCH VERDICT:** nothing in this arc needed it (emulandice block runs 20 s/scenario).

---

## 1. ⭐ NEXT (the paper's to-do, in order)

1. **Code-review-ready version for Tony's team** (Marcus: Zenodo only AFTER the team review).
   Cleanups done this arc are listed in §3; what remains is the **package extraction** — a
   "Ladrillo v1.0" tree (components, calibrator, projection kernel, target prep, figure drivers,
   data manifest, L24 posterior) instead of pointing reviewers at a 4,016-file research repo.
   Decide with Tony: new repo vs `MimiBRICK` v3 branch (his Ladrillo-vs-BRICK-3.0 call).
2. **`facts` needs a remote** (fork + push; the 10 `global.shared.*.n200` experiments and their
   per-region emulandice outputs are the paper's FACTS inputs). Creating a GitHub repo is
   Marcus's action, not an agent's.
3. **Scope question, open (Marcus 09-16):** do the FACTS and MAGICC comparisons belong in the
   model-description paper, or wait for the collaborative pulse paper? See §5 for the argument.
4. **Open science items the paper must STATE** (not fix): cross-series error correlation
   unmodelled (Frederikse components; an ensemble estimate is ~1 h); the emulandice gap not
   separated (timescale source vs inventory basis — needs GlacierMIP2 per-model volumes, ~½ day);
   "three Antarctic changes not tested individually"; SLOWG amp product dependence.
5. **Benchmark freeze at the release tag** (`bench_ladrillo.py` prints "LITERATURE ARM MOVED"
   since the vv rows; `--freeze-fixed` is Marcus's call) so the frozen reference = the paper.
6. **Then the pulse analysis** (`INDEX_cmp_pulse.md`) — unchanged.

## 2. WHAT HAPPENED 09-14 → 09-16 (numbers in the CHANGELOG entries named)
- **Two comment rounds applied** (09-14e/f/g/h/k): Sampler + Convergence + Discrepancy-terms
  paragraphs; Table 3 rebuilt (checksums/dates → footnotes ¹³–²², GlacierMIP3 row, Dangendorf and
  IGCC as "not a calibration target"); Vintage split; blocks renamed **SLOWG/FASTG in the document**;
  intro now names TWO departures (channel + GlacierMIP3); onset "4.69 K global mean temperature".
- ⭐ **Dangendorf is NOT in L24's likelihood** (`DROP_TOTAL` on since L11) — Marcus ruled: no refit,
  doc corrected ⇒ [[dangendorf_not_in_l24_likelihood]]. L24 is fitted to components + point terms
  only; the total is out-of-sample.
- **R̂ criterion corrected**: the gate is R̂ < 1.05 AND ESS > 400 (19 fail; 14 on R̂ alone).
- **SSP5-8.5 vs vv High**: warmer at every horizon (ensemble-mean 4.31/7.50 vs 3.32/6.66 K at
  2100/2300); the FACTS ar5glaciers cap is what Marcus saw in FIG 4.
- ⭐ **Glaciers vs emulandice on matched configs + scope** (09-14i/j, FIG 12): 13 % low, = SLOWG
  0.74 + RGI 19 0.45, FASTG 1.13; paired 5–95 % spans zero; CMIP6-amp arm does NOT close it;
  aggregation ruled out (GlacierMIP3 S1a per-region τ) ⇒ [[gsic_blocks_vs_emulandice]]. Drivers:
  `python/dump_shared_climate_for_blocks.py` → `julia/diag_gsic_blocks_vs_emulandice.jl` (arms
  joint/fixed/joint_cmip6amp, seed 2026 in the sidecar) → `python/diag_gsic_blocks_vs_emulandice.py`.
- **CMIP7 forcing sentence verified** (`build_emissions_v160_ssp245.py`: CMIP7 1750–2023, Zenodo
  18828694, spliced 2023.5, harmonized; L24 ran after the 08-28 rebuild).
- **Likelihood-independence audit** for Tony ⇒ `notes/audit_2026-09-16_likelihood_independence.md`
  (18 terms; residual exposures i–v; IMBIE + total already removed).
- **Email facts checked**: "better than BRICK or SURFER" → BRICK only; "most widely used model" →
  dropped; FRISIA is FaIR-coupled but no pre-2002 ice-sheet test; BRICK also climate-driven past
  2100 on FaIR; LARMIP DOES respond after 2100 (200-yr memory).

## 3. CLEANUPS DONE (CHANGELOG 09-16b has the receipts)
- ⭐ **`scripts/gate_calibrator_identity.sh`** — 300-iter seed-2026 byte-identity against
  `benchmark/reference/calibrator_300iter/` (40 s, mutation-tested). RUN IT after ANY edit to
  `calibrate_mcmc_ext.jl`. The pre-cleanup file sits beside the reference.
- `calibrate_mcmc_ext.jl` 2,412 → 2,108 lines: adcov ladder + six vintage name tables gone
  (covariances must be NAMED files; `adapted_cov_L11tune3_seed2026_named.csv` = header-replaced
  copy, chain byte-identical); ten legacy flag arms gone; L24's Greenland is the default;
  `--amp-basis` kept as a TEST-ONLY knob; `--adcov` defaults to the canonical seed with a banner.
  **Still to do:** the else-branches of `GIS_AB/GIS_BASINS/GISB_TERM/GIS_ORDERED` (77 sites, all
  constants now `true`), the steric-cap arm (documented optional; keep or drop is a choice).
- Literal tap stems → helpers (15 files); the L24 posterior + 1.196 arm now TRACKED; `git gc`.
- ⚠ **`run_ladrillo_tests.sh` test 6 [3] FAILS and was already failing since the 08-28 driver
  migration** (offline-cell reference constants are 1.4.5-forcing numbers). Not edited (standing
  rule). Fix = regenerate `python/gis_offline_cell.py`'s cell on the 1.6.0 forcing, Marcus's call.
  Same signature: running the suite REWRITES `outputs/gis_port_reference.csv` (test 4 regenerates
  it; max |Δ| 0.36 cm after 2024 on the 1.6.0 forcing vs the tracked 08-20 file) — reverted, not
  committed, because a reference a test writes itself is not a reference. Decide the regeneration
  together with test 6.
- NOT done, by decision: SLOWP/FAST code rename (44 data files incl. the posterior and the frozen
  benchmark carry the names — do it at the v1.0 package extraction); `dang`→`total` column rename
  (same reason; the stale comment is fixed). ~15 GB of June `wong_cond_pulse_pairs_*` blobs sit in
  history — `git filter-repo` on a public repo is Marcus's call.

## 4. ⚠ NON-OBVIOUS STATE / TRAPS (new this arc)
- **`outputs/diag_emu_blocks/`**: per-draw CSVs and the shared-climate dumps are GITIGNORED
  (86 MB per-row provenance was committed once and force-pushed away, `d4ba1e9`); only the
  `*_provenance.txt` sidecars are tracked. Regenerate in ~2 min for all five scenarios.
- **`facts` per-region emulandice outputs** exist ONLY on this laptop
  (`experiments/global.shared.<scen>.n200/output/*glac{1..19}*`).
- **The calibrator's `'dang'` comment is stale** (target IS Dangendorf 2024, and dropped anyway).
- **`.git` is 7.8 GB + eight `tmp_pack_*` garbage files** from interrupted pushes — `git gc` before
  anyone clones.
- **Word**: `~$drillo.9.14.26.docx` lock = the comments file, not the deliverable; still check
  `ls deliverables | grep '^~'` before every build.

## 5. The FACTS/MAGICC-in-the-paper question — the case either way
- **In**: a model-description paper without a comparator set can't make the "niche" claims
  (Table 1/2, FIGs 2–4, 7, 9, 11) that justify the model's existence; SLEIP already benchmarks the
  seven, so an eighth that isn't placed against them reads as unfinished; the comparisons are DONE
  and regenerable.
- **Out/later**: every comparator row is a claim about someone else's model that a reviewer from
  that group will contest (MAGICC's Greenland start year, FACTS past 2100, the emulandice gap);
  they double the reviewer surface; and the pulse paper will re-run all of them on the pulse
  cubes anyway. A middle path: keep Tables 1–2 (documented scope facts) + the hindcast vs BRICK
  (Table 4, FIG 1) + FIG 12 (the one comparison that tests Ladrillo's own module) in the model
  paper; move FIGs 2–4, 7, 9, 11 to the pulse paper.

## 6. FILES (this arc)
**New:** `python/dump_shared_climate_for_blocks.py`, `julia/diag_gsic_blocks_vs_emulandice.jl`,
`python/diag_gsic_blocks_vs_emulandice.py`, `outputs/diag_gsic_blocks_vs_emulandice.csv`,
`figures/gsic_blocks_vs_emulandice_L24.png` (FIG 12), `notes/audit_2026-09-16_likelihood_independence.md`,
comment files `deliverables/Ladrillocomments.9.13.26.docx`, `Ladrillo.9.14.26.docx`.
**Changed:** the deliverable + FILLED.md (12 figures), `sync_filled_from_docx.py` (FIGS = 12),
`build_l24_deliverable_doc.sh` (FIG 12 step), `.gitignore`, `handoff_2026-09-14` §1.3.
**Memory:** `dangendorf_not_in_l24_likelihood`, `gsic_blocks_vs_emulandice`; `INDEX_slr` pointers.
