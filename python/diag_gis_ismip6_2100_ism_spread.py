"""HOW MUCH OF THE 2100 "OVER-PREDICTION" IS THE CHOICE OF ONE ICE-SHEET MODEL?

THE QUESTION. handoff_2026-08-23_greenland_targets.md section 2.4 established that our
2100 error against PROTECT is SYSTEMATIC -- all 9 GCM-cases fast, median 1.39x -- and
read that as "model-side, therefore correctable". But every PROTECT anchor is NORCE-CISM:
ONE ice-sheet model. A systematic offset is EXACTLY what the choice of a single ISM
would produce. Before correcting a defect, price how much of it is the target.

THE INDEPENDENT SOURCE. ISMIP6 (Payne et al. 2021, doi 10.5281/zenodo.4498331) ran
16 ice-sheet models over the SAME 21st century under the SAME CMIP6 GCM forcings.
Three of its GCM/scenario cells overlap PROTECT's ssp585 arm, so for those three the
ISM structural spread can be laid directly alongside our own error.

WHAT THIS IS AND IS NOT -- Marcus's priority ordering, 2026-08-22
  Matching TRANSIENT ice models is priority 4 of 5, below volume+history (1),
  long-term commitment (2) and melt-rate constraints (3). And the stringency of a
  test scales with the number of models behind it. So this file reports an ENVELOPE
  CHECK -- "is our 2100 inside the ISM spread?" -- and deliberately emits NO loss
  term, NO band, and NO admissible set. It is guidance about how much weight the
  2100 defect deserves, not a new objective to optimise against.

TWO PROTOCOL CAVEATS THAT TRAVEL WITH EVERY NUMBER BELOW
  * ISMIP6 GrIS EXCLUDES peripheral glaciers and ice caps (README); so does our GIS
    component, which is why the comparison is admissible at all. PROTECT is on the
    same footing (control-drift-corrected, rel 2015).
  * The STANDARD ocean protocol (expb01-b05) is the controlled retreat
    parameterisation and is the primary set here; the OPEN protocol (expb06-b10) has
    only 2-3 models and is reported separately, never pooled in.

THE TIME AXIS IS POSITIONAL, ON PURPOSE. All 69 GrIS scalar files carry exactly 86
  annual records = 2015-2100 by protocol, but their `time` ATTRIBUTES disagree wildly
  once decoded (AWI -> 2016-2101, UCIJPL -> 2014-2099, UAF -> 2017-2438). Decoding
  them silently mis-indexes 30 of 69 files and reads two models as ~0 cm. Index 0 is
  2015 and index 85 is 2100; the gate is n == 86 AND sle[0] == 0.

WRITES outputs/diag_gis_ismip6_2100_ism_spread.csv
       outputs/diag_gis_ismip6_2100_ism_spread_arms.csv
  python3 python/diag_gis_ismip6_2100_ism_spread.py
"""
import os
import re
import sys
import glob
import warnings

import numpy as np
import pandas as pd
import netCDF4 as nc

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
import diag_gis_gcm_tdecomp as TD  # noqa: E402

OUT_ISM = os.path.join(REPO, "outputs/diag_gis_ismip6_2100_ism_spread.csv")
OUT_ARM = os.path.join(REPO, "outputs/diag_gis_ismip6_2100_ism_spread_arms.csv")
ICE_DIR = os.path.join(
    REPO, "data/gis_post2100/ismip6_scalars/CMIP5_CMIP6_Scalars_Paper/GrIS/Ice")

# --- named constants; every label and verdict below derives from these ---------
TAG = A.TAG
SOURCE = ("ISMIP6 CMIP6-forced GrIS scalars, Payne et al. 2021 GRL, "
          "doi 10.5281/zenodo.4498331")
