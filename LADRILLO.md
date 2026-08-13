# Ladrillo 1.0 — the baseline

The single definition of what "Ladrillo" currently means: which model, which
posterior, which files, what may be said about them, and what is not in 1.0.
If you are picking this up cold, read this file and
`notes/handoff_2026-08-13b_amp_law_implemented.md`; everything else is detail.

Baseline commit: tag **`ladrillo-1.0`**, branch `brick-mengel-vnext`.
Status 2026-08-13: deliverables shipped; four open threads (§7).

---

## 1. What the model is

**Ladrillo = MimiBRICK v2.0.0 with two components replaced.**

| component | Ladrillo 1.0 | source |
|---|---|---|
| glaciers & small ice caps | **three-reservoir Mengel-type emulator** — R19 (RGI 19), SLOWP (RGI 03/09/07/06), FAST (the other 13), each on its own area-weighted driver | `julia/glaciers_nu3_component.jl` |
| Greenland | **A+B: two-channel relaxation** (fast/SMB + slow/dynamic) sharing an equilibrium commitment through `gis_f`, on a **regional** south-Greenland driver | `julia/greenland_ab_component.jl` |
| Antarctic, thermal expansion, LWS | stock MimiBRICK v2.0.0 | MimiBRICK |

Glacier reservoirs integrate `S_eq,b = a_b (1 − exp(−b_b (T_b − T_off,b)))` with
`dS_b = min(κ_b · exc^ν_b, 1)(S_eq,b − S_b)`; `ν_b` is **fixed**, not sampled
(the hindcast cannot identify it).

**The external interface is GMST + OHC only.** Both regional drivers are built
inside the model from observed series plus an anchor-preserving splice, which is
what keeps Ladrillo a drop-in replacement rather than a model that needs its own
climate input. Do not add an input to the interface without deciding that
deliberately.

### The Greenland amplification law (projection-side)
The post-2024 Greenland splice uses `amp(ΔT) = amp_draw × S(ΔT)`: the **observed
level**, the **CMIP6 shape**. `S` is a PCHIP through pooled binned medians of 40
CMIP6 models over 0.75–2.75 K, held flat outside, normalised to 1 at
`ΔT_eff = 0.940 K` — the x²-weighted effective warming level of the observed
through-origin fit, so the law meets the calibration at the point the calibration
was made. Projection-side only: the calibrator runs to 2026, so `gis_amp` is
likelihood-inert and no chain re-run was needed.

Constants and shape table: `LADRILLO_GIS_*` in `julia/ladrillo_projection.jl`,
`outputs/gis_amp_shape{,_meta}.csv`.

---

## 2. The posterior

**`data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv`** — 10 000 draws
subsampled from 4 × 2M chains (seeds 2026–2029, acceptance 0.236–0.237,
over-dispersed starts), 55 columns. **Gitignored**: it exists only on this
machine. Regenerate with

```bash
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=L10 --accept-slr
```

(~41 min; needs `outputs/mcmc/slr_convergence_L10.csv`, which IS tracked).

### ACCEPTED ON THE DELIVERABLE — and what that permits

Cross-chain convergence of **projected SLR** passes; **19 parameter marginals do
not**. Certificate: `outputs/mcmc/slr_convergence_L10.csv` (carries a
`gis_shape` column recording which model it certifies).

| | R̂ | ESS | sd(medians) | mean(sd within) | ratio |
|---|---|---|---|---|---|
| SLR@2100 | 1.000 | 1586 | 0.110 cm | 12.486 | 0.009 |
| SLR@2150 | 1.000 | 1685 | 4.641 cm | 33.865 | 0.137 |

