# Fossil vs non-fossil CH₄ pulse → SLR marginal

FaIR 2.2.4 has NO native fossil-CH₄ option (oxidation_matrix commented out). A fossil CH₄ pulse =
CH₄ pulse + co-emitted oxidation CO₂ (1 g CH₄ → 2.7432 g CO₂, full molar). Built by linear
superposition of the existing CH₄ and CO₂ arms (validated at GMST to 0.007%, BRICK linear by
the Step-0 sanity battery). Weighted median [5–95%]; pre-#93 & BRICK 2.0 Wong, BRICK-Mengel equal.

## A. CH₄ SLR marginal, cm per TgCH₄ — non-fossil vs fossil
| Version | basis | 2100 | 2150 | 2300 |
|---|---|---|---|---|
| pre-#93 (v1.2.1) | nonfossil | 7.23e-04 [3.82e-04, 1.39e-03] | 7.45e-04 [3.80e-04, 1.46e-03] | 5.91e-04 [2.92e-04, 1.16e-03] |
| pre-#93 (v1.2.1) | fossil | 7.55e-04 [4.00e-04, 1.44e-03] | 7.98e-04 [4.07e-04, 1.55e-03] | 6.77e-04 [3.39e-04, 1.31e-03] |
| BRICK 2.0 (v2.0.0) | nonfossil | 3.24e-04 [2.00e-04, 5.37e-04] | 2.83e-04 [1.58e-04, 5.16e-04] | 1.83e-04 [5.98e-05, 4.90e-04] |
| BRICK 2.0 (v2.0.0) | fossil | 3.38e-04 [2.10e-04, 5.59e-04] | 3.03e-04 [1.70e-04, 5.52e-04] | 2.13e-04 [7.29e-05, 5.60e-04] |
| BRICK-Mengel | nonfossil | 2.80e-04 [1.96e-04, 4.12e-04] | 2.58e-04 [1.68e-04, 4.10e-04] | 2.12e-04 [1.20e-04, 4.19e-04] |
| BRICK-Mengel | fossil | 2.93e-04 [2.06e-04, 4.29e-04] | 2.76e-04 [1.81e-04, 4.37e-04] | 2.44e-04 [1.40e-04, 4.73e-04] |

## B. Fossil premium (fossil ÷ non-fossil, median)
| Version | 2100 | 2150 | 2300 |
|---|---|---|---|
| pre-#93 (v1.2.1) | 1.044× | 1.071× | 1.145× |
| BRICK 2.0 (v2.0.0) | 1.044× | 1.072× | 1.164× |
| BRICK-Mengel | 1.047× | 1.072× | 1.149× |

## C. Per GtCO₂eq (non-fossil GWP-100=27.0 ×37.04; fossil GWP-100=29.8 ×33.56), vs CO₂
Median cm/GtCO₂(eq). 'CO₂' = the CO₂ pulse marginal (cm/GtCO₂) for reference.
| Version | quantity | 2100 | 2150 | 2300 |
|---|---|---|---|---|
| pre-#93 (v1.2.1) | CO₂ | 1.15e-02 | 1.86e-02 | 3.10e-02 |
| pre-#93 (v1.2.1) | CH₄ non-fossil (÷27) | 2.68e-02 | 2.76e-02 | 2.19e-02 |
| pre-#93 (v1.2.1) | CH₄ fossil (÷29.8) | 2.53e-02 | 2.68e-02 | 2.27e-02 |
| BRICK 2.0 (v2.0.0) | CO₂ | 5.36e-03 | 7.35e-03 | 1.07e-02 |
| BRICK 2.0 (v2.0.0) | CH₄ non-fossil (÷27) | 1.20e-02 | 1.05e-02 | 6.77e-03 |
| BRICK 2.0 (v2.0.0) | CH₄ fossil (÷29.8) | 1.14e-02 | 1.02e-02 | 7.13e-03 |
| BRICK-Mengel | CO₂ | 4.69e-03 | 6.73e-03 | 1.15e-02 |
| BRICK-Mengel | CH₄ non-fossil (÷27) | 1.04e-02 | 9.55e-03 | 7.85e-03 |
| BRICK-Mengel | CH₄ fossil (÷29.8) | 9.82e-03 | 9.27e-03 | 8.18e-03 |

## D. Component decomposition of the fossil premium (fossil − non-fossil, cm/TgCH₄ median)
The premium is the oxidation-CO₂ response, so it lands in the CO₂-driven components (TE, GIS, AIS).
| Component | pre93 2100 | brick2 2100 | mengel 2100 | pre93 2300 | brick2 2300 | mengel 2300 |
|---|---|---|---|---|---|---|
| total | 3.15e-05 | 1.41e-05 | 1.31e-05 | 8.55e-05 | 2.99e-05 | 3.16e-05 |
| ais | -2.86e-07 | 3.67e-07 | 2.55e-06 | -1.26e-07 | 4.37e-06 | 1.02e-05 |
| gsic | 3.84e-06 | 4.13e-06 | 8.34e-07 | 2.37e-06 | 1.90e-06 | 6.06e-07 |
| gis | 2.52e-05 | 1.36e-06 | 1.41e-06 | 7.58e-05 | 4.63e-06 | 4.71e-06 |
| te | 2.86e-06 | 8.55e-06 | 7.96e-06 | 5.19e-06 | 1.49e-05 | 1.40e-05 |
| lws | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 |
