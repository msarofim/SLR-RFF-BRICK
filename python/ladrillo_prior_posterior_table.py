#!/usr/bin/env python3
"""
ladrillo_prior_posterior_table.py — the prior / posterior table for every sampled Ladrillo
parameter (the GMD paper's appendix, modelled on Wong et al. 2017 GMD Tables A1–A7).

  python3 python/ladrillo_prior_posterior_table.py --tag=L24

Inputs
  outputs/ladrillo_priors_<tag>.csv   — written by `calibrate_mcmc_ext.jl --dump-priors` run with
                                        the production flags: the prior AS THE CALIBRATOR SCORES
                                        IT (FREE, PRIOR_SKIP, the paleo block, the noise block),
                                        never transcribed by hand. Regenerate with
                                        `julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 100 2026
                                         --tag=L24 --gis-ordered --gis-basins2 --amp-mu=1.09
                                         --amp-sigma=0.180 --dump-priors`.
  data/MimiBRICK/parameters_subsample_brick_mengel_<tag>.csv — the shipped posterior (10,000 draws).
Outputs
  outputs/ladrillo_prior_posterior_<tag>.csv  (+ provenance column)
  outputs/ladrillo_prior_posterior_<tag>.md   (the appendix table, grouped by block)

GATES (hard-fail): the prior file's parameter order == the posterior's columns; every posterior
draw lies inside its prior bounds (rho < 0.99); the row count == 58. A prior row without a
description entry below also fails — a parameter must not appear in the paper without its units.

Only the DESCRIPTION/UNITS column is hand-written here. Sources: DAIS units from Wong et al. 2017
Table A4; glacier-block units from julia/glaciers_nu3_component.jl (m SLE, K glacier-frame,
log10 kappa); Greenland from julia/greenland_ab_component.jl (m SLE); ledger/scope terms from
calibrate_mcmc_ext.jl comments (mm); d2 in cm (unit-RMS basis); noise in cm (residuals in cm).
"""
import argparse
import os
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# block -> (heading, [parameter names in table order])
BLOCKS = [
    ("Glacier reservoirs (three blocks; SLOWG = SLOWP and FASTG = FAST in the code)", [
        "gic_a_R19", "gic_b_R19", "gic_T_off_R19", "gic_log10_kappa_R19",
        "gic_a_SLOWP", "gic_b_SLOWP", "gic_T_off_SLOWP", "gic_log10_kappa_SLOWP",
        "gic_a_FAST", "gic_b_FAST", "gic_T_off_FAST", "gic_log10_kappa_FAST"]),
    ("Glacier regional temperature amplification", ["gic_amp_R19", "gic_amp_SLOWP", "gic_amp_FAST"]),
    ("Glacier scope and ledger terms (hindcast-target constructs)", ["gic_u_unch", "gic_delta", "gic_u_pre", "gic_s_r5"]),
    ("Greenland ice sheet (two channels, two basins)", [
        "gis_c1", "gis_c0", "gis_f", "gis_alpha_f", "gis_beta_f", "gis_slow_ell", "gis_slow_w",
        "gis_s_high", "gis_amp"]),
    ("Antarctic ice sheet (DAIS) and Antarctic ocean", [
        "ais_gmst_amp", "ais_ocean_temperature₀", "antarctic_alpha", "antarctic_nu",
        "antarctic_temp_threshold", "anto_alpha", "anto_beta", "antarctic_lambda",
        "antarctic_gamma", "antarctic_kappa",
        "ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0", "ais_precip0_LOG", "ais_precip_u",
        "ais_runoff_Ton", "ais_c"]),
    ("Thermal expansion", ["thermal_alpha"]),
    ("Model-discrepancy coefficients", ["d2_gsic_1", "d2_gsic_2", "d2_steric_1", "d2_steric_2"]),
    ("Observation-error model (AR(1) per target series)", [
        "sd_ais", "rho_ais", "sd_gsic", "rho_gsic", "sd_gis", "rho_gis", "sd_steric", "rho_steric"]),
]

