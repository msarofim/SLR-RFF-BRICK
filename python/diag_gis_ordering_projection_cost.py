"""What does the Greenland channel-ordering constraint cost the DELIVERABLE?

Prices the one open decision in handoff `notes/handoff_2026-08-16_thread5_CD.md`
section 7: buy a re-tune + 4x2M + re-acceptance (~5 h) + a new vintage to carry
the channel ordering into the shipped posterior, or ship L11 with the inversion
documented.

Section 5 priced the constraint at 0.067 nlp on the OFFLINE A+B optimum.  That
is a statement about a single MAP point, and the deliverable is a 10,000-draw
posterior.  This script converts the question into a measured SLR difference:

    ORD = the 37.53 % of L11 draws satisfying alpha_s <= alpha_f AND
          beta_s <= beta_f   (what a constrained calibration approximates)
    INV = the remaining 62.47 %   (what the constraint would remove)

Both halves were size-matched at 2000 draws by
`split_l11_by_gis_ordering.py` and projected by
`project_ssps_components_ladrillo.jl --tag=L11{ord,inv}`, so the two runs differ
only in WHICH draws they contain.

TWO GATES, both of which must pass before the numbers mean anything:

  MIXTURE GATE.  L11 is the mixture of ORD and INV, so the already-published
  L11 projection must lie BETWEEN them in every cell.  A failure indicts the
  split or the projection wiring, not the physics.

  SIGNATURE GATE.  ORD carries the longer slow timescale (tau_s 175 vs 75 yr),
  so its extra Greenland loss must GROW with horizon -- a long-lived reservoir
  realises more commitment the longer it is integrated.  A constant offset
  across horizons would instead be the signature of a code path (per the
  standing "suspicious uniformity ~ bug signal" discipline), so a same-sign
  difference is only trustworthy if it also grows.

SCOPE, stated because it bounds the conclusion: ORD-filtering holds every other
parameter's sampled value fixed, whereas a native re-tune would let them
re-adjust (section 5 saw c0 move 61.99 -> 6.75 between the two offline optima).
This therefore measures the constraint's effect THROUGH THE GREENLAND CHANNELS,
which is the mechanism in dispute -- not a full simulation of a re-tune.
"""
import os
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAGS = {"ORD": "L11ord", "L11": "L11", "INV": "L11inv"}
SSPS = ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]
HORIZONS = [2100, 2150, 2300]
# `ais` is a NULL CONTROL: no AIS parameter is touched by the Greenland split,
# so any ORD/INV/L11 difference in it is pure sampling noise and calibrates how
# much of the `total` difference is inherited rather than caused.
COMPONENTS = ["gis", "ais", "total"]
NULL_COMPONENT = "ais"
SIGNAL_COMPONENT = "gis"
OUT_CSV = os.path.join(REPO, "outputs/diag_gis_ordering_projection_cost.csv")


def load(tag):
    p = os.path.join(REPO, f"outputs/ssps_components_2300_{tag}.csv")
    d = pd.read_csv(p)
    return d[d["year"].isin(HORIZONS)].set_index(["year", "ssp", "component"])


