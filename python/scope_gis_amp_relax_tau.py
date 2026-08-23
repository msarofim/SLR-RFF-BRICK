"""DOES RELAXING THE AMP LAW'S LEVEL OFFSET BUY ANYTHING AT BOTH HORIZONS AT ONCE?

THE KNOB. The shipped amplification law is EXACTLY "the CMIP6 shape times a constant
level offset":

    applied_amp(dT) = obs_amp_full * S(dT)
                    = obs_amp_full * R(dT)/r_anchor
                    = R(dT) * (obs_amp_full / r_anchor)
                    = R(dT) * 1.2864

so the observed-minus-CMIP6 disagreement enters as ONE number, 1.2864x, and is carried
forward MULTIPLICATIVELY FOREVER. This scan asks what happens if it is instead treated
as a present-day anomaly that RELAXES toward the models' own level:

    f(t) = [1 + (LEVEL_OFFSET - 1) * exp(-(t - t_last)/tau)] / LEVEL_OFFSET
    applied_amp(dT, t) = obs_amp_full * S(dT) * f(t)

  tau -> inf   f == 1            the SHIPPED law, exactly
  tau -> 0     f == 1/1.2864     the 40-model pooled CMIP6 level, immediately

f(t_last) = 1 identically, so the anchor-preserving splice offset is untouched and the
hindcast is bit-identical at every tau (the law is post-splice by construction).

MARCUS'S PRIOR, RECORDED BEFORE THE RUN (2026-08-23): "it seems like it won't be
helpful." The two endpoints were already measured and they bracket every tau --
diag_gis_amp_likeforlike_2100.csv has 2100 going 1.39x -> 0.89x while 2300 goes
0.78x -> 0.39x -- so unless the two horizons respond on DIFFERENT timescales there is
no interior optimum, only a trade. The scan exists to price the trade and to say
whether the response is monotone, not because an optimum is expected.

⚠ tau -> 0 here is the 40-MODEL POOLED secant level, NOT the per-GCM like-for-like
driver. They answer different questions and do not have to agree.

WRITES outputs/scope_gis_amp_relax_tau.csv
  python3 python/scope_gis_amp_relax_tau.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
import scope_gis_2300_relaxation as R2  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
import diag_gis_gcm_tdecomp as TD  # noqa: E402
import scope_gis_reservoir_offline as RO  # noqa: E402
import gis_targets  # noqa: E402

OUT = os.path.join(REPO, "outputs/scope_gis_amp_relax_tau.csv")

TAG, ARMS = A.TAG, A.ARMS
ARMS_R2300 = [a for a in ARMS if a[2] == "r2300"]
SSP_OF = TD.SSP_OF
HORIZONS_TEST = (2100, 2300)
K_FIXED = 1.0
OBS_AMP_FULL, R_ANCHOR = 1.9221976385152952, 1.4942493826789536
LEVEL_OFFSET = OBS_AMP_FULL / R_ANCHOR

## The ladder. inf is the shipped law and 0.0 is immediate collapse to the pooled
## CMIP6 level; the interior is log-spaced over the range a "present-day anomaly"
## could plausibly persist.
TAUS = [np.inf, 400.0, 200.0, 100.0, 50.0, 25.0, 0.0]

## BOTH ARMS ARE SCORED, and the tapped one is the one that matters.
## The untapped base model's 2300 error on this arm is DOMINATED by its commitment
## deficit -- the defect the tap exists to remove. Pricing an amp knob against the
## base model's 2300 would charge the amp law for an error the shipped model does not
## have. The tap is added as the offline reservoir the wired component was priced on
## (V * unit, cm), read from the Julia constant so the arm cannot drift from the cell.
CELL = gis_targets.tap_cell()
CM_PER_M = 100.0


def relax_factor(tau):
    """f(t) on the YEARS axis. 1 at and before the last observed year, decaying to
    1/LEVEL_OFFSET after it."""
    tgz = pd.read_csv(os.path.join(R2.OBS, "t_gis_zones.csv"))
    last = int(tgz["year"].max())
    dt = np.maximum(YEARS - last, 0).astype(float)
    if np.isinf(tau):
        decay = np.ones_like(dt)
    elif tau == 0.0:
        decay = np.where(dt > 0, 0.0, 1.0)
    else:
        decay = np.exp(-dt / tau)
    return (1.0 + (LEVEL_OFFSET - 1.0) * decay) / LEVEL_OFFSET


def regional_driver_tau(gmst_rb, amp, S, tau):
    """`regional_driver` with the level offset relaxed by f(t).

    MIRRORS scope_gis_2300_relaxation.regional_driver TERM FOR TERM -- the only change
    is `amp` becoming `amp * f(t)` inside the splice, and `f(t_last)` (== 1) in the
    anchor term so the seam is untouched. GATED at tau = inf against the real function;
    see main()."""
    tgz = pd.read_csv(os.path.join(R2.OBS, "t_gis_zones.csv"))
    gd = dict(zip(tgz["year"].astype(int), tgz[R2.GIS_ZONE].astype(float)))
    last = int(tgz["year"].max())
    obs = np.array([gd.get(int(y), 0.0) for y in YEARS])
    mask = YEARS <= last
    ianch = np.isin(YEARS, np.arange(last - R2.ANCHOR_N + 1, last + 1))
    anchor = obs[ianch].mean()
    shape = S(R2._running_mean(gmst_rb, R2.SHAPE_WIN))
    shape_anchor = float((shape[ianch] * gmst_rb[ianch]).mean())
    f = relax_factor(tau)
    amp = np.atleast_1d(np.asarray(amp, float))[:, None]
    spliced = (amp * f[None, :] * shape[None, :] * gmst_rb[None, :]
               + (anchor - amp * shape_anchor))     # f == 1 on the anchor window
    return np.where(mask[None, :], obs[None, :], spliced)


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    amp = post["gis_amp"].to_numpy()
    S_tab = gis_shape_table()
    nd = len(post)
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in HORIZONS_TEST + tuple(A.HIND) + (2015,)}

    g = pd.read_csv(f"outputs/{ARMS[0][3]}.csv").set_index(
        "year")[f"gmst_{A.ARM}"].reindex(YEARS).to_numpy()
    gmst_rb = g - g[ibd].mean()

    ## [GATE] tau = inf must reproduce the shipped driver EXACTLY, or this scan is
    ## measuring a re-derivation rather than a knob.
    d_ship = regional_driver(gmst_rb, amp, S_tab)
    d_inf = regional_driver_tau(gmst_rb, amp, S_tab, np.inf)
    dev = float(np.max(np.abs(d_ship - d_inf)))
    print(f"[GATE] tau=inf reproduces regional_driver: max|diff| = {dev:.3e} K", end="")
    assert dev < 1e-12, f"  FAIL — the variant has drifted from the kernel"
    print("   PASS")
    ## [GATE] the hindcast must be untouched at EVERY tau.
    worst = max(float(np.max(np.abs(
        regional_driver_tau(gmst_rb, amp, S_tab, t)[:, YEARS <= 2024] -
        d_ship[:, YEARS <= 2024]))) for t in TAUS)
    print(f"[GATE] hindcast (<=2024) unmoved at every tau: max|diff| = {worst:.3e} K",
          end="")
    assert worst == 0.0, "  FAIL — the relaxation is leaking into the calibration window"
    print("   PASS\n")

    hind_drv = regional_driver(gmst_rb, amp, S_tab)
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[A.HIND[1]] - tgt.loc[A.HIND[0]])
    lo, hi = np.full(nd, 1e-4), np.full(nd, 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(hind_drv, post, K_FIXED, mid)
        b = 100.0 * (L[:, idx[A.HIND[1]]] - L[:, idx[A.HIND[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s = np.sqrt(lo * hi)
    offs = float(np.median(rebase_cm(
        basin2_series(hind_drv, post, 1.0, 1.0))[:, idx[2015]]))

    def curve(drv):
        c = np.median(rebase_cm(basin2_series(drv, post, K_FIXED, s)), axis=0)
        return {y: c[idx[y]] - offs for y in HORIZONS_TEST}

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]

    print(f"scope_gis_amp_relax_tau — {TAG}, {nd} draws, "
          f"LEVEL_OFFSET {LEVEL_OFFSET:.4f}x\n")
    rows = []
    for ssp, lab, fam, _ in ARMS_R2300:
        sub = A.protect_band(ann, lab, fam)
        for gcm in sorted(sub.gcm.unique()):
            ser = TD.gcm_series(TD.GCM_ALIAS.get(gcm, gcm), SSP_OF[lab])
            gr = sub[sub.gcm == gcm]
            ism = {y: float(gr[gr.year == y].gis_cm.median()) for y in HORIZONS_TEST}
            ## The reservoir is driven by GMT and is INDEPENDENT of the amp law
            ## (the onset is global, not regional) -- so it is the same additive
            ## series at every tau, which is exactly why it can be added here.
            res = CM_PER_M * CELL["V_m"] * RO.reservoir_unit_n(
                ser["gmst"], CELL["onset_K"], CELL["tau_yr"], int(CELL["stages"]))
            for tau in TAUS:
                c = curve(regional_driver_tau(ser["gmst"], amp, S_tab, tau))
                rows.append(dict(arm=f"{lab} {fam}", gcm=gcm, tau_yr=tau,
                                 amp_2100=float(OBS_AMP_FULL * relax_factor(tau)[
                                     idx[2100]] * 0.8596),
                                 **{f"ism_{y}": ism[y] for y in HORIZONS_TEST},
                                 **{f"ours_{y}": c[y] for y in HORIZONS_TEST},
                                 **{f"tapped_{y}": c[y] + res[idx[y]] - res[idx[2015]]
                                    for y in HORIZONS_TEST}))
    out = pd.DataFrame(rows)
    for y in HORIZONS_TEST:
        out[f"r_{y}"] = out[f"ours_{y}"] / out[f"ism_{y}"]
        out[f"rt_{y}"] = out[f"tapped_{y}"] / out[f"ism_{y}"]
    out.to_csv(OUT, index=False)

    summ = {}
    for pre, nm in (("r", "UNTAPPED base model"),
                    ("rt", f"TAPPED — the SHIPPED model ({gis_targets.tap_cell_label()})")):
        print(f"=== {nm} ===")
        print(f"  {'tau (yr)':>10}{'amp@2100':>10}"
              f"{'2100 med':>11}{'2100 |log|':>12}{'2300 med':>11}{'2300 |log|':>12}"
              f"{'joint |log|':>13}")
        summ[pre] = []
        for tau in TAUS:
            sub = out[out.tau_yr == tau]
            e = {y: float(np.mean(np.abs(np.log(sub[f"{pre}_{y}"]))))
                 for y in HORIZONS_TEST}
            j = 0.5 * (e[2100] + e[2300])
            summ[pre].append((tau, j, e[2100], e[2300]))
            print(f"  {('inf' if np.isinf(tau) else f'{tau:.0f}'):>10}"
                  f"{sub.amp_2100.iloc[0]:10.3f}"
                  f"{sub[f'{pre}_2100'].median():11.2f}{e[2100]:12.3f}"
                  f"{sub[f'{pre}_2300'].median():11.2f}{e[2300]:12.3f}{j:13.3f}")
        print()

    for pre, nm in (("r", "untapped"), ("rt", "TAPPED/shipped")):
        b = min(summ[pre], key=lambda t: t[1])
        sh = [j for t, j, _, _ in summ[pre] if np.isinf(t)][0]
        print(f"  {nm:16} shipped-law joint {sh:.3f}  ->  best tau="
              f"{'inf' if np.isinf(b[0]) else f'{b[0]:.0f}'} joint {b[1]:.3f}"
              f"   ({sh / b[1]:.3f}x better)")
    ## WEIGHT SENSITIVITY. Equal weighting is a choice, and it is NOT Marcus's
    ## stated one (2100 > 2300 > 3001). Report the verdict under each rather than
    ## letting one weighting decide -- the ranking is what transfers, not the number.
    print("  WEIGHT SENSITIVITY on the TAPPED/shipped arm — w(2100):w(2300)\n")
    print(f"  {'weights':>12}{'best tau':>10}{'joint@best':>12}"
          f"{'joint@shipped-law':>19}{'gain':>8}")
    for w21, w23 in ((2, 1), (1, 1), (1, 2)):
        sc = [(t, (w21 * e21 + w23 * e23) / (w21 + w23))
              for t, _, e21, e23 in summ["rt"]]
        b = min(sc, key=lambda x: x[1])
        sh = [v for t, v in sc if np.isinf(t)][0]
        print(f"  {f'{w21}:{w23}':>12}"
              f"{('inf' if np.isinf(b[0]) else f'{b[0]:.0f}'):>10}"
              f"{b[1]:12.3f}{sh:19.3f}{sh / b[1]:8.2f}x")
    print()
    summ_ = summ["r"]
    best = min(summ_, key=lambda t: t[1])[:2]
    ship = [j for t, j, _, _ in summ_ if np.isinf(t)][0]
    print(f"\n  |log| mean is scale-free: 0 is perfect, and a factor 2 high and a "
          f"factor 2 low\n  score alike. 'joint' weights the two horizons EQUALLY, "
          f"which is a CHOICE.\n")
    print(f"  shipped (tau=inf) joint {ship:.3f}   best on the ladder "
          f"tau={'inf' if np.isinf(best[0]) else f'{best[0]:.0f}'} joint {best[1]:.3f}"
          f"   ({ship / best[1]:.3f}x)")
    e21 = [(t, float(np.mean(np.abs(np.log(out[out.tau_yr == t].r_2100)))))
           for t in TAUS]
    e23 = [(t, float(np.mean(np.abs(np.log(out[out.tau_yr == t].r_2300)))))
           for t in TAUS]
    mono21 = all(a[1] >= b[1] for a, b in zip(e21, e21[1:]))
    mono23 = all(a[1] <= b[1] for a, b in zip(e23, e23[1:]))
    print(f"  2100 error falls monotonically as tau shortens: {mono21}")
    print(f"  2300 error rises monotonically as tau shortens: {mono23}")
    print(f"    => {'a pure TRADE with no interior optimum' if mono21 and mono23 else 'NOT a pure trade — look at the table'}")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
