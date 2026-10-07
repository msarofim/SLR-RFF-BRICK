# Handoff 2026-10-07b: Ladrillo.jl package built and certified; van Vuuren arms re-running on the CMIP7 basis

Follows `handoff_2026-10-07_clean_l27_repo.md`. That handoff's manifest (§3 A–G) is still the porting map; it is not
repeated here. This note records what was decided and built, and what is still in flight.

## 1. What we are doing

We are building a clean, submission-ready, L27-only Julia package `Ladrillo.jl`, as Tony asked: a reviewer should be
able to clone it from GitHub and run an example. At the same time, the paper's van Vuuren (vv) arms are being re-run
on the CMIP7 forcing basis.

## 2. Decisions (all Marcus, 2026-10-07)

| # | decision | rationale / receipt |
|---|---|---|
| 1 | **Rerun every vv arm on CMIP7, FACTS included**; the paper's vv numbers update | FACTS's `vvM` input rebuilds from the QUARANTINED Smith cubes at max\|Δ\| = 0.0 K, so FACTS was on the Smith basis. On that basis the vv pre-2014 history sat up to 0.074 K off the `ssp245harm` calibration driver (1995–2014 mean 0.750 vs 0.803 °C), so the vv arms were MIXED-BASIS even against Ladrillo's own SSP arms. On CMIP7 the gap is 0.015 K. After 2014 the spliced path moves +0.055 K @2100 and +0.067 K @2300 (median). MAGICC-SLR uses its own climate and is unaffected; the MAGICC-climate SPLICED arms ARE affected, because they take `MEAN_G` before 2014. |
| 2 | **Joint arm + Table A2 read the 10k subsample**, not the raw chains | For the JOINT ARM this is proven a no-op: `subsample[1:5:end]` is bit-identical (50 columns, same order) to its chain draws. Confirmed end to end by product gate 2. **Table A2 (thinned by 200, 20k draws) is NOT a subset and will move. Quantify it when porting.** |
| 3 | Dangendorf v2 **may be redistributed** (ship it with citation) | — |
| 4 | `regen_imbie_fig_L27.sh` → **fold into the figures script** as a direct `diag_imbie2026_vs_targets.py` call | its target swap has been unneeded since 09-30 |
| 5 | **Keep v1.0's two paleo-attachment rules**; single assignment at v1.1 (with the land-water fix) | The joint arm attaches λ/T_crit per CHAIN (blocks of 500, seed restarted), so its 4 chains reuse the same 500 paleo rows. The SSP panel attaches once over its 2,000 rows. A single assignment over 10k leaves ssp585 medians unchanged (≤1.3 se) but moves the 2100 p95 by −3.6 cm (total) and −5.0 cm (AIS), about 2.5 bootstrap se. Tool: `scripts/project_joint.jl --paleo=single`. |
| 6 | **The BRICK 2.0 posterior is fetched, not shipped** | `parameters_subsample_brick.csv` (sha256 78247db8…) is Tony's post-PR#93 subsample with no documented public source. `tools/fetch_brick20_posterior.sh` needs a URL from Marcus/Tony. The file was purged from the package's local history (no remote existed yet). |

Also: package authors = Marcus only for now; **adding Tony is Marcus's call, not yet asked**. CITATION.cff affiliation
must be "NYU Marron Institute" (professional output).

## 3. Built

### New repo `~/Documents/2026/CodeProjects/Ladrillo/` (local git, `main`, NO remote yet; HEAD 151ea00)

`src/`: `Ladrillo.jl` (module), `components/glaciers.jl` (`ladrillo_glaciers`, R19/SLOWG/FASTG),
`components/greenland.jl` (`ladrillo_greenland`, two basins + the shipped 2-stage whole-sheet tap), `landwater.jl`
(`:observed` / `:central`, with the `:v1_step` known issue), `posterior.jl` (`posterior(rows, paleo_block)`,
`attach_paleo!`, `native_greenland!`), `model.jl` (`LadrilloModel`, `apply_draw!`, `run_draw!`, `sea_level`),
`forcing.jl` (`mean_forcing`, `forcing_cube`, `splice`). Data is in `data/` (88 MB) with `data/MANIFEST.csv`
recording source, commit and sha256. It was imported by `tools/import_l27_data.py`; renames are label-only and
verified per file.

**Scripts:**
- `project_joint.jl` — joint + fixed arms, one scenario.
- `project_fixed.jl` — the SSP panel.
- `brick20_joint.jl` — the BRICK 2.0 arm.

`README.md` and `CHANGELOG.md` exist. LICENSE is MIT.

**Certification:**
- **Gate 1, kernel** (`test/identity/{cases,dump_old,dump_new,compare}.jl`): every component × year × draw, `==`,
  against the research kernel. PASS on K1 (ssp585, all 10k draws, tap on), K2 (ssp245, no tap), K3 (hindcast,
  `:central`, to 2026) and K4 (vvH joint).
