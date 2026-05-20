# Methods

This document describes the methodology behind the SLR-RFF-BRICK pipeline.
It is adapted from the project's substack-post methods draft
([notes/handoff_2026-05-19_claude_chat_substack.md](notes/handoff_2026-05-19_claude_chat_substack.md))
and is intended as the technical reference for users of the code.

## 1. Model chain

```
RFF-SP emissions  →  FaIR v2.2.4 climate model  →  MimiBRICK sea-level model
   (10,000 scenarios)   (841 v1.4.1 configs)         (10,000 posterior draws)
```

Each link in the chain is sampled probabilistically and propagated through
to the next. The final ensemble is then importance-weighted against
observed historical GMSL via the Wong (2026) AR(1) likelihood.

### 1.1 RFF-SP emissions scenarios

The Rennert et al. (2022) RFF-SP set is a probabilistic 21st-century
socio-economic + emissions ensemble — 10,000 internally-consistent
trajectories spanning the joint distribution of GDP, population, and GHG
emissions under no climate policy. We use a 398-RFF or 490-RFF subset
(depending on the cube vintage; see § 5 below) drawn via Latin Hypercube
sampling over the joint (RFF, FaIR cfg) space, then expanded to all 841
FaIR configs per unique RFF (since FaIR with 841 configs costs about the
same as 1 config — almost all the time is per-timestep).

Variable name in code: `rff_idx` (1-indexed, integers in 1..10,000).

### 1.2 FaIR v2.2.4 climate model

FaIR is a reduced-complexity ("simple") climate model that converts
emissions of CO₂, CH₄, N₂O, and aerosols into a GMST anomaly time
series, with explicit carbon-cycle and energy-balance components.

**Important version distinction:** the *model* is **FaIR v2.2.4**
(the Python package `from fair import FAIR`). The *calibration* is
**FaIR-calibrate v1.4.1** — Chris Smith et al.'s 841-member posterior
over FaIR's free parameters (climate sensitivity, ocean heat uptake
rate, aerosol forcing, carbon-cycle feedbacks), constrained against
historical observations and AR6 assessed ranges. Captions in this
project that say "FaIR v1.4.1" are referring to the calibration, not
the model version.

Variable name in code: `fair_cfg_idx` (0-indexed, 0..840).

### 1.3 MimiBRICK sea-level model

MimiBRICK converts a FaIR-supplied GMST trajectory into GMSL with
explicit components for thermal expansion, glaciers, the Greenland
ice sheet, and the Antarctic ice sheet (the latter with an explicit
tipping-threshold parameterization).

The MimiBRICK posterior — 10,000 posterior subsample draws over
BRICK's free parameters (ice-sheet sensitivities, AIS tipping
thresholds, AR(1) likelihood nuisance terms) — feeds the project's
probabilistic SLR projections. Each FaIR-driven BRICK run produces
a year-by-year GMSL trajectory through 2300.

Variable name in code: `post_idx` (1-indexed, 1..10,000).

## 2. Final SLR ensemble: LHS-10k conditional BRICK

The SLR-side figures in this project are built from a final ensemble of
**10,000 (RFF, FaIR cfg, BRICK posterior) triplets** sampled by Latin
Hypercube ([python/scripts/build_lhs10k_metadata.py](python/scripts/build_lhs10k_metadata.py)).
Coverage is excellent: every one of the 490 RFFs is used 19–22 times,
every one of the 841 FaIR configs 11–13 times, and each of the 10,000
MimiBRICK posterior members is used exactly once. Triplet pairings are
randomized across axes to avoid spurious structural correlations.

For each triplet we run a paired baseline + pulse BRICK simulation through
1850–2300, then compute a Wong (2026) importance weight per row:

```
log(w_i)  ∝  l_FB( gmsl_i | cfg_i, post_i )  −  l_B( post_i )
```

where:

- **l_FB** is the AR(1) Gaussian log-likelihood of the row's paired
  FaIR-driven BRICK trajectory against observed historical GMSL
  (Dangendorf et al. 2024).
- **l_B** is the same likelihood evaluated with BRICK's default-forcing
  trajectory for that posterior member.

The ratio rewards (cfg, post) pairings whose joint historical fit beats
the unconditional-on-cfg fit for the same BRICK member.

