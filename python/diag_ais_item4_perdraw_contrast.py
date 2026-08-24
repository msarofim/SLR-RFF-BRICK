"""
diag_ais_item4_perdraw_contrast.py -- rank-safe dependence of the AIS projection
on the ANCHORED-window flux quantities, read off the item-4 per-draw table.

WHY THIS IS NOT DONE IN THE JULIA FILE. `diag_ais_item4_sampler.jl` prints Pearson
correlations in its [SAME-Q] block, and Pearson is the WRONG statistic on the cell
the block is about: ssp245 AIS @2100 is bimodal in tipped/not-tipped, and
`diag_ais_block_propagation.jl` already established that a linear correlation across
that bimodality understates a quantity moving the MIXTURE WEIGHT rather than the
level. So the Julia [SAME-Q] number is a screen, and the verdict is taken here on
the DECILE CONTRAST -- median(top decile) - median(bottom decile), expressed as a
fraction of the projection's own p05-p95, which is the same statistic and the same
normalisation the propagation ranking uses (memory `tolerance_scaled_to_spread`).
Spearman is reported alongside so a monotone-but-curved dependence is not read as
absence through Pearson alone.

WHAT IT SETTLED. The hypothesis that the one deliverable cell failing R-hat and the
one flux quantity failing R-hat were the SAME direction -- they have nearly equal
R-hat (1.070 / 1.069) and ESS (38.4 / 43.6). Refuted: contrast +0.026 of the spread.
And it located the direction that DOES qualify on the item-4 criterion, which is
neither of the two named parameters. See CHANGELOG 2026-08-24k sec [4].

  python3 python/diag_ais_item4_perdraw_contrast.py [--tag=L14]
Writes outputs/diag_ais_item4_contrast_<tag>.csv
"""
import csv
import os
import sys
from statistics import mean, median

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
SRC = os.path.join(REPO, "outputs", f"diag_ais_item4_perdraw_{TAG}.csv")
OUT = os.path.join(REPO, "outputs", f"diag_ais_item4_contrast_{TAG}.csv")

DECILE = 0.10          # matches diag_ais_block_propagation.jl
SCENARIOS = ("ssp245", "ssp585")
# (label, predictor column, response column)
PAIRS = [
    ("net->AIS2100",   "net_anchored_gt",        "ais_2100_cm"),
    ("net->AIS2300",   "net_anchored_gt",        "ais_2300_cm"),
    ("smb->AIS2100",   "smb_anchored_gt",        "ais_2100_cm"),
    ("smb->AIS2300",   "smb_anchored_gt",        "ais_2300_cm"),
    ("disch->AIS2100", "discharge_anchored_gt",  "ais_2100_cm"),
    ("disch->AIS2300", "discharge_anchored_gt",  "ais_2300_cm"),
    ("rate->AIS2100",  "ais_rate_anchored_mmyr", "ais_2100_cm"),
    ("rate->AIS2300",  "ais_rate_anchored_mmyr", "ais_2300_cm"),
]


def ranks(v):
    """Average ranks. Ties matter: a stuck chain repeats values exactly, and a naive
    ordinal rank would invent an ordering among them."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2
        i = j + 1
    return out


def pearson(x, y):
    mx, my = mean(x), mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return float("nan") if den == 0 else num / den


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def quantile(v, p):
    s = sorted(v)
    h = p * (len(s) - 1)
    lo = int(h)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def decile_contrast(x, y, q=DECILE):
    """median(y | x in its top decile) - median(y | x in its bottom decile).
    Strict on both sides so a predictor constant over a decile yields nan rather
    than a contrast computed against itself."""
    lo, hi = quantile(x, q), quantile(x, 1 - q)
    ylo = [b for a, b in zip(x, y) if a <= lo]
    yhi = [b for a, b in zip(x, y) if a >= hi]
    if not ylo or not yhi:
        return float("nan")
    return median(yhi) - median(ylo)


rows = list(csv.DictReader(open(SRC)))
print(f"item-4 per-draw dependence | tag {TAG} | {len(rows)} rows | "
      f"decile contrast at {DECILE:.0%}, normalised by the response's own p05-p95")

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["scenario", "pair", "predictor", "response", "n",
                "pearson_r", "spearman_rho", "decile_contrast",
                "response_p05_p95", "contrast_frac_spread"])
    for scen in SCENARIOS:
        sub = [r for r in rows if r["scenario"] == scen]
        if not sub:
            continue
        print(f"\n--- {scen} (n={len(sub)}) ---")
        print(f"  {'pair':16s} {'pearson':>9s} {'spearman':>9s} "
              f"{'contrast':>10s} {'frac':>8s}")
        for label, px, py in PAIRS:
            x = [float(r[px]) for r in sub]
            y = [float(r[py]) for r in sub]
            spread = quantile(y, 0.95) - quantile(y, 0.05)
            c = decile_contrast(x, y)
            frac = c / spread if spread else float("nan")
            print(f"  {label:16s} {pearson(x, y):+9.4f} {spearman(x, y):+9.4f} "
                  f"{c:+10.2f} {frac:+8.4f}")
            w.writerow([scen, label, px, py, len(sub),
                        f"{pearson(x, y):.6f}", f"{spearman(x, y):.6f}",
                        f"{c:.6f}", f"{spread:.6f}", f"{frac:.6f}"])

print(f"\nwrote {os.path.relpath(OUT, REPO)}")
