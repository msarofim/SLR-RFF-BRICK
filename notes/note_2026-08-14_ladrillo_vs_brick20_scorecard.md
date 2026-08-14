# Ladrillo 1.0 vs BRICK 2.0 — scorecard against Marcus's acceptance criteria

Marcus, 2026-08-14, per module (GSIC / Greenland / AIS / TE / LWS): (1) physical
formulation at least as credible as BRICK 2.0's; (2) hindcast match at least as
good; (3) projection spread at least as good — better FACTS/MAGICC match, or just
more physical; (4) the same for the joint calibration.

**Marcus's refinement, adopted here: criterion 1 splits into two bins —
STRUCTURE (the equations) and CALIBRATION APPROACH (what data and priors the
calibration is allowed to see). Expanding the observational base is itself an
improvement over BRICK 2.0 and should be credited as one, not folded into
"formulation".**

Evidence: `python/scope_ladrillo_vs_brick20_scorecard.py` →
`outputs/scope_ladrillo_vs_brick20_scorecard.csv` (hindcast);
`outputs/ladrillo_model_comparison{,_spread}.csv` (projections).

---

## 0. CORRECTION — AIS is NOT unchanged

An earlier reading of this session said "AIS, TE and LWS are BRICK 2.0's own code,
unchanged" on the basis that `build_brick_nu3_gis` only `replace!`s the glacier
and Greenland slots. **That was wrong for AIS**: the component object is stock
DAIS, but the calibrator re-parameterises it in four separate ways
(`calibrate_mcmc_ext.jl`). The mistake was checking which components are swapped
instead of what the calibrator does to them — the same failure mode as
"grepping for symbol references finds call sites, not live paths" (spec §8.1).

**A6 — the GMST→Antarctic temperature map (this is the one Marcus flagged).**
BRICK 2.0 hard-codes `coef 0.8365, intercept 15.42`, i.e. **amplification 1.196,
the inverted paleo/EQUILIBRIUM regression**. Ladrillo samples it as a *transient*
amplification, prior **N(0.95, 0.10)** on [0.70, 1.25], with the anchor
`T_ant(GMST=0) = −18.435` preserved so only the anomaly scaling moves. Centred on
CMIP6 PAI1 over the AIS (Xie et al. 2022, Sci Rep 12:16548 — 0.88/0.95/0.97/1.03
across SSP1-2.6…5-8.5). The old equilibrium value sits **+2.5σ** from the new
prior, i.e. deliberately excluded. `--amp-equilibrium` isolates A6 by pinning it
back. Threshold-crossing GMST becomes `(threshold − T_ant0)/amp`, so this moves
the tipping threshold, not just the level.

Three more AIS changes in the same lineage:
- **λ, γ, κ (fast dynamics) freed**, previously fixed at the DAISfastdyn medoid —
  which was biased in the pulse-amplifying direction (λ 0.0137 vs paleo mean
  0.0104) and carried **zero** reported uncertainty on the dominant lever of the
  100/150-yr pulse response.
- **Strategy B**: 7 DAIS geometry parameters freed under a joint paleo prior
  (standardised `MvNormal(0, C)`, cond 2.75), previously fixed at the medoid,
  discarding both spread and paleo correlation.
- **`T_on` reparameterisation**: the runoff line sampled along its identified
  direction (`ais_runoffline_snowheight₀ = −ais_runoff_Ton · ais_c`).

TE and LWS *are* unchanged in structure (LWS seeded rather than randomly drawn).

## 0b. SUB-GLOBAL TEMPERATURE PATTERNS — a model-wide change, under-credited above

Marcus, 2026-08-14: the third improvement is **sub-global temperature patterns for
the historic fit, and CMIP6-calibrated patterns for the projections**. An earlier
version of this note credited the regional driver to Greenland only. It is
model-wide, across all three ice/glacier modules, and it splits across BOTH bins.

**Historic (observational patterns).** BRICK 2.0 drives every module off GMST.
Ladrillo drives each off its own region:
- **Glaciers**: `t_glac_blocks.csv` — **GlaMBIE-area-weighted HadCRUT5** per block
  (R19 / SLOWP / FAST), K rel 1850-1900.
- **Greenland**: `t_gis_zones.csv` — southern Greenland (59-70 N) land-masked,
  already on the 1850-1900 frame.

**Projection (where CMIP6 enters).**
- **AIS**: A6 amp N(0.95, 0.10) — fully CMIP6 (Xie 2022 PAI1).
- **Greenland**: amplification **level** from observations (1.9222 ± 0.3181,
  `gis_amp_prior.csv` south/full), **warming-level SHAPE from 40 CMIP6 models**
  (secant ratio S(dT), monotone 1.498 → 1.284 over 0.75-2.75 K, −0.050/K), so
  `amp(dT) = amp_draw · S(dT)` with `S(dT_eff) = 1` at the calibration point.
