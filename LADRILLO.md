# Ladrillo — the baseline

The single definition of what "Ladrillo" currently means: which model, which
posterior, which files, what may be said about them, and what is not in it.
If you are picking this up cold, read this file plus
`notes/handoff_2026-09-03b_docx_canonical_and_pulse_next.md` (the current pickup
document); everything else is detail.

**Status 2026-09-02.** Branch `ladrillo-dev`. Posterior **L24 — champion on all six modules
since 2026-09-02** (`benchmark/champions.json`): L23's configuration with the Antarctic
amplification prior at its shipped width **N(1.09, 0.180)**, the measured 34-model CMIP6 spread.
On fit it is indistinguishable from L23 — **3 of 304 cells** change verdict for a 1.8× wider
prior — so it was promoted on **provenance, not skill**.

⚠ **L24 vs L21 is NOT like-for-like.** Their amp priors differ (N(1.09, 0.180) vs N(0.95, 0.10)),
so the gap between those vintages is a **prior change, not a model improvement**. The L21→L23 amp
move was a **dropped `--amp-mu=0.95`** — not the glacier law, not the proposal covariance.
Post-mortem in §6.

⚠ **This header has named four champions in a fortnight** (L14 until 08-29, L21 until 09-01,
L23 until 09-02). L14's *configuration* survives in the L21→L24 line; L14 as a *posterior* does not.
⚠ **Numbers in §4 have NOT been regenerated past L14 — see §4.**

Both replaced components are shipped and gated in `run_ladrillo_tests.sh`; the convergence
certificates were cut at the **L14** vintage and have not been re-cut since. **Greenland has its
own module memo** — `notes/memo_2026-08-23_greenland_module.md` — which is the authority on that
component; this file gives the model-level view and does not duplicate it.

> **This is no longer "Ladrillo 1.0".** That was the 2026-08-13 baseline (tag
> `ladrillo-1.0`, posterior L10, whole-sheet `greenland_ab`, branch
> `brick-mengel-vnext`), and the Greenland component, its parameterisation, its
> posterior and its projections have all changed since. **Whether the current state
> earns a `2.0` tag is Marcus's call and has not been made** — no tag has been cut.

---

## 1. What the model is

**Ladrillo = MimiBRICK v2.0.0 with two components replaced.**

| component | Ladrillo | source |
|---|---|---|
| glaciers & small ice caps | **three-reservoir Mengel-type emulator** — R19 (RGI 19), SLOWP (RGI 03/09/07/06) and FAST (the other 13 — **18 of 19 RGI regions**, see below), each on its OWN area-weighted driver | `julia/glaciers_nu3_component.jl` |
| Greenland | **two-basin Mouginot-sector A+B** — two-channel relaxation (fast/SMB + slow/dynamic) sharing an equilibrium commitment through `gis_f`, partitioned over active (SW+CW+CE+SE+NW) and high (NO+NE) basins, on a **regional** south-Greenland driver, **plus a volume tap** | `julia/greenland_3basin_component.jl` |
| Antarctic, thermal expansion, LWS | stock MimiBRICK v2.0.0 | MimiBRICK |

Glacier reservoirs integrate `S_eq,b = a_b (1 − exp(−b_b (T_b − T_off,b)))` with
`dS_b = min(κ_b · exc^ν_b, 1)(S_eq,b − S_b)`; `ν_b` is **fixed**, not sampled
(the hindcast cannot identify it).

⚠ **The three blocks cover 18 of the 19 RGI first-order regions — `RGI 05` (Greenland Periphery) is
excluded, and the two peripheries are treated ASYMMETRICALLY.** Frederikse 2020's glacier target
excludes **both** peripheral regions (05 and 19), which is why the scope-matched inventory is
0.221 ± 0.057 m SLE rather than the 0.324 ± 0.084 full-RGI value. Ladrillo drops 05 entirely — it
falls inside the Greenland ice-sheet mask, so carrying it here would **double-count against the
Greenland module** — but keeps 19 as its own block, because GlaMBIE (spliced from 2019) does include
it and RGI 19's ice is not inside DAIS's scope the way 05's is inside the Greenland mask. Hence the
hindcast is scored on **SLOWP + FAST only**, matching the target's scope, while R19 still contributes
to projected totals. Members are in `outputs/extc_block_constants.csv`, which is the source of truth.