**Conditional sampling via importance weighting.** Because the numerator
l_FB depends on each row's *specific* paired FaIR cfg, the weights are
*conditional on the cfg* by construction — they approximate the joint
posterior p(cfg, post | obs GMSL) rather than the product of marginals.
This addresses the methodological concern that pairing FaIR
climate-sensitivity draws with BRICK posterior members independently of
the cfg could let high-sensitivity FaIR runs stack on top of
high-sensitivity ice-sheet parameters, inflating the projection spread.
The conditional weighting prevents this — though as it turns out the
practical effect was small (the older 500-cell paired ensemble already
used the same Wong-weighting mechanism, and percentiles agreed with
LHS-10k to within ~1–2 cm).

**Effective sample size after weighting: ESS = 7,037 / 10,000 (70.4%)**.
The weighted 10,000-row ensemble is statistically equivalent to ~7,000
equal-weight independent samples. In Bayesian importance sampling
ESS > 50% of N is considered excellent.

The pipeline files are:

| File | Role |
|---|---|
| [python/scripts/build_lhs10k_metadata.py](python/scripts/build_lhs10k_metadata.py) | Generate 10,000-row LHS triplet metadata |
| [julia/run_mimibrick_paired_explicit.jl](julia/run_mimibrick_paired_explicit.jl) | Run paired baseline + pulse BRICK for each triplet |
| [python/apply_wong_weights.py](python/apply_wong_weights.py) | Compute l_FB, look up l_B, derive w_norm |
| [julia/compute_lB_per_post.jl](julia/compute_lB_per_post.jl) | Pre-compute l_B per BRICK posterior member |
| [slurm/submit_lhs10k_brick_pipeline.sh](slurm/submit_lhs10k_brick_pipeline.sh) | Full Torch HPC submit |

## 3. Key methodological choices

### 3.1 Observational anchors

**GMST: IGCC 2024 4-dataset consensus** (HadCRUT5 + Berkeley Earth +
GISTEMP + NOAAGlobalTemp). The 2015–2024 mean rel. preindustrial
(1850–1900) baseline is **+1.254 °C**. This is the value FaIR is
bias-corrected to (§ 3.2). The IGCC dataset is the one FaIR's own
calibration team uses, which avoids an apples-to-oranges anchor mismatch.

The IGCC line is sourced from **Trewin's raw 4-dataset average**, not
Walsh's fitted `total_p50`. The Walsh `total_p50` is an
attribution-method regression fit that smooths over the 2024 ENSO
peak; we use Walsh's band width (p95−p05 about p50) for honest
cross-dataset uncertainty, centered on Trewin's raw value.

**SLR:** Dangendorf et al. 2024 (tide-gauge reconstruction) for pre-1993
historical data + NOAA STAR satellite altimetry for the altimetry era
(1993–2024). 2015–2024 anchor: +6.38 cm rel. year 2000.

### 3.2 AR6-style bias correction

FaIR's ensemble-median modelled 2015–2024 warming is +1.04 °C rel
preindustrial, versus the IGCC observation of +1.254 °C. FaIR's
ensemble systematically under-predicts the observed present-day warming
by about 0.21 °C.

We apply the AR6 framing: each FaIR trajectory is rebaselined to its
*own* 2015–2024 mean, then shifted up to the IGCC observed anchor:

```
T_corrected(t) = T_FaIR(t) − T_FaIR(2015-2024 mean) + 1.254 °C
```

Result: every trajectory passes through the observed present-day value,
and the future spread is added on top of observed warming. This is the
standard AR6 projection-framing — it respects the historical observation
record rather than blindly trusting the model's absolute level.

### 3.3 Hawkins-Sutton variance decomposition

The Hawkins-Sutton (2009) framework partitions the total variance of a
projection at year *t* into additive components:

- **V_emissions(t)** — variance across RFF-SP scenarios, holding climate
  response and other factors fixed.
- **V_climate(t)** — variance across FaIR parameter configs, for a given
  emissions trajectory.
- **V_internal(t)** — chaotic year-to-year fluctuations (only present
  when FaIR is run with stochastic seeds).
- **V_brick(t)** — *for SLR only* — variance across BRICK ice-sheet /
  glacier / thermal-expansion parameter posteriors.

Each component is expressed as a fraction of total variance, varying
with year. Figure 4-way decompositions (Panels C and D of the poster,
plus the substack H-S figures) use the 13,500-row balanced ANOVA
factorial design (100 RFFs × 15 cfgs × 3 seeds × 3 posts), because
classical 4-way variance decomposition requires the factorial
replication structure that pure LHS doesn't provide. The total-SLR
envelope and pulse-marginal envelope figures, by contrast, use the
LHS-10k ensemble.

