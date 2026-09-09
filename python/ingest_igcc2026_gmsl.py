#!/usr/bin/env python3
"""
ingest_igcc2026_gmsl.py -- adopt the IGCC 2025-indicators GMSL release (Forster et al., ESSD 18,
3889-3933, 2026) as the canonical observed total-GMSL comparison for Ladrillo, replacing the
2024-indicators drop we have been plotting since May 2026.

⭐ THIS IS NOT AN EXTENSION BY ONE YEAR. Sect. 12 of the paper replaces the ENTIRE satellite
portion of the series from 1993 onward with a re-derived three-product ensemble (AVISO, NASA and
University of Colorado; NOAA dropped), re-downloaded Feb-Mar 2026 so that one set of corrections
applies across the whole altimetry record. So every altimetry-era value moves, not just 2025.

⚠⚠ THE PUBLISHED `std` IS A LEVEL UNCERTAINTY AND MOSTLY CANCELS UNDER RE-REFERENCING.
It is near-constant over the record (38.4-49.4 mm) and is NOT zero at 1901, so it is dominated by
a term common to every year -- which drops out when a consumer re-references the series to its own
window, as `plot_hindcast_components.py` does. The paper's own numbers settle it: the 1993-2025
DIFFERENCE has a very-likely half-width of 4.4 mm, against the ~90 mm you would get by propagating
+/-1.645*std across two years. That is a factor of 20. So:
  * the column is named `sigma_level_mm`, NOT `sigma_mm`, so a downstream plot cannot silently
    treat a level uncertainty as an uncertainty on a re-referenced anomaly;
  * the honest quantitative gate is the PERIOD-DIFFERENCE table (Table 11), which is already a
    re-referenced quantity and is emitted alongside as `igcc2026_gmsl_benchmarks.csv`.
IGCC publishes only mean and std -- no ensemble members -- so the correct re-referenced band
`sd(x_t - mean(x_window))` CANNOT be computed from this release. Say that rather than drawing a
band that looks defensible and is not.

⚠ The release ships NO `.metadata.yml` for sea level (the 2025 drop shipped six). The old drop's
yml files are therefore kept as the only machine-readable provenance and are NOT deleted.

  ~/climate-env/bin/python python/ingest_igcc2026_gmsl.py
  ... --mutate {shiftlevel,dropyear}
"""
import argparse
import hashlib
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data", "observations")

# --- the two releases; every label and message below derives from these ---------------------
NEW_TAG = "v2026.06.02"
OLD_TAG = "2cd2409"
NEW_CSV = os.path.join(OBS, "raw", "igcc2026", "data-2026.06.02", "data", "sea_level_rise",
                       "IGCC_GMSL_ensemble.csv")
OLD_CSV = os.path.join(OBS, "raw", "igcc2024", "ClimateIndicator-data-%s" % OLD_TAG, "data",
                       "sea_level_rise", "IGCC_GMSL_ensemble.csv")
PAPER = "Forster et al. 2026, ESSD 18, 3889-3933 (IGCC, 2025 indicators)"
PAPER_DOI = "10.5194/essd-18-3889-2026"
DATA_DOI = "10.5281/zenodo.20499280"
DATA_URL = "https://github.com/ClimateIndicator/data/archive/refs/tags/%s.zip" % NEW_TAG

OUT_SERIES = os.path.join(OBS, "igcc2026_gmsl_annual.csv")
OUT_BENCH = os.path.join(OBS, "igcc2026_gmsl_benchmarks.csv")

