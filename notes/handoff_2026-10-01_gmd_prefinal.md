# Handoff 2026-10-01: the GMD draft is ready for Marcus's last read before it goes to Tony Wong

**Start here.** This note is self-contained. It follows `handoff_2026-09-29b_gmd_review_round.md` and covers the session that ran
09-29 evening → 10-01. In CHANGELOG it covers entries 09-29e/f, 09-30, 09-30b/c/d and 10-01. All commits are on `ladrillo-dev`
and pushed. Memory was updated: `INDEX_slr_post.md` (live file pointer, L27 is the code default),
`gmd_review_0929_carried_numbers`, `l27_paper_posterior`, `INDEX_ais_decision.md`.

## 0. ⛔ THE LIVE FILE

| | |
|---|---|
| **NEWEST** | `deliverables/GMD.Ladrillo.v1_review-2026-10-01_L27.docx` (md5 `9062e357`). Built on Marcus's 09-30 **16:40** save of `…09-30b` (md5 `2b718f21`, untouched). |
| state | **47 tracked edits by Claude, dated 2026-10-01T00:00:00Z.** Marcus's base had 0 tracked changes. 5 comments: Marcus's Zenodo placeholder plus 4 new questions. |
| lineage | 09-29 → 09-30 (Claude) → Marcus accepted all → 09-30b (Claude) → Marcus 16:40 (accepted all, own edits) → **10-01 (Claude)** |
| scripts | `deliverables/redline/r0930/`, `r0930b/`, `r1001/`. Apply in order: normalise → edits_* → comments_*. Each round has its OWN `w:date`. |

⛔ **Rules learned this session (validator-enforced):**
1. **Every tracked round needs its own `w:date`.** If two rounds share author and date, the validator matches new
   paragraph marks to old ones and merges paragraphs.
2. **Never edit text inside an earlier insertion.** Split that insertion and nest a `<w:del>` inside it
   (`revise_own_ins`).
3. **Use `set -o pipefail`.** A failing edit script piped into `tail` once went unnoticed and produced a build missing a
   whole edit set.
4. `pandoc --track-changes=reject` shows tracked-inserted TABLE ROWS as blank rows. That is a pandoc artifact; Word
   removes them.

## 1. What changed in the draft this session

- **Table 5** was re-run with equal draws (10,000 per model) on L27's own Frederikse target. ΔBIC is now 26 / 82 / 147
  at ρ ≤ 0.99 / 0.95 / 0.90 (it was 21 / 78 / 145). A control run of the old 2,000/10,000 pipeline reproduced all seven
  09-20 files byte-identically first.
- **Marcus's 09-30 comment replies were all acted on:**
  - Greenland dates now 1920–30 warming, plateau to ~1960, low ~1990.
  - Amplification sentence moved to the JOINT arm: 0.7–7.6 cm.
  - Antarctic leverage reported as per-draw means: 46 cm (17%) and 20 cm (4%).
  - Pre-observational melt scored against N(0.5, 1.2).
  - Rignot ×0.888 explained.
  - The SLEIP-rate sentence deleted.
- **Greenland separation target re-derived on calib 1.6.0: 5.7** (it was 6.4 on 1.4.5). Ladrillo gives 4.4 with the
  above-threshold channel and 2.4 without; Marcus's sentence now gives both.
- **References completed:**
  - Wong et al. 2017a (Wong, Bakker & Keller) for the DAIS paleo file; BRICK v0.2 becomes 2017b.
  - Table 3 dataset DOIs moved into the reference list.
  - Added: FACTS modules (as Kopp 2023 cites them), GlacierMIP2, ISMIP6 Antarctica, PISM (cited as Golledge 2019),
    Mimi (all-versions DOI), the SLEIP emulators, Levitus 2017 (NCEI).
  - Every entry is Crossref/DataCite-verified, except the two IPCC chapters, whose author lists come from the Kopp and
    SLEIP reference lists.
- **Table 3 rows added:** HadCRUT5, NOAA STAR altimetry (it extends the total over 2022–2024; Dangendorf ends in 2021),
  NOAA NCEI 0–2000 m thermosteric. The GRACE row now also covers the AIS/GIS targets 2019–2025.
- **10-01 pass:**
  - **Arm terms:** joint and fixed arm are defined in Overall structure, and the fixed-arm numbers are labelled
    (Antarctic leverage, the 1.196 reversion, convergence R̂, refit precision, FIG 5).
  - **Scenarios:** the seven van Vuuren scenarios are named, and the vv codes are replaced by names.
  - **Figure order:** a FIG 2–6 signpost sentence was added, and FIG 5 is no longer cited before FIG 1.
  - **Number fixes:** the Antarctic widths at High are now 274 / 332 cm; "MAGICC narrow outlier" is now scoped to
    Antarctica, thermal expansion and the total; the 1993–2024 window is stated for the 1.10 × 1.10 split; "reductions of
    up to 31 cm".
  - **Forcing:** an SSP forcing sentence was added.
  - **Removed:** the per-block regrowth claim, "SLOWG dominates" and internal wording.
  - **Back matter:** Correspondence (msarofim@gmail.com), an Author contributions skeleton, Financial support (Wellcome
    Trust), the Smith 2026 citation, the STAR acknowledgement.