A direct intellectual companion is Darnell et al. 2025 (*Nature
Climate Change*), who decompose total-SLR uncertainty into emissions
vs geophysical components and find that emissions timing dominates in
the 21st century, with geophysical (AIS tipping) uncertainty becoming
more important under optimistic scenarios.

### 3.4 Pulse-marginal calculations

For social-cost-of-CO₂-style analysis we run paired baseline + pulse
runs. The "marginal climate response" to a 1 GtCO₂ emission at 2030 is
the year-by-year difference (pulse − baseline) for each triplet,
summarized as median + 5–95% band.

- **GMST marginal:** Linear in pulse size; computed at the +1 GtC
  production pulse (verified pulse-size invariant). Per-GtCO₂ units
  obtained by dividing by the C-to-CO₂ molecular-mass ratio (3.667).
- **SLR marginal:** Has a nonlinearity from Antarctic ice-sheet (AIS)
  tipping at large pulses, so for the headline per-tonne SC-SLR number
  we use the +0.01 GtC small-pulse companion run (linear regime). The
  4-way variance decomposition is necessarily done at the +1 GtC
  production-pulse scale, where the AIS tipping-state-dependent
  variance is actually present.

### 3.5 AIS tipping (Lemoine-style decomposition)

A small fraction (~5%) of BRICK posterior draws have ice-sheet states
pre-positioned near a tipping threshold (Antarctic SLR contribution at
year 2100 > 20 cm at baseline). For these draws, a 1 GtCO₂ pulse can
push the system over the tipping point, producing very large marginal
SLR.

The figure decomposition uses the Lemoine framework where expected
marginal damage is split into:

1. **Linear sensitivity** — the response in the absence of tipping
   (computed from the non-tipping-prone subset, or from the small-pulse
   limit).
2. **Tipping insurance premium** — the additional expected response from
   the probability of crossing the threshold.

The classifier `baseline ais_2100 > 20 cm` and the median-based per-tonne
sensitivities are implemented in
[python/scripts/extract_pulse_marginals.py](python/scripts/extract_pulse_marginals.py)
and [python/scripts/extract_lhs10k_smallpulse_summary.py](python/scripts/extract_lhs10k_smallpulse_summary.py).

## 4. Computational pipeline (Tiers 2 and 3)

### Tier 3 — generate FaIR cubes from RFF-SP

```
data/RFF-SP-emissions/  +  data/RFF-SP-socioeconomics/
            │
            ▼
   python/lhs_climate_pilot{,_ext}.py
            │
            ▼
   outputs/rff_baseline_stoch_to2300.npz        (1.9 GB, 490 RFF × 841 cfg × 451 yr)
   outputs/rff_pulse_stoch_to2300.npz           (1.9 GB, paired +1 GtC at 2030)
   outputs/rff_pulse0p01gtc_stoch_to2300.npz    (1.9 GB, paired +0.01 GtC at 2030)
```

Submit script: [slurm/submit_lhs_fair.sh](slurm/submit_lhs_fair.sh) and
[slurm/submit_small_pulse_fair.sh](slurm/submit_small_pulse_fair.sh).

### Tier 2 — run BRICK against the FaIR cubes

```
FaIR cubes  +  data/MimiBRICK/parameters_subsample_brick.csv
            │
            ▼
   python/scripts/build_lhs10k_metadata.py     # 10k LHS triplets
            │
            ▼
   julia/run_mimibrick_paired_explicit.jl      # paired BRICK for each triplet
            │
            ▼
   python/apply_wong_weights.py                # Wong importance weights
            │
            ▼
   outputs/brick_lhs10k_{baseline,pulse,pulse0p01gtc}_to2300_weighted.csv
```

Submit scripts: [slurm/submit_lhs10k_brick_pipeline.sh](slurm/submit_lhs10k_brick_pipeline.sh)
and [slurm/submit_lhs10k_brick_smallpulse.sh](slurm/submit_lhs10k_brick_smallpulse.sh).

### Tier 1 — regenerate figures from weighted ensembles

```
outputs/brick_lhs10k_*_weighted.csv  →  outputs/poster/slr_band.png
outputs/brick_lhs10k_*_weighted.csv  →  outputs/substack/obs_overlay_slr.png
outputs/plots/hawkins_sutton_*.csv   →  outputs/substack/updated_hawkins_sutton_slr.png
                                     →  outputs/poster/hawkins_sutton_slr_4way.png
outputs/substack/co2_pulse_*_summary*.csv  →  outputs/substack/pulse_responses_clean.png
outputs/lhs_pilot_gmst_full_N200_to2300.npz  →  outputs/substack/exceedance_table.png
                                              →  outputs/substack/median_crossing_year.png
                                              →  outputs/substack/obs_overlay.png
```

