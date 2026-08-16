# Where Ladrillo stands — observations, BRICK 2.0, MAGICC-SLR, FACTS, and structural form

**Basis: L11** (the D1+D2 change set, accepted 2026-08-15), 10k-member subsample,
2000 draws, FaIR-mean forcing. Hindcast rel. 1995-2005; projections rel.
1995-2014. All numbers regenerated 2026-08-16 from the `--tag=`-driven chain.

Sources: `outputs/postpred_L11_{bias,coverage}.csv`,
`outputs/scope_ladrillo_vs_brick20_scorecard_L11.csv`,
`outputs/ladrillo_model_comparison_L11{,_spread}.csv`,
`outputs/diag_l10_vs_l11_projection.csv`.

---

## 0. The one-paragraph version

Ladrillo = MimiBRICK v2.0.0 with **two components replaced** (glaciers,
Greenland) and three inherited unchanged (AIS/DAIS, thermal expansion,
land-water storage). Against observations it is a large improvement on stock
BRICK in every module it replaced — AIS and Greenland RMSE fall by 12-33×, and
glaciers by 2.7× — while thermal expansion is now at parity rather than the
regression it was. Against MAGICC-SLR and FACTS it sits **at or below the low
end of the multi-model range at 2100 for SSP1-2.6 and SSP2-4.5, and at the high
end for SSP5-8.5**, and that entire scenario span is carried by one inherited
term: DAIS fast dynamics. The two components with the weakest structural
justification are the two that were *not* replaced.

---

## 1. Against observations (hindcast 1900-2026, L11)

| component | mean bias (cm) | 90% param coverage | reading |
|---|---|---|---|
| AIS | −0.003 | 0.85 | essentially unbiased, band well calibrated |
| glaciers | +0.009 | 0.80 | unbiased; D2 raised coverage from 0.64 |
| Greenland | +0.005 | 0.60 | unbiased, band somewhat narrow |
| thermal expansion | **+0.175** | **0.31** | **the weak module** |
| total | +0.646 | 0.24 | **OUT OF SAMPLE** — D1 dropped it from the likelihood |

Two caveats that must travel with this table:

- **The total is out-of-sample in L11.** D1 removed the Dangendorf total from the
  likelihood, so the total has no calibrated error model and its +0.65 cm bias is
  a *prediction*, not a fit. That bias is **entirely pre-1950** (1900-1919
  +1.125, 1920-49 +0.918, 1950-92 +0.617, **1993-2026 +0.130 — better than L10**).
- **Coverage is parameter-band coverage**, not predictive. Adding the calibrated
  AR(1)+obs error model takes every in-sample component to ≥0.97. The AR(1)
  noise model is itself known to be misspecified — see
  `project_ladrillo_noise_model_misspecified`.

**Thermal expansion is the standing observational weakness.** Coverage 0.31
against a nominal 0.90 says the parameter band is roughly 3× too narrow for the
residual — the error model, not the physics, is absorbing the misfit.

---

## 2. Against BRICK 2.0 (same targets, same baseline, full record)

RMSE in cm; ratio < 1 favours Ladrillo.

| component | Ladrillo | BRICK 2.0 | ratio | coverage L / B |
|---|---|---|---|---|
| AIS | 0.032 | 1.176 | **0.03** | 0.82 / 0.31 |
| Greenland | 0.058 | 0.723 | **0.08** | 0.54 / 0.22 |
| glaciers | 0.328 | 0.894 | **0.37** | 0.53 / 0.47 |
| thermal expansion | 0.318 | 0.324 | 0.98 | **0.29 / 0.96** |
| TOTAL | 0.685 | 1.820 | **0.38** | 0.23 / 0.25 |

- **The replaced modules are where the gains are**, which is the expected result
  and worth stating as a validation of the replacement rather than a surprise.
- **TE reached parity on RMSE under L11** (0.98; it was 1.19 on L10, i.e. a
  regression). D2's steric discrepancy term is what closed it. But **BRICK 2.0
  still beats Ladrillo 3× on TE coverage** (0.96 vs 0.29) — BRICK 2.0's `te_α`
  posterior is nearly 4× wider (sd 0.0289 vs 0.0075), so it is buying coverage
  with an uninformative parameter, not with a better model. Read RMSE and
  coverage together here; neither alone is honest.

---

## 3. Against MAGICC-SLR and FACTS — medians at 2100 (cm, rel. 1995-2014)

FACTS is per-workflow/module; ranges below span its modules.
**Band widths are not comparable** — Ladrillo and BRICK 2.0 run on mean forcing
(posterior-parameter spread only); MAGICC and FACTS carry climate spread too.

