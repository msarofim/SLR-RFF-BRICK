# Ladrillo (L14) — model description, evaluation, and open concerns
### DRAFT for Marcus. Technical content complete; argument and voice are yours.

**Status.** Ladrillo posterior **L14** is the canonical arm (promoted 2026-08-20).
Prior lineage: MimiBRICK v2.0.0 → Ladrillo. Basis for every projection number below:
**cm, re-referenced to 1995–2014**. Commit `bfc65ae`. Frozen comparison inputs are
hashed in `benchmark/reference/_fixed/manifest.json`.

> **[MARCUS — framing paragraph goes here.]** What Ladrillo is for, and why a standalone,
> global-only, calibrated SLR emulator is the right object for this use. The two positioning
> claims you named — *standalone* (vs MAGICC, which SLR rides inside) and *simpler, global-only*
> (vs FACTS) — belong here in your words.

---

## 1. What changed since BRICK 2.0, and why

Grouped by module. Every row is a change to the model or its calibration, not to tooling.

### 1.1 Glaciers — the largest structural replacement

| change | justification |
|---|---|
| Wigley–Raper glacier module → **Mengel-style S_eq + Nauels-ν transient on T_glac** (`extB3`, 2026-08-07) | W-R saturates: it cannot reproduce the observed 20th-century glacier trajectory and the scenario spread simultaneously. The `d0_glacier_shootout` comparison drove the replacement. |
| **Three-reservoir** glacier block (`extC`, 2026-08-09) | A single reservoir cannot hold both the fast-responding and the long-τ inventory; the 3-reservoir split (R19 / SLOWP / FAST) is what lets the inventory constraint and the transient coexist. |
| **Sampled `gic_amp`** with dataset-informed priors (2026-08-09) | The glacier-area-weighted temperature amplification was pinned; it is a first-order control and was carrying a fixed value with no uncertainty. |
| **Glacier inventory likelihood** + 19th-century flow constraint `S(1900)−S(1850) ~ N(0.020, 0.009) m SLE` (2026-08-06) | Anchors the absolute inventory and the pre-observational flow, which the transient alone does not identify. |
| **GlaMBIE R19 rate** partition (2026-08-13/14) | A claimed 2.59σ covariance tension was **retracted** on checking and re-expressed as a partition — recorded because the retraction is part of the provenance. |

### 1.2 Greenland — from one channel to a constrained multi-basin sheet

| change | justification |
|---|---|
| **Greenland A+B two-channel module** wired into the joint calibrator (2026-08-12) | A single channel cannot represent fast (outlet/dynamic) and slow (SMB) response with different time constants. |
| **`gis_amp` sampled** rather than pinned (2026-08-12) | Identified as *the dominant control on the 2100 projection* — it was previously fixed. |
| **`amp(GMST)` law** for Greenland (2026-08-13) | Reduced the G4 spread 9.80 → 7.37 cm on the L10 posterior. |
| Slow channel **reparameterised as (log r_s, w)** (2026-08-14) | The native (α_s, β_s) coordinates are strongly correlated; the reparameterisation is what makes the block samplable. |
| **Channel-ordering wedge** `--gis-ordered` (2026-08-17) | The prior centre was itself *inverted* (slow faster than fast). Starting there gives `logposterior = −Inf`, every MH ratio `NaN`, and acceptance exactly 0.0. The wedge removes a defect, not a degree of freedom. |
| **Multi-basin** (`--gis-basins2`) + sector shares + pinned reference basin (2026-08-18/19) | The common mode of the basin shares is *exactly degenerate*; pinning the reference basin removes an unidentified direction rather than adding information. |
| **High-basin volume TAP** (2026-08-20/23): V = 5.64 m, τ = 800 yr, onset 4.69 K, 2 stages, whole-sheet | Post-2100 commitment behaviour. Off-by-default and port-tested; fires only above the onset, so cool scenarios are unaffected (visible in the run logs as "the tap will not fire on this scenario"). |

### 1.3 Antarctica — geometry freed, runoff line reparameterised

