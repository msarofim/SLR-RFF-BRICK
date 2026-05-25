# Ensemble Design Tradeoffs — 3,000 RFF × 3-cfg-per-RFF (ECS-stratified)
## Pro/con analysis before launching new Torch runs

**Date:** 2026-05-20
**Trigger:** Tony Wong follow-up; handoff `FaIRtoFrEDI/notes/handoff_2026-05-20_tony_wong_followup.md` §2.1
**Scope:** Choose the FaIR-cube sampling design that becomes canonical for SLR-RFF-BRICK. Replaces the current 490-RFF × 841-cfg pool (LHS-10k subsample). Cube generation is 4-8 hours of Torch compute per scenario × 5-9 scenarios; locking the design wrong is expensive.

> **Read this before any `sbatch` for the new cube.** Decisions on this page propagate through every downstream SLR figure, H-S decomposition, pulse experiment, and (eventually) permafrost/Layer-A coupling.

---

## 1. What the new ensemble has to do

| Use case | What it needs from the design |
|---|---|
| Canonical SLR percentile bands (substack/poster/Tony reply) | Adequate posterior coverage of climate sensitivity; Wong-weighting machinery intact |
| Hawkins–Sutton variance decomposition (Panel C) | Identifiable variance partition between "scenario" (RFF), "model" (cfg), "internal" (BRICK posterior + stochastic FaIR) |
| ± pulse experiments at 2030 (CO₂/CH₄, ±1 + ±0.01) | Cell-paired baseline & pulse at the same (RFF, cfg, seed); sign-flip diagnostic + AIS-asymmetry detection |
| Permafrost / Layer-A coupling (future) | Forcing-perturbation post-processing per cell — needs per-cell forcing trajectories retained |
| SCC / SC-GHG-style economic uncertainty (future) | Wide RFF coverage so socioeconomic emissions tails are sampled |

These pull in different directions. There is no single design that maximizes all.

---

## 2. Current baseline (LHS-10k)

- **Pool available:** 490 RFFs × 841 cfgs = 412,090 (RFF, cfg) pairs, full factorial.
- **Cells used (canonical):** 10,000 (RFF, cfg, BRICK-post) tuples via LHS over (RFF-id, cfg-id, BRICK-post-id).
- **Weights:** Wong importance weights conditional on cfg (see memory `project_lhs10k_brick_coupling.md`).
- **FaIR cost:** 490 × 841 = 412k FaIR runs *per scenario*. Most are unused after the LHS draw, but they are precomputed and stored on Torch.
- **BRICK cost:** 10k runs per scenario × N scenarios.
- **Where it's strong:** good marginal coverage of (RFF, cfg, posterior); LHS keeps the joint design unbiased.
- **Where it's weak:** the 412k-cell FaIR pool is mostly wasted, only ~2.4% of it gets used; physical-uncertainty contrast within a given RFF is unidentified (each cell has 1 cfg).

---

## 3. Proposed design: 3,000 RFFs × 3 cfgs ECS-stratified (D)

- **Pool:** 3,000 RFFs (fresh-sampled from the 10,000-member RFF-SP pool) × 3 cfgs/RFF, one cfg drawn from each tercile of the 841-cfg posterior's ECS distribution.
- **Cells:** 9,000 (RFF, cfg) with 1 BRICK posterior draw per cell.
- **FaIR cost:** 3,000 × 3 = 9,000 FaIR runs per scenario. **~46× cheaper than current FaIR pool**; only what we need.
- **BRICK cost:** 9,000 per scenario, comparable to LHS-10k.
- **Strength:** every RFF has 3 cfgs spanning the ECS distribution — within-RFF physical contrast is identifiable.
- **Weakness:** 3 cfgs per RFF is enough for a low/mid/high contrast but **not enough to estimate within-RFF variance** (only 2 degrees of freedom).

---

## 4. Alternatives considered

| ID | Design | Cells | FaIR runs/scen | Within-RFF physical resolution | RFF coverage | Notes |
|----|--------|-------|----------------|-------------------------------|--------------|-------|
| A | 1,000 RFFs × 10 cfgs (ECS-decile) | 10,000 | 10,000 | High (10 ECS bins) | Modest | Best for within-RFF physical-uncertainty estimation |
| B | 5,000 RFFs × 2 cfgs (ECS-median split) | 10,000 | 10,000 | Low (binary lo/hi) | Strong | Best for tail emissions coverage; binary cfg loses curvature |
| C | 10,000 RFFs × 1 cfg (LHS-matched) | 10,000 | 10,000 | None (per-cell) | Strongest | Equivalent in spirit to current LHS-10k; loses paired pulse coverage of physical uncertainty |
| **D** | **3,000 RFFs × 3 cfgs (ECS-tercile)** | **9,000** | **9,000** | **Modest (3 bins)** | **Good** | **Proposed.** Roughly balanced. |
| E | 3,000 RFFs × 5 cfgs (ECS-quintile) | 15,000 | 15,000 | Strong (5 bins) | Good | ~67% more compute than D for better ECS resolution |
| F | Status quo (LHS-10k, 490×841 pool) | 10,000 | 412,000 | None | Modest (490) | Existing baseline; FaIR pool is mostly wasted |