- **MAY** be used for projected SLR and anything derived from it.
- **MAY NOT** be used for parameter-level inference. The failing marginals are
  mixtures of chains that never merged, not posteriors. No credible intervals, no
  scatter plots, no cross-vintage marginal comparisons for:
  - **AIS geometry** — `ais_iceflow0` R̂ 2.359 / ESS 12 / τ 3.3e5, chains with
    nearly disjoint support; also `antarctic_alpha` 1.505, `ais_slope` 1.288.
  - **the Greenland SLOW channel** — `gis_f` 1.335, `gis_alpha_s` 1.180 (chain
    medians spanning 2.8×), `gis_beta_s` 1.137, `gis_c0` 1.102. The FAST channel
    IS converged (`gis_c1` 1.015, `gis_alpha_f` 1.029, `gis_beta_f` 1.025, ESS
    220–270). Table: `outputs/mcmc/gis_block_convergence_L10.csv`.
- **WATCH at 2150**: the median spread there is ~15× the 2100 value relative to
  within-chain scatter (ratio 0.137 vs 0.009) — the AIS tipping tail is the
  slowest-mixing feature, and **R̂ is mean-based so it reads 1.000 and does not
  surface this**. Carry the caveat manually wherever 2150 or 2300 is reported.

---

## 3. Canonical files

| role | file |
|---|---|
| **projection kernel** (the one place that maps a draw → MimiBRICK) | `julia/ladrillo_projection.jl` |
| calibrator | `julia/calibrate_mcmc_ext.jl` |
| SSP projections deliverable | `julia/project_ssps_components_ladrillo.jl` → `outputs/ssps_components_2300_L10.csv` |
| hindcast deliverable | `julia/posterior_predictive_ladrillo.jl` → `outputs/postpred_L10_{components_timeseries,bias,coverage}.csv` |
| memo figures | `python/plot_ladrillo_memo_figures.py` → `figures/ladrillo_fig{1,2,3}_*.png` |
| comparison vs FACTS / MAGICC / BRICK 2.0 | `python/ladrillo_model_comparison.py` |
| acceptance gate | `julia/diag_slr_convergence_by_chain_ladrillo.jl` |
| G4 scenario spread | `julia/diag_gis_spread_2100_ladrillo.jl` |
| Greenland block convergence | `julia/diag_gis_block_convergence.jl` |
| amp law: shape | `python/diag_gis_amp_cmip6.py`, anchor `python/diag_gis_amp_anchor.py`, scenario test `python/diag_gis_amp_scenario_split.py` |

Every driver **includes the kernel** rather than re-deriving the parameter map.
That rule exists because the copy-pasted version drifted onto the wrong Greenland
once already; a diagnostic that re-implements the mapping can certify a model
different from the one the projections use.

### Reproduce the deliverables

```bash
./run_ladrillo_tests.sh
```

```bash
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl 2000
julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl 2000
source ~/climate-env/bin/activate && python3 python/ladrillo_model_comparison.py && python3 python/plot_ladrillo_memo_figures.py
```