- **Gate 2, products** (`test/identity/compare_products.jl`): **vvVL PASS** for Ladrillo (72,000 values) and BRICK 2.0
  (36,000). The fixed SSP panel reproduces the SHIPPED `ssps_components_2300_L27_tap…_n2_ws.csv` and
  `ssps_components_2300_L27.csv` exactly (5,598 rows each).
- **Mutation test** (`test/identity/mutation_test.sh`, result in `mutation_result_K4.txt`): 3 of 3 real mutants
  killed (1-ulp share, reassociation, paleo block). 2 no-power controls survived, as they should.
- The MimiBRICK build scenario does NOT leak (0 cells differ between ssp585 and ssp245 builds), so every product
  builds on ssp245.

### SLR-RFF-BRICK (commit 0c4de0a)
- `python/gate_vv_cmip7_basis.py` — the [VV-BASIS] ordering gate; mutation-tested to FAIL 7/7 on the Smith copy.
- `run_vv_cmip7_rerun_20261007.sh arms|downstream`.
- CHANGELOG 2026-10-07b.

### facts (branch `slr-comparison-arm`, uncommitted)
- `run_vv_cmip7_rerun_20261007.sh`: quarantines inputs/outputs, rebuilds the 14 vv climate inputs, checks configs
  byte-identical, runs docker, re-extracts, then gates [SSP-ROWS].

## 4. ⚠ IN FLIGHT and next steps

1. **`./run_vv_cmip7_rerun_20261007.sh arms` is RUNNING.** It was started 15:28 from the session shell and was at
   22/29 steps, 0 failed, at 16:45. ETA about 17:15. Log: `outputs/log_vv_cmip7_rerun_20261007.txt`. Snapshot:
   `outputs/quarantine/20261007_vv_smith_history_arms/` (586 files; pruned in the downstream phase).
   **Do not edit `julia/*.jl` or `python/*.py` in SLR-RFF-BRICK until it ends.** Check the work process with `ps`, not
   `pgrep -f` (it matches its own command line).
2. **FACTS:** `colima start` (profile default: 8 CPU / 8 GiB), then `~/Documents/2026/CodeProjects/facts/run_vv_cmip7_rerun_20261007.sh`
   (about 45 min).
   - The CCX `run_dispersed_multistart.R` (8 workers, another session) was holding 8 cores. Check `uptime` first.
   - Then write `facts/quarantine/20261007_vv_smith_history/README.md` and commit on `slr-comparison-arm`.
3. **`./run_vv_cmip7_rerun_20261007.sh downstream`** — tables and figures, then prunes the quarantine snapshot to
   what moved. Then write the quarantine `README.md` (bug, files, canonical replacements).
4. **Paper-number diff for Marcus:** old (quarantine) vs new vv cells at 2100/2150/2300, for Ladrillo, BRICK 2.0 and
   FACTS. Sections 4.2–4.3, Figs 2–6. ⛔ **Do not edit the GMD docx.** Tony holds the review copy; list the changes
   for Marcus.
5. **Product gate 2 on all 7 markers**, against the fresh research outputs:
   `julia --project=. scripts/project_joint.jl --scenario=vvX`, then `brick20_joint.jl`, then
   `compare_products.jl ../SLR-RFF-BRICK/outputs ladrillo|brick20 vvX`.
6. **Remaining ports** (manifest §3 of the earlier handoff):
   - posterior predictive (`LadrilloModel` needs a `ref` kwarg, FIT_REF 1995–2005, `lws=:central`, `ssp245harm`,
     plus `recalib_targets_ext_gsicadj.csv`);
   - IC residuals, Table 5;
   - calibration (`calibrate_mcmc_ext.jl` L27 path) with `gate_calibrator_identity` on the renamed headers;
   - the FaIR builders (§3C: relative paths, Zenodo download, fix `requirements.txt`);
   - figures and tables (§3E), with Table A2 on the subsample (quantify the move);
   - tests (§3D, L27-only);
   - CITATION.cff; trim the Manifest of julia_v2's extra deps;
   - a `test/runtests.jl` that a reviewer can run without the research repo (the identity gate needs it).
   Then create the PRIVATE GitHub repo with `gh`; Marcus makes it public and adds Tony.

## 5. Non-obvious state

- The identity references (`old_*.jls`, about 0.5 GB) are in this session's scratchpad (`…/scratchpad/identity/`) and
  WILL NOT survive. Regenerate with `julia --project=$SLR/julia_v2 test/identity/dump_old.jl $SLR` (about 10 min)
  before re-running gate 1 or the mutation test.
- `data/brick20/parameters_subsample_brick.csv` exists locally (gitignored) so `brick20_joint.jl` runs. A fresh clone
  lacks it until the URL exists.
- Package outputs (`outputs/projections/`, gitignored): joint vvVL and ssp585 (v1 + `_paleosingle`); fixed panels
  (tap and no-tap); brick20 vvVL.
- Julia reads a whole script before running it, so editing a `.jl` under a running Julia is safe. That is NOT true
  for Rscript. Rewriting DATA files under a running job is not safe; it happened once today, and the gates passed
  afterwards.
- Memory: `ladrillo_clean_repo_decisions.md` (updated with decisions 5–6 and the build state).