---

## 5. Axis-by-axis tradeoffs

### 5.1 RFF sample size (N_RFF)

- **Bigger N_RFF buys:** better coverage of socioeconomic tails (extreme-emissions RFF draws), tighter SCC distributions, more credible RFF-driven scenario uncertainty in H-S.
- **For SLR specifically:** ~most SLR variance is climate-physics-driven, not RFF-driven, by 2100; by 2300 RFF matters more. N_RFF = 1,000-3,000 is plenty for 2100; N_RFF = 5,000+ matters for 2300 tails.
- **Practical floor:** 1,000 is roughly the threshold where bootstrap CIs on RFF-quantile estimates become tight enough for percentile-band reporting.
- **Bayes factor against status quo:** going from 490 → 3,000 quintuples RFF coverage at no FaIR-runtime cost over what the LHS-10k actually uses.

### 5.2 Cfgs per RFF (N_cfg/RFF)

- **N_cfg/RFF = 1** (status quo): each (RFF, cfg) cell pairs one cfg with one RFF. Within-RFF physical uncertainty is unobserved at the cell level; recovered only by pooling across cells.
- **N_cfg/RFF = 3** (proposed): allows lo/mid/hi ECS contrast within each RFF. Pulse experiments become cleaner: ΔSLR(RFF_i, cfg_low) vs ΔSLR(RFF_i, cfg_high) is a meaningful sensitivity.
- **N_cfg/RFF = 5-10:** within-RFF *variance* of physical response becomes estimable. Worth ~2× compute if a future paper-level H-S figure is the goal.
- **N_cfg/RFF = 841** (FaIR pool size): full posterior per RFF. Unnecessary given Wong weights already define an effective posterior over cfgs.

### 5.3 Stratification variable

| Variable | Captures | Tradeoff |
|---|---|---|
| **ECS** | Long-term equilibrium temperature & SLR response | Dominant for 2200-2300 SLR. Proposed. |
| TCR | Near-term (2030-2080) temperature response | Better for pulse-temperature work; weaker for long-term SLR |
| TCRE | Cumulative emissions → temperature | Strong for SCC. Less direct for SLR. |
| Effective forcing | Forcing efficacy | Smaller across-posterior spread; less leverage |
| Composite (PCA) | Joint variation across cfgs | More information per stratum but harder to communicate |

ECS is the right call for the SLR-centric headline use case. If we eventually want a TCR-stratified or TCRE-stratified companion ensemble, the 3-cfg-per-RFF design is reusable — just change the tercile variable.

### 5.4 BRICK posterior sample size

- **1 per cell** (proposed): 9,000 BRICK draws total, stratified across the 10,000-member posterior. ~90% posterior coverage.
- **3 per cell:** 27,000 BRICK runs total. Identifies *posterior* uncertainty within each (RFF, cfg). Useful for H-S "internal variability" component.
- **10 per cell:** posterior-distribution shape per cell. Probably overkill for headline figures, useful for a paper-level analysis.

For the canonical headline ensemble, 1 per cell is right. For the pulse experiment, **pair the same BRICK draw across baseline + pulse cubes** — otherwise paired-difference variance is dominated by BRICK-posterior noise, not by the pulse signal.

---

## 6. Compute cost summary

Per-scenario costs on Torch (rough, using existing pipeline benchmarks):

| Design | FaIR runs | FaIR time @ ~5k runs/hr | BRICK runs | BRICK time @ ~50k/hr | Total per scenario |
|---|---|---|---|---|---|
| A (1,000×10) | 10,000 | 2 hr | 10,000 | 0.2 hr | 2.2 hr |
| B (5,000×2)  | 10,000 | 2 hr | 10,000 | 0.2 hr | 2.2 hr |
| C (10,000×1) | 10,000 | 2 hr | 10,000 | 0.2 hr | 2.2 hr |
| **D (3,000×3 proposed)** | **9,000** | **1.8 hr** | **9,000** | **0.2 hr** | **2.0 hr** |
| E (3,000×5) | 15,000 | 3 hr | 15,000 | 0.3 hr | 3.3 hr |
| F (status quo, 490×841 pool) | 412,000 | 82 hr | 10,000 | 0.2 hr | 82 hr (mostly wasted) |

**Pulse-experiment compute (9 scenarios: baseline + ±1 GtC + ±1 Tg + ±0.01 GtC + ±0.01 Tg):**

