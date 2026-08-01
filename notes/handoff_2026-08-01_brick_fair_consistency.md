# Handoff 2026-08-01 — BRICK-AM ↔ FaIR forward-propagation consistency (conditional Wong-weighting)

**Self-contained pickup:** read this + `CLAUDE.md` + memory `project_fair_brick_coupling_joint_calib`.

## TL;DR / state
Built and validated a **conditional Wong-weighting** method that makes BRICK-AM posterior draws consistent
with FaIR in **forward propagation** (never re-calibrates the forcing). Local validation passed. The full
**launch code** (Torch run → coupled SLR bands) is built, smoke-tested locally, and staged on Torch.
**HELD for Monday** (fairshare recovery). Monday = submit a 5-config smoke, then the full run.

## How we got here (the arc)
1. The **joint FaIR/BRICK forcing calibration** was built, run on Torch, and **REJECTED** — it let the SLR
   likelihood *re-infer* the forcing (bent GMST ~0.28 °C cool @2100 via fpc1, the ECS mode), and the
   te_α↔OHC coupling it recovered is **immaterial to the total-SLR bands**. Record:
   `notes/negresult_2026-08-01_joint_forcing_calibration.md`.
2. **Marcus principle (2026-08-01):** SLR must not influence atmospheric variables (forcing/ECS) — they're
   better constrained by data not in this likelihood. **Propagate forcing forward; don't re-calibrate it.**
3. This work: build the correct forward-propagation consistency method, **conditional on each FaIR config,
   with every FaIR parameter set kept equally likely** (forcing marginal untouched).

## The method
Per FaIR config *k*: `w_{i|k} ∝ exp[c·(ℓ^FB_{ik} − ℓ^B_i)]`, **normalized WITHIN each config** so
`p(config)=1/841` stays uniform (SLR never touches the forcing marginal — only the pairing / conditional).
- `ℓ^FB` / `ℓ^B` = historical total-SLR (Frederikse "dang" channel, each draw's own AR(1) `sd_dang`/`rho_dang`)
  under config-*k* vs the **mean** (calibration) forcing. The **ratio** cancels each draw's intrinsic fit →
  healthy ESS (Tony's insight; my crude step-1 used absolute ℓ and degenerated to ESS=1) and mitigates the
  Mengel double-count (Tony excluded the Mengel arm from global Wong-weighting for this reason).
- `c` tuned to a **gentle** mean conditional ESS/N (default 0.6): a consistency nudge, not a re-calibration.
- **Recovers the te_α↔OHC coupling in PROPAGATION**, forcing marginal fixed.

**Validated locally** (`weight_brick_conditional_fair.jl`, 60 cfg × 400 draws): mean-forcing recovery EXACT
(max|ℓ^FB−ℓ^B|=0, ESS/N=1.000); coupling signature corr(weight, te_α) vs config OHC@2018 = **−0.46**
(hottest configs −0.156, coldest +0.113 — hot ocean-heat down-weights high-te_α draws, TE∝te_α·OHC);
c=0.145, ESS/N=0.60 (≈ Tony's c≈0.2 for GMSL-only).

## Files (all committed; last commit 5d3741f)
| file | role |
|---|---|
| `julia/weight_brick_conditional_fair.jl` | weighting only (validated; historical) |
| `julia/weight_and_project_brick_fair.jl` | **THE launch driver** — weighting + projection to 2300 + COUPLED vs INDEPENDENT bands (one BRICK run per (config,draw) gives both ℓ^FB and future SLR) |
| `slurm/weight_and_project_brick_fair.sbatch` | single job, `cpu_short` 4h, `DRAWS`/`CONFIGS` env-overridable |
| `julia/calibrate_mcmc_ext.jl` | ★ CANONICAL BRICK-AM (mean forcing); now `PROGRAM_FILE`-guarded so the drivers `include` its FREE list + θ→BRICK apply + dang likelihood |
| `calibrate_mcmc_joint*.jl`, `project_slr_*.jl` | REJECTED joint experiment, banner-marked DIAGNOSTIC |

## Monday launch — exact steps
On Torch (VPN up; `ssh torch`; `cd /scratch/ms17839/SLR-RFF-BRICK`):
```
sshare -u ms17839 -A torch_pr_1041_general        # confirm FairShare recovered off 0.28
DRAWS=200 CONFIGS=5 sbatch slurm/weight_and_project_brick_fair.sbatch    # SMOKE first (~few min)
#   verify exit 0 + sane COUPLED/INDEP bands in logs/wpf_brick_<jid>.out
DRAWS=2000 CONFIGS=all sbatch slurm/weight_and_project_brick_fair.sbatch # FULL (~1.68M runs to 2300, ~1–2.5 h)
```
Outputs → `outputs/mcmc/wong_cond_slr_bands.csv` (COUPLED vs INDEPENDENT, total+comps @2050/2100/2150/2300)
+ `wong_cond_weights_full.csv`. Pull back, interpret coupled-vs-independent.

## Non-obvious state / gotchas
- **Torch has the full input set** (verified): both drivers, ext + all its inputs, extA108 subsample, and
  the **wide forcing** (transferred 2026-08-01 to `/scratch/ms17839/FaIRtoFrEDI/magicc_comparison/processed/curv_wide/`
  — the driver reads it via `REPO/../FaIRtoFrEDI/...`), pristine MimiBRICK depot.
- **ext parses `ARGS[1]` as N_ITER with no flag-guard** → must pass positional `2000 2026` *before* flags.
  The sbatch already does this; keep it if invoking by hand.
- **Fairshare 0.28** on 2026-08-01 (RawUsage 65k from the rejected joint run); ~7-day half-life.
- Rejected joint chains (~13 GB, `chain_jcont_*_n4000000.csv`) left on scratch as reproducible diagnostics.
- **Expected result:** coupling is immaterial to the *total* SLR (the shuffle test showed −0.55 cm @2100),
  so COUPLED ≈ INDEPENDENT on the total; the method should matter for the **steric/TE** component and for
  **pulse / SC-SLR** work — that's the real payoff to pursue next.

## Next after the bands land
- Interpret COUPLED vs INDEPENDENT. If small on the total (expected), the current independent pipeline is
  ~adequate for levels; document the coupling's (small) effect and move the method to where it bites.
- Apply the conditional weighting to **pulse / SC-SLR** (te_α↔OHC may matter more on the marginal).
