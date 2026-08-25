#!/usr/bin/env python3
"""
diag_total_spread_ssp585_2150.py — THE ONE UNEXAMINED FAIL: is `TOTAL ssp585@2150 spread
                                   = 0.365x lit` a defect of the total, or of one component
                                   scored against a comparator set the component itself is
                                   NOT scored against?

`bench_ladrillo.py` at L14 leaves three candidate FAILs. Two have been priced (the TE rate
= an OHC-driver/depth-scope question, `d24cc67`; the Greenland ssp126@2100 spread = ~4% of
one band, `bbee082`). This is the third and it had never been looked at.

THE SUSPICION, STATED BEFORE MEASURING. The same cell's own AIS component scores 0.525
PASS. A total cannot be 0.365x the literature while every component of it is 0.46-0.90x
unless the two are being scored against DIFFERENT comparator sets. `audit_every_target`.

WHAT THIS SCRIPT ESTABLISHES, IN ORDER:

  [A] WHAT THE FACTS WORKFLOWS ARE, FROM THE DATA. This repo stores wf1f/wf2f/wf3f/wf4 as
      opaque total-level module strings with no documented composition -- and a benchmark
      cannot classify a comparator it cannot name. Rather than assert the AR6 taxonomy from
      recall, the composition is IDENTIFIED by fitting each workflow total against
      every (AIS module x GIS module) combination present in the same file, on THREE
      independent statistics -- the sum of component medians, the quadrature sum of
      component p05-p95 spreads, and the quadrature sum of component UPPER half-widths
      (p95 - med). Each SLOT is voted on separately, and only by the statistics that
      DISCRIMINATE it -- a statistic whose best fit worsens by less than 2x when that slot
      is forced to any other value has RANKED without discriminating and does not vote.
      ⚠ THE FIRST VERSION OF THIS TEST USED TWO STATISTICS, REJECTED wf4, AND THAT
      REJECTION WAS RIGHT TO FIRE. bamber19's AIS median (36.5 cm) and larmip's (37.4 cm)
      differ by 2% at ssp585@2150, so the median test cannot see the AIS slot at all: it
      picked larmip while the spread test picked bamber19, at a margin of 1.9x against the
      4.2-5.5x the other three workflows show. The UPPER half-width is what discriminates
      -- bamber19's AIS upper is 517.9 cm against larmip's 105.0, and wf4's own total upper
      is 553.6 cm, a value no larmip-based composition can reach (wf2f, which IS larmip,
      has 105.5). With it, wf4 identifies as bamber19 in BOTH ice sheets.

  [B] THE COMPONENT DECOMPOSITION OF THE GAP. For every comparator, how much of its
      total-spread difference from ours is its AIS-spread difference.

  [C] WHAT THE CLASSIFICATION IS WORTH, at every total cell, with the honest per-cell
      before/after -- never only at the cell where it helps.

⚠ THE LINE IS NOT MOVED TO IMPROVE OUR SCORE. `benchmark/comparator_classes.csv` already
classifies bamber19 as structured expert judgement; what this script tests is whether the
EXISTING line is being applied CONSISTENTLY between a component row and a total row that
contains it. Drawing a NEW line (e.g. separating the MICI workflow) is deliberately NOT
done here: deconto21 stays in `model` at the AIS level, so wf3f stays in `model` at the
total level, and the MICI gap is reported as what it is -- the already-priced, already-
declined `ais_binary_form_priced` decision, not a new defect.

    source ~/climate-env/bin/activate
    python python/diag_total_spread_ssp585_2150.py [--tag=L14]
Reads   benchmark/reference/_fixed/facts_components_n200.csv
        benchmark/reference/_fixed/literature_rows.csv
        outputs/bench_ladrillo_<TAG>.csv
Writes  outputs/diag_total_spread_ssp585_2150_<TAG>.csv
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUT = os.path.join(REPO, "outputs", f"diag_total_spread_ssp585_2150_{TAG}.csv")

FACTS_CSV = os.path.join(REPO, "benchmark", "reference", "_fixed", "facts_components_n200.csv")
LIT_CSV = os.path.join(REPO, "benchmark", "reference", "_fixed", "literature_rows.csv")
BENCH_CSV = os.path.join(REPO, "outputs", f"bench_ladrillo_{TAG}.csv")

# THE CELL UNDER TEST -- every label below derives from these three constants.
CELL_SSP, CELL_YEAR = "ssp585", 2150
CELL = f"{CELL_SSP}@{CELL_YEAR}"

# The benchmark's own spread verdict band, restated here so the before/after in [C] is
# graded by the SAME rule the benchmark uses (bench_ladrillo.SPREAD_PASS).
SPREAD_PASS = (0.5, 2.0)

# Workflow identification [A]: the candidate module pools, and the shared modules every
# FACTS workflow in this file uses for the non-ice-sheet components.
AIS_POOL = ["ar5AIS", "bamber19", "deconto21", "larmip"]
GIS_POOL = ["FittedISMIP", "bamber19"]
SHARED = {"glaciers": "ar5glaciers", "te": "tlm", "lws": "ssp-lws"}
WORKFLOWS = ["wf1f", "wf2f", "wf3f", "wf4"]
# Cells the identification is fitted over -- the "f" workflows carry all three SSPs at both
# FACTS horizons, so the fit is over 6 cells, not the one under test.
FIT_CELLS = [(s, y) for s in ("ssp126", "ssp245", "ssp585") for y in (2100, 2150)]
# A combination is ACCEPTED only if it wins on both statistics AND its median error is under
# this. Both winners below come in at 0.96-2.07%, so the gate is not doing subtle work.
ID_MEDIAN_TOL = 0.10


def spread(df, comp, mod, ssp, yr):
    r = df[(df.component == comp) & (df.module == mod) &
           (df.scenario == ssp) & (df.year == yr)]
    if r.empty or not np.isfinite(float(r.p95.iloc[0])) or not np.isfinite(float(r.p05.iloc[0])):
        return np.nan
    return float(r.p95.iloc[0]) - float(r.p05.iloc[0])


def upper(df, comp, mod, ssp, yr):
    """UPPER half-width p95 - med. The statistic that discriminates the wf4 AIS slot: the
    two candidates there agree to 2% on the median and differ 4.9x on this."""
    r = df[(df.component == comp) & (df.module == mod) &
           (df.scenario == ssp) & (df.year == yr)]
    if r.empty or not np.isfinite(float(r.p95.iloc[0])):
        return np.nan
    return float(r.p95.iloc[0]) - float(r.med.iloc[0])


def med(df, comp, mod, ssp, yr):
    r = df[(df.component == comp) & (df.module == mod) &
           (df.scenario == ssp) & (df.year == yr)]
    return np.nan if r.empty else float(r.med.iloc[0])


def main():
    fa = pd.read_csv(FACTS_CSV)
    fa["year"] = fa.year.astype(int)
    lit = pd.read_csv(LIT_CSV)
    lit["year"] = lit.year.astype(int)
    bench = pd.read_csv(BENCH_CSV)
    rows = []

    # ---------------------------------------------------------------- [A] identification
    # THREE STATISTICS. Each is a different functional of the same component
    # distributions, so a combination that wins on all three is not winning on one
    # coincidence. The majority rule exists because a statistic can be BLIND to a slot
    # rather than wrong about it -- see the wf4 note in the docstring.
    STATS = [
        ("median", lambda parts, s, y: sum(med(fa, c, m, s, y) for c, m in parts),
         lambda s, y, wf: med(fa, "total", wf, s, y)),
        ("spread", lambda parts, s, y: np.sqrt(sum(spread(fa, c, m, s, y) ** 2 for c, m in parts)),
         lambda s, y, wf: spread(fa, "total", wf, s, y)),
        ("upper", lambda parts, s, y: np.sqrt(sum(upper(fa, c, m, s, y) ** 2 for c, m in parts)),
         lambda s, y, wf: upper(fa, "total", wf, s, y)),
    ]
    print(f"\n[A] WHAT ARE THE FACTS WORKFLOWS? -- identified from the data, three statistics")
    print(f"    fitted over {len(FIT_CELLS)} cells: {', '.join(f'{s}@{y}' for s, y in FIT_CELLS)}")
    print(f"    each SLOT is voted on separately, by the statistics that DISCRIMINATE it")
    # ⚠ THE VOTE IS PER SLOT, NOT PER COMBINATION. A statistic can be BLIND to one slot
    # while resolving the other, and a per-combination vote throws that away: at wf4 the
    # GIS slot is unanimous while the AIS slot is degenerate on the median. The margin for
    # a slot is how much worse the best fit becomes when that slot is forced to any OTHER
    # value -- a number under ~2x means the statistic ranked without discriminating.
    SLOT_MARGIN_MIN = 2.0
    print(f"\n{'workflow':7s} {'slot':5s} | {'median':>20s} | {'spread':>20s} | {'upper':>20s} | verdict")
    ident = {}
    for wf in WORKFLOWS:
        allsc = {}
        for name, compose, total_of in STATS:
            sc = {}
            for a_, g_ in itertools.product(AIS_POOL, GIS_POOL):
                parts = [("ais", a_), ("gis", g_)] + [(c, m) for c, m in SHARED.items()]
                e = [abs(compose(parts, s, y) / total_of(s, y, wf) - 1.0) for s, y in FIT_CELLS]
                sc[(a_, g_)] = float(np.mean(e))
            allsc[name] = sc
        chosen, allok = {}, True
        for islot, (slot, pool) in enumerate((("ais", AIS_POOL), ("gis", GIS_POOL))):
            votes, cells = [], []
            for name, _, _ in STATS:
                sc = allsc[name]
                best = min(sc, key=sc.get)
                win = best[islot]
                other = min(v for k, v in sc.items() if k[islot] != win)
                marg = other / sc[best] if sc[best] else np.inf
                votes.append((win, marg))
                cells.append(f"{win[:12]:<12s} {marg:5.1f}x")
            # a statistic only VOTES if it discriminated this slot
            disc = [v for v in votes if v[1] >= SLOT_MARGIN_MIN]
            if disc:
                tally = {w: sum(1 for v in disc if v[0] == w) for w in {v[0] for v in disc}}
                win, n = max(tally.items(), key=lambda kv: kv[1])
                ok = n == len(disc)          # every discriminating statistic must agree
            else:
                win, n, ok = None, 0, False
            chosen[slot] = win
            allok &= ok
            print(f"{wf if islot == 0 else '':7s} {slot:5s} | " + " | ".join(cells) +
                  f" | {'OK' if ok else 'AMBIGUOUS'} ({n}/{len(disc)} discriminating agree)")
            rows.append(dict(block="A", cell=f"fit over {len(FIT_CELLS)} FACTS cells",
                             quantity=f"composition/{wf}/{slot}", value=np.nan, unit="",
                             note="; ".join(f"{STATS[i][0]}: {votes[i][0]} margin {votes[i][1]:.1f}x"
                                            for i in range(3)) +
                                  f"; {len(disc)} of 3 statistics discriminated this slot "
                                  f"(margin >= {SLOT_MARGIN_MIN}x)",
                             verdict=f"{win} ({'OK' if ok else 'AMBIGUOUS'})"))
        ident[wf] = (chosen["ais"], chosen["gis"]) if allok else None
        print(f"{'':7s} {'=>':5s} | ais:{chosen['ais']}  gis:{chosen['gis']}"
              f"   {'IDENTIFIED' if allok else 'NOT IDENTIFIED'}")

    sej_wfs = [w for w, v in ident.items() if v and "bamber19" in v]
    print(f"\n  => SEJ-composed workflow(s): {', '.join(sej_wfs) if sej_wfs else 'NONE'}")
    print(f"     `benchmark/comparator_classes.csv` already classifies bamber19 as `sej`, and the")
    print(f"     AIS and GIS rows of this same cell DO exclude it. The TOTAL rows carry the module")
    print(f"     string `wf4`, so that exclusion has never fired on them. That is the inconsistency.")

    # ------------------------------------------------------- [B] decomposition of the gap
    def ours(comp, metric):
        r = bench[(bench.block == "P") & (bench.component == comp) &
                  (bench.scenario == CELL_SSP) & (bench.horizon == CELL_YEAR) &
                  (bench.metric == metric)]
        return float(r.value.iloc[0])

    o = {c: ours(c, "spread_joint") for c in
         ("ais", "gis", "glaciers", "te", "lws", "total")}
    print(f"\n[B] WHOSE WIDTH IS THE GAP AT {CELL}?  ours (cm): " +
          ", ".join(f"{k} {v:.1f}" for k, v in o.items()))
    print(f"\n{'comparator':11s} {'AIS':>7s} {'GIS':>7s} {'GLAC':>6s} {'TE':>6s} {'LWS':>5s} "
          f"{'TOTAL':>7s} | {'ours/theirs':>11s} | {'tot gap':>8s} {'AIS gap':>8s} {'AIS share':>9s}")
    comparators = [(w, ident[w][0], ident[w][1], fa) for w in WORKFLOWS if ident[w]]
    comparators.append(("Nauels2025", "Nauels2025", "Nauels2025", lit))
    for name, amod, gmod, src in comparators:
        th = {"ais": spread(src, "ais", amod, CELL_SSP, CELL_YEAR),
              "gis": spread(src, "gis", gmod, CELL_SSP, CELL_YEAR)}
        for c, m in SHARED.items():
            th[c] = spread(src, c, m if src is fa else "Nauels2025", CELL_SSP, CELL_YEAR)
        tt = spread(src, "total", name if src is fa else "Nauels2025", CELL_SSP, CELL_YEAR)
        gap, agap = tt - o["total"], th["ais"] - o["ais"]
        share = agap / gap if gap else np.nan
        print(f"{name:11s} {th['ais']:7.1f} {th['gis']:7.1f} {th['glaciers']:6.1f} "
              f"{th['te']:6.1f} {th['lws']:5.1f} {tt:7.1f} | {o['total']/tt:11.3f} | "
              f"{gap:8.1f} {agap:8.1f} {100*share:8.0f}%")
        rows.append(dict(block="B", cell=CELL, quantity=f"gap_decomposition/{name}",
                         value=o["total"] / tt, unit="x their total spread",
                         note=f"their total {tt:.1f} cm (AIS {th['ais']:.1f} via {amod}, "
                              f"GIS {th['gis']:.1f} via {gmod}); total gap {gap:+.1f} cm of which "
                              f"AIS is {agap:+.1f} = {100*share:.0f}%",
                         verdict=""))
    print(f"\n  ⚠ The comparator AIS spreads span "
          f"{min(spread(fa,'ais',ident[w][0],CELL_SSP,CELL_YEAR) for w in WORKFLOWS if ident[w]):.0f}"
          f"-{max(spread(fa,'ais',ident[w][0],CELL_SSP,CELL_YEAR) for w in WORKFLOWS if ident[w]):.0f}"
          f" cm, an {max(spread(fa,'ais',ident[w][0],CELL_SSP,CELL_YEAR) for w in WORKFLOWS if ident[w])/min(spread(fa,'ais',ident[w][0],CELL_SSP,CELL_YEAR) for w in WORKFLOWS if ident[w]):.1f}x span.")
    print(f"    A median over a set that disagrees {max(spread(fa,'ais',ident[w][0],CELL_SSP,CELL_YEAR) for w in WORKFLOWS if ident[w])/min(spread(fa,'ais',ident[w][0],CELL_SSP,CELL_YEAR) for w in WORKFLOWS if ident[w]):.0f}x is not a summary of anything -- quote the comparator.")

    # ---------------------------------------------- [C] what the classification is worth
    print(f"\n[C] WHAT EXCLUDING {'/'.join(sej_wfs) or '(nothing -- no SEJ workflow identified)'} IS WORTH -- AT EVERY TOTAL CELL, not just this one")
    allrows = lit
    print(f"\n{'cell':14s} | {'median ratio':>22s} | {'spread ratio':>28s}")
    print(f"{'':14s} | {'with':>10s} {'without':>10s} | {'with':>13s} {'without':>13s}")
    for ssp in ("ssp126", "ssp245", "ssp585"):
        for yr in (2100, 2150, 2300):
            sel = allrows[(allrows.component == "total") & (allrows.scenario == ssp) &
                          (allrows.year == yr)]
            if sel.empty:
                continue
            om = float(bench[(bench.block == "P") & (bench.component == "total") &
                             (bench.scenario == ssp) & (bench.horizon == yr) &
                             (bench.metric == "median_joint")].value.iloc[0])
            osp = float(bench[(bench.block == "P") & (bench.component == "total") &
                              (bench.scenario == ssp) & (bench.horizon == yr) &
                              (bench.metric == "spread_joint")].value.iloc[0])
            keep = sel[~sel.module.isin(sej_wfs)]

            def rr(sub):
                m = np.median(sub.med.astype(float).values)
                s = (sub.p95.astype(float) - sub.p05.astype(float)).dropna().values
                return om / m, (osp / np.median(s) if len(s) else np.nan), len(sub), len(s)
            mw, sw, nw, nsw = rr(sel)
            mo, so, no, nso = rr(keep)

            # ⚠ GRADED BY THE BENCHMARK'S OWN RULES, INCLUDING THE MAJORITY CAP added in
            # this same change -- otherwise this table would report a PASS at a cell the
            # benchmark caps at WARN, and the two would disagree in the deliverable.
            def vd(x, sub):
                if not np.isfinite(x):
                    return "  --  "
                sp = (sub.p95.astype(float) - sub.p05.astype(float)).dropna().values
                if len(sp) < 3:
                    return f"{x:.3f} " + ("PASS" if SPREAD_PASS[0] <= x <= SPREAD_PASS[1] else "WARN")
                side = lambda r: ("in" if SPREAD_PASS[0] <= r <= SPREAD_PASS[1]
                                  else ("low" if r < SPREAD_PASS[0] else "high"))
                per = [side(osp / v) for v in sp]
                if per.count(side(x)) * 2 <= len(per):
                    return f"{x:.3f} WARN"
                return f"{x:.3f} " + ("PASS" if side(x) == "in" else "FAIL")
            flip = "  <== VERDICT FLIPS" if vd(sw, sel).split()[-1] != vd(so, keep).split()[-1] else ""
            print(f"{ssp}@{yr:<9d} | {mw:10.3f} {mo:10.3f} | {vd(sw, sel):>13s} {vd(so, keep):>13s}{flip}")
            rows.append(dict(block="C", cell=f"{ssp}@{yr}", quantity="total_spread_vs_lit",
                             value=so, unit="x lit spread",
                             note=f"with {'/'.join(sej_wfs)}: {sw:.3f} (n={nsw}); without: {so:.3f} "
                                  f"(n={nso}); median ratio {mw:.3f} -> {mo:.3f}",
                             verdict=("FLIPS" if flip else "")))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
