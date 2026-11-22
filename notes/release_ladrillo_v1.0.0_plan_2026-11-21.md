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
