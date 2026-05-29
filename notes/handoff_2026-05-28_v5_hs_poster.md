# Handoff — v5 H-S figures, Sobol attribution, poster v5 update (2026-05-28)

**Owner:** Marcus C. Sarofim
**Context:** Long session continued from the v5 noise-isolated H-S work. This
note is self-contained for a cold start; read it + `CLAUDE.md` +
`memory/project_v5_hs_landed.md`.

---

## TL;DR of where things stand

1. **GMST H-S figures**: DONE and correct (v5, canonical shape). Not in question.
2. **SLR H-S figures**: METHODOLOGY IN FLUX. The published v5 hybrid figure
   (`shapley_hs_total_slr_hybrid_tipping.png`) **under-attributes emissions
   by ~5×** because TreeSHAP fails on correlated RFF/cfg features. The fix is
   **Group-Sobol** (prototype validated). Decision made: invest in a better
   surrogate and switch the SLR H-S framework to Group-Sobol. NOT YET BUILT
   to production.
3. **Poster**: Panels C, D (H-S) updated to v5 hybrid+tipping; F, H, I updated
   to v5 LHS-10k_s FrEDI. Panel J not updated (no script — Marcus's own figure).
   **Caveat**: C/D still use the TreeSHAP hybrid, which the Sobol work shows is
   wrong on emissions. They should be re-rendered once Sobol is production.
4. **CH4 pulse SLR de-noising**: v5 CH4 FaIR cube rerunning on Torch (job
   **9746801**, `cs` partition, 8 hr). First attempt (job 9727928, cpu_short
   4 hr) TIMED OUT — this node ran 2.4× slower than baseline. Downstream BRICK
   + summary still TODO.

---

## DO NOT treat ANOVA-18k as ground truth

Marcus's explicit caution (2026-05-28): we moved away from ANOVA-18k for a
reason — it explores only **15 cfgs × 400 RFFs** (vs v5's 841 × 10,000). When
I compared Group-Sobol to ANOVA-18k "main effects", ANOVA is a *limited-
sampling reference*, not truth. Group-Sobol on the **full v5 ensemble** with a
good surrogate is the preferred answer precisely because it explores the full
parameter space. Use ANOVA-18k only as a rough cross-check, and expect real
differences (especially for V_cfg, where 15 cfgs is very sparse).

---

## The SLR H-S attribution saga (why Sobol)

Timeline of methods tried for total_slr variance decomposition:

| method | emi @2150 | cfg @2150 | brick @2150 | problem |
|---|---|---|---|---|
| TreeSHAP (cfg+RFF surrogate) | 8.6% | 12% | — | under-attributes correlated features 5× |
| model-free within-cell V_BRICK | — | — | 40% | conflates main_post + post×cfg interactions (5× over) |
| ANOVA-18k main effects | 43% | 35% | 7% | limited 15-cfg/400-RFF sampling |
| **Group-Sobol on v5 surrogate** | **41.7%** | **31.4%** | 16.7% | surrogate modeling gap (R²≈0.71); sum S₁=1.04 at 2050 |

Group-Sobol reproduces the emissions story on v5's full coverage. Root cause of
all the trouble: RFF emissions features (`cum_co2_2030/2100/2300`) are highly
collinear; TreeSHAP splits their joint contribution arbitrarily so the summed
per-feature SHAP variance ≪ the true axis contribution. Same for correlated cfg
ocean-heat params.

### Prototype that validated Sobol
`python/scripts/substack/group_sobol_prototype.py` — fits one HistGB on v5
(RFF+cfg+post), then Saltelli pick-and-freeze (empirical cell-based sampling so
within-group correlations are preserved) for grouped first-order (S₁) and
total-order (ST) Sobol indices. Output: `outputs/substack/sobol_proto_total_slr.csv`.
Landmark results in the table above.

### Production Sobol — NEXT STEP (Marcus chose this path)
Build the full Group-Sobol H-S for all 4 targets (total/pulse × GMST/SLR),
131 years, replacing TreeSHAP everywhere. Requirements:
1. **Better surrogate** (the weak link). Current HistGB OOF R² for SLR is only
   0.71 at 2150 → injects noise (sum of S₁ exceeded 1.0 at 2050). Options:
   more boosting iterations, monotonic constraints on cumulative-emissions
   features, or a small MLP. Target: OOF R² > 0.9 so sum(S₁) ≤ 1 at all years.
2. Validate sum(S₁) ≤ 1 and ST ≥ S₁ at every year before rendering.
3. V_internal (seed) stays model-free from seed augmentation (~0.7% at 2150);
   it is NOT in the surrogate. Add as a separate wedge.
4. Keep the AIS-tipping wedge (p99-clip difference) — that part of the current
   hybrid is fine.
5. Re-render: substack total/pulse SLR + poster panels C, D + the paired SLR
   figure once Sobol is production.

---

## What's DONE this session

### v5 H-S (TreeSHAP hybrid) — shipped but SLR superseded-pending-Sobol
- `outputs/substack/shapley_hs_total_gmst.png` (internal-bottom stack) — CORRECT
- `outputs/substack/shapley_hs_pulse_gmst.png` (climate-bottom) — CORRECT
- `outputs/substack/shapley_hs_total_slr_hybrid_tipping.{png,pdf}` — emi under-attributed, redo with Sobol
- `outputs/substack/shapley_hs_pulse_slr_hybrid_tipping.{png,pdf}` — same caveat
- Per-axis CSVs: `shapley_hs_per_axis_*.csv`

### Paired figures (top=projection band, bottom=H-S)
`python/scripts/substack/paired_figures_hs.py` →
`outputs/substack/paired_{gmst,slr,pulse}.{png,pdf}`. The SLR + pulse-SLR bottom
panels inherit the TreeSHAP-hybrid attribution → re-render after Sobol.

### Poster (AGU Chapman) — `outputs/poster/iec_graphics_handoff/`
- C_total_slr_hawkins_sutton.pdf, D_pulse_slr.pdf — v5 hybrid+tipping (redo after Sobol)
- F_damage_function_methodology.pdf — v5 LHS-10k_s FrEDI ✓
- H_coastal_property_and_htf_damages.pdf — v5 LHS-10k_s FrEDI ✓
- I_state_damages_map.pdf — v5 LHS-10k_s FrEDI ✓ (per-capita ranking LA≫FL>MA>VA>NJ confirmed; caption unchanged)
- J_htf_elder_mortality.pdf — NOT updated (no script in repo; Marcus's own figure)
- Captions in `poster_text.txt` updated for C, D, F, H to v5 wording.

### FrEDI v5 LHS-10k_s rerun — DONE
- Inputs: `python/scripts/build_fredi_inputs_v145.py` now CLI-parameterized
  (`--cube --brick-slim --out-gmst --out-slr`). Built
  `outputs/fredi_input_rff_baseline_{gmst,slr}_v145_lhs10ks.csv` (1000 SIR draws, ESS 8192).
- R driver `R/run_fredi_slr_phaseC_baseline_v145.R` now env-var parameterized
  (`FREDI_TAG`, `FREDI_GMST_CSV`, etc.). Ran with `FREDI_TAG=v145_lhs10ks`
  (72.9 min). Outputs:
  `outputs/fredi_slr_phaseC_rff_baseline_v145_lhs10ks_{long,state_long}.csv`.
- Aggregated: `aggregate_fredi_slr_v145.py` (FREDI_TAG env) →
  `..._v145_lhs10ks_quantiles.csv`.
- Headline v5 coastal damages (annual, weighted, USD B):
  CP 2100 P50 $34.9B / 2150 $72.5B; HTF 2100 P50 $183B / 2150 $337B.
- Downstream poster scripts now FREDI_TAG-aware: `poster/htf_transport_table.py`,
  `plot_state_damages_2100.py` (copied from archive), `poster/sweet_scenarios.py`.

### FrEDI panels confirmed BRICK-SLR-driven (not FrEDI internal SLR)
`import_inputs(tempfile=..., slrfile=...)` — both GMST and SLR come from the
external FaIR→BRICK pipeline; FrEDI's internal Kopp SLR scenario is bypassed.

---

## CH4 pulse SLR de-noising — IN FLIGHT

**Goal**: reduce noise in the CH4 1-GtCO₂eq pulse-marginal SLR subplot by
averaging each cell's marginal over 10 BRICK posterior draws (√10 ≈ 3.2× SE
reduction). Chosen approach (option 1a): build a v5 CH4 pulse cube + BRICK
augmentation.

**Status**:
- FaIR v5 CH4 pulse cube: **job 9746801** (resubmitted on `cs`, 8 hr, 8 cores,
  PYTHONUNBUFFERED). First try (9727928, cpu_short 4 hr) TIMED OUT — node was
  2.4× slower than baseline. Driver does NOT resume from partial checkpoint, so
  this is a fresh run.
  Output: `cube_v145_lhs10ks_pulse_ch4_pos_001tg_flat2015.npz`.
- Next (auto-submit was wired in the now-dead monitor — must re-do manually):
  after cube lands, run BRICK twice on it:
  - paired (metadata `outputs/lhs10ks_brick_metadata.csv`) →
    `brick_lhs10ks_pulse_ch4_pos_001tg.csv`
  - postaug (metadata `outputs/lhs10ks_brick_postaugment_metadata.csv`) →
    `brick_lhs10ks_pulse_ch4_pos_001tg_postaugment.csv`
  via `scripts/submit_brick_arm.sh` with SAVE_COMP=false.
- Then run the (already-written) summary:
  `python/scripts/substack/ch4_pulse_summary_brick_averaged.py` →
  `ch4_pulse_slr_summary_lhs10ks_0p01tg_brickavg.csv`. It prints the
  noise-reduction ratio vs the existing single-post summary.
- Then re-render the CH4 panel in `pulse_responses_clean.py` (point its CH4 SLR
  CSV at the new brickavg summary).

**Watch**: `cs` partition has no time cap but the node speed varies; if it times
out again, check whether `f.ch4_method="Thornhill2021"` is the slow path or the
node was contended.

---

## Re-arm the Torch monitor (cold start)

```bash
ssh ms17839@login.torch.hpc.nyu.edu 'squeue -u ms17839 -o "%i %j %T %M %l"; ls -la /scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10ks_pulse_ch4_pos_001tg_flat2015.npz 2>&1'
```

When the cube exists, submit the two BRICK arms (see CH4 section), pull them,
run the summary, re-render.

---

## Other in-flight Torch jobs (not ours to manage, just noise)
- 9710726 fredi_unc_multi_v145 (Peter Howard multidecade SC-CO₂ mortality)
- 9746765 / vehicle_fredi_v145 (vehicle rule FrEDI)

## Key scripts touched this session
```
python/scripts/substack/group_sobol_prototype.py        (NEW — Sobol prototype)
python/scripts/substack/hybrid_hs_slr_unified.py        (total/pulse × clip)
python/scripts/substack/render_hybrid_tipping_split.py
python/scripts/substack/paired_figures_hs.py            (NEW — 3 paired figs)
python/scripts/substack/ch4_pulse_summary_brick_averaged.py (NEW — awaiting data)
python/scripts/poster/hawkins_sutton_panels.py          (NEW — poster C/D)
python/scripts/build_fredi_inputs_v145.py               (CLI-parameterized)
python/scripts/aggregate_fredi_slr_v145.py              (FREDI_TAG env)
python/scripts/plot_state_damages_2100.py               (copied from archive, FREDI_TAG)
python/scripts/poster/htf_transport_table.py            (FREDI_TAG env)
python/scripts/poster/sweet_scenarios.py                (FREDI_TAG env)
R/run_fredi_slr_phaseC_baseline_v145.R                  (env-var parameterized)
```
