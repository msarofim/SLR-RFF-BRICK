# Ladrillo.jl v1.0.0 release: DOI and repository URL (plan, 2026-11-21)

Goal: replace the paper's two placeholders ("DOI [to be assigned at submission]", "[repository URL]") before the
GMD submission (target: before Thanksgiving, 26 November). GMD requires the code in a persistent public archive with a
DOI when the preprint is submitted.

## State on 2026-11-21

- `msarofim/Ladrillo.jl`: PRIVATE, MIT licence, `main` clean and pushed at dbe2f69.
- Tags. GitHub still has the OLD names v1.0.0–v1.3.0 (= local v0.1.0–v0.4.0). Locally both sets exist: the renamed
  v0.1.0–v0.4.0 and the old v1.0.0–v1.3.0. A new v1.0.0 must point at the release commit, so the old v1.x tags must be
  deleted locally and on GitHub first (Marcus 11-11: rename approved; pushing it waits for his go-ahead).
- Archive test (`git archive HEAD`): 318 files, 103 MB unpacked, 41 MB zipped. It contains the component code, the
  calibration and projection drivers, `tools/targets/` (target builders), `data/posterior/ladrillo_L27_posterior.csv`
  (10,000 draws), the figure and table scripts, the FaIR forcing files, LICENSE, README and CITATION.cff, which is
  everything the Code and data availability section lists.
