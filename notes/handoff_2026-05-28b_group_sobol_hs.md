# Handoff — Group-Sobol SLR H-S (replacing TreeSHAP) + normalized framing (2026-05-28b)

**Owner:** Marcus C. Sarofim
**Continues:** `notes/handoff_2026-05-28_v5_hs_poster.md` (the Sobol decision).
Self-contained for a cold start; read this + `CLAUDE.md` +
`memory/project_slr_hs_sobol_decision.md`.

**📊 FIGURE INVENTORY (single source of truth for ALL poster + Substack figures →
generating script → output path → status):** `notes/figure_inventory.md`.
Read it to know which figures exist, what's current vs quarantined, and which
script regenerates each. (This handoff documents only the figures changed this
session; the inventory covers the whole set.)

---

## STATUS 2026-05-28 (later) — COMPLETE

All steps below are DONE. Full 131-year Group-Sobol run finished (all 4 targets),
all figures re-rendered with 11-yr display smoothing, poster panels C/D + IEc
handoff copies regenerated, poster_text.txt captions C/D + Discussion numbers
updated to Group-Sobol, scoping memo written
(`notes/memo_2026-05-28_hs_ensemble_scoping.md`). Final numbers (smoothed,
of-total): total SLR @2150 emissions 29% / climate 27% / brick 17% /
interactions 21% / tipping 5% / internal 0.6%. Project is NOT a git repo → no
commit made. Only remaining (separate, Torch-blocked) item: CH4 pulse de-noising.

## ADDENDUM 2026-05-29 (later) — 324k ANOVA LAUNCHED; CH4 left as-is

- **CH4: decided LEAVE AS-IS** (Marcus). No repoint, no smoothing. Brick-averaging
  was a null result (see below). pulse_responses_clean.py unchanged.
