# Note 2026-08-12 — Vivek's joint-vs-original BRICK calibration artifacts: what they say, and what (if anything) changes for Ladrillo

**Provenance.** Two Claude artifacts from Vivek, read 2026-08-12:

- A1 — *"BRICK hindcast & SSP2-4.5 projection: joint vs. original-scheme calibration"*
  `https://claude.ai/code/artifact/41acefbd-8131-418b-b0e7-430722e94352`
- A2 — *"BRICK posterior distributions: joint vs. original-scheme calibration"*
  `https://claude.ai/code/artifact/91ccf9a4-84e9-4d2d-afc8-921314c28971`

Both are **figure-only** — charts, stat cards and two tables, with caption text but no
methods prose. `WebFetch` refused them ("served to you as a public (non-member) reader"),
so they were read through the logged-in browser and captured across the full scroll.

**Numeric confidence.** Everything in §3 comes from A2's rendered **tables** and is exact
as printed. Everything in §2 is **read off boxplots by eye** and is marked `≈`; treat those
as ±1 in the last digit shown, and do not quote them without asking Vivek for the
underlying CSV.

**Baseline caveat, load-bearing.** A1 never states its zero. Our SSP comparisons are on a
**1995–2014** baseline; the recalibration targets are re-referenced to **1995–2005**.
Any Ladrillo-vs-Vivek level comparison in §5 is provisional until his reference window is
confirmed.

---

## 1. What the two artifacts actually compare

One model, one dataset, one compute budget, **two samplers**:

| | scheme |
|---|---|
| **Joint** | Turing per-block RAM (robust adaptive Metropolis), **sampling a cross-stream correlation matrix R** — 16 entries, 10 unique on/off-diagonal |
| **Original** | single robust-adaptive-Metropolis chain, **marginal / independent per-stream likelihoods, no R** |

Standalone BRICK. Data: **Zemp et al. glaciers, Wang et al. 2024 GMSL**. Scale:
4 × 10,000,000 sweeps; 28,000,000 pooled post-burn-in draws (4 chains); densities in A2
thinned to 700,000 draws per series.

The sampled parameter blocks in A2 identify the model as **stock BRICK**: glaciers
`glaciers_{v0,s0,beta0,n}` (GSIC-MAGICC), Greenland `greenland_{v0,a,b,alpha,beta}`
(SIMPLE), Antarctic `antarctic_*` + `anto_*` (DAIS/DP16), thermal `thermal_{s0,alpha}`.
**Four likelihood streams only** — the `sd_*` / `rho_*` blocks exist for
`glaciers`, `greenland`, `antarctic`, `gmsl`. There is **no thermal-expansion and no
land-water-storage stream**: in Vivek's setup TE is constrained *only* through the total.
(Ladrillo scores five components plus the total, with a NOAA thermosteric target on TE.
This difference matters in §5.)

---

## 2. Artifact 1 — hindcast 1850–2017 and SSP2-4.5 projection

Six rows: GMSL total, glaciers/small ice caps, GIS, AIS, thermal expansion, land water
storage. Left panels = ensemble median + 95% with observations overlaid; right panels =
2050 and 2100 boxes (25–75th, median line), whiskers to 5th/95th.

| component (m SLE) | 2050 joint / original | 2100 joint / original |
|---|---|---|
| GMSL total | ≈0.21 / ≈0.195 | ≈0.405 / ≈0.385 (5–95 ≈0.33–0.53 / ≈0.31–0.51) |
| glaciers | ≈0.059 / ≈0.059 | ≈0.122 / ≈0.122 |
| **Greenland** | ≈0.040 / ≈0.036 | ≈0.083 / ≈0.075 (whiskers ≈0.062–0.118 / ≈0.058–0.102) |
| Antarctic | ≈0.007 / ≈0.007 | ≈0.052 / ≈0.055, whiskers to ≈0.20 / ≈0.21 |
| **thermal** | ≈0.063 / ≈0.059 | ≈0.108 / ≈0.102 |
| land water storage | ≈0.0098 / ≈0.0098 | ≈0.0248 / ≈0.0248 |

Three readings:

1. **The scheme change is a near-no-op for glaciers, AIS and LWS.** Essentially all of the
   joint scheme's ≈ +0.02 m at 2100 is **Greenland (+≈11%)** and **thermal (+≈6%)**.