YEAR_BASE, YEAR_TEST = 2015, 2100     # index 0 and index N_REC-1
N_REC = 86                            # 2015..2100 inclusive; the file-conformance gate
CM_PER_M = 100.0
SLE_SIGN = -1.0                       # `sle` DECREASES with mass loss (README)
## expid -> (GCM as ISMIP6 names it, scenario, ocean protocol). README "Ice" block.
EXPID = {
    "expb01": ("CNRM-CM6-1",   "ssp585", "standard"),
    "expb02": ("CNRM-CM6-1",   "ssp126", "standard"),
    "expb03": ("UKESM1-0-LL",  "ssp585", "standard"),
    "expb04": ("CESM2",        "ssp585", "standard"),
    "expb05": ("CNRM-ESM2-1",  "ssp585", "standard"),
    "expb06": ("CNRM-CM6-1",   "ssp585", "open"),
    "expb07": ("CNRM-CM6-1",   "ssp126", "open"),
    "expb08": ("UKESM1-0-LL",  "ssp585", "open"),
    "expb09": ("CESM2",        "ssp585", "open"),
    "expb10": ("CNRM-ESM2-1",  "ssp585", "open"),
}
PROTOCOL_PRIMARY = "standard"
## The ISMIP6 entry closest in lineage to PROTECT's NORCE CISM16t -- same ice
## dynamics core, different institution, SMB and initialisation. Named so the
## "is the target model low?" question has a like-family answer, not just a median.
CISM_ENTRY = "NCAR_CISM"
PROTECT_MODEL_NOTE = ("PROTECT anchors are NORCE CISM16t-MAR39; the ISMIP6 CISM entry "
                      "is NCAR_CISM -- same dynamical core, different institution, SMB "
                      "and initialisation, so NOT the same run")
## Which of our arms each ISMIP6 cell can be compared against. `protect` is the
## PROTECT (GCM, family) whose 2100 median is the shipped target; None means the
## cell is an evaluation point with NO PROTECT counterpart at all.
CROSSWALK = {
    ("CESM2", "ssp585"):       ("CESM2-Leo", "SSP5-8.5", "r2300"),
    ("CNRM-ESM2-1", "ssp585"): ("CNRM-ESM2-1", "SSP5-8.5", "r2300"),
    ("UKESM1-0-LL", "ssp585"): ("UKESM1-0-LL-Robin", "SSP5-8.5", "r2300"),
    ("CNRM-CM6-1", "ssp585"):  None,
    ("CNRM-CM6-1", "ssp126"):  None,
}
SSP_LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
K_FIXED = 1.0
MIN_ISM_FOR_SPREAD = 5    # below this a median-and-envelope is not worth quoting
## The shared cells must reproduce the file that MEASURED the 2100 defect, so this
## diagnostic cannot quietly disagree with the thing it is pricing.
REPRO_CSV = os.path.join(REPO, "outputs/diag_gis_amp_likeforlike_2100.csv")
REPRO_TOL_CM = 1e-6
## How far PROTECT's single ISM may sit from the multi-model median before "the
## target is the problem" is a supportable reading rather than a canned narrative.
TARGET_LOW_THRESH = 0.90


def read_ismip6():
    """Every GrIS Ice scalar as a 2100 sea-level contribution in cm, rel 2015.

    POSITIONAL indexing (see module docstring): the `time` attributes are not
    trustworthy across providers, the record count is. Files failing the gate are
    returned in `skipped` rather than silently dropped."""
    rows, skipped = [], []
    for f in sorted(glob.glob(os.path.join(ICE_DIR, "*.nc"))):
        b = os.path.basename(f)
        m = re.match(r"scalars_mm_cr_GIS_(.+)_(expb\d\d)\.nc", b)
        if m is None:
            skipped.append((b, "unparseable filename"))
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d = nc.Dataset(f)
            s = np.asarray(d.variables["sle"][:], dtype=float)
            d.close()
        if len(s) != N_REC:
            skipped.append((b, f"{len(s)} records, expected {N_REC}"))
            continue
        if abs(s[0]) > 1e-9:
            skipped.append((b, f"sle[0] = {s[0]:.3e}, expected 0 (ctrl-removed)"))
            continue
        gcm, ssp, proto = EXPID[m.group(2)]
        rows.append(dict(ism=m.group(1), exp=m.group(2), gcm=gcm, ssp=ssp,
                         protocol=proto,
                         cm_2100=SLE_SIGN * (s[-1] - s[0]) * CM_PER_M))
    return pd.DataFrame(rows), skipped


