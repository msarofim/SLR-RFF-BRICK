# Handoff 2026-10-08b: make the Ladrillo.jl GitHub repo (private) and push

Follows `handoff_2026-10-08_ladrillo_v11_done.md`, whose decisions 2 and 4 are now ruled and implemented (§4).

**Marcus 10-08:** *"3, 5, and 6 should be done first. Find a URL for the BRICK2.0 code. Do anything else that's easy,
Then write a handoff for the new session to make the github repo."*

## 1. ⛔ The job: create a PRIVATE GitHub repo for Ladrillo.jl and push it

Standing ruling (memory `ladrillo_clean_repo_decisions`, 10-07): Claude creates a **PRIVATE** repo once the local build
passes; **Marcus makes it public and adds Tony.** Do NOT make it public and do NOT invite anyone.

Creating the repo is an outward-facing action. Before running `gh repo create`, confirm the name with Marcus.

**Steps:**
1. Confirm the name with Marcus.
   - Recommendation: **`Ladrillo.jl`**. That is the Julia convention, and the package README and CITATION title already
     use it.
   - Neither `msarofim/Ladrillo.jl` nor `msarofim/Ladrillo` exists (checked 10-08). `gh` is logged in as `msarofim`,
     with scopes `repo`, `workflow`, `read:org`, `gist`.
2. **Pre-push checks.** The repo will later be public, so treat this as a publication review.
   - `git -C ~/Documents/2026/CodeProjects/Ladrillo status`: clean, and everything §2 lists is committed.
   - **History:** nothing that must not be published.
     - Checked 10-08: the BRICK 2.0 POSTERIOR (`parameters_subsample_brick.csv`) is not in any commit; it was purged
       10-07. `test/reference/research_brick20_joint_draws_ssp245.csv` holds BRICK 2.0 OUTPUT values, not its
       parameters, consistent with ruling 6.
     - Largest blob: the 9.8 MB posterior. `.git` is 36 MB.
   - **The FaIR builders** (`tools/forcing/`, §2 item 3) are ported from the PRIVATE FaIRtoFrEDI repo.
     - Read every file there before pushing.
     - No hard-coded `/Users/...` paths.
     - No licence-less or private INPUT data committed; only `inputs.sha256` and fetch code.
     - ⚠ `calibration_v160_prod/` has no LICENCE, so if any of it is needed, ask Marcus.
   - `julia --project=. test/runtests.jl`: 92/92, EXACT on this machine. `Pkg.test()` runs in portable mode and
     also passes.
   - Tracked files contain no `/Users/` or scratch paths (checked 10-08). `test/runtests.jl` looks for Python in
     `LADRILLO_PYTHON`, then `~/climate-env`, then `python3`. That is harmless for others; drop the personal default
     before a public release if Marcus prefers.
   - Ladrillo HEAD at handoff: **08a9b99**, working tree clean. Commits since v1.1.0: 6edd284 (opt-in conditioning),
     c9b0366 (likelihood weights), 7f93f69 (tests + item 6), 3bf4992 (FaIR builders), 08a9b99 (Tables A1/A2).
3. `gh repo create msarofim/<name> --private --source ~/Documents/2026/CodeProjects/Ladrillo --remote origin` (check
   `gh repo create --help`). Then `git -C … push -u origin main` and **`git -C … push origin v1.0.0 v1.1.0`**: the
   tags are the paper's versions.
4. Add `repository-code: https://github.com/msarofim/<name>` to `CITATION.cff` and the clone URL to the README's Install
   section (it says `git clone <this repository>`). Commit and push.
5. **Fresh-clone test FROM GITHUB:** `gh repo clone` into the scratchpad, `Pkg.instantiate()`, quick start,
   `test/runtests.jl`.
   - The BRICK 2.0 testset will SKIP: the posterior isn't fetchable (§3.1). Say so.
6. Tell Marcus it is ready to make public and to add Tony. The ccd_pr tools don't apply: there is no PR.

## 2. State of Ladrillo.jl (`~/Documents/2026/CodeProjects/Ladrillo/`, branch `main`, no remote)

