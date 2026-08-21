#!/usr/bin/env python3
"""
build_protect_cool_forcing.py — the GMST paths that FORCED the PROTECT-Greenland
COOL-scenario long runs (ssp126 r2300/x2300, ssp245 r2300), as Ladrillo drivers.

WHY (2026-08-21h, notes/handoff_2026-08-21e ... §3.1)
  The shape scorecard (scope_gis_ridge_vs_protect.py) runs our model on THEIR
  forcing -- the only like-for-like comparison in the arc -- but it covers ssp585
  ARMS ONLY. Its verdict (interior optimum k = 2-3) therefore sits in direct
  opposition to the cool scenarios' 2300 LEVEL bands (k <= 1.0) with no single
  scorecard holding both. Those two constraints have never been evaluated against
  each other at matched forcing, and that is exactly the question `gamma` has to
  answer. This script builds the three missing drivers.

  Marcus's standing instruction, 2026-08-21: make every comparison as like-for-like
  as possible, forcing trajectory first. [[like_for_like_forcing]]

CONSTRUCTION -- identical to the two ssp585 builders, deliberately
  r2300  the GCM's own scenario through 2100, then HELD at its 2081-2100 mean
         (Goelzer 2025's own definition, not an approximation of it).
  x2300  the natural CMIP6 extension. Available at ssp126 because CESM2-WACCM's
         ssp126 store runs to 2299 and the standard reduce already pulled it --
         [[pangeo_cmip6_no_ext]] is about the ssp585 stores, not extensions in
         general. Its final year is held to 2300 and FLAGGED.
  Both n-weighted by the runs table, never hardcoded, and both emitted in the same
  two arms the ssp585 builders emit:
    `spliced`  our own GMST through 2014, then the GCM anomaly re-referenced to its
               1995-2014 mean and added to ours. Changes ONLY the future path and
               leaves the hindcast anchor identical to the shipped run. THIS is the
               arm the model is driven with.
    `raw`      the GCM path on its own 1850-1900 baseline throughout, carried as the
               sensitivity on the splice choice.

TWO GATES, because these drivers have NO Julia counterpart to check against
  The ssp585 arms are gated by diag_protect_forcing_matched; there is no such run
  for the cool arms, so the NEW code paths are gated directly instead:

  GATE A (splice arithmetic)  re-splice the PREBUILT ssp585 `gmst_raw` columns with
      this file's own splice code and require the result to reproduce their
      committed `gmst_spliced` columns. If the arithmetic here differs from the
      arithmetic that produced the published ssp585 drivers, this fails.
  GATE B (hold construction)  `gcm_path(model, "ssp585", "r2300")` must reproduce
      outputs/cmip6_gsat_r2300_gcms.csv for every GCM that is cached locally
      (CESM2, IPSL-CM6A-LR, MPI-ESM1-2-HR -- UKESM1-0-LL and CNRM-ESM2-1 are not in
      data/cmip6_gis, which is why ssp585 is READ rather than rebuilt).

  Together they cover both halves of what is new: how a per-GCM path is built, and
  how the composite is spliced onto ours. Neither is a proxy for the other.

WRITES outputs/protect_{ssp}_{family}_forcing_gmst.csv  (3 files)
  python3 python/build_protect_cool_forcing.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

from scope_gis_cool_band_forcing import (  # noqa: E402
    ALIAS, BASE_HI, BASE_LO, DROP, HOLD_HI, HOLD_LO, RUNS, SMOOTH, Y0, Y1,
    gcm_path,
)

OURS_FMT = os.path.join(REPO, "data/observations/fair_mean_gmst_{ssp}.csv")
OUT_FMT = os.path.join(REPO, "outputs/protect_{ssp}_{fam}_forcing_gmst.csv")
PREBUILT_FMT = os.path.join(REPO, "outputs/protect_{fam}_forcing_gmst.csv")
GCM_REF = os.path.join(REPO, "outputs/cmip6_gsat_r2300_gcms.csv")

# --- named constants ---------------------------------------------------------
SPLICE_YEAR = 2014                   # last year from our own path in the spliced arm
REF0, REF1 = 1995, 2014              # splice offset window -- multi-year, never one
COOL_ARMS = [("ssp126", "SSP1-2.6", "r2300"), ("ssp126", "SSP1-2.6", "x2300"),
             ("ssp245", "SSP2-4.5", "r2300")]
GATE_A_TOL = 1e-10                   # arithmetic identity, not a tolerance on physics
GATE_B_TOL = 1e-9
REPORT_YEARS = (2050, 2100, 2150, 2200, 2300)


def splice(ours, gcm):
    """Our path through SPLICE_YEAR, then the GCM re-referenced on REF0-REF1.
    The ONE definition; GATE A checks it against the published ssp585 drivers."""
    off = ours.loc[REF0:REF1].mean() - gcm.loc[REF0:REF1].mean()
    return pd.concat([ours.loc[:SPLICE_YEAR], gcm.loc[SPLICE_YEAR + 1:] + off]), float(off)


def gate_a():
    ours585 = pd.read_csv(OURS_FMT.format(ssp="ssp585")).set_index("year").gmst_C.loc[Y0:Y1]
    worst = 0.0
    for fam in ("r2300", "x2300"):
        pb = pd.read_csv(PREBUILT_FMT.format(fam=fam)).set_index("year")
        got, off = splice(ours585, pb.gmst_raw.loc[Y0:Y1])
        d = float(np.max(np.abs(got - pb.gmst_spliced.loc[Y0:Y1])))
        worst = max(worst, d)
        print(f"  GATE A {fam}: re-spliced vs published, max |diff| {d:.3e} "
              f"(offset {off:+.4f} C)")
    if worst >= GATE_A_TOL:
        sys.exit(f"GATE A FAILED: {worst:.3e} >= {GATE_A_TOL}. The splice here is not "
                 f"the splice that produced the published ssp585 drivers.")
    print(f"  GATE A PASSED, worst {worst:.3e}")


def gate_b():
    ref = pd.read_csv(GCM_REF)
    worst, checked, skipped = 0.0, [], []
    for gcm in sorted(set(ref.gcm)):
        model = ALIAS.get(gcm, gcm)
        if not os.path.exists(os.path.join(REPO, f"data/cmip6_gis/tas_series_gis_{model}.csv")):
            skipped.append(f"{gcm}->{model}")
            continue
        got, _ = gcm_path(model, "ssp585", "r2300")
        want = ref[ref.gcm == gcm].set_index("year").gsat_anom_C.loc[Y0:Y1]
        d = float(np.max(np.abs(got - want)))
        worst = max(worst, d)
        checked.append(f"{gcm} {d:.2e}")
    print(f"  GATE B hold construction vs cmip6_gsat_r2300_gcms.csv: " + ", ".join(checked))
    print(f"    not cached, NOT checked (and not silently passed): "
          + (", ".join(skipped) if skipped else "none"))
    if worst >= GATE_B_TOL:
        sys.exit(f"GATE B FAILED: {worst:.3e} >= {GATE_B_TOL}.")
    print(f"  GATE B PASSED, worst {worst:.3e}\n")


def main():
    print("build_protect_cool_forcing — the three missing PROTECT drivers\n")
    gate_a()
    gate_b()

    runs = pd.read_csv(RUNS)
    L = runs[runs.long & runs.y2300.notna()].copy()
    L["fam"] = L.exp.str.extract(r"(r2300|x2300)")[0]
    L["gcm"] = L.exp.str.split("_").str[0]

    for ssp, lab, fam in COOL_ARMS:
        ours = pd.read_csv(OURS_FMT.format(ssp=ssp)).set_index("year").gmst_C.loc[Y0:Y1]
        assert ours.index.equals(pd.Index(range(Y0, Y1 + 1))), f"{ssp} driver has gaps"
        s = L[(L.ssp == lab) & (L.fam == fam)]
        w_all = s.gcm.value_counts()
        w = w_all.drop(labels=[g for g in DROP if g in w_all.index])
        paths, notes = {}, {}
        for g in w.index:
            paths[g], notes[g] = gcm_path(ALIAS.get(g, g), ssp, fam)
        gcm = sum(paths[g] * w[g] for g in w.index) / w.sum()
        spl, off = splice(ours, gcm)

        out = pd.DataFrame({"year": range(Y0, Y1 + 1)}).set_index("year")
        out["gmst_ours"], out["gmst_raw"], out["gmst_spliced"] = ours, gcm, spl
        for c in ("gmst_ours", "gmst_raw", "gmst_spliced"):
            out[f"{c}_{SMOOTH}yr"] = out[c].rolling(SMOOTH, center=True, min_periods=1).mean()
        out["n_runs"] = int(w.sum())
        out["weights"] = "|".join(f"{k}:{v}" for k, v in w.items())
        out["basis"] = (
            f"C vs {BASE_LO}-{BASE_HI}; "
            + (f"forcing HELD at each GCM's {HOLD_LO}-{HOLD_HI} mean from 2101 "
               f"(Goelzer 2025 r2300)" if fam == "r2300" else
               "natural CMIP6 extension (Goelzer 2025 x2300)")
            + f"; spliced = ours <={SPLICE_YEAR} re-ref on {REF0}-{REF1}")
        p = OUT_FMT.format(ssp=ssp, fam=fam)
        out.reset_index().to_csv(p, index=False)

        print(f"{lab} {fam}: n={int(w.sum())}, weights "
              + ", ".join(f"{k}:{v}" for k, v in w.items()) + f", splice offset {off:+.3f} C")
        for g in w.index:
            print(f"    {g:16} ({ALIAS.get(g, g):14}) {notes[g]}")
        print("    " + "".join(f"{y:>9}" for y in REPORT_YEARS))
        for nm, col in (("spliced", "gmst_spliced_11yr"), ("ours", "gmst_ours_11yr")):
            print("    " + "".join(f"{out.loc[y, col]:9.2f}" for y in REPORT_YEARS)
                  + f"   {nm} (K)")
        print(f"    wrote {os.path.relpath(p, REPO)}\n")


if __name__ == "__main__":
    main()
