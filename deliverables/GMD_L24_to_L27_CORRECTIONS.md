# GMD draft — the L24→L27 vintage audit

**What this is.** The draft ships **L27** (Marcus, 2026-09-24) but several methods passages are still
**L24's**, one of them naming "L24" in the text. Every correction below is a *verifiable number*, which
is my side of our split — **the prose and the framing are yours.** Nothing here is an interpretive change.

**Source of truth for each number is named per item.** `ladrillo_priors_L27.csv`'s provenance column
carries L27's exact ARGS, which is how the flag differences were established rather than assumed:

```
L24: --gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180
L27: ... --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4
     --precip-reparam --cut-fastdyn --fix-gamma --no-ledger
```

Those seven extra flags are what drop **9 parameters** and add **1** (`ais_precip0_LOG` →
`ais_precip_u` under `--precip-reparam`). **58 → 50.**

---

## ⛔ 1. The parameter count and its breakdown

> **Draft:** *"58 parameters are sampled: 17 Antarctic, 9 Greenland, 19 glacier, 13 remaining (thermal
> expansion, two discrepancy bases of two coefficients each, and four AR(1) noise pairs)."*

**L27:** **50** parameters — **14 Antarctic, 9 Greenland, 16 glacier, 11 remaining (thermal expansion,
*one* discrepancy basis of two coefficients, and four AR(1) noise pairs).**

⭐ **The grouping is reconstructed, not guessed, and it is validated:** applying the same mapping to
L24 reproduces the draft's own published 17 / 9 / 19 / 13 = 58 exactly. Applied to L27 it gives
14 / 9 / 16 / 11 = 50. Source `outputs/ladrillo_prior_posterior_{L24,L27}.csv`.

| | Antarctic | Greenland | glacier | remaining | total |
|---|---|---|---|---|---|
| L24 (draft) | 17 | 9 | 19 | 13 | 58 |
| **L27** | **14** | **9** | **16** | **11** | **50** |

⚠ **"two discrepancy bases" → "one".** `--no-d2-gsic` drops `d2_gsic_1`/`d2_gsic_2`; only the steric
basis (`d2_steric_1`, `d2_steric_2`) survives.

**Dropped (9):** `ais_precip0_LOG`, `antarctic_gamma`, `antarctic_lambda`, `antarctic_temp_threshold`,
`d2_gsic_1`, `d2_gsic_2`, `gic_delta`, `gic_s_r5`, `gic_u_pre`. **Added (1):** `ais_precip_u`.

## ⛔ 2. The convergence paragraph is L24's throughout — and it says so

> **Draft:** *"…39 of the 58 parameters pass it. The 19 that fail are concentrated in the Antarctic block
> (the geometry ridge and the ocean-temperature parameters; ais_iceflow0 R̂ = 1.26, antarctic_alpha 1.28)
> **and in Greenland's slow channel**… **L24** is therefore accepted on the deliverable-level criterion:
> projected sea level converges (R̂ = 1.008 at 2100 and 1.011 at 2150 …, effective sample size of about
> 1050 on the 1,600 thinned draws)."*

⚠⚠ **This paragraph names "L24" in a paper that ships L27.** Source for every L27 value:
`outputs/log_l27_postprocess_driver.txt` (the run's own log) and `outputs/mcmc/slr_convergence_L27.csv`.

| | draft (L24) | **L27** |
|---|---|---|
| parameters passing R̂<1.05 **and** ESS>400 | 39 of 58 | **42 of 50** |
| failing | 19 | **8** |
| where they fail | Antarctic block **and Greenland's slow channel** | **all 8 are Antarctic** — Greenland's slow channel now passes |
| `ais_iceflow0` R̂ | 1.26 | **1.031** |
| `antarctic_alpha` R̂ | 1.28 | **1.047** |
| SLR R̂ @2100 / @2150 | 1.008 / 1.011 | **1.001 / 1.002** |
| ESS on the 1,600 thinned draws | ~1050 | **1238.5 / 1249.4** |

The 8 that fail, with R̂ and ESS: `antarctic_alpha` 1.047/84.9, `anto_alpha` 1.013/189.7, `anto_beta`
1.016/243.8, `ais_slope` 1.063/78.6, `ais_iceflow0` 1.031/141.5, `ais_precip_u` 1.043/91.9,
`ais_runoff_Ton` 1.313/19.5, `ais_c` 1.079/64.2. (Several fail on **ESS**, not R̂ — worth keeping the
gate's two clauses distinct in the text.)

⭐ **The correction runs in the draft's favour**: L27 is markedly better converged than L24, and the
"Greenland's slow channel" clause should simply go. *"Four chains of 2,000,000 iterations"* and
*"1,600 thinned draws"* are both still correct.

## ⛔ 3. A named parameter the shipped model does not have

> **Draft:** *"The seven parameters (ais_mu, ais_bedheight0, ais_slope, ais_iceflow0, **ais_precip0_LOG**,
> ais_runoff_Ton, ais_c) are freed under a joint paleo prior."*

**L27 samples `ais_precip_u` in its place** (`--precip-reparam`). Still **seven**, so only the name changes.

## ⛔ 4. The 2300 Antarctic spread — the number is stale AND the mechanism no longer applies

> **Draft:** *"Ladrillo's 2300 Antarctic spread is dominated by the prior for **antarctic_lambda**, the
> DAIS fast-dynamics rate; BRICK 2.0 samples the same parameter from the same fast-dynamics ensemble
> (mean 0.0105, sd 0.0033 in Ladrillo; 0.0104, 0.0036 in BRICK 2.0), which is why the two Antarctic
> spreads are alike (5–95 % widths of **329** and 405 cm at SSP5-8.5 in 2300)."*

⭐ **This sentence was CORRECT at L24 and I checked before saying otherwise.** L24's joint-arm spread is
**329.1 cm** and BRICK 2.0's joint is **405.2** — a like-for-like joint/joint pair. (BRICK's *fixed* arm
is 329.8, a near-coincidence that makes this look like a misattribution. It is not one.)