2. **Both schemes undershoot the Greenland observations** across roughly 1900–2000 — the
   obs sit above the ensemble median for the whole mid-century stretch. Changing the
   sampler did not fix it. Independent corroboration that the SIMPLE-era GIS shortfall is
   structural, consistent with `project_brick_gis_posterior_pathology` and with the whole
   premise of the Greenland pass-1 work.
3. The hindcasts are anchored near 2017, so the joint scheme's **lower 1850 start**
   (GMSL ≈ −0.155 m vs ≈ −0.105 m; AIS ≈ −0.075 vs ≈ −0.052) means a **larger total
   1850–2017 rise**, not a lower present-day level.

Caption confirms TE and LWS have no direct observation series in the comparison, and
GMSL = TE + glaciers + GIS + AIS + LWS (our five components, same decomposition).

---

## 3. Artifact 2 — posteriors, cost, convergence (exact figures)

### 3.1 The cost/quality trade

| | joint | original |
|---|---|---|
| wall clock, 4 chains parallel | **33.8 h** | **1.06 h** — 31.8× faster |
| median ESS (of 28 M draws) | **234,829** | 86,117 — joint 2.7× higher |
| max R̂ | **1.0059** | 1.0231 |
| median ESS / wall-hour | 6,939 | **80,861** — 11.7× more efficient |

Self-consistent (33.8/1.06 = 31.9; 80861/6939 = 11.7; 234829/86117 = 2.73).
**Joint buys ~2.7× ESS and a clean R̂ for ~32× the wall clock — i.e. ~12× worse sampling
efficiency per hour.**

*Quantitative pre-check on that 32×:* per-block updating with ~5–6 blocks costs ~5–6×
the model evaluations per sweep; Turing overhead plausibly supplies the remaining ~5×.
The number is therefore not obviously anomalous, but the decomposition is worth asking
Vivek for — if most of it is Turing rather than the extra evaluations, a hand-rolled
per-block RAM sampler recovers most of the R̂ benefit at a fraction of the cost.

### 3.2 Where the posteriors actually move (mean ± sd, J vs O)

| parameter | joint | original | note |
|---|---|---|---|
| **`rho_gmsl`** | **0.8828 ± 0.1060** | **0.9596 ± 0.0498** | largest shift; 5th pct 0.6704 vs 0.8582 |
| `rho_antarctic` | 0.9450 ± 0.0389 | 0.9117 ± 0.0646 | |
| `sd_antarctic` | 3.87e−4 ± 1.04e−4 | 3.15e−4 ± 8.50e−5 | joint wider |
| `sd_glaciers` | 2.92e−4 | 3.27e−4 | |
| `sd_gmsl` | 0.0025 | 0.0028 | |
| **`thermal_alpha`** | 0.0647 ± 0.0099 | 0.0613 ± 0.0087 | +6% → the TE projection shift |
| **`greenland_alpha`** | 1.88e−4 ± 1.79e−4 | 1.52e−4 ± 1.52e−4 | +24% → the GIS projection shift |
| `greenland_a` | −0.2303 ± 0.2322 | −0.1855 ± 0.1867 | |
| `anto_alpha` | 0.2805 ± 0.2221 | 0.3368 ± 0.2453 | joint lower |
| `antarctic_alpha` | 0.2157 ± 0.1795 | 0.2741 ± 0.2113 | joint lower |

Everything else is superimposed: the whole glaciers block, `greenland_{v0,b,beta}`, and
`antarctic_{gamma,mu,nu,kappa,flow0,c,bed_height0,slope,lambda,temp_threshold}`.

### 3.3 Convergence — the failures are all Antarctic

R̂ flagged when > 1.01. **Original** flags exactly four parameters, all AIS:
`antarctic_slope` **1.0231**, `antarctic_precip0` **1.0120**, `antarctic_c` **1.0119**,
`antarctic_runoff_height0` **1.0110**. **Joint clears all four** (max 1.0059, on the same
`antarctic_slope`). Joint's own weakest ESS are also Antarctic — `antarctic_slope` 60,432,
`antarctic_flow0` 61,184, `anto_beta` 67,871 — against a joint median of 234,829 and
maxima of 2.7 M (`thermal_s0`) and 1.15 M (`glaciers_n`).

*ESS caveat:* these are large numbers on 28 M draws. Before quoting the 2.7× as settled,
confirm the `maxlag` used in the ESS call — see `feedback_mcmc_ess_maxlag_trap`
(a default `maxlag=250` floors ESS and would distort a ratio like this).