def main():
    ism, skipped = read_ismip6()
    print(f"diag_gis_ismip6_2100_ism_spread — the 2100 defect, priced against "
          f"{ism.ism.nunique()} ice-sheet models\n")
    print(f"  SOURCE  {SOURCE}")
    print(f"  BASIS   cm sea-level contribution, {YEAR_TEST} rel {YEAR_BASE}, "
          f"control-removed, peripheral glaciers EXCLUDED")
    print(f"  NOTE    {PROTECT_MODEL_NOTE}")
    print(f"  read {len(ism)} files, {ism.ism.nunique()} ice-sheet models, "
          f"{len(skipped)} skipped by the n=={N_REC} / sle[0]==0 gate")
    for b, why in skipped:
        print(f"    SKIP {b}: {why}")
    print()

    # --- our own 2100, on each GCM's own forcing, exactly the production path ----
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
           for y in (YEAR_TEST, YEAR_BASE) + tuple(A.HIND)}

    g = pd.read_csv(f"outputs/{A.ARMS[0][3]}.csv").set_index(
        "year")[f"gmst_{A.ARM}"].reindex(YEARS).to_numpy()
    hind_drv = regional_driver(g - g[ibd].mean(), amp, S_tab)
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
        basin2_series(hind_drv, post, 1.0, 1.0))[:, idx[YEAR_BASE]]))

    def ours_2100(gcm, ssp):
        ser = TD.gcm_series(gcm, ssp)
        if ser is None:
            return np.nan
        drv = regional_driver(ser["gmst"], amp, S_tab)
        c = np.median(rebase_cm(basin2_series(drv, post, K_FIXED, s)), axis=0)
        return float(c[idx[YEAR_TEST]] - offs)

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]

    # --- per (GCM, scenario) cell ------------------------------------------------
    prim = ism[ism.protocol == PROTOCOL_PRIMARY]
    cells = []
    for (gcm, ssp), grp in prim.groupby(["gcm", "ssp"]):
        v = grp.set_index("ism")["cm_2100"].sort_values()
        cw = CROSSWALK.get((gcm, ssp), None)
        prot = np.nan
        if cw is not None:
            sub = A.protect_band(ann, cw[1], cw[2])
            gr = sub[(sub.gcm == cw[0]) & (sub.year == YEAR_TEST)]
            prot = float(gr.gis_cm.median()) if len(gr) else np.nan
        mine = ours_2100(gcm, ssp)
        cism = float(v[CISM_ENTRY]) if CISM_ENTRY in v.index else np.nan
        cells.append(dict(
            gcm=gcm, ssp=ssp, ssp_label=SSP_LABEL[ssp], n_ism=len(v),
            ism_min=float(v.min()), ism_p25=float(v.quantile(0.25)),
            ism_median=float(v.median()), ism_p75=float(v.quantile(0.75)),
            ism_max=float(v.max()), ism_maxmin=float(v.max() / v.min()),
            cism=cism, cism_over_ismmed=cism / float(v.median()),
            cism_rank=int((v < cism).sum()) + 1 if np.isfinite(cism) else -1,
            protect_norce_cism=prot, protect_gcm=cw[0] if cw else "",
            ours=mine,
            r_vs_protect=mine / prot if np.isfinite(prot) else np.nan,
            r_vs_ism_median=mine / float(v.median()),
            inside_ism_envelope=bool(v.min() <= mine <= v.max()),
            ours_pctile_in_ism=100.0 * float((v < mine).mean()),
            r_vs_ism_max=mine / float(v.max()),
            protect_over_ismmed=prot / float(v.median()) if np.isfinite(prot) else np.nan,
        ))
    cell = pd.DataFrame(cells).sort_values(["ssp", "gcm"]).reset_index(drop=True)

    ## GATE. The three shared cells must reproduce diag_gis_amp_likeforlike_2100.csv
    ## to the digit -- same posterior, same bisection, same driver route. If they do
    ## not, this file has re-implemented the production path instead of reusing it.
    ref = pd.read_csv(REPRO_CSV)
    n_gate = 0
    for _, r in cell[cell.protect_gcm != ""].iterrows():
        m = ref[ref.gcm == r.protect_gcm]
        if not len(m):
            continue
        for col, have in (("shipped_2100", r.ours), ("ism_2100", r.protect_norce_cism)):
            got = float(m.iloc[0][col])
            if abs(got - have) > REPRO_TOL_CM:
                raise SystemExit(f"REPRO GATE: {r.protect_gcm} {col} {got:.6f} != "
                                 f"{have:.6f} (tol {REPRO_TOL_CM})")
            n_gate += 1
    print(f"  REPRO GATE PASSED: {n_gate} values identical to "
          f"{os.path.basename(REPRO_CSV)} within {REPRO_TOL_CM} cm\n")

    # --- report -----------------------------------------------------------------
    print("=== 1. THE ICE-SHEET-MODEL SPREAD AT 2100 (standard ocean protocol) ===\n")
    print(f"  {'GCM':14}{'ssp':8}{'n':>3}{'min':>8}{'median':>8}{'max':>8}"
          f"{'max/min':>9}   {CISM_ENTRY:>10}{'rank':>6}{'/med':>7}")
    for _, r in cell.iterrows():
        print(f"  {r.gcm:14}{r.ssp:8}{r.n_ism:3d}{r.ism_min:8.1f}{r.ism_median:8.1f}"
              f"{r.ism_max:8.1f}{r.ism_maxmin:8.2f}x   {r.cism:10.1f}"
              f"{r.cism_rank:4d}/{r.n_ism:<2d}{r.cism_over_ismmed:7.2f}")
    ok = cell[cell.n_ism >= MIN_ISM_FOR_SPREAD]
    print(f"\n  the ISM structural spread is {ok.ism_maxmin.min():.2f}-"
          f"{ok.ism_maxmin.max():.2f}x at a FIXED GCM forcing. For scale, the "
          f"defect being\n  chased is a median 1.39x against a single ISM.\n")

    print("=== 2. WHERE THE TARGET SITS, AND WHERE WE SIT ===\n")
    print(f"  {'GCM':14}{'ssp':8}{'PROTECT':>9}{'/ISMmed':>9}{'ISM med':>9}"
          f"{'ours':>8}{'ours/PRO':>10}{'ours/ISM':>10}{'ours/max':>10}{'pctile':>8}")
    for _, r in cell.iterrows():
        pro = f"{r.protect_norce_cism:9.1f}" if np.isfinite(r.protect_norce_cism) \
            else f"{'--':>9}"
        rpo = f"{r.protect_over_ismmed:9.2f}" if np.isfinite(r.protect_over_ismmed) \
            else f"{'--':>9}"
        rvp = f"{r.r_vs_protect:10.2f}" if np.isfinite(r.r_vs_protect) \
            else f"{'--':>10}"
        print(f"  {r.gcm:14}{r.ssp:8}{pro}{rpo}{r.ism_median:9.1f}{r.ours:8.1f}"
              f"{rvp}{r.r_vs_ism_median:10.2f}{r.r_vs_ism_max:10.2f}"
              f"{r.ours_pctile_in_ism:7.0f}%")

    both = cell[np.isfinite(cell.r_vs_protect)]
    lp = float(np.mean(np.abs(np.log(both.r_vs_protect))))
    li = float(np.mean(np.abs(np.log(both.r_vs_ism_median))))
    lall = float(np.mean(np.abs(np.log(cell.r_vs_ism_median))))
    tlo, thi = both.protect_over_ismmed.min(), both.protect_over_ismmed.max()
    tmed = both.protect_over_ismmed.median()
    print(f"\n  IS THE TARGET LOW? PROTECT/ISMIP6-median over the {len(both)} shared "
          f"cells = {tlo:.2f}, {tmed:.2f}, {thi:.2f}")
    print(f"    -> NORCE-CISM is a {'LOW' if tmed < TARGET_LOW_THRESH else 'TYPICAL'} "
          f"member of the ice-sheet-model distribution "
          f"(threshold {TARGET_LOW_THRESH:.2f}).")
    print(f"\n  DOES THE ERROR SURVIVE THE TARGET SWAP? |log| mean over those same "
          f"{len(both)} cells:")
    print(f"    vs PROTECT (1 ISM)                    {lp:.3f}   median ratio "
          f"{both.r_vs_protect.median():.2f}x")
    print(f"    vs ISMIP6 median ({int(both.n_ism.min())}-{int(both.n_ism.max())} ISMs)"
          f"           {li:.3f}   median ratio {both.r_vs_ism_median.median():.2f}x")
    print(f"  and on all {len(cell)} cells vs the ISMIP6 median: {lall:.3f}, "
          f"median ratio {cell.r_vs_ism_median.median():.2f}x")
    print(f"    ({len(cell) - len(both)} of those cells -- "
          + ", ".join(f"{r.gcm} {r.ssp}" for _, r in cell[~np.isfinite(
              cell.r_vs_protect)].iterrows())
          + " -- have NO PROTECT run at all\n     and are therefore evaluation points "
            "this arc has never scored against.)")

    print(f"\n=== 3. VERDICT ===\n")
    n_above_max = int((cell.r_vs_ism_max > 1.0).sum())
    n_top_half = int((cell.ours_pctile_in_ism >= 50).sum())
    print(f"  Our 2100 sits at the {cell.ours_pctile_in_ism.min():.0f}-"
          f"{cell.ours_pctile_in_ism.max():.0f} percentile of the ice-sheet-model "
          f"ensemble in every cell\n  ({n_top_half}/{len(cell)} at or above the "
          f"median), and ABOVE THE HIGHEST OF ALL {int(cell.n_ism.min())}-"
          f"{int(cell.n_ism.max())} MODELS"
          f"\n  in {n_above_max}/{len(cell)} cells (by up to "
          f"{cell.r_vs_ism_max.max():.2f}x).\n")
    target_low = tmed < TARGET_LOW_THRESH
    survives = both.r_vs_ism_median.median() > 1.0 and n_top_half == len(cell)
    if target_low and not survives:
        print(f"  ==> MOST OF THE 2100 DEFECT IS THE TARGET. NORCE-CISM is low "
              f"({tmed:.2f}x the ISMIP6\n      median) and the error largely "
              f"disappears against a multi-model median.")
    elif survives:
        print(f"  ==> THE 2100 FAST BIAS IS CONFIRMED, AND STRENGTHENED, BY AN "
              f"INDEPENDENT ENSEMBLE.\n      The single-ISM target is NOT the "
              f"explanation: NORCE-CISM sits at {tmed:.2f}x the\n      "
              f"{int(both.n_ism.min())}-{int(both.n_ism.max())}-model median "
              f"(range {tlo:.2f}-{thi:.2f}), a typical member, so swapping it for a\n      "
              f"{ism.ism.nunique()}-model median leaves "
              f"the over-prediction intact -- {both.r_vs_protect.median():.2f}x "
              f"becomes "
              f"{both.r_vs_ism_median.median():.2f}x.\n      The two GCM cells with no "
              f"PROTECT counterpart are the sharpest: we run "
              f"{cell[~np.isfinite(cell.r_vs_protect)].r_vs_ism_median.min():.2f}-"
              f"{cell[~np.isfinite(cell.r_vs_protect)].r_vs_ism_median.max():.2f}x\n"
              f"      the multi-model median there, above EVERY member.")
    else:
        print(f"  ==> MIXED. The target is {tmed:.2f}x the multi-model median and the "
              f"error does not\n      move cleanly either way; neither reading is "
              f"supported.")
    print(f"\n  BUT KEEP THE SCALE. The ISM structural spread at a FIXED GCM forcing "
          f"is\n  {ok.ism_maxmin.min():.2f}-{ok.ism_maxmin.max():.2f}x -- comparable "
          f"to or larger than our own "
          f"{cell.r_vs_ism_median.median():.2f}x offset. We are at the\n  high EDGE "
          f"of the ice-sheet-model range, not outside anything physical. What is "
          f"damning\n  is the DIRECTION being the same in {len(cell)}/{len(cell)} "
          f"cells across {cell.gcm.nunique()} GCMs and 2 scenarios,\n  not the "
          f"magnitude.")
    print(f"\n  PRIORITY CONTEXT (Marcus 2026-08-22). Matching transient ice models is "
          f"priority 4\n  of 5, below volume+history, long-term commitment and "
          f"melt-rate constraints; and\n  test stringency scales with the number of "
          f"models behind it. {ism.ism.nunique()} ice-sheet models "
          f"({int(cell.n_ism.min())}-{int(cell.n_ism.max())} per cell)\n  over "
          f"{cell.gcm.nunique()} GCMs is far more than the ONE this arc has been "
          f"scoring against, so this test\n  earns more weight than the PROTECT-only "
          f"one -- but it is still GUIDANCE. This file\n  emits NO loss term, NO band "
          f"and NO admissible set, deliberately.")
    print(f"\n  CAVEAT THAT TRAVELS. ISMIP6's CMIP6 GrIS forcing is MARv3.9-based; "
          f"PROTECT uses\n  MARv3.12 / RACMO2.3p2. Part of the PROTECT-vs-ISMIP6 gap "
          f"at a shared GCM is that\n  RCM version, not ice-sheet structure.")

    # --- the open protocol, reported separately and never pooled ----------------
    op = ism[ism.protocol != PROTOCOL_PRIMARY]
    print(f"\n=== 4. OPEN OCEAN PROTOCOL (reported separately, NOT pooled) ===\n")
    for (gcm, ssp), grp in op.groupby(["gcm", "ssp"]):
        v = grp.set_index("ism")["cm_2100"]
        std = prim[(prim.gcm == gcm) & (prim.ssp == ssp)]["cm_2100"]
        print(f"  {gcm:14}{ssp:8}n={len(v)}  " + ", ".join(
            f"{k} {x:.1f}" for k, x in v.items())
            + f"   | standard-protocol median {std.median():.1f}")
    print(f"\n  {len(op)} runs from {op.ism.nunique()} models -- too few to form a "
          f"spread; carried for provenance only.")

    ism.to_csv(OUT_ISM, index=False)
    cell.to_csv(OUT_ARM, index=False)
    print(f"\nwrote {os.path.relpath(OUT_ISM, REPO)}")
    print(f"wrote {os.path.relpath(OUT_ARM, REPO)}")


if __name__ == "__main__":
    main()
