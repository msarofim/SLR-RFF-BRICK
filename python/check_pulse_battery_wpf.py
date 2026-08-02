"""Sanity battery verdicts for the weight_and_project_brick_fair.jl pulse arm.

Compares three matched runs (same 10 configs x 100 draws, each self-paired on its
own wide-file basis):
  wong_cond_pulse_bands_p10ref.csv    +10 GtCO2 canonical arm  (per-GtCO2 = /10)
  wong_cond_pulse_bands_signflip.csv  -10 GtCO2 companion      (per-GtCO2 = /10, negative)
  wong_cond_pulse_bands_dbl.csv       +20 GtCO2 companion      (per-GtCO2 = /20)

Tests (climate-modeling skill, INDEP median per-GtCO2 basis):
  sign-flip: med(-10)/med(+10) ~ -1 within TOL on the near-linear metrics
  doubling : med(+20)/med(+10) ~ +1 within TOL (already per-GtCO2 normalized)
AIS/total metrics carry genuine tipping asymmetry at 10-20 GtCO2 (mimibrick-quirks
item 11), so hard PASS/FAIL is applied to the LINEAR set; the rest is reported.
"""
import csv
import sys
from pathlib import Path

BANDS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "mcmc"
# NB output suffix = basis + out-tag (driver OUTSFX composition)
RUNS = {"p10": "wong_cond_pulse_bands_p10ref.csv",
        "m10": "wong_cond_pulse_bands_neg10gt_signflip.csv",
        "d20": "wong_cond_pulse_bands_20gt_dbl.csv"}
TOL = 0.10                       # linear-regime tolerance (skill default ~10%)
LINEAR_METRICS = ["te@2100", "te@2150", "te@2300", "gsic@2100", "gis@2100",
                  "total@2050"]  # pre-tipping / non-AIS: linear-regime expectations hold


def load(fname):
    with open(BANDS_DIR / fname) as f:
        return {r["metric"]: float(r["ind_med"]) for r in csv.DictReader(f)}


runs = {k: load(v) for k, v in RUNS.items()}
metrics = list(runs["p10"])
fails = []
print(f"{'metric':<12} {'+10/Gt':>11} {'-10/Gt':>11} {'+20/Gt':>11} {'flip_ratio':>10} {'dbl_ratio':>10}  verdict")
for m in metrics:
    p, n, d = runs["p10"][m], runs["m10"][m], runs["d20"][m]
    flip = n / p if p != 0 else float("nan")
    dbl = d / p if p != 0 else float("nan")
    if m in LINEAR_METRICS:
        ok = abs(flip + 1.0) <= TOL and abs(dbl - 1.0) <= TOL
        verdict = "PASS" if ok else "FAIL"
        if not ok:
            fails.append(m)
    else:
        verdict = "(reported; AIS-tipping asymmetry expected)"
    print(f"{m:<12} {p:>11.3e} {n:>11.3e} {d:>11.3e} {flip:>10.3f} {dbl:>10.3f}  {verdict}")

if fails:
    print(f"\nBATTERY FAIL on linear metrics: {', '.join(fails)} (tol {TOL:.0%})")
    sys.exit(1)
print(f"\nBATTERY PASS: all linear metrics within {TOL:.0%} on sign-flip and doubling")
