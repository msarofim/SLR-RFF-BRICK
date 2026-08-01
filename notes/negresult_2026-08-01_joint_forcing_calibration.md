# Negative result: joint FaIR/BRICK forcing calibration — BUILT, TESTED, REJECTED

**Date:** 2026-08-01 · **Verdict:** the joint free-forcing calibration is **rejected for production**.
**Canonical BRICK-AM = the mean-forcing calibration (`julia/calibrate_mcmc_ext.jl`, posterior
`data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv`), with FaIR forcing uncertainty
PROPAGATED FORWARD (existing LHS-10k pairing), not re-calibrated.** The joint drivers are retained
as the diagnostic that earned this conclusion — do not run them as production.

---

## The question (Marcus, 2026-07-24)

BRICK-AM is calibrated on the FaIR **mean** forcing; FaIR forcing uncertainty is added downstream by
pairing BRICK draws with FaIR members independently. That factorization drops the θ_BRICK↔forcing
coupling — physically `TE ∝ te_α·OHC`, so `te_α` should anti-correlate with the driving OHC member.
Does a **joint** calibration (sample θ_BRICK + the forcing jointly, recovering the coupling) beat the
mean-forcing shortcut, and by how much?

## What was built

- `julia/diag_coupling_reweight.jl` — step-1 importance-reweight proxy. Coupling real (coarse ESS 40%,
  corr(hist-fit, OHC@2018) −0.58) but post-hoc reweighting degenerate (fine ESS 1/841).
- `julia/calibrate_mcmc_joint.jl` — discrete-index joint (z over the 841-member ensemble). Recovery
  bit-identical to ext, but the single-site MH z-step mixed poorly (θ↔z coupling) → abandoned.
- `julia/calibrate_mcmc_joint_cont.jl` — **continuous** reparam: the forcing = K=3 PCA scores over the
  ensemble (`outputs/forcing_pca_basis.csv`, builder `python/precompute_forcing_pca.py`), sampled
  jointly with the 39 BRICK params in one RAM. `--recover` (scores excluded) is bit-identical to ext.
- Torch production (array 15090052): 4 overdispersed chains × 4M iters, acceptance 0.237.
- `julia/project_slr_joint_cont.jl` (deliverable R̂) and `julia/project_slr_coupling_test.jl`
  (COUPLED vs DECOUPLED-shuffle vs EXT_MEAN).

## What was found — three results

1. **The coupling is real and converged.** Pooled `corr(te_α, fpc2)=−0.52, corr(te_α, fpc3)=−0.61`;
   te_α R̂ 1.004, forcing-score R̂ 1.004–1.008. Total-SLR **deliverable converged**: R̂ 1.0006/1.0010/1.0019
   at 2100/2150/2300 (beats the ext benchmark 1.003/1.002).

2. **The coupling is IMMATERIAL to the total SLR bands.** Permutation test (COUPLED − DECOUPLED, fpc
   shuffled across draws → identical BRICK + forcing marginals, only the dependence broken): it tightens
   the *directly-coupled* TE component ~29 % (te@2100 width 9.59→6.77 cm) but on the **total** @2100 that
   is only **−1.4 cm width (−2.3 %) / −0.55 cm median** — the AIS tipping tail (total width ~58 cm) swamps
   it. So the mean-forcing shortcut loses almost nothing on the reported bands.

3. **Freeing the forcing is HARMFUL — SLR re-infers the forcing.** COUPLED vs EXT_MEAN median gap was
   large (−7.7/−45/−122 cm @2100/2150/2300) but it is **not** the coupling and **not** the parameters
   (joint vs extA108 param medians near-identical: amp 1.070 vs 1.069, AIS within a few %; only te_α
   0.1375 vs 0.1494). It is the **forcing**: the joint posterior's fpc1 (the ±0.68 °C ECS/atmosphere mode,
   74.5 % of forcing variance) drifted to median **+11.6 → future GMST −0.28 °C @2100 (→ −0.48 @2300)**
   vs the FaIR ensemble mean, amplified by AIS tipping. fpc1 is weakly identified by SLR (post sd 19,
   prior 26; spans 0) — the free forcing bent cool to absorb BRICK's historical SLR over-prediction. The
   joint's lower, "AR6-consistent" 39 cm @2100 is **low for the wrong reason.**

## The principle (Marcus, 2026-08-01)

**SLR fitting must not influence atmospheric variables (forcing, ECS/GMST)** — they are far better
constrained by data (GMST/OHC/energy budget) that this BRICK likelihood does not include. The correct
operation is to **PROPAGATE FaIR's forcing uncertainty FORWARD** (a fixed prior, carried into the
projections), **not to RE-CALIBRATE the forcing against SLR**. The joint calibration conflated the two.

- **Partial-freeze does not cleanly isolate ocean heat:** the PCA modes are entangled — fpc2 still
  carries ±0.37 °C GMST; only fpc3 is ~pure OHC (±0.01 °C GMST). A true OHC-only freedom would need
  freezing GMST=mean and freeing only the OHC residual orthogonal to GMST.
- **Even OHC-only is rejected:** (i) DOUBLE-COUNT — FaIR calib1.4.5 is AR6-constrained (OHC/energy
  budget) and BRICK's te_α/steric was itself calibrated vs OHC-derived steric (Wong vs Church-White,
  SNEASY OHC), so SLR would dip twice from OHC data; (ii) te_α↔OHC DEGENERACY — from TE alone you cannot
  separate te_α from OHC, so BRICK's steric cannot independently pin OHC → the freedom is low-value AND
  double-county.

## Decision

- **Canonical BRICK-AM = `calibrate_mcmc_ext.jl` (mean forcing), posterior `..._extA108.csv`.** Forcing
  is a FIXED prior; propagate its uncertainty forward with the existing LHS-10k FaIR pairing.
- The joint drivers + forcing PCA basis are **retained as this documented diagnostic**, banner-marked
  "DIAGNOSTIC / REJECTED FOR PRODUCTION" so they are not re-run as production.
- Torch: the 4 raw joint chains (`outputs/mcmc/chain_jcont_*_n4000000.csv`, ~13 GB) are diagnostic
  outputs, reproducible from the committed driver + basis; the small extracted results are committed
  (`rhat_jcont_summary.csv`, `slr_projection_rhat_jcont.csv`, `slr_coupling_test.csv`,
  `jcont_thinned_draws.csv`).

## Open (separate, safe) sub-question

Whether the **forward propagation** should pair each BRICK draw with a random FaIR member (independent)
or with an OHC-consistent member (honoring te_α↔OHC in *propagation*, never in calibration). Smaller,
safe lever — it never lets SLR touch the forcing. Distinct from this decision.

**Memory:** `project_fair_brick_coupling_joint_calib` (full numbers + provenance).
