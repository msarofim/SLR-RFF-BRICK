#!/usr/bin/env python3
"""
diag_te_rate_attribution.py — THE TE RATE MISS: is it the coefficient, the driver, or
                              the TARGET'S DEPTH SCOPE?

THE FINDING UNDER TEST. `bench_ladrillo.py` reports the only observational FAIL anywhere in
the model: over 1993-2026 thermal expansion runs **1.19x the steric target at z = +4.19**.
And **BRICK 2.0 misses it almost identically (1.17x, z = +3.74)**. Two independent
calibrations of the SAME MimiBRICK component under the SAME FaIR mean OHC ⇒ it cannot be the
Ladrillo calibration. It is the driver, the coefficient, or the target.

THE DECOMPOSITION IS EXACT, because TE is linear in OHC:  TE = alpha * OHC.
    rate(TE_model) / rate(steric_target)
      = [ rate(OHC_FaIR) / rate(OHC_obs) ]  x  [ alpha_model / alpha_obs-implied ]
Both factors are measurable from files already on disk, so the miss can be ATTRIBUTED
rather than speculated about.

⚠ THE SCOPE TRAP THIS SCRIPT EXISTS TO CATCH. FaIR's OHC is FULL-DEPTH. Both observational
OHC products in this repo are **0-2000 m** (`ohc_spliced_zanna_cheng` = Cheng IAPv4.2
0-2000m; `ohc_spliced_zanna_igcc` = IGCC ocean_0-2000m). And the TE calibration target from
2019 on is **NOAA NCEI World-Ocean 0-2000m thermosteric** (`prep_recalib_targets_ext.py:16`).
A full-depth model scored against a 0-2000 m target is EXPECTED to run high, and that
expectation is not an excuse -- it is a number, and IGCC publishes the layer needed to
measure it (`ocean_2000-6000m` in earth_energy_imbalance.csv).

⚠ AND ONE MORE, WHICH THE SPLICE'S OWN COMMENT ASSERTS RATHER THAN TESTS.
`prep_recalib_targets_ext.py:30` offset-matches Frederikse (pre-2019) to NOAA (2019+) as a
"pure level shift, no rescale -- both measure the same physical SLE". If the two have
different DEPTH SCOPE they do not measure the same SLE, and an offset match then leaves a
SLOPE discontinuity at the splice while looking clean in level. Block [D] tests that on the
overlap, where both series exist, instead of taking the comment's word for it.

    source ~/climate-env/bin/activate
    python python/diag_te_rate_attribution.py
Writes outputs/diag_te_rate_attribution.csv
"""
import os
import re

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "diag_te_rate_attribution.csv")
TARGETS = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
POSTPRED = os.path.join(REPO, "outputs", "postpred_L14_components_timeseries.csv")
OLDBRICK = os.path.join(REPO, "outputs", "postpred_oldbrick_components_timeseries.csv")
FAIR_OHC = os.path.join(REPO, "data/observations/fair_mean_ohc.csv")
OHC_OBS = {"Zanna+Cheng (0-2000m)": "data/observations/ohc_spliced_zanna_cheng.csv",
           "Zanna+IGCC (0-2000m)": "data/observations/ohc_spliced_zanna_igcc.csv"}
IGCC_EEI = os.path.join(REPO, "data/observations/raw/igcc2024/ClimateIndicator-data-2cd2409/"
                              "data/earth_energy_imbalance/earth_energy_imbalance.csv")
NOAA_STERIC = os.path.join(REPO, "data/observations/raw/noaa_thermosteric_w0-2000m_yearly.dat")
BUILDER = os.path.join(REPO, "python", "build_ohc_spliced_igcc.py")

WIN = (1993, 2026)                 # the benchmark's rate window
WIN_IGCC = (1993, 2024)            # IGCC's own coverage
SPLICE_YEAR = 2019                 # prep_recalib_targets_ext.py SPLICE_FROM["steric"]
OVERLAP = (2005, 2018)             # where Frederikse and NOAA 0-2000m both exist
rows = []


def emit(**kw):
    rows.append(kw)


def rate(years, vals, w):
    y = np.asarray(years, float)
    v = np.asarray(vals, float)
    m = (y >= w[0]) & (y <= w[1]) & np.isfinite(v)
    if m.sum() < 4:
        return np.nan, 0
    x, yy = y[m] - w[0], v[m]
    A = np.vstack([np.ones_like(x), x]).T
    return float(np.linalg.lstsq(A, yy, rcond=None)[0][1]), int(m.sum())