Greenland carries **nine** sampled parameters: the five A+B shape/rate parameters,
the slow channel as a reparameterised pair `(gis_slow_ell, gis_slow_w)`, the
amplification `gis_amp`, and one basin rate scale `gis_s_high` (log₁₀). Basin volume
shares, `gis_v0 = 7.42 m`, `gis_g` and the channel-ordering wedge are fixed structure.
**Full detail, priors, and per-parameter numbers: the module memo §2–§3.**

**The external interface is GMST + OHC only.** Both regional drivers are built inside
the model from observed series plus an anchor-preserving splice, which is what keeps
Ladrillo a drop-in replacement rather than a model needing its own climate input. Do
not add an input to the interface without deciding that deliberately.

### The Greenland amplification law (projection-side)
The post-2024 Greenland splice uses `amp(ΔT) = amp_draw × S(ΔT)`: the **observed
level**, the **CMIP6 shape**. `S` is a PCHIP through pooled binned medians of 40
CMIP6 models over 0.75–2.75 K, held flat outside, normalised to 1 at
`ΔT_eff = 0.940 K`. **Projection-side only** — `regional_driver` returns observed
regional T for every year of the observational record, so the law is exactly
hindcast-inert and no chain re-run was needed.

⚠ **This law carries the model's largest known projection-side defect, and as of 2026-08-24 it is
REPORTED rather than corrected.** At 2100 our Greenland runs ~1.31× the ISMIP6 median through the
law, but lands on it (0.99×, n = 5) when driven by each GCM's own Greenland temperature — so the
defect is in the **driver**, not the ice response, and within the driver it is the **level**, not
the shape. Three fixes were tested and all three failed:

- a **τ relaxation**, whose preferred timescale tracks the *observational product* rather than any
  decadal mode;
- **re-anchoring to Berkeley Earth**, which is the worst of the three products against the observed
  melt record *and* is the calibration driver, so switching it is a recalibration;
- a **glacier-module counterpart**, which does not exist — the glacier blocks sit *below* CMIP6 at
  every baseline frame.

The premise is itself frame-dependent: rebasing both sides consistently gives obs/CMIP6 = 1.274× on
1850-1900 and **below 1 on all four alternatives**. So: report the bias, quantified and
one-directional. It is worth ~4 cm at ssp585 2100 against an AIS spread of 50.6 cm there. Module
memo caveat 4.

Constants and shape table: `LADRILLO_GIS_*` in `julia/ladrillo_projection.jl`,
`outputs/gis_amp_shape{,_meta}.csv`.

### The Greenland volume tap — ON by default
`GIS_TAP_CELL = (onset 4.69 K, V 5.64 m, τ 800 yr, ramp 1.0 K, stages 2, whole-sheet)`.
A two-stage discharge cascade opening above a **global** temperature onset. It is a
**prior specification, not a fit**, and is exactly likelihood-inert (the calibration
tops out at 1.385 K). Since 2026-08-23 it is the **default arm** of the projections;
`--no-tap` produces the base model. It moves ssp585 after 2100 and **nothing else** —
tapped minus untapped is `0.000e+00` at every year ≤ 2100 and at every year on both
cool scenarios. Module memo §6.

---

## 2. The posterior

**`data/MimiBRICK/parameters_subsample_brick_mengel_L14.csv`** — 10 000 draws
subsampled from 4 × 2M chains (seeds 2026–2029), 57 columns. **Gitignored**: it exists
only on this machine. Regenerate with

```bash
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=L14 --accept-slr
```

(needs `outputs/mcmc/slr_convergence_L14.csv`, which IS tracked).

### ACCEPTED ON THE DELIVERABLE — and what that permits

Cross-chain convergence of **projected SLR** passes; **20 parameter marginals do
not**. Certificate: `outputs/mcmc/slr_convergence_L14.csv`.