| component | SSP | Ladrillo | MAGICC | FACTS range | BRICK 2.0 | position |
|---|---|---|---|---|---|---|
| glaciers | 1-2.6 | **7.8** | 10.4 | 8.9-9.2 | 12.0 | below all |
| | 2-4.5 | **9.9** | 12.5 | 11.4-12.2 | 13.5 | below all |
| | 5-8.5 | **14.1** | 15.3 | 15.5-17.7 | 16.5 | below all |
| Greenland | 1-2.6 | 6.3 | 6.4 | 5.5-13.0 | — | mid-range |
| | 2-4.5 | 8.3 | 9.3 | 8.0-14.4 | — | low-mid |
| | 5-8.5 | 13.8 | 13.5 | 12.7-20.3 | — | low-mid |
| AIS | 1-2.6 | 4.7 | 3.7 | 6.3-11.9 | — | below FACTS |
| | 2-4.5 | 5.9 | 11.2 | 5.5-13.7 | — | bottom |
| | 5-8.5 | **37.2** | 39.1 | 4.0-28.6 | — | **above all FACTS** |
| thermal exp. | 1-2.6 | 13.7 | 11.1 | 14.1 | — | close to FACTS |
| | 2-4.5 | 18.0 | 16.6 | 18.8 | — | close to FACTS |
| | 5-8.5 | 27.0 | 27.9 | 28.8 | — | close to both |
| **TOTAL** | 1-2.6 | **35.1** | 35.6 | 39.8-53.5 | — | = MAGICC, below FACTS |
| | 2-4.5 | **45.3** | 53.2 | 48.7-67.9 | — | below all |
| | 5-8.5 | **95.1** | 97.8 | 64.9-91.9 | — | ≈ MAGICC, above FACTS |

**Scenario spread, SSP1-2.6 → SSP5-8.5 at 2100 (cm):**

| | Ladrillo | MAGICC | FACTS | BRICK 2.0 |
|---|---|---|---|---|
| glaciers | +6.3 | +4.8 | +6.5 / +8.5 | +4.5 |
| Greenland | +7.5 | +7.1 | +6.3 to +7.3 | — |
| AIS | **+32.5** | +35.4 | **−2.3 to +19.7** | — |
| total | **+59.9** | +62.3 | +25.2 to +50.7 | — |

### Three readings

1. **Ladrillo tracks MAGICC-SLR closely and diverges from FACTS.** Totals agree
   with MAGICC to 0.5 cm (ssp126), 2.7 cm (ssp585); the ssp245 gap is 7.9 cm.
   Both sit far outside the FACTS AIS spread. This is a *structural family*
   effect — both are simple-model emulators with an explicit AIS instability
   term; FACTS's AIS modules mostly are not.

2. **The glacier module is now low against every comparison source, in every
   scenario.** On L10 it was below-all in 2 of 3 scenarios; **D2 pushed it below
   in all 3 and widened the gap** (−1.0 to −1.2 cm). The scenario *spread*
   (+6.3) is healthy — mid-range, and the saturation pathology the Mengel form
   was adopted to fix is genuinely fixed. But the *level* is low and getting
   lower. This is a live concern, not a settled result, and it interacts with the
   open D2 question in §5.

3. **All of Ladrillo's high-end SSP5-8.5 total comes from AIS.** Remove the AIS
   column and Ladrillo is at or below the FACTS range everywhere. The +32.5 cm
   AIS scenario response versus FACTS's −2.3 to +19.7 is the single largest
   structural disagreement in the whole comparison.

---

## 4. Structural form against the underlying science

