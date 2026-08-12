#!/usr/bin/env python3
"""
ladrillo_posterior_summary.py — the Ladrillo posterior parameter table.

Median and 5-95% for every sampled parameter of the accepted extC posterior,
next to the prior it was sampled under, split into the blocks a reader needs to
reimplement the model: the three-reservoir glacier block, the glacier scope and
ledger terms, the Antarctic block, and the remaining BRICK modules.

Priors are transcribed from julia/calibrate_mcmc_ext.jl (the per-block glacier
priors are built there from outputs/extc_block_constants.csv, so those entries
are read from the constants file rather than hard-coded).

  python3 python/ladrillo_posterior_summary.py
Writes outputs/ladrillo_posterior_summary.csv and prints a markdown table.
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTERIOR = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
CONSTANTS = os.path.join(REPO, "outputs/extc_block_constants.csv")
OUT = os.path.join(REPO, "outputs/ladrillo_posterior_summary.csv")

BLOCKS = ["R19", "SLOWP", "FAST"]
# Priors not derived from the block constants, as (prior, source).
FIXED_PRIORS = {
    "gic_amp_R19":   ("N(0.72, 0.15) on [0.58, 0.88]", "cross-dataset obs amplification"),
    "gic_amp_SLOWP": ("N(2.50, 0.45) on [1.80, 3.50]", "cross-dataset obs amplification"),
    "gic_amp_FAST":  ("N(1.45, 0.15) on [1.33, 1.82]", "cross-dataset obs amplification"),
    "gic_u_unch":    ("flat [14.5, 41.8] mm", "Parkes & Marzeion 2018 uncharted ice"),
    "gic_delta":     ("N(0, 0.30) mm/yr", "Marzeion-2015 early-segment rate bias"),
    "gic_u_pre":     ("flat [0, 25] mm", "pre-1901 uncharted set-aside"),
    "gic_s_r5":      ("N(2.5, 2) on [0, 8] mm", "region-5 share of the 19th-century datum"),
    "ais_gmst_amp":  ("N(1.08, 0.15)", "CMIP6 Antarctic amplification, land frame"),
    "ais_ocean_temperature₀": ("N(0.72, 0.50) on [0.50, 2.00]", "calibrate_mcmc_ext.jl"),
}
GROUPS = [
    ("glacier reservoirs",
     [f"gic_{p}_{b}" for b in BLOCKS for p in ("a", "b", "T_off", "log10_kappa")]),
    ("glacier temperature amplification", [f"gic_amp_{b}" for b in BLOCKS]),
    ("glacier scope and ledger", ["gic_u_unch", "gic_delta", "gic_u_pre", "gic_s_r5"]),
    ("Antarctic ice sheet",
     ["ais_ocean_temperature₀", "antarctic_alpha", "antarctic_nu", "anto_alpha",
      "anto_beta", "antarctic_temp_threshold", "antarctic_lambda", "antarctic_gamma",
      "antarctic_kappa", "ais_gmst_amp", "ais_mu", "ais_bedheight0", "ais_slope",
      "ais_iceflow0", "ais_precip0_LOG", "ais_runoff_Ton", "ais_c"]),
    ("Greenland and thermal expansion",
     ["greenland_a", "greenland_b", "greenland_alpha", "greenland_beta", "greenland_v0",
      "thermal_alpha"]),
    ("observation error model (AR(1) per target series)",
     [f"{p}_{s}" for s in ("ais", "gsic", "gis", "steric", "dang") for p in ("sd", "rho")]),
]


def block_priors():
    """The per-reservoir priors the calibrator builds from the block constants."""
    bc = pd.read_csv(CONSTANTS).set_index("block")
    out = {}
    for b in BLOCKS:
        r = bc.loc[b]
        out[f"gic_a_{b}"] = (f"N({r.a0:.3f}, {r.a0_sig:.3f}) m SLE",
                             "Farinotti 2019 inventory")
        out[f"gic_b_{b}"] = (f"flat [0.05, 3.0], start {r.b_fit_obsfit:.3f}",
                             "constrained by the GlacierMIP3 rung likelihood")
        out[f"gic_T_off_{b}"] = (f"flat [-3.0, 1.0], start {r.T_off_fit_obsfit:.3f}",
                                 "constrained by the GlacierMIP3 rung likelihood")
        out[f"gic_log10_kappa_{b}"] = (
            f"N({np.log10(r.kappa_anch_obsfit):.3f}, 0.114)",
            "tau50 anchored to the regional response times")
    return out


def main():
    post = pd.read_csv(POSTERIOR)
    priors = {**block_priors(), **FIXED_PRIORS}
    rows = []
    for group, names in GROUPS:
        for name in names:
            if name not in post.columns:
                raise KeyError(f"{name} is not a column of the posterior subsample")
            v = post[name].to_numpy()
            prior, source = priors.get(name, ("outputs/param_priors.csv", "BRICK prior file"))
            rows.append(dict(group=group, parameter=name, median=np.median(v),
                             p05=np.percentile(v, 5), p95=np.percentile(v, 95),
                             prior=prior, prior_source=source))
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print(f"Ladrillo posterior — {len(post)} draws from {os.path.basename(POSTERIOR)}\n")
    for group, _ in GROUPS:
        sub = df[df.group == group]
        print(f"**{group}**\n")
        print("| parameter | median | 5-95% | prior |")
        print("|---|---|---|---|")
        for _, r in sub.iterrows():
            # r.median would resolve to the Series METHOD, not the column
            print(f"| `{r['parameter']}` | {r['median']:.4g} | "
                  f"{r['p05']:.4g} – {r['p95']:.4g} | {r['prior']} |")
        print()
    print(f"wrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