| change | justification |
|---|---|
| **7 DAIS geometry parameters freed** under a joint paleo prior (2026-07-18) | They were fixed at the prior medoid, which discards both their spread and the paleo correlation structure. The prior is built in standardised form (correlation, cond 2.75) because the raw covariance is ill-conditioned (cond 5.2e13). |
| **Runoff line sampled in its identified direction**: `T_on = −h0/c` instead of (h0, c) | h0 and c enter only as `hR = h0 + c·T_ant`, so they ride an r = 0.9997 ridge. Sampling `T_on` (runoff onset, °C on the DAIS Antarctic-surface scale) replaces that ridge with an identified coordinate; the paleo prior was rebuilt in (T_on, c) coordinates from the same ensemble. |
| **A6: `amp` (GMST → Antarctic) freed** with prior N(0.95, 0.10) | Stock DAIS hard-codes 1.196, the inverted paleo *equilibrium* regression, applied to a *transient* problem. **DECIDED 2026-08-27: keep N(0.95, 0.10)** — see §4.1. |
| **SMB likelihood term** on β_total vs Rignot 2019, area-corrected ×0.888 | The posterior pinned SMB − discharge to −145 ± 15 Gt/yr while each flux was individually ±505/±509 — the textbook input–output degeneracy. One Gaussian term anchors the absolute flux scale. |

### 1.4 Calibration targets and forcing

| change | justification |
|---|---|
| **Dangendorf 2024** GMSL + budget-closure σ inflation (2026-08-12) | The total target's σ is inflated by Frederikse's own budget-closure spread rather than assumed. |
| **LWS extended with JPL GRACE/GRACE-FO mascons** (2026-08-24) | The LWS target was held flat 2019–2026; the GRACE extension replaces held-flat values with data. |
| **Closure σ trend-extended** (2026-08-25) | Same window, same reason. |
| **D1 "drop the total"** / **D2 mean-zero discrepancy basis** on gsic and steric, orthogonal to S(t) (2026-08-14/15) | Prevents the total from double-counting its own components; the D2 basis is orthogonal to the signal, not merely to the constant. |
| **FaIR-consistent conditional weighting**; **mean-forcing** canonical, **joint free-forcing REJECTED** (2026-08-01) | Recorded as a rejected arm, not an untried one. |
| **Over-dispersed chain starts** (`--overdisperse`, 2026-07-19) | Every prior run started all 4 chains at the same θ0, making R̂ anti-conservative: between-chain variance cannot reflect mass no chain reached. |

---

## 2. Hindcast: Ladrillo L14 vs BRICK 2.0 vs observations

![Hindcast](../figures/doc_hindcast_L14_vs_brick20.png)

**FIG 1.** Posterior median and 5–95% band, 1900–2026, against the calibration targets.
*Glaciers are shown against the **delta-corrected** target — the series the model is actually
scored on (`posterior_predictive_ladrillo.jl:206`); the raw `gsic` column is a different object
and plotting it would show a ~1.8 cm bias at 1900 that does not exist.*

**RMSE ratio, L14 ÷ BRICK 2.0 (< 1 = Ladrillo better):**

| component | 1920–1949 | 1950–1992 | 1993–2026 | full |
|---|---|---|---|---|
| Antarctica | **0.003** | **0.008** | 0.548 | **0.026** |
| Greenland | **0.102** | **0.054** | 0.272 | **0.082** |
| Glaciers | 0.359 | 1.011 | 0.345 | 0.370 |
| Thermal expansion | 0.944 | 0.974 | 1.090 | 0.988 |
| **Total** | **0.384** | **0.353** | 0.965 | **0.380** |

Reading: the ice-sheet components are where the rebuild bought almost everything (Antarctica ~38×,
Greenland ~12× on full-window RMSE). **Thermal expansion is unchanged (0.988)** — it was not
rebuilt and does not pretend to be better. Glaciers gain ~2.7× overall but are **level with
BRICK 2.0 in 1950–1992 (1.011)**. In the satellite era the total is 0.965, i.e. the two models
agree where the data are strongest; the gain is in the pre-satellite record.

> **[MARCUS — one paragraph on what the hindcast gain does and does not license.]**

---

## 3. Projections, like-for-like

![Projections](../figures/doc_projection_L14_vs_lit.png)

