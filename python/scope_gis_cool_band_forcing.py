#!/usr/bin/env python3
"""
scope_gis_cool_band_forcing.py — WHAT FORCING PRODUCED EACH BAND IN `LIT_2300_M`?

WHY THIS EXISTS (2026-08-21g, notes/handoff_2026-08-21d ... §2.1 step 1)
  Every Greenland scorecard in this repo scores 2300 against `LIT_2300_M`. Its
  ssp585 entry was traced 2026-08-21f to the PROTECT `x2300` family, forced to
  13.64 K at 2300 against our ssp585's 7.78 K -- i.e. the headline "SHORT by
  3.5-6.3x" is in part a comparison at two different forcings.

  The two COOL bands were never checked. They are labelled "stabilised" and
  "stabilised+ext" and their forcing LEVEL was unknown. That is the highest-value
  unknown in the repo right now, because the pre-flight's kill of k = 2-3 on the
  phi*Leq ridge (2026-08-21f) rests ENTIRELY on those two bands: ssp245 leaves its
  band at k = 1.5 and ssp126 at k = 2.0.

  THE FALSIFIER, STATED BEFORE RUNNING (handoff §2.1): if the literature's
  stabilised arms sit near OUR plateaus (ssp126 1.74 K, ssp245 3.15 K at 2300),
  Q1 stands as written and k <= 1.25 holds. If they sit HIGHER, the cool bands are
  scoring a hotter world than ours and k <= 1.25 loosens.

WHAT IS MEASURED
  The PROTECT-Greenland long runs at SSP1-2.6 and SSP2-4.5, split by forcing
  family exactly as the ssp585 arms were, with the n-weighted GSAT path each
  family was actually forced by, on this repo's GMST convention.

    r2300   the GCM's own scenario through 2100, then HELD at its 2081-2100 mean
            (Goelzer 2025: "the climate forcing from 2100 is held constant and
            repeated through 2300"). Needs NO post-2100 CMIP6 -- [[pangeo_cmip6_no_ext]].
    x2300   the natural CMIP6 extension. Available for ssp126 because CESM2-WACCM's
            ssp126 zarr store runs to 2299 and the standard reduce already pulled
            it; the ssp585 stores are the ones that stop at 2100.

  Both are compared to ours at MATCHED YEARS, and additionally on the TIME-INTEGRAL
  of warming over 2015-2300, because an ice sheet integrates forcing -- two paths
  agreeing at 2300 but differing over 200 yr are not the same forcing.

NOT MEASURED HERE
  Whether `LIT_2300_M`'s cool numbers are literally these runs' quantiles. The
  band is a hand transcription from TC 19:6887; this script measures the FAMILY it
  is labelled as, and prints our own extraction's quantiles beside it so the
  correspondence can be read off rather than assumed.

WRITES outputs/scope_gis_cool_band_forcing.csv     (per ssp x family, per year)
       outputs/scope_gis_cool_band_targets.csv     (the per-family SLR quantiles)
  python3 python/scope_gis_cool_band_forcing.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

GIS_DIR = os.path.join(REPO, "data/cmip6_gis")
RUNS = os.path.join(REPO, "outputs/protect_greenland_gis_runs.csv")
OURS_FMT = os.path.join(REPO, "data/observations/fair_mean_gmst_{ssp}.csv")
# The ssp585 arms were built 2026-08-21d/e and are the authority; this script READS
# them rather than re-deriving the kernel a fourth time ([[audit_live_paths]]). They
# also carry UKESM1-0-LL and CNRM-ESM2-1, which are NOT in data/cmip6_gis, so
# rebuilding ssp585 offline is not even possible.
PREBUILT = {("ssp585", "r2300"): os.path.join(REPO, "outputs/protect_r2300_forcing_gmst.csv"),
            ("ssp585", "x2300"): os.path.join(REPO, "outputs/protect_x2300_forcing_gmst.csv")}
OUT_F = os.path.join(REPO, "outputs/scope_gis_cool_band_forcing.csv")
OUT_T = os.path.join(REPO, "outputs/scope_gis_cool_band_targets.csv")

# --- named constants; every label below derives from these -------------------
Y0, Y1 = 1850, 2300
BASE_LO, BASE_HI = 1850, 1900        # 51-yr baseline, same as both ssp585 reducers
HOLD_LO, HOLD_HI = 2081, 2100        # the 20-yr level r2300 repeats after 2100
SMOOTH = 11
REPORT_YEARS = (2100, 2150, 2200, 2300)
INTEG_LO, INTEG_HI = 2015, 2300      # the PROTECT series start end-2015
FAMILIES = ("r2300", "x2300")
# The two bands under test, and the ssp585 one as the VERIFIED control.
SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
# Mirrors scope_gis_leq_ridge_vs_literature.LIT_2300_M -- imported, not retyped.
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
LIT_2300_M, LIT_2300_NOTE = ridge.LIT_2300_M, ridge.LIT_2300_NOTE
ALIAS = {"CESM2-Leo": "CESM2", "UKESM1-0-LL-Robin": "UKESM1-0-LL"}
DROP = {"ACCESS1.3"}                 # CMIP5, dropped from BOTH sides (r2300 ssp585)
QUANTS = (0.05, 0.17, 0.50, 0.83, 0.95)


def gcm_path(model, ssp, family):
    """GSAT anomaly vs BASE_LO-BASE_HI, 1850-Y1, on this repo's convention.
    Returns (series, note). r2300 holds the HOLD window's mean from 2101;
    x2300 uses the model's own extension and holds only its final year, flagged."""
    f = os.path.join(GIS_DIR, f"tas_series_gis_{model}.csv")
    if not os.path.exists(f):
        sys.exit(f"{model}: no cached tas series -- this script is offline by design")
    d = pd.read_csv(f)
    d = d[d.member == d.member.iloc[0]]
    hist = d[d.scenario == "historical"].set_index("year").tas_global
    scen = d[d.scenario == ssp].set_index("year").tas_global
    base = hist.loc[BASE_LO:BASE_HI]
    if len(base) < (BASE_HI - BASE_LO + 1):
        sys.exit(f"{model}: baseline window incomplete ({len(base)} yr)")
    anom = pd.concat([hist, scen]).sort_index() - base.mean()
    full = anom.reindex(range(Y0, Y1 + 1))
    if family == "r2300":
        hold = float(scen.loc[HOLD_LO:HOLD_HI].mean() - base.mean())
        full.loc[2101:] = hold
        note = f"HELD at {hold:.2f} K from 2101"
    else:
        last = int(scen.index.max())
        if last < 2101:
            sys.exit(f"{model} {ssp}: no extension past {last} -- x2300 not buildable")
        if last < Y1:
            full.loc[last + 1:] = float(full.loc[last])
            note = f"extension to {last}, held to {Y1} (flat, {float(full.loc[last]):.2f} K)"
        else:
            note = f"extension to {last}"
    if full.isna().any():
        sys.exit(f"{model} {ssp}: gaps inside {Y0}-{Y1} -- refusing to fill")
    return full, note


