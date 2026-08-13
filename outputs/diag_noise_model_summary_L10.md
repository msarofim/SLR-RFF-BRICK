# Noise-model specification, stream dependence and target grip (L10)
Vintage: **L10 (Ladrillo 1.0; Greenland A+B in the joint likelihood)**; posterior medians from the subsample; residual = model - target, cm; common window 1900-2023.

## A. The five streams are not independent — by construction

Per draw the tie is EXACT: `calibrate_mcmc_ext.jl` scores `tot_full = ais + gsic_tot + gis + te` plus observed LWS against the total target, while the gsic component channel scores `gsic_flow` (hindcast scope), so `total_model − Σ(component_models)` is exactly the R19 seam. The total stream is **100% redundant with the components** apart from that one model term, the observed LWS, and its own likelihood weight.

The p50-level statistic below is a SHADOW of that identity, not a measure of it: medians are not additive, so it reads **-322.2%** here over 1900-2023 with a gap of sd 0.5051 cm. It was 55.9% on extC and −322% on L10 with the algebra unchanged — the L10 total residual is half the size, so the same non-additivity swamps it. Do not quote it as the redundancy.

## B. Cross-stream correlation

Leading PC of the standardised residuals carries **29.2%** of the variance. Correlation of the AR(1) innovations (levels correlation is inflated by the shared persistence) is tabulated in `outputs/diag_noise_model_crosscorr.csv`.

## C. Which streams put the noise model under load

resid sd / mean band σ: ais 0.17, gsic 1.06, gis 0.33, steric 0.95, dang 0.12. Only **gsic, steric** exceed 0.5, i.e. only there does the residual approach its own observation band; on the rest the likelihood is band-dominated and 'AR(1) vs white' compares two terms that barely enter. Full BIC table in `diag_noise_model_streams_L10.csv`.

## F. Item 4.3 — thermal expansion

L10 `thermal_alpha` p50 = **0.1502** kg m^-3 C^-1 (90% 0.1380-0.1625), i.e. **0.0986 cm per 1e22 J**. Physics range 0.1011-0.1348. Observed Zanna+IGCC 0.1043; Zanna+Cheng 0.1133 cm per 1e22 J.