| component | status | form as implemented | commitment |
|---|---|---|---|
| glaciers | **REPLACED** | 3 reservoirs (R19/SLOWP/FAST), `S_eq = a(1−e^{−b(T−T_off)})`, Nauels-2017 kinetics `dS/dt = κ(S_eq−S)·max(T−T_eq,0)^ν` | **finite, saturating at `a_b`** |
| Greenland | **REPLACED** | two channels (SMB/dynamic), `eq = clamp(c1·T + c0, 0, v0)`, rate `= clamp(α·T + β, 1e-9, 1)` | linear-then-clipped |
| AIS | inherited | DAIS geometric ODE (radius/volume) + **constant-rate** disintegration above a temperature threshold | **none** |
| thermal exp. | inherited | `te = te_s₀ + te_α·(OHC(t) − OHC(t₀))` — one scalar | none (inherits the climate module's) |
| LWS | inherited | random walk with drift, identically 0 before 2018 | none; climate-independent |

### Where the form is defensible

**Glaciers — the strongest structural upgrade in the model.** A finite,
temperature-dependent equilibrium is the physically correct shape: glaciers have
finite volume and an equilibrium-line altitude that responds to temperature.
Stock BRICK's Wigley-Raper form has *no* finite equilibrium — any sustained
`T > teq` drains the reservoir to `v₀` — the "commit-everything pathology" the
replacement was built to fix. The three-reservoir split with per-block drivers
also gives the module a scenario response that the single reservoir could not
produce. Provenance is explicit in code: Mengel 2016 (PNAS 113:2597) for the
equilibrium curve, Nauels 2017 (MAGICC Eq. 3) for the kinetics, Farinotti 2019 /
Hock 2023 for the volume priors.

**Thermal expansion — structurally the simplest, and in projection the best
behaved.** One scalar times cumulative OHC, and it lands within 0.2-1.8 cm of
FACTS's `tlm` in all three scenarios. There is little to criticise in the form
*given* that OHC is supplied exogenously.

### Where the form is weak, and it is the inherited half

**Greenland — the equilibrium has the wrong shape.** `eq = c1·T + c0` clipped at
`v₀ = 7.42 m` is **linear in regional temperature**. With posterior `c1 ≈ 0.033
m/K` the cap never binds over any plausible range, so in practice the commitment
is unbounded-linear. The ice-sheet literature says the GrIS equilibrium is
strongly nonlinear with threshold behaviour and multiple stable states. This is
exactly why **the 2300 commitment sits 19-24× below Bochow** and why the model is
unidentified along the φ·Leq ridge (14.6 → 58.3 cm at identical hindcast fit).
Option C — using the PISM equilibrium ladder as `V_eq` — was tried offline and
**failed**. This is the one *confirmed* structural failure in the model. Note the
hindcast cannot see it: Greenland's hindcast bias is +0.005 cm.

**AIS — the largest form risk, and it is a switch rather than a process.** Above
`temperature_threshold`, DAIS disintegrates at a **constant rate**
`−λ·24.78e15/57`, independent of remaining volume. Three consequences follow
directly:
- **No equilibrium exists** for the fast-dynamics term.
- **Hard annual quantisation** — the threshold is tested once per year, so a
  perturbation shifts the *crossing year* discontinuously
  (`project_dais_fastdynamics_quantization`).
- It produces the +32.5 cm scenario response that puts Ladrillo above every
  FACTS AIS module, and it is the direct cause of the AIS-geometry block never
  mixing (`ais_iceflow0` R̂ **2.449**), which is why L11's acceptance carries an
  explicit **MAY-NOT** clause against parameter-level AIS inference.

Note also that no Shaffer/DeConto citation appears anywhere in the installed
MimiBRICK v2.0.0 source for this component — the DAIS-side literature anchors
(Xie 2022 for the amplification prior, Rignot 2019 for SMB) live in the Ladrillo
calibrator, not in the form itself.

**LWS — not modelled at all.** A climate-independent random walk, zero before
2018, with **no sampled parameters** and no code-level provenance for its
`N(0.0003, 0.00018)` m/yr rate. It contributes 2.6 cm at 2100 and **8.5 cm at
2300** with zero climate dependence and zero uncertainty propagation. Small near
term; a real gap at 2300, where it is comparable to the entire Greenland
contribution under SSP1-2.6 (8.3 cm).

### Two fixed parameters worth knowing about

- **`gic_nu_b` is not sampled** — fixed offline per block, because "the hindcast
  cannot identify ν" (free arms rail it to ~0). One shape parameter per glacier
  reservoir is therefore set, not inferred.
- **The glacier reservoirs are melt-only** (`exc = max(T − T_eq, 0)`), so `S` is
  monotone non-decreasing — no regrowth. Justified as accumulation-limited
  asymmetry; Nauels 2017 states no convention either way.

---

## 5. Standing weaknesses, ranked

1. **Greenland's equilibrium form** — the one confirmed structural failure.
   Linear-in-T where the science says threshold/nonlinear; 19-24× below Bochow at
   2300; invisible to the hindcast. Needs an external Leq(T) target.
2. **AIS fast dynamics** — a volume-independent constant-rate switch. Drives the
   entire SSP5-8.5 high end, the disagreement with all FACTS AIS modules, the
   annual quantisation, and the non-mixing that bounds what the posterior may be
   used for.
3. **Glacier level is low against all four comparison sources** in all three
   scenarios, and D2 made it lower. The *spread* is healthy; the *level* is not.
4. **Thermal-expansion coverage 0.31** — the parameter band is ~3× too narrow;
   the misfit is absorbed by a discrepancy term and an error model, not a
   mechanism.
5. **`thermal_alpha` moved +1.31 L10 sd under the change set** (mix ratio 19.7,
   81% attributable to D2), **away from the precision-weighted optimum 0.1395
   and toward the zero-mean-bias one 0.1771**. L10 sat between them, so this is
   an era trade: early-century fit bought with modern-era fit, and the projection
   is anchored on the era that got worse. **Which D2 stream causes it is under
   test** (`julia/run_d2_stream_attribution.sh`, 8 chains, running 2026-08-16).
6. **LWS is unmodelled** — matters only at 2300, but there it is ~8.5 cm.
7. **The AR(1) noise model is misspecified** — see
   `project_ladrillo_noise_model_misspecified`; never quote the "56%" figure.

---

## 6. What the posterior may and may not be used for

Carried unchanged from the L11 acceptance (handoff 15b):

- **MAY** — projected SLR and anything derived from it. Projected SLR converges:
  R̂ 1.002 @2100, 1.005 @2150, ESS ~1300.
- **MAY NOT** — parameter-level inference on the AIS-geometry block, whose
  pooled marginals are a mixture of four chains that never merged (18 marginals
  unconverged; `ais_iceflow0` R̂ 2.449).
