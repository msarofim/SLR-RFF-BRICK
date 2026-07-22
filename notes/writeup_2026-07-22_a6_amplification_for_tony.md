# The GMST→Antarctic temperature map in BRICK-FM: a CMIP6-based update (for Tony)

*Marcus Sarofim / 2026-07-22. Prepared as a discussion note. Scripts, reduced data, and
figures are committed on `SLR-RFF-BRICK @ brick-mengel-vnext`
(`python/reduce_cmip6_tas_pai.py`, `python/diag_pai_cmip6_time.py`,
`python/diag_pai_mask_sensitivity.py`; outputs `outputs/diag_pai_cmip6_time.*`).*

## 1. Background: what we did to the map, and why we're revisiting it

DAIS drives its runoff line and fast-dynamics threshold with an Antarctic surface
temperature computed linearly from global temperature each timestep:

> T_ant = T_ant,PI + a · ΔT_glob,  with the classic a = 1/0.8365 ≈ **1.196** and
> T_ant,PI ≈ −18.4 °C (the −15.42/0.8365 regression in the DAIS lineage, Shaffer 2014).

In the BRICK-FM phase-2 recalibration we freed `a` ("item A6") under a CMIP6-*transient*
prior N(0.95, 0.10), on the argument that 1.196 is an equilibrium/paleo number while a
21st-century simulation runs far from equilibrium. The 0.95 came from Xie et al. 2022
(Sci Rep 12:16548): their annual "PAI1" over the AIS = trend(T_AIS)/trend(T_global) over
2015–2100 = 0.95 (SSP2-4.5) / 1.03 (SSP5-8.5). The posterior followed the prior (0.944 —
the obs don't constrain `a`), and this single change drove roughly two-thirds of the
phase-2 drop in projected SSP2-4.5 GMSL @2100 (76 → 40 cm median).

Because the prior effectively *sets* the projection, we ran a diagnostic to ask: is a
constant transient value even the right shape — does the amplification rise with time and
warming? Short answer: **yes, it rises, it is warming-level-controlled, and it saturates
at your equilibrium value** — plus one metric subtlety that partly rehabilitates 0.95.

## 2. The diagnostic

34 CMIP6 models (one member each, Amon `tas` streamed from the public Pangeo/GCS mirror),
historical + ssp245 + ssp585. Antarctic region = **land (sftlf ≥ 50%) south of 60°S**,
area-weighted; anomalies rel. 1850–1900. We compute a *windowed* PAI1: the 41-yr OLS
trend ratio trend(T_AIS)/trend(T_glob), sliding through 1850–2100 (windows with global
trend < 0.05 K/decade masked — the ratio is unstable there).

Findings (figure: `outputs/diag_pai_cmip6_time.png`):

1. **Within-scenario rise.** Median windowed ratio climbs 1.06 → 1.19 through the century
   in SSP2-4.5 (+0.035/decade) and 1.13 → 1.19 in SSP5-8.5.
2. **Collapse on warming level.** Plotted against window-mean ΔT_glob, the two scenarios
   lie on ~one curve: ≈0.9 at 0.7 K, ≈1.1 at 1.5–2 K, flattening at ≈1.15–1.2 by 2–4 K.
   SSP5-8.5 at a given warming level (reached decades earlier) matches SSP2-4.5 at the
   same level — amplification behaves as a function of warming level, not elapsed time or
   forcing mix.
3. **It saturates at the DAIS equilibrium value.** Fitting a saturating curve with a free
   asymptote returns ≈1.14; *fixing* the asymptote at 1.196 fits essentially as well
   (RMSE 0.054 vs 0.050). CMIP6's transient Antarctic amplification relaxes toward the
   paleo-equilibrium slope — a nice independent consistency check of the classic number.
4. **Mask matters at the 0.15–0.2 level.** Our land-only metric gives a full-window
   (2015–2100) ratio of 1.13/1.16 (ssp245/585) — not Xie's 0.95/1.03. Their values are
   reproduced almost exactly by an **all-points polar cap south of 60°S** (6-model test:
   cap 0.92/0.98; land-only 1.09/1.16; the Southern Ocean's delayed warming drags the cap
   ratio down). So the 0.95 we used in the A6 prior appears to be a cap-referenced number,
   while DAIS's temperature is ice-sheet-referenced (ice-core lineage) — the land-only
   frame is the like-for-like one. *(Question for you below.)*

## 3. The subtlety that saves the constant: level vs marginal slope

The windowed trend ratio is a **marginal** slope, dT_ant/dT_glob, which rises with
warming. But DAIS's constant `a` is a **secant (level)** slope anchored at pre-industrial:
T_ant − T_ant,PI = a·ΔT_glob. For what the map actually controls — when T_ant reaches the
runoff/disintegration thresholds — the constant that reproduces the nonlinear truth is the
*level* ratio at the crossing-relevant warming, i.e. the warming-average of the marginal,
which sits well below the late-century marginal.

Integrating the fitted marginal (§4) gives level ratios of ~0.85 at 1 K, **0.95 at 2 K,
1.02 at 3 K** (land frame). So two corrections nearly cancel: moving from Xie's cap frame
to the land frame raises the number ~+0.15, and moving from marginal to level lowers it
~−0.13. The original 0.95 lands close to the land-referenced level ratio at ~2 K — closer
to right than either correction alone suggests. For the thresholds our posterior actually
holds (T_ant must rise ~2.3–3.3 K, i.e. crossings at ΔT_glob ≈ 2.5–3.5 K on SSP2-4.5),
the crossing-relevant level ratio is ~0.97–1.03.

## 4. The two proposals

**A. Constant (cheap; a prior swap only): `a ~ N(1.00, 0.15)`.**
Center = the land-referenced level ratio at crossing-relevant warming (0.97–1.03 over
2.5–3.5 K). Width = inter-model spread (per-model projection-era ratios: sd 0.20–0.27,
inflated by single-member internal variability) plus the mask/level systematics (~±0.05
each). Two consequences we want your read on: (i) the equilibrium 1.196 now sits at
+1.3σ — *admitted* rather than effectively excluded (old prior: +2.45σ); (ii) since the
obs don't identify `a`, the posterior will track this prior, and projections shift
modestly up from phase-2 (direction certain, size not yet run; the fully-recalibrated
equilibrium-amp run brackets the top: 63.6 cm @2100 vs phase-2's 39.7).

**B. Simple equation (structural; needs recalibration).** Fit to the pooled 34-model
median collapse curve (ΔT ≥ 0.6 K), asymptote fixed at the DAIS equilibrium:

> marginal: da/dΔT form  **amp(ΔT) = 1.196 − 0.54·exp(−ΔT/1.05)**
> (0.86 at 0.5 K, 0.99 at 1 K, 1.12 at 2 K, 1.17 at 3 K)

and the map DAIS would implement is its integral — still algebraic, per-timestep, no new
state variable:

> **T_ant = T_ant,PI + 1.196·ΔT_glob − 0.57·(1 − exp(−ΔT_glob/1.05))**

Properties: exactly the equilibrium slope in the high-warming/paleo limit (so the paleo
constraints that produced 0.8365/−15.42 are honored where they apply); transient
suppression at low warming emerges automatically; our "transient vs equilibrium"
calibration pair collapses to one model. Against the CMIP6 median curve it beats any
constant by construction (constant-fit RMSE 0.065 vs 0.054).

| ΔT_glob (K) | marginal amp(ΔT) | level ratio T_ant′/ΔT |
|---|---|---|
| 0.5 | 0.86 | 0.77 |
| 1.0 | 0.99 | 0.85 |
| 2.0 | 1.12 | 0.95 |
| 3.0 | 1.17 | 1.02 |
| 4.0 | 1.18 | 1.06 |

## 5. Caveats

- The ΔT→0 intercept (0.655) is extrapolation: trend ratios are unstable below ~0.6 K of
  global warming, so the first ~0.6 K of the integral leans on the fitted form (shifting
  the intercept to 0.85 moves the 2 K level ratio only ~+0.02).
- One member per model; a few non-r1i1p1f1. Trend ratios pre-~1990 are internal-variability
  noise (masked in the fit).
- sftlf treats ice shelves inconsistently across models; our "land south of 60°S" is a
  proxy for the ice sheet, and Xie's actual mask is unstated (our cap attribution is
  inference from numerical reproduction, not from their methods).
- The equation form assumes the marginal depends on warming *level*, not rate — supported
  by the ssp245/ssp585 collapse, but overshoot/paleo trajectories are untested.

## 6. Questions for you

1. **Reference frame:** can you confirm the DAIS 0.8365/−15.42 regression is
   continent/ice-core-referenced Antarctic temperature (Shaffer 2014 lineage)? The
   land-vs-cap correction in §3 hinges on it.
2. **Structure:** any objection to a warming-dependent map (proposal B) interacting with
   the runoff-line parameterization — anything downstream that assumes linearity of
   T_ant in ΔT_glob?
3. **Prior width:** is admitting the equilibrium value at +1.3σ (proposal A) acceptable
   for a "transient" calibration, or would you argue for the state-dependent map instead
   and drop the transient/equilibrium dichotomy altogether?
