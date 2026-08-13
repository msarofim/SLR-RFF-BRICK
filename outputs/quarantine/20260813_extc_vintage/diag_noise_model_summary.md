# Noise-model specification, stream dependence and target grip
extC posterior medians; residual = model - target, cm; common window 1900-2023.

## A. The five streams are not independent — by construction

`dang_resid = sum(component resids) - closure + (R19 + delta ramp)`. Measured over 1900-2023: the identity explains **55.9%** of the total residual's variance, leaving a gap of sd 0.2762 cm which is the R19 glacier scope term plus the gsic delta ramp — both genuine model terms, not slop.

## B. Cross-stream correlation

Leading PC of the standardised residuals carries **50.3%** of the variance. Correlation of the AR(1) innovations (levels correlation is inflated by the shared persistence) is tabulated in `outputs/diag_noise_model_crosscorr.csv`.

## F. Item 4.3 — thermal expansion

extC `thermal_alpha` p50 = **0.1540** kg m^-3 C^-1 (90% 0.1422-0.1648), i.e. **0.1010 cm per 1e22 J**. Physics range 0.1011-0.1348. Observed Zanna+IGCC 0.1043; Zanna+Cheng 0.1133 cm per 1e22 J.
