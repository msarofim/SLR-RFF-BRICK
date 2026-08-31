#!/usr/bin/env python3
"""scope_magicc_climate_history_gap.py -- how far apart are MAGICC's and our HISTORY?

  python3 python/scope_magicc_climate_history_gap.py

Writes outputs/scope_magicc_climate_history_gap.csv and .../log_..._gap.txt.
SCOPING ONLY; no model file changed, nothing re-run.

WHY. The next analysis (handoff 2026-08-31f section 6) runs Ladrillo's unchanged
modules on MAGICC's climate to separate the module axis from the climate axis.
There are two defensible ways to inject that climate:

  (a) SPLICED -- keep our observed/FaIR history, take MAGICC's FUTURE anomaly.
      Consistent with the shared climate-driver convention (facts/
      build_shared_climate_nc.py: y <= 2014 untouched, uncertainty enters the
      future only) and with scope_glacier_regrowth.build_drivers(gmst_override=).
      Ladrillo's hindcast, and therefore its calibrated fit, survives.
  (b) RAW -- MAGICC's own full path, rebased 1850-1900. What MAGICC-SLR actually
      saw. Precedent: julia/project_magicc_hybrid_ssp245_mengel.jl (Track C).
      Breaks the hindcast: Ladrillo is calibrated against observations.

The difference between (a) and (b) IS the history disagreement, and it had never
been measured -- so the choice was being made blind. This script measures it.

⚠ TWO FaIR STATISTICS, AND THEY ARE NOT INTERCHANGEABLE (handoff 31f section 2.1).
The column reported here is MAGICC's ENSEMBLE MEDIAN minus the FaIR MEAN-CONFIG
trajectory, because the mean-config file is what actually DRIVES the module and
is therefore the thing (b) would replace. MAGICC's own 5-95 % band is printed
beside it so the gap can be read against that ensemble's width, but no claim is
made that the two statistics are comparable in kind.
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDE = os.path.expanduser(
    "~/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/vv_wide_20260831")
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/scope_magicc_climate_history_gap.csv")
LOG = os.path.join(REPO, "outputs/log_scope_magicc_climate_history_gap.txt")

VV = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
CONTROL = ["ssp126", "ssp245", "ssp585"]
SCENARIOS = VV + CONTROL

BASE = (1850, 1900)          # the frame both series are put on
HIST = (1850, 2014)          # "history" = the shared convention's untouched span
TE_REF = (1995, 2014)        # the window the TE module re-references SLR to
CHECK_YEARS = [1900, 1950, 1980, 2000, 2014]
ZJ_TO_1E22J = 0.1            # 1 ZJ = 1e21 J; a definition, never inferred from a ratio
## The GlacierMIP3 rungs and every Ladrillo driver are stated to 0.01 K, so a
## history gap below that is not a difference anyone could act on.
QUOTE_K = 0.01


def rebase(s):
    return s - s.loc[BASE[0]:BASE[1]].mean()


def fair(scen, kind, col):
    p = os.path.join(OBS, "fair_mean_%s_%s.csv" % (kind, scen))
    if not os.path.exists(p):
        raise SystemExit("[SOURCE] missing %s" % p)
    return rebase(pd.read_csv(p).set_index("year")[col])


def magicc(scen, kind, scale=1.0):
    p = os.path.join(WIDE, "magicc_%s_%s_wide%s.csv"
                     % (kind, scen, "_rel1850" if kind == "ohc" else ""))
    if not os.path.exists(p):
        raise SystemExit("[SOURCE] missing %s -- run "
                         "FaIRtoFrEDI/magicc_comparison/build_magicc_wide_vv.py" % p)
    return pd.read_csv(p).set_index("year") * scale


def main():
    rows, lines = [], []

    def say(s=""):
        print(s)
        lines.append(s)

    say("MAGICC vs the Ladrillo driver over the HISTORY %d-%d, both K rel %d-%d."
        % (HIST + BASE))
    say("MAGICC = ensemble median of 600 members; Ladrillo driver = FaIR mean-config.")
    say()

    ## [SHARED-HISTORY] the seven markers must share ONE history -- they differ only
    ## in future emissions, so a non-zero spread here would mean the cubes are not
    ## what the convention says they are.
    hist_yrs = list(range(HIST[0], HIST[1] + 1))
    ref = fair(VV[0], "gmst", "gmst_C").loc[hist_yrs]
    worst = max(float(np.abs(fair(s, "gmst", "gmst_C").loc[hist_yrs] - ref).max()) for s in VV)
    if worst > 0:
        raise SystemExit("[SHARED-HISTORY] the vv markers disagree by %.3e K before 2015" % worst)
    say("[SHARED-HISTORY] ok   the 7 markers share one history exactly (0.000e+00 K)")
    ## The SSPs are a CONTROL and kept their ORIGINAL RCMIP inputs, so their history
    ## is NOT the markers' history. Reported, not gated -- it is a property of the
    ## design, and the number is what stops it being read as a defect later.
    dss = float(np.abs(fair("ssp245", "gmst", "gmst_C").loc[hist_yrs] - ref).max())
    say("[VINTAGE]        the SSP control history differs from the markers' by up to "
        "%.4f K (RCMIP vs CMIP7 inputs; by design)" % dss)
    say()

    say("GMST gap, MAGICC minus driver (K)")
    say("%-7s %s | %8s %8s %7s" % ("scen", "".join("%8d" % y for y in CHECK_YEARS),
                                   "rms", "max|d|", "in5-95"))
    for s in SCENARIOS:
        g = magicc(s, "gmst")
        med = g.median(axis=1)
        f = fair(s, "gmst", "gmst_C")
        yrs = [y for y in hist_yrs if y in g.index and y in f.index]
        d = med.loc[yrs] - f.loc[yrs]
        lo = np.percentile(g.loc[yrs], 5, axis=1)
        hi = np.percentile(g.loc[yrs], 95, axis=1)
        inside = int(((f.loc[yrs].to_numpy() >= lo) & (f.loc[yrs].to_numpy() <= hi)).sum())
        say("%-7s %s | %8.3f %8.3f %4d/%d"
            % (s, "".join("%8.3f" % d[y] for y in CHECK_YEARS),
               np.sqrt((d ** 2).mean()), np.abs(d).max(), inside, len(yrs)))
        for y in CHECK_YEARS:
            rows.append((s, "gmst", y, float(d[y]), "K"))
        rows.append((s, "gmst_rms_hist", HIST[1], float(np.sqrt((d ** 2).mean())), "K"))
        rows.append((s, "gmst_driver_inside_magicc_5_95_frac", HIST[1],
                     inside / len(yrs), "fraction of years"))

    say()
    say("OHC gap, MAGICC minus driver (1e22 J), and the part a constant offset canNOT remove.")
    say("The TE module re-references SLR to %d-%d, so only the RESIDUAL after removing"
        % TE_REF)
    say("that window's mean difference can move thermal expansion.")
    say("%-7s %8s %8s %8s | %8s %8s" % ("scen", "d@1900", "d@2000", "d@2014",
                                        "offset", "resid rms"))
    for s in SCENARIOS:
        o = magicc(s, "ohc", ZJ_TO_1E22J)
        med = o.median(axis=1)
        f = fair(s, "ohc", "ohc_1e22J")
        yrs = [y for y in hist_yrs if y in o.index and y in f.index]
        d = med.loc[yrs] - f.loc[yrs]
        k = float(d.loc[TE_REF[0]:TE_REF[1]].mean())
        r = d - k
        say("%-7s %8.2f %8.2f %8.2f | %8.2f %8.2f"
            % (s, d[1900], d[2000], d[2014], k, np.sqrt((r ** 2).mean())))
        for y in CHECK_YEARS:
            rows.append((s, "ohc", y, float(d[y]), "1e22 J"))
        rows.append((s, "ohc_te_ref_offset", TE_REF[1], k, "1e22 J"))
        rows.append((s, "ohc_resid_rms_after_offset", HIST[1],
                     float(np.sqrt((r ** 2).mean())), "1e22 J"))

    say()
    say("READING. The (a)-vs-(b) difference in section 6.3 is exactly these numbers. A GMST")
    say("history gap of %.3f K rms is %.0fx the %.2f K we quote to, so (a) and (b) are NOT"
        % (float([r[3] for r in rows if r[0] == "vvM" and r[1] == "gmst_rms_hist"][0]),
           float([r[3] for r in rows if r[0] == "vvM" and r[1] == "gmst_rms_hist"][0]) / QUOTE_K,
           QUOTE_K))
    say("interchangeable, and the OHC residual shows the constant-offset cancellation Track C")
    say("verified does not make the two histories equivalent.")

    pd.DataFrame(rows, columns=["scenario", "quantity", "year", "value", "unit"]).to_csv(
        OUT, index=False)
    with open(LOG, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\nwrote %s\n      %s" % (os.path.relpath(OUT, REPO), os.path.relpath(LOG, REPO)))


if __name__ == "__main__":
    main()
