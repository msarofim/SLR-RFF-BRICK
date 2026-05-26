# Quarantine: confabulated "Hermans" TSLS citation

**Date:** 2026-05-25
**Bug:** The script `slr_pulse_vs_hermans_tsls.py` attributed its
TSLS reference value to "Hermans et al. 2021, Ocean Science 17:181,"
which is fabricated. There is no Hermans first-author paper in
Ocean Science for 2020-2022.

The Ocean Science 17:181-186 paper that introduced the TSLS concept
is actually **Grinsted & Christensen (2021)**. The author name was
the confabulation; the volume/page is real and belongs to a real
paper by a different first author.

The TSLS value used (0.40 ± 0.05 m/century/K) was also not traceable
to either Grinsted & Christensen 2021 or its follow-up Grinsted et
al. 2022 (Earth's Future, e2022EF002696). Grinsted 2022 reports
GMSL TSLS values of 5.3 ± 1.0 mm/yr/K (2016-2050 models), 3.0 ± 0.4
(2051-2100 models), 3.3 ± 0.4 (observations) — none of which is
4.0 mm/yr/K = 0.40 m/century/K.

## Files

- `slr_pulse_vs_hermans_tsls.py` — script with the confabulated
  citation and unsourced value
- `slr_pulse_vs_hermans_tsls.png` / `.pdf` — the figure outputs

## Canonical replacement

`python/scripts/substack/brick_vs_grinsted_tsls_components.py`

The replacement does a far stronger comparison: per-component
(steric / GIS / AIS / GSIC / GMSL), per-period (2016-2050 /
2051-2100), against properly-sourced Grinsted 2022 reference values
for both CMIP6 models and historical observations. Computes both
baseline TSLS (cross-cell regression Grinsted-style) and pulse-
marginal TSLS (per-cell ratio of paired Δrate / ΔT_pulse). The
comparison surfaces the AIS-tipping nonlinearity (baseline 6.06
vs. pulse 0.09 mm/yr/K) as a feature of BRICK that the single-
number Hermans comparison was masking.

Outputs of the replacement:
- `outputs/substack/brick_vs_grinsted_tsls_components.csv`
- `outputs/substack/brick_vs_grinsted_tsls_components.{png,pdf}`