# ⭐ TABLE 11, "This study" column. These are TYPED because the paper IS the source -- they are
# the external benchmark this ingest is checked against, not a quantity we could derive
# (`derived_must_mean_computed` forbids retyping a COMPUTED value, not a cited one). Total change
# in the annual mean over the period (mm) and the equivalent rate (mm/yr), with the very likely
# (90 %) range. End year 2025 throughout.
END_YEAR = 2025
TABLE11 = {
    1901: dict(delta=229.6, lo=178.6, hi=280.6, rate=1.85, rate_lo=1.44, rate_hi=2.26),
    1971: dict(delta=137.3, lo=101.4, hi=173.3, rate=2.54, rate_lo=1.88, rate_hi=3.21),
    1993: dict(delta=108.9, lo=104.5, hi=113.3, rate=3.40, rate_lo=3.26, rate_hi=3.54),
    2006: dict(delta=69.7, lo=65.0, hi=74.4, rate=3.66, rate_lo=3.42, rate_hi=3.92),
}
# ⚠ THE BOUND IS THE PAPER'S OWN PRINTED PRECISION, not a tolerance chosen to pass. Table 11
# prints the totals to 0.1 mm, so half a unit in the last printed digit is the tightest agreement
# the comparison can express (`threshold_from_obs_or_law`).
DELTA_TOL = 0.05
# ⚠⚠ THE RATE IS **NOT** GATED, DELIBERATELY (`no_power_null`). Table 11's rate is defined as the
# total change divided by the number of years, so it is Δ/n on BOTH sides -- it carries no
# information about this file that the Δ gate has not already tested, and gating it only exposes
# the comparison to how the paper rendered a last digit. It does exactly that: the paper prints
# 3.66 mm/yr for 2006-2025 where its own Δ/n = 3.6684, which ROUNDS to 3.67. The other three rows
# round; this one is truncated. A 0.005 bound FAILED on that and would have sent me looking for a
# data discrepancy that does not exist. The rate is REPORTED below with that fact stated.
RATE_RENDER_TOL = 0.011      # one unit in the paper's last printed digit, for the report only
# Our Δ/n vs the paper's OWN Δ/n: both divide by the same integer, so this inherits DELTA_TOL
# divided by the shortest period. DERIVED, not typed.
RATE_TOL_D = DELTA_TOL / (END_YEAR - 2006)
# The splice check: the paper changes only the altimetry era, so pre-1993 the two releases must
# differ by a CONSTANT (the re-splice offset) and nothing else. Bound = the CSVs' own written
# precision, so this discriminates a real revision from float noise by many orders of magnitude.
SPLICE_YEAR = 1993
SPLICE_TOL = 1e-6

MUTATE = {"mode": ""}
GATES = []


def gate(name, key, value, ok, note=""):
    GATES.append(dict(gate=name, key=str(key), value=float(value),
                      verdict="PASS" if ok else "FAIL", note=note))
    return ok