| | R̂ | ESS | sd(medians) | mean(sd within) | ratio |
|---|---|---|---|---|---|
| SLR@2100 | 1.017 | 953 | 0.603 cm | 11.804 | 0.051 |
| SLR@2150 | 1.015 | 967 | 3.053 cm | 32.350 | 0.094 |

- **MAY** be used for projected SLR and anything derived from it.
- **MAY NOT** be used for parameter-level inference. The failing marginals are
  mixtures of chains that never merged, not posteriors. No credible intervals, no
  scatter plots, no cross-vintage marginal comparisons for the **AIS geometry** block
  — worst axis `ais_iceflow0`, whose R̂ has run **2.2–2.4 across recent vintages**
  (2.359 at L10, 2.449 at L11), plus `antarctic_alpha` and `ais_slope`. The L14 value has not
  been re-measured — quote a vintage with its number, or quote none.
- **The Greenland half of this caveat is SUPERSEDED.** Ladrillo 1.0's rule named four
  failing Greenland marginals with chain medians spanning 2.8×. At L14 the block is
  **3 of 9 failing, all marginally, worst R̂ 1.075**, and the slow-rate median spread
  is 1.30×. Certificate: `outputs/mcmc/gis_block_convergence_L14.csv`; table and the
  native-scale caveat in the module memo §4. **The projections-only rule still
  stands — it is set by AIS, not by Greenland.**
- **2150 is still the worst horizon, but the margin has collapsed and 2100 has got
  WORSE.** Between/within ratios for the total
  (`outputs/diag_iceflow0_propagation_L14.csv`):

  | | 2100 | 2150 | 2300 |
  |---|---|---|---|
  | L10 | 0.009 | **0.137** | 0.051 |
  | **L14** | **0.051** | **0.094** | 0.081 |

  2150 improved 1.5×, 2100 degraded **5.7×**, and 2300 is now close behind 2150. The
  L10 shorthand "2150 is the bad one, 2300 is better" no longer describes the model.
  R̂ is mean-based and reads ~1.02 at every horizon regardless.

---

## 3. Canonical files

| role | file |
|---|---|
| **projection kernel** (the one place that maps a draw → MimiBRICK) | `julia/ladrillo_projection.jl` |
| calibrator | `julia/calibrate_mcmc_ext.jl` (`--gis-ordered --gis-basins2`) |
| SSP projections deliverable | `julia/project_ssps_components_ladrillo.jl [--tag=] [--no-tap]` |
| — tapped (DEFAULT, the shipped model) | `outputs/ssps_components_2300_<TAG>_tap4p69K_V5p64m_tau800_n2_ws.csv` |
| — base arm (`--no-tap`) | `outputs/ssps_components_2300_<TAG>.csv` |
| hindcast deliverable | `julia/posterior_predictive_ladrillo.jl [--tag=]` → `outputs/postpred_<TAG>_{components_timeseries,bias,coverage}.csv` |
| memo figures | `python/plot_ladrillo_memo_figures.py [--tag=] [--no-tap]` → `figures/ladrillo_<TAG>_fig{1,2,3}_*.png` |
| comparison vs FACTS / MAGICC / BRICK 2.0 | `python/ladrillo_model_comparison.py [--tag=] [--no-tap]` |
| SLR acceptance gate | `julia/diag_slr_convergence_by_chain_ladrillo.jl` |
| Greenland block convergence | `julia/diag_gis_block_convergence.jl` |
| Greenland priority-ladder scorecard | `julia/diag_gis_cell_vs_priority_ladder.jl` |
| the tap cell, from python | `gis_targets.tap_cell()` — parses the Julia constant |
| Greenland 2300 target bands | `python/gis_targets.py` (`lit` vs `matched`, default matched) |
| amp law: shape | `python/diag_gis_amp_cmip6.py`, anchor `diag_gis_amp_anchor.py`, 2100 decomposition `diag_gis_2100_bias_decomp.py` |

**THE ARM IS IN EVERY FILENAME.** A tapped and an untapped 2300 projection differ by
~46 cm on ssp585 and are otherwise identical in shape, units and header. Which arm you
get is chosen by an argument, never by which name is on disk — and the untapped file
keeps the plain name because four consumers read it meaning the base model.

