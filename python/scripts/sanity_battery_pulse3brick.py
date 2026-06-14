#!/usr/bin/env python
"""
Sanity battery for the CO2/CH4 pulse->SLR 3-BRICK-version study.

Gates the 90k-run production launch. Operates on the SMOKE arms produced by
run_mimibrick_pulse_versioned.jl on the OLD lhs10k family (the only family with
the full pos/neg/1Gt/CH4 cube set; the canonical lhs10ks family has positive
pulses only, so the sign-flip / x-magnitude checks use the lhs10k proxy -- these
are RELATIVE consistency checks, so the sample identity is irrelevant).

Per-cell marginal: dSLR = (SLR_pulse - SLR_base) / pulse_size, paired on
(rff_idx, fair_cfg_idx, seed_idx, post_idx). pulse sizes: 001gt/001tg = 0.01,
1gt = 1.0.

Tests:
  1. zero-pulse / cross-process determinism: base vs baseB bit-identical (diff==0)
  2. sign-flip: (pos-base) ~= -(neg-base) per cell (linear regime)
  3. x-magnitude: per-unit from 1Gt ~= per-unit from 0.01Gt (median; tails diverge at AIS tipping)
  4. first-principles: dGIS, dTE per +unit are positive (warming -> melt/expansion); CH4:CO2 ratio sane
  5. closure on marginals: d(ais+gsic+gis+te+lws) ~= d(total) per cell
"""
import os, sys
import numpy as np
import pandas as pd

SD = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sanity"
KEY = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
COMP = ["ais", "gsic", "gis", "te", "lws"]
YEARS = [2100, 2150, 2300]
SLR = [f"slr_{y}_cm" for y in YEARS]
ALLCOLS = SLR + [f"{c}_{y}_cm" for y in YEARS for c in COMP]

def load(tag):
    return pd.read_csv(f"{SD}/{tag}.csv").sort_values(KEY).reset_index(drop=True)

def marg(pulse, base, size):
    """per-unit marginal dataframe (cm per unit), paired on KEY."""
    m = pulse.merge(base, on=KEY, suffixes=("_p", "_b"))
    out = m[KEY].copy()
    for c in ALLCOLS:
        out[c] = (m[f"{c}_p"] - m[f"{c}_b"]) / size
    return out

def med(df, c):
    return float(np.median(df[c]))

PASS, FAIL = "PASS", "**FAIL**"
results = []

# ---------------- Test 1: zero-pulse / determinism (brick2) ----------------
try:
    a, b = load("b2_base"), load("b2_baseB")
    d = (a[ALLCOLS].values - b[ALLCOLS].values)
    maxabs = float(np.max(np.abs(d)))
    ok = maxabs == 0.0
    results.append(("1 zero-pulse/determinism (brick2 base vs baseB)",
                    PASS if ok else FAIL, f"max|diff|={maxabs:.3e} cm (must be 0)"))
except Exception as e:
    results.append(("1 zero-pulse/determinism", FAIL, f"err: {e}"))

# ---------------- per-version pulse marginals ----------------
def battery_for(v):
    base = load(f"{v}_base")
    co2p = marg(load(f"{v}_co2p"), base, 0.01)   # per GtCO2
    co2n_raw = load(f"{v}_co2n")
    ch4p = marg(load(f"{v}_ch4p"), base, 0.01)   # per Tg CH4
    # sign-flip: (pos-base) vs (neg-base) raw differences (0.01 vs -0.01 pulse)
    mp = load(f"{v}_co2p").merge(base, on=KEY, suffixes=("_p","_b"))
    mn = co2n_raw.merge(base, on=KEY, suffixes=("_p","_b"))
    return base, co2p, ch4p, mp, mn