def load(path):
    d = pd.read_csv(path)
    d["year"] = d.time.astype(int)
    return d.set_index("year")


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    # ⚠ MUTATION MODES. A gate that has never failed is not known to be a gate.
    #   shiftlevel -> adds 5 mm to the new series from 1994 on: [TABLE-11] must FAIL.
    #   dropyear   -> truncates at 2024: [COVERAGE] must FAIL.
    ap.add_argument("--mutate", default="", choices=["", "shiftlevel", "dropyear"])
    a = ap.parse_args()
    MUTATE["mode"] = a.mutate
    if a.mutate:
        print("⚠ MUTATION RUN (%s) -- nothing is written\n" % a.mutate)

    for f in (NEW_CSV, OLD_CSV):
        if not os.path.exists(f):
            raise SystemExit("missing %s" % os.path.relpath(f, REPO))
    new, old = load(NEW_CSV), load(OLD_CSV)
    if MUTATE["mode"] == "shiftlevel":
        new.loc[1994:, "mean"] = new.loc[1994:, "mean"] + 5.0
    if MUTATE["mode"] == "dropyear":
        new = new.loc[:2024]

    print("=" * 96)
    print("IGCC GMSL -- adopting %s (%s)" % (NEW_TAG, PAPER))
    print("  replaces %s; the ENTIRE altimetry era (>=%d) is re-derived, not just extended"
          % (OLD_TAG, SPLICE_YEAR))
    print("=" * 96)
    print("  new: %d-%d (n=%d)   old: %d-%d (n=%d)"
          % (new.index.min(), new.index.max(), len(new),
             old.index.min(), old.index.max(), len(old)))

    gate("COVERAGE", "end_year", new.index.max(), int(new.index.max()) == END_YEAR,
         "the release must reach the paper's end year")

    # ---- [TABLE-11] the provenance gate: this file IS the paper's "This study" column ------
    print("\n%s\n[TABLE-11] does the downloaded file reproduce the paper's own table?\n%s"
          % ("-" * 96, "-" * 96))
    print("  %-11s %10s %10s | %10s %10s" % ("period", "file Δmm", "paper Δmm",
                                             "file mm/yr", "paper mm/yr"))
    for y0, t in TABLE11.items():
        if y0 not in new.index or END_YEAR not in new.index:
            gate("TABLE-11", "%d-%d" % (y0, END_YEAR), np.nan, False, "year missing")
            continue
        delta = float(new.loc[END_YEAR, "mean"] - new.loc[y0, "mean"])
        rate = delta / (END_YEAR - y0)
        okd = abs(delta - t["delta"]) <= DELTA_TOL
        # REPORTED, not gated -- see RATE_RENDER_TOL. `render` says whether the paper's printed
        # rate is its own Δ/n rounded or truncated, so the one odd row is documented, not hidden.
        implied = t["delta"] / (END_YEAR - y0)
        render = ("rounded" if abs(round(implied, 2) - t["rate"]) < 1e-9 else
                  "TRUNCATED" if abs(int(implied * 100) / 100 - t["rate"]) < 1e-9 else "?")
        print("  %-11s %10.2f %10.1f | %10.4f %10.2f  (paper Δ/n = %.4f, printed %s)   %s"
              % ("%d-%d" % (y0, END_YEAR), delta, t["delta"], rate, t["rate"], implied, render,
                 "OK" if okd else "⛔ MISMATCH"))
        gate("TABLE-11", "%d_delta" % y0, abs(delta - t["delta"]), okd,
             "half a unit in the paper's last printed digit (%g mm)" % DELTA_TOL)
        # What CAN be tested about the rate is that our rate matches the paper's own Δ/n --
        # i.e. that we and they divide the same total by the same number of years.
        gate("RATE-CONSISTENT", "%d" % y0, abs(rate - implied), abs(rate - implied) <= RATE_TOL_D,
             "our Δ/n vs the paper's own Δ/n, NOT vs its printed last digit")

    # ---- [SPLICE] the tide-gauge era must be untouched apart from one constant offset ------
    j = new.join(old["mean"].rename("old"), how="inner")
    pre = (j["mean"] - j.old).loc[:SPLICE_YEAR - 1]
    resid = float((pre - pre.mean()).abs().max()) if len(pre) else np.nan
    gate("SPLICE", "pre%d_residual_mm" % SPLICE_YEAR, resid, bool(resid <= SPLICE_TOL),
         "pre-altimetry the two releases may differ only by the constant re-splice offset")
    post = (j["mean"] - j.old).loc[SPLICE_YEAR:]
    print("\n%s\nWHAT MOVED\n%s" % ("-" * 96, "-" * 96))
    print("  pre-%d : a UNIFORM %+.2f mm offset (residual %.1e mm) -- the tide-gauge record is "
          "untouched" % (SPLICE_YEAR, float(pre.mean()) if len(pre) else np.nan, resid))
    print("  %d-  : re-derived; max |change| %.2f mm at %d"
          % (SPLICE_YEAR, float(post.abs().max()), int(post.abs().idxmax())))
    # ⭐ What a hindcast figure ACTUALLY sees, because every consumer re-references first.
    for w0, w1 in ((1995, 2005), (1995, 2014)):
        a_ = j["mean"] - j["mean"].loc[w0:w1].mean()
        b_ = j.old - j.old.loc[w0:w1].mean()
        d_ = (a_ - b_).abs()
        print("  re-referenced to %d-%d (what the figure plots): max |new-old| = %.2f mm "
              "= %.3f cm, at %d" % (w0, w1, float(d_.max()), float(d_.max()) / 10,
                                    int(d_.idxmax())))

    # ---- the level-uncertainty warning, MEASURED rather than asserted ----------------------
    sig = float(new["std"].mean())
    prop = 1.645 * sig * np.sqrt(2)
    tightest = min((t["hi"] - t["lo"]) / 2 for t in TABLE11.values())
    print("\n%s\nWHY THE BAND IS NOT THE GATE\n%s" % ("-" * 96, "-" * 96))
    print("  published std is near-constant: %.1f-%.1f mm (mean %.1f), and is NOT 0 at %d"
          % (new["std"].min(), new["std"].max(), sig, new.index.min()))
    print("  propagating ±1.645σ across two years would give ±%.1f mm on a difference;" % prop)
    print("  the paper's own tightest difference interval is ±%.1f mm -- a factor of %.0f."
          % (tightest, prop / tightest))
    print("  ⇒ σ is a LEVEL uncertainty, common-mode, and largely cancels on re-referencing.")
    print("    Use the Table 11 benchmarks as the quantitative gate; the band is illustrative.")
    gate("SIGMA-IS-LEVEL", "propagated_vs_published_ratio", prop / tightest,
         bool(prop / tightest > 5),
         "REPORTED, not a pass/fail on the data: records that the published std cannot be the "
         "uncertainty on a re-referenced anomaly")

    # ---- gates ------------------------------------------------------------------------------
    print("\n%s\nGATES\n%s" % ("=" * 96, "=" * 96))
    g = pd.DataFrame(GATES)
    for name, sub in g.groupby("gate", sort=False):
        nf = int((sub.verdict == "FAIL").sum())
        worst = sub.loc[sub.value.abs().idxmax()]
        print("  [%-14s] %3d/%3d PASS   worst %-24s %.6g%s"
              % (name, len(sub) - nf, len(sub), worst.key, worst.value,
                 "" if nf == 0 else "   ⛔ %d FAIL" % nf))
    nfail = int((g.verdict == "FAIL").sum())
    print("  TOTAL %d/%d PASS%s" % (len(g) - nfail, len(g),
                                    "" if nfail == 0 else "   ⛔ %d FAIL" % nfail))
    if MUTATE["mode"]:
        return
    if nfail:
        raise SystemExit("\n⛔ gates FAILED -- nothing written")

    # ---- write ------------------------------------------------------------------------------
    prov = ("%s | data %s | %s | tag %s | md5 %s"
            % (PAPER, DATA_DOI, DATA_URL, NEW_TAG, md5(NEW_CSV)))
    ser = pd.DataFrame(dict(year=new.index, gmsl_mm=new["mean"].values,
                            sigma_level_mm=new["std"].values))
    ser["provenance"] = prov
    ser.to_csv(OUT_SERIES, index=False)

    rows = []
    for y0, t in TABLE11.items():
        rows.append(dict(start_year=y0, end_year=END_YEAR, delta_mm=t["delta"],
                         delta_lo_mm=t["lo"], delta_hi_mm=t["hi"], rate_mm_yr=t["rate"],
                         rate_lo_mm_yr=t["rate_lo"], rate_hi_mm_yr=t["rate_hi"],
                         interval="very likely (90%)", source="Table 11, This study column",
                         provenance=prov))
    pd.DataFrame(rows).to_csv(OUT_BENCH, index=False)
    print("\nwrote %s  (%d years)" % (os.path.relpath(OUT_SERIES, REPO), len(ser)))
    print("      %s  (%d benchmark periods)" % (os.path.relpath(OUT_BENCH, REPO), len(rows)))


if __name__ == "__main__":
    main()
