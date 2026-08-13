# Note 2026-08-14 — thread 4 item 1.0 is DONE, and it changes the noise-model spec

Prerequisite from `handoff_2026-08-13d_threads_4_and_5.md` §1.0: re-point
`diag_noise_model_and_grip.py` and `diag_gis_likelihood_leverage.py` at L10 and
re-run **before** designing anything, because the design in §1.1 rests on numbers
those two produce and both were pinned to the quarantined extC vintage.

Done. Both are now `--vintage {L10,extC}` (default **L10**), every output path and
label carries the tag, and `--vintage extC` reproduces the recorded extC numbers
(gis step cost 27.69 vs 27.71, net +25.36 vs +25.37). The eight extC-vintage
output files moved into `outputs/quarantine/20260813_extc_vintage/` (README §7).
Full numbers in the CHANGELOG entry for 2026-08-14; this note is the part that
changes what thread 4 should DO.

## Cost

~40 min → **2 s and 18 s**. Both scripts touched the 4 × 2.2 GB chains only for
posterior medians, and the 10,000-member subsample is a uniform stride over the
pooled post-burn draws, so its marginal medians ARE the pooled medians. Verified
against a stride-100 read of all four L10 chains: agreement < 0.01 posterior sd on
all 11 parameters. `--post-source=chains` restores the full read.
(`cut -d, -f` does this extraction in 46 s per chain; `awk -F,` on 55 fields does
not finish in 2 minutes. Worth knowing for the next chain-level question.)

## What changed for the spec — three items

### 1. §1.1's Greenland premise no longer applies to Greenland
The mechanism `diag_gis_likelihood_leverage.py` identified — `rho_gis` = 0.985
reclassifying a decades-long miss as correlated noise, **n_eff 0.93** — is gone on
the shipped model. A+B fits the window, so the sampled noise process collapses:
rho 0.985 → **0.789**, stationary sd 0.318 → **0.025 cm**, n_eff 0.93 → **14.85**,
and the cost of a 0.65 cm systematic step over 1942-1982 goes 27.7 → **311.8**
log-likelihood units. The gis residual over that window is now **+0.008 cm** (was
−0.822).

It was the module, not the noise model. That does not retire the discrepancy-term
question — it moves it off Greenland.

### 2. Only TWO streams put the noise specification under load
New discriminator, `resid sd / mean band σ`. A stream whose residual sits well
inside its own observation band gives the noise model nothing to do:

| stream | extC | L10 |
|---|---|---|
| ais | 0.17 | 0.17 |
| gsic | 1.06 | **1.06** |
| gis | **1.84** | 0.33 |
| steric | 0.90 | **0.95** |
| dang | 0.21 | 0.12 |

Ljung-Box still rejects every member of the AR(1) family on every stream
(p = 0.0000 throughout; the self-test returns p = 0.84 on data it generated), so
"no member of this family whitens any of them" **stands**. But BIC now puts white
*marginally ahead* of AR(1) on ais/gis/dang (−2.5 to −4.2) and far behind on gsic
(+18.7) and steric (+108.0). So design axis 1 should be scoped to **gsic and
steric**, which is a much narrower change than replacing AR(1) on five streams.

### 3. The "56% redundant" total stream is 100% redundant — the 56% was a p50 artefact
Section A's "variance explained by the identity" read 55.9% on extC and **−322%**
on L10 with the algebra unchanged. Diagnosed at the source instead of from the
statistic: `calibrate_mcmc_ext.jl` scores `tot_full = ais + gsic_tot + gis + te`
plus observed LWS, while the gsic COMPONENT channel scores `gsic_flow` (hindcast
scope), so **per draw** `total_model − Σ(component_models) = gsic_tot −
gsic_flow` = the R19 seam, exactly.
`posterior_predictive_ladrillo.jl` builds its `total` the same way. The
diagnostic evaluates this on posterior MEDIANS, and medians are not additive; the
L10 total residual is half extC's (sd 0.246 vs 0.415 cm) while the non-additivity
term grew with the Greenland distribution change (gap sd 0.276 → 0.505 cm), which
is the entire sign flip. Section A now states the per-draw exactness and labels
the p50 number as not-the-redundancy.

**This strengthens design axis 2 rather than weakening it.** The total channel
carries exactly one piece of model information the components do not (the R19
seam), plus observed LWS, plus its own likelihood weight — and §E confirms it is
still the loosest constraint in every window (σ on a window-mean offset
0.232-0.565 cm, against 0.014-0.062 for ais/gis). Dropping it costs one seam
term, not 44% of an independent constraint.

## Unchanged
- **Item 4.3 (TE) still passes**: `thermal_alpha` p50 0.1502 (was 0.1540) →
  0.0986 cm per 1e22 J, against observed 0.1043 (Zanna+IGCC) / 0.1133
  (Zanna+Cheng), physics range 0.1011-0.1348. Low-side, as before.
- The grip ordering by window, and the total as the loosest constraint.

## Thread 5, first step — done too, and it found something

`scope_greenland_bochow2026.py` now reads the Ladrillo column from
`outputs/ssps_components_2300_L10.csv` (median + posterior 5-95%) instead of
three hardcoded extC numbers. At 2100 Ladrillo and Bochow are within 1.7-4.3 cm.
At 2300 Bochow is 3.1× / 3.7× / 4.3× higher (7.8/14.6/39.1 vs 24.5/54.5/167.1 cm).

The finding that matters: **at 2300, A+B is 9.5-11.4 cm BELOW the stock SIMPLE it
replaced, on every scenario** (−59% / −43% / −20%), even though at 2100 it is
+4.78 cm above on SSP5-8.5. It is not the amp law — the law removes 6.9% of the
driver at SSP1-2.6/2300 and 14.0% at SSP5-8.5/2300, so its damping runs opposite
to the effect, and the least-damped scenario declines the most. The module chosen
for its 2100 scenario spread relaxes LESS in the long run than the one it
replaced. Under SSP1-2.6 it delivers 1.6 cm of further Greenland loss between
2100 and 2300 against a Bochow committed loss of 3.0-3.6 m SLE at that sustained
warming.

This is thread 5's open question with a number on it, and it lines up with the
already-recorded fact that the slow channel carrying the multi-millennial
commitment is the one the 1900-2024 record cannot identify. Bochow's own caveats
are unchanged and still binding (preprint in open discussion; UQ and verification
concerns; code availability a placeholder), and its 2300 5-95% is very wide
(4.5-140.7 cm at SSP1-2.6) — but the median gap is not inside that noise.

## What is now waiting on Marcus

The three design axes in §1.1 are unblocked and their evidence is current, but
all three are still HIS calls, and item 2 is the one that changes what the
calibration is:

1. **What replaces AR(1)** — and now, on which streams. The measurement says
   gsic + steric; a discrepancy term on those two is defensible, on all five is
   not (three of them are band-dominated).
2. **The total stream** — drop, down-weight, or model the cross-covariance. The
   redundancy is exact, so "dropping loses little" is now a stronger claim than
   when it was written.
3. **Whether the target sigmas get re-derived** in the same pass
   (`prep_recalib_targets_ext.py`'s anchor-shaped closure sigma caveat).

Item 1.2 (Greenland slow-channel reparameterisation) is independent of all three
and needs no further measurement — it can start whenever.
