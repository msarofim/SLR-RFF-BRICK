"""OPTION (b) — SPLIT THE GCM SPREAD INTO A LOCAL-T PART WE CAN CORRECT FOR AND A
PRECIPITATION/SMB RESIDUAL WE CANNOT.

THE FRAMING IS MARCUS'S (2026-08-22). The two things that differ between the GCMs
behind a PROTECT band are (1) the rate of LOCAL temperature change, which our emulator
could in principle be driven with directly, and (2) the change in PRECIPITATION, which
our emulator has no term for at all. So the band-basis question is NOT "run-level or
GCM-clustered quantiles". It is: how much of the across-GCM band width is local
temperature, and how much is irreducible?

WHY IT MATTERS NOW. diag_gis_scorecard_logo.py showed two single GCMs each void the
entire admissible set -- CESM2 through the ssp245 matched band, MPI-ESM1-2-HR through
ssp585. If most of that spread is local-T, it is CORRECTABLE and the bands are far
tighter than they look. If it is precipitation, the band is honest and our emulator is
structurally short a term.

THE DECOMPOSITION, per arm
  total     spread across GCMs of the ISM runs' own 2300 SLR          <- today's band
  local-T   spread across GCMs of OUR prediction when each GCM is
            driven by ITS OWN Greenland temperature                   <- correctable
  residual  spread across GCMs of (ISM - our prediction)              <- IRREDUCIBLE:
            precipitation / SMB, plus ISM structure

TWO DRIVE ROUTES, so the amp law is separated from the GCM's actual local warming
  GMST route    our production path: regional_driver(GMST_own, amp draws, S). Uses the
                GCM's global temperature and OUR amplification law.
  DIRECT route  the GCM's OWN Greenland-south anomaly spliced in place of amp*S*GMST,
                bypassing the amp law entirely.
  The gap between them IS the amp law's error for that GCM -- Marcus's "rate of local
  temperature change, which we might be able to correct for", measured per model.

SCOPE, AND WHAT IS NOT COVERED -- stated, not buried
  * r2300 ARMS ONLY. Their convention is the GCM's own scenario to 2100 then HELD at
    its 2081-2100 mean (Goelzer 2025), so they need NO post-2100 CMIP6 and can be
    rebuilt per GCM exactly. The x2300 arms need the CMIP6 extension, which exists
    only for CESM2-WACCM ssp126 -- [[pangeo_cmip6_no_ext]]. x2300 is OUT OF SCOPE here.
  * UKESM1-0-LL IS ABSENT from data/cmip6_gis, so UKESM1-0-LL-Robin cannot be
    T-normalised and is EXCLUDED from ssp585 r2300 (4 of its 5 GCMs remain). This is a
    coverage gap in the diagnostic, not a finding about that model.
  * PROVIDER TAGS. PROTECT writes "CESM2-Leo" (ssp585) and bare "CESM2" (ssp245/126)
    for what the label convention says is the same model, and "UKESM1-0-LL-Robin" for
    UKESM1-0-LL; "-Leo"/"-Robin" are provider/downscaling tags. CESM2-Leo -> CESM2 is
    an ALIAS DECISION, flagged, and its sensitivity is reported by re-running the
    ssp585 decomposition without it.
  * MEMBER. One member per model in cmip6_gis (CESM2 is r10i1p1f1, not r1); whichever
    member PROTECT forced with is not recorded here, so member spread lands in the
    residual and is NOT separated from precipitation.
  * RCM. The "GCM" label conflates GCM and regional model -- ssp126 CESM2 is RACMO2.3p2
    while ssp245 CESM2 is MARv3.12. The RCM is itself a precipitation choice, so the
    per-RCM split is REPORTED alongside rather than averaged over.

WRITES outputs/diag_gis_gcm_tdecomp.csv
  python3 python/diag_gis_gcm_tdecomp.py
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
    DRIVER_BASE, YEARS, GIS_ZONE, OBS, ANCHOR_N,
    gis_shape_table, regional_driver,
)

OUT = os.path.join(REPO, "outputs/diag_gis_gcm_tdecomp.csv")

# --- named constants ---------------------------------------------------------
TAG = A.TAG
CMIP6_DIR = os.path.join(REPO, "data/cmip6_gis")
## The shipped 40-model panel is capped alphabetically at NorESM2-MM, so UKESM1-0-LL
## lives in a SEPARATE directory (reduce_cmip6_tas_gis_extra.py) precisely so that
## diag_gis_amp_cmip6.py's glob over the shipped panel -- and therefore the shipped
## gis_amp_shape.csv -- cannot change. Searched second; opting in is explicit.
CMIP6_EXTRA_DIR = os.path.join(REPO, "data/cmip6_gis_extra")
TAS_GLOBAL, TAS_REG = "tas_global", f"tas_gis_{GIS_ZONE}"
## The ISM responds to the WHOLE sheet; our emulator's driver zone is `south`. Both are
## carried, because the difference between them turned out to be the main result.
TAS_ALL = "tas_gis_all"
ZONES = [GIS_ZONE, "all", "central", "north"]
AMP_WIN = (2081, 2100)          # the window the r2300 hold is taken over
## The r2300 convention, verbatim from Goelzer 2025 as scope_gis_cool_band_forcing.py
## records it: the GCM's own scenario through 2100, then HELD at its 2081-2100 mean.
HOLD_WIN = (2081, 2100)
ARMS_IN_SCOPE = [a for a in A.ARMS if a[2] == "r2300"]
## PROTECT label -> cmip6_gis series. "-Leo"/"-Robin" are provider tags, not models.
GCM_ALIAS = {"CESM2-Leo": "CESM2", "UKESM1-0-LL-Robin": "UKESM1-0-LL"}
ALIAS_SENSITIVITY = "CESM2-Leo"     # re-run ssp585 without this to price the alias
SSP_OF = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}
RATE_WIN = (2250, 2300)
K_FIXED = 1.0
MIN_GCM_FOR_FIT = 3       # below this a regression across GCMs is not defined
SPREAD = lambda v: (float(np.max(v) - np.min(v)) if len(v) > 1 else np.nan)


def gcm_series(model, ssp):
    """That model's own (GMST, Greenland-south) on the r2300 convention, rebased to
    DRIVER_BASE. Returns None if the model is not in data/cmip6_gis."""
    p = os.path.join(CMIP6_DIR, f"tas_series_gis_{model}.csv")
    if not os.path.exists(p):
        p = os.path.join(CMIP6_EXTRA_DIR, f"tas_series_gis_{model}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p)
    d = d[d.scenario.isin(("historical", ssp))].sort_values("year")
    if d.empty:
        return None
    out = {}
    for col, key in ((TAS_GLOBAL, "gmst"), (TAS_REG, "reg"), (TAS_ALL, "all")):
        s = d.set_index("year")[col].reindex(YEARS)
        hold = s.loc[HOLD_WIN[0]:HOLD_WIN[1]].mean()
        s = s.where(YEARS <= HOLD_WIN[1], hold).to_numpy()
        if np.isnan(s).any():          # no pre-1850 / gaps: fill forward from first
            s = pd.Series(s).ffill().bfill().to_numpy()
        ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
        out[key] = s - s[ibd].mean()
    ## the model's OWN amplification per zone over AMP_WIN, for the zone table
    dd = d.set_index("year")
    b = dd.loc[DRIVER_BASE[0]:DRIVER_BASE[1]].mean(numeric_only=True)
    l = dd.loc[AMP_WIN[0]:AMP_WIN[1]].mean(numeric_only=True)
    dg = float(l[TAS_GLOBAL] - b[TAS_GLOBAL])
    out["dgmst"] = dg
    out["amp"] = {z: float(l[f"tas_gis_{z}"] - b[f"tas_gis_{z}"]) / dg for z in ZONES}
    return out


def driver_from_regional(reg_rb, ndraw):
    """The SAME splice as regional_driver (scope_gis_2300_relaxation.py:114-129) --
    observed history through the obs record, then an anchor-preserving splice -- but
    with the regional anomaly supplied DIRECTLY instead of built as amp*S*GMST."""
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    gd = dict(zip(tgz["year"].astype(int), tgz[GIS_ZONE].astype(float)))
    last = int(tgz["year"].max())
    obs = np.array([gd.get(int(y), 0.0) for y in YEARS])
    mask = YEARS <= last
    ianch = np.isin(YEARS, np.arange(last - ANCHOR_N + 1, last + 1))
    off = obs[ianch].mean() - reg_rb[ianch].mean()
    spliced = reg_rb + off
    return np.tile(np.where(mask, obs, spliced), (ndraw, 1))


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    amp = post["gis_amp"].to_numpy()
    S_tab = gis_shape_table()
    nd = len(post)
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in (2015, 2100, 2300) + RATE_WIN + A.HIND}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    ## ONE bisection. The driver is OBSERVED through the obs record and only spliced
    ## after, so a per-GCM projection tail cannot touch the fitted period -- the same
    ## structural reason the amp law came out exactly hindcast-inert.
    g = pd.read_csv(f"outputs/{ARMS_IN_SCOPE[0][3]}.csv").set_index(
        "year")[f"gmst_{A.ARM}"].reindex(YEARS).to_numpy()
    Th = regional_driver(g - g[ibd].mean(), amp, S_tab)
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[A.HIND[1]] - tgt.loc[A.HIND[0]])
    lo, hi = np.full(nd, 1e-4), np.full(nd, 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(Th, post, K_FIXED, mid)
        b = 100.0 * (L[:, idx[A.HIND[1]]] - L[:, idx[A.HIND[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s = np.sqrt(lo * hi)
    offs = float(np.median(rebase_cm(basin2_series(Th, post, 1.0, 1.0))[:, idx[2015]]))

    def predict(drv):
        c = np.median(rebase_cm(basin2_series(drv, post, K_FIXED, s)), axis=0)
        return (c[idx[2300]] - offs,
                (c[idx[RATE_WIN[1]]] - c[idx[RATE_WIN[0]]])
                / (RATE_WIN[1] - RATE_WIN[0]) * 100.0)

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]
    ann["rcm"] = ann.exp.str.split("_").str[2]

    print(f"diag_gis_gcm_tdecomp — local-T vs precipitation in the GCM spread, "
          f"{TAG}, {nd} draws")
    print(f"  r2300 arms only (held at the {HOLD_WIN[0]}-{HOLD_WIN[1]} mean, so no "
          f"post-2100 CMIP6 is needed)\n")

    rows, missing = [], []
    for ssp, lab, fam, _ in ARMS_IN_SCOPE:
        sub = A.protect_band(ann, lab, fam)
        print(f"=== {lab} {fam} ===\n")
        print(f"  {'GCM':22}{'RCM':22}{'ISM':>9}{'GMST-rt':>11}{'DIR-sth':>9}"
              f"{'DIR-all':>10}{'amp sth':>9}{'ours':>9}")
        for gcm in sorted(sub.gcm.unique()):
            model = GCM_ALIAS.get(gcm, gcm)
            ser = gcm_series(model, SSP_OF[lab])
            g_runs = sub[sub.gcm == gcm]
            ism = float(g_runs[g_runs.year == 2300].gis_cm.median())
            rcm = "/".join(sorted(set(g_runs.rcm)))
            if ser is None:
                missing.append(f"{lab} {fam} / {gcm} (-> {model})")
                print(f"  {gcm:22}{rcm:22}{ism:9.1f}"
                      f"{'ABSENT from data/cmip6_gis':>39}")
                continue
            L2300_g, rate_g = predict(regional_driver(ser["gmst"], amp, S_tab))
            L2300_d, rate_d = predict(driver_from_regional(ser["reg"], nd))
            L2300_a, rate_a = predict(driver_from_regional(ser["all"], nd))
            ## the GCM's OWN Greenland amplification, secant at 2300 on its own
            ## r2300-held path, against what our law applies at that warming level
            own_amp = ser["reg"][idx[2300]] / ser["gmst"][idx[2300]]
            our_amp = float(np.median(amp) * S_tab(np.array([ser["gmst"][idx[2300]]]))[0])
            rows.append(dict(arm=f"{lab} {fam}", gcm=gcm, model=model, rcm=rcm,
                             n_runs=int(g_runs.groupby(["group", "model", "exp"]).ngroups),
                             ism_2300_cm=ism, pred_gmst_cm=L2300_g,
                             pred_direct_cm=L2300_d, pred_allzone_cm=L2300_a,
                             rate_gmst=rate_g, rate_direct=rate_d, rate_allzone=rate_a,
                             **{f"amp_{z}": ser["amp"][z] for z in ZONES},
                             dgmst_K=ser["dgmst"], gmst_2300_K=ser["gmst"][idx[2300]],
                             reg_2300_K=ser["reg"][idx[2300]],
                             own_amp=own_amp, our_amp=our_amp,
                             resid_gmst=ism - L2300_g, resid_direct=ism - L2300_d,
                             resid_allzone=ism - L2300_a,
                             src=("shipped" if os.path.exists(os.path.join(
                                 CMIP6_DIR, f"tas_series_gis_{model}.csv"))
                                 else "extra")))
            print(f"  {gcm:22}{rcm:22}{ism:9.1f}{L2300_g:11.1f}{L2300_d:9.1f}"
                  f"{L2300_a:10.1f}{own_amp:9.2f}{our_amp:9.2f}")
        print()

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    if missing:
        print(f"  NOT T-NORMALISABLE (absent from data/cmip6_gis): "
              f"{'; '.join(missing)}\n")

    # --- HOW MUCH OF THE ACROSS-GCM ORDERING DOES LOCAL T EXPLAIN? --------------
    ## NOT a max-min "decomposition". Spreads do not add, and a route that makes the
    ## prediction WORSE can produce a residual spread LARGER than the total, which
    ## reads as a nonsense >100 % share. The honest measure is how much of the
    ## across-GCM VARIANCE in the ISM output each route explains, plus the rank
    ## agreement, which is what a band basis actually needs.
    def explains(g, col):
        x, y = g[col].to_numpy(float), g.ism_2300_cm.to_numpy(float)
        if len(g) < MIN_GCM_FOR_FIT or np.std(x) == 0:
            return np.nan, np.nan, np.nan
        r = float(np.corrcoef(x, y)[0, 1])
        rk = float(np.corrcoef(np.argsort(np.argsort(x)),
                               np.argsort(np.argsort(y)))[0, 1])
        # residual after the BEST linear rescale of this predictor
        res = y - np.polyval(np.polyfit(x, y, 1), x)
        return r ** 2, float(np.std(res, ddof=1) / np.std(y, ddof=1)), rk

    print(f"=== HOW MUCH OF THE ACROSS-GCM SPREAD IS LOCAL TEMPERATURE? ===\n")
    print(f"  {'arm':22}{'nGCM':>5}{'ISM sd':>9}  {'route':<14}{'R2':>7}{'rank r':>8}"
          f"{'resid sd / ISM sd':>20}")
    for arm, g in out.groupby("arm"):
        if len(g) < MIN_GCM_FOR_FIT:
            print(f"  {arm:22}{len(g):5d}{g.ism_2300_cm.std(ddof=1):9.1f}  "
                  f"n < {MIN_GCM_FOR_FIT} — NOT FITTED; see the GUIDANCE block below")
            continue
        first = True
        for col, nm in (("pred_gmst_cm", "GMST (ours)"), ("pred_direct_cm", "DIRECT-south"),
                        ("pred_allzone_cm", "DIRECT-all")):
            r2, ratio, rr = explains(g, col)
            head = (f"  {arm:22}{len(g):5d}{g.ism_2300_cm.std(ddof=1):9.1f}  "
                    if first else f"  {'':22}{'':5}{'':9}  ")
            print(head + f"{nm:<14}{r2:7.2f}{rr:8.2f}{ratio:20.2f}")
            first = False
    print(f"\n  R2 = across-GCM variance in the ISM 2300 level explained by that route; "
          f"'rank r' is\n  Spearman, which does not assume linearity. 'resid sd / ISM "
          f"sd' = the fraction of the\n  band's own width surviving the best linear "
          f"rescale of that predictor — the IRREDUCIBLE\n  share: precipitation / SMB "
          f"+ ISM structure + member, which this cannot separate further.")
    print(f"\n  ** n IS SMALL. ** The only arm with enough GCMs to fit is "
          f"ssp585 r2300, and it has {int(out[out.arm.str.startswith('SSP5')].shape[0])} "
          f"— a 2-parameter fit on\n  {int(out[out.arm.str.startswith('SSP5')].shape[0])} "
          f"points. Read R2 as indicative, not as an estimate with an interval. The two "
          f"COOL\n  arms have 2 GCMs each and CANNOT be assessed this way at all — "
          f"which includes ssp245,\n  the arm where CESM2 was load-bearing in "
          f"diag_gis_scorecard_logo.py.")

    # --- GUIDANCE FROM THE UNDER-POWERED ARMS ------------------------------------
    ## Marcus 2026-08-22: an arm with too few GCMs to fit is still usable for GUIDANCE.
    ## With n = 2 there is exactly one pairwise contrast, and it answers the same
    ## question a regression would -- does our route move in the right direction, and
    ## by how much of the gap -- without pretending to be an estimate.
    print(f"\n=== GUIDANCE FROM THE ARMS TOO SMALL TO FIT (pairwise, n = 2) ===\n")
    print(f"  {'arm':22}{'contrast':34}{'ISM gap':>9}{'ours':>8}{'explained':>11}"
          f"{'residual':>10}")
    for arm, g in out.groupby("arm"):
        if len(g) != 2:
            continue
        g = g.sort_values("ism_2300_cm")
        a, bq = g.iloc[0], g.iloc[1]
        ism_gap = bq.ism_2300_cm - a.ism_2300_cm
        our_gap = bq.pred_gmst_cm - a.pred_gmst_cm
        print(f"  {arm:22}{bq.gcm + ' - ' + a.gcm:34}{ism_gap:9.1f}{our_gap:8.1f}"
              f"{our_gap / ism_gap:10.2f}x{ism_gap - our_gap:10.1f}")
    print(f"\n  'explained' = our GMST-route gap over the ISM gap. 1.00x would mean "
          f"local temperature\n  accounts for the whole difference between those two "
          f"models; negative would mean our\n  route orders them the WRONG WAY. One "
          f"contrast is guidance, not an estimate — but it is\n  the only evidence "
          f"these arms can give, and discarding it would leave them unexamined.")

    # --- THE ZONE RESULT ---------------------------------------------------------
    print(f"\n=== THE ZONE — our driver is SOUTH Greenland carrying a NORTH-sized "
          f"amplification ===\n")
    print(f"  per-model amplification over {AMP_WIN[0]}-{AMP_WIN[1]} vs 1850-1900, "
          f"by zone:\n")
    print(f"  {'arm':22}{'GCM':16}{'dGMST':>7}" + "".join(f"{z:>10}" for z in ZONES)
          + f"{'OUR law':>10}")
    for _, r in out.iterrows():
        print(f"  {r.arm:22}{r.gcm:16}{r.dgmst_K:7.2f}"
              + "".join(f"{r[f'amp_{z}']:10.2f}" for z in ZONES)
              + f"{r.our_amp:10.2f}")
    sth = out[[f"amp_{GIS_ZONE}"]].to_numpy().ravel()
    print(f"\n  OUR law applies {out.our_amp.min():.2f}-{out.our_amp.max():.2f} to the "
          f"`{GIS_ZONE}` zone. These models put `{GIS_ZONE}` at\n  "
          f"{sth.min():.2f}-{sth.max():.2f} and `north` at "
          f"{out.amp_north.min():.2f}-{out.amp_north.max():.2f} — so the law applies a "
          f"NORTH-sized\n  amplification to a SOUTH-zone driver, over-driving it by "
          f"{np.median(out.our_amp / sth):.2f}x at the median.")
    print(f"\n  This is a DIRECT measurement of section 4.2's sub-choice 1, on the very "
          f"models\n  PROTECT used: the flat-hold's {out.our_amp.median():.2f} against "
          f"a measured {np.median(sth):.2f}. It does NOT\n  by itself mean the emulator "
          f"is wrong — c1 was calibrated against the OBSERVED south\n  driver and "
          f"absorbs the level — which is exactly why the DIRECT routes above "
          f"UNDER-predict.")

    # --- THE ALIAS SENSITIVITY ----------------------------------------------------
    a585 = out[out.arm.str.startswith("SSP5-8.5")]
    if ALIAS_SENSITIVITY in set(a585.gcm) and len(a585) - 1 >= MIN_GCM_FOR_FIT:
        print(f"\n=== ALIAS SENSITIVITY — dropping {ALIAS_SENSITIVITY}, the one GCM "
              f"whose cmip6_gis series is an ALIAS ===\n")
        for nm, g in (("with    it", a585),
                      ("without it", a585[a585.gcm != ALIAS_SENSITIVITY])):
            r2, ratio, rr = explains(g, "pred_gmst_cm")
            print(f"  {nm}: n={len(g)}  GMST-route R2 {r2:.2f}  rank r {rr:.2f}  "
                  f"resid sd / ISM sd {ratio:.2f}")
        print(f"  (dropping it leaves n={len(a585) - 1}, the bare minimum for a fit — "
              f"treat as a direction, not a number.)")

    # --- WHAT THE BAND BASIS SHOULD THEREFORE BE ----------------------------------
    g5 = out[out.arm.str.startswith("SSP5-8.5")]
    r2, ratio, rr = explains(g5, "pred_gmst_cm")
    print(f"\n=== THE ANSWER TO THE BAND-BASIS QUESTION ===\n")
    print(f"  On the one arm that can be fitted, OUR OWN production drive route "
          f"explains R2 = {r2:.2f}\n  of the across-GCM variance, and only "
          f"{ratio:.0%} of the band's width survives it. So most\n  of what the raw "
          f"band calls uncertainty is LOCAL TEMPERATURE the emulator already "
          f"tracks,\n  not ice-sheet disagreement.")
    print(f"\n  ==> Build the band on the RESIDUAL after regressing out our own "
          f"prediction, not on\n      raw ISM output — neither run-level nor "
          f"GCM-clustered quantiles of the raw runs.\n      Run-level and "
          f"GCM-clustered were the WRONG two options; both quantile the total.")
    print(f"\n  ==> Expected effect on the diag_gis_scorecard_logo.py fragility: a "
          f"residual band is\n      ~{1 / max(ratio, 1e-9):.1f}x narrower, so one "
          f"GCM moves proportionally less of it. NOT YET MEASURED\n      — that is "
          f"the next step, and it needs the cool arms, which have only 2 GCMs each.")
    nex = int((out.src == "extra").sum())
    print(f"\n  ==> UKESM1-0-LL is now INCLUDED ({nex} model(s) from "
          f"data/cmip6_gis_extra), so the ssp585\n      arm is complete at n="
          f"{len(g5)} — every GCM PROTECT forced it with.")

    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