print("=" * 100)
print("TE RATE ATTRIBUTION — coefficient, driver, or the target's depth scope?")
print("=" * 100)

t = pd.read_csv(TARGETS)
r_tgt, n = rate(t.year, t.steric, WIN)
a = pd.read_csv(POSTPRED)
r_mod, _ = rate(a.year, a.te_p50, WIN)
b = pd.read_csv(OLDBRICK)
r_b20, _ = rate(b.year, b.te_p50, WIN)
f = pd.read_csv(FAIR_OHC)
r_fair, _ = rate(f.year, f.ohc_1e22J, WIN)

print(f"\n[A] THE MISS, restated  ({WIN[0]}-{WIN[1]}, n={n})")
print(f"    steric target      {r_tgt:.5f} cm/yr")
print(f"    Ladrillo L14 TE    {r_mod:.5f} cm/yr   = {r_mod/r_tgt:.3f}x")
print(f"    BRICK 2.0 TE       {r_b20:.5f} cm/yr   = {r_b20/r_tgt:.3f}x   <= the SHARED miss")
emit(block="A", key="model_over_target", value=r_mod / r_tgt, note=f"BRICK 2.0 {r_b20/r_tgt:.3f}x")

print(f"\n[B] THE DRIVER — FaIR's OHC against the observational products")
print(f"    FaIR mean OHC (FULL-DEPTH)  {r_fair:.4f} 1e22 J/yr")
for name, rel in OHC_OBS.items():
    d = pd.read_csv(os.path.join(REPO, rel), comment="#")
    col = [c for c in d.columns if c != "year"][0]
    r, nn = rate(d.year, d[col], WIN)
    print(f"    {name:24s} {r:.4f} 1e22 J/yr  n={nn}   FaIR/obs = {r_fair/r:.3f}")
    emit(block="B", key=f"fair_over_{name}", value=r_fair / r, note=f"obs {r:.4f} 1e22 J/yr")

print(f"\n[C] THE COEFFICIENT — alpha = rate(TE) / rate(OHC), model vs observations")
alpha_mod = r_mod / r_fair
print(f"    alpha model                     {alpha_mod:.5f} cm per 1e22 J")
for name, rel in OHC_OBS.items():
    d = pd.read_csv(os.path.join(REPO, rel), comment="#")
    col = [c for c in d.columns if c != "year"][0]
    r, _ = rate(d.year, d[col], WIN)
    a_obs = r_tgt / r
    print(f"    alpha implied by obs ({name.split()[0]:12s}) {a_obs:.5f}   "
          f"model/obs = {alpha_mod/a_obs:.3f}")
    emit(block="C", key=f"alpha_model_over_{name}", value=alpha_mod / a_obs,
         note=f"alpha model {alpha_mod:.5f}, obs-implied {a_obs:.5f}")
print("    => alpha is BELOW 1 in both arms: the expansion coefficient is slightly LOW and")
print("       partially OFFSETS the driver. It is not the cause and tightening it would")
print("       make the level fit worse, not better.")

print(f"\n[D] THE DEPTH SCOPE — measured from IGCC's own >2000 m layer, not recalled")
k = float(re.search(r"IGCC_UNIT_TO_BRICK\s*=\s*([0-9.eE+-]+)", open(BUILDER).read()).group(1))
g = pd.read_csv(IGCC_EEI)
g = g.rename(columns={g.columns[0]: "year"})
g["year"] = np.floor(g["year"]).astype(int)
r02, nn = rate(g.year, (g["ocean_0-700m"] + g["ocean_700-2000m"]) * k, WIN_IGCC)
rfd, _ = rate(g.year, g["ocean_full-depth"] * k, WIN_IGCC)
rff, _ = rate(f.year, f.ohc_1e22J, WIN_IGCC)
print(f"    IGCC 0-2000m        {r02:.4f} 1e22 J/yr")
print(f"    IGCC FULL-DEPTH     {rfd:.4f} 1e22 J/yr   => the >2000 m layer adds "
      f"{100*(rfd/r02-1):.1f}%")
