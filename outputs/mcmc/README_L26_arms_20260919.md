# L26 candidate arms (2026-09-19), single chain each, 500k iterations, seed 2026, start = MAP (no --overdisperse)
Common: --gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --toff-lo=-4 --precip-reparam
  L26a  --obs-corr-len=20   (the candidate: bands as correlated error, 20-yr e-folding)
  L26b  --obs-corr-len=0    (control: diagonal bands as in L24 — isolates the error-model change)
  L26c  --obs-corr-len=50   (sensitivity: longer correlation)
55 parameters (L24: 58): gic_delta, d2_gsic_1, d2_gsic_2 not sampled; ais_precip0_LOG replaced by ais_precip_u = log P0 + kappa*TBAR_ANT.
Priors: the eight non-geometry DAIS parameters on the DAISfastdyn paleo marginals (outputs/paleo_dais_marginals.csv), thermal_alpha Uniform(0.05, 0.3).
Machine: nine R multistart jobs from another session (load ~32/10 cores) — expect 2-3x the uncontended 50 min.