---

## 4. Is Zemp a useful addition to Ladrillo's calibration data family?

**No — it is already in there, and adding it separately would double-count.**

Verified directly from the paper this session (`ClaudeDocs/Papers/Frederikse.2020.s41586-020-2591-3.pdf`,
Methods, glacier paragraph):

> "For glaciers, we use two mass-change estimates. The first estimate, which covers the
> whole twentieth century, is based on a global glacier model driven by observation-based
> surface forcing [Marzeion et al. 2015]. … The second estimate [Zemp et al. 2019], which
> provides mass changes since 1961, uses in situ glaciological and geodetic observations…
> For each ensemble member, we randomly choose between the two estimates. Before 1961,
> each member uses the estimates from the first estimate."

Ladrillo's **C3** constraint (mid/early glacier flow, `recalib_targets_ext.csv` 1900–2018)
*is* the Frederikse glacier component. So for **1961+ Zemp is already one of the two
branches each ensemble member draws from**; for **1900–1960 the component is 100%
Marzeion-2015** — which is precisely the era C3 is weakest in and where our σ×2 and the
Roe-2021 initialization-artifact critique apply. **Zemp cannot help there: its record
starts in 1961.**

This is consistent with what the repo already knew — `memo_2026-08-05` §2c calls it "the
Zemp branch" and reads Frederikse's `compute_indiv_glaciers` at code level to establish
that the glacier column is regions 1–18 minus 5 by construction. The present check
confirms that from the published Methods rather than the code, which is worth having on
the record.

**Three residual roles Zemp could still play, none of them a new likelihood term:**

- **(a) A branch-spread diagnostic — cheap and genuinely informative.** Frederikse's 1961+
  glacier σ mixes *within-method* error with the *Marzeion-vs-Zemp method choice*. Splitting
  the 5000-member ensemble by which branch each member drew would tell us how much of C3's
  mid-century σ is method disagreement. That directly sharpens the "C3 mid: MODERATE"
  confidence rating in `memo_2026-08-07_glacier_constraint_anatomy` §1, and it is a read of
  data we already hold.
- **(b) An independent cross-check on the 1961–2000 segment**, in the same role IMBIE 2023
  already plays for AIS/GIS in `prep_recalib_targets_ext.py` — *not* fed to the fit.
- **(c) Already mined.** Zemp's Table 1 r19 = −14 ± 108 Gt/yr is the evidence base for the
  documented Frederikse r19 zero; that work is done (`memo_2026-08-05` §2c).

**Verdict: do not add Zemp as a stream. Item (a) is worth one afternoon; (b) is optional.**

---

## 5. Wang et al. 2024 vs Dangendorf 2024 as the total-GMSL target

**Identification.** Wang et al. (2024), *"Improved Sea Level Reconstruction from 1900 to
2019"*, J. Climate 37(24), JCLI-D-23-0410.1. It is a **reduced-space optimal interpolation
tide-gauge reconstruction in the Church & White (2011) lineage**, improved with sea-level
fingerprints, sterodynamic-sea-level climate-change patterns and fuller local vertical
land motion. Published GMSL trend **1.6 ± 0.2 mm yr⁻¹ (90% CL) over 1900–2019**, which the
paper reports as consistent with a 1.5 ± 0.2 mm yr⁻¹ sum of observed contributions.

Ladrillo's total target is **Dangendorf et al. (2024)**, ESSD 16, 3471–3494 — a
**hybrid Kalman-smoother probabilistic reconstruction**, spliced with NOAA STAR altimetry
for 2022–2024 (`prep_recalib_targets_ext.py`).

**Computed from data we hold** (`data/observations/dangendorf2024_gmsl_annual.csv`;
`data/calibration/CSIRO_Recons_gmsl_yr_2015.csv` = Church & White 2011, the legacy
BRICK v1.2 target):

| window | Church & White 2011 | Dangendorf 2024 | Wang 2024 (published) |
|---|---|---|---|
| 1900–2013 | 1.689 | 1.427 | — |
| 1900–1990 | 1.526 | 1.380 | — |
| 1961–2013 | 2.149 | 1.580 | — |
| 1900–2019 | — | **1.499** | **1.6 ± 0.2 (90%)** |
| 1900–2021 | — | 1.524 | — |

