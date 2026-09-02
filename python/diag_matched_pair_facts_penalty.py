#!/usr/bin/env python3
"""diag_matched_pair_facts_penalty.py — FACTS on the MATCHED-dT overshoot pair.

WHY. Ladrillo and BRICK 2.0 agree on the matched-dT overshoot penalty (+2.21 vs +2.57 cm
@2300), but they share a lineage and a driver, so their agreement is not fully independent
evidence. FACTS is process-based, uses different ice-sheet methods entirely (IPCC AR5,
LARMIP-2, DeConto/Kopp SEJ, Bamber SEJ) and different glacier models (ar5/emu), so it is the
one comparator independent of the BRICK line on BOTH glaciers and ice sheets.

⚠⚠ HORIZON. FACTS is configured to pyear_end 2150 and does NOT reach 2300. It therefore
CANNOT speak to SLEIP's 2300 headline. Everything here is 2100/2150 and must be compared
against Ladrillo/BRICK AT THOSE YEARS, never against their 2300 numbers.

⭐ THE PAIRING IS EXACT. FACTS is deterministic on the non-emu workflows (default_rng(1234)):
two identical runs are bit-identical, and both arms draw the SAME 200 FaIR configs in the same
order ([CONFIG-AXIS] in build_shared_climate_nc.py). So sample i in the two arms shares its
climate config AND its module RNG draws, and the paired difference cancels structural
ice-sheet noise EXACTLY rather than approximately (memory facts_install_scope).

⚠ ssp534overMATCH is IDEALISED -- never quote it as SSP5-3.4-OS.
"""
import os, sys, numpy as np, netCDF4 as nc4

REPO = os.path.dirname(os.path.abspath(__file__))
REF, OVR = "ssp126nomarker", "ssp534overMATCH"
WORKFLOWS = ["wf1f", "wf2f", "wf3f", "wf4"]
WF_LABEL = {"wf1f": "wf1f IPCC AR5",  "wf2f": "wf2f LARMIP-2",
            "wf3f": "wf3f DeConto/Kopp", "wf4": "wf4 Bamber SEJ"}
HORIZONS = [2100, 2150]
MM_TO_CM = 0.1
## Ladrillo / BRICK 2.0 on the SAME matched pair, from diag_matched_dt_penalty.csv (paired median, cm).
LAD = {2100: 4.046, 2150: 3.318}
BRK = {2100: 3.631, 2150: 3.345}

def total(key, wf):
    p = os.path.join(REPO, "experiments", "global.shared.%s.n200" % key, "output",
                     "global.shared.%s.n200.total.workflow.%s.global.nc" % (key, wf))
    if not os.path.exists(p): return None, None
    d = nc4.Dataset(p)
    return d.variables["sea_level_change"][:, :, 0] * MM_TO_CM, d.variables["years"][:]

print("=" * 92)
print("FACTS ON THE MATCHED-dT OVERSHOOT PAIR — paired penalty, cm")
print("  %s minus %s   n=200, paired sample-for-sample" % (OVR, REF))
print("  ⚠ FACTS STOPS AT 2150 — it cannot address SLEIP's 2300 headline.")
print("=" * 92)
print("  %-20s%12s%10s%10s%10s%10s" % ("workflow", "horizon", "median", "mean", "p05", "p95"))
out = {}
for wf in WORKFLOWS:
    A, ya = total(OVR, wf); B, yb = total(REF, wf)
    if A is None or B is None: print("  [SKIP] %s" % wf); continue
    assert np.array_equal(ya, yb) and A.shape == B.shape, "axis/shape mismatch %s" % wf
    D = A - B
    for H in HORIZONS:
        i = int(np.where(ya == H)[0][0])
        x = np.asarray(D[:, i])
        out[(wf, H)] = float(np.median(x))
        print("  %-20s%12d%10.3f%10.3f%10.3f%10.3f"
              % (WF_LABEL[wf], H, np.median(x), x.mean(), np.percentile(x, 5), np.percentile(x, 95)))

print("\n" + "=" * 92)
print("AGAINST THE BRICK-LINEAGE MODELS ON THE SAME PAIR (paired median, cm)")
print("=" * 92)
print("  %-22s%12s%12s" % ("", "@2100", "@2150"))
print("  %-22s%12.2f%12.2f" % ("Ladrillo L24", LAD[2100], LAD[2150]))
print("  %-22s%12.2f%12.2f" % ("BRICK 2.0", BRK[2100], BRK[2150]))
for wf in WORKFLOWS:
    if (wf, 2100) in out:
        print("  %-22s%12.2f%12.2f" % (WF_LABEL[wf], out[(wf, 2100)], out[(wf, 2150)]))
if out:
    fv = [out[(w, 2150)] for w in WORKFLOWS if (w, 2150) in out]
    print("\n  FACTS spread @2150: %.2f to %.2f cm across %d workflows; "
          "Ladrillo %.2f, BRICK 2.0 %.2f" % (min(fv), max(fv), len(fv), LAD[2150], BRK[2150]))
