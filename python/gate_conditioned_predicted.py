#!/usr/bin/env python3
"""
gate_conditioned_predicted.py -- the record-conditioned Ladrillo joint arm (scope_slr_fair_uncertainty.jl, RECORD
CONDITIONING, 2026-10-08) must reproduce, EXACTLY, the conditioned statistics that diag_record_crossing_effect.py
predicted on 10-08 by deleting the crossing draws from the shipped v1.1 draws files.

    python python/gate_conditioned_predicted.py

Two implementations of one rule: the driver drops draws by the MODEL's own onset during the run; the diagnostic
deleted them from the written draws afterwards, recomputing Julia's quantile arithmetic for arithmetic. Conditioning
by rejection leaves every other draw unchanged, so the two must agree to the bit.

SSP scenarios only: the 10-08 prediction was made on the `harmonized` van Vuuren cubes, which this rerun replaces.
[DROPPED-SET]  the driver's REJECTED rows (gates file) must be exactly the prediction's `dropped_draws` at RECORD_END.
[CELLS]        joint-arm med / p05 / p95 of ais and total at 2100 / 2150 / 2300 == the prediction's conditioned_cm;
               joint n_draws == 2000 - n_dropped.
Power: the same comparison against the prediction at RECORD_END + 1 (a different dropped set) must FAIL, or the gate
is refused as blind.
"""
import os, sys
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED = os.path.join(REPO, "outputs/diag_record_crossing_effect_L27.csv")
TAP = "_tap4p69K_V5p64m_tau800"
CELLS = lambda s: os.path.join(REPO, f"outputs/scope_slr_fairunc_cells_{s}_spliced_L27{TAP}.csv")
GATES = lambda s: os.path.join(REPO, f"outputs/scope_slr_fairunc_gates_{s}_spliced_L27{TAP}.csv")
SSPS = ("ssp126", "ssp245", "ssp585")
RECORD_END = 2025
NDRAW = 2000
STAT_COL = {"med": "med_cm", "p05": "p05_cm", "p95": "p95_cm"}


def compare(pred_year):
    p = pd.read_csv(PRED, float_precision="round_trip")
    p = p[(p.last_year == pred_year) & p.scenario.isin(SSPS)]
    nbad, ncmp, setbad = 0, 0, []
    for s in SSPS:
        c = pd.read_csv(CELLS(s), float_precision="round_trip")
        c = c[c.arm == "joint"]
        g = pd.read_csv(GATES(s))
        rej = sorted(int(k.split("_")[1]) for k in g[g.gate == "REJECTED"].key)
        ps = p[p.scenario == s]
        want = sorted(int(x) for x in str(ps.dropped_draws.iloc[0]).split())
        if rej != want:
            setbad.append((s, rej, want))
        for _, r in ps.iterrows():
            cell = c[(c.component == r.component) & (c.horizon == r.horizon)]
            if len(cell) != 1:
                sys.exit(f"ERROR: {s} {r.component} {r.horizon}: {len(cell)} joint cells")
            got = float(cell[STAT_COL[r.stat]].iloc[0])
            ncmp += 1
            if got != float(r.conditioned_cm) or int(cell.n_draws.iloc[0]) != NDRAW - int(r.n_dropped):
                nbad += 1
    return ncmp, nbad, setbad


def main():
    n, bad, setbad = compare(RECORD_END + 1)
    if bad == 0 and not setbad:
        sys.exit(f"ERROR: [POWER] the prediction at {RECORD_END + 1} (a different dropped set) also matched; blind")
    print(f"[POWER] against the {RECORD_END + 1} prediction: {bad} of {n} cells and {len(setbad)} dropped sets differ, as they must")
    n, bad, setbad = compare(RECORD_END)
    for s, got, want in setbad:
        print(f"  [DROPPED-SET] {s}: driver dropped {got}, prediction {want}: FAIL")
    print(f"  [DROPPED-SET] {len(SSPS) - len(setbad)} of {len(SSPS)} scenarios match")
    print(f"  [CELLS] {n - bad} of {n} conditioned cells bit-identical to the prediction")
    ok = bad == 0 and not setbad
    print(f"[CONDITIONED-PREDICTED] {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
