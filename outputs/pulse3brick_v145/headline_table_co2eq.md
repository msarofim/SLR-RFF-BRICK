# Pulse→SLR headline, CH₄ expressed in GtCO₂eq (AR6 GWP-100 = 27.0, non-fossil)

CH₄ marginal converted cm/TgCH₄ → cm/GtCO₂eq via ×(1000/27.0) = ×37.037.
Non-fossil GWP chosen because the FaIR pulse has NO direct CH₄→CO₂ oxidation flux — verified
EMPIRICALLY (FaIRtoFrEDI/test_ch4_pulse_co2_response.py): a +300 TgCH₄ pulse moves CO₂ by only
5.3e-3 ppm (5% of full-oxidation), and that response goes EXACTLY to zero (bit-identical CO₂) when
the CO₂ carbon-cycle temperature feedback is disabled — i.e. the CO₂ response is the climate-carbon
feedback, not oxidation. AR6 GWP-100 includes that feedback for BOTH fossil (29.8) and non-fossil
(27.0); the fossil/non-fossil delta is purely the oxidation CO₂, which this config does not model →
27.0 is correct. Weighted median [5–95%], paired FaIR-RFF LHS-10k.
pre-#93 & BRICK 2.0 Wong-weighted (ESS/N=0.5); BRICK-Mengel equal-weighted. Units: cm per GtCO₂(eq).

## Total marginal SLR — CO₂ vs CH₄(as CO₂eq), median [5–95]
| Version | Gas | 2100 | 2150 | 2300 |
|---|---|---|---|---|
| pre-#93 (v1.2.1) [Wong] | CO₂ | 1.15e-02 [5.98e-03, 2.17e-02] | 1.86e-02 [9.05e-03, 3.63e-02] | 3.10e-02 [1.40e-02, 5.79e-02] |
| pre-#93 (v1.2.1) [Wong] | CH₄→CO₂eq | 2.68e-02 [1.41e-02, 5.13e-02] | 2.76e-02 [1.41e-02, 5.39e-02] | 2.19e-02 [1.08e-02, 4.31e-02] |
| BRICK 2.0 (v2.0.0) [Wong] | CO₂ | 5.36e-03 [3.29e-03, 8.69e-03] | 7.35e-03 [4.02e-03, 1.32e-02] | 1.07e-02 [4.21e-03, 2.73e-02] |
| BRICK 2.0 (v2.0.0) [Wong] | CH₄→CO₂eq | 1.20e-02 [7.42e-03, 1.99e-02] | 1.05e-02 [5.85e-03, 1.91e-02] | 6.77e-03 [2.21e-03, 1.81e-02] |
| BRICK-Mengel [equal] | CO₂ | 4.69e-03 [3.23e-03, 6.68e-03] | 6.73e-03 [4.19e-03, 1.03e-02] | 1.15e-02 [5.99e-03, 2.11e-02] |
| BRICK-Mengel [equal] | CH₄→CO₂eq | 1.04e-02 [7.24e-03, 1.53e-02] | 9.55e-03 [6.22e-03, 1.52e-02] | 7.85e-03 [4.45e-03, 1.55e-02] |

## Ratio CH₄(as CO₂eq) ÷ CO₂  — per-CO₂eq SLR potency of CH₄ (median)
| Version | 2100 | 2150 | 2300 |
|---|---|---|---|
| pre-#93 (v1.2.1) | 2.34× | 1.48× | 0.71× |
| BRICK 2.0 (v2.0.0) | 2.24× | 1.42× | 0.63× |
| BRICK-Mengel | 2.21× | 1.42× | 0.68× |

## Per-component, CH₄ as CO₂eq (weighted median, cm/GtCO₂eq)
| Component | pre93 2100 | brick2 2100 | mengel 2100 | pre93 2300 | brick2 2300 | mengel 2300 |
|---|---|---|---|---|---|---|
| total | 2.68e-02 | 1.20e-02 | 1.04e-02 | 2.19e-02 | 6.77e-03 | 7.85e-03 |
| ais | -3.21e-04 | 1.73e-04 | 2.19e-03 | -2.24e-04 | 7.65e-04 | 3.11e-03 |
| gsic | 3.61e-03 | 3.84e-03 | 8.22e-04 | 8.34e-04 | 6.73e-04 | 1.80e-04 |
| gis | 2.12e-02 | 1.29e-03 | 1.30e-03 | 1.99e-02 | 1.49e-03 | 1.52e-03 |
| te | 2.15e-03 | 6.27e-03 | 5.87e-03 | 1.05e-03 | 3.03e-03 | 2.86e-03 |