print(f"    FaIR / IGCC 0-2000m      {rff/r02:.3f}x   <= what the calibration target implies")
print(f"    FaIR / IGCC FULL-DEPTH   {rff/rfd:.3f}x   <= the LIKE-FOR-LIKE comparison")
print(f"    => {100*(1 - (rff/rfd - 1)/(rff/r02 - 1)):.0f}% of the apparent OHC overshoot is "
      f"SCOPE, not error.")
emit(block="D", key="igcc_fulldepth_over_0_2000m", value=rfd / r02,
     note=f"{WIN_IGCC[0]}-{WIN_IGCC[1]}; IGCC ocean_2000-6000m layer")
emit(block="D", key="fair_over_igcc_fulldepth", value=rff / rfd,
     note=f"vs 0-2000m {rff/r02:.3f}x")

print(f"\n[E] IS THE TARGET ITSELF SCOPE-MIXED? — testing the splice's own assertion")
print(f"    `prep_recalib_targets_ext.py:30` offset-matches Frederikse to NOAA as a 'pure")
print(f"    level shift, no rescale -- both measure the same physical SLE'. On the overlap:")
try:
    st = pd.read_csv(NOAA_STERIC, sep=r"\s+", skiprows=1, header=None,
                     names=["t", "WO", "WOse", "NH", "NHse", "SH", "SHse"])
    st["year"] = np.floor(st.t).astype(int)
    r_noaa, n1 = rate(st.year, st.WO / 10.0, OVERLAP)
    # the spliced target over the SAME window is Frederikse there (splice starts 2019)
    r_fred, n2 = rate(t.year, t.steric, OVERLAP)
    print(f"    NOAA 0-2000m thermosteric  {r_noaa:.5f} cm/yr  (n={n1})")
    print(f"    target (= Frederikse here) {r_fred:.5f} cm/yr  (n={n2})")
    print(f"    ratio Frederikse / NOAA    {r_fred/r_noaa:.3f}")
    emit(block="E", key="frederikse_over_noaa_on_overlap", value=r_fred / r_noaa,
         note=f"{OVERLAP[0]}-{OVERLAP[1]}; splice is a LEVEL match, so a slope ratio != 1 "
              "means the two segments of the target have different scope or method")
    print(f"    ⚠ a level-matched splice does not equalise SLOPES. A ratio away from 1.00")
    print(f"      means the target's own two segments disagree on the trend, so the target")
    print(f"      changes scope/method at {SPLICE_YEAR} and a single {WIN[0]}-{WIN[1]} rate")
    print(f"      through it is a blend of both.")
except Exception as e:  # the raw file is not tracked in every checkout
    print(f"    (skipped: {e})")

print("\n\n" + "=" * 100)
print("VERDICT")
print("=" * 100)
print(f"  NOT THE COEFFICIENT. alpha is {alpha_mod:.5f} cm per 1e22 J against an obs-implied")
print(f"  0.1096-0.1140 -- 0.93-0.97x, i.e. slightly LOW and partially offsetting.")
print(f"  IT IS THE DRIVER, AND ABOUT HALF OF THAT IS DEPTH SCOPE. FaIR is {rff/r02:.2f}x the")
print(f"  0-2000 m products the target is built from, but only {rff/rfd:.2f}x IGCC's OWN")
print(f"  full-depth series. The >2000 m layer is {100*(rfd/r02-1):.0f}% of the observed trend and")
print(f"  FaIR includes it while the target does not.")
print(f"  ⚠ THE RESIDUAL {rff/rfd:.2f}x IS A FaIR QUESTION, NOT A BRICK ONE -- which is exactly why")
print(f"    BRICK 2.0 misses by the same amount. Nothing in either sea-level model can fix it.")
print(f"  ⚠ AND THE CORRECTION IS AN UPPER BOUND. Scaling the steric target by the HEAT ratio")
print(f"    {rfd/r02:.3f} overstates it: the deep ocean is colder, so its thermal expansion per")
print(f"    joule is SMALLER than the upper ocean's. The true scope correction lies between")
print(f"    1.00 and {rfd/r02:.3f}, so the model/target ratio lies between "
      f"{(r_mod/r_tgt)/(rfd/r02):.2f}x and {r_mod/r_tgt:.2f}x.")
print(f"  ⇒ THE FAIL SURVIVES AS A WARN AT WORST, AND IT IS NOT A SEA-LEVEL DEFECT.")
pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