- History scan: no credentials and no Frederikse files. The history and the archive contain the Dangendorf `_v2.nc`
  file supplied by S. Dangendorf (shipped by Marcus's ruling, 11-12); confirm with him before the repo is public.
- 15 commits carry the author address `MarcusMarcus@MacBook-Pro-2.local` (harmless; visible once public).

## State on 2026-11-22

- DOI reserved by Marcus: **10.5281/zenodo.24445689** (version DOI; Zenodo adds a concept DOI when the record is
  published). The paper cites the version DOI.
- Ladrillo.jl f056a7d (pushed to private `main`): CITATION.cff `doi:` + `date-released: 2026-11-22`; README cites the
  DOI. Annotated tag `v1.0.0` at f056a7d, pushed. GitHub release v1.0.0 created as a DRAFT (publish when the repo goes
  public).
- Zenodo file: `SLR-RFF-BRICK/deliverables/zenodo_ladrillo_v1.0.0/Ladrillo.jl-1.0.0.zip`, 40,696,030 bytes, sha256
  cf42ee2f…382bf (full hash in the `.sha256` next to it). Built from the tag and again from the commit: byte-identical.
  284 files (= the tag's tree), one top-level folder `Ladrillo.jl-1.0.0/`; CITATION.cff inside carries the DOI.
- Steps 1–4 are done; step 5 draft saved by Marcus 11-22; step 7 done in GMD round r1122 (11-22). Left: Publish at submission, 6 (public at submission,
  after Sönke), and publishing the draft GitHub release.

## Re-cut on 2026-11-22 (afternoon): v1.0.0 moved to 46a93de

Marcus 11-22: add the FACTS configs and MAGICC extraction scripts to the archive (GMD's code and data policy), fix
Fig. 5's resolution, keep the label 1.0.0. Ladrillo.jl 46a93de adds `comparison/` and saves Fig. 5 at 300 dpi; no model,
posterior or number changed (196/196 tests, figure identity gate PASS). `v1.0.0` was deleted and re-created there and
force-pushed (repo private, record unpublished); the draft GitHub release still names `v1.0.0`.
- **New Zenodo file:** `deliverables/zenodo_ladrillo_v1.0.0/Ladrillo.jl-1.0.0.zip`, 40,772,194 bytes, md5
  34cb351fba191ec435eaa57ee0d2422a, sha256 e0901918…356f7 (full hash in the `.sha256`), 321 files. Built from the tag
  and from the commit: byte-identical.
- The earlier zip (f056a7d, sha256 cf42ee2f…) is in `superseded_20261122_precut_f056a7d/` with a README. If it was
  uploaded to the Zenodo draft, delete it there and upload the new one.
- **Licence on Zenodo:** set "MIT License". Add to the description that data files keep their sources' licences
  (`data/sources/README.md`; the Berkeley Earth series is CC BY-NC 4.0).

## Recommended route: Zenodo manual upload with a reserved DOI

The GitHub–Zenodo integration only archives public repositories and mints the DOI when a GitHub release is published.
A manual upload can reserve the DOI now, while the repo is private and the code can still change, and stays an
unpublished draft until it is published at submission.

1. **Marcus, on zenodo.org (signed in):** New upload → "Do you already have a DOI?" No → **Reserve DOI**. Save as
   draft. Send the DOI to Claude. (Nothing is public until "Publish".)
2. **Claude:** CITATION.cff gets `doi:` and `date-released:`; README gets the DOI; commit; push to private `main`.
3. **Claude:** ~~delete the old tags v1.0.0–v1.3.0 (local and GitHub), push v0.1.0–v0.4.0~~ DONE 11-21 (Marcus's go;
   Ladrillo.jl CHANGELOG 2026-11-21). Still to do: tag v1.0.0 at the release commit, push it, create the GitHub release.
4. **Claude:** `git archive --format=zip --prefix=Ladrillo.jl-1.0.0/ v1.0.0` → `Ladrillo.jl-1.0.0.zip`; check its
   contents against the availability section.
5. **Marcus:** upload the zip to the Zenodo draft, paste the metadata below, and **Publish** at or just before
   submission. Publishing cannot be undone (later fixes become new versions under the same concept DOI).
6. **Marcus, at submission (his choice 11-21), after Sönke answers about the `_v2.nc` file:** make `msarofim/Ladrillo.jl` public (Settings → General → Change visibility). The repository URL is
   then `https://github.com/msarofim/Ladrillo.jl`.
7. **Claude:** a tracked round on the paper filling in the DOI and the URL.

## Zenodo metadata (to paste)

- Resource type: Software
- Title: Ladrillo.jl: a calibrated reduced-complexity emulator of global mean sea level rise (v1.0.0)
- Creators: Sarofim, Marcus C. (NYU Marron Institute) only (Marcus 11-21; matches CITATION.cff).
- Version: 1.0.0
- Licence: MIT. The data files keep their sources' licences (data/sources/README.md); the Berkeley Earth series is
  CC BY-NC 4.0.
- Description: Ladrillo v1.0, the model described in Sarofim and Wong (Geoscientific Model Development, submitted):
  component code, calibration and projection drivers, calibration targets with the scripts that build them, the
  10,000-member posterior, and the scripts that produce every figure and table in the paper.
- Related identifiers: "is supplement to" https://github.com/msarofim/Ladrillo.jl/tree/v1.0.0 (Software) and, once
  assigned, the GMD preprint DOI (metadata stays editable after publishing); "references" 10.5281/zenodo.20713982
  (van Vuuren emissions v1.1.1); "is derived from" MimiBRICK.jl
  v2.0.0 (https://github.com/raddleverse/MimiBRICK.jl); "references" 10.5281/zenodo.20592337 (MimiBRICK v2.0.0
  posterior) and 10.5281/zenodo.18828694 (fair calibration data 1.6.0).
- Keywords: sea level rise; emulator; reduced-complexity model; BRICK; Bayesian calibration

## Dangendorf `_v2.nc`: ship as is (2026-11-24)

The 11-22 acknowledgments email asked Sönke about the file but did not go to his address (sdangendorf1@tulane.edu).
Marcus 11-24: forwarding it to him, saying it will ship as is. Reason: the original is in Zenodo 10621070 (open, CC BY
4.0, contains the mis-written `KalmanSmootherHR_Global.nc`), and `_v2` is the corrected version of that public file.
The submission-day gate on his answer is lifted. If he objects later, the file comes out in a new version (history
rewrite only while the repo is still private).

- 2026-11-24: repo made public (Marcus); GitHub release v1.0.0 published by Claude (tag object 81c5f70 -> 46a93de; notes now name `comparison/`). No webhooks on the repo. Repo, tree/v1.0.0 and release pages return 200 without sign-in. Next: Marcus publishes the Zenodo draft.