**Two separate problems for L27:**

1. **The number.** L27's ssp585 2300 AIS 5–95 % width is **313.8 cm** (joint arm), not 329.
   Source `outputs/scope_slr_fairunc_cells_ssp585_spliced_L27_tap4p69K_V5p64m_tau800.csv`, horizon 2300,
   component `ais`. BRICK 2.0's **405.2** is unchanged. ⚠ Quote the **joint** arm for both or the
   **fixed** arm for both (L27 fixed 242.9, BRICK fixed 329.8) — never one of each. That exact mix-up
   is what the 09-03 audit caught in Fig 9.

2. ⭐⭐ **THE MECHANISM SURVIVES — and the sentence is MORE true at L27, not less.**
   ⚠⚠ **I got this wrong in my first pass and corrected it the same session.** I read
   `--cut-fastdyn` in L27's flags, saw `antarctic_lambda` absent from the sampled set, and
   concluded the fast-dynamics channel was gone. **It is not.** The calibrator says so in its own
   words (`calibrate_mcmc_ext.jl:857-860`):

   > `--cut-fastdyn` — *lambda and T_crit are NOT sampled: their likelihood is exactly flat (the
   > threshold is never crossed in the hindcast). The model holds their paleo MEDIANS during the
   > calibration; **projections attach JOINT paleo draws per posterior draw** … "propagated, not
   > estimated", made literal.*

   Confirmed at runtime: every chain read prints
   `ladrillo_attach_propagated!: lambda/T_crit attached as JOINT paleo draws (seed 20260920,
   paleo_fastdyn_draws.csv)`. So lambda still drives L27's projections — it is now **exactly** a
   prior draw rather than a posterior that happened to sit on its prior.

   ⇒ **Do NOT delete this sentence.** Only the parenthetical moves:

   | | draft (L24, sampled) | **L27 (propagated)** |
   |---|---|---|
   | Ladrillo `antarctic_lambda` | mean 0.0105, sd 0.0033 | **mean 0.01038, sd 0.00359** |
   | BRICK 2.0 | 0.0104, 0.0036 | 0.0104, 0.0036 (unchanged) |

   Source: `outputs/paleo_fastdyn_draws.csv` (20,000 draws), the ensemble L27 propagates from.
   ⭐ **The two now agree to the digit**, because both draw lambda from the same fast-dynamics
   ensemble — which makes the draft's own *"which is why the two Antarctic spreads are alike"*
   **more** defensible at L27, not less. `[MCS — you may even want to strengthen it.]`

   ⭐⭐ **AND "DOMINATED" IS NOW RECEIPTED ON L27.** The measurement behind that word was on **L14**
   ([[ais_spread_is_lambda_prior]]: R² 0.78, contrast 0.92), which *sampled* lambda. Re-measured on
   L27 (`julia/diag_ais_block_propagation.jl 500 --tag=L27`, 2,000 draws,
   `outputs/diag_ais_block_propagation_L27.csv`):

   | ssp585 @2300 | R² | decile contrast / spread |
   |---|---|---|
   | **`antarctic_lambda`** | **0.708** | **0.897** |
   | `antarctic_temp_threshold` | 0.049 | 0.345 |
   | `ais_gmst_amp` | 0.080 | 0.326 |

   **The word stands**, and at L27 it is *stronger* in kind: lambda is now an exact prior draw, so
   *"the band is sampled, not inferred"* is literal rather than inferred from a posterior sitting on
   its prior.

   ⚠ **Two caveats to carry if you quote these.** (a) The attribution is measured on the
   **fixed-climate** arm (spread 242.85 cm), which is the right arm for isolating *parameter*
   uncertainty — but the band widths quoted in the sentence (313.8 / 405.2) are **joint** arm. Do not
   mix them in one clause. (b) ⛔ **The ranking INVERTS by scenario**, so an AIS sensitivity quoted
   without its scenario is meaningless: at **ssp245 @2300** the order is `ais_gmst_amp` **0.68**,
   `antarctic_temp_threshold` **−0.48**, `antarctic_lambda` **0.47**. The sentence is an ssp585
   statement and should say so.

## ⚠ 5. Table A1 (priors/posterior appendix) is built on L24

`deliverables/GMD_TableA1_priors_posterior_L24.docx` (2026-09-19) predates the switch to L27 (the draft
filenames carry `_L27` from 09-20). It lists **58** parameters — including **9 the shipped model does not
sample** — and the posterior columns move by up to several hundred percent between vintages.
**It needs rebuilding from `outputs/ladrillo_prior_posterior_L27.csv`.** I did not rebuild it yet
because I do not know whether you want the same layout and caption; say so and it is quick.

---

## What I did NOT change, and why

- **Nothing in the draft `.docx`.** It is untracked, has no markdown source, and you edit it directly
  ([[marcus_edits_docx_directly]]). Editing it here would risk your prose.
- ⚠ *"Four Antarctic changes distinguish Ladrillo's calibration from BRICK 2.0's"* — the draft already
  says, correctly, that they *"have not been tested individually, so the AIS changes cannot be formally
  attributed by parameter."* That caveat is doing its job; **no ablation exists** and I am not going to
  imply one does. Left alone.
- The **IMBIE-2026 insert** (`GMD_imbie2026_null_INSERT.md`) is ready and unaffected by any of this.