Every driver **includes the kernel** rather than re-deriving the parameter map. That
rule exists because the copy-pasted version drifted onto the wrong Greenland once
already; a diagnostic that re-implements the mapping can certify a model different
from the one the projections use.

### Reproduce the deliverables

⚠⚠ **`deliverables/LadrilloUpdateDescription_L24.docx` is CANONICAL** (Marcus, 2026-09-03) —
Marcus edits it directly in Word; `LadrilloUpdateDescription_FILLED.md` is a GENERATED
pandoc intermediate, never a hand-maintained source. Before editing the deliverable's text:
`python3 deliverables/sync_filled_from_docx.py --verify`. Skipping that pre-sync reverted
Marcus's own edits once already.

```bash
./run_ladrillo_tests.sh
```

Ten steps, all must pass before any number leaves the repo: data assembly → calibrator
glacier path → projection kernel → Greenland A+B component → calibrator Greenland
wiring → projection-kernel Greenland (incl. the amp law) → 2-basin variant selection →
3-basin nesting and partition → channel-ordering wedge → the shipped tap cell.

```bash
TAG=L14
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl 2000 --tag=$TAG
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl 2000 --tag=$TAG --no-tap
julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl 2000 --tag=$TAG
source ~/climate-env/bin/activate
python3 python/ladrillo_model_comparison.py --tag=$TAG
python3 python/plot_ladrillo_memo_figures.py --tag=$TAG
```

The base arm is needed as well as the tapped one: `test_gis_tap_wiring.jl` measures its
2150 tolerance from it, and several Greenland diagnostics score against it.

---

## 4. Headline numbers

⚠ **THESE ARE L14 NUMBERS AND KEEP THAT LABEL UNTIL RE-RUN.** The champion has moved three times
since (L21, L23, **L24**) and this table has been regenerated on none of them. Do **not** relabel
them.
⚠ **FaIR-MEAN forcing = a FIXED driver**, so this band is posterior-parameter spread only and
carries no forcing uncertainty. It is **not** the JOINT band, and it is not comparable in
width to MAGICC or FACTS. See the band-provenance table in the model document.

Total sea level, cm rel. 1995–2014, FaIR-mean forcing, **L14 tapped** (the arm shipped at
that vintage), 2000 draws:

| ssp | glaciers | gis | ais | te | **total (p17–p83)** |
|---|---|---|---|---|---|
| SSP1-2.6 @2100 | 7.92 | 6.48 | 4.40 | 13.70 | **35.1** [33.7, 36.5] |
| SSP2-4.5 @2100 | 9.99 | 8.46 | 5.58 | 17.95 | **44.9** [42.7, 59.0] |
| SSP5-8.5 @2100 | 14.29 | 13.90 | 37.07 | 26.92 | **94.7** [81.5, 110.7] |
| SSP1-2.6 @2300 | 12.39 | 10.08 | 13.47 | 22.69 | **67.1** [64.3, 70.0] |
| SSP2-4.5 @2300 | 19.08 | 18.32 | 131.35 | 41.85 | **219.1** [107.8, 323.0] |
| SSP5-8.5 @2300 | 27.62 | 95.74 | 281.69 | 99.74 | **513.7** [443.3, 592.8] |

Bands are **posterior-parameter spread only** — the forcing is FaIR-mean per SSP, so
there is no climate spread in them. Say so wherever they are compared to FACTS
workflows, which include it.

⚠ **Quote the file, not the promotion note.** The L14 promotion entry records
SLR@2100 = 45.01 cm; the 2000-draw deliverable gives **44.9465**. Chain-level median
vs thinned-projection median — the gap is a tenth of the between-chain scatter at that
horizon. Not a discrepancy to chase, but say which you mean.

Scenario spread (SSP1-2.6 → SSP5-8.5) at 2100 against the comparison arms
(`outputs/ladrillo_model_comparison_L14_spread.csv`):