DESC = {
    "gic_a_R19": ("Committed-loss scale a, RGI 19", "m SLE"),
    "gic_b_R19": ("Equilibrium temperature sensitivity b, RGI 19", "K⁻¹ (glacier frame)"),
    "gic_T_off_R19": ("Equilibrium temperature offset T_off, RGI 19", "K rel. 1850–1900, glacier frame"),
    "gic_log10_kappa_R19": ("log₁₀ of the response-rate constant κ, RGI 19", "log₁₀(yr⁻¹ K⁻ν)"),
    "gic_a_SLOWP": ("Committed-loss scale a, SLOWG", "m SLE"),
    "gic_b_SLOWP": ("Equilibrium temperature sensitivity b, SLOWG", "K⁻¹ (glacier frame)"),
    "gic_T_off_SLOWP": ("Equilibrium temperature offset T_off, SLOWG", "K rel. 1850–1900, glacier frame"),
    "gic_log10_kappa_SLOWP": ("log₁₀ of the response-rate constant κ, SLOWG", "log₁₀(yr⁻¹ K⁻ν)"),
    "gic_a_FAST": ("Committed-loss scale a, FASTG", "m SLE"),
    "gic_b_FAST": ("Equilibrium temperature sensitivity b, FASTG", "K⁻¹ (glacier frame)"),
    "gic_T_off_FAST": ("Equilibrium temperature offset T_off, FASTG", "K rel. 1850–1900, glacier frame"),
    "gic_log10_kappa_FAST": ("log₁₀ of the response-rate constant κ, FASTG", "log₁₀(yr⁻¹ K⁻ν)"),
    "gic_amp_R19": ("Regional/global warming ratio, RGI 19", "–"),
    "gic_amp_SLOWP": ("Regional/global warming ratio, SLOWG", "–"),
    "gic_amp_FAST": ("Regional/global warming ratio, FASTG", "–"),
    "gic_u_unch": ("Uncharted-ice content of the Frederikse glacier target", "mm SLE"),
    "gic_delta": ("Early-segment (1900–1960) rate bias of the glacier target", "mm yr⁻¹"),
    "gic_u_pre": ("Pre-1901 uncharted-ice set-aside (ledger)", "mm SLE"),
    "gic_s_r5": ("RGI 05 share of the 19th-century glacier datum (ledger)", "mm SLE"),
    "gis_c1": ("Committed-loss sensitivity to regional temperature", "m SLE K⁻¹"),
    "gis_c0": ("Committed loss at zero regional anomaly", "m SLE"),
    "gis_f": ("Surface-mass-balance share of the committed loss", "–"),
    "gis_alpha_f": ("Fast (SMB) channel rate, temperature-dependent part", "yr⁻¹ K⁻¹"),
    "gis_beta_f": ("Fast (SMB) channel rate, constant part", "yr⁻¹"),
    "gis_slow_ell": ("Slow (discharge) channel: log rate at the reference temperature", "ln(yr⁻¹)"),
    "gis_slow_w": ("Slow (discharge) channel: temperature-dependent fraction of the rate", "–"),
    "gis_s_high": ("log₁₀ rate scale of the high basin (NO+NE) relative to the active basin", "log₁₀(–)"),
    "gis_amp": ("Southern-Greenland/global warming ratio", "–"),
    "ais_gmst_amp": ("Antarctic/global warming ratio", "–"),
    "ais_ocean_temperature₀": ("Initial high-latitude ocean subsurface temperature T_oc,0", "°C"),
    "antarctic_alpha": ("Partition of ocean subsurface temperature into ice flux, α_DAIS", "–"),
    "antarctic_nu": ("Runoff-decrease-with-height to precipitation constant ν", "m⁻¹ᐟ² yr⁻¹ᐟ²"),
    "antarctic_temp_threshold": ("Fast-dynamics temperature threshold", "°C (DAIS scale)"),
    "anto_alpha": ("Antarctic ocean temperature sensitivity a_ANTO", "°C °C⁻¹"),
    "anto_beta": ("Antarctic ocean temperature offset b_ANTO", "°C"),
    "antarctic_lambda": ("Fast-dynamics disintegration rate λ", "m yr⁻¹"),
    "antarctic_gamma": ("Power of ice-flow speed on water depth γ", "–"),
    "antarctic_kappa": ("Exponential dependence of precipitation on Antarctic temperature κ_DAIS", "°C⁻¹"),
    "ais_mu": ("Profile parameter µ", "m¹ᐟ²"),
    "ais_bedheight0": ("Bed height at the continent centre b₀", "m"),
    "ais_slope": ("Bed slope", "–"),
    "ais_iceflow0": ("Ice-flow constant f₀", "m yr⁻¹"),
    "ais_precip0_LOG": ("ln of the precipitation constant P₀", "ln(m yr⁻¹)"),
    "ais_precip_u": ("u = ln P₀ + κ_DAIS·T̄ (T̄ = −17.99 °C, DAIS scale); ln P₀ is derived", "ln(m yr⁻¹)"),
    "ais_runoff_Ton": ("Runoff onset temperature T_on = −h₀/c (sampled in place of h₀)", "°C (DAIS scale)"),
    "ais_c": ("Runoff-line slope c", "m °C⁻¹"),
    "thermal_alpha": ("Thermal expansion coefficient α", "kg m⁻³ °C⁻¹"),
    "d2_gsic_1": ("Glacier discrepancy, basis coefficient 1", "cm (RMS)"),
    "d2_gsic_2": ("Glacier discrepancy, basis coefficient 2", "cm (RMS)"),
    "d2_steric_1": ("Thermal-expansion discrepancy, basis coefficient 1", "cm (RMS)"),
    "d2_steric_2": ("Thermal-expansion discrepancy, basis coefficient 2", "cm (RMS)"),
    "sd_ais": ("AR(1) innovation sd, Antarctica", "cm"),
    "rho_ais": ("AR(1) autocorrelation, Antarctica", "–"),
    "sd_gsic": ("AR(1) innovation sd, glaciers", "cm"),
    "rho_gsic": ("AR(1) autocorrelation, glaciers", "–"),
    "sd_gis": ("AR(1) innovation sd, Greenland", "cm"),
    "rho_gis": ("AR(1) autocorrelation, Greenland", "–"),
    "sd_steric": ("AR(1) innovation sd, thermal expansion", "cm"),
    "rho_steric": ("AR(1) autocorrelation, thermal expansion", "–"),
}


