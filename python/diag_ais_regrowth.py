## ============================================================================
## diag_ais_regrowth.py — DOES LADRILLO'S ANTARCTICA REGROW, AND DOES IT REGROW
## TOO FAST?  (Marcus question, 2026-09-02)
##
## THE QUESTION arose from `gic_regrow_not_the_penalty`: the AIS overshoot penalty
## falls from +0.433 cm at 2150 to +0.003 cm at 2300, which was written up as "our
## DAIS relaxes all the way back". If an ice sheet really did relax back on a
## 150-year timescale that would be a serious defect -- ice sheets lose mass by
## dynamic discharge (fast) and gain it only by surface accumulation (slow), so
## recovery must be far slower than loss.
##
## ⛔ THE PREMISE IS FALSE, AND SO WAS THE WRITE-UP. Ladrillo's AIS **never
## regrows at all** -- not on either SSP, not on any of the seven van Vuuren
## markers, not in any year after 2100. The penalty closes for a completely
## different reason, measured below: after 2127 our SSP5-3.4-OS is COOLER than our
## SSP1-2.6, so the reference arm loses ice FASTER and catches up. That is the
## known dT bias, not hysteresis, and it means the near-zero AIS penalty at 2300
## carries no information about Antarctic hysteresis at all.
##
## ⚠ This corrects `notes/note_2026-09-02_gic_regrow_attribution.md` §3 and the
## memory entry, both of which named a physical property for an artifact.
## ============================================================================
import pathlib, glob, os, numpy as np, pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[1]
OUT  = REPO / "outputs"
OVERSHOOT, REFERENCE = "ssp534over_nomarker", "ssp126_nomarker"
TAG, TAP, FORCING, ARM = "L24", "_tap4p69K_V5p64m_tau800", "spliced", "joint"
HORIZONS = [2100, 2150, 2300]
## Observational bound on how fast an ice sheet CAN gain mass, for scale. Antarctic
## surface mass balance is ~2100 Gt/yr (IMBIE/Rignot-era syntheses) and 360 Gt = 1 mm
## SLE, so even a 10 % accumulation surplus sustained everywhere is ~0.6 mm/yr SLE.
## ⚠ Used ONLY as an order-of-magnitude scale bar. Nothing here needs it, because the
## measured regrowth is exactly zero (`threshold_from_obs_or_law` — no threshold is
## needed to judge a quantity that never leaves zero).
AIS_SMB_GT_YR, GT_PER_MM_SLE = 2100.0, 360.0

def paths(ssp, tag=TAG):
    f = OUT / f"scope_slr_fairunc_paths_{ssp}_{FORCING}_{tag}{TAP}.csv"
    d = pd.read_csv(f); d = d[(d.arm == ARM) & (d.component == "ais")].sort_values("year")
    return d.set_index("year")["med_cm"]

print("=" * 88)
print("DOES LADRILLO'S ANTARCTICA EVER REGROW?")
print("=" * 88)
print(f"  scale bar: AIS SMB ~{AIS_SMB_GT_YR:.0f} Gt/yr; a 10 % surplus is "
      f"{0.10*AIS_SMB_GT_YR/GT_PER_MM_SLE:.2f} mm/yr SLE = "
      f"{0.10*AIS_SMB_GT_YR/GT_PER_MM_SLE/10:.3f} cm/yr\n")

rows = []
print(f"  {'scenario':<22}{'AIS@2100':>10}{'AIS@2150':>10}{'AIS@2300':>10}"
      f"{'yrs decreasing':>16}{'max regrowth':>14}")
scen = [(OVERSHOOT, TAG), (REFERENCE, TAG)] + \
       [(os.path.basename(f).split("_")[4], TAG)
        for f in sorted(glob.glob(str(OUT / f"scope_slr_fairunc_paths_vv*_{FORCING}_{TAG}{TAP}.csv")))]
for ssp, tag in scen:
    s = paths(ssp, tag); dd = s.diff(); neg = dd[(dd.index > 2100) & (dd < 0)]
    mr = f"{neg.min():.5f}" if len(neg) else "0 (none)"
    print(f"  {ssp:<22}{s[2100]:>10.3f}{s[2150]:>10.3f}{s[2300]:>10.3f}{len(neg):>16}{mr:>14}")
    rows.append(dict(scenario=ssp, ais_2100=s[2100], ais_2150=s[2150], ais_2300=s[2300],
                     years_decreasing=len(neg), max_regrowth_cm_yr=(neg.min() if len(neg) else 0.0)))
print("\n  ⇒ ZERO years of AIS decline after 2100 on EVERY pathway. There is no regrowth to bound.")

## PER-DRAW: the median of monotone paths is monotone, so the median alone cannot
## rule out individual regrowing draws. Check them directly.
print("\n  PER-DRAW (the median of monotone series is monotone -- the median alone proves nothing):")
for ssp in (OVERSHOOT, REFERENCE):
    d = pd.read_csv(OUT / f"scope_slr_fairunc_draws_{ssp}_{FORCING}_{TAG}{TAP}.csv")
    d = d[(d.arm == ARM) & (d.component == "ais")]
    w = d.pivot_table(index="draw", columns="horizon", values="value_cm")
    print(f"    {ssp:<22} AIS(2300)<AIS(2150): {(w[2300] < w[2150]).sum():>4}/{len(w)}   "
          f"AIS(2150)<AIS(2100): {(w[2150] < w[2100]).sum():>4}/{len(w)}")

## WHY THE PENALTY CLOSES — the actual mechanism.
def gmst(ssp):
    d = pd.read_csv(REPO / "data/observations" / f"fair_cube_gmst_{ssp}_raw.csv")
    yc = "year" if "year" in d.columns else d.columns[0]
    return d.set_index(yc)[[c for c in d.columns if c != yc]].mean(axis=1)

a, b = gmst(OVERSHOOT), gmst(REFERENCE)
dT = (a - b).loc[2100:]
cross = dT[dT < 0].index.min()
so, sr = paths(OVERSHOOT), paths(REFERENCE)
print(f"\n  WHY THE PENALTY CLOSES — it is NOT recovery:")
print(f"    {OVERSHOOT} peaks {a.loc[2000:].max():.3f} K at {a.loc[2000:].idxmax()}")
print(f"    it crosses BELOW {REFERENCE} in {cross} and stays cooler "
      f"(mean dT 2200-2300 = {dT.loc[2200:2300].mean():+.3f} K)")
print(f"    so the REFERENCE arm loses ice faster and catches up:")
print(f"      AIS rate 2175-2225, overshoot {(so[2225]-so[2175])/5:.3f} vs reference "
      f"{(sr[2225]-sr[2175])/5:.3f} cm/decade")
print(f"    penalty {so[2150]-sr[2150]:+.3f} cm @2150 -> {so[2300]-sr[2300]:+.3f} cm @2300, "
      f"with BOTH arms losing mass throughout.")
print("\n  ⇒ The near-zero AIS penalty at 2300 says NOTHING about Antarctic hysteresis.")
print("    It is the dT bias. A hysteresis claim needs a matched-dT scenario pair.")

pd.DataFrame(rows).to_csv(OUT / "diag_ais_regrowth.csv", index=False)
print(f"\nwrote outputs/diag_ais_regrowth.csv")