Six suites, all must pass before any number leaves the repo: data assembly →
calibrator glacier path → projection kernel → Greenland component → calibrator
Greenland wiring → projection-kernel Greenland (incl. the amp law's gates).

---

## 4. Headline numbers (2100, cm, rel. 1995–2014, FaIR-mean forcing)

| ssp | glaciers | gis | ais | te | total (p17–p83) |
|---|---|---|---|---|---|
| SSP1-2.6 | 9.01 | 6.18 | 4.77 | 12.86 | **35.4** [34.4, 36.4] |
| SSP2-4.5 | 11.03 | 8.17 | 5.95 | 16.85 | **45.0** [43.2, 59.2] |
| SSP5-8.5 | 15.16 | 13.57 | 37.72 | 25.28 | **94.2** [82.2, 109.6] |

Bands are **posterior-parameter spread only** — the forcing is FaIR-mean per SSP,
so there is no climate spread in them. Say so wherever they are compared to FACTS
workflows, which include it.

Scenario spread (SSP1-2.6 → SSP5-8.5) against the comparison arms:

| component | Ladrillo | arms |
|---|---|---|
| glaciers | 6.14 | FACTS 6.52 / 8.48, MAGICC 4.85, BRICK 2.0 4.47 |
| **Greenland** | **7.39** | FittedISMIP 6.34, MAGICC 7.09, bamber19 7.23, emuGrIS 7.26 |
| Antarctic | 32.95 | ar5AIS −2.3, emuAIS −0.2, larmip 2.5, bamber19 8.9, deconto21 19.7, MAGICC 35.4 |
| total | 58.8 | FACTS workflows 25.2–50.7, MAGICC 62.3 |

**Greenland is now in family; the Antarctic is the outlier** — and it is
simultaneously the block that fails to converge and whose tail the red team
recorded as prior- rather than data-driven. Report components, not just totals:
a reader comparing totals sees AIS (high) and TE (low) cancel.

---

## 5. Standing caveats — carry these into any report

1. **Antarctic**: quote a distribution, never a median difference. The 2100
   distribution is bimodal (tipped / not tipped) and vintage changes move the
   *tipping probability*, not a level. "X cm lower at SSP2-4.5" is a misleading
   sentence.
2. **2150 and 2300**: the AIS tipping tail is the slowest-mixing feature and R̂
   does not see it (§2).
3. **High-warming Greenland**: option C failed and is out of pass 1, but its
   criticism — proportional relaxation cannot serve both a small historical loss
   and a huge post-threshold commitment — applies to A+B too, where it is
   *invisible rather than absent*. It now has a numerical fingerprint: the slow
   channel that carries the multi-millennial commitment is exactly the one the
   1900–2024 record cannot identify (§2). Compounds with the flat-hold of `S`
   above 2.75 K.
4. **`gis_beta_f` is unidentified and consequential**: the data bound it only to
   < ~1e-2/yr, and β_f = 0 costs 2Δ = +0.55 while moving SSP5-8.5 2100 by 1.70 cm.
   Part of the Greenland band width is prior width.
5. **Noise model**: per-series AR(1) is misspecified on all five streams and the
   total stream is 56% algebraically redundant with the components. Not changed
   for 1.0 — extC and L10 were both calibrated under it.
6. **Structural uncertainty is not in the bands** wherever they are compared to
   FACTS.

---

## 6. Provenance — superseded vintages

Quarantined, not deleted. Both are **vintage differences, not bugs**; each
directory carries a README with the component table and the reasoning.

| directory | what |
|---|---|
| `outputs/quarantine/20260813_pre_extc_mengel_vintage/` | the pre-extC BRICK-Mengel projections (the "78.02 cm" vintage) |
| `outputs/quarantine/20260813_extc_vintage/` | extC (accepted 2026-08-10, stock-SIMPLE Greenland), plus the original constant-amp acceptance certificate |

Scripts that **describe** a superseded vintage are pinned to its quarantine path
rather than migrated — repointing them at L10 would make their own prose wrong.
See §6 of the extC README for which, and why.

---

## 7. NOT in 1.0 — the open threads

1. **Per-scenario amp curve** — DONE 2026-08-13; the flat-hold above 2.75 K is
   what the composition-controlled data support.
2. **`gis_beta_f` prior re-bounding** — does re-bounding to the data support buy
   anything, or is β_f riding a ridge with `f` (in which case only
   reparameterisation helps)?
3. **Reparameterise the correlated blocks** — AIS geometry
   `(bedheight0, slope, iceflow0, c)` and, on the evidence of §2, the Greenland
   slow block `(c0, alpha_s, beta_s, f)`. Precedent: the `ais_runoff_Ton`
   reparameterisation fixed the runoff line the same way. **Do not simply run
   longer** — τ ≈ 3.3e5 needs O(1e7–1e8) iterations.
4. **Next calibration** — collects (2), (3) and an explicit discrepancy term for
   the noise model into ONE spec, rather than three changes each invalidating the
   last.
5. **Through 2300** — report with the §5 caveats, and keep investigating what
   replaces proportional relaxation at high warming (re-running
   `scope_greenland_bochow2026.py` against A+B is the first step).

Also owed: ν sensitivity once; a refit with the four glacier set-asides at prior
centres; the etymology sentence for the sharing memo (**Marcus drafts prose**);
and the branch is still named `brick-mengel-vnext`, which no longer describes
what is on it.
