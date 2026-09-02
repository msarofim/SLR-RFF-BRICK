#!/usr/bin/env python3
"""diag_matched_pair_facts_penalty.py — FACTS on the MATCHED-dT overshoot pair.

WHY. Ladrillo and BRICK 2.0 agree on the matched-dT overshoot penalty (+2.21 vs +2.57 cm
@2300), but they share a lineage and a driver, so their agreement is not fully independent
evidence. FACTS is process-based, uses different ice-sheet methods entirely (IPCC AR5,
LARMIP-2, DeConto/Kopp SEJ, Bamber SEJ) and different glacier models (ar5/emu), so it is the
one comparator independent of the BRICK line on BOTH glaciers and ice sheets.

⚠⚠ HORIZON. OUR shared-climate arms are configured to pyear_end 2150, so everything here is
2100/2150 and must be compared against Ladrillo/BRICK AT THOSE YEARS, never against their 2300
numbers. ⚠ That is OUR convention, NOT a FACTS limit -- eight configs in this repo run to 2300
and SLEIP runs FACTS to 2300. A 2300 arm is UNTESTED for this module set, not unsupported.

⭐ THE PAIRING IS EXACT. FACTS is deterministic on the non-emu workflows (default_rng(1234)):
two identical runs are bit-identical, and both arms draw the SAME 200 FaIR configs in the same
order ([CONFIG-AXIS] in build_shared_climate_nc.py). So sample i in the two arms shares its
climate config AND its module RNG draws, and the paired difference cancels structural
ice-sheet noise EXACTLY rather than approximately (memory facts_install_scope).

⚠ ssp534overMATCH is IDEALISED -- never quote it as SSP5-3.4-OS.
"""
import os, sys, numpy as np, netCDF4 as nc4

REPO = os.path.dirname(os.path.abspath(__file__))
## Two horizon arms of the SAME pair. The 2150 set is the original shared-climate convention;
## the 2300 set was added 2026-09-02 to reach SLEIP's actual headline year, as SEPARATE
## experiments so the 2150 comparison column stays like-for-like.
ARMS = {2150: ("ssp126nomarker", "ssp534overMATCH"),
        2300: ("ssp126nomarker2300", "ssp534overMATCH2300")}
WORKFLOWS = ["wf1f", "wf2f", "wf3f", "wf4"]
WF_LABEL = {"wf1f": "wf1f IPCC AR5",  "wf2f": "wf2f LARMIP-2",
            "wf3f": "wf3f DeConto/Kopp", "wf4": "wf4 Bamber SEJ"}
HORIZONS = {2150: [2100, 2150], 2300: [2100, 2150, 2300]}
MM_TO_CM = 0.1
## Ladrillo / BRICK 2.0 on the SAME matched pair, from diag_matched_dt_penalty.csv (paired median, cm).
LAD = {2100: 4.046, 2150: 3.318, 2300: 2.213}
BRK = {2100: 3.631, 2150: 3.345, 2300: 2.575}

def total(key, wf):
    p = os.path.join(REPO, "experiments", "global.shared.%s.n200" % key, "output",
                     "global.shared.%s.n200.total.workflow.%s.global.nc" % (key, wf))
    if not os.path.exists(p): return None, None
    d = nc4.Dataset(p)
    return d.variables["sea_level_change"][:, :, 0] * MM_TO_CM, d.variables["years"][:]

rows = {}
for endyear, (ref, ovr) in ARMS.items():
    print("=" * 96)
    print(f"FACTS ON THE MATCHED-dT OVERSHOOT PAIR — paired penalty, cm   [arm run to {endyear}]")
    print(f"  {ovr} minus {ref}   n=200, paired sample-for-sample")
    print("=" * 96)
    print("  %-20s%10s%10s%10s%10s%10s" % ("workflow", "horizon", "median", "mean", "p05", "p95"))
    for wf in WORKFLOWS:
        A, ya = total(ovr, wf); B, yb = total(ref, wf)
        if A is None or B is None:
            print(f"  [MISSING] {wf} — the {endyear} arm did not produce a total"); continue
        assert np.array_equal(ya, yb) and A.shape == B.shape, "axis/shape mismatch %s" % wf
        D = A - B
        for H in HORIZONS[endyear]:
            if H not in list(ya): continue
            i_ = int(np.where(ya == H)[0][0]); x = np.asarray(D[:, i_])
            rows[(endyear, wf, H)] = (float(np.median(x)), float(x.mean()),
                                      float(np.percentile(x, 5)), float(np.percentile(x, 95)))
            print("  %-20s%10d%10.3f%10.3f%10.3f%10.3f" % ((WF_LABEL[wf], H) + rows[(endyear, wf, H)]))
    print()

print("=" * 96)
print("AGAINST THE BRICK-LINEAGE MODELS ON THE SAME PAIR (paired median, cm)")
print("=" * 96)
hs = [2100, 2150, 2300]
print("  %-24s" % "" + "".join("%12s" % f"@{h}" for h in hs))
print("  %-24s" % "Ladrillo L24" + "".join("%12.2f" % LAD[h] for h in hs))
print("  %-24s" % "BRICK 2.0" + "".join("%12.2f" % BRK[h] for h in hs))
for wf in WORKFLOWS:
    cells = []
    for h in hs:
        v = rows.get((2300, wf, h)) or rows.get((2150, wf, h))
        cells.append("%12.2f" % v[0] if v else "%12s" % "--")
    print("  %-24s" % WF_LABEL[wf] + "".join(cells))
f2300 = [rows[(2300, w, 2300)][0] for w in WORKFLOWS if (2300, w, 2300) in rows]
if f2300:
    p95 = [rows[(2300, w, 2300)][3] for w in WORKFLOWS if (2300, w, 2300) in rows]
    print(f"\n  ⭐ AT 2300 — SLEIP's own headline year:")
    print(f"     FACTS medians {min(f2300):.2f} to {max(f2300):.2f} cm across {len(f2300)} workflows; "
          f"Ladrillo {LAD[2300]:.2f}, BRICK 2.0 {BRK[2300]:.2f}")
    print(f"     FACTS p95     {min(p95):.1f} to {max(p95):.1f} cm   (Ladrillo 43.3, BRICK 2.0 51.3)")
    print(f"     SLEIP reports 10-30 cm at 2300.")
