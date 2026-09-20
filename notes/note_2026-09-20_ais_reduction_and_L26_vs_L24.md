# (1) Shrinking the Antarctic block / reducing its R̂ failures; (2) L26 vs L24 — pros and cons (2026-09-20)

Inputs: `python/diag_ais_block_pca.py` (PCs of the 17-parameter block in prior-sd units, per-PC R̂),
`julia/diag_ais_leverage.jl` + Spearman of each parameter with ssp245 AIS/total SLR at 2300 (2,000 draws),
`calibrate_mcmc_ext.jl --profile` on λ, T_crit, amp, γ, ν, f₀ (L26 config), and the four L26 chains.

## 1. Where the information is, parameter by parameter (L26)

| parameter | post sd / prior sd | Spearman with AIS@2300 | likelihood profile (Δ log-post at ±2 prior sd) | class |
|---|---|---|---|---|
| λ | 0.99 | **+0.55** | **0.00** (the AIS term does not move at all) | prior-propagated, projection lever |
| T_crit | 1.00 | **−0.44** | **0.00** | prior-propagated, projection lever |
| amp | 0.97 | **+0.51** | −1.5 / −5 (weak) | prior-propagated, projection lever |
| γ | 0.86 | −0.04 | ±0.1 | prior-only, no leverage |
| ν | 0.80 | −0.02 | −6 / −19 | weakly identified, no leverage |
| f₀ | 0.82 (marginal) | −0.02 | −590 at −0.5 sd (CONDITIONAL) | on the geometry ridge |
| T_on, ln P₀, slope | 0.36 / 0.12 / 0.49 | 0.05 / −0.01 / −0.03 | sharp | identified (Table A2), no leverage |
| κ, µ, b₀, c, α, a_ANTO, b_ANTO, T_oc,0 | 0.62–0.86 | ≤ 0.13 | — | partly identified, no leverage |

Reading: projection uncertainty in Antarctica beyond 2100 comes from THREE parameters (λ, T_crit, amp),
all three prior-propagated — and the historical record cannot inform them because the fast-dynamics
threshold is never crossed in the hindcast (λ and T_crit have an exactly flat likelihood). Everything the
record identifies (Table A2) has no projection leverage. The two sets are disjoint.

**Why R̂ fails.** The unmixed direction (PC1: f₀ +0.54, λ −0.41, T_crit +0.33, κ −0.30; R̂ 1.17; the
per-parameter failures on f₀ 1.28, slope 1.23, T_on 1.33, precip_u 1.11) keeps 88 % of its PRIOR variance.
It is not a curved ridge: f₀ regressed on (slope, ln P₀) has R² 0.52 raw, 0.56 in logs, 0.53 with quadratic
terms — linear, so a log/whitened reparameterisation would not straighten anything (the RAM already adapts
a full covariance). It is a WIDE, FLAT direction in a 7-parameter block under a joint prior, walked by a
random-walk proposal with an integrated autocorrelation of ~200k iterations; ESS 17–44 per parameter at
4 × 1M post-burn. Getting ESS > 400 that way needs ~10× the iterations. Projected SLR converges (R̂ 1.002)
because SLR does not depend on where the chain sits along that direction.

## 2. Options, priced

| option | k (from 55) | hindcast | projections | R̂ failures | verdict |
|---|---|---|---|---|---|
| **A. Cut λ and T_crit out of the MCMC; draw them from their paleo priors per projection draw** | 53 | unchanged (flat likelihood — EXACT) | unchanged in distribution | removes their share of the flat block; f₀/T_on/slope/precip remain | **do it**: it is what already happens, made explicit; "propagated, not estimated" becomes literal |
| B. Same for amp | 52 | ≤ 1.5 log-units of curvature discarded; posterior sd 0.97 → 1.00 × prior | 2300 AIS spread widens ~3 % | — | defensible; costs the one weak constraint the record has on amp. Judgement call |
| C. Fix γ at its paleo median | 52 (with A) | unchanged (flat, no leverage) | unchanged | — | do it |
| D. Drop the two glacier ledger terms (`gic_u_pre`, `gic_s_r5`) | 50 | the 1850–1900 datum then rests on the point terms alone (test needed) | none | — | probably; one chain to check |
| E. Fix or re-prior `gis_slow_w` | 49 | small | discharge spread narrows (unidentified but projection-relevant) | — | decision, not evidence |
| F. Fix f₀ (or one of f₀/slope/ln P₀) to kill the geometry ridge | 52 | the AIS hindcast loses one degree of freedom it uses (conditional profile is sharp) | none | removes most of the R̂ failures | NO: it fixes an identified combination's partner at an arbitrary point; the ridge is real |
| G. Longer chains / thinning | — | — | — | ESS ~10× per 10× iterations | 30 h per 10×; not the answer |
| H. A different sampler for the geometry block (e.g. ensemble/DE-MC, or HMC on the 7-dim block) | — | — | — | plausible | infrastructure; not for this paper |
| I. Sample the geometry block in posterior-PC or log coordinates | — | — | — | none expected (linear ridge; RAM already whitens) | no |