Each substack and poster figure has a single script in
`python/scripts/substack/` or `python/scripts/poster/` and a small CSV
input committed to git. Tier 1 needs no external downloads.

## 5. Caveats worth documenting

### 5.1 RFF cube size: 398 vs 490

The substack-side cube file `outputs/lhs_pilot_gmst_full_N200_to2300.npz`
has 398 unique RFFs; the production cube on Torch
(`outputs/rff_baseline_stoch_to2300.npz`) has 490 unique RFFs. They are
*not* a subset relationship — only 13 RFFs are shared by coincidence.
Both were drawn via 2-D Latin Hypercube over (RFF in 1..10,000, cfg in
0..840), expanded to all 841 cfgs per unique RFF. Different LHS seeds
gave different unique-RFF lists.

### 5.2 FaIR cool anomaly bias is not fully canceled

Even after AR6 bias correction (which shifts each trajectory to match
IGCC at 2015–2024), FaIR's cumulative warming trajectory from
1850–1900 to present is about 0.21 °C cooler than IGCC observed. The
bias correction places the trajectories at the right *level* today, but
the *path* of warming from PI to today is gentler in FaIR than observed.

### 5.3 BRICK historical SLR underestimate

Observed (Dangendorf 2024) GMSL rise 1900 → 2018: **+20.9 cm**. BRICK p50
modelled rise 1900 → 2018: **+12.0 cm**. Shortfall: **~8.9 cm**, of
which ~2–3 cm is plausibly attributable to FaIR's cool anomaly bias.
The remainder (~6–7 cm) is BRICK-side — candidate causes include
under-parameterized glacier melt, conservative ice-sheet rate constants,
or a Wong AR(1) likelihood weighting that under-fits early-20th-century
discrepancies.

### 5.4 BRICK underestimates the modern SLR rate

Over 2010–2024: NASA STAR observed slope is 3.99 mm/yr; BRICK p50
slope is 2.60 mm/yr (65% of obs); BRICK p95 slope is 3.14 mm/yr (still
below obs median). The observed slope sits outside BRICK's 5–95% band.

### 5.5 RFF-SP vs SSP probabilistic interpretation

RFF-SP is a single internally-consistent probabilistic set, so quoting
percentiles is well-defined. SSPs are policy scenarios without intrinsic
probability weights, so a "median RFF" and a "median SSP5-8.5" are
incommensurable in a strict probabilistic sense.

### 5.6 Median is pulse-size invariant; mean is not

For SC-CO₂-SLR sensitivities, always cite the **median** small-pulse
value. The mean response to a +1 GtC pulse is contaminated by AIS tipping
in a small subset of posterior draws, which makes it sensitive to pulse
size. We verified pulse-size invariance of the median across 0.01, 0.1,
and 1.0 GtC pulses ([python/scripts/substack/pulse_convergence.py](python/scripts/substack/pulse_convergence.py)).

## 6. References

- Darnell et al. 2025. *Nature Climate Change* 15:1205–1211. [doi:10.1038/s41558-025-02457-0](https://doi.org/10.1038/s41558-025-02457-0)
- Hawkins & Sutton 2009. *Bulletin of the American Meteorological Society*.
- Rennert et al. 2022. *Nature*. [doi:10.1038/s41586-022-05224-9](https://doi.org/10.1038/s41586-022-05224-9)
- Smith et al. 2024. *Geosci Model Dev*. [doi:10.5194/gmd-17-8569-2024](https://doi.org/10.5194/gmd-17-8569-2024)
- Wong et al. 2017. *Geosci Model Dev* 10:2741–2760 (BRICK v0.2). [doi:10.5194/gmd-10-2741-2017](https://doi.org/10.5194/gmd-10-2741-2017)
- Wong 2026. *arXiv preprint* (Wong importance weighting). [doi:10.48550/arXiv.2604.13446](https://doi.org/10.48550/arXiv.2604.13446)
- Dangendorf et al. 2024. *Earth System Science Data*. [doi:10.5281/zenodo.10621070](https://doi.org/10.5281/zenodo.10621070)
- Sweet et al. 2022. NOAA Tech Rep NOS 01.