(mm yr⁻¹. Dangendorf 1900–2021 = 1.524 reproduces the paper's published 1.5 ± 0.19, as
already validated in `diag_dangendorf_vs_frederikse.py`.)

**Reading.**

- Over the matched 1900–2019 window Wang is **+0.10 mm yr⁻¹ (≈ +7%)** above Dangendorf —
  ≈ **+1.2 cm of cumulative 20th-century rise** against Dangendorf's 20.7 cm.
- That gap is **inside both stated uncertainties** (Wang ±0.2 at 90%, Dangendorf ±0.19).
  The two are statistically consistent; this is not a conflict.
- But it is **not noise either** — it is the RSOI-vs-Kalman lineage difference, and Wang
  lands between its own ancestor (Church & White 1.689 over 1900–2013) and Dangendorf
  (1.427 over the same window). Wang narrows the historical gap without closing it.
- **Where the gap sits is the open question.** The lineage difference is classically
  concentrated **pre-1990** (Dangendorf 2017 PNAS reassessed 1902–1990 downward), and our
  own numbers show CW−Dangendorf widening from +0.15 (1900–1990) to +0.57 (1961–2013) mm/yr.
  I have **not** verified where Wang's residual +0.10 sits, because we do not hold Wang's
  time series. **Test, if it matters:** pull `GMSL_yr.txt` from the J. Climate supplement
  and difference it against our Dangendorf CSV by decade.

**Recommendation: keep Dangendorf.** It is the canonical choice under the
`obs-model-comparisons` convention, it is already validated in-repo against its own paper,
and switching would invalidate the gate-3.1 closure work — which is expressed entirely in
the Frederikse-vs-Dangendorf frame. **Wang's value is as a documented sensitivity**: it
brackets the plausible historical-rate range at ≈ +7%, and it is the right citation for
"how much would the total target move if we adopted the RSOI lineage instead". Worth one
sentence in the sharing memo's data-choice section.

*Side observation:* Vivek's pairing of **Wang GMSL + Zemp glaciers** is close to a
modernized version of legacy BRICK's own targets (Church & White GMSL; Dyurgerov & Meier
2005 glaciers, periphery-inclusive). Our Dangendorf + Frederikse/GlaMBIE family is a
different lineage, not a better-resourced version of the same one. **Any Ladrillo-vs-Vivek
comparison is a comparison of two target families as much as two models.**

---

## 6. Other tidbits — ranked by whether they change anything

### 6.1 The `rho_gmsl` collapse is directly relevant to gate 3.1 — **highest value item**

Introducing R drops `rho_gmsl` from **0.9596 ± 0.0498 to 0.8828 ± 0.1060** (5th pct
0.858 → 0.670). Everything else about the total-stream likelihood is unchanged.

Gate 3.1's verdict rests on the sampled per-series AR(1) being near-unity — **ρ_gis 0.985
(τ ≈ 67.5 yr), ρ_steric 0.973** — which removes **14–16×** of the leverage on a mid-century
GIS offset. And `prep_recalib_targets_ext.py` already carries the flagged caveat that an
anchor-shaped closure σ "may partly double-count level correlation" given ρ ≈ 0.97.

Vivek's result is **independent evidence for the mechanism behind that caveat**: a large
part of a near-unity per-series AR(1) can be cross-stream correlation that an independent
likelihood has nowhere else to put. If that carries to Ladrillo, an R-sampling scheme
would **lower ρ_gis, restore leverage on the mid-century GIS offset, and change the
step-5 pre-registration** — the +12.43 logl the Greenland correction currently nets is
computed under the current, leverage-suppressed likelihood.

**This does not mean adopt R.** It means the pre-registration should say what we expect
under *both* likelihood structures, so that a step-5 posterior coming back ≈ extC is not
misattributed. Cheap test that does not require a sampler rewrite: compute the empirical
cross-stream correlation of the extC residuals (we have them — gate 3.1 used them) and
check whether it is large enough to explain ρ_gis ≈ 0.985.

### 6.2 The R̂ failures are all Antarctic — corroborates the red team, from outside

Every original-scheme R̂ > 1.01 is an AIS parameter, and the joint scheme fixes all four.
`redteam_2026-08-11` records 8 non-converged AIS marginals as the block that sets the
tail, and gate 3.2 established that **what moved between BRICK-Mengel and Ladrillo is the
probability of Antarctic tipping by 2100, which is substantially prior-driven**. Vivek's
result says the AIS block is where a joint/R sampler earns its keep — i.e. there is a
*sampling* contribution to the AIS tail problem, on top of the prior-dominance one. Both
can be true. Worth stating in the red-team follow-up rather than treating AIS
non-convergence as purely a prior story.

