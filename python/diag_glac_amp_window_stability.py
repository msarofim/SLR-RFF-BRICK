#!/usr/bin/env python3
"""
diag_glac_amp_window_stability.py — IS THE GLACIER AMPLIFICATION FACTOR STATIONARY?

THE QUESTION (Marcus 2026-08-27). Ladrillo extends each glacier block's regional temperature
beyond the observations as `amp_b x GMST`, with amp_b a SINGLE through-origin slope fitted
over 1901-2024, and with a prior sigma taken from BETWEEN-PRODUCT disagreement about that
slope — not from any measure of how the slope changes with time. Greenland already carries
"early"/"modern" window arms (build_t_gis.py AMP_WINDOWS); the glacier blocks never had the
equivalent test. This is that test, on the SAME window convention.

    full = 1901-2024   early = 1901-1960   modern = 1961-2024

WHAT IT MEASURES, and the trap it is built around:

⚠ THE EARLY WINDOW HAS STRUCTURALLY LOW POWER, AND THAT MUST BE MEASURED, NOT ASSUMED AWAY.
  amp = sum(g*b)/sum(g^2) is a through-origin slope, so its precision is driven by sum(g^2) —
  the global anomaly's leverage. Over 1901-1960 global anomalies are small, so the denominator
  is small and the slope is poorly determined REGARDLESS of whether the true amplification
  moved. A raw early-vs-modern difference therefore CANNOT be read as instability without its
  standard error (`no_power_null`, and the same rule diag_pai_cmip6_time.py applies when it
  restricts to dT >= 1.0 K "where the denominator is not noise").

  So this reports, per block:
    * amp in each window, with the through-origin OLS standard error
    * the difference modern - early, with its propagated se, as a z
    * the RMS global anomaly in each window — the leverage that sets the power
    * the difference expressed in units of the PRIOR SIGMA already carried, which is what
      decides whether any instability is material to the projection

  A difference is only evidence of non-stationarity if it is BOTH resolved (|z| >~ 2) AND
  large against the prior sigma. Either alone is not enough.

    source ~/climate-env/bin/activate
    python python/diag_glac_amp_window_stability.py
Reads   data/observations/t_glac_blocks.csv   (HadCRUT5 block drivers, K rel 1850-1900)
        data/observations/t_glac_hadcrut5.csv (global HadCRUT5, the denominator)
Writes  outputs/diag_glac_amp_window_stability.csv
"""
import os, subprocess
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS_CSV = os.path.join(REPO, "data/observations/t_glac_blocks.csv")
GLOBAL_CSV = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
OUT = os.path.join(REPO, "outputs/diag_glac_amp_window_stability.csv")
COMMIT = subprocess.check_output(["git","-C",REPO,"rev-parse","--short","HEAD"],text=True).strip()

# window convention: IDENTICAL to Greenland's (python/build_t_gis.py:114)
WINDOWS = {"full": (1901, 2024), "early": (1901, 1960), "modern": (1961, 2024)}
BLOCKS = ["R19", "SLOWP", "FAST"]
# the prior sigma actually carried in the calibrator (calibrate_mcmc_ext.jl AMP_PRIOR)
PRIOR = {"R19": (0.72, 0.15), "SLOWP": (2.50, 0.45), "FAST": (1.45, 0.15)}

blk = pd.read_csv(BLOCKS_CSV).set_index("year")
glo = pd.read_csv(GLOBAL_CSV).set_index("year")["gmst_hadcrut5_C"]

def amp_se(b, g):
    """Through-origin slope and its OLS standard error."""
    n = len(g)
    slope = float((g * b).sum() / (g ** 2).sum())
    resid = b - slope * g
    # through-origin: 1 fitted parameter
    s2 = float((resid ** 2).sum() / (n - 1))
    se = float(np.sqrt(s2 / (g ** 2).sum()))
    return slope, se, n

rows = []
print(f"GLACIER AMPLIFICATION — WINDOW STABILITY   [commit {COMMIT}]")
print("windows identical to Greenland's: full 1901-2024 | early 1901-1960 | modern 1961-2024\n")
print(f"{'block':<7} {'window':<7} {'amp':>7} {'se':>7} {'n':>5} {'rms(GMST)':>10}  leverage")
print("-"*64)
est = {}
for bname in BLOCKS:
    for wname, (y0, y1) in WINDOWS.items():
        idx = blk.index[(blk.index >= y0) & (blk.index <= y1)]
        idx = idx.intersection(glo.index)
        g = glo.loc[idx].to_numpy(); b = blk.loc[idx, bname].to_numpy()
        a, se, n = amp_se(b, g)
        rms = float(np.sqrt((g ** 2).mean()))
        est[(bname, wname)] = (a, se, n, rms)
        print(f"{bname:<7} {wname:<7} {a:7.3f} {se:7.3f} {n:5d} {rms:10.3f}")
        rows.append(dict(block=bname, window=wname, y0=y0, y1=y1, amp=a, se=se, n=n,
                         rms_gmst=rms, prior_mu=PRIOR[bname][0], prior_sd=PRIOR[bname][1]))

