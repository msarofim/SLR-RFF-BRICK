"""diag_ais_region_lit_check.py — is an EAIS/WAIS/APIS partition SCORABLE?

The Antarctic analogue of `diag_gis_basin_lit_check.py`. Before any AIS split can
be priced, three things have to hold, and this script tests them in order:

  [1] CLOSURE  — the three regions must sum to the whole-sheet series IMBIE also
      publishes. If they do not, "shares of the total" is ambiguous before the
      model is even involved.
  [2] DENOMINATOR — the scored windows must have a total rate far enough from zero
      that a SHARE is well defined. This is the block-1c treatment that saved the
      Greenland term: EAIS is near zero and can flip sign, so a window where the
      regions cancel produces a vanishing denominator and an exploding share.
  [3] STABILITY — the partition must be stable enough across windows that a
      static-share term is not fitting noise. Greenland's shares moved ~0.05 over
      two windows and were scored at sigma = 0.05; anything much larger here means
      a static term is the wrong shape.

Sign convention: IMBIE "mass balance" is Gt/yr of MASS (negative = loss). Shares
are computed on MASS LOSS (the negated rate) so they are directly comparable with
`GISB_SHARE` in calibrate_mcmc_ext.jl.

    python python/diag_ais_region_lit_check.py
"""
import numpy as np, pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data/observations/raw"
# Windows: the two the Greenland term uses, plus the full IMBIE record and the
# satellite-gravimetry era, so a window choice cannot be tuned after the fact.
WINDOWS = [(2002, 2011), (2012, 2018), (1992, 2020), (2002, 2020)]
REGIONS = {"EAIS": "east_antarctica", "WAIS": "west_antarctica", "APIS": "antarctic_peninsula"}
WHOLE   = "antarctica"
# The share sigma the Greenland shares term uses; the stability test is read against it.
GISB_SHARE_SD  = 0.05
# A window is unscorable if |total loss rate| falls below this. Set at the level
# where a 0.05 share error would need a >20% rate error to matter.
RATE_FLOOR_GT  = 20.0

def load(stem):
    d = pd.read_csv(RAW / f"imbie_{stem}_2021_Gt.csv")
    d.columns = ["year", "rate", "rate_sd", "cum", "cum_sd"]
    return d

reg   = {k: load(v) for k, v in REGIONS.items()}
whole = load(WHOLE)

print(f"IMBIE-3 / Otosaka 2023 regional partition — scorability check")
print(f"  files: imbie_{{{','.join(REGIONS.values())},{WHOLE}}}_2021_Gt.csv")
print(f"  coverage {whole.year.min():.4f}–{whole.year.max():.4f}, {len(whole)} monthly steps\n")

# ---- [1] closure ---------------------------------------------------------
print("[1] CLOSURE — do the three regions sum to the published whole sheet?")
yrs = whole.year.values
assert all(np.allclose(r.year.values, yrs) for r in reg.values()), "year grids differ"
s_rate = sum(r.rate.values for r in reg.values())
s_cum  = sum(r.cum.values for r in reg.values())
for lab, s, w in (("rate (Gt/yr)", s_rate, whole.rate.values),
                  ("cumulative (Gt)", s_cum, whole.cum.values)):
    resid = s - w
    scale = np.max(np.abs(w))
    print(f"    {lab:18s} max|sum-whole| = {np.max(np.abs(resid)):10.4f}   "
          f"rel. to max|whole| ({scale:.1f}) = {np.max(np.abs(resid))/scale:.2e}")
closed = np.max(np.abs(s_cum - whole.cum.values)) / np.max(np.abs(whole.cum.values)) < 1e-3
print(f"    => {'CLOSES' if closed else 'DOES NOT CLOSE — shares are ambiguous'}\n")

# ---- [2]+[3] windowed shares ---------------------------------------------
print("[2] DENOMINATOR + [3] STABILITY — mass-loss shares by window")
print(f"    (loss = -rate; window mean of the monthly rate; floor {RATE_FLOOR_GT:.0f} Gt/yr)\n")
print(f"    {'window':12s} {'total loss':>12s} {'EAIS':>8s} {'WAIS':>8s} {'APIS':>8s}  scorable")
rows = {}
for w in WINDOWS:
    m = (whole.year >= w[0]) & (whole.year < w[1] + 1)
    loss = {k: -reg[k].rate.values[m].mean() for k in REGIONS}
    tot  = sum(loss.values())
    sh   = {k: loss[k] / tot for k in REGIONS}
    rows[w] = sh
    ok = abs(tot) >= RATE_FLOOR_GT
    print(f"    {w[0]}-{w[1]:<7d} {tot:12.2f} " +
          " ".join(f"{sh[k]:8.3f}" for k in REGIONS) +
          f"  {'YES' if ok else 'NO — denominator too small'}")

print(f"\n    drift across the two Greenland-term windows (2002-2011 -> 2012-2018):")
a, b = rows[(2002, 2011)], rows[(2012, 2018)]
worst = 0.0
for k in REGIONS:
    d = b[k] - a[k]
    worst = max(worst, abs(d))
    print(f"      {k:5s} {a[k]:6.3f} -> {b[k]:6.3f}   delta {d:+.3f}   "
          f"= {abs(d)/GISB_SHARE_SD:5.2f} x the sigma=0.05 the GIS term uses")
print(f"\n    worst drift {worst:.3f} = {worst/GISB_SHARE_SD:.2f} sigma.")
print("    A STATIC shares term is only defensible if this is well under 1 sigma —")
print("    Greenland's was (mid moved 0.055 = 1.1 sigma and the term still passed at")
print("    1.08 sigma because the model reproduced the LEVEL, not the trend).")

# ---- [4] the alternative: score ABSOLUTE rates, not shares ---------------
# Closure passing means absolute per-region rates are a legitimate target — the
# option Greenland did NOT have (Mouginot's sector sum disagreed with the
# calibration total by 1.227x, which is what forced shares-only there). But an
# absolute target is only worth adding if the datum is far from zero relative to
# its OWN published uncertainty, so that is the last test.
print("\n[4] ABSOLUTE per-region loss rates — is each one distinguishable from zero?")
print("    (window-mean of the monthly rate and of the published uncertainty)\n")
print(f"    {'window':12s} {'region':6s} {'loss Gt/yr':>11s} {'sigma':>9s} {'|loss|/sigma':>13s}")
for w in WINDOWS:
    m = (whole.year >= w[0]) & (whole.year < w[1] + 1)
    for k in REGIONS:
        loss = -reg[k].rate.values[m].mean()
        sd   = reg[k].rate_sd.values[m].mean()
        print(f"    {w[0]}-{w[1]:<7d} {k:6s} {loss:11.2f} {sd:9.2f} {abs(loss)/sd:13.2f}")
    tl = sum(-reg[k].rate.values[m].mean() for k in REGIONS)
    ts = whole.rate_sd.values[m].mean()
    print(f"    {'':12s} {'WHOLE':6s} {tl:11.2f} {ts:9.2f} {abs(tl)/ts:13.2f}")