def fmt(v, ref):
    """Format v to a precision set by ref (the parameter's scale)."""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "–" if v is None or np.isnan(v) else ("∞" if v > 0 else "−∞")
    s = abs(ref) if ref not in (None, 0) and np.isfinite(ref) else abs(v)
    if s == 0:
        return "0"
    d = max(0, 2 - int(np.floor(np.log10(s))))        # three significant figures on the row's scale
    d = min(d, 6)
    t = f"{v:.{d}f}".rstrip("0").rstrip(".") if d > 0 else f"{v:.0f}"
    return t.replace("-", "−")


def prior_text(r):
    form = r.prior_form
    if form.startswith("flat"):
        return f"flat [{fmt(r.lo, r.lo)}, {fmt(r.hi, r.hi)}]"
    if form.startswith("half-normal"):
        return "half-normal N⁺(0, 5)"
    if form.startswith("N(k10c"):
        return f"N(κ̂(amp), {fmt(r.sigma, r.sigma)}) on [{fmt(r.lo, r.lo)}, {fmt(r.hi, r.hi)}]ᵃ"
    if form.startswith("joint paleo"):
        return f"paleo N({fmt(r.mu, r.mu)}, {fmt(r.sigma, r.sigma)}) on [{fmt(r.lo, r.lo)}, {fmt(r.hi, r.hi)}]ᵇ"
    return f"N({fmt(r.mu, r.mu)}, {fmt(r.sigma, r.sigma)}) on [{fmt(r.lo, r.lo)}, {fmt(r.hi, r.hi)}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="L24")
    a = ap.parse_args()
    pri = pd.read_csv(os.path.join(REPO, f"outputs/ladrillo_priors_{a.tag}.csv"))
    post_path = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{a.tag}.csv")
    post = pd.read_csv(post_path)
    names = list(pri.name)
    # ---- gates ----
    npost = [c for c in post.columns if c != "log_post"]
    assert len(names) == len(npost), f"prior file has {len(names)} parameters, posterior has {len(npost)}"
    assert list(npost) == names, "prior file order != posterior column order"
    missing = [n for n in names if n not in DESC]
    assert not missing, f"no description/units for {missing}"
    blocks = [(h, [n for n in ps if n in names]) for h, ps in BLOCKS]     # tag-aware: L26 drops 3, renames 1
    listed = [n for _, ps in blocks for n in ps]
    assert sorted(listed) == sorted(names), f"BLOCKS does not cover every parameter exactly once: {sorted(set(names)-set(listed))}"
    for r in pri.itertuples():
        v = post[r.name].to_numpy()
        lo, hi = r.lo, r.hi
        if r.name.startswith("rho_"):
            hi = 0.99
        assert (v >= lo - 1e-12).all() and (v <= hi + 1e-12).all(), \
            f"{r.name}: posterior draws outside the prior bounds [{lo}, {hi}] ({v.min()}, {v.max()})"
    # ---- table ----
    q = post[names].quantile([0.05, 0.5, 0.95]).T
    q.columns = ["p05", "p50", "p95"]
    out = pri.set_index("name").join(q)
    out["mean"] = post[names].mean()
    out["description"] = [DESC[n][0] for n in out.index]
    out["units"] = [DESC[n][1] for n in out.index]
    commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    out["provenance"] = (f"ladrillo_prior_posterior_table.py | tag {a.tag} | priors from calibrate_mcmc_ext.jl --dump-priors "
                         f"({pri.provenance.iloc[0].split(' | ')[1]}) | posterior {os.path.basename(post_path)} n={len(post)} | "
                         f"quantiles 5/50/95 over all draws | commit {commit} | {datetime.now():%Y-%m-%d %H:%M}")
    csv_out = os.path.join(REPO, f"outputs/ladrillo_prior_posterior_{a.tag}.csv")
    out.reset_index().to_csv(csv_out, index=False)
    # ---- markdown, grouped by block ----
    lines = [f"**Table A1.** Prior distributions and posterior median (5–95%) of the {len(names)} sampled Ladrillo "
             f"parameters ({len(post):,} thinned draws of the four chains). N(µ, σ) on [lo, hi] is a normal density "
             "restricted to the bounds; 'flat' is bounds only. Glacier-block temperatures are in the block's regional "
             "frame (K relative to 1850–1900). ᵃ κ's prior centre κ̂(amp) is a log-linear function of the block's sampled "
             "amplification (τ₅₀ anchored to GlacierMIP3); ᵇ the seven DAIS geometry parameters carry a joint normal prior "
             "with the correlation of the DAIS paleo ensemble — the marginal is shown. The Greenland channel ordering "
             "(SMB faster than discharge) is a hard constraint on top of these marginals. Antarctic temperatures on the "
             "DAIS scale; ais_runoff_Ton replaces h₀ (h₀ = −T_on·c).", ""]
    lines += ["| Parameter | Description | Units | Prior | Median | 5% | 95% |",
              "|---|---|---|---|---|---|---|"]
    for head, ps in blocks:
        if not ps:
            continue
        lines.append(f"| **{head}** | | | | | | |")
        for n in ps:
            r = out.loc[n]
            code = n.replace("SLOWP", "SLOWG").replace("_FAST", "_FASTG")
            sc = max(abs(r.p05), abs(r.p50), abs(r.p95))     # one precision per row
            lines.append(f"| `{code}` | {r.description} | {r.units} | {prior_text(pri.set_index('name').loc[n])} | "
                         f"{fmt(r.p50, sc)} | {fmt(r.p05, sc)} | {fmt(r.p95, sc)} |")
    md_out = os.path.join(REPO, f"outputs/ladrillo_prior_posterior_{a.tag}.md")
    with open(md_out, "w") as f:
        f.write("\n".join(lines) + "\n\n" + f"<!-- {out.provenance.iloc[0]} -->\n")
    print(f"wrote {os.path.relpath(csv_out, REPO)} and {os.path.relpath(md_out, REPO)} ({len(names)} parameters; all gates PASS)")


if __name__ == "__main__":
    main()
