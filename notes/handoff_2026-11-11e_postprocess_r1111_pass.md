# Handoff 2026-11-11e: calibration post-processing ported; GMD next pass (r1111) built, final build pending

Session `eed2332f` (launched from FaIRtoFrEDI, worked in Ladrillo and SLR-RFF-BRICK), 2026-11-11 16:00 onward.
Previous: `notes/handoff_2026-11-11d_calibration_port_gamma.md`.

## 1. What we were working on

(a) Piece (2) of the calibration port (11-11c §5): post-processing. (b) Marcus, 16:4x: "the 15:07 save is done, run
the draft pass".

## 2. Done

**Ladrillo.jl `main`, e7d7f81 (not pushed yet: waits for the mutation result).**
- `src/postprocess.jl` (`Ladrillo.Postprocess`) + `scripts/postprocess_calibration.jl [--chains=] [--outdir=]
  [--accept-slr] [--force]`. These port run_l27_postprocess.sh's noise-mode check, the projected-SLR certificate
  (diag_slr_convergence_by_chain_ladrillo.jl) and postprocess_mcmc_ext.jl --accept-slr. The certificate model is the
  acceptance-time one: lws :central, tap off, per-chain paleo block of 400, γ at the paleo median.
- Gate `test/calibration/gate_postprocess.jl <SLR repo>` **PASS**:
  - posterior byte-identical to `data/posterior/ladrillo_L27_posterior.csv`;
  - certificate byte-identical to the research file;
  - covariance equal at all 2,500 entries;
  - 28 log lines equal (the 8 failing parameters' R̂/ESS/τ, the per-chain projected quantiles).
  
  Runtime 25 min (21 of them the parameter ESS), 3.3 GB peak.
- MCMCDiagnosticTools 0.3.18 added (only the project hash moved). runtests 118/118. `tools/build_test_reference.py`:
  new `log_lines` kind; untracked research sources recorded as `untracked` (sha256 pins them).
- **Mutation test running** (background, from a frozen copy in the scratchpad; result → `test/calibration/
  mutation_result_postprocess.txt` must be COPIED back from the frozen copy, then commit + push). P1 (subsample
  offset) KILLED at 17:05; P2 certificate thinning, P3 cov jitter, P4 ESS maxlag, P5 no-power noise threshold
  (expected SURVIVE) pending, ~25 min each.

**SLR-RFF-BRICK `ladrillo-dev`, afb900d (not pushed).** `deliverables/redline/r1111/`. CHANGELOG 2026-11-11e has the
full list:
- 84 tracked edits and 7 comments; `verify_r1111.py` gate PASS; `mutation_test_verify.py` 3/3 killed.
- Developed on a frozen copy of the 17:00 save (md5 `fad8a36a…`, scratchpad).
- Runtime script provenance now names the BRICK 2.0 posterior and the load average.

## 3. Open: to finish the pass

1. **Final build** when Marcus confirms his last save. In order:
   - `ls -t deliverables/`;
   - extract the new save (`python/docx_review_extract.py`) and diff its paras.txt against the 17:00 extract, to see
     what he changed;
   - adjust the anchors if he edited a target span;
   - run `BASE_MD5=<md5> deliverables/redline/r1111/build.sh <fresh wd> deliverables/GMD.Ladrillo.v1_review-2026-11-11_L27_r1111.docx`;
   - run `verify_r1111.py <base> <out>`;
   - add the output's md5 to the CHANGELOG.
2. **Runtime sentence** (p. 24: "1.2× … 6.3 against 5.1 ms … 0.72 against 0.62 ms"). Re-run
   `julia --project=julia_v2 julia/diag_runtime_ladrillo_vs_brick20.jl 300 --tag=L27` after the mutation test ends
   (the other session's R workers may still run; the provenance now records the load average). Under load on 11-11 it
   gave Ladrillo 7.54 vs BRICK 2.0 6.02 ms (1.25×), run-only 0.81 vs 0.63, about 20 % slower than 09-21. Add the edits
   to `ENTRIES` (Tony's wording stays; numbers only), then build.
3. Report to Marcus:
   - **HAND items still open in the 17:00 save:** the R̂ comma and the "(20–244)" semicolon in the convergence
     paragraph; the seed sentence; the Fig. 5 caption "FaIR ensemble mean of GMST forcing (a)"; "0104" → "0.0104";
     "are not unrealistic"; About ¾ → four-fifths (optional); Lin/Poinelli option (a/b); the Sect. 4.2 component
     sentences (optional); the FACTS reply; the Acknowledgements NOAA wording.
   - **Fig. 5 move** not done (comment).
   - **Mimi.jl citation:** option 1 (GitHub v1.6.0, 2026) or option 2 (concept DOI, 2022).
   - **NOAA access date:** 18 or 20 May.
   - **ais_c:** the row now says c_R while the adjacent T_on row still writes −h₀/c (the guidance listed only ais_c).

## 4. Piece (3), target builders: map (subagent, read-only, 11-11; re-check before acting)

- **Byte provenance.** Every research source matches at 43d84aa, at HEAD and in the MANIFEST sha.
- **Builders, with the 11-11c corrections:**
  - `prep_recalib_targets_ext.py` (no flags) builds the targets;
  - `python/ladrillo_data.py` WRITES t_glac_blocks, extc_block_constants and the gsic-adjusted target
    (`build_t_glac.py` only builds the regional HadCRUT5 inputs);
  - `build_t_gis.py` builds the Greenland driver and gis_amp_prior;
  - `diag_gis_amp_anchor.py`, then `diag_gis_amp_cmip6.py --zone south`, build the amp shape (its meta CSV has a
    `commit` column = d59ce12);
  - `download_obs.py` only gives the NOAA STAR file.
- **No builder exists** for central_row, paleo_dais_marginals, paleo_fastdyn_draws or paleo_geo_prior_ton
  (`compute_paleo_geo_prior_ton.jl` is in no git history). Freeze them.
- **Code:** ~1,115 Python lines on the L27 path. It needs scipy and pyshp, and matplotlib.path for the masks.
  Byte-identity needs Python, so keep a pinned `tools/` tier like `tools/forcing/`.
- **Traps:**
  - hard-coded paths: prep:88, build_t_glac:45, diag_constraint_anatomy:42 (plus its exec of d0_glacier_shootout);
  - a silent LWS-flat fallback at prep:483-497;
  - a circular read between the LWS builder (:225) and prep (:480);
  - the newest mascon file is picked by glob (:106-109);
  - build_t_gis :362-377 compares against its old output before overwriting.
- **Inputs:**
  - Tier A, ~7.6 MB tracked: Frederikse xlsx+nc; Dangendorf v2 nc (non-public); GRACE txt (Earthdata); GlaMBIE;
    NOAA thermosteric and STAR (rolling); GMIP3 tables; d1 ladder cache; cmip6_gis (40 CSVs).
  - Tier B, local only: HadCRUT5 32.5 MB; Berkeley Earth 455 MB; GISTEMP 57 MB; GRCTellus 46 MB.
- **Marcus decides:**
  1. ship the Dangendorf v2 nc or only its 122-value SE series;
  2. GRACE redistribution;
  3. licences (Berkeley Earth possibly CC BY-NC, verify; CMIP6; Zenodo, GlaMBIE, GTN-G, GlacierMIP3);
  4. archive Tier B or make that gate maintainer-only;
  5. frozen paleo and central_row;
  6. a pinned-Python tier versus a Julia port with a tolerance gate.
- **Suggested order:** gate + inputs.sha256 → targets → ladrillo_data + regions → build_t_gis → amp anchor/shape →
  build_t_glac → LWS extension.

## 5. Non-obvious state

- **State at 18:30 (written before a /clear).**
  - **Marcus saved again at 17:06** (canonical TW2 md5 `9f152d66980d2bd29b5d6f9beb0d6d03`). build.sh's default md5
    `84c9f503…` is no longer at the canonical path, so the guard will refuse until a save is looked at and passed as
    BASE_MD5. The pass was developed and gated on `base_1700.docx` (md5 `fad8a36a…`).
  - The frozen saves and the 17:00 extract were copied OUT of the scratchpad to
    `deliverables/redline/r1111/bases_untracked/` (untracked, 3 MB each; do not commit):
    - `base_1507.docx` (`872c3fef…`) and `base_1700.docx` (`fad8a36a…`);
    - `extract1700/paras.txt`, the file to diff the next save's extract against;
    - the piece-3 map and refs-report summaries.
  - **Post-processing mutation test:** P1–P4 KILLED; P5, the no-power control expected to SURVIVE, started 18:10. If
    Ladrillo.jl `main` is still `ahead 1` at e7d7f81, the session ended before P5 finished. In that case, read
    `/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/eed2332f-9d15-44ff-856e-a58b68e2876c/scratchpad/frozen_pkg/test/calibration/mutation_result_postprocess.txt`.
    If P5 is there, copy the file to Ladrillo `test/calibration/`, add a CHANGELOG line, commit and push. If P5 is not
    there, re-run only P5 (`mutation_test_postprocess.sh` runs all five, so ~2 h for all of them; ~25 min for P5 alone).
  - `data/RFF-SP-emissions/csv/INPUTS.manifest.json` shows as modified in SLR. This session did not touch it; leave it.
- The scratchpad held the frozen draft copies and the mutation-test frozen package; what the next session needs is
  copied out above.
- `outputs/diag_runtime_ladrillo_vs_brick20_L27*`: the tracked file is the 09-21 run (May posterior);
  `_rep2_0921_mayposterior` is the same file; `_rep3_20261111_underload` is the 11-11 run. The tracked file will be
  overwritten by the quiet re-run.
- Marcus's Word lock file (14:00) is still present; he is editing the TW2 review file live.
- Neither repo is pushed this session. Ladrillo.jl waits for the mutation result. SLR waits for the final build.
  Pushing SLR `ladrillo-dev` is routine (he pushes it regularly); still say so.
- Memory: `redline_reader_gaps_r1111` (new; pointer in `INDEX_conv_build`), `gmd_1111_decisions` (session 4 status).
