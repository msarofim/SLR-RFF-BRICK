#!/usr/bin/env python3
"""
diag_gmip3_realised_fraction.py — the REALISED FRACTION phi(t) from GlacierMIP3,
per Ladrillo block, and what it says about our late-phase relaxation.

WHY GLACIERMIP3 RATHER THAN OGGM (Marcus, 2026-08-14, and he is right twice over)
  * It is 8 glacier models — PyGEM-OGGM_v13, GloGEMflow, GloGEMflow3D, OGGM_v16,
    GLIMB, Kraaijenbrink, GO, CISM2 — against OGGM's one.
  * **OGGM_v16 is a MEMBER of it.** Constraining on the OGGM archive would be
    using one member of an ensemble we already hold, and discarding the other
    seven. That is not a close call.
  * It is a CONSTANT-CLIMATE commitment experiment: each `period_scenario` holds a
    fixed 20-yr climate and integrates 5000 years, with the warming level of that
    climate published as `temp_ch_ipcc`. So it is indexed on WARMING LEVEL, which
    removes the scenario-label/ECS confound that made the OGGM comparison
    ambiguous (its 2300 branch is 6 GCMs skewed to high sensitivity).
  * And it carries the full TRANSIENT, not just the steady state — which is what
    the project has been using it for (the committed `com*` rungs are its t->inf
    limit). The same file answers the response-time question for free.

WHAT THIS MEASURES. phi(t) = (loss at t) / (loss at equilibrium), per block, at a
sustained warming level near the one our ssp126 run settles at (1.74 K over
2290-2300). Ladrillo's own phi at 2300 is 0.61-0.81 by block; if the 8-model
ensemble puts phi near 1.0 at the same horizon, our late-phase approach is too
slow — and since our kappa sits within 17-19% of GlacierMIP3's own tau50 anchor,
the cause is not kappa.

CAVEAT, stated: GlacierMIP3 holds the climate CONSTANT while our ssp126 rises to
1.84 K near 2100 and settles to 1.74 K. The comparison is of response SHAPE at a
comparable level, not a scenario replay.

  source ~/climate-env/bin/activate
  python3 python/diag_gmip3_realised_fraction.py
Writes outputs/diag_gmip3_realised_fraction.csv
"""
import os

import numpy as np
import pandas as pd
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NC = os.path.join(REPO, "data/observations/raw/gmip3/GMIP3_reg_glacier_model_data",
                  "all_shifted_glacierMIP3_Feb12_2024_models_all_rgi_regions_sum_"
                  "scaled_extended_repeat_last_101yrs_via_5yravg.nc")
OUT = os.path.join(REPO, "outputs/diag_gmip3_realised_fraction.csv")

BLOCKS = {"R19": ["19"], "SLOWP": ["03", "09", "07", "06"],
          "FAST": ["01", "04", "17", "13", "14", "02", "15", "08", "10", "11",
                   "16", "18", "12"]}
# the constant-climate scenario nearest our ssp126 settled level (1.74 K)
SCENARIO = "2021-2040_ssp126"
HORIZONS = [80, 180, 280, 500, 1000]      # years after 2020 -> 2100, 2200, 2300, ...
# STEADY STATE: the archive's last ~50 timesteps are NaN, and an xarray sum over
# regions silently turns all-NaN into 0.0 — which read as "all ice gone" and
# corrupted the first version of this diagnostic. The trajectory is flat from
# t~300 to t=4950, so average a window that ends well before the NaN tail and
# aggregate with skipna=False so a missing region can never masquerade as zero.
EQ_WIN = (4850, 4950)
# Ladrillo's own phi at 2300 under ssp126 (diag_block_committed_vs_realised.jl)
LADRILLO_PHI_2300 = {"R19": 0.65, "SLOWP": 0.61, "FAST": 0.81}


def main():
    d = xr.open_dataset(NC)
    tk = d.temp_ch_ipcc.sel(period_scenario=SCENARIO).to_pandas()
    print("GlacierMIP3 realised fraction phi(t), 8 models, constant climate")
    print(f"  scenario {SCENARIO}: warming level {tk.mean():.2f} K "
          f"[{tk.min():.2f}, {tk.max():.2f}] across {len(tk)} GCMs")
    print(f"  (our ssp126 settles at 1.74 K over 2290-2300)\n")

    vol = d["volume_m3"].sel(period_scenario=SCENARIO)
    rows = []
    for b, mem in BLOCKS.items():
        v = vol.sel(rgi_reg=mem).sum("rgi_reg", skipna=False)   # NaN-propagating
        v0 = v.sel(year_after_2020=0.0)
        loss = (v0 - v)                                   # volume lost since 2020
        loss_eq = loss.sel(year_after_2020=slice(*EQ_WIN)).mean("year_after_2020")
        print(f"  {b}")
        print(f"    {'t (yr)':>7s} {'year':>6s} {'phi median':>11s} "
              f"{'phi min-max over 8 models':>28s}")
        for h in HORIZONS:
            phi = (loss.sel(year_after_2020=float(h)) / loss_eq)
            # collapse GCMs first, then look at the MODEL spread — the model
            # spread is the quantity a term would have to span
            per_model = phi.median("gcm").to_pandas().dropna()
            med = float(per_model.median())
            print(f"    {h:7d} {2020 + h:6d} {med:11.3f} "
                  f"{'[' + f'{per_model.min():.3f}, {per_model.max():.3f}' + ']':>28s}")
            rows.append(dict(block=b, t_after_2020=h, year=2020 + h,
                             phi_median=med, phi_min=float(per_model.min()),
                             phi_max=float(per_model.max()),
                             n_models=int(per_model.size)))
        p280 = [r for r in rows if r["block"] == b and r["t_after_2020"] == 280][0]
        lp = LADRILLO_PHI_2300[b]
        print(f"    Ladrillo phi at 2300 = {lp:.2f} against GlacierMIP3 "
              f"{p280['phi_median']:.3f} "
              f"[{p280['phi_min']:.3f}, {p280['phi_max']:.3f}]\n")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print("  READING. If GlacierMIP3's phi at 2300 brackets Ladrillo's, our")
    print("  late-phase relaxation is defensible and the OGGM gap was one model.")
    print("  If GlacierMIP3 sits well above, the stall is ours — and since kappa")
    print("  matches GlacierMIP3's own tau50 anchor to 17-19%, the remaining")
    print("  suspect is the FIXED exponent nu in rate = kappa * exc^nu, which")
    print("  drives the rate to zero as the excess temperature closes.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
