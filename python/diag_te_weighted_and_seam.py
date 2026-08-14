#!/usr/bin/env python3
"""
diag_te_weighted_and_seam.py — two checks that decide what (if anything) to do
about thermal expansion, prompted by Marcus's objection (2026-08-14) to splicing
an observed-OHC hindcast onto a FaIR-OHC projection.

THE OBJECTION, and it is right. The glacier/Greenland splices are a GLOBAL→LOCAL
temperature mapping: the global driver (GMST) is the same object either side of
the seam, and only the spatial pattern is spliced — observed historically,
CMIP6-calibrated forward. An OHC splice is different in kind. OHC *is* the global
driver, so the hindcast and the projection would be driven by DIFFERENT global
quantities, with the seam papering over a FaIR-vs-observations discrepancy we
cannot explain. Worse, `thermal_alpha` would be calibrated against one heat
series and then applied to another.

CHECK 1 — is the FaIR-vs-obs OHC difference SCALE or SHAPE?
If it is a constant factor, it is EXACTLY DEGENERATE with `thermal_alpha`
(te_sea_level = te_α·S(t), so rescaling S rescales the fitted α and nothing else
moves). In that case there is no problem to fix and no seam to introduce. Only a
SHAPE difference can bias anything.

CHECK 2 — was "TE is the one module worse than BRICK 2.0" the right reading?
Both arms are driven by the SAME FaIR OHC (posterior_predictive_oldbrick.jl uses
fair_mean_ohc.csv), so the driver cannot explain the difference between them —
only `thermal_alpha` can. And the scorecard's RMSE is UNWEIGHTED, which treats a
1920s steric observation as being as informative as a 2010s one. The calibrator
does not: it weights by the per-year band σ, `ϵband = max((hi-lo)/(2·1.645),
0.05)`. So the fair comparison is the precision-weighted one, and the α that
zeroes the UNWEIGHTED bias is not what the likelihood is trying to find.

  source ~/climate-env/bin/activate
  python3 python/diag_te_weighted_and_seam.py
Writes outputs/diag_te_weighted_and_seam.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/diag_te_weighted_and_seam.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

TE_A, TE_C, TE_RHO, TE_S0 = 3.619e14, 3991.86795711963, 1027.0, 0.0
FIT_REF = (1995, 2005)
EPS_FLOOR = 0.05                    # ϵband floor, cm (calibrate_mcmc_ext.jl L253)
EPS_Z = 2 * 1.645                   # ϵband divisor — the target bands are 90%
YEARS = np.arange(1850, 2026)
FIT0 = 1900                         # calibrator's first fit year

ALPHA = {"Ladrillo L10": 0.15023, "BRICK 2.0": 0.15834}
ALPHA_SD = {"Ladrillo L10": 0.00747, "BRICK 2.0": 0.02892}
FAIR_OHC = "fair_mean_ohc_ssp245harm.csv"
OBS_OHC = [("Zanna+Cheng", "ohc_spliced_zanna_cheng.csv"),
           ("Zanna+IGCC", "ohc_spliced_zanna_igcc.csv")]
SEAM = 2025                         # last observed year — where a splice would sit


def ohc(fname):
    d = pd.read_csv(os.path.join(OBS, fname), comment="#")
    s = d.set_index(d.columns[0])["ohc_1e22J"].astype(float)
    s.index = s.index.astype(int)
    return s.reindex(YEARS).dropna()


def shape(o):
    yrs, q = o.index.to_numpy(), o.to_numpy(float)
    dq = np.diff(q, prepend=q[0]) * 1e22
    s = 100.0 * (TE_S0 + np.cumsum(dq) / (TE_A * TE_C * TE_RHO ** 2))
    ib = (yrs >= FIT_REF[0]) & (yrs <= FIT_REF[1])
    return pd.Series(s - s[ib].mean(), index=yrs)


def main():
    tg = pd.read_csv(TARGETS).set_index("year")
    obs = tg["steric"].reindex(YEARS)
    eps = np.maximum((tg["steric_hi"] - tg["steric_lo"]).reindex(YEARS) / EPS_Z,
                     EPS_FLOOR)
    S_fair = shape(ohc(FAIR_OHC))
    rows = []

    # ---- CHECK 1: scale or shape? ------------------------------------------
    print("CHECK 1 — is FaIR-vs-observed OHC a SCALE difference or a SHAPE one?")
    print("  A pure scale factor is EXACTLY degenerate with thermal_alpha, so it")
    print("  biases nothing and needs no seam. Only shape can.\n")
    print(f"  {'product':14s} {'best scale k':>13s} {'R^2 of k*S_fair':>17s} "
          f"{'resid RMSE cm':>14s} {'as % of obs range':>18s}")
    for name, f in OBS_OHC:
        S_obs = shape(ohc(f))
        yrs = S_obs.index.intersection(S_fair.index)
        yrs = yrs[yrs >= FIT0]
        a, b = S_fair.reindex(yrs).to_numpy(), S_obs.reindex(yrs).to_numpy()
        k = float(a @ b / (a @ a))                    # best pure-scale match
        resid = b - k * a
        r2 = 1.0 - float(resid @ resid) / float(((b - b.mean()) ** 2).sum())
        rng = float(b.max() - b.min())
        print(f"  {name:14s} {k:13.4f} {r2:17.4f} {np.sqrt((resid ** 2).mean()):14.4f} "
              f"{100 * np.sqrt((resid ** 2).mean()) / rng:17.1f}%")
        rows.append(dict(check="scale_vs_shape", arm=name, scale_k=k, r2=r2,
                         resid_rmse_cm=float(np.sqrt((resid ** 2).mean()))))
    print("\n  R^2 near 1 with a small residual = mostly SCALE (absorbed by alpha).")
    print("  A large residual = SHAPE, which alpha cannot absorb.\n")

    # ---- CHECK 2: weighted vs unweighted, both arms on the SAME driver ------
    print("CHECK 2 — Ladrillo vs BRICK 2.0 on steric, SAME FaIR OHC driver.")
    print("  Only thermal_alpha differs. chi2/n uses the calibrator's own per-year")
    print("  band sigma; RMSE is the scorecard's unweighted metric.\n")
    m = (YEARS >= FIT0) & obs.notna().to_numpy() & S_fair.reindex(YEARS).notna().to_numpy()
    s, o, e = (S_fair.reindex(YEARS)[m].to_numpy(), obs[m].to_numpy(),
               eps[m].to_numpy())
    # what each objective actually wants
    a_unw = float(o.mean() / s.mean())
    a_ls = float(s @ o / (s @ s))
    a_w = float((s * o / e ** 2).sum() / (s * s / e ** 2).sum())
    print(f"  alpha wanted by: zero-mean-bias {a_unw:.5f} | unweighted LS {a_ls:.5f} "
          f"| PRECISION-WEIGHTED {a_w:.5f}")
    print(f"  {'arm':14s} {'alpha':>8s} {'(alpha-a_w)/sd':>15s} {'chi2/n':>9s} "
          f"{'RMSE cm':>9s}")
    for arm, a in ALPHA.items():
        r = a * s - o
        chi2n = float(((r / e) ** 2).mean())
        rmse = float(np.sqrt((r ** 2).mean()))
        print(f"  {arm:14s} {a:8.5f} {(a - a_w) / ALPHA_SD[arm]:15.2f} "
              f"{chi2n:9.3f} {rmse:9.3f}")
        rows.append(dict(check="weighted", arm=arm, alpha=a, chi2_per_n=chi2n,
                         rmse_cm=rmse, alpha_sd=ALPHA_SD[arm]))
    best = a_w * s - o
    print(f"  {'best possible':14s} {a_w:8.5f} {0.0:15.2f} "
          f"{float(((best / e) ** 2).mean()):9.3f} "
          f"{float(np.sqrt((best ** 2).mean())):9.3f}")

    print("\n  The precision-weighted alpha is what the likelihood is trying to find.")
    print("  Read the chi2/n column, not RMSE, when asking whether TE is a regression.\n")

    # ---- what a seam would actually cost -----------------------------------
    print("CHECK 3 — what an obs-OHC/FaIR-OHC seam would cost, if built anyway.")
    print(f"  Calibrate alpha on observed OHC, then project on FaIR OHC from {SEAM}.")
    print(f"  {'product':14s} {'alpha on obs':>13s} {'implied jump':>14s}")
    for name, f in OBS_OHC:
        S_obs = shape(ohc(f))
        yrs = S_obs.index[(S_obs.index >= FIT0)]
        ob = obs.reindex(yrs).to_numpy()
        ep = eps.reindex(yrs).to_numpy()
        so = S_obs.reindex(yrs).to_numpy()
        ok = np.isfinite(ob)
        a_obs = float((so[ok] * ob[ok] / ep[ok] ** 2).sum() /
                      (so[ok] * so[ok] / ep[ok] ** 2).sum())
        # the two rates at the seam, per year, under each arm's own alpha
        y2 = min(SEAM, int(S_obs.index.max()), int(S_fair.index.max()))
        rate_obs = a_obs * float(S_obs.loc[y2] - S_obs.loc[y2 - 10]) / 10
        rate_fair = a_obs * float(S_fair.loc[y2] - S_fair.loc[y2 - 10]) / 10
        print(f"  {name:14s} {a_obs:13.5f} {rate_fair - rate_obs:+13.4f} cm/yr")
        rows.append(dict(check="seam", arm=name, alpha=a_obs,
                         seam_rate_jump_cm_yr=rate_fair - rate_obs))
    print("  (the rate discontinuity the projection would inherit at the seam,")
    print("   holding the obs-calibrated alpha fixed across it)")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