**Recommended package (A + C + D):** 55 → 50 sampled parameters, hindcast and projections unchanged to
the numbers the paper quotes, λ/T_crit/γ stated as prior-propagated in Table A1, the remaining R̂ failures
confined to the identified geometry ridge and stated with Table A2 (what the record identifies) and the
projected-SLR R̂ (what the deliverable rests on). Δk against BRICK 2.0 goes 20 → 15; the AIC/BIC margins
widen (AR(1) ρ ≤ 0.99: ΔAIC ≈ +93, ΔBIC ≈ +30 instead of −1, same ln L). One tuning chain (~1 h) to
confirm A + C + D leave the hindcast unchanged before a production run.

## 3. L26 vs L24 — pros and cons

**L26 pros**
- Priors are priors: the eight DAIS parameters on the DAISfastdyn paleo marginals (MimiBRICK's own
  construction); L24's were BRICK 2.0's posterior mean/sd at ±2 sd — data re-used, and truncations that
  clipped T_crit and κ. thermal_alpha on MimiBRICK's uniform range.
- The published target is what is scored: no early-segment ramp δ (a +1.5 cm correction of the 1900
  glacier target estimated from the same fit, 2.7 σ from zero, with no independent citation).
- The band error model matches what a reconstruction band is (level-like; L sampled on [5, 100] railed at
  100). Consequences: the Antarctic runoff onset is a posterior, +2.2 K [1.4, 3.2] (≈ the paleo prior),
  not a date (L24: +0.60 K [0.53, 0.76], crossed 1998 — a claim the pre-1992 reconstruction cannot carry);
  T_on's posterior width 0.4 → 1.8 °C; the T_on–amp ridge (r = +0.78) is gone (0.06).
- Fewer parameters: 55 vs 58 (δ, two glacier discrepancy coefficients), κ–P₀ ridge removed (r +0.96 → −0.02),
  T_off bound no longer clips (23 % of SLOWG's mass was below −3).
- Hindcast against the bare targets: glaciers 0.65 → 0.32 cm (1900–1919 1.43 → 0.67), total (out of
  sample) 0.87 → 0.42 — closer than BRICK 2.0 on EVERY row of Table 4 including the total (L24 lost the
  total, 1.17); parameter-band coverage of the total 0.30 → 0.81.
- AIC/BIC vs BRICK 2.0 unchanged in verdict with three fewer parameters (ρ ≤ 0.99: ΔAIC +83, ΔBIC −1;
  iid +2427/+2342); the Antarctic share of the gain (+6 → +1) is exactly the reconstruction-tracking given up.
- Same convergence status as L24 (18 vs 19 marginals fail; projected SLR R̂ 1.002 vs 1.008), so no new
  caveat.

**L26 cons**
- Antarctica and Greenland give back their near-exact tracking: AIS RMSE 0.03 → 0.09 cm, GIS 0.06 → 0.20
  (still 0.06× and 0.28× BRICK's); Greenland parameter-band coverage 0.60 → 0.34 (predictive 0.92), bias
  −0.14 cm; discharge timescale 168 → 270 yr (projection-relevant at 2300); three Table 4 windows now worse
  than BRICK (AIS 1993–2026 1.07, glaciers 1950–1992 1.82, TE 1993–2026 1.30 — the last was 1.52 in L24).
- The glacier fit's early-century device moved rather than vanished: `u_unch` 28 → 33–37 mm, the upper
  half of the Parkes & Marzeion range — a physical quantity, but it must be said.
- L = 100 yr is a convention the data pushed to a bound; the runoff-onset LOCATION follows it (1991 /
  2027 / 2049 / 2063 for L = 20 / 0 / 50 / 100) and the paper has to carry that sensitivity.
- The benchmark scores it WORSE than the L24 champion on the AIS and Greenland hindcast cells (6.2× and
  3.5× mean RMSE ratio) — because the benchmark measures tracking; every projection cell and the glacier
  and total hindcast cells are BETTER or SAME.
- Single-chain AIS medians differed between arms (α_DAIS 0.36–0.77), and the 4-chain block still does not
  mix; L26's AIS marginals are no better determined than L24's.
- Cost: everything downstream re-runs (projection arms ~1.5 h, IC test done, hindcast figure/Table 4,
  Table A1/A2 swap, the paper's Antarctic text), and the shipped memo (Ladrillo.9.14.26 / L24) becomes a
  provenance document.

**L24 pros** (mirror): the numbers already in the memo, the deliverable and the AIC paragraph; tighter
tracking of every component; the benchmark champion. **L24 cons:** priors that are BRICK's posterior; a
target correction estimated from the fit; an Antarctic onset in 1998 known to ±0.1 K from a modelled
series; a T_off bound clipping a quarter of a posterior; 58 parameters with a κ–P₀ ridge at r = 0.96.

**My recommendation:** promote L26, then run the A + C + D reduction as L27 for the paper if the tuning
chain confirms the hindcast is unchanged; report L24 in the paper only as the "tracking" comparison
(Table 4 note) if at all.
