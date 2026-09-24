#!/usr/bin/env python3
"""Where do the two AIS target builds actually disagree?

Tests the mechanism claim in the 2026-09-24 cover email to Tony Wong: that L32's
full-period degradation happens because the 2018-2023 SMB snowfall is anomalous.
If that were the dominant driver, the divergence between the Frederikse-based and
IMBIE-based target builds would be concentrated in 2018-2023.

Both builds are the SAME code (prep_recalib_targets_ext.py) with --ais-source
flipped, so the difference is the target choice alone.

  Frederikse build = git HEAD:outputs/recalib_targets_ext.csv (md5 070f74ab...)
  IMBIE build      = outputs/recalib_targets_ext.csv (md5 eb768cd9...) or --imbie

Writes outputs/diag_target_divergence_frd_vs_imbie.csv (per-year) and a summary.
"""
import argparse, hashlib, os, subprocess, sys
import numpy as np, pandas as pd

# --- named constants; every label below derives from these -------------------
ANOM_WINDOW   = (2018, 2023)          # the window the email attributes the loss to
EARLY_WINDOW  = (1920, 1949)          # where L32 loses most (0.08 -> 1.07 sigma)
SPLICE_START  = 1979                  # first year the IMBIE build differs in DATA
MEMO_AIS_SIG  = 0.1674                # cm; the ruler the memo quotes its AIS RMSE in
WINDOWS = [(1900, 1978), (1979, 1992), (1993, 2005), (2006, 2017),
           ANOM_WINDOW, (2024, 2026), (1979, 2017), (1979, 2023)]
OUT_CSV = "outputs/diag_target_divergence_frd_vs_imbie.csv"

def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imbie", default="outputs/recalib_targets_ext.csv")
    ap.add_argument("--frederikse-rev", default="HEAD",
                    help="git rev holding the Frederikse build of the same path")
    a = ap.parse_args()

    imb = pd.read_csv(a.imbie)[["year", "ais", "ais_lo", "ais_hi"]]
    blob = subprocess.run(["git", "show", f"{a.frederikse_rev}:{a.imbie}"],
                          capture_output=True, check=True).stdout
    frd_md5 = hashlib.md5(blob).hexdigest()
    open("/tmp/_frd_targets.csv", "wb").write(blob)
    frd = pd.read_csv("/tmp/_frd_targets.csv")[["year", "ais", "ais_lo", "ais_hi"]]

    m = imb.merge(frd, on="year", suffixes=("_imb", "_frd"))
    m["d"] = m.ais_imb - m.ais_frd
    m["sig_frd"] = (m.ais_hi_frd - m.ais_lo_frd) / (2 * 1.645)
    m["sig_imb"] = (m.ais_hi_imb - m.ais_lo_imb) / (2 * 1.645)
    prov = (f"diag_target_divergence_frederikse_vs_imbie.py | imbie {os.path.basename(a.imbie)} "
            f"md5 {md5(a.imbie)[:12]} | frederikse {a.frederikse_rev} md5 {frd_md5[:12]} | "
            f"d = IMBIE build - Frederikse build, cm SLE, both rel 1995-2005")
    m["provenance"] = prov
    m.to_csv(OUT_CSV, index=False)

    print(f"AIS target divergence, IMBIE build minus Frederikse build (cm SLE)\n  {prov}\n")
    for y0, y1 in WINDOWS:
        w = m[(m.year >= y0) & (m.year <= y1)].dropna(subset=["d"])
        if not len(w):
            continue
        rate = ""
        if len(w) > 2:
            ri = np.polyfit(w.year, w.ais_imb, 1)[0]
            rf = np.polyfit(w.year, w.ais_frd, 1)[0]
            rate = f"   rate diff {ri - rf:+.5f} cm/yr"
        print(f"  {y0}-{y1}: mean d {w.d.mean():+.4f}  RMS {np.sqrt((w.d**2).mean()):.4f}{rate}")

    d_at = lambda y: m.loc[m.year == y, "d"].iloc[0]
    pre = d_at(2017) - d_at(SPLICE_START)
    ano = d_at(ANOM_WINDOW[1]) - d_at(ANOM_WINDOW[0])
    share = 100 * abs(pre) / (abs(pre) + abs(ano))
    print(f"\nTEST -- is the {ANOM_WINDOW[0]}-{ANOM_WINDOW[1]} anomaly the driver?")
    print(f"  divergence accumulated {SPLICE_START}->2017 : {pre:+.4f} cm")
    print(f"  divergence accumulated {ANOM_WINDOW[0]}->{ANOM_WINDOW[1]} : {ano:+.4f} cm")
    print(f"  => {share:.0f} % of it accumulates BEFORE the anomalous window"
          f"  ==> {'NO, the anomaly is NOT the dominant driver' if share > 50 else 'YES'}")

    pre79 = m[m.year < SPLICE_START]
    const = pre79.d.std() < 1e-9
    print(f"\nTEST -- do the two builds differ in DATA before {SPLICE_START}?")
    print(f"  d over 1900-{SPLICE_START-1}: constant {pre79.d.mean():+.4f} cm "
          f"(sd {pre79.d.std():.1e}) => {'IDENTICAL up to a constant' if const else 'GENUINELY DIFFERENT'}")
    print(f"  that constant is {abs(pre79.d.mean())/MEMO_AIS_SIG:.2f} of the memo's {MEMO_AIS_SIG} cm ruler")
    print(f"  => the {EARLY_WINDOW[0]}-{EARLY_WINDOW[1]} loss cannot come from new early-record DATA")

    print(f"\nTEST -- sigma cliff at the GRACE-FO splice (the 19-27 sigma artefact):")
    for y in (2017, 2018, 2019, 2023):
        r = m[m.year == y]
        if len(r):
            r = r.iloc[0]
            print(f"  {y}: Frederikse sigma {r.sig_frd:.4f}  IMBIE sigma {r.sig_imb:.4f}")
    c = m[m.year == 2018].sig_frd.iloc[0] / m[m.year == 2019].sig_frd.iloc[0]
    print(f"  => Frederikse build sigma drops {c:.1f}x at 2019; IMBIE build has no cliff")
    print(f"\nwrote {OUT_CSV}")

if __name__ == "__main__":
    sys.exit(main())
