# Calibration review, 2026-09-19 — droppable parameters, joint Antarctic parameters, mis-specified priors, further tests, the T_on precision, the SLOWG offset test

Inputs: `outputs/ladrillo_prior_posterior_L24.csv`, the L24 subsample (10,000 draws), the four L24 chains,
`calibrate_mcmc_ext.jl --profile` (new, conditional slices through the posterior median),
`outputs/param_priors.csv`, and two 500k-iteration test chains launched today (`L24TOFF4`, `L24DELTA0`).
"Width ratio" = posterior 5–95 % width ÷ prior 5–95 % width (truncated-normal priors evaluated numerically).

## 1. The prior that is mis-specified, and we had not said so: nine "BRICK" priors are BRICK 2.0's POSTERIOR

`outputs/param_priors.csv` — the source of the priors for `thermal_alpha`, `antarctic_alpha`, `antarctic_nu`,
`antarctic_temp_threshold`, `anto_alpha`, `anto_beta`, `antarctic_lambda`, `antarctic_gamma`, `antarctic_kappa`
— is the mean and sd of BRICK 2.0's own posterior subsample (`parameters_subsample_brick.csv`), matched to
four decimals on every row, with hard bounds at mean ± 2 sd. Wong et al. (2017) sampled these under UNIFORM
priors over physical ranges (their Tables A2/A4). So Ladrillo's "prior" on these nine is an informative
Gaussian carrying the information of BRICK's calibration data — IMBIE 1992–2017, the CSIRO total, the Gouretski
ocean heat, the GIS series — which overlaps the targets Ladrillo scores. Consequences visible in Table A1:

- `antarctic_temp_threshold`, `antarctic_lambda`, `antarctic_gamma`, `antarctic_kappa`, `anto_beta` have width
  ratio 1.00: the posterior IS the recycled BRICK posterior. The fast-dynamics trio that carries the 2300
  Antarctic spread is therefore neither calibrated by us nor sampled from a stated physical prior.
- `anto_alpha` moved +0.7 sd against it — a shift against a prior that was itself a posterior is a tension
  between two datasets, not an update.
- the ± 2 sd truncation is a hard bound: `antarctic_temp_threshold` posterior −16.2 … −14.9 sits inside a
  [−16.4, −14.5] box; `antarctic_kappa` has ~2 % of draws at each bound.
- (`antarctic_lambda`, `gamma`, `kappa`: BRICK's posterior on these may itself be its paleo prior; the
  DAISfastdyn ensemble marginals should be checked and used directly, as the seven geometry parameters already are.)

**Recommendation:** replace the nine with Wong 2017's uniform ranges (or the DAISfastdyn marginals where they
exist), refit, and say in the text that the BRICK-lineage parameters carry no prior information from BRICK's
calibration. The AIC/BIC comparison is not affected (it charges parameters, not priors), but "calibrated to
observations from 1900" currently overstates what the Antarctic block learned. This is the single most
important refit before submission; ~3 h.

## 2. Parameters that could be dropped (or fixed)

| parameter(s) | evidence | what to do |
|---|---|---|
| `d2_gsic_1`, `d2_gsic_2`, `d2_steric_2` | posterior medians 0.04 / 0.04 / 0.01 cm, all 5–95 % inside ±0.14 cm of zero | drop (3). `d2_steric_1` (0.26 cm) is doing real work and stays. |
| `gic_u_pre`, `gic_s_r5` | width ratios 0.97 (s_r5) / flat, ledger terms with no projection role | drop (2) or fix at the ledger's central values; they exist only to keep the 1850–1900 datum honest. |
| `antarctic_kappa` vs `ais_precip0_LOG` | r = +0.96 — a ridge: P₀·exp(κ T) is identified, not the pair | fix κ (or sample log P₀ + κ·T̄); drops 1. |
| `gis_slow_w` | flat prior, posterior 0.08–0.95: unidentified | NOT droppable without a decision — w is the temperature-dependent fraction of the slow-channel rate and its spread propagates into the discharge projection. Either an informative prior (the offline value 0.93) or fix it and say so. |
| `gis_amp`, `gic_amp_*`, `ais_gmst_amp` | width ratio 0.90–1.01, likelihood-inert (splice tails only) | keep sampled — they are prior-PROPAGATED, which is the honest way to carry a projection-side uncertainty; the paper should say "propagated, not estimated". |

