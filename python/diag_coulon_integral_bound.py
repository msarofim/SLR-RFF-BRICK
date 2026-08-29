"""
diag_coulon_integral_bound.py

THE DELIVERABLE OF THE [DECIDED] 2026-08-29 COULON RULING: report BOTH averaging
domains as a bound, on the quantity the arms are actually centred on -- the
2015-2299 TEMPERATURE INTEGRAL, not the 2300 endpoint.

The earlier reachability pass (diag_coulon_domain_reachability.py) priced the
ENDPOINT because that was all the domain-sensitivity table held. The arms were
respecified on the integral (Marcus, 2026-08-28) after AIS@2300 was measured
~linear in it, so the endpoint answer was a stand-in. This closes it.

INPUTS, one per domain, same schema:
  data/cmip6_coulon/           land proxy, sftlf >= 50%   (as delivered; UNTOUCHED)
  data/cmip6_coulon_allcells/  all surface types south of 60S (built 2026-08-29)

⚠ ACCEPTANCE GATE FIRST. The all-cells series is newly built here, so before any
integral is reported it must reproduce the PUBLISHED endpoint table
(outputs/diag_coulon_domain_sensitivity.csv) that the ruling was made on. If it
does not, the build is wrong and nothing below is usable.

WINDOW is the reducer's own named constant: 2015-2299 for ALL four models, so
CESM2-WACCM's 2299 coverage does not shorten anyone else and the window cancels
in every cross-model comparison.

  source ~/climate-env/bin/activate && python python/diag_coulon_integral_bound.py
"""
import os
import numpy as np
import pandas as pd

REPO   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS = {"sftlf>=50": "data/cmip6_coulon", "all_cells": "data/cmip6_coulon_allcells"}
PUB    = os.path.join(REPO, "outputs/diag_coulon_domain_sensitivity.csv")
CUBE   = os.path.join(REPO, "data/observations/fair_cube_gmst_ssp585_spliced.csv")
POST   = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L21.csv")
OUT    = os.path.join(REPO, "outputs/diag_coulon_integral_bound.csv")
REF    = (1995, 2014)
INT0, INT1 = 2015, 2299          # the reducer's named window
SSP    = "ssp585"
GATE_TOL_K = 0.02                # endpoint reproduction tolerance


def series(d, model):
    f = os.path.join(REPO, d, f"tas_series_{model}.csv")
    if not os.path.exists(f):
        return None
    s = pd.read_csv(f)
    s = s[s.scenario.isin(["historical", SSP])]
    t = s.groupby("year")["tas_ais"].mean()
    ref = t.loc[REF[0]:REF[1]].mean()
    return t - ref


