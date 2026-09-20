# Handoff — L27 shipped as the paper's posterior; NEXT = the one-round docx swap (09-20 14:45 → 19:50)

**Start here.** Continues `handoff_2026-09-20_L26_promoted_L27_running.md` (its §3 decisions, §5 traps and §6 open
questions all still stand; only its §1 NEXT list is superseded by this file). CHANGELOG **09-20e** is the primary
record (5 commits `1a51056..19e317d` on `ladrillo-dev`, all pushed). Memory written this arc: `l27_paper_posterior`,
`ic_profile_optimiser_bimodal`; `INDEX_slr.md` LIVE STATE header rewritten (it still said L24 champion).
Read `INDEX_slr.md` and `INDEX_cmp.md` before touching a deliverable.

**STATE AT HANDOFF (2026-09-20 ~19:50):**
- **L27 (50 params) IS THE PAPER'S POSTERIOR** per Marcus's 09-20 conditional ("if the hindcast is unchanged, L27 is
  the paper's posterior") — the one-axis gate PASSED (§2). **L26 stays CHAMPION** in `benchmark/champions.json`;
  promoting L27 is Marcus's call (`bench_ladrillo.py --freeze` then `--promote`; the 09-20 reasoning is in the registry).
- **Every L27 product exists**: subsample, postpred, SSP components (tap / no-tap), 3 joint bands, 13 paper projection
  arms, Tables 4 / 5 (IC, three ρ bounds) / A1 / A2, benchmark, memo + `--paper` figures (`figures/paper/*L27*`).
- **ONE BACKGROUND JOB STILL RUNNING** (launched 19:40, nohup, ~1 h): `run_l27_vv_magiccclim.sh` — the 7 vv-marker
  MAGICC-climate Ladrillo arms (spliced + raw) that FIG 11 (climate swap) needs, chained to
  `plot_ladrillo_memo_figures.py --tag=L27` and `plot_vv_climate_swap.py --tag=L27 --year=all`. Log:
  `outputs/log_l27_vv_magiccclim.txt` (ends with `memo exit N`, `swap exit N`, `ALLDONE`). Its outputs are NOT
  committed yet — commit `outputs/scope_slr_fairunc_*_vv*_magiccclim_L27_*.csv` (cells/gates only; draws/paths are
  gitignored), `figures/*climate_swap*L27*`, `figures/*memo*L27*` / fig1–3 when it lands. Kill by PID, never `pkill -f`.
- Draft: `deliverables/GMD.Ladrillo.v1_review-2026-09-20.docx` — **still on L24 numbers throughout.** Nothing in the
  docx was touched this arc.

---

## 1. ⭐ NEXT (in order)

1. **Check the background job landed** (`ALLDONE`, both exits 0); commit its outputs (see above). If `memo` failed
   again, its driver is `python/plot_ladrillo_memo_figures.py` (its OWN `TAG_DESC` now declares L26/L27).
2. **THE ONE-ROUND DOCX SWAP to L27** — every table and figure together, never a mix (handoff §5 trap). Tooling:
   `deliverables/redline/redline.py` + a new `apply_edits_r6_l27.py` modelled on `apply_edits_r5_tableA2.py`
   (tracked changes under author "Claude"; reject-all must reproduce the base). Base = the 09-20 docx. The swap list:
   - **FIG 1** hindcast → `figures/paper/hindcast_components_L27.png`; **FIGs** vv comparison 2100/2150/2300,
     vv trajectories, gsic ladrillo-only, responsiveness → `figures/paper/*_L27*.png` (sidecar `.caption.txt` = the
     provenance the memo figure would have drawn).
   - **Table 4** (hindcast RMSE by window) → recompute from `outputs/postpred_L27_components_timeseries.csv` the same
     way the L24 table was (the 09-20e CHANGELOG lists the full-window values; the per-window ones are in this
     session's transcript table and reproduce from the file).
   - **Table 5** (IC) → `outputs/ic_ladrillo_vs_brick20_L27.md` (+ `_rho0.95`, `_rho0.9`): Δk **15**, ρ≤0.99 ΔAIC
     **+84.1** / ΔBIC **+20.8**; 0.95: +141.2 / +78.0; 0.90: +207.9 / +144.6. The AIC paragraph's "BIC tie" sentence
     changes: the tie is gone at every bound.
   - **Table A1** → `outputs/ladrillo_prior_posterior_L27.md` (50 rows; `deliverables/GMD_TableA1_priors_posterior_L24.docx`
     was the pandoc route — rebuild with the L27 md). **Table A2** → `outputs/ladrillo_table_a2_L27.md` (14-parameter
     block, 3 identified combinations — same three as L26).
   - **Text**: parameter count 58 (= 17 + 9 + 19 + 13) → **50**; "λ, T_crit, γ held at their paleo medians / attached
     as joint paleo draws in projections" (Methods); the Antarctic "onset 1998" text → the wide posterior (already
     drafted in spirit for L26 — check the draft's current wording); `u_unch` in the upper half of its Parkes &
     Marzeion range and the runoff-onset LOCATION following L (handoff §3) still owed; headline joint numbers
     ssp245 total **52.6 cm @2100 [36.2, 107.1] / 248 @2300 [84, 445]**, ssp585 **90.7 / 498** (`outputs/
     scope_slr_fairunc_cells_ssp*_spliced_L27_tap*.csv`, arm `joint`). ⚠ ssp245@2300 is the 48 %-tipped cell — mean
     + tipped fraction, never the bare median.
   - Convergence sentence: 8 of 50 marginals fail R̂ (AIS geometry ridge; Greenland converges), projected SLR R̂
     1.001 / 1.002.
3. **Decide the L27r question** (§3 below) — it changes one sentence of the paper (the stated precision of the AIS
   medians) and costs ~4 h (Torch-eligible; ask first).
4. Then the 09-16 list, unchanged: venue (GMD recommended), package extraction for Tony's team, the `facts`
   remote (Marcus's action), the FACTS/MAGICC-scope call, the "must STATE" items, the pulse analysis.

## 2. WHAT HAPPENED 14:45 → 19:50 (receipts: CHANGELOG 09-20e)

- Chains done 17:39; postprocess unattended to 18:19. Arm verification OK (every banner: cut-fastdyn / fix-gamma /
  no-ledger, 50 free). Noise-mode gate PASS (sd_gis 0.025). 8/50 R̂ fails, all AIS ridge. `--accept-slr`.
- **One-axis gate PASS**: postpred full-window RMSE L26 → L27: glaciers 0.315 → 0.317, AIS 0.090 → 0.093, GIS 0.198
  → 0.196, TE 0.472 → 0.467, total 0.417 → 0.403 cm (L26 values reproduce CHANGELOG 09-20). Option D exonerated.
- **IC**: `ic_hindcast_residuals.jl --tag=L27` GATE PASS (0.0 vs postpred p50). The first `run_ic_arms.sh L27`
  FAILED its 24-draw optimiser validation — a real bug in `python/ic_ladrillo_vs_brick20.py` (bimodal profiled
  surface: sd → 0 plateau vs peak at the ρ bound; the reference multistart sat on the plateau, the polish could not
  cross basins, and the near-bound grid rows were literals for ρ ≤ 0.99). Fixed (d774b01), tolerance untouched;
  **L26 regression identical to the shipped 09-20b numbers**; pre-fix outputs → `outputs/quarantine/20260920_ic_optimiser/`.
- **Projections**: glaciers / TE / GIS unchanged (≤ 0.5 cm); AIS ssp126 2300 p95 167 → 65 (fixed-climate) = the
  paleo corr(λ, T_crit) +0.45 removing 4.5× of the collapse corner — DESIGNED; AIS medians −3 cm @2100 / −13 @2300
  (fixed) or −1 / −8 (joint) on ssp245 = a move ALONG the flat ridge (§3).
- Benchmark: 2/178 verdicts change, both WARN → PASS. Table A2 on L27 (PCA diag made tag-aware). Paper arms +
  figures 18:43–19:40. `run_paper_arms_L27.sh` is the reusable template for any later tag (T via `TAG=`).

## 3. THE OPEN QUESTION — between-refit precision of the AIS medians (not resolved; Marcus's call)

The DAIS block moved 0.3–0.5 L26-sd between L26 and L27 with the AIS hindcast unchanged. Tests done: (i) the three
cut parameters were likelihood-FLAT in L26 (post sd / prior sd 0.99, 1.00, 0.86 = γ's truncation factor; corr with
the geometry ≤ 0.04) ⇒ the cut cannot have moved the geometry through the likelihood; (ii) per-chain medians
(`outputs/diag_ais_geometry_perchain_L26_L27.csv`): slope / iceflow0 / T_on = L26's chain 2029 was 0.8–1.4 sd off
the other three (mixing); anto_α / anto_β / ocean_T₀ / antarctic_α = all four L27 chains agree at a place OUTSIDE
L26's four-chain range — not explained by L26's spread, not a likelihood effect. Candidate explanations: shared
slow drift along the ridge (τ ≈ 47k; all four chains of each run share a start region — L26 from L26d draws, L27
from L26 draws), or the ledger marginalisation coupling in a way I cannot see. **Two tests that separate them:**
L27r (same objective, new seeds AND starts from the L27 adapted cov + overdispersed L27 draws; if it lands on L27,
the move is real and L26 was the drifted one) and L27b (L27 without `--no-ledger`; if it lands on L26, D couples).
Either is ~4 h. The paper needs at minimum a STATED precision on the AIS projection medians; the current evidence
is ~±1 cm @2100 / ±8 @2300 (joint) between two refits of near-identical objectives. No likelihood column is written
to the chains, so a mode-vs-mode likelihood check needs a Julia evaluation (not built).

## 4. FILES (new or changed this arc)

Scripts: `run_paper_arms_L27.sh` (template), `run_l27_vv_magiccclim.sh`. Code: `python/ic_ladrillo_vs_brick20.py`
(optimiser), `python/diag_ais_block_pca.py` (tag-aware), `python/ladrillo_figs.py` (L27 in TAG_DESC),
`python/plot_ladrillo_memo_figures.py` (L26/L27 in its own TAG_DESC). Outputs (committed): `postpred_L27_*`,
`bench_ladrillo_L27.{csv,md}`, `ic_ladrillo_vs_brick20_L27*` (+ `_L26` re-run), `ladrillo_prior_posterior_L27.{csv,md}`,
`ladrillo_table_a2_L27.md`, `diag_ais_block_pca_L27.csv`, `diag_ais_geometry_perchain_L26_L27.csv`,
`ladrillo_model_comparison_L27*.csv`, `vv_model_comparison_L27.csv`, `ladrillo_priors_L27.csv`,
`data/MimiBRICK/parameters_subsample_brick_mengel_L27.csv` (force-added). Figures: `figures/*L27*`,
`figures/paper/*L27*`. Not committed (gitignored or pending): the L27 chains (4 × 2 GB), `scope_slr_fairunc_*L27*`
draws/paths, `outputs/quarantine/20260920_ic_optimiser/` (README), the running job's outputs. Logs:
`outputs/log_l27_postprocess_driver.txt`, `outputs/log_paper_arms_L27.txt`, `outputs/log_ic_arms_L27.txt`,
`logs/ic_ladrillo_vs_brick20_L27_rho*.log`, `outputs/log_l27_vv_magiccclim.txt`.

## 5. ⚠ NON-OBVIOUS STATE / TRAPS (adds to the 09-20 handoff's §5, which all still applies)

- **Never mix L24 / L26 / L27** — the docx is L24 throughout until the one-round swap; `figures/paper/` now holds BOTH
  `*_L24*` and `*_L27*` renders side by side.
- **The IC max-over-draws ln L is an extreme-value statistic**: L27 238.0 vs L26 242.6 while the posterior-median
  series scores 229.9 vs 230.2. Don't read a 4.6 ln L "loss" into it.
- **The L27 subsample carries NO λ / T_crit / γ columns**; the kernel attaches them at projection time
  (`ladrillo_attach_propagated!`, seed 20260920, 500 rows per chain of `paleo_fastdyn_draws.csv`). Any reader that
  expects those columns must go through the kernel; `_count_sampled` in the IC script therefore reads k = 42 correctly.
- **`--rho-max` arms**: the grid's near-bound rows are now RELATIVE to the bound; the ρ ≤ 0.90 arm's optimum for some
  glacier draws sits AT the bound (ρ = 0.900) — that arm's gain is partly the bound, as the md's own caveat says.
- Three tracked L24 outputs in the tree (`ladrillo_priors_L24.csv`, `seed_diag_L24_seed2026.txt`,
  `vv_responsiveness_L24.csv`) differ from HEAD ONLY in provenance timestamps (numeric columns byte-identical) —
  test-suite re-runs; left uncommitted deliberately.
- `champions.json` untouched: L26 is champion, L27 the paper's posterior. Say both when either is quoted.