for v in ["b2", "p9", "mg"]:
    try:
        base, co2p, ch4p, mp, mn = battery_for(v)

        # Test 2: sign-flip on slr_2100
        c = "slr_2100_cm"
        dpos = (mp[f"{c}_p"] - mp[f"{c}_b"]).values   # +0.01 pulse
        dneg = (mn[f"{c}_p"] - mn[f"{c}_b"]).values   # -0.01 pulse
        # expect dneg ~= -dpos ; report symmetry ratio on the median magnitude
        denom = np.median(np.abs(dpos)) + 1e-30
        asym = np.median(np.abs(dpos + dneg)) / denom
        results.append((f"2 sign-flip {v} (slr2100)", PASS if asym < 0.05 else FAIL,
                        f"median|dpos+dneg|/median|dpos|={asym:.3e} (want ~0; pos median={np.median(dpos):.3e} cm)"))

        # Test 4: first-principles signs (per +unit CO2): GIS, TE positive
        gis = med(co2p, "gis_2100_cm"); te = med(co2p, "te_2100_cm")
        tot100 = med(co2p, "slr_2100_cm"); tot300 = med(co2p, "slr_2300_cm")
        ok4 = (gis > 0) and (te > 0) and (tot100 > 0)
        results.append((f"4 first-principles {v} (CO2 dGIS,dTE>0)", PASS if ok4 else FAIL,
                        f"per-GtCO2 median dTE2100={te:.4e} dGIS2100={gis:.4e} dSLR2100={tot100:.4e} dSLR2300={tot300:.4e} cm"))

        # Test 5: closure on marginals (per cell, year 2300)
        cs = sum(co2p[f"{c}_2300_cm"] for c in COMP)
        resid = (co2p["slr_2300_cm"] - cs).abs().max()
        results.append((f"5 closure {v} (marginal d-components==d-total @2300)",
                        PASS if resid < 1e-9 else FAIL, f"max|resid|={resid:.3e} cm"))

        # CH4:CO2 ratio (informational + sign check)
        ch4_100 = med(ch4p, "slr_2100_cm")
        results.append((f"4b CH4 {v} (dSLR>0, CH4:CO2 ratio)", PASS if ch4_100 > 0 else FAIL,
                        f"per-Tg dSLR2100={ch4_100:.4e} cm ; CH4/CO2 (per-unit, slr2100)={ch4_100/tot100:.3f}"))
    except Exception as e:
        results.append((f"version {v}", FAIL, f"err: {e}"))

# ---------------- Test 3: x-magnitude (brick2 only) ----------------
try:
    base = load("b2_base")
    perunit_small = marg(load("b2_co2p"),  base, 0.01)
    perunit_big   = marg(load("b2_co2p1"), base, 1.00)
    rows = []
    for c in ["slr_2100_cm","slr_2300_cm","ais_2300_cm","gis_2300_cm","te_2300_cm"]:
        s, bgm = med(perunit_small,c), med(perunit_big,c)
        rows.append(f"{c}: small={s:.3e} big={bgm:.3e} ratio={ (bgm/s) if s else float('nan'):.3f}")
    # in the linear regime the MEDIAN per-unit should agree within ~15%; AIS tail diverges
    s100, b100 = med(perunit_small,"slr_2100_cm"), med(perunit_big,"slr_2100_cm")
    rel = abs(b100 - s100) / (abs(s100) + 1e-30)
    results.append(("3 x-magnitude (brick2 median slr2100, 0.01 vs 1Gt)",
                    PASS if rel < 0.15 else FAIL,
                    f"rel diff median={rel:.3f}; " + " | ".join(rows)))
except Exception as e:
    results.append(("3 x-magnitude", FAIL, f"err: {e}"))

# ---------------- report ----------------
print("\n" + "="*78)
print("SANITY BATTERY  —  CO2/CH4 pulse -> SLR, 3 BRICK versions  (smoke, lhs10k proxy)")
print("="*78)
nfail = 0
for name, status, detail in results:
    if status == FAIL: nfail += 1
    print(f"[{status}] {name}\n        {detail}")
print("="*78)
print(f"{'ALL PASS — gate OPEN for production' if nfail==0 else f'{nfail} FAILURES — gate CLOSED'}")
sys.exit(1 if nfail else 0)
