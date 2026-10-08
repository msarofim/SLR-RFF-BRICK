# Handoff 2026-10-07c: Ladrillo v1.1 (paleo single assignment + land-water frame fix)

Follows `handoff_2026-10-07b_ladrillo_package.md`, whose §4 work is now done (§3 below). That handoff's manifest
(`handoff_2026-10-07_clean_l27_repo.md` §3 A–G) is still the porting map for what remains.

## 1. What v1.1 is

v1.1 is **the same posterior (L27), with two projection-side fixes**. **No recalibration.** The calibration forcing
(`ssp245harm`) was CMIP7-based throughout. Every calibration-dependent product came back unchanged after the 10-07 vv
rerun: the posterior, the hindcast bands, Table 4 values and Table 5.

| fix | v1.0 (shipped) | v1.1 | measured size | where |
|---|---|---|---|---|
| **A. Paleo assignment** | λ / T_crit attached per CHAIN in the joint arm (blocks of 500, RNG re-seeded per block; the 4 chains reuse the same 500 paleo rows). The SSP panel attaches once over its own 2,000 rows. | ONE assignment over all 10,000 posterior draws, then any subset keeps the rows its draws have in the full table | ssp585: medians ≤ 1.3 bootstrap se; 2100 p95 −3.6 cm total, −5.0 cm AIS (~2.5 se) | package: `posterior()` + `attach_paleo!`, `scripts/project_joint.jl --paleo=single` (exists). Research: `julia/scope_slr_fair_uncertainty.jl` reads raw chains, `n_per_chain` 500 (:46, :90); `julia/project_ssps_components_ladrillo.jl:138` |
| **B. Land-water frame step** | `:observed` land water starts at obs[1900] = +1.565 cm (1995–2005 frame) while the other components start at 0 in 1850; DAIS's sea-level feedback sees the step | `:zero_at_first_year` | ≤ 0.012 cm of Antarctic sea level at any year (all 2,000 draws, 2026-10-01) | package: `src/landwater.jl:21` `LWS_OBS_ANCHOR`. Research: `julia/brick_mengel.jl:79` (`lws_frame_guard`, `LWS_V1_NEWEST_TAG = 35`, suite step 11) |

Decision 5 (Marcus 10-07 morning): "keep v1.0's two paleo-attachment rules; single assignment at v1.1 with the
land-water fix". Memory: `ladrillo_clean_repo_decisions`, `lws_frame_step_v1`.

## 2. ⛔ OPEN DECISIONS — ask Marcus before building

1. **Does the GMD paper move to v1.1 now, or does v1.1 ship after review?**
   - Moving now reverses ruling 5. Its reproducibility argument is weaker now that the paper's vv numbers are changing
     anyway (§3), but it widens the change set from vv-only to EVERY projection: SSP figures, Figs 2–6, and the
     Conclusions' "up to 31 cm".
   - Claude leaned towards "now" (one round of number changes, and a reviewer cloning the package would find the
     per-chain reuse). Marcus has not ruled.
2. **Which code produces the v1.1 numbers?**
   - (a) Add both fixes to the research drivers and re-run, as for the vv rerun. The package is then re-certified
     against the new research outputs.
   - (b) Make the package the producer and point the research figure scripts at its outputs.
   - (a) keeps one certified chain of custody. (b) avoids a second implementation of the single assignment. The research
     joint arm reads RAW CHAINS (2 GB each), so under (a) it must first be switched to the 10k subsample (decision 2;
     proven a no-op at v1.0 by product gate 2).
3. **Versioning:** tag the package `v1.0.0` at its current HEAD before any change, so the paper-as-submitted stays
   reproducible. v1.1 must keep both v1.0 behaviours reachable as options (`--paleo=v1`, `LWS_OBS_ANCHOR=:v1_step`).
   Proposed: `Project.toml` version 1.1.0, defaults flipped, options retained.
4. **Table A2 on the subsample** (decision 2, still owed): quantify the move from the chains-thinned-by-200 table to
   the 10k subsample. If the paper moves to v1.1 anyway, do it in the same pass.

## 3. State at handoff (all committed)

| repo | commit | pushed? |
|---|---|---|
| `SLR-RFF-BRICK` (`ladrillo-dev`) | 5184a57 | **no: 3 ahead of origin** |
| `facts` (`slr-comparison-arm`) | 43bf0204 | no upstream configured |
| `Ladrillo` (`main`) | a2bb3b0 | **no remote yet** |

### vv CMIP7 rerun: DONE
- Arms: 0 failed. FACTS: 14/14 OK; [DRIVER] 20/20, [EXTEND] 10/10, [SSP-ROWS] 4,599 identical. Downstream: 16/16.
- The FACTS driver's shell died after 4/14 experiments; `facts/run_vv_cmip7_rerun_20261007_resume.sh` finished the run.
- Quarantine READMEs:
  - `outputs/quarantine/20261007_vv_smith_history_arms/README.md` (129 files). §3 lists three files that moved for
    OTHER reasons: the benchmark (the 09-30 AIS target revert, bc50130), Table 4 (provenance column only) and the SSP
    memo figures (palette only).
  - `facts/quarantine/20261007_vv_smith_history/README.md`.