- **Glaciers**: `gic_amp_b` **sampled**, priors centred near HadCRUT5 with σ and
  hard bounds from the **cross-dataset spread** (`diag_amp_dataset_comparison.csv`:
  SLOWP 1.82 BE / 2.48 HadCRUT5 / 3.46 GISTEMP; R19 0.58-0.85). Observationally
  informed, not CMIP6.

**Design constraint worth crediting separately** (`calibrate_mcmc_ext.jl` L207):
the external interface is still **GMST + OHC only** — the regional drivers are
built inside the model's own inputs. Ladrillo keeps the drop-in property that
distinguishes it from MAGICC-SLR while getting the pattern-scaling benefit.

### This RETRACTS part of §2's caveat, for Greenland at least
§2 says the hindcast win is "largely the calibration-approach bin cashing out".
**For Greenland that is demonstrably wrong**, and `outputs/gis_offline_cell_fits.csv`
has the parameter-count-controlled decomposition:

| cell | n_par | neg_log_post | mid-century bias cm | RMSE cm |
|---|---|---|---|---|
| incumbent (stock SIMPLE, as calibrated) | 5 | 980.04 | −0.828 | 0.533 |
| stock (stock SIMPLE, **refit**) | 5 | 234.92 | −0.226 | 0.325 |
| **A — regional driver alone, one channel** | **5** | **17.87** | **+0.014** | **0.061** |
| B — two channels, GMST driver | 8 | 232.07 | −0.227 | 0.282 |
| A+B | 8 | 17.856 | +0.015 | 0.062 |

**The sub-global driver does essentially all of it.** Cell A drops the objective
234.92 → 17.87 **at the same parameter count** as the refit stock model; cell B
adds three parameters on the GMST driver and buys 2.9 nlp. Adding the channels on
top of A buys **0.019 nlp**. So this is not extra freedom fitting better — it is a
capability the GMST-driven model does not have at any parameter values, because
Greenland cooled ~1.8 °C/century over 1940-1990 while the globe warmed.

Corollary: the two-channel split (B) is NOT earning its keep on the hindcast. It
is carried for the Mouginot partition and the commitment/SMB physics — which is
also where it now fails at 2300 (§4, and the commitment-ridge note).

### And the CMIP6 shape law is what fixes Greenland's projection spread
The offline A+B cell at **constant** amp gives a 2100 scenario spread of
**10.44 cm**, outside the FACTS/MAGICC evaluation band (6.3-7.3 cm). With the
CMIP6 shape law on, the shipped L10 spread is **7.39 cm** — into (just above) the
band. So the CMIP6-calibrated pattern is load-bearing for criterion 4 on Greenland,
not decoration. NB `gate4_spread` in the fits CSV is **EVAL ONLY**
(`gis_offline_cell.py` L600), not a pass/fail gate — its `False` on A+B is the
constant-amp value and is superseded by the law.

## 1. The calibration-approach bin

| | BRICK 2.0 (as published) | Ladrillo 1.0 |
|---|---|---|
| total GMSL | CSIRO/Church & White recon to 2013 | Dangendorf 2024 + NOAA STAR → 2024 |
| components | IMBIE AIS 92-17, IMBIE GIS 92-18, Dyurgerov GSIC 61-03, MAR/InSAR GIS 58-13 — as **Gaussian point terms** | **Frederikse 2020 five-component budget 1900-2018, per-year σ from its own 5000-member ensemble**, extended to 2025/26 (GRACE-FO AIS+GIS→2025, GlaMBIE GSIC→2023, NOAA NCEI steric→2025) |
| OHC | Gouretski 3000 m | (forcing-side; FaIR mean GMST+OHC) |
| glacier partition | — | **GlaMBIE** SLOWP/FAST share, 0.6876 ± 0.0500 |
| glacier commitment | — | **GlacierMIP3** 4 correlated warming rungs |
| Greenland partition | — | **Mouginot 2019** SMB/discharge share |
| glacier inventory | — | A2 inventory + SMB anchor |
| AIS temperature map | fixed paleo/equilibrium | **Xie 2022 CMIP6 transient prior** |
| GIS amplification | — (GMST driver) | amp **level OBSERVATIONAL** N(1.92, 0.32); **warming-level SHAPE from 40 CMIP6 models** (§0b — do not call the level CMIP6) |
| glacier amplification | — (GMST driver) | sampled, **cross-dataset** priors (HadCRUT5 / BE / GISTEMP) |
| regional drivers | — (GMST everywhere) | **per-block + Greenland-zone observed T** (§0b) |
| AIS geometry/fast-dyn | medoid, fixed | DAISfastdyn paleo ensemble, joint prior |

The IMBIE dAIS(92-17) and Dyurgerov dGSIC(61-03) point terms were **dropped**,
replaced by the full time series they summarised. So this is not only additive.

**This bin is an unambiguous improvement**, and it is the bin that makes the
criterion-2 comparison unfair in Ladrillo's favour (§2).

## 2. Hindcast (criterion 2) — matched metrics, computed 2026-08-14