## 2. Repo changes this session (all committed)

- **L27 is the code default everywhere:**
  - The kernel `LADRILLO_POSTERIOR_CSV` points at L27, and ~40 `--tag` defaults are now L27.
  - The test contract in `test_ladrillo_projection.jl` [4] is now header-aware (Marcus-approved). Suite 10/10.
- **Calibrator identity gate:**
  - It now certifies L27 against the first 300 rows of the PRODUCTION chain; mutation-tested.
  - The L24 gate is kept as `gate_calibrator_identity_L24.sh`.
- **Target file:**
  - `prep_recalib_targets_ext.py` default = the Frederikse target (md5 070f74ab).
  - The IMBIE build needs `--ais-imbie2026` and is kept as `outputs/recalib_targets_ext_imbie2026*`.
  - The working-tree split-brain is gone.
- **IC driver:** equal draws by default; `ic_ladrillo_vs_brick20.py` refuses unequal counts.
- **`scope_slr_fair_uncertainty.jl`:** a non-default `LADRILLO_GIS_SHAPE` now goes into filenames and provenance (it
  previously overwrote canonical outputs). New script: `diag_gis_amp_shape_joint.py`.
- **Figures:**
  - FIG 1's obs band is hatched (it was the same grey as BRICK's band).
  - FIG 4's sidecar draw counts are read from the data.
  - All six paper figures re-render byte-identically.
- **Docs:** stale docs updated to L27 (LADRILLO.md, README, headers). The poster pointers were removed (the poster is done).
- **Other session (`calib160_everywhere_ruling_0930`):** the Greenland matched targets are now calib 1.6.0 canonical.
  - The `fair_mean_*` files for ssp119/370/460 were renamed `_pre160`, so those SSPs do not exist on 1.6.0 yet.
  - **Its open questions are still with Marcus:** the tap-cell parameters chosen on 1.4.5, two held ICs, the MCMC start
    point, and the SSP1-2.6 p50 definition.

## 3. OPEN, in priority order

1. **Marcus** reads the 10-01 file and accepts or rejects. Answer the 4 comments:
   - Möller spelling and the Wellcome grant number;
   - the observation end year (2025) vs the "1900–2026" labels;
   - FACTS 112 cm has no receipt;
   - Greenland timescales are recorded only in CHANGELOG.
2. **Prose items left to Marcus** (see `notes/gmd_prefinal_review_2026-09-30.md` and `gmd_prefinal_clarity_2026-09-30.md`):
   - BRICK naming (BRICK / BRICK 2.0 / MimiBRICK / BRICK v0.2) and the SNEASY framing vs Table 1's "runs on FaIR: yes";
   - the projection baseline (1995–2014), stated once;
   - "BRICK runs slightly high" vs IGCC;
   - "thermal expansion ties by construction";
   - undefined acronyms;
   - heading format; the Appendix should sit BEFORE Code availability in Copernicus order;
   - GMD's reproducibility-from-text expectations (equations for the Greenland channels and AR(1) likelihood; a table
     of the fixed values; a verification subsection; a user manual).
3. **Code availability:** the Zenodo DOI and "[repository URL]" are placeholders (waiting on Tony's review). The
   MimiBRICK citation is a GitHub URL, which GMD doesn't accept as an archive. `slr-comparison-arm` (FACTS) still has no
   remote.
4. **Not added, by decision:**
   - Nauels 2017b (it would force a/b labels on Nauels 2017).
   - AR5 Ch. 4 for Table 2 fn 8 (no verified author list).
   - The Levitus 2012 GRL paper (article number unverified); the NCEI data set is cited instead.
5. **Small loose ends:**
   - the 12.295 vs 12.353 × 10⁶ km² Antarctic area in the Rignot scaling (0.07σ; source unknown);
   - `diag_te_rate_attribution` row C's α 0.109 vs the paper's 0.167 (probably units; unchecked);
   - `data/observations/nasa_gmsl_annual.csv` is actually NOAA STAR (misnamed).
6. **Memory hygiene:** `INDEX_conv.md` was over its soft target as of 09-29.

## 4. Non-obvious state

- No background jobs. Scratch builds are in this session's scratchpad (`v0930/`, `v0930b/`, `v1001/`). Everything needed
  to rebuild is in `deliverables/redline/r*/`.
- Two `pgrep -f` wait loops matched their own command line this session, the CLAUDE.md trap. Only watchers hung. Wait on
  PIDs (`kill -0`).
