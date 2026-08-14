# Greenland slow-channel reparameterisation — which T-bar?

`L10` posterior, within-chain, thin 50; driver `south`; commit `6856795`.

## A. Which rail is actually occupied

Posterior draws within tolerance of a bound, per chain: alpha_s 0.56%, 1.61%, 0.36%, 0.95%; beta_s 0.00%, 0.01%, 0.00%, 0.00%. The offline `A+B` optimum on record sits at alpha_s=0.00707921, beta_s=1e-06, i.e. it rails **beta_s**.

## B. Conditioning (within-chain mean |corr|)

as sampled `(alpha_s, beta_s)` **0.578**; `hindcast_mean_1900_2025` tilt=w **0.282** / tilt=alpha_s 0.251; `anchor_2015_2024` tilt=w **0.139** / tilt=alpha_s 0.575. Scan minimum 0.135 at T-bar 1.900 K.

## D. Offline refit

Native optimum nlp 17.8559. hindcast_mean_1900_2025 tilt=w 17.8559; hindcast_mean_1900_2025 tilt=alpha 17.8559; anchor_2015_2024 tilt=w 17.8559; anchor_2015_2024 tilt=alpha 17.8559. Gate (no arm worse than native): **PASS**.