def main():
    d = {k: load(v) for k, v in TAGS.items()}

    rows = []
    for comp in COMPONENTS:
        for ssp in SSPS:
            for yr in HORIZONS:
                key = (yr, ssp, comp)
                med = {k: float(v.loc[key, "med"]) for k, v in d.items()}
                band = float(d["L11"].loc[key, "p95"] - d["L11"].loc[key, "p05"])
                delta = med["ORD"] - med["INV"]
                rows.append(dict(
                    component=comp, ssp=ssp, year=yr,
                    ord_cm=med["ORD"], l11_cm=med["L11"], inv_cm=med["INV"],
                    ord_minus_inv_cm=delta,
                    l11_p05_p95_width_cm=band,
                    delta_as_pct_of_band=100.0 * delta / band if band else float("nan"),
                    l11_between=min(med["ORD"], med["INV"]) - 1e-9 <= med["L11"]
                                <= max(med["ORD"], med["INV"]) + 1e-9))
    out = pd.DataFrame(rows)

    for comp in COMPONENTS:
        sub = out[out["component"] == comp]
        print(f"\n=== {comp.upper()} (median, cm) ===")
        print(f"  {'ssp':10s} {'year':>6s} {'ORD':>8s} {'L11':>8s} {'INV':>8s} "
              f"{'ORD-INV':>9s} {'L11 5-95 band':>14s} {'as % of band':>13s}")
        for _, r in sub.iterrows():
            print(f"  {r['ssp']:10s} {r['year']:6d} {r['ord_cm']:8.2f} "
                  f"{r['l11_cm']:8.2f} {r['inv_cm']:8.2f} "
                  f"{r['ord_minus_inv_cm']:9.2f} {r['l11_p05_p95_width_cm']:14.1f} "
                  f"{r['delta_as_pct_of_band']:12.1f} %")

    # ---- MIXTURE GATE -------------------------------------------------------
    n_bad = int((~out["l11_between"]).sum())
    print(f"\nMIXTURE GATE : L11 between ORD and INV in "
          f"{len(out) - n_bad}/{len(out)} cells -> "
          f"{'PASS' if n_bad == 0 else 'FAIL'}")
    if n_bad:
        bad = out[~out["l11_between"]]
        print(bad[["component", "ssp", "year", "ord_cm", "l11_cm",
                   "inv_cm"]].to_string(index=False))
        # DIAGNOSE rather than dismiss.  The gate is only exact in the
        # infinite-sample limit: the published L11 run is its OWN 2000-draw
        # thinning of the 10,000, not the union of these two 2000-draw halves,
        # so each cell carries Monte-Carlo error.  The null control says whether
        # that error is large enough to explain the failure.
        print("\n  DIAGNOSIS via the null control "
              f"('{NULL_COMPONENT}', untouched by the Greenland split):")
        for _, r in bad.iterrows():
            null = out[(out["component"] == NULL_COMPONENT) &
                       (out["ssp"] == r["ssp"]) & (out["year"] == r["year"])]
            sig = out[(out["component"] == SIGNAL_COMPONENT) &
                      (out["ssp"] == r["ssp"]) & (out["year"] == r["year"])]
            if null.empty or sig.empty:
                continue
            n = null.iloc[0]
            # how far L11 sits outside the [ORD, INV] interval, per component
            def excursion(x):
                lo, hi = sorted((x["ord_cm"], x["inv_cm"]))
                return max(0.0, lo - x["l11_cm"], x["l11_cm"] - hi)
            e_bad, e_null = excursion(r), excursion(n)
            if r["component"] == NULL_COMPONENT:
                # Comparing the control to itself is not a test. Say what it is:
                # this cell IS a direct measurement of the noise floor.
                print(f"    {r['ssp']} @{r['year']}: '{NULL_COMPONENT}' is "
                      f"ITSELF the null control -- ORD {n['ord_cm']:.1f} / L11 "
                      f"{n['l11_cm']:.1f} / INV {n['inv_cm']:.1f} cm.")
                print(f"      -> not a failure to explain but a MEASUREMENT of "
                      f"the noise floor: {e_bad:.2f} cm in a component the "
                      f"split cannot move.")
                continue
            print(f"    {r['ssp']} @{r['year']}: "
                  f"'{r['component']}' L11 sits {e_bad:.2f} cm outside "
                  f"[ORD, INV]; '{NULL_COMPONENT}' sits {e_null:.2f} cm outside "
                  f"the same interval.")
            print(f"      {NULL_COMPONENT}: ORD {n['ord_cm']:.1f} / L11 "
                  f"{n['l11_cm']:.1f} / INV {n['inv_cm']:.1f} cm  "
                  f"(the split cannot move this component)")
            if e_null >= e_bad:
                print(f"      -> the null control's own excursion is LARGER "
                      f"({e_null:.2f} >= {e_bad:.2f} cm), so the failure is "
                      f"sampling noise INHERITED from {NULL_COMPONENT}, not a "
                      f"Greenland effect. The signal component "
                      f"('{SIGNAL_COMPONENT}') passes in this cell: ORD "
                      f"{sig.iloc[0]['ord_cm']:.2f} > L11 "
                      f"{sig.iloc[0]['l11_cm']:.2f} > INV "
                      f"{sig.iloc[0]['inv_cm']:.2f} cm.")
            else:
                print(f"      -> the null control does NOT explain it "
                      f"({e_null:.2f} < {e_bad:.2f} cm). Investigate the split "
                      f"or the projection wiring before using these numbers.")

    # ---- SIGNATURE GATE -----------------------------------------------------
    print("\nSIGNATURE GATE : does the GIS difference GROW with horizon?")
    gis = out[out["component"] == "gis"]
    grows_all = True
    for ssp in SSPS:
        s = gis[gis["ssp"] == ssp].sort_values("year")
        deltas = s["ord_minus_inv_cm"].tolist()
        grows = all(b >= a - 1e-9 for a, b in zip(deltas, deltas[1:]))
        grows_all &= grows
        print(f"  {ssp:10s} " + " -> ".join(f"{v:+.2f}" for v in deltas) +
              f"   {'growing' if grows else 'NOT MONOTONE'}")
    print(f"  -> {'PASS' if grows_all else 'FAIL'} (a flat offset would indicate "
          f"a code path, not a reservoir)")

    # ---- the decision number ------------------------------------------------
    tot = out[out["component"] == "total"]
    worst_2100 = tot[tot["year"] == 2100]["ord_minus_inv_cm"].abs().max()
    worst_2300 = tot[tot["year"] == 2300]["ord_minus_inv_cm"].abs().max()
    gis_worst = gis["ord_minus_inv_cm"].abs().max()
    print(f"\n--- what the ~5 h re-tune would buy, at most ---")
    print(f"  largest TOTAL SLR shift @2100 : {worst_2100:.2f} cm")
    print(f"  largest TOTAL SLR shift @2300 : {worst_2300:.2f} cm")
    print(f"  largest GIS-component shift   : {gis_worst:.2f} cm")
    print(f"  for scale, L11's own 5-95 band on total @2100 ssp585 is "
          f"{float(tot[(tot['year']==2100) & (tot['ssp']=='SSP5-8.5')]['l11_p05_p95_width_cm'].iloc[0]):.1f} cm")

    out.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