Net: 58 → 52 with no loss of fit; k in the AIC/BIC test goes 58 → 52 and every margin widens.

## 3. Joint Antarctic parameters

The 17-parameter block needs 10 principal components for 80 % of its posterior variance — not a collapsed
block, but three ridges: `antarctic_kappa`–`ais_precip0_LOG` (+0.96, above), `ais_gmst_amp`–`ais_runoff_Ton`
(+0.78) and `ais_slope`–`ais_iceflow0` (−0.58). The first should be reparameterised (one parameter). The second
is the runoff onset expressed in GMST: T_on,GMST = (T_on − T_ant,0)/amp; sampling T_on,GMST and amp instead of
T_on and amp would remove the ridge and make the identified quantity the sampled one (the calibrator already
did this once for h₀/c → T_on/c; this is the same move one level up). The third is the DAIS profile geometry
and is already under the joint paleo prior — leave it. The geometry block cannot be reduced on the prior side:
its standardised paleo correlation has condition number 2.75, i.e. all seven directions carry comparable prior
variance. What the DATA identify is fewer directions than seven — the R̂ failures on `ais_iceflow0` (1.26) and
`antarctic_alpha` (1.28) are the sampler walking the unidentified ones — so the honest reduction is a
posterior-side one: report the block as its identified combinations (the two ridges above plus whatever a
posterior PCA of the seven shows), not as seven marginals.

## 4. Why `ais_runoff_Ton` is so precise, and whether it matters

`--profile` (conditional slice through the posterior median, every other parameter held): moving T_on by
−0.5 posterior sd (−0.063 °C) costs **156** log-posterior units, ALL of it in the Antarctic series term (the
glacier, Greenland, steric and prior terms move by < 0.1); by −1 °C it costs 4,860. The conditional curvature
implies a sd of ~0.004 °C; the marginal is 0.25 °C only because of the +0.78 ridge with `ais_gmst_amp`. This is
the likelihood, not mixing: all four chains give −17.77 … −17.80 with the same width.

Mechanism: the runoff line hR = c·(T_ant − T_on) is a switch, and the Antarctic target is a 126-year series
scored with per-year σ of 0.35 cm (1900s) falling to 0.06 cm (2010s) plus an AR(1) term whose fitted innovation
sd is 0.0135 cm — the model tracks the reconstruction to 0.1 mm per year. In GMST terms the fitted onset is
(−17.79 + 18.435)/1.074 = **+0.60 K above 1850–1900, first crossed in 1997** on the ensemble-mean forcing, against
a paleo prior centred at +2.3 K. That is a substantive claim — DAIS's surface-runoff switch is being used to
reproduce the post-1990s Antarctic acceleration — and it is stated with a precision the pre-1992 reconstruction
(a modelled series, not a measurement) cannot support.

Is it a problem? For the hindcast, no. For projections, yes in two ways: the onset timing carries no
uncertainty into the projection, and the mechanism it credits (runoff) is not the one the observational
literature credits (ocean-driven discharge; Rignot 2019). Tests, in order of cost: (i) inflate the pre-1992
AIS σ by ×3 (one flag) and watch T_on's width and the AIS RMSE; (ii) add a two-coefficient discrepancy term
to the AIS stream, as glaciers and steric already have; (iii) fit 1900–1992 only and predict 1993–2026 (the
honest out-of-sample for exactly this parameter); (iv) fit without the pre-1992 AIS series at all (paleo +
modern only) to see what the reconstruction buys.

## 5. Tests of the same kind as the gic_delta test