### 6.3 Prior-dominance signal in the DAIS block — corroborating, needs one test

`antarctic_{gamma, mu, nu, bed_height0, slope, lambda, temp_threshold}` agree between the
two schemes to 3–4 significant figures (e.g. `temp_threshold` −15.610 ± 0.4356 vs
−15.610 ± 0.4352; `bed_height0` 782.0 ± 22.577 vs 782.2 ± 22.571), and several of those
marginals render **flat-to-ramp shaped** rather than peaked. Two very different samplers
landing on identical marginals is *consistent with* prior-dominance — but it is equally
consistent with both being well identified, so **do not report it as prior-dominance
without the test**: prior-vs-posterior overlap (or KL) per parameter. We should run that on
our own DAIS block regardless; it is the cleanest way to substantiate the red team's
"prior-driven tail" claim quantitatively.

### 6.4 The TE story may not transfer — structural difference in the likelihood

`thermal_alpha` moves +6% under the joint scheme in a setup where **TE has no observation
stream** and is constrained only through the total. TE is therefore the residual absorber,
and changing how the total's residuals are apportioned moves it. **Ladrillo has a NOAA
thermosteric target on TE**, so the same change would land differently — do not carry the
+6% across. Related: item 4.3 in the step-5 handoff (re-check TE against a modern OHC
target) and the ρ_steric = 0.973 finding are plausibly the same story as §6.1, and are
worth doing together.

### 6.5 Level comparison — suggestive, blocked on the baseline question

Vivek's standalone BRICK gives SSP2-4.5 @2100 GMSL ≈ **0.405 m** with Antarctic ≈ 0.052 m.
Ours (gate 3.2, 1995–2014 baseline): BRICK-Mengel **78.02 cm** → Ladrillo extC **49.48 cm**
total, Antarctic 43.05 → 11.74 cm. If the baselines are compatible, **Ladrillo sits between
BRICK-Mengel and an independently-calibrated standalone BRICK, and the −28.54 cm move went
toward it rather than past it** — a useful external sanity point for the gate-3.2 write-up.
**Do not use this until Vivek confirms his reference window**, and note it compares
different Greenland/glacier structures *and* different target families (§5).

### 6.6 Non-findings, logged so they are not re-investigated

- Vivek's LWS is flat-zero through the hindcast and ≈0.0098 / 0.0248 m at 2050 / 2100 —
  same convention as `project_brick_lws_calibration_convention`. No change.
- Glaciers are identical between schemes at both horizons — sampler choice does not touch
  the glacier block. Our glacier work is unaffected by any of this.
- His Greenland is stock SIMPLE and his glaciers stock GSIC-MAGICC, so neither the GIS
  undershoot nor the glacier behaviour is evidence about Ladrillo's replacements — only
  about the baseline they replace.

---

## 7. Actions

**Do:**
1. Add the §6.1 residual-cross-correlation check to the step-5 pre-registration, and state
   the expected posterior under both likelihood structures. *(Blocks nothing; do before
   launching step 5, since it changes how the result is read.)*
2. Run the prior-vs-posterior overlap test on our DAIS block (§6.3) — it substantiates the
   red team's prior-driven-tail claim with a number.
3. Add one sentence to the sharing memo's data-choice section citing Wang 2024 as the
   RSOI-lineage sensitivity on the total target (≈ +7% on the 1900–2019 rate), with
   Dangendorf retained. **Marcus drafts the prose.**
4. Note in the red-team follow-up that AIS non-convergence has a *sampling* component, not
   only prior-dominance (§6.2).

**Do not:**
5. Do not add Zemp as a likelihood stream (§4). Optionally do the branch-spread diagnostic.
6. Do not switch the total target to Wang (§5).
7. Do not adopt a joint/R sampler for step 5 on this evidence — 32× wall clock for a
   ≈ +0.02 m projection change on a model whose blocks we have replaced anyway.

**Ask Vivek:**
8. His reference/baseline window for A1 (§5, §6.5); the underlying CSVs behind the A1
   boxplots; the `maxlag` in his ESS call (§3.3); and whether the 32× decomposes into
   per-block model evaluations vs Turing overhead (§3.1).
