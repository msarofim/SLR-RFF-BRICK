"""THE SCORECARD RESTATED ON MEDIANS, because band EDGES do not survive and medians do.

WHY. Across 2026-08-22c:
  * diag_gis_scorecard_logo.py -- 2 of 7 GCMs each VOID the admissible set; every
    pass/fail verdict is band-edge driven and none is GCM-robust.
  * diag_gis_residual_band.py -- the cool bands are spuriously precise (2 models
    agreeing to 1.5 cm read as a 1.5 cm uncertainty); a sample-size-respecting interval
    makes them 3-9x WIDER than shipped.
  * diag_gis_k_vs_residual.py -- with n = 2 the cool arms cannot constrain k AT ALL;
    what survives is their PREFERENCE (an rms argmin against MEDIANS), robust 8/8.
  The common thread: everything scored against a band EDGE is unsupported, and
  everything scored against a MEDIAN survives. So state the scorecard that way.

WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT
  It is a RANKING on a scale-free median-distance loss, reported with its own
  leave-one-GCM-out stability. It is NOT a pass/fail admissibility test and it does NOT
  emit an admissible set -- that is the whole point. A "band" here would reintroduce
  exactly the edge dependence being removed.

  LOSS = mean over horizons of |log(ours / PROTECT median)|, per arm, then RMS over
  arms. Scale-free, symmetric in over- and under-prediction, and it never touches p05
  or p95.

WRITES outputs/scope_gis_median_scorecard.csv
  python3 python/scope_gis_median_scorecard.py
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
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
import scope_gis_reservoir_offline as R  # noqa: E402
import scope_gis_reservoir_rate_rank as RR  # noqa: E402

OUT = os.path.join(REPO, "outputs/scope_gis_median_scorecard.csv")

TAG, ARMS, HORIZONS, HIND = A.TAG, A.ARMS, A.HORIZONS, A.HIND
SSP585_ARMS, COOL_ARMS, OURS = A.SSP585_ARMS, A.COOL_ARMS, R.OURS
RES_TAU, RES_ONSET_K, RES_V_M = R.RES_TAU, R.RES_ONSET_K, R.RES_V_M
RAMP_W_GRID, RAMP_W_SHIPPED = RR.RAMP_W_GRID, RR.RAMP_W_SHIPPED
CM_PER_M, V_MAX_M, Y2100_TOL_CM = R.CM_PER_M, R.V_MAX_M, R.Y2100_TOL_CM
K_FIXED = 1.0
RATE_WIN = RR.RATE_WIN
TOP_N = 8                      # cells listed
## THE RATE MUST BE IN THE LOSS. Handoff stage 1b is "score the RATE, not just the
## level", and a level-only median loss re-selects the wide-ramp cell that stage 1a
## rejected for trading the rate away. Same median-distance form, same footing.
RATE_WEIGHT = 1.0              # weight of the rate term relative to ONE horizon
RATE_ARMS_MS = SSP585_ARMS     # cool-arm rates are 1.3-2.5 cm/century: no signal
## The cells the arc has argued over, carried by name so the restatement is comparable
## to everything already written rather than a fresh ranking with no anchors.
NAMED = {(1.0, 4.69, 800.0, 1.0): "A  (shipped offline optimum, psi 0.125)",
         (2.0, 6.5, 50.0, 1.0): "shipped TAP cell (greenland_3basin GIS_TAP_CELL)",
         (0.0, 0.0, 1.0, 1.0): "base, no reservoir"}


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
           for y in tuple(HORIZONS) + tuple(HIND) + (2015,) + RATE_WIN}

    def load(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, amp, S_tab)

    gmst, drivers = {}, {}
    for ssp, lab, fam, stem in ARMS:
        gmst[(ssp, fam)], drivers[(ssp, fam)] = load(
            f"outputs/{stem}.csv", f"gmst_{A.ARM}")
    ours_gmst = {lab: load(f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")[0]
                 for ssp, lab in OURS}
    ours_drv = {lab: load(f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")[1]
                for ssp, lab in OURS}

    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[A.HIND_ARM]
    lo, hi = np.full(nd, 1e-4), np.full(nd, 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(Th, post, K_FIXED, mid)
        b = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s = np.sqrt(lo * hi)
    base_arm = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                for k, v in drivers.items()}
    base_ours = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                 for k, v in ours_drv.items()}
    offs = float(np.median(rebase_cm(basin2_series(Th, post, 1.0, 1.0))[:, idx[2015]]))

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]

    def medians(av):
        """PROTECT MEDIAN only — p05/p95 are never read. Returns levels AND the
        2250-2300 rate median, both as medians."""
        out, rate = {}, {}
        for ssp, lab, fam, _ in ARMS:
            sub = av[(av.ssp == lab) & av.exp.str.contains(fam)
                     & ~av.exp.str.startswith(A.DROP_GCM)]
            if sub.empty:
                continue
            q = sub.groupby("year").gis_cm.median()
            out[(ssp, fam)] = {y: q[y] + offs for y in HORIZONS}
            rate[(ssp, fam)] = (q[RATE_WIN[1]] - q[RATE_WIN[0]]) / \
                (RATE_WIN[1] - RATE_WIN[0]) * 100.0
        return out, rate

    cache = {}
    for on in RES_ONSET_K:
        for tau in RES_TAU:
            for w in RAMP_W_GRID:
                for k, g in list(gmst.items()) + [(("OURS", l), ours_gmst[l])
                                                  for _, l in OURS]:
                    cache[(on, tau, w, k)] = RR.reservoir_unit_w(g, on, tau, w)

    def loss(medrate, add):
        med, mrate = medrate
        per = {}
        for ssp, lab, fam, _ in ARMS:
            if (ssp, fam) not in med:
                continue
            L = base_arm[(ssp, fam)] + add[(ssp, fam)]
            terms = [abs(np.log(max(L[idx[y]], 1e-6) / med[(ssp, fam)][y]))
                     for y in HORIZONS]
            wts = [1.0] * len(HORIZONS)
            if (ssp, fam) in [(a[0], a[2]) for a in RATE_ARMS_MS]:
                rr = (L[idx[RATE_WIN[1]]] - L[idx[RATE_WIN[0]]]) / \
                    (RATE_WIN[1] - RATE_WIN[0]) * 100.0
                terms.append(abs(np.log(max(rr, 1e-6)
                                        / max(mrate[(ssp, fam)], 1e-6))))
                wts.append(RATE_WEIGHT)
            per[(ssp, fam)] = float(np.average(terms, weights=wts))
        agg = lambda ar: float(np.sqrt(np.mean(
            [per[(a[0], a[2])] ** 2 for a in ar if (a[0], a[2]) in per])))
        return per, agg(SSP585_ARMS), agg(COOL_ARMS), agg(ARMS)

    CELLS = [(0.0, 0.0, 1.0, 1.0)] + [(V, on, tau, w) for V in RES_V_M
                                      for on in RES_ONSET_K for tau in RES_TAU
                                      for w in RAMP_W_GRID]

    def rank(med):
        rows = []
        for V, on, tau, w in CELLS:
            if V == 0.0:
                add = {(a[0], a[2]): np.zeros(len(YEARS)) for a in ARMS}
                ao = {l: np.zeros(len(YEARS)) for _, l in OURS}
            else:
                add = {(a[0], a[2]): CM_PER_M * V * cache[(on, tau, w, (a[0], a[2]))]
                       for a in ARMS}
                ao = {l: CM_PER_M * V * cache[(on, tau, w, ("OURS", l))] for _, l in OURS}
            per, r5, rc, ra = loss(med, add)
            rows.append(dict(V_m=V, onset_K=on, tau_yr=tau, ramp_w_K=w,
                             psi=(CM_PER_M * V / tau if tau else 0.0),
                             loss_ssp585=r5, loss_cool=rc, loss_all=ra,
                             within_inventory=bool(V <= V_MAX_M),
                             keeps_2100=bool(all(abs(ao[l][idx[2100]]) < Y2100_TOL_CM
                                                 for _, l in OURS)),
                             ours_ssp585_2300=base_ours["SSP5-8.5"][idx[2300]]
                             + ao["SSP5-8.5"][idx[2300]],
                             name=NAMED.get((V, on, tau, w), "")))
        return pd.DataFrame(rows)

    print(f"scope_gis_median_scorecard — the scorecard on MEDIANS, {TAG}, {nd} draws\n")
    print(f"  LOSS = weighted mean of |log(ours / PROTECT median)| over horizons "
          f"{HORIZONS}\n  PLUS the {RATE_WIN[0]}-{RATE_WIN[1]} RATE (weight "
          f"{RATE_WEIGHT:g}, ssp585 arms only), RMS over arms.\n  p05/p95 are NEVER "
          f"read. A RANKING, not an admissibility test — no band, so no edge.\n"
          f"  The rate term is NOT optional: without it the ranking re-selects the "
          f"wide-ramp cell\n  that stage 1a rejected for trading the rate away.\n")
    full = rank(medians(ann))
    adm = full[full.within_inventory & full.keeps_2100]
    print(f"=== RANKING, best {TOP_N} of {len(adm)} cells within inventory and "
          f"2100-preserving ===\n")
    print(f"  {'V':>5}{'onset':>7}{'tau':>7}{'w':>5}{'psi':>8}{'loss_all':>10}"
          f"{'ssp585':>9}{'cool':>8}{'our 2300':>10}   name")
    for _, r in adm.nsmallest(TOP_N, "loss_all").iterrows():
        print(f"  {r.V_m:5g}{r.onset_K:7g}{r.tau_yr:7g}{r.ramp_w_K:5g}{r.psi:8.3f}"
              f"{r.loss_all:10.4f}{r.loss_ssp585:9.4f}{r.loss_cool:8.4f}"
              f"{r.ours_ssp585_2300:10.1f}   {r['name']}")
    print(f"\n  named reference cells:")
    for _, r in full[full.name != ""].iterrows():
        rk = int((adm.loss_all < r.loss_all).sum()) + 1 if r.within_inventory else -1
        print(f"    {r['name']:44} loss_all {r.loss_all:.4f}  rank "
              f"{rk if rk > 0 else 'n/a (outside inventory)'}")

    # --- leave-one-GCM-out ON THE RANKING ---------------------------------------
    print(f"\n=== IS THE RANKING GCM-ROBUST? (the pass/fail scorecard was NOT) ===\n")
    gcms = sorted(set(ann.gcm))
    best = adm.loss_all.idxmin()
    keys = ["V_m", "onset_K", "tau_yr", "ramp_w_K"]
    b0 = full.loc[best, keys].tolist()
    print(f"  {'dropped GCM':22}{'best cell (V,onset,tau,w)':>30}{'psi':>8}"
          f"{'loss_all':>10}{'same cell?':>12}")
    recs = []
    for g in [None] + gcms:
        av = ann if g is None else ann[ann.gcm != g]
        f2 = rank(medians(av))
        a2 = f2[f2.within_inventory & f2.keeps_2100]
        bb = a2.loc[a2.loss_all.idxmin()]
        same = bb[keys].tolist() == b0
        nm = "(none) FULL" if g is None else g
        recs.append(dict(dropped=nm, V_m=bb.V_m, onset_K=bb.onset_K, tau_yr=bb.tau_yr,
                         ramp_w_K=bb.ramp_w_K, psi=bb.psi, loss_all=bb.loss_all,
                         same_as_full=bool(same)))
        print(f"  {nm:22}{f'{bb.V_m:g},{bb.onset_K:g},{bb.tau_yr:g},{bb.ramp_w_K:g}':>30}"
              f"{bb.psi:8.3f}{bb.loss_all:10.4f}{('YES' if same else 'no'):>12}")
    out = pd.DataFrame(recs)
    out.to_csv(OUT, index=False)
    d = out.iloc[1:]
    print(f"\n  best cell unchanged under {int(d.same_as_full.sum())}/{len(d)} drops; "
          f"psi over the drops {d.psi.min():.3f}-{d.psi.max():.3f} "
          f"(full {out.iloc[0].psi:.3f})")
    print(f"  loss_all of the winner over the drops "
          f"{d.loss_all.min():.4f}-{d.loss_all.max():.4f} "
          f"(full {out.iloc[0].loss_all:.4f})")
    print(f"\n  Compare diag_gis_scorecard_logo.py, where 2 of 7 drops took the "
          f"admissible set to ZERO.\n  A median ranking has no edge to fall off, so "
          f"the question becomes 'does the WINNER move',\n  which is answerable — and "
          f"is the form every downstream statement should now take.")
    print(f"\n  ** THIS EMITS NO ADMISSIBLE SET, DELIBERATELY. ** Re-adding a pass/fail "
          f"band would\n  reintroduce exactly the edge dependence this removes. Quote "
          f"a RANK and its stability.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