Running now (500k iterations, one chain each, seed 2026, otherwise L24's flags):
- **`L24DELTA0`** — `--delta-sigma=0.001`, δ pinned at 0: what the glacier block does without the +1.5 cm
  early-century target correction.
- **`L24TOFF4`** — `--toff-lo=-4`: the SLOWG offset bound test (§6).

Worth running next (each ~45 min single-chain, ~3 h at production length):
- the nine BRICK-posterior priors → Wong 2017 uniform ranges (§1) — first;
- AIS σ ×3 pre-1992 / AIS d2 term / 1900–1992 fit-and-predict (§4);
- `gis_f` and `gis_slow_ell` prior centres moved to the null (f = 0.5, ell at BRICK's single-channel rate) —
  a prior-centre sensitivity for the two centres taken from an offline fit to the same target;
- `gis_slow_w` fixed at 0.93 (the offline value) vs sampled — how much of the discharge projection spread it
  carries;
- κ/P₀ ridge collapsed to one parameter (§3), which is a code change plus a refit.

## 6. The SLOWG offset bound (result appended when `L24TOFF4` finishes)

L24: `gic_T_off_SLOWP` flat on [−3, 1], posterior −1.65 (−2.85, +0.09), 10 % of draws within a tenth of the
posterior width of −3. The conditional profile is soft on this side (−1 posterior sd costs 30 log-units, 23 of
them in the glacier term, 5 in the Antarctic term through the sea-level feedback), so the marginal reaches −3
only through its co-movement with `gic_b_SLOWP` (+0.65) and `gic_u_unch` (+0.48).

**Result (`L24TOFF4`, 500k, one chain, second half):** with the bound at −4 the posterior is −2.02 (−3.73, −0.09)
against L24's −1.63 (−2.86, +0.17); **23 % of the mass lies below −3**, i.e. the −3 bound was clipping about a
quarter of it, and only 2.7 % sits within 0.15 of −4, so the new bound is nearly free. Everything else in the
glacier block moves by < 0.3 of its width (b_SLOWG 0.200 → 0.177, amp 2.55 → 2.71, u_unch 28.1 → 27.5, δ
unchanged); log-posterior unchanged (220.0 → 220.8, same flat prior). The glacier hindcast RMSE is unchanged to
0.1 cm (1900–1919 1.44 → 1.34; full 0.66 → 0.61). Reading: T_off_SLOWG is unidentified toward cold values —
the data pin the product b·T_off (the committed loss at 1850–1900 temperature, S_eq(0)/a = 1 − e^{b·T_off}, which
is 0.27 in L24 and 0.30 here), not the two factors (r = +0.65). **Recommendation:** ship the bound at −4 (or
reparameterise to (b, S_eq(0)/a)) and say the offset's cold tail is prior-bounded; the regrowth statement
("full regrowth needs cooling below 1850–1900") only strengthens.

## 7. The gic_delta test (`L24DELTA0`, δ pinned at 0 by a N(0, 0.001) prior)

| | L24 | δ = 0 |
|---|---|---|
| glacier hindcast RMSE vs the BARE target, cm: 1900–1919 / 1920–1949 / 1950–1992 / 1993–2026 / full | 1.44 / 0.60 / 0.14 / 0.09 / 0.66 | **0.45 / 0.18** / **0.25** / 0.09 / 0.25 |
| `gic_u_unch` (uncharted ice, mm; flat on [14.5, 41.8]) | 28.1 (18.2–37.8) | **37.0 (29.6–41.3)** — 15 % of draws within 5 % of the upper bound |
| `gic_T_off_FASTG` / `gic_b_FASTG` | −1.53 / 0.332 | −1.90 / 0.292 |
| `gic_T_off_SLOWG` | −1.63 | −2.00 |
| `gic_delta` | 0.24 (0.11–0.39) | 0.000 |
| log-posterior (2nd-half median; priors differ, so indicative only) | 220.0 | 221.8 |

So the model CAN fit the raw early-century glacier series three times better than L24 does — L24 chose to
correct the target (+1.5 cm at 1900) instead — and the price of not correcting it is (a) the uncharted-ice scope
term pushed to the top of the Parkes & Marzeion range and piling on its bound, (b) colder equilibrium offsets in
both large blocks, (c) the 1950–1992 window worse by 0.12 cm (its Table 4 ratio would go from 1.06 to ≈ 2).
The two devices, δ and u_unch, are alternative explanations of the same feature: the model's early-century
glacier melt is ~1.5 cm short of Frederikse/Marzeion-2015 unless the uncharted-ice content is maximal. Neither
chain is "wrong"; the paper has to say which story it tells and why. My reading: the δ = 0 arm is the more
defensible one to SHOW (it scores the target we publish against and it does not change Table 4's construction),
with the u_unch bound then the thing to justify; the L24 arm is the more defensible one to SAMPLE only if
Marzeion-2015's early-segment bias can be cited independently — and I could not find that citation in the repo.
Decision for Marcus. (A four-chain production run of the δ = 0 arm is ~3 h.)
