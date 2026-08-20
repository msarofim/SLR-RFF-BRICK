# Handoff — L13 was certified on the wrong model, its R̂ failure is a frozen `ais_c`, and the AIS split is dead

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**, pushed and
in sync at `ef6d623`. Predecessor: `notes/handoff_2026-08-19b_shares_term_wired.md`.

**Bottom line. Two of 19b's open items are now CLOSED by measurement, and neither
closed the way 19b expected. (1) The L13 SLR certificate was computed on a model L13
was never fitted under — `ladrillo_projection.jl` had no 3-basin variant, so every
L13 projection ran at s = 1. Correcting it moves SLR@2100 47.89 → 46.23 cm, which
means most of the "+2.36 cm move" was an artefact. (2) That does NOT fix convergence;
the R̂ failure is a proposal covariance degenerate in `ais_c` (adapted sd 7.9e-07 vs
L12's 1.28), which freezes the parameter and splits the chains 2+2 on the AIS
directions left open. Both other 19b candidates — `gis_amp` and "the tail" — are
refuted by measurement. (3) The EAIS/WAIS split is dead: the IMBIE-3 regional data
DO exist and close, but EAIS's share is negative and only WAIS is measurable.
L12 remains canonical at 45.53 cm. THE NEXT ACTION IS TO RESEED THE PROPOSAL — §1.**

---

## 1. THE NEXT ACTION: reseed, then re-tune, then re-run

Do not re-run L13 production from the current proposal. It will freeze `ais_c` again
and cost ~4 h 25 m to learn nothing.

1. **Reseed from a covariance in which `ais_c` actually moves.**
   `adapted_cov_L12_seed2026.csv` (57×57, `ais_c` sd **1.28**) name-mapped into the
   59-param L13 layout. `embed_cov!` already does this by NAME and the L11-vintage
   branch is the pattern to copy; the two basin rows take the fresh diagonal, which
   is correct — they are new parameters with no prior proposal shape.
   **Check the seed before launching:** print `sqrt(diag(cov0))` for the seven
   `GEO_NAMES` and refuse to start if `ais_c` is below, say, 0.1.
2. **Re-tune** (1 M single chain ≈ 3 h 20 m), then **verify the tune did not collapse
   it again** — this is the step that was missing. `adapted_cov_L13tune` had
   `ais_c` at 6.6e-07 from a seed that was healthy at 0.606, and nothing looked.
3. **Rebuild the starts** from the re-tuned chain and **check dispersion in `ais_c`**,
   not only in `ais_iceflow0`. 19b already flagged the starts (spread 1.15e-05 vs
   the L12-vintage file's 30.92); that flag was right but insufficient — R̂ needs
   over-dispersed starts to be VALID, and it needs a proposal that can move.
4. Then 4 × 2 M production (≈ 4 h 25 m in parallel), postprocess, SLR gate.

**Still open, and worth answering before step 2:** what collapsed `ais_c` inside
L13tune. `embed_cov!` maps by name, so it is not 19b §5.1's positional trap, and the
seed was healthy — the collapse happened during L13tune's own adaptation. First place
to look is whether the adaptation carries a ridge / ε floor on the proposal
covariance, or whether an all-rejections stretch can drive an empirical direction to
zero irreversibly.

---

## 2. THE L13 CERTIFICATE RAN THE WRONG GREENLAND

### 2.1 How it was silent

`ladrillo_projection.jl` knew only `:stock` and `:ab`. An L13 chain carries every A+B
column, so:

* `ladrillo_gis_variant` returned `:ab` — nothing looked for the basin columns;
* `ladrillo_used_cols(:ab)` therefore did not even READ `gis_s_mid`/`gis_s_high`, so
  the gate could not have warned;
* `ladrillo_setup(gis_ab=true)` built `build_brick_nu3_gis` (A+B).

So the L13 posterior was projected at **s = 1, the partition-invariance null**, while
its shared Greenland parameters had been fitted against `s_high ≈ 0.26`. Silent
precisely BECAUSE of nesting gate [3]: at s = 1 the two Greenlands are algebraically
identical, so nothing errors and nothing looks wrong.

This is not a small perturbation. Σ k_b s_b = 0.456·1 + 0.173·0.933 + 0.371·0.255 =
**0.712**, i.e. Greenland ran ~40 % hot. The compensating inflation is visible in the
posterior — every Greenland shared parameter rose L12 → L13 (post-burn medians,
seed2026): `gis_c1` 0.0385→0.0425, `gis_c0` 0.0467→0.0585, `gis_alpha_f`
0.00409→0.00531, `gis_beta_f` 0.00762→0.00920.

### 2.2 What it was worth

`julia/diag_l13_projection_variant.jl` — three arms over the certificate's OWN chains,
burn-in and thinning, so the `:ab` arm must reproduce `slr_convergence_L13.csv`. It
does, exactly (47.89 pooled, R̂ 1.057, ESS 65.6, sd(medians) 1.411, per-chain
48.91 / 47.39 / 48.86 / 45.94).

**Nesting gate through the live kernel: `max|basins at s=1 − ab| = 1.28e-12 cm`.**
So every difference below is the fitted scales and nothing else.

| horizon | `ab_shipped` | `basins_fitted_s` | move |
|---|---|---|---|
| 2100 | 47.89 | **46.23** | −1.66 cm |
| 2150 | 76.78 | **74.71** | −2.07 cm |

Corrected per-chain 2100 medians: 47.26 / 45.58 / 47.04 / 44.16.

**Against L12's 45.53 the corrected move is +0.70 cm, not +2.36** — and the chains
still disagree by 3.10 cm, so it remains uncertifiable. **L12 stays canonical.
46.23 may NOT be quoted as a result either**: it is a corrected diagnostic on chains
that failed their gate.

### 2.3 The repair

Added `:basins` end to end — variant detection, `ladrillo_used_cols`, a builder branch
to `build_brick_nu3_gis3`, `update_gis3_shares!` at setup (the three `gis_s_b` are
UNBOUND Parameters after the builder, so this is required, not cosmetic), and the
per-draw `10.0^` scales in `ladrillo_apply_draw!`, matching `calibrate_mcmc_ext.jl`
exactly. `gis_ab=` still works for `:ab`/`:stock`; passing both must agree or it
errors.

Swept **16 callers** off `gis_ab = X === :ab` to `gis_variant = X`. That idiom mapped
`:basins` silently to `:stock`, which would have failed later with a confusing
"missing greenland_a". `diag_slr_convergence_by_chain_ladrillo.jl` now accepts
`:basins` and certifies through the 3-basin model.

**Nothing published is affected** — the canonical posterior is L12, which has no basin
columns and still reads `:ab`.

---

## 3. THE R̂ FAILURE: a degenerate proposal, not Greenland

Correcting the projection moves R̂ **1.057 → 1.061** and sd(medians) 1.411 → 1.441.
The scales shift the level and leave the disagreement alone. **The hypothesis that the
mis-projection caused the failure is wrong** — recorded because it is the obvious
thing to try next and it does not work.

### 3.1 `ais_c` is FROZEN, and the receipt is the proposal

Post-burn q05→q95 across all four chains spans 88.809052 – 88.809179, a range of
**1.3e-4**, against L12's 56.7 – 124.1. Four independent chains agreeing to seven
significant figures on one coordinate of a 7-D joint prior is a code path, not a
posterior (`~/.claude/CLAUDE.md`: suspicious uniformity ≈ bug signal).

Diagonal of the adapted covariance, seed2026, as proposal sd:

| param | L12 production | L13 production | shared seed `adapted_cov_L11tune3` |
|---|---|---|---|
| `ais_c` | 1.282 | **7.92e-07** | 0.606 |
| `ais_mu` | 0.1145 | 6.81e-04 | 0.0520 |
| `ais_bedheight0` | 0.962 | 0.156 | 0.567 |
| `ais_runoff_Ton` | 0.0137 | 0.0416 | 0.0139 |
| `ais_precip0_LOG` | 0.0276 | 0.0446 | 0.0163 |

**L12tune and L13tune seeded from the SAME file** (logs: L12tune "seeding proposal
from adapted covariance adapted_cov_L11tune3_seed2026.csv"; L13tune "name-mapped 57 of
57 rows … as L11 layout; dropped " — nothing dropped). L12tune kept it at 0.762 and
L12 production grew it to 1.282; L13tune collapsed it by ~10⁶ and L13 production
inherited the collapse. So the AIS geometry block is exploring a **5-D slice of its
7-D paleo prior** and compensating in the two directions that stayed open.

### 3.2 And that is exactly where the chains split

The four chains cluster **2+2** — {2026, 2028} high SLR, {2027, 2029} low — and the
parameters that separate the clusters with NO overlap are the AIS block, led by the
directions the degenerate proposal forced it into:

| param | 2026 | 2028 | 2027 | 2029 | r with chain SLR median |
|---|---|---|---|---|---|
| `ais_precip0_LOG` | −0.326 | −0.291 | −0.577 | −0.599 | +0.93 |
| `ais_runoff_Ton` | −20.88 | −21.74 | −17.81 | −17.82 | −0.89 |
| `anto_alpha` | 0.2435 | 0.2366 | 0.2734 | 0.2791 | −0.94 |
| `sd_ais` | 0.0214 | 0.0220 | 0.0140 | 0.0116 | +0.97 |

**So "why does L13 fail where L12 passed with the same AIS pathology" has an answer:
it is NOT the same pathology.** L12's proposal could still move `ais_c` (sd 1.28) and
its chains converged; L13's cannot (7.9e-07) and its geometry block has partitioned
into two non-communicating modes. 19b's own note that L12 started far apart in `ais_c`
and still agreed is consistent — L12's chains could MOVE. The starts were never the
control variable; the proposal is.

### 3.3 Both other 19b candidates are refuted BY MEASUREMENT

*Candidate 1, `gis_amp`.* The 4-chain-median correlation (r = 0.81 in L13 vs 0.15 in
L12) is **spurious**, and I initially believed it. Regressed WITHIN chains on the
1600-draw dump, `gis_amp` moves SLR@2100 by 1.79 cm per unit at r = 0.028 — its 0.113
between-chain spread buys **0.20 cm of the observed 3.10**. Per-chain Spearman is
+0.221 / +0.210 / +0.047 / +0.073, not even consistent in size. No dumped parameter
carries the within-chain variance; the largest stable one is `thermal_alpha`
(ρ = +0.239 / +0.279 / +0.250 / +0.269) and it accounts for 0.06 cm. **n = 4 chain
medians cannot establish a sensitivity — measure it within-chain.**

*Candidate 2, "Greenland via the TAIL, not the median".* The shift is in the **BULK**.
Restricting to draws below 50 cm, per-chain medians are 46.24 / 44.54 / 45.76 / 43.36
— a 2.88 cm spread, essentially all of the 3.10. P(>60 cm) moves too (0.215 / 0.230 vs
0.165 / 0.160, same 2+2) but is not where the median disagreement lives, and
within-chain sd is stable at 12.2–13.0 throughout. This is a location shift of the
whole distribution.

---

## 4. THE AIS SPLIT IS DEAD — and the data DO exist

19b §1.1 said no Antarctic regional product was local and implied it might not exist.
It exists and is open: six IMBIE-3 / Otosaka 2023 files (EAIS / WAIS / APIS × Gt, mm)
from the SAME BAS PDC DOI as the whole-sheet file already in the repo
(10.5285/77b64c55-…, RAMADDA entry, **Open Government Licence v3.0**), fetched
2026-08-19 with sizes verified against the catalogue listing. They are in
`data/observations/raw/`, provenance in `README_modern_extensions.md`.

`python/diag_ais_region_lit_check.py` — the Antarctic analogue of
`diag_gis_basin_lit_check.py`:

**[1] Closure PASSES.** The three regions reproduce the published whole sheet to
4.5e-07 (rate) / 3.7e-08 (cumulative). Antarctica has **no** analogue of Greenland's
1.227× Mouginot-vs-total disagreement — so absolute per-region targets would be
legitimate, the option the Greenland design did not have.

**[2] But shares are the WRONG parameterisation.** Mass-loss shares:

| window | total Gt/yr | EAIS | WAIS | APIS |
|---|---|---|---|---|
| 2002–2011 | 96.2 | **−0.207** | 0.998 | 0.209 |
| 2012–2018 | 142.8 | 0.009 | 0.936 | 0.055 |
| 1992–2020 | 92.1 | −0.031 | 0.891 | 0.140 |
| 2002–2020 | 117.0 | −0.052 | 0.896 | 0.156 |

EAIS's share is **negative in 3 of 4 windows** — East Antarctica gains mass while the
sheet loses — so the three do not live on a simplex and a `GISB`-style
`Normal(target, 0.05)` on `d[j]/dtot` has no valid target. Drift across the two
Greenland-term windows is **4.33σ** against Greenland's worst of 1.1σ, so a STATIC
shares term would be fitting a partition that moves four times harder.

**[3] As absolute rates, only WAIS is measured.** |loss|/σ on IMBIE's own
uncertainties: WAIS **1.76–2.79**, EAIS **0.02–0.25**, APIS **0.30–0.80**. EAIS and
APIS are consistent with zero in every window.

**⇒ Do not split AIS.** The one region distinguishable from zero is WAIS, already
89–100 % of the whole-sheet loss the AIS likelihood scores today (`S.ais` + the SMB
anchor) — so the split's only scorable datum duplicates the existing one, in exchange
for two geometries, two grounding lines and splitting a joint paleo MvNormal built for
one sheet (19b §1.3). Same conclusion as 19b §1.6, by a different route, and it no
longer rests on "the data don't exist."

The physical case (19b §1.4: retrograde marine WAIS vs terrestrial EAIS, MICI) is
untouched. Re-run the diagnostic if a product with real EAIS constraint appears — it
is the gate.

---

## 5. TRAPS AND CONVENTIONS FROM THIS SESSION

1. **A model can be silently WRONG rather than broken when a restructure NESTS.** The
   3-basin work's own strength — exact partition invariance at s = 1 — is what made
   the mis-projection invisible. Whenever a new sampled parameter is added, ask
   explicitly whether the PROJECTION kernel reads it; `ladrillo_used_cols` not listing
   a column is the tell, and it is easy to grep for.
2. **`X === :ab` as a boolean is a silent-downgrade idiom.** Sixteen call sites mapped
   a third variant to `:stock`. Pass the variant, not a boolean derived from it.
3. **n = 4 chain medians cannot establish a sensitivity.** The `gis_amp` correlation of
   0.81 was real arithmetic and completely misleading; the within-chain regression
   (r = 0.028) reversed it. Dump per-draw values and measure.
4. **Check the PROPOSAL, not only the starts, when R̂ fails.** A frozen coordinate
   looks like slow mixing in every parameter-level summary; the diagnostic that
   settles it is `sqrt(diag(adapted_cov))` compared against a vintage that worked.
5. **R̂ on a frozen coordinate is not interpretable** (19b said this for `ais_c` and
   was right) — but "frozen" itself is a finding, not a reason to look away.
6. macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1`.

---

## 6. FILES, TIMINGS, COMMITS

**New:** `julia/diag_l13_projection_variant.jl`, `python/diag_ais_region_lit_check.py`,
`data/observations/raw/imbie_{east_antarctica,west_antarctica,antarctic_peninsula}_2021_{Gt,mm}.csv`.
**Changed:** `julia/ladrillo_projection.jl` (the `:basins` variant),
`julia/diag_slr_convergence_by_chain_ladrillo.jl`, 15 other diagnostics (the
`gis_variant` sweep), `data/observations/raw/README_modern_extensions.md`,
`CHANGELOG.md` (19c, 19d).

**Outputs:** `outputs/mcmc/projection_variant_L13.csv`,
`projection_variant_draws_L13.csv` (1600 draws × per-arm SLR + 11 parameters — this
is the file to regress on before believing any new candidate),
`log_projvariant_L13.txt`.

**Measured timings (M4, `OPENBLAS_NUM_THREADS=1`):** the 3-arm projection diagnostic
is 211 s for 4 chains × 400 draws (~52 s/chain, dominated by the 2.2 GB CSV reads);
a full per-parameter median scan over the four chains is ~4 min in parallel.

**Commits:** `1704d46` (wrong model + frozen `ais_c`), `ef6d623` (IMBIE-3 regional
data + the split verdict). Branch pushed.

**Memory written:** `l13_wrong_model_frozen_aisc`, `ais_split_not_scorable`, both
indexed in `INDEX_slr.md`.

**Open decisions for Marcus:**
- reseed-and-re-run L13 per §1, or park L13 and stay on L12 — L12 is canonical either
  way, and nothing published depends on L13
- `GIS_ZONE` `"south"` → `"all"`, still deferred from 19b; NOT one line
  (`GIS_AMP` 1.92→2.347 and the amp prior on [1.51, 2.28] move with it), and it will
  legitimately fail `--gis-check` — regenerate the reference, do not widen the tolerance
- whether to add the high-basin volume tap (deferred; only bites near 2300)