**FIG 2.** Total GMSL. Full component tables in `outputs/doc_tables_L14.md`.

> ⚠ **Band caveat, and it is the important one.** Ladrillo and BRICK 2.0 run on **mean climate
> forcing**, so their bands are **posterior-parameter spread only**. MAGICC and FACTS bands
> **also carry climate uncertainty**. **Medians are comparable; band widths are not.**

> ⚠ **Coverage is not uniform. Blanks mean *no data*, not zero.** FACTS stops at **2150**.
> **AR6 Table 9.9 has no 2300 row and only totals at 2150.** MAGICC-SLR and BRICK 2.0 run to
> **2300**.

> **AR6 T9.9** = IPCC AR6 WG1 Ch9 Table 9.9 (Fox-Kemper 2021, p.1302), median and *likely*
> (17–83%) range, medium confidence, verified from the chapter PDF. This is the **assessed IPCC
> number itself**, not a FACTS workflow standing in for one.

> **FACTS workflows, identified from the data** (not from the AR6 taxonomy — each 3/3 on three
> statistics): `wf1f` = ar5AIS + FittedISMIP; `wf2f` = larmip + FittedISMIP (**no MICI, no expert
> elicitation** — the pure process workflow); `wf3f` = deconto21/**MICI** + FittedISMIP; `wf4` =
> **bamber19 in both ice sheets = the structured-expert-judgement envelope**.

> ✅ **BRICK 2.0 now carries proper 17–83% bands for every component — no re-run was needed.**
> The earlier glacier-only, 5–95% column was an artefact of `ladrillo_model_comparison.py:62`
> reading the superseded `ssps_gsic_2300.csv`. `project_ssps_components_oldbrick.jl` already
> produces all six components to 2300 with p17/p83, for exactly this reason. **That comparison
> script should be repointed** — flagged, not silently changed, because its output is hashed in
> the benchmark manifest.

### Total GMSL — median [17–83%]

| scenario | horizon | Ladrillo L14 | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f (MICI) | FACTS wf4 (SEJ) | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 35.1 [33.7, 36.5] | 44.0 [32, 62] | 39.8 [31.1, 48.5] | 46.1 [37.0, 61.3] | 43.1 [37.0, 50.0] | 53.5 [35.5, 83.9] | 35.6 [27.4, 48.9] | 39.2 [35.7, 44.2] |
| ssp126 | 2150 | 45.8 [44.0, 47.6] | 68.0 [46, 99] | 60.2 [43.5, 77.6] | 72.0 [55.1, 97.5] | 74.9 [60.4, 96.6] | 83.1 [52.5, 144.2] | 45.9 [34.0, 66.9] | 55.2 [50.3, 62.1] |
| ssp126 | 2300 | 67.1 [64.3, 70.0] | — | — | — | — | — | 66.5 [47.0, 106.5] | 91.2 [82.3, 102.0] |
| ssp245 | 2100 | 44.9 [42.7, 59.0] | 56.0 [44, 76] | 48.7 [39.0, 58.1] | 56.9 [46.0, 75.2] | 55.1 [46.8, 81.2] | 67.9 [45.2, 120.2] | 53.2 [40.6, 70.4] | 70.9 [49.7, 92.9] |
| ssp245 | 2150 | 70.7 [64.7, 127.7] | 92.0 [66, 133] | 80.0 [61.9, 99.3] | 98.1 [79.9, 134.6] | 105.2 [83.1, 300.4] | 111.2 [71.9, 207.7] | 88.1 [64.6, 125.3] | 138.0 [107.6, 173.7] |
| ssp245 | 2300 | 219.1 [107.8, 323.0] | — | — | — | — | — | 186.8 [118.0, 305.9] | 317.5 [253.9, 405.5] |
| ssp585 | 2100 | 94.7 [81.5, 110.7] | 77.0 [63, 101] | 64.9 [54.4, 77.2] | 76.6 [63.6, 101.8] | 91.9 [70.6, 114.9] | 90.8 [60.7, 160.2] | 97.8 [74.8, 132.3] | 104.7 [88.1, 124.9] |
| ssp585 | 2150 | 201.1 [175.2, 231.1] | 132.0 [98, 188] | 117.1 [96.7, 141.5] | 151.7 [123.6, 208.4] | 310.7 [193.8, 476.6] | 162.3 [113.3, 306.4] | 262.9 [189.7, 387.8] | 202.8 [169.1, 243.0] |
| ssp585 | 2300 | 513.7 [443.3, 592.8] | — | — | — | — | — | 1016.0 [691.1, 1585.3] | 482.4 [386.8, 592.5] |

### The single clearest characterisation: Ladrillo's scenario response is steeper than AR6's

**Ladrillo ÷ AR6 Table 9.9 median:**

| horizon | ssp126 | ssp245 | ssp585 | ssp585 ÷ ssp126 |
|---|---|---|---|---|
| 2100 | **0.80** | 0.80 | **1.23** | **1.54×** |
| 2150 | **0.67** | 0.77 | **1.52** | **2.26×** |

The same thing in absolute terms — the ssp585 − ssp126 median spread:

| horizon | Ladrillo | AR6 | ratio |
|---|---|---|---|
| 2100 | 59.6 cm | 33.0 cm | **1.81×** |
| 2150 | 155.3 cm | 64.0 cm | **2.43×** |

**Ladrillo is systematically *below* the IPCC assessment at low forcing and *above* it at high
forcing**, and the effect grows with horizon. It is not biased high or low; it is **more
scenario-sensitive**. MAGICC agrees with Ladrillo at both ssp126 (35.6 vs 35.1 at 2100) and
ssp585@2100 (97.8 vs 94.7), so this is not Ladrillo alone against the field — but at 2150
MAGICC's ssp585 (262.9) exceeds even Ladrillo's.

**At 2300, where AR6 and FACTS are both silent**, the only three sources are Ladrillo (513.7),
**BRICK 2.0 (482.4 — within 6% of Ladrillo)**, and **MAGICC-SLR (1016.0 — 2.0× Ladrillo)**. The
two BRICK-lineage models agree closely and MAGICC is the outlier; that agreement is *not*
independent evidence, since they share the DAIS/Greenland/glacier structural lineage.

Per-component tables (Antarctica, Greenland, glaciers, thermal expansion), including the
BRICK 2.0 glacier column, are in `outputs/doc_tables_L14.md`.

> **[MARCUS — interpretation of the ssp585@2300 factor-of-2 against MAGICC.]**

---

## 4. Largest remaining concerns

### 4.1 Ladrillo / L14

| # | concern | status | severity |
|---|---|---|---|
| **C1** | **Antarctic runoff onset sits at ~0.64 °C GMST** (0.637 ± 0.077), against a paleo/Shaffer DAIS prior of **+2.3–2.5 °C** — a **3.6× discrepancy** in a physically meaningful quantity. Identical across three different amp priors (0.637 / 0.645 / 0.644), so it is a property of the fit, not of a prior choice. | **OPEN, unexplained** | **Highest.** It is the caveat that should lead. |
| **C2** | `ais_gmst_amp` is **unidentified** — posterior sd ÷ truncated-prior sd = 0.992; the posterior *is* the prior. It is degenerate with `T_on` at r = 0.79, so choosing the amp prior *is* choosing the runoff-onset decomposition. | **DECIDED, not resolved** | High, but bounded: the decision was made on fit, and the frame ambiguity (0.92–1.16 across masks/metrics, a span 1.3× one frame's between-model sd) means 0.95 is a *frame choice*, not an error. |
| **C3** | The **`T_on` posterior mode is start-determined.** Chains never cross bands: 4 chains started in LOW/LOW/HIGH/MID stayed 100% in their start band over 4M draws. The barrier is real — all 16 chains sit 3.5–28.5× above a driftless-diffusion null of 2.0×. | **Mitigated, not eliminated** | Moderate. MID independently wins the equilibrated log-density by 5.7–6.9 nats (~40–140× after a volume correction), so the champion's mode is the right one — but it was verified *by a separate arm*, not by L14's own run. |
| **C4** | **20 parameter marginals are not converged**, accepted under the documented `--accept-slr` deliverable gate. Projected SLR *is* converged across chains (R̂ < 1.05 at all horizons). | Disclosed gate | Moderate — must be stated in any write-up. |
| **C5** | Bands are **posterior-parameter spread on mean forcing**, so they are not comparable to MAGICC/FACTS widths and are **not** full predictive uncertainty. | By construction | Moderate; a presentation risk more than a model defect. |
| **C6** | At a **1.09 amp centre** the ssp126 AIS band widens **6.5×** and is **not** bimodal tipping (<3% of draws tip at ssp126 in any arm) — mechanism unexplained. | OPEN | Low *for the shipped model*: at the adopted 0.95 centre the band is the narrow 6.91 cm. Flagged because it is unexplained, not because it is active. |
| **C8** | **Scenario response is 1.8–2.4× steeper than AR6's** (Ladrillo ÷ AR6 median: 0.80/0.80/1.23 at 2100, 0.67/0.77/1.52 at 2150). Below the IPCC assessment at low forcing, above it at high forcing, growing with horizon. MAGICC agrees with Ladrillo at ssp126 and ssp585@2100, so Ladrillo is not alone — but the pattern is systematic and unexplained. | **OPEN** | **High** — it is the most visible difference from the assessed literature and any user will meet it first. |
| **C7** | Thermal expansion was **not rebuilt** (hindcast ratio 0.988 vs BRICK 2.0) and glaciers are **level with BRICK 2.0 in 1950–1992** (1.011). | Known scope limit | Low–moderate. |

### 4.2 The comparison models — and what we can honestly say

> ⚠ **Asymmetry of evidence, stated up front.** L14's concerns above are itemised because *we
> built it and instrumented it*. FACTS and MAGICC have not been audited to remotely the same
> depth here; what follows is what is visible **from their published structure and from their
> outputs in this comparison**, and it should not be read as a like-for-like concern audit.

| model | concerns visible from here |
|---|---|
| **BRICK 2.0** | Hindcast is **substantially worse on both ice sheets** (AIS 38×, GIS 12× on full-window RMSE) and the Antarctic trajectory is qualitatively wrong pre-2000 (FIG 1). Its glacier module (Wigley–Raper) saturates. In this comparison it survives only as the **glacier-only** legacy arm. |
| **FACTS** | **Not one number** — seven AR6 workflows. At ssp126/2100 the three process workflows alone span 39.8 (wf1f) – 46.1 (wf2f) cm, and `wf3f` carries **MICI** (deconto21), which at ssp585/2150 gives 310.7 cm against wf1f's 117.1 — a **2.7× spread inside FACTS itself**. **`wf4` is a structured-expert-judgement envelope** (bamber19 in both ice sheets), a deep-uncertainty width no calibrated model reproduces; including it in a median scores a model against an object it is not. **Stops at 2150**, so it cannot speak to the 2300 horizon at all. Operationally it is a heavyweight framework — the *simplicity* advantage you name is real and is about use, not correctness. |
| **MAGICC-SLR** | SLR is **embedded in MAGICC**, so it cannot be exercised or recalibrated independently of the full climate emulator — the *standalone* advantage you name. Its **ssp585/2300 median of 1016 cm is ~2× Ladrillo's 514 cm**, with a 17–83% band of 691–1585 cm; that divergence is the single largest disagreement anywhere in the comparison and neither side is independently validated at 2300. Its bands carry climate uncertainty, so they are wider by construction and not comparable to ours. |

> **[MARCUS — your judgement on how to weigh C1 against the comparison models' own
> uncertainties, and the closing positioning paragraph.]**

---

## 5. Provenance

- Posterior: **L14**, 4 chains × 2M, over-dispersed starts, `--gis-ordered --gis-basins2`,
  amp ~ N(0.95, 0.10). Champion since 2026-08-20; `benchmark/champions.json` unchanged through
  the L15–L20 arc.
- Arms tested and **not** promoted: L15 (amp re-centre), L16 (σ 0.180), L17 (mode-local proposal,
  **rejected**), L18 (start-matched), L19 (`T_on`-dispersed, **diagnostic only**), L20 (σ 0.10,
  **rejected**).
- Figures/tables regenerated by `python/doc_l14_vs_brick20.py --tag=L14`.
- Comparison inputs frozen and hashed: `benchmark/reference/_fixed/manifest.json`.