- **For Marcus:** `notes/vv_cmip7_paper_number_diff_2026-10-07.md` (+ CSV). 18 of 31 quoted quantities change at the
  text's rounding, and the prose orderings survive. Two caveats:
  - The Very Low 2300 width moves 137 → 161 cm: a near-threshold DAIS tail.
  - FACTS DeConto/Bamber p95 is bimodal at n = 200 (memory `facts_p95_bimodal_at_n200`).
  - ⛔ The GMD docx was NOT edited; Tony holds `GMD.Ladrillo.v1_forTonyreview_TW1.docx`.

### Ladrillo.jl: every gate PASS against the research outputs, bit-identical
| gate | covers | file | mutation-tested |
|---|---|---|---|
| 1 kernel | 4 cases, every component × year × draw | `test/identity/compare.jl` | yes (3/3 killed) |
| 2 products | joint arm, all 7 vv markers × Ladrillo + BRICK 2.0 | `compare_products.jl` | via gate 1 |
| 3 postpred | bands, bias, coverage | `compare_postpred.jl` | yes (seed, F_unch) |
| 4 hindcast | BRICK 2.0 hindcast, IC residuals 10k × 644 × 2, obs sigma | `compare_hindcast.jl` | yes (ref, lws; seed is NOT a control, below) |
| 5 Table 5 | 3 rho bounds, table + per-draw | `compare_ic_table.py` | comparator power, 1-ulp |

Added this session:
- `src/targets.jl` (`calibration_targets`), `src/brick20.jl`;
- `LadrilloModel(...; ref=)`, `sea_level(...; funch=)`;
- scripts `posterior_predictive{,_brick20}.jl`, `ic_hindcast_residuals.jl`, `python/ic_ladrillo_vs_brick20.py`;
- CITATION.cff (Marcus only, "NYU Marron Institute"; adding Tony is Marcus's call), `requirements.txt`, README
  reproduction sections.

## 4. Build plan for v1.1 (once §2 is ruled)

1. Tag `v1.0.0` in Ladrillo (and note the SLR commit it certifies against).
2. **Fix B (land water):**
   - Flip `LWS_OBS_ANCHOR` in both codebases.
   - Gate: only `ais` and `total` (and `lws` itself) may move, and AIS by at most the measured 0.012 cm. Every other
     component must be IDENTICAL; that ordering is the gate.
   - Run the LWS flip ALONE first, so its effect is separable from fix A.
3. **Fix A (paleo):**
   - Default `--paleo=single` in the package. Research: implement the same single assignment on the 10k subsample
     (or adopt §2.2b).
   - Expect the ssp585 numbers in §1 and no movement in any hindcast product.
   - **Measured this session:** the IC residuals (paleo attached over 10,000 rows) reproduce the postpred p50
     (attached over 2,000) to < 1e-9. λ / T_crit do not touch the 1850–2026 hindcast. If a hindcast product moves under
     fix A, that is a bug.
4. Regression: with both v1.0 options set, the v1.1 package must reproduce v1.0 bit-for-bit (gates 1–5 unchanged).
5. Re-run the projections (vv arms ≈ 1.5 h; the SSP panel; downstream), quarantine the v1.0 products as SUPERSEDED,
   not bugged (they are the submitted version), and write a v1.0 → v1.1 number diff like the vv one.
6. Then the remaining ports (manifest §3): calibration (`calibrate_mcmc_ext.jl` L27 path + `gate_calibrator_identity`
   on renamed headers; **porting the code, not re-running the 2M-iteration chains**), the FaIR builders (§3C), the
   figures (§3E), Table A2, tests, a `runtests.jl` that works without the research repo, the Manifest trim, then the
   PRIVATE GitHub repo via `gh` (Marcus makes it public and adds Tony).

## 5. Non-obvious state

- **Colima is still running** (8 CPU / 8 GiB VM, about 3.5 cores busy even when idle). `colima stop` when FACTS is not
  needed. The CCX `run_dispersed_multistart.R` (another session) holds about 5 cores; check `uptime` before long jobs.
- **Gate 1 needs the research-kernel references** (`old_*.jls`, about 0.5 GB). They lived in an earlier session's
  scratchpad and are gone. Regenerate with `julia --project=$SLR/julia_v2 test/identity/dump_old.jl $SLR` (about 10
  min). Gates 2–5 compare against files in `SLR-RFF-BRICK/outputs/` and need nothing extra.
- **The BRICK 2.0 get_model seed is a real input of the hindcast:** ≤ 8.8e-4 cm on AIS 2020–2025, via BRICK's 2019+
  land-water draw and the AIS sea-level feedback (memory `mimibrick_getmodel_seed`). It is recorded in every
  provenance column.
- **Comparators must parse floats exactly.** pandas needs `float_precision="round_trip"`; CSV.jl is exact.
- **Table 5 takes about 40 min per rho bound** with `IC_WORKERS=4` on 10k + 10k draws.
- **Never rewrite `data/` under a running Julia job.** It happened once this session: `import_l27_data.py` re-run
  mid-gate, bytes identical, gates passed. Julia reads a whole `.jl` before running, so editing scripts is safe; but a
  `src/` edit is picked up by any Julia process started afterwards.
- **The package's `data/brick20/parameters_subsample_brick.csv`** exists locally (gitignored). A fresh clone needs the
  fetch URL from Marcus/Tony (decision 6).
- **Memory:** `ladrillo_clean_repo_decisions` (build state), `facts_p95_bimodal_at_n200`, `mimibrick_getmodel_seed`
  (extended), `lws_frame_step_v1`.
