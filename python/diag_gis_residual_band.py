"""THE RESIDUAL BAND, BUILT END-TO-END, AND THE LEAVE-ONE-GCM-OUT RE-RUN AGAINST IT.

THE ARGUMENT SO FAR
  diag_gis_scorecard_logo.py: two single GCMs each void the entire admissible set --
  CESM2 through the ssp245 matched band, MPI-ESM1-2-HR through ssp585.
  diag_gis_gcm_tdecomp.py: on the one arm that can be fitted, our OWN drive route
  explains R2 = 0.95 of the across-GCM variance, and only 23 % of the band's width
  survives regressing it out. On the two arms too small to fit, the single pairwise
  contrast still puts 0.49x / 0.78x of the gap on local temperature.
  ==> most of what the raw band calls uncertainty is local temperature the emulator
      already tracks. So band it on the RESIDUAL, not on raw ISM output.

WHAT A RESIDUAL BAND IS, HERE
  For each arm and each of its GCMs, drive OUR base model with THAT GCM's own forcing
  and compare to THAT GCM's own ISM runs:
      additive        d_g = ISM_g - pred_g          (cm)
      multiplicative  r_g = ISM_g / pred_g          (dimensionless)
  The spread of d (or r) ACROSS GCMs is the irreducible part. Transfer it to our own
  forcing with the SAME rule the shipped builder uses -- PCHIP through the anchors
  against the 2015-2300 GSAT integral -- and the band at our forcing is
      additive        base_ours + [d_lo, d_hi]
      multiplicative  base_ours * [r_lo, r_hi]

  Written that way the criterion has a clean reading: the reservoir must supply what
  our base systematically under-delivers against the ISMs, and the residual band says
  how much that is and how uncertain it is.

BOTH FORMS ARE COMPUTED AND THE CHOICE IS FLAGGED, NOT RESOLVED. The residuals grow
with level (6.5-65.0 cm on ssp585 against -2.4 to -0.9 on ssp245), which argues
multiplicative; but the cool arms straddle zero, where a ratio is ill-conditioned.
RESID_FORM selects which one the re-run scores on; both are printed.

THE LIMITATION THAT MATTERS
  The shipped matched bands rest on FIVE anchors. This rests on THREE -- the r2300
  arms only -- because an x2300 arm cannot be T-normalised without post-2100 CMIP6,
  which exists for one model [[pangeo_cmip6_no_ext]]. Our ssp585 forcing integral sits
  ABOVE the r2300 anchor hull, so its band comes from the hull rule, not interpolation.
  That is a weaker construction than the shipped one in exactly the place our headline
  scenario lives, and it is the price of the residual basis.

WRITES outputs/diag_gis_residual_band.csv
  python3 python/diag_gis_residual_band.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
import gis_targets  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
from build_gis_matched_targets import interp_log  # noqa: E402
import scope_gis_reservoir_offline as R  # noqa: E402
import scope_gis_reservoir_rate_rank as RR  # noqa: E402
import diag_gis_gcm_tdecomp as TD  # noqa: E402

OUT = os.path.join(REPO, "outputs/diag_gis_residual_band.csv")

TAG, ARMS, OURS = A.TAG, A.ARMS, R.OURS
ARMS_R2300 = [a for a in ARMS if a[2] == "r2300"]
RES_TAU, RES_ONSET_K, RES_V_M = R.RES_TAU, R.RES_ONSET_K, R.RES_V_M
RAMP_W_GRID, RAMP_W_SHIPPED = RR.RAMP_W_GRID, RR.RAMP_W_SHIPPED
CM_PER_M, V_MAX_M, Y2100_TOL_CM = R.CM_PER_M, R.V_MAX_M, R.Y2100_TOL_CM
K_FIXED, HORIZONS, HIND = 1.0, A.HORIZONS, A.HIND
RESID_FORM = "additive"            # {"additive","multiplicative"} FLAGGED, not resolved
BAND_Q = (0.05, 0.95)
MIN_GCM_FOR_QUANTILE = 3           # below this use min/max; a 2-point p05 is not a p05
## HOW THE RESIDUAL SPREAD BECOMES AN INTERVAL. `minmax` takes the observed residuals
## at face value, which on an arm with 2 GCMs converts "we have almost no models" into
## "we have almost no uncertainty" -- the ssp245 band collapses to 1.5 cm and EXCLUDES
## our own base, so nothing can pass. `t_pi` is a Student-t PREDICTION interval for a
## further model, mean +/- t(n-1,0.975)*sd*sqrt(1+1/n), which is the same information
## with the sample size respected. BOTH are computed; the re-run scores on RESID_INTERVAL.
RESID_INTERVAL = "t_pi"            # {"minmax","t_pi"} FLAGGED, not resolved
MIN_GCM_FOR_SPREAD = 2             # below this an arm has no spread; band UNDEFINED
PI_LEVEL = 0.975
ANCHOR_SRC = os.path.join(REPO, "outputs/scope_gis_cool_band_targets.csv")
PRED, PRED_OURS = "gmst_int_theirs_Kyr", "gmst_int_ours_Kyr"
QCOLS_Q = [("slr2300_p05_cm", .05), ("slr2300_p17_cm", .17), ("slr2300_p50_cm", .50),
           ("slr2300_p83_cm", .83), ("slr2300_p95_cm", .95)]
SSP_OF = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}


def hull_pick(t, predcol, oi):
    """The shipped builder's UNION rule: bracketing anchors when outside the hull."""
    if oi > t[predcol].max():
        return t[t[predcol] >= t[t[predcol] < t[predcol].max()][predcol].max()]
    return t[t[predcol] <= t[t[predcol] > t[predcol].min()][predcol].min()]


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
           for y in tuple(HORIZONS) + tuple(HIND) + (2015,)}

    def load(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, amp, S_tab)

    gmst, drivers = {}, {}
    for ssp, lab, fam, stem in ARMS:
        gmst[(ssp, fam)], drivers[(ssp, fam)] = load(
            f"outputs/{stem}.csv", f"gmst_{A.ARM}")
    ours_gmst, ours_drv = {}, {}
    for ssp, lab in OURS:
        ours_gmst[lab], ours_drv[lab] = load(
            f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")

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
    offs = float(np.median(rebase_cm(basin2_series(Th, post, 1.0, 1.0))[:, idx[2015]]))
    base_ours = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                 for k, v in ours_drv.items()}

    def pred_at(gmst_rb):
        c = np.median(rebase_cm(basin2_series(
            regional_driver(gmst_rb, amp, S_tab), post, K_FIXED, s)), axis=0)
        return c[idx[2300]] - offs

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]

    print(f"diag_gis_residual_band — the residual band end-to-end, {TAG}, {nd} draws\n")
    per = []
    for ssp, lab, fam, _ in ARMS_R2300:
        sub = A.protect_band(ann, lab, fam)
        for gcm in sorted(sub.gcm.unique()):
            ser = TD.gcm_series(TD.GCM_ALIAS.get(gcm, gcm), SSP_OF[lab])
            if ser is None:
                sys.exit(f"{gcm}: no cmip6_gis series — run "
                         f"python/reduce_cmip6_tas_gis_extra.py {gcm} first.")
            gr = sub[sub.gcm == gcm]
            per.append(dict(arm=f"{lab} {fam}", lab=lab, fam=fam, gcm=gcm,
                            ism=float(gr[gr.year == 2300].gis_cm.median()),
                            pred=pred_at(ser["gmst"])))
    per = pd.DataFrame(per)
    per["d_add"] = per.ism - per.pred
    per["r_mult"] = per.ism / per.pred
    print(f"  {'arm':22}{'GCM':20}{'ISM':>8}{'ours':>8}{'d=ISM-ours':>13}"
          f"{'r=ISM/ours':>13}")
    for _, r in per.iterrows():
        print(f"  {r.arm:22}{r.gcm:20}{r.ism:8.1f}{r.pred:8.1f}{r.d_add:13.1f}"
              f"{r.r_mult:13.2f}")

    anchors = pd.read_csv(ANCHOR_SRC)

    def resid_band(per_v, form, interval=None):
        interval = RESID_INTERVAL if interval is None else interval
        col = "d_add" if form == "additive" else "r_mult"
        rows = []
        for arm, g in per_v.groupby("arm"):
            lab, fam = arm.rsplit(" ", 1)
            a = anchors[(anchors.label == lab) & (anchors.family == fam)]
            if a.empty or g.empty:
                continue
            v = g[col].to_numpy(float)
            ## A LEAVE-ONE-OUT IS NOT DEFINED ON A 2-GCM ARM. Dropping one leaves a
            ## SINGLE model and no spread at all; taking min==max would silently
            ## produce a ZERO-WIDTH band that nothing can clear, and that would read
            ## as "this GCM is load-bearing" when it is really "this arm has 2 models".
            if len(v) < MIN_GCM_FOR_SPREAD:
                return None
            if interval == "t_pi" and len(v) >= 2:
                half = (stats.t.ppf(PI_LEVEL, len(v) - 1) * v.std(ddof=1)
                        * np.sqrt(1.0 + 1.0 / len(v)))
                lo_, hi_ = v.mean() - half, v.mean() + half
            elif len(v) >= MIN_GCM_FOR_QUANTILE:
                lo_, hi_ = np.quantile(v, BAND_Q[0]), np.quantile(v, BAND_Q[1])
            else:
                lo_, hi_ = v.min(), v.max()
            rows.append(dict(lab=lab, pred=float(a[PRED].iloc[0]), lo=lo_, hi=hi_))
        t = pd.DataFrame(rows)
        if len(t) < 2:
            return None
        ## interp_log needs positive values; the additive residuals straddle zero, so
        ## shift by a constant, interpolate, shift back. The shift is common to lo and
        ## hi so it cannot change the band's WIDTH, only its placement.
        sh = float(min(t.lo.min(), t.hi.min())) - 1.0
        out = {}
        for ssp, lab in OURS:
            oi = float(anchors.loc[anchors.label == lab, PRED_OURS].iloc[0])
            base = base_ours[lab][idx[2300]]
            bl, e1 = interp_log(t.pred, t.lo - sh, oi)
            bh, e2 = interp_log(t.pred, t.hi - sh, oi)
            bl, bh = bl + sh, bh + sh
            if e1 or e2:
                near = hull_pick(t, "pred", oi)
                bl, bh = float(near.lo.min()), float(near.hi.max())
            out[lab] = ((base + bl, base + bh) if form == "additive"
                        else (base * bl, base * bh))
        return out

    print(f"\n=== THE RESIDUAL BAND AT OUR OWN FORCING (2300, cm) ===\n")
    print(f"  {'scenario':11}{'n':>3}{'base':>7}   {'SHIPPED':>19}"
          f"{'RESID add minmax':>21}{'RESID add t-PI':>23}{'widths sh/mm/t':>22}")
    nby = per.groupby("lab").size()
    for ssp, lab in OURS:
        sh = (100 * gis_targets.MATCHED_2300_M[lab][0],
              100 * gis_targets.MATCHED_2300_M[lab][1])
        mm = resid_band(per, "additive", "minmax")[lab]
        tp = resid_band(per, "additive", "t_pi")[lab]
        print(f"  {lab:11}{int(nby[lab]):3d}{base_ours[lab][idx[2300]]:7.1f}   "
              f"{sh[0]:7.1f}-{sh[1]:<11.1f}{mm[0]:8.1f}-{mm[1]:<12.1f}"
              f"{tp[0]:9.1f}-{tp[1]:<13.1f}"
              f"{sh[1] - sh[0]:6.0f}/{mm[1] - mm[0]:.0f}/{tp[1] - tp[0]:.0f}")
    print(f"\n  ** THE minmax BAND EXCLUDES OUR OWN BASE ON SSP2-4.5 ** "
          f"(top {resid_band(per, 'additive', 'minmax')['SSP2-4.5'][1]:.1f} vs base "
          f"{base_ours['SSP2-4.5'][idx[2300]]:.1f}),\n  and the reservoir can only ADD "
          f"— so under minmax NO cell can pass, on any drop. That is not a\n  model "
          f"failure, it is 2 GCMs agreeing to 1.5 cm being read as a 1.5 cm "
          f"uncertainty.")

    cache = {}
    for on in RES_ONSET_K:
        for tau in RES_TAU:
            for w in RAMP_W_GRID:
                for _, lab in OURS:
                    cache[(on, tau, w, lab)] = RR.reservoir_unit_w(
                        ours_gmst[lab], on, tau, w)

    def count_pass(bs):
        n = 0
        for V in RES_V_M:
            for on in RES_ONSET_K:
                for tau in RES_TAU:
                    for w in RAMP_W_GRID:
                        ok = V <= V_MAX_M
                        for _, lab in OURS:
                            u = cache[(on, tau, w, lab)]
                            v23 = base_ours[lab][idx[2300]] + CM_PER_M * V * u[idx[2300]]
                            ok &= bs[lab][0] <= v23 <= bs[lab][1]
                            ok &= abs(CM_PER_M * V * u[idx[2100]]) < Y2100_TOL_CM
                        n += bool(ok)
        return n

    def raw_band(av):
        t, keep = anchors.copy(), []
        for i, r in t.iterrows():
            sb = av[(av.ssp == r.label) & av.exp.str.contains(r.family)
                    & ~av.exp.str.startswith(A.DROP_GCM) & (av.year == 2300)]
            if sb.empty:
                continue
            for c, qq in QCOLS_Q:
                t.at[i, c] = float(sb.gis_cm.quantile(qq))
            keep.append(i)
        t = t.loc[keep]
        out = {}
        for ssp, lab in OURS:
            oi = float(t.loc[t.label == lab, PRED_OURS].iloc[0])
            vl, e1 = interp_log(t[PRED], t["slr2300_p05_cm"], oi)
            vh, _ = interp_log(t[PRED], t["slr2300_p95_cm"], oi)
            if e1:
                near = hull_pick(t, PRED, oi)
                vl, vh = float(near["slr2300_p05_cm"].min()), \
                    float(near["slr2300_p95_cm"].max())
            out[lab] = (vl, vh)
        return out

    print(f"\n=== LEAVE-ONE-GCM-OUT: RAW matched band vs RESIDUAL band "
          f"({RESID_FORM}, {RESID_INTERVAL}) ===\n")
    ncell = len(RES_V_M) * len(RES_ONSET_K) * len(RES_TAU) * len(RAMP_W_GRID)
    print(f"  cells clearing the three 2300 bands + the 2100 tolerance, of {ncell}\n")
    print(f"  {'dropped GCM':22}{'RAW band':>10}{'RESIDUAL band':>16}")
    recs = []
    for g in [None] + sorted(set(per.gcm)):
        pv = per if g is None else per[per.gcm != g]
        av = ann if g is None else ann[ann.gcm != g]
        rb = resid_band(pv, RESID_FORM)
        nr = count_pass(raw_band(av))
        nres = count_pass(rb) if rb is not None else np.nan
        nm = "(none) FULL" if g is None else g
        ## which arms lost their spread entirely on this drop
        lost = [a for a, gg in pv.groupby("arm") if len(gg) < MIN_GCM_FOR_SPREAD]
        recs.append(dict(dropped=nm, n_raw=nr, n_resid=nres,
                         arms_below_min=";".join(lost) or "-"))
        print(f"  {nm:22}{nr:10d}"
              + (f"{nres:16.0f}" if nres == nres else f"{'UNDEFINED':>16}")
              + (f"   {lost[0]} down to 1 GCM" if lost else ""))

    out = pd.DataFrame(recs)
    out.to_csv(OUT, index=False)
    b, d = out.iloc[0], out.iloc[1:]
    print(f"\n=== DID BANDING ON THE RESIDUAL FIX THE FRAGILITY? ===\n")
    for c, nm in (("n_raw", "RAW matched band"), ("n_resid", "RESIDUAL band")):
        ok = d[c].notna()
        print(f"  {nm:22} baseline {b[c]:4.0f}   over the {int(ok.sum())} DEFINED drops "
              f"{d.loc[ok, c].min():4.0f}-{d.loc[ok, c].max():4.0f}   zeroed: "
              f"{int((d.loc[ok, c] == 0).sum())}/{int(ok.sum())}"
              + (f"   ({int((~ok).sum())} undefined)" if (~ok).any() else ""))
    print(f"\n  ** THE COOL ARMS HAVE 2 GCMs, SO NO DROP IS DEFINED FOR THEM. ** Only "
          f"the ssp585 arm\n  (n=5) can carry a leave-one-out at all. The RAW band "
          f"appears to survive cool-arm drops\n  only because it quantiles RUN-level "
          f"percentile variants rather than models — which is\n  the same "
          f"over-counting diag_gis_scorecard_logo.py flagged.")
    print(f"\n  RESID_FORM = {RESID_FORM!r}, RESID_INTERVAL = {RESID_INTERVAL!r} — both "
          f"FLAGGED, not resolved.\n  Built on THREE r2300 anchors, not the shipped "
          f"five: an x2300 arm cannot be T-normalised\n  without post-2100 CMIP6. Our "
          f"ssp585 forcing sits ABOVE that 3-anchor hull, so its band\n  comes from "
          f"the hull rule rather than interpolation — weaker than the shipped\n  "
          f"construction exactly where our headline scenario lives.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