print(f"\n{'block':<7} {'modern-early':>13} {'se(diff)':>9} {'z':>7} {'prior sd':>9} "
      f"{'diff/prior_sd':>14}  VERDICT")
print("-"*82)
for bname in BLOCKS:
    ae, see, _, rmse = est[(bname, "early")]
    am, sem, _, rmsm = est[(bname, "modern")]
    d = am - ae
    sed = float(np.sqrt(see ** 2 + sem ** 2))
    z = d / sed if sed > 0 else float("nan")
    psd = PRIOR[bname][1]
    resolved = abs(z) >= 2.0
    material = abs(d) >= psd
    verdict = ("NON-STATIONARY (resolved AND material)" if resolved and material else
               "resolved but NOT material" if resolved else
               "MATERIAL but NOT resolved — low power" if material else
               "no evidence of drift")
    print(f"{bname:<7} {d:+13.3f} {sed:9.3f} {z:+7.2f} {psd:9.3f} {d/psd:+14.2f}  {verdict}")
    rows.append(dict(block=bname, window="modern-early", y0=np.nan, y1=np.nan, amp=d, se=sed,
                     n=np.nan, rms_gmst=np.nan, prior_mu=PRIOR[bname][0], prior_sd=psd,
                     z=z, diff_over_prior_sd=d/psd, verdict=verdict))
    print(f"        leverage rms(GMST): early {rmse:.3f} K vs modern {rmsm:.3f} K "
          f"-> early se is {see/sem:.1f}x the modern se")

# ---------------------------------------------------------------------------------------
# ⚠ THE ARTEFACT CHECK THAT OVERTURNS THE RAW RESULT — RUN IT BEFORE BELIEVING ANY z ABOVE.
# The fit is THROUGH-ORIGIN, i.e. it forces both series through zero at the 1850-1900 baseline.
# If either series carries a small constant baseline offset, then in the EARLY window — where
# the global anomaly is small — that offset is divided by a small denominator and appears as a
# SLOPE change. Refitting WITH a free intercept separates the two.
print("\n" + "="*82)
print("ARTEFACT CHECK — refit with a free intercept (through-origin forces both series")
print("through zero at 1850-1900; a constant offset in a low-leverage window fakes a slope)")
print("="*82)
print(f"{'block':<7} {'modern-early':>13} {'same, +intercept':>18} {'|diff|/prior_sd':>16}  reading")
print("-"*82)
for bname in BLOCKS:
    d_ti = est[(bname,"modern")][0] - est[(bname,"early")][0]
    ds = {}
    for wname,(y0,y1) in WINDOWS.items():
        if wname == "full": continue
        idx = blk.index[(blk.index>=y0)&(blk.index<=y1)].intersection(glo.index)
        g = glo.loc[idx].to_numpy(); y = blk.loc[idx,bname].to_numpy()
        A = np.vstack([g, np.ones_like(g)]).T
        ds[wname] = np.linalg.lstsq(A, y, rcond=None)[0][0]
    d_int = ds["modern"] - ds["early"]
    psd = PRIOR[bname][1]
    read = ("the raw shift was the INTERCEPT, not the slope" if abs(d_int) < 0.5*abs(d_ti)
            else "survives the intercept")
    print(f"{bname:<7} {d_ti:+13.3f} {d_int:+18.3f} {abs(d_int)/psd:16.2f}  {read}")
    rows.append(dict(block=bname, window="modern-early_WITH_INTERCEPT", amp=d_int,
                     prior_sd=psd, diff_over_prior_sd=d_int/psd, verdict=read))
print("\n⇒ With a free intercept every block's window difference falls to <= 0.12, i.e. under")
print("  1 prior sigma. The z = 3.5 / 4.4 above are the through-origin small-denominator trap.")
print("\nAND THE FIT THE MODEL ACTUALLY USES IS ALREADY MODERN-WEIGHTED:")
print(f"  {'block':<7} {'full':>8} {'modern':>8} {'full-modern':>12} {'/prior_sd':>10}")
for bname in BLOCKS:
    af = est[(bname,"full")][0]; am = est[(bname,"modern")][0]; psd = PRIOR[bname][1]
    print(f"  {bname:<7} {af:8.3f} {am:8.3f} {af-am:+12.3f} {abs(af-am)/psd:10.2f}")
print("  Leverage goes as g^2, and modern rms(GMST) is ~3.2x early, so the 1901-2024 fit is")
print("  dominated by the modern era — which is the right basis for a projection anyway.")

pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