| component | Ladrillo | arms |
|---|---|---|
| glaciers | 6.37 | FACTS 6.52 / 8.48, MAGICC 4.85, BRICK 2.0 4.47 |
| **Greenland** | **7.42** | FittedISMIP 6.34, MAGICC 7.09, bamber19 7.23, emuGrIS 7.26 |
| Antarctic | 32.67 | ar5AIS −2.3, emuAIS −0.2, larmip 2.5, bamber19 8.9, deconto21 19.7, MAGICC 35.4 |
| thermal expansion | 13.22 | tlm 14.77, MAGICC 16.79 |
| total | 59.62 | FACTS workflows 25.2–50.7, MAGICC 62.3 |

**Greenland is in family; the Antarctic is the outlier** — and it is simultaneously
the block that fails to converge and whose tail the red team recorded as prior- rather
than data-driven. Report components, not just totals: a reader comparing totals sees
AIS (high) and TE (low) cancel.

**At 2300 on ssp585 the picture has inverted since 1.0.** Greenland is **18.6%** of
the total with a p05–p95 of **26.9 cm**; Antarctic is **54.8%** with **252.3 cm**
(and at SSP2-4.5 an AIS band of [15.4, 296.1] cm — a 19× range, wider than the whole
total's spread). **Greenland is now the smallest-uncertainty ice component in the
model. The leverage is AIS.**

### The overshoot penalty, and the pair you must use to measure it

⛔ **THE NATIVE `ssp534over`/`ssp126` PAIR CANNOT MEASURE THIS.** Our SSP5-3.4-OS crosses
**below** SSP1-2.6 in **2127** and ends **0.126 K cooler**, so the reference arm becomes the
warmer one and catches up on its own. That artifact alone closes the whole penalty and inverts
its sign. Use **`ssp534overMATCH`** = `ERF_126 + max(ERF_534 − ERF_126, 0)`, built in *forcing*
space (`build_fair_cube_matched_dt.py`, FaIRtoFrEDI `claude/calib160-migration`); GSAT then
relaxes back from **above** (+0.042 K @2150, +0.020 @2300). ⚠ Idealised — never label it
SSP5-3.4-OS.

Total penalty, paired median, cm (`python/diag_matched_dt_penalty.py`):

| | native pair | matched pair |
|---|---|---|
| Ladrillo L24 @2300 | −1.23 | **+2.21** |
| BRICK 2.0 @2300 | −0.52 | **+2.57** |

**Ladrillo is mid-pack, at 2300 as well as 2150.** FACTS was run to **2300** on 2026-09-02 — our
module set runs there unchanged, 26 outputs per arm, same file set as the 2150 twins — so the
comparison reaches SLEIP's own headline year. Paired median penalty, cm:

| | 2100 | 2150 | **2300** |
|---|---|---|---|
| wf4 Bamber SEJ | 2.72 | 2.40 | **1.65** |
| **Ladrillo L24** | **4.05** | **3.32** | **2.21** |
| BRICK 2.0 | 3.63 | 3.35 | 2.58 |
| wf1f IPCC AR5 | 3.18 | 3.21 | 3.39 |
| wf3f DeConto/Kopp | 3.70 | 4.06 | 4.97 |
| wf2f LARMIP-2 | 4.22 | 5.48 | 5.39 |

FACTS is independent of the BRICK line on both glaciers and ice sheets, so this corroborates the
Ladrillo/BRICK agreement rather than echoing it.

⭐ **The models split 3–3 on whether the penalty decays.** 2300/2100 ratio: Ladrillo **0.55**, Bamber
SEJ 0.61, BRICK 2.0 0.71 — against IPCC-AR5 1.07, LARMIP-2 1.28, DeConto/Kopp 1.34. Ladrillo decays
fastest, but an independent process-based SEJ workflow sits right beside it, so a decaying overshoot
penalty is **not a Ladrillo peculiarity**.

⭐ **The medians agree and the tails do not.** At 2300 medians span **1.65–5.39 cm** (3.3×) while p95
spans **7.1–858.4 cm** (121×). Ladrillo's p95 is 43.3 and BRICK 2.0's 51.3; DeConto/Kopp — the one
workflow that can express MICI — carries a **mean of 107 cm**. The MICI gap is real and lives
**entirely in the tail**.

⚠ **SLEIP reports 0.1–0.3 m at 2300, which is above EVERY model's median here** (largest 5.39 cm).
It sits in the mean/tail region instead — Ladrillo's own mean is 8.94 cm. The likeliest reading is
that their figure is not a median; confirming which statistic it is remains the open item.

⭐ **Antarctica carries this.** The AIS penalty @2300 goes **+0.003 → +0.630 cm** (Ladrillo) and
**+0.174 → +0.793** (BRICK 2.0) between the native and matched pairs — the largest non-TE share in
both. The AIS still **never regrows** on any pathway (zero years of decline after 2100 on both SSPs
and all seven van Vuuren markers); the native zero was the temperature artifact, not an absence of
hysteresis.

---

## 5. Standing caveats — carry these into any report

1. **Antarctic**: quote a distribution, never a median difference. The 2100
   distribution is bimodal (tipped / not tipped) and vintage changes move the
   *tipping probability*, not a level. "X cm lower at SSP2-4.5" is a misleading
   sentence.
2. **Horizon ordering is vintage-specific** — see §2. 2150 is still the worst, but
   2100 degraded 5.7× at L14 and 2300 is now close behind. Re-measure; do not reuse
   L10's "2150 is bad, 2300 is better".
3. **High-warming Greenland**: the criticism that proportional relaxation cannot
   serve both a small historical loss and a huge post-threshold commitment **was
   correct, and the tap is the answer to it** — a separate reservoir is the only form
   that decouples rate from commitment (every completely monotone family is refuted
   by an exact bound). What remains is that the cell sits **on** the melt-rate ceiling
   rather than inside it, and that its **cell-choice envelope is unquantified for the
   cascade**. Module memo caveats 2–3.
4. **`gis_beta_f` is unidentified and consequential**: the data bound it only to
   < ~1e-2/yr. Part of the Greenland band width is prior width.
5. **Noise model**: per-series AR(1) is misspecified on all five streams. D1 dropped
   the Dangendorf total from the likelihood, so **the total is out-of-sample** and has
   no predictive band — mean bias +0.65 cm, entirely pre-1950.
6. **Structural uncertainty is not in the bands** wherever they are compared to FACTS.
   For Greenland the cell-choice term was quantified 2026-08-24: **38.0 cm on
   ssp585@2300, 1.41× the sampled p05–p95**, and it must be reported **one-sided** —
   the shipped 95.7 cm is the *maximum* of the admissible range (median 66.8 cm),
   because the cell was chosen as the largest V clearing the melt-rate band. A
   symmetric ± band around it is wrong in both directions.
7. **Overshoot scenarios: use the matched pair, and never a median alone.** §4. The native
   `ssp534over`/`ssp126` pair inverts in temperature and measures an artifact rather than
   hysteresis; and on the matched pair the models' medians agree to 2.3× while their p95 span 44×.
8. **Greenland-specific caveats do not all live here.** The module memo carries ten,
   including the 2100 amplification bias, the cool-arm separation residual, the
   contradictory 2150 evidence, and the zero moderate-scenario SC-GHG term.

---

## 6. Provenance — superseded vintages

Quarantined, not deleted. Each directory carries a README with the component table and
the reasoning.

| directory | what |
|---|---|
| `outputs/quarantine/20260813_pre_extc_mengel_vintage/` | the pre-extC BRICK-Mengel projections (the "78.02 cm" vintage) |
| `outputs/quarantine/20260813_extc_vintage/` | extC (stock-SIMPLE Greenland), plus the original constant-amp acceptance certificate |
| `outputs/quarantine/20260823_old_tap_cell/` | the first-order tap cell (6.5 K, 2.0 m, 50 yr) — a **refutation** of the form |
| `outputs/quarantine/20260823_v6p0_cell/` | the V = 6.0 m cascade — a **refinement within one family**, not a refutation |

### Why L23's promotion reasoning was retired

L23 was promoted on a 2x2 attributing a **+66 cm** AIS@2300 move to the glacier law. Three
measurements retire that attribution:

* the law is **inert in the calibration likelihood** — ≤7.3e-05 log-units against 1.86 for a 1 %
  glacier-parameter wiggle, a null **with** power;
* **L25** (L23's config with L21/L22's proposal covariance) reads **1.0791 ± 0.0030**, 0.7 se from
  L23, so the covariance is exonerated too;
* the actual cause is a **third dropped flag**. `run_mcmc_L21.sh`/`run_mcmc_L22.sh` pass
  `--amp-mu=0.95`; there is no `run_mcmc_L23.sh`, so L23 onward took the default **1.09**. Prior-mean
  shift **+0.1400**, posterior span **+0.1386**, ratio **0.990** — and `ais_gmst_amp` is
  prior-dominated, so it follows its prior. At 386 cm/unit that is ~53 cm of the move.

The floored glacier law remains a physical improvement; what it does not have is the AIS effect it
was credited with. Every vintage now has a pinned `run_mcmc_<TAG>.sh` with an arm-verification block.

Named posterior constants for superseded vintages: `LADRILLO_POSTERIOR_L12_CSV`
(the last whole-sheet vintage, and the `:ab` test fixture — point `:ab` tests here,
never at the canonical constant) and `LADRILLO_POSTERIOR_L13_CSV` (never promoted;
the only `:basins` posterior, so the fixture for anything needing `gis_s_mid`).

Scripts that **describe** a superseded vintage are pinned to it rather than migrated —
repointing them would make their own prose wrong. `plot_protect_forcing_matched.py` is
the worked example: its constants are named for the 2026-08-21 cell they draw, and it
prints the gap against the shipped cell at import.

---

## 7. Open threads

1. **The Greenland amplification-law estimator** — the bias itself is diagnosed and reported (§1),
   and three fixes are refuted. The one live thread is the estimator: a through-origin secant is not
   baseline-invariant. Reopening the law needs a new idea, not another fix.
2. **`gis_beta_f` prior re-bounding** — does re-bounding to the data support buy anything, or is
   β_f riding a ridge with `f`?
3. **Next calibration** — collects (2) and an explicit discrepancy term for the noise model into
   ONE spec, rather than changes that each invalidate the last.
4. ⭐ **Which statistic is SLEIP's 0.1–0.3 m?** One fact, and it decides whether our overshoot
   penalty disagrees with theirs at all (§4). Highest-value open item in this file.
5. ⭐ **How deep is the real SSP5-3.4-OS overshoot?** Ours has a peak excess of only **+0.311 K**
   over SSP1-2.6. If the published pair is nearer 0.5–0.6 K, much of any residual gap is scenario
   depth rather than model physics.

Also owed: ν sensitivity once; a refit with the four glacier set-asides at prior centres; and a
decision on whether the current state gets a `2.0` tag.

### Settled — do not re-derive

| question | verdict |
|---|---|
| Is the floored glacier law why Ladrillo recovers from an overshoot? | **No**, ruled out *with power*: ≤6.2e-05 cm against a 0.008–0.068 bar (`diag_gic_regrow_penalty.py`) |
| Does Ladrillo's Antarctica regrow unrealistically fast? | **No — it never regrows at all**; zero years of decline after 2100 on both SSPs and all seven van Vuuren markers (`diag_ais_regrowth.py`). At ~1.6 K, continued loss is expected |
| Is sampler work on AIS warranted? | **No.** No ridge to rotate (worst direction `ais_iceflow0` alone, block condition number 8) and the axis explains R² < 0.001 of the projection. A reporting caveat |
| The cascade cell-choice envelope | **Quantified** 2026-08-24 — §5 caveat 6 |
| The Greenland slow-channel reparameterisation | **Done** 2026-08-23. Sampling `(log r_s, tilt)` took the slow channel from R̂ 1.180 / ESS 34 to R̂ 1.005 / ESS 1598 |
| Where is the leverage? | **Antarctica** — §4, and the overshoot decomposition agrees: AIS carries the largest non-TE share of the matched-pair penalty in Ladrillo *and* BRICK 2.0 |