- Design D: 9 × 2 hr = **18 hr Torch**, total cells 81,000.
- Design A: 9 × 2.2 hr = 20 hr Torch.
- Design E: 9 × 3.3 hr = 30 hr Torch.

All are tractable on Torch within a day. The Torch cost is *not* the binding constraint; the binding constraint is the LHS-design choice itself.

---

## 7. H-S decomposition power

For the Hawkins-Sutton variance attribution figure (Panel C in the substack/poster), the design must separate:

1. **Scenario uncertainty (RFF):** within-cfg variance across RFFs. Needs N_RFF ≥ ~1,000 for stable estimation.
2. **Model uncertainty (cfg):** within-RFF variance across cfgs. Needs N_cfg ≥ ~3 per RFF for a difference; ≥ ~10 for a distribution.
3. **Internal variability:** within-(RFF, cfg) variance across BRICK posterior + stochastic FaIR. Needs N_post ≥ ~30 per cell to be tight.

| Design | (1) RFF power | (2) cfg power | (3) internal power |
|---|---|---|---|
| A (1,000×10) | OK | Strong | Weak (1 per cell) |
| B (5,000×2)  | Strong | Weak | Weak |
| C (10,000×1) | Strongest | None at cell level | Weak |
| **D (3,000×3)** | **Strong** | **OK** | **Weak** |
| E (3,000×5) | Strong | Strong | Weak |
| F (status quo) | OK | Pooled-only | Weak |

For **internal variability** estimation we'd need N_post > 1 per cell, which is a separate decision. Current LHS-10k handles this by pooling across cells; the proposed design can do the same.

**Bottom line for H-S:** D is competitive with A and E. C loses cfg power at the cell level. B loses cfg curvature.

---

## 8. Recommendation framework (not a recommendation)

If the next 6 months emphasize:

- **SLR percentile bands + pulse experiments for substack/poster/Tony reply** → **D** is the right balance. Proposed.
- **A formal H-S decomposition paper with cfg-resolved physical uncertainty** → **E** (3,000 × 5).
- **SCC-style economic damage distributions** → **B** or **C** (more RFF coverage).
- **Permafrost/Layer-A coupling that demands per-cell forcing retention** → **D** or **E** with extended forcing diagnostics saved at run-time.

The handoff specifies the goals as (1)-(3)-ish (SLR-centric, pulse-friendly, H-S-supporting). **D** is consistent with that.

---

## 9. Open questions Marcus should resolve before launch

- [ ] **Confirm D vs E** (3 cfgs vs 5 cfgs per RFF). Costs 67% more for E but identifies cfg variance, not just contrast. If a future paper-level H-S figure is on the roadmap, E may be worth it now (avoids re-running later).
- [ ] **Confirm stratification on ECS** (not TCR/TCRE/composite). Defaults to ECS; flag if any planned figure puts TCR-stratification on the critical path.
- [ ] **Confirm 1 BRICK posterior per cell** for headline; consider 3-per-cell for a publication-grade variant later.
- [ ] **Confirm same-seed BRICK pairing** across baseline+pulse cubes for sign-flip and pulse-marginal correctness.
- [ ] **Confirm the LHS-10k stays callable for direct comparison** during the transition window — proposed-D outputs go to `outputs/rff3000_*` namespace, LHS-10k outputs stay at canonical `outputs/lhs10k_*` paths.
- [ ] **Confirm sampling seed for fresh RFF draw** (default seed=2026 stratified-uniform over 1..10,000).

---

## 10. If you sign off on D as proposed

Then the launch checklist is:

1. Modify `python/lhs_climate_pilot.py` to (a) sample 3,000 fresh RFFs with `np.random.default_rng(2026)` stratified-uniform draw, (b) within each RFF, pick 3 cfgs by ECS tercile from the 841-cfg posterior. ECS values are in the FaIR-calibrate v1.4.1 posterior data — verify before coding.
2. Generate **9 FaIR cubes**: baseline, +1 GtC, −1 GtC, +1 Tg, −1 Tg, +0.01 GtC, −0.01 GtC, +0.01 Tg, −0.01 Tg. Same RFF/cfg seed list across all 9. Save as `outputs/rff3000_<scenario>_stoch_to2300.npz`.
3. Build LHS metadata for 9,000 (RFF, cfg, BRICK-post) triples.
4. Run BRICK on each cube; paired BRICK posterior draws across cubes.
5. Apply Wong weights (existing machinery; no recalibration this round).
6. Sanity-test all 5 (zero-perturbation, sign-flip, magnitude-doubling, bit-identical reproducibility, first-principles magnitude) per `feedback_apply_sanity_tests_for_pulses.md`.
7. Re-run H-S decomposition; compare to LHS-10k baseline.

Estimated total Torch wall-time: ~20-25 hours sequential, or ~3-4 hours with parallel scenario runs. RAM-friendly for 16-cell Torch nodes.