def main():
    pub = pd.read_csv(PUB)
    models = sorted(pub.model.unique())
    print(f"\n{'='*84}\nCOULON: BOTH AVERAGING DOMAINS AS A BOUND, ON THE {INT0}-{INT1} INTEGRAL"
          f"\n{'='*84}\n")

    # ---- acceptance gate: reproduce the published endpoints -----------------
    print(f"  [GATE] the newly built all-cells series must reproduce the PUBLISHED endpoints\n")
    print(f"  {'model':>14} {'domain':>11} {'published':>10} {'rebuilt':>9} {'diff':>7}")
    ok = True
    for m in models:
        for dom, d in DOMAINS.items():
            t = series(d, m)
            p = pub[(pub.model == m) & (pub["mask"] == dom)]
            if t is None or p.empty:
                continue
            yr = INT1 + 1 if (INT1 + 1) in t.index else int(t.index.max())
            got, want = float(t.loc[yr]), float(p.tant_2300_degC.iloc[0])
            bad = abs(got - want) > GATE_TOL_K
            ok &= not bad
            print(f"  {m:>14} {dom:>11} {want:10.2f} {got:9.2f} {got-want:+7.2f}"
                  f"{'  ⚠' if bad else ''}")
    if not ok:
        print("\n  ⚠ GATE FAILED — the rebuilt series does not reproduce the table the ruling\n"
              "    was made on. STOP: do not read the integrals below.\n")
    else:
        print(f"\n  -> GATE PASSES (all within {GATE_TOL_K} K)\n")

    # ---- the integral, both domains ----------------------------------------
    print(f"  ANTARCTIC WARMING INTEGRAL {INT0}-{INT1}, degC-century (anomaly vs "
          f"{REF[0]}-{REF[1]})\n")
    print(f"  {'model':>14} {'land proxy':>12} {'all cells':>11} {'difference':>12}")
    rows = []
    for m in models:
        vals = {}
        for dom, d in DOMAINS.items():
            t = series(d, m)
            if t is None:
                continue
            w = t.loc[INT0:INT1]
            if len(w) < (INT1 - INT0 + 1):
                print(f"  {m:>14}  ⚠ only {len(w)} of {INT1-INT0+1} years; skipped"); vals = {}; break
            vals[dom] = float(w.sum()) / 100.0
        if len(vals) == 2:
            print(f"  {m:>14} {vals['sftlf>=50']:12.2f} {vals['all_cells']:11.2f} "
                  f"{vals['all_cells']-vals['sftlf>=50']:+12.2f}")
            rows.append(dict(model=m, integral_land=vals["sftlf>=50"],
                             integral_allcells=vals["all_cells"]))
    r = pd.DataFrame(rows)
    if r.empty:
        print("\n  no model had both domains at full coverage.\n"); return
    print(f"\n  THE BOUND: land proxy {r.integral_land.min():.2f}-{r.integral_land.max():.2f}"
          f"  |  all cells {r.integral_allcells.min():.2f}-{r.integral_allcells.max():.2f}"
          f"  degC-century")

    # ---- does our ensemble reach it, under either domain? ------------------
    c = pd.read_csv(CUBE).set_index("year")
    anom = c - c.loc[REF[0]:REF[1]].mean()
    integ = anom.loc[INT0:INT1].sum().values / 100.0          # per config, degC-century
    amp = pd.read_csv(POST)["ais_gmst_amp"].values
    amed, imax = float(np.median(amp)), float(integ.max())
    print(f"\n  OUR ENSEMBLE: {len(integ)} configs, integral max {imax:.2f}, "
          f"median {np.median(integ):.2f} degC-century; L21 median amp {amed:.4f}")
    print(f"  -> reachable at the median amp up to {amed*imax:.2f} degC-century\n")
    print(f"  {'model':>14} {'domain':>11} {'target':>8} {'amp needed':>11} {'amp %ile':>9} "
          f"{'n cfg':>7} {'reach':>6}")
    for _, q in r.iterrows():
        for dom, col in (("sftlf>=50", "integral_land"), ("all_cells", "integral_allcells")):
            T = float(q[col]); need = T / imax
            pct = 100.0 * (amp >= need).mean()
            ncfg = int((integ * amed >= T).sum())
            print(f"  {q.model:>14} {dom:>11} {T:8.2f} {need:11.3f} {pct:8.1f}% {ncfg:7d} "
                  f"{'YES' if ncfg else 'no':>6}")
            rows_out = dict(model=q.model, domain=dom, integral=T, amp_needed=need,
                            amp_pct_above=pct, n_configs=ncfg)
            r.loc[r.model == q.model, f"amp_needed_{dom}"] = need
    r.to_csv(OUT, index=False)
    nl = sum(1 for _, q in r.iterrows() if (integ*amed >= q.integral_land).sum() > 0)
    na = sum(1 for _, q in r.iterrows() if (integ*amed >= q.integral_allcells).sum() > 0)
    print(f"\n  VERDICT ON THE INTEGRAL: reachable at the median amp — {nl} of {len(r)} under the")
    print(f"  land proxy, {na} of {len(r)} under all cells." +
          ("  SAME under both: the domain question does NOT bind on the integral."
           if nl == na else
           "  DIFFERENT: domain-sensitive, as on the endpoint."))
    print(f"\n  wrote {OUT}\n")


if __name__ == "__main__":
    main()