- **324k balanced-factorial ANOVA: LAUNCHED on Torch** (cs partition):
  - FaIR cube **job 9811743** (`cube_v145_anova324k_baseline_flat2015.npz`),
    metadata `anova324k_fair_metadata.csv` (54k FaIR cells: rff300×cfg60×seed3).
  - BRICK arm **job 9811744** (`--dependency=afterok:9811743`), metadata
    `anova324k_brick_metadata.csv` (324k BRICK cells ×post6), output
    `outputs/brick_v145/brick_anova324k_baseline.csv`, SAVE_TRAJS=true SAVE_COMP=false.
  - **Measured FaIR rate (smoke 9810807): ~3,760 cells/min on 8 cores** (ANOVA regime
    ~18× the I/O-bound baseline). 324k chain ≈ ~18 min FaIR + ~65 min BRICK.
  - A background waiter runs `anova_hs_decomp.py --tag 324k` ON TORCH when BRICK
    finishes (decomp is LoTV-correct: internal = within-cell across-seed variance,
    validated on synthetic data, sums to 1). **Pending (task #12):** pull
    `outputs/substack/shapley_hs_per_axis_total_slr_anova324k.csv`, overlay vs
    `shapley_hs_per_axis_total_slr_hybrid_tipping.csv` (Sobol) at 2100/2150.
    Expect ANOVA emissions ≈ Sobol ~27-29% (validates it's not a surrogate artifact);
    differences expected since ANOVA is unweighted + has no tipping wedge.
  - To resume cold: `ssh torch 'sacct -j 9811743,9811744 ...'`; if BRICK COMPLETED,
    the decomp CSV is already on Torch — pull + compare.

## ADDENDUM 2026-05-29 — CH4 de-noising (null result) + ANOVA draft

### CH4 de-noising — DONE but NULL RESULT (do not ship brick-averaging)
- CH4 pulse cube finished (Torch 9746801). Ran both BRICK arms on it: jobs
  **9788770** (paired, 2:25) + **9788771** (postaug, 11:19), COMPLETED. Outputs on
  Torch: `outputs/brick_v145_lhs10ks/brick_lhs10ks_pulse_ch4_pos_001tg{,_postaugment}.csv`.
- Ran `ch4_pulse_summary_brick_averaged.py` on Torch (big inputs live there);
  pulled `outputs/substack/ch4_pulse_slr_summary_lhs10ks_0p01tg_brickavg.csv`.
- **Finding:** brick-averaging does NOT de-noise the CH4 SLR panel. The panel
  plots median + 5–95% band (NOT mean). vs the old single-post summary:
  p50 yr-to-yr wiggle 0.86× (slightly worse), p95 1.17× (marginal), nowhere near
  the hoped √10. The **mean** is tipping-corrupted (−0.054→+0.096 cm/GtCO₂eq,
  sign-swinging) — the documented AIS-tipping-contaminates-the-mean issue — but
  the mean isn't plotted. Root cause: the CH4 0.01-Tg marginal median is at the
  numerical floor (p50≈0.0003 cm/GtCO₂eq) and the visible wiggle is
  quantization + FaIR-seed noise (a FaIR axis), neither reducible by averaging
  over BRICK posts. **Did NOT repoint pulse_responses_clean.py** (line 84 still
  the old summary). The brickavg CSV + BRICK arms are kept as artifacts.
- **Recommended alternative** (await Marcus): light display-smoothing of the CH4
  SLR band in `pulse_responses_clean.py` (same 11-yr trick as the H-S figs) —
  directly fixes the visible stair-stepping; OR median-over-posts (robust to
  tipping) instead of mean-over-posts; OR a larger CH4 pulse to lift off the floor.

### ANOVA balanced-factorial cross-check — DRAFTED + locally validated (not submitted)
- Design doc: `notes/design_2026-05-28_anova_factorial.md`. Key: crossed
  cfg×rff×post; FaIR only on cfg×rff×seed (post-independent) so 27k BRICK ≈ 9k
  FaIR ≈ <1 hr Torch.
- Scripts (all written): `python/scripts/build_anova_factorial_metadata.py`
  (validated: --n-rff 100 --n-cfg 30 --n-seed 3 --n-post 3 --tag 27k --stratify-rff
  → 9000 FaIR + 27000 BRICK rows, balanced, correct index conventions);
  `FaIRtoFrEDI/slurm_v5_anova_factorial.sh` (v5-faithful: flat2015 forcing +
  stochastic seeds); reuse `scripts/submit_brick_arm.sh` for BRICK;
  `python/scripts/substack/anova_hs_decomp.py` (model-free per-axis decomp →
  same schema as the Sobol figures).
- **5 OPEN CHOICES to confirm before the real run** (in the design doc):
  weighting (recommend unweighted), level allocation (recommend Option A 27k),
  seed handling (3 crossed), baseline-only vs +pulse (baseline-only first),
  rff stratification (by cum_co2_2100). Workflow to submit is in the design doc.

## TL;DR / where we stopped

Building the **production Group-Sobol** Hawkins-Sutton variance decomposition to
replace TreeSHAP (which under-attributed the SLR emissions axis ~5×). All code is
written and validated on quick (landmark-year) runs. The **full 131-year run was
killed when the laptop went to sleep** — it must be re-run on resume. Then render
figures + poster, and run the Torch-scoping analysis. [↑ all DONE — see STATUS]

Two things Marcus asked for (2026-05-28):
1. **Produce the normalized figure** (DONE in code; needs full run + render).
2. **Analyze how big a new Torch ensemble** would need to be for a better H-S
   plot (ANOVA / Shapley / Sobol). Script written, NOT yet run (task #7).

---

## Decisions locked this session

- **Scope:** all 4 targets (total/pulse × GMST/SLR) via Group-Sobol.
- **Surrogate:** unweighted HistGB (`max_iter=600, max_leaf_nodes=63, lr=0.03,
  min_samples_leaf=20, l2=0.5`) on the **p99-clipped** target, monotonic
  constraints on unambiguous cumulative-emissions feats. Unweighted fit chosen
  (higher OOF R², better generalization — confirms the shapley ESS rationale);
  Saltelli sampling + R² + V_total all Wong-weighted.
- **Framing:** NORMALIZED to the surrogate-explained variance. Wedges =
  first-order Sobol main effects (emissions/climate/brick) + a real
  interactions wedge (= aggregate ST − S₁) + model-free internal (seed for SLR,
  OOF residual for GMST) + AIS-tipping wedge (clip-vs-unclip V_total). The
  ~28% model-unresolved variance is DROPPED (not shown); caption notes R²≈0.71–0.81.

## Key empirical findings (durable — save to memory)

- **R²≈0.71 at 2150 for total SLR is IRREDUCIBLE.** Tested 6 model families
  (HGB best 0.711, MLP 0.692, RF 0.656, ExtraTrees 0.665, KNN 0.41) and two
  feature sets — none beats HGB; more HGB capacity (1500 trees) *overfit*. The
  ceiling is the cfg/post→SLR response surface under 10k cells, **NOT** emissions
  lossiness and NOT internal variability (~0.5%).
- **Richer emissions features did NOT help** (R² 0.708 vs 0.711). The 8 cumulative
  summaries already capture the emissions effect. (Built `rff_features_rich.csv`
  + `build_rff_features_rich.py` to test this; not used in production.)
- The gap is **mostly real**: first-order sum S₁≈0.77 but total-order sum ST≈0.99
  at 2150 → ~23% genuine group interactions (climate×BRICK, emissions×BRICK; SLR
  ≈ GMST-path × ice-sensitivity, multiplicative). sum(S₁)≤1 holds at every year.
- **Normalized headline numbers** (from the validated quick run):
  - Total SLR @2150: emissions **27%** (TreeSHAP was 8.6% — a 3.2× fix),
    climate 32%, brick 14% (model-free was 40%), interactions 21%, internal 0.6%,
    tipping 5%.
  - Pulse SLR @2150: emissions ~1% (per-tonne SLR is scenario-independent),
    climate 43%, brick 19%, tipping 20%, interactions 18%.
  - Total GMST @2150: R²≈0.97; internal 3%, climate ~38%, emissions ~53%,
    interactions ~5% (canonical H-S shape preserved; figure barely changes).
  - Pulse GMST: climate-dominated 89–99%.

---

## RESUME — exact next steps

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
source ~/climate-env/bin/activate
```

1. **Re-run full production Sobol** (parallel, ~6–10 min; writes canonical CSVs):
```bash
python python/scripts/substack/group_sobol_hs.py
```
   - Expect: 4 targets. SLR writes `v5_hybrid_decomp_{total,pulse}_{clip,unclip}.csv`
     (unclip has V_total only — wedges are 0 by design, the render only reads
     unc.V_total for tipping). GMST writes `shapley_hs_per_axis_{total,pulse}_gmst.csv`
     + re-renders `shapley_hs_{total,pulse}_gmst.{png,pdf}`.
   - **Sanity:** total SLR clip @2150 should print R²≈0.71, emi S≈0.29.

2. **Re-render SLR figures + poster** (task #5):
```bash
python python/scripts/substack/render_hybrid_tipping_split.py
python python/scripts/substack/paired_figures_hs.py
python python/scripts/poster/hawkins_sutton_panels.py
```
   - Verify total SLR emissions wedge ≈ 27% at 2150 (was 8.6% TreeSHAP).
   - paired_figures_hs.py reads the per-axis CSVs incl.
     `shapley_hs_per_axis_*_slr_hybrid_tipping.csv` (written by step-2 render).

3. **Run the Torch-scoping learning curve** (task #7):
```bash
python python/scripts/substack/hs_scoping_learning_curve.py
```
   - Fits HGB on N∈{500,1000,2000,4000,7000} subsets, fixed 2000-cell test, 3
     seeds; extrapolates R²(N)=R∞−C·N^−p to find N for R²=0.80/0.85/0.90.
     Answers: is the ceiling data-limited (bigger ensemble helps) or structural?
   - Then write the short scoping memo (recommended ensemble size + Torch cost,
     ANOVA vs Shapley vs Sobol data needs) → `notes/`.

4. **Update poster_text.txt** captions C/D to Group-Sobol wording (not yet done).

5. Consider committing (project is NOT a git repo yet — Marcus's call).

---

## Files created / modified this session

NEW:
- `python/scripts/substack/group_sobol_hs.py` — production module (4 targets,
  parallel joblib n_jobs=4, OMP_NUM_THREADS=2, normalized framing). **canonical**
- `python/scripts/build_rff_features_rich.py` + `outputs/rff_features_rich.csv`
  (diagnostic only — rich feats gave no R² lift; NOT used in production)
- `python/scripts/substack/hs_scoping_learning_curve.py` (task #7, not yet run)
- diagnostics (throwaway): `_sobol_surrogate_diag.py`, `_sobol_rich_test.py`,
  `_sobol_mlp_test.py`

MODIFIED (column rename V_BRICK_modelfree→V_brick, V_seed_modelfree→V_seed; and
captions/labels TreeSHAP→Group-Sobol):
- `python/scripts/substack/render_hybrid_tipping_split.py`
- `python/scripts/poster/hawkins_sutton_panels.py`

UNCHANGED reuse deps: `shapley_hawkins_sutton.py` (loaders, assemble_features,
GMST cube load), `hybrid_hs_slr_unified.py` (load_baseline/pulse_v5,
compute_v_seed_total, clip_per_year).

## Quarantine (done)

Pre-Sobol TreeSHAP outputs moved to
`outputs/quarantine/20260528_treeshap_slr_underattribution/` (43 files + README).
NOTE: the `v5_hybrid_decomp_total_{clip,unclip}` pair were already overwritten by
a quick-test before quarantine (3-row scratch); the pulse pair + figures are the
intact TreeSHAP-era files. **The current canonical `v5_hybrid_decomp_*.csv` and
`shapley_hs_per_axis_*gmst.csv` are STALE 3-row quick-run / partial killed-run
output — step 1 above overwrites them with the real 131-year production.**

## Non-obvious state / gotchas

- Module emits per-year `R2_oof`, `S_emi/clim/brick`, `ST_emi/clim/brick` into the
  SLR clip CSV (useful for the scoping/caption; render ignores extras).
- joblib loky auto-memmaps the 4.4 MB feature matrix (shared, read-only). Per-year
  rng seeds are deterministic (`SEED_BASE[target]+it`) → reproducible, order-free.
  Results differ from the serial version only within Monte-Carlo noise (N_SOBOL=8192).
- GMST internal = OOF residual (R²≈0.97 so ≈ true internal); SLR internal =
  model-free seed-augmentation. The "drop model-unresolved" asymmetry is fine
  because GMST R² is high (nothing to drop) while SLR R² is ~0.71.
- pulse_gmst Sobol S can exceed 1 at low-variance near-term years (MC noise on
  tiny variance); the normalization absorbs it (climate≈100%, interactions→0).
  Not a bug.
- Other Torch jobs still in flight (not ours): CH4 pulse cube 9746801 (for the
  separate CH4 de-noising workstream — blocked until that cube lands), vehicle
  9746765, multidecade 9710726.

## Still pending from the parent handoff (unchanged)

- CH4 pulse SLR de-noising (Torch cube 9746801 → BRICK arms → summary → re-render
  pulse_responses_clean CH4 panel). Independent of this Sobol work.