| | state |
|---|---|
| version | `main` = 1.2.0-DEV; tags `v1.0.0` (submitted), `v1.1.0` (the paper's, at 78b03c6) |
| model + projections + hindcast + Table 5 | ported, certified bit-identical to the research outputs (identity gates 1–5 + panel gate, mutation-tested) |
| v1.2 opt-in conditioning | `posterior(; drop_record_crossings=true)`, `fastdyn_onset_year`, `scripts/record_crossings.jl`, `scripts/record_likelihood_weights.jl` (6edd284, c9b0366) |
| **item 5: self-contained tests** | ✅ `test/runtests.jl` (7f93f69). 83 checks, about 2 min. Exact on the reference runtime (macOS arm64, Julia 1.12.6, default bounds checking); `Pkg.test()` runs in portable mode (rtol 1e-12; it forces `--check-bounds=yes`, measured ≤ 1.7e-15). Mutation-tested. |
| **item 6: Manifest / CITATION / compat** | ✅ (7f93f69). Julia compat 1.12. The Manifest has nothing to prune: all 306 entries are MimiBRICK v2.0.0's own closure. CITATION version 1.1.0. |
| **item 3: FaIR forcing builders** | ✅ `tools/forcing/` (3bf4992). All 43 `data/forcing/` files rebuild BYTE-FOR-BYTE (re-verified independently with `shasum`), in ~1 min. Gate mutation-tested. ⛔ Two inputs are NOT public (§3.4). |
| Tables A1 / A2 ("easy") | ✅ `python/tables/` (08a9b99). All four research outputs reproduced exactly (PCA CSV, both tables' md, A1 CSV). In `runtests.jl`; the suite is now **92/92**, about 2 min, exact. ⚠ Table A1's heading still says "SLOWG = SLOWP and FASTG = FAST in the code" (kept so it matches the paper; Marcus's wording). |
| item 2: calibration code | NOT done: port `calibrate_mcmc_ext.jl`'s L27 path + `gate_calibrator_identity` on renamed headers. Do not rerun the chains. Handoff `handoff_2026-10-07_clean_l27_repo.md` §3B is the map. |
| item 4: figures | NOT done (§3E of the same handoff) |

## 3. Open items for Marcus / Tony (not blockers for a PRIVATE push)

1. **⛔ The BRICK 2.0 posterior has no public URL** (SLR CHANGELOG 10-08h; Ladrillo CHANGELOG 10-08e).
   - The public MimiBRICK v2.0.0 Zenodo file (10.5281/zenodo.20592337, `parameters_subsample_brick.csv`, sha256
     `fecabef3…`) is a DIFFERENT calibration from the paper's file (Tony's 2026-05-22 post-PR#93 subsample, sha256
     `78247db8…`).
   - On our forcing its TE hindcast RMSE is 1.97 vs 0.52 cm, and its SSP2-4.5 TE is 6.6 vs 19.4 cm at 2100.
   - Either Tony publishes our file (a Zenodo record or a release asset; then set the URL in
     `tools/fetch_brick20_posterior.sh`), or the BRICK 2.0 arm moves to the public posterior (a substantive rerun).
2. **The deferred conditioning rerun** (Marcus 10-08): bundle it with the next substantive rerun. Item 1's second
   option would be one.
3. **The docx pass** (when Marcus green-lights it and has Tony's latest file). It carries:
   - the v1.1 and 10-07 numbers;
   - the label "Ladrillo v1.1";
   - Table A2 on the subsample;
   - Intro 1.3× → 1.4×;
   - the paired tap statistics (decision 4);
   - the one-sentence conditioning qualifier (candidate wording in `notes/ladrillo_v11_paper_number_diff_2026-10-08.md`
     §3.5);
   - the 8 wording fixes of `handoff_2026-10-01c_gmd_round.md` §1c.
4. **⛔ Two FaIR-forcing inputs are not public** (Ladrillo CHANGELOG 10-08f; `tools/forcing/README.md`). A reviewer can
   rebuild the SSP and calibration forcing, but NOT the van Vuuren forcing.
   - The IIASA `scenariomip-2026-prerelease` emissions (gated login) feed ALL 28 vv files.
     - The public Zenodo 20713982 file is not a substitute: names and values differ, by up to 4× in minor gases.
     - Options: wait for the final public ScenarioMIP release; ship the derived vv emissions intermediate (if the terms
       allow); or rebuild vv on the Zenodo file, which changes numbers.
   - The EDF / Rennels AR6 SSP2-4.5 file shapes ssp245harm after 2100 only. Ask Lisa Rennels / EDF about the licence.
   - ⚠ Before a PUBLIC release, decide what `tools/forcing/README.md` says about both. A private push is fine as is:
     no input data is committed, only checksums and fetch code.

## 4. What this session did (CHANGELOG 10-08d → 10-08h in SLR-RFF-BRICK; 10-08c → 10-08e in Ladrillo)

- **Decision 4, ruled:** quote the tap as paired statistics. 2300: SSP5-8.5 96.2% / +35.0 cm; SSP2-4.5 11.7% /
  +1.5 cm; SSP1-2.6 0.25% / 0.00. `python/diag_tap_paired_contribution.py`.
- **Decision 2, ruled:** no conditioning in the paper; v1.2 opt-in in the package.
  - Then found: the joint arm DOES hold record-crossing draws, 3 of 2,000 SSP and 2 vv by 2025.
  - The likelihood-weighting test: the calibration likelihood rejects every onset through 2025 (Δ log L −46 to −1703)
    and keeps every 2026 onset (w = 1), so the record end is its own cutoff.
  - Effect: medians ≤ 0.23 cm, p95 ≤ 3.8 cm (≤ 0.38 se); the Very Low width 163 → 162.
  - Marcus: defer the rerun; add a one-sentence qualifier at the next full edit.
- Items 3, 5 and 6, Tables A1/A2, and the BRICK 2.0 URL search (§3.1).
  - Items 3 and A1/A2 were done by delegated agents and verified here: an independent forcing rebuild + `shasum`; a
    tables gate rerun; a 1-ulp mutant on the reference-only tables gate; the full suite.
- **Item 2 (calibration code) and item 4 (figures) remain.** Not needed for a private push. Marcus listed 3, 5 and 6
  first.

## 5. Non-obvious state

- **Colima may still be running** (FACTS is not needed); `colima stop` frees about 3.5 cores. That is Marcus's call.
- **`tools/build_test_reference.py <SLR-RFF-BRICK>`** regenerates `test/reference/` from the research outputs. It
  refuses dirty sources. Re-run it only for a new certified release, and commit the result with the release.
- **Scratchpad copies** (the Zenodo BRICK file, mutation copies) are in the old session's scratchpad and are disposable.
- **macOS `/bin/bash` is 3.2:** no `$BASHPID`, and `set -u` traps.
