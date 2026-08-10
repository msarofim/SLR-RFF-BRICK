#!/usr/bin/env python3
"""
scope_greenland_options.py — why BRICK's Greenland module under-responds to
scenario, and which structural change would fix it.

BRICK-F* leaves Greenland at stock SIMPLE (Bakker et al. 2016):

    V_eq(T)  = a·T + b                            equilibrium volume, m SLE
    1/tau(t) = (alpha·T + beta) · V(t)/V0         relaxation rate, 1/yr
    V(t)     = V(t-1) + (V_eq(t-1) - V(t-1))/tau(t-1)
    SLE(t)   = V0 - V(t)

driven by GLOBAL mean temperature. At 2100 it gives 6.6 / 7.3 / 8.8 cm under
SSP1-2.6 / SSP2-4.5 / SSP5-8.5 — a scenario spread of +2.2 cm where MAGICC-SLR
and every FACTS module give +6.3 to +7.3 cm.

This script reimplements SIMPLE (validated against the Julia projections), then
runs one-at-a-time counterfactuals to attribute the shortfall and price each
candidate fix. It changes nothing in the model; it is a scoping diagnostic.

Counterfactuals
  regional driver   drive SIMPLE with Greenland-region temperature (amp x GMST)
                    instead of GMST — the fix that worked for the glaciers
  faster response   scale (alpha, beta) so the ice sheet relaxes faster
  steeper V_eq      scale a, i.e. more committed loss per degree
  no V/V0 damping   drop the term that SLOWS the response as ice is lost
  two channel       add a fast surface-mass-balance channel responding within
                    a decade, alongside the slow dynamic relaxation

  python3 python/scope_greenland_options.py
Writes outputs/scope_greenland_options.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTERIOR = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/scope_greenland_options.csv")

Y0, Y1 = 1850, 2300
REF = (1995, 2014)
SSPS = ["ssp126", "ssp245", "ssp585"]
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
NDRAW = 2000
# Julia projections to validate against (outputs/ssps_components_2300_extC.csv, gis @2100)
JULIA_GIS_2100 = {"ssp126": 6.633, "ssp245": 7.266, "ssp585": 8.797}
# What the model is being asked to match at 2100 (cm, medians):
#   MAGICC-SLR (Nauels 2025)     6.4 / 9.3 / 13.5
#   FACTS FittedISMIP            7.7 / 10.2 / 14.0
TARGET_SPREAD = {"MAGICC-SLR": 7.1, "FACTS FittedISMIP": 6.3}

YEARS = np.arange(Y0, Y1 + 1)
IREF = (YEARS >= REF[0]) & (YEARS <= REF[1])
I2100 = int(np.where(YEARS == 2100)[0][0])


def load_gmst(ssp):
    d = pd.read_csv(os.path.join(OBS, f"fair_mean_gmst_{ssp}.csv")).set_index("year")["gmst_C"]
    return d.reindex(YEARS).to_numpy()


def greenland_amplification():
    """Through-origin fit of Greenland-region temperature on global HadCRUT5,
    both relative to 1850-1900 — the same convention used for the glacier
    reservoirs. Region 05 of t_glac_regions_hadcrut5.csv is Greenland."""
    reg = pd.read_csv(os.path.join(OBS, "t_glac_regions_hadcrut5.csv")).set_index("year")["r05"]
    glob = pd.read_csv(os.path.join(OBS, "t_glac_hadcrut5.csv")).set_index("year")["gmst_hadcrut5_C"]
    base = lambda s: s - s.loc[1850:1900].mean()
    reg, glob = base(reg), base(glob)
    lo, hi = 1901, 2024
    x, y = glob.loc[lo:hi].to_numpy(), reg.loc[lo:hi].to_numpy()
    ok = np.isfinite(x) & np.isfinite(y)
    return float((x[ok] * y[ok]).sum() / (x[ok] ** 2).sum())


def simple(T, a, b, alpha, beta, v0, damping=True, fast_frac=0.0, fast_tau=10.0):
    """SIMPLE, vectorised over draws. `T` is (nyear,), parameters are (ndraw,).

    fast_frac splits the equilibrium response into a fast surface-mass-balance
    channel (fraction of a, relaxing on fast_tau years) and the remaining slow
    dynamic channel, which is the stock behaviour when fast_frac = 0.
    """
    n = len(T)
    V = np.repeat(v0[None, :], 1, axis=0)[0].copy()
    Vf = np.zeros_like(V)                       # fast-channel loss, m SLE
    out = np.empty((n, len(v0)))
    slow_a = a * (1 - fast_frac)
    fast_a = a * fast_frac
    for i in range(n):
        if i == 0:
            out[i] = v0 - V
            continue
        v_eq = slow_a * T[i - 1] + b
        rate = alpha * T[i - 1] + beta
        if damping:
            rate = rate * (V / v0)
        V = V + rate * (v_eq - V)
        if fast_frac > 0:
            # fast channel relaxes toward its own equilibrium loss, -fast_a*T
            Vf = Vf + ((-fast_a * T[i - 1]) - Vf) / fast_tau
        out[i] = v0 - V + Vf
    return out


def rebase(series):
    return 100 * (series - series[IREF].mean(axis=0))


def main():
    post = pd.read_csv(POSTERIOR)
    step = max(1, len(post) // NDRAW)
    post = post.iloc[::step][:NDRAW]
    a = post.greenland_a.to_numpy()
    b = post.greenland_b.to_numpy()
    alpha = post.greenland_alpha.to_numpy()
    beta = post.greenland_beta.to_numpy()
    v0 = post.greenland_v0.to_numpy()
    amp = greenland_amplification()
    gmst = {s: load_gmst(s) for s in SSPS}

    print(f"Greenland scoping | {len(post)} posterior draws | "
          f"Greenland/global amplification {amp:.2f}\n")

    variants = {
        "stock SIMPLE": dict(),
        "regional driver": dict(scale_T=amp),
        "faster response x3": dict(scale_rate=3.0),
        "faster response x10": dict(scale_rate=10.0),
        "steeper V_eq x2": dict(scale_a=2.0),
        "no V/V0 damping": dict(damping=False),
        "two channel (30% SMB, tau 10 yr)": dict(fast_frac=0.30, fast_tau=10.0),
        "regional + two channel": dict(scale_T=amp, fast_frac=0.30, fast_tau=10.0),
    }

    rows = []
    print(f"  {'variant':34s} " + "".join(f"{LABEL[s]:>11s}" for s in SSPS) + "     spread")
    for name, kw in variants.items():
        meds = {}
        for s in SSPS:
            T = gmst[s] * kw.get("scale_T", 1.0)
            sle = simple(T, a * kw.get("scale_a", 1.0), b,
                         alpha * kw.get("scale_rate", 1.0),
                         beta * kw.get("scale_rate", 1.0), v0,
                         damping=kw.get("damping", True),
                         fast_frac=kw.get("fast_frac", 0.0),
                         fast_tau=kw.get("fast_tau", 10.0))
            meds[s] = float(np.median(rebase(sle)[I2100]))
        spread = meds["ssp585"] - meds["ssp126"]
        print(f"  {name:34s} " + "".join(f"{meds[s]:11.1f}" for s in SSPS) + f"{spread:11.1f}")
        rows.append(dict(variant=name, year=2100, **{LABEL[s]: meds[s] for s in SSPS},
                         spread_126_585=spread))

    stock = rows[0]
    err = max(abs(stock[LABEL[s]] - JULIA_GIS_2100[s]) for s in SSPS)
    print(f"\n  [validation] stock SIMPLE vs the Julia projections: max|diff| "
          f"{err:.3f} cm  {'PASS' if err < 0.15 else 'FAIL'}")
    print(f"  [target]     scenario spread to match: " +
          ", ".join(f"{k} {v:+.1f} cm" for k, v in TARGET_SPREAD.items()))

    # --- why: how much of the equilibrium gap is realised by 2100 ------------
    print("\nWHY THE SPREAD IS SMALL")
    for s in SSPS:
        T2100 = gmst[s][I2100]
        gap = np.median(v0 - (a * T2100 + b)) * 100          # cm still committed
        tau = np.median(1.0 / (alpha * T2100 + beta))
        realised = stock[LABEL[s]] - stock[LABEL["ssp126"]] if s != "ssp126" else 0.0
        print(f"  {LABEL[s]}: GMST@2100 {T2100:+.2f} C | committed loss {gap:5.1f} cm "
              f"| e-folding time {tau:5.0f} yr | fraction of gap realised by 2100 "
              f"{100 * stock[LABEL[s]] / gap:4.1f}%")
    dcom = np.median(a) * (gmst["ssp126"][I2100] - gmst["ssp585"][I2100]) * 100
    print(f"\n  The committed-loss DIFFERENCE between SSP1-2.6 and SSP5-8.5 is "
          f"{dcom:.0f} cm,\n  which is ample. Only ~{100 * stock['SSP5-8.5'] / (np.median(v0 - (a * gmst['ssp585'][I2100] + b)) * 100):.0f}% "
          f"of it is realised by 2100, because the relaxation\n  time is millennial. "
          f"The bottleneck is the TRANSIENT, not the equilibrium.")

    # --- does the frame fix also address the 1942-1982 hindcast miss? --------
    # Fair comparison without refitting: compare the SHAPE of the modelled melt
    # rate against the observed one. Levels are not comparable, because the
    # parameters were calibrated for a global driver.
    print("\nHINDCAST SHAPE (1900-2018), model melt rate vs the Frederikse GIS target")
    tgt = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets_ext.csv")).set_index("year")
    reg = pd.read_csv(os.path.join(OBS, "t_glac_regions_hadcrut5.csv")).set_index("year")["r05"]
    reg = reg - reg.loc[1850:1900].mean()
    hist = pd.read_csv(os.path.join(OBS, "fair_mean_gmst_ssp245harm.csv")
                       ).set_index("year")["gmst_C"].reindex(YEARS).to_numpy()
    hist = hist - np.nanmean(hist[(YEARS >= 1850) & (YEARS <= 1900)])
    # observed Greenland driver through its last year, then amp x GMST
    reg_full = reg.reindex(YEARS).to_numpy()
    last = int(reg.dropna().index.max())
    anchor = (YEARS >= last - 10) & (YEARS <= last)
    off = np.nanmean(reg_full[anchor]) - amp * np.nanmean(hist[anchor])
    reg_full = np.where(YEARS <= last, reg_full, amp * hist + off)

    obs_rate = tgt["gis"].dropna().diff().rolling(11, center=True).mean()
    win = np.arange(1900, 2019)
    med = lambda x: np.median(x, axis=1)
    shape_rows = []
    for name, T in (("global (stock)", hist), ("Greenland regional", reg_full)):
        sle = med(simple(T, a, b, alpha, beta, v0))
        rate = pd.Series(np.gradient(sle), index=YEARS).rolling(11, center=True).mean()
        both = pd.concat([rate.reindex(win), obs_rate.reindex(win)], axis=1).dropna()
        r = float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1])
        # re-reference both cumulative series to 1995-2005, the calibration window
        ref = (YEARS >= 1995) & (YEARS <= 2005)
        mod = pd.Series(100 * (sle - sle[ref].mean()), index=YEARS)
        o = tgt["gis"]
        o = o - o.loc[1995:2005].mean()
        bias = float((mod.reindex(np.arange(1942, 1983)) -
                      o.reindex(np.arange(1942, 1983))).mean())
        print(f"  {name:20s} rate correlation r = {r:+.2f}   "
              f"mean 1942-1982 bias = {bias:+.2f} cm")
        shape_rows.append(dict(variant=f"hindcast: {name}", year=1942,
                               rate_corr=r, bias_1942_1982_cm=bias))

    pd.DataFrame(rows + shape_rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