def main():
    runs = pd.read_csv(RUNS)
    L = runs[runs.long & runs.y2300.notna()].copy()
    L["fam"] = L.exp.str.extract(r"(r2300|x2300)")[0]
    L["gcm"] = L.exp.str.split("_").str[0]

    print(f"PROTECT-Greenland long runs by scenario x forcing family "
          f"(n={len(L)}), and the GSAT each family was forced by.\n"
          f"GSAT: {SMOOTH}-yr centred, C vs {BASE_LO}-{BASE_HI}, n-weighted over the "
          f"family's own GCMs.\nOURS: data/observations/fair_mean_gmst_<ssp>.csv, "
          f"same smoothing and baseline.\n")

    rows, trows = [], []
    for ssp, lab in SSPS:
        ours = pd.read_csv(OURS_FMT.format(ssp=ssp)).set_index("year").gmst_C.loc[Y0:Y1]
        ours_s = ours.rolling(SMOOTH, center=True, min_periods=1).mean()
        sub = L[L.ssp == lab]
        print(f"=== {lab} | LIT_2300_M {LIT_2300_M[lab][0]:.3f}-{LIT_2300_M[lab][1]:.3f} m "
              f"[{LIT_2300_NOTE[lab]}] ===")
        for fam in FAMILIES:
            s = sub[sub.fam == fam]
            if s.empty:
                print(f"  {fam}: no long runs at {lab}")
                continue
            w_all = s.gcm.value_counts()
            w = w_all.drop(labels=[g for g in DROP if g in w_all.index])
            if w.empty:
                print(f"  {fam}: all {int(w_all.sum())} runs dropped ({sorted(DROP)})")
                continue
            ## The SLR quantiles must be over the SAME runs the forcing is weighted
            ## over, or the two sides of the comparison are different ensembles.
            s = s[s.gcm.isin(w.index)]
            notes = {}
            if (ssp, fam) in PREBUILT:
                pb = pd.read_csv(PREBUILT[(ssp, fam)]).set_index("year")
                gcm, gcm_s = pb.gmst_raw.loc[Y0:Y1], pb.gmst_raw_11yr.loc[Y0:Y1]
                notes["(prebuilt)"] = (f"{os.path.basename(PREBUILT[(ssp, fam)])}: "
                                       f"{pb.weights.iloc[0]} | spliced arm "
                                       f"{pb.gmst_spliced_11yr.loc[2300]:.2f} K at 2300")
            else:
                paths = {}
                for g in w.index:
                    paths[g], notes[g] = gcm_path(ALIAS.get(g, g), ssp, fam)
                gcm = sum(paths[g] * w[g] for g in w.index) / w.sum()
                gcm_s = gcm.rolling(SMOOTH, center=True, min_periods=1).mean()

            drop_n = int(w_all.sum() - w.sum())
            print(f"  {fam}: n={int(w.sum())}" + (f" ({drop_n} dropped)" if drop_n else "")
                  + ", weights " + ", ".join(f"{k}:{v}" for k, v in w.items()))
            for g, n in notes.items():
                print(f"      {g:20} ({ALIAS.get(g, g):14}) {n}"
                      if g in w.index else f"      {n}")
            head = "      " + "".join(f"{y:>9}" for y in REPORT_YEARS)
            print(head)
            print("      " + "".join(f"{gcm_s.loc[y]:9.2f}" for y in REPORT_YEARS) + "   forcing (K)")
            print("      " + "".join(f"{ours_s.loc[y]:9.2f}" for y in REPORT_YEARS) + "   OURS (K)")
            print("      " + "".join(f"{gcm_s.loc[y] - ours_s.loc[y]:+9.2f}" for y in REPORT_YEARS)
                  + "   THEIRS - OURS")
            ig = float(gcm_s.loc[INTEG_LO:INTEG_HI].sum())
            io = float(ours_s.loc[INTEG_LO:INTEG_HI].sum())
            print(f"      integral {INTEG_LO}-{INTEG_HI}: theirs {ig:8.0f} K.yr | "
                  f"ours {io:8.0f} K.yr | ratio {ig / io:5.2f}x")

            q = s.y2300.quantile(QUANTS)
            print("      their SLR@2300 cm: " + "  ".join(
                f"p{int(p*100):02d} {q.loc[p]:6.1f}" for p in QUANTS))
            print()

            for y in range(Y0, Y1 + 1):
                rows.append({"ssp": ssp, "label": lab, "family": fam, "year": y,
                             "gmst_theirs": gcm.loc[y], "gmst_theirs_11yr": gcm_s.loc[y],
                             "gmst_ours": ours.loc[y], "gmst_ours_11yr": ours_s.loc[y],
                             "n_runs": int(w.sum()),
                             "weights": "|".join(f"{k}:{v}" for k, v in w.items())})
            trows.append({"ssp": ssp, "label": lab, "family": fam, "n_runs": int(w.sum()),
                          "n_dropped": drop_n,
                          "gmst_2300_theirs": float(gcm_s.loc[2300]),
                          "gmst_2300_ours": float(ours_s.loc[2300]),
                          "gmst_int_theirs_Kyr": ig, "gmst_int_ours_Kyr": io,
                          **{f"slr2300_p{int(p*100):02d}_cm": float(q.loc[p]) for p in QUANTS},
                          "lit_lo_m": LIT_2300_M[lab][0], "lit_hi_m": LIT_2300_M[lab][1],
                          "lit_note": LIT_2300_NOTE[lab],
                          "basis": (f"GSAT C vs {BASE_LO}-{BASE_HI}, {SMOOTH}-yr; SLR cm rel 2015; "
                                    f"r2300 held at {HOLD_LO}-{HOLD_HI}")})

    pd.DataFrame(rows).to_csv(OUT_F, index=False)
    t = pd.DataFrame(trows)
    t.to_csv(OUT_T, index=False)

    print("=== VERDICT ON THE FALSIFIER ===")
    for ssp, lab in SSPS:
        for _, r in t[t.label == lab].iterrows():
            d = r.gmst_2300_theirs - r.gmst_2300_ours
            v = ("MATCHED" if abs(d) < 0.25 else
                 f"THEIRS {'HOTTER' if d > 0 else 'COOLER'} by {abs(d):.2f} K "
                 f"({r.gmst_2300_theirs / r.gmst_2300_ours:.2f}x)")
            print(f"  {lab:9} {r.family}: {r.gmst_2300_theirs:5.2f} K vs ours "
                  f"{r.gmst_2300_ours:5.2f} K -> {v}")
    print(f"\nwrote {os.path.relpath(OUT_F, REPO)}, {os.path.relpath(OUT_T, REPO)}")


if __name__ == "__main__":
    main()