Both arms: 1995-2005 re-reference (verified: the targets are themselves zeroed on
that window to −0.0000 cm), same FaIR forcing, PARAMETRIC 90% bands.

| component | RMSE ratio L10/B2.0, full record | 90% coverage L10 | 90% coverage B2.0 |
|---|---|---|---|
| AIS | **0.03×** | 82% | 31% |
| glaciers | **0.31×** | 44% | 47% |
| Greenland | **0.08×** | 57% | 22% |
| thermal exp. | **1.18× (worse)** | **29%** | 96% |
| TOTAL | **0.19×** | 42% | 25% |

**Two caveats that matter more than the ratios.**

1. **In-sample vs out-of-sample.** BRICK 2.0 runs its own published posterior and
   was never recalibrated on these targets. Ladrillo was fit to exactly them, so
   these ratios overstate the win by an unknown amount.
   **But do NOT read the whole win as the calibration bin cashing out** — §0b
   decomposes Greenland's at controlled parameter count and it is STRUCTURE
   (the sub-global driver), not freedom. A fair structure
   test needs a BRICK 2.0 arm recalibrated on the extended targets. **That arm
   does not exist.**
2. **The uncertainty is worse calibrated than BRICK 2.0's.** Parametric bands
   under-cover everywhere (29-82% against a nominal 90%); the predictive bands
   over-cover (99-100%, `postpred_L10_coverage.csv`). Neither is a 90% interval.
   This is D2's territory and it is systemic, not per module.

TE is the one regression, and it is a *calibration* outcome (structure
unchanged): mean bias **+0.255 cm** here, consistent with the spec's recorded
+0.281 cm steric residual and `thermal_alpha` 0.0986 vs 0.1043 observed.

## 3. Projection spread (criterion 3), 2100

`ladrillo_model_comparison_spread.csv`, SSP1-2.6→SSP5-8.5 spread in cm:

| component | L10 | BRICK 2.0 | MAGICC | FACTS |
|---|---|---|---|---|
| glaciers | 6.14 | 4.47 | 4.85 | 6.52 / 8.48 |
| gis | 7.39 | — | 7.09 | 6.34 / 7.26 / 7.23 |
| ais | **32.95** | — | 35.45 | −2.32 / 2.53 / 19.66 / −0.22 / 8.92 |
| te | 12.42 | — | 16.79 | 14.77 |
| total | 58.83 | — | 62.26 | 25.15-50.69 |

**AIS re-read in light of §0.** L10's AIS scenario spread exceeds every FACTS
module and matches only MAGICC. Read against a model whose fast-dynamics
parameters were *frozen at a medoid*, that is not obviously a defect — freeing
λ/γ/κ and the geometry block was a deliberate decision to propagate fast-dynamics
uncertainty BRICK 2.0 reported as zero, and the FACTS modules with ~zero scenario
spread (ar5AIS −2.32, emuAIS −0.22) are the ones that look unphysical. **The
earlier "AIS fails criterion 3" verdict is downgraded to OPEN**, pending a
decomposition of what actually drives the 33 cm: if it is λ/γ/κ + geometry, it is
by design; if it is `ais_iceflow0` (R̂ 2.359, the non-mixing direction), it is an
artefact. Not measured.

Note the BRICK 2.0 comparator row exists **only for glaciers** — criterion 3
against BRICK 2.0 specifically is unanswered for gis/ais/te/total.

## 4. Where it stands

| module | structure | calib. approach | hindcast | spread |
|---|---|---|---|---|
| GSIC | better (3 reservoirs + ν; **per-block regional drivers**) | better | better (0.31×) | better (closer to FACTS than B2.0) |
| Greenland | better ≤2100 (**the regional driver is the whole hindcast win, §0b**); **fails at 2300** (no millennial reservoir; commitment ridge) | better | better (0.08×) | best-matched module at 2100, **and only with the CMIP6 shape law** |
| AIS | **better** (A6 transient map; λ/γ/κ + geometry freed) | better | better (0.03×) | **OPEN** — wide by design or artefact, undecided |
| TE | unchanged | better | **worse (1.18×)** | narrower than FACTS and MAGICC |
| LWS | unchanged (seeded) | — | n/a | zero by construction |
| **joint** | — | — | better (0.19×), **but in-sample** | centre good; total on the low side of FACTS |

**Systemic, not per-module: band calibration.** Every module's parametric interval
is too narrow and every predictive interval too wide. That is the single finding
that applies to the whole model and is not addressed by any thread now open
except D2.

## 5. What is not measured

- No BRICK 2.0 arm recalibrated on the extended targets → criterion 2 cannot
  separate structure from calibration inputs.
- No BRICK 2.0 spread row for gis/ais/te/total.
- FACTS in the comparison file stops at 2150 → **nothing tests 2300**, which is
  where Greenland is now known to be broken.
- No decomposition of the AIS 2100 spread into its freed parameter groups.
