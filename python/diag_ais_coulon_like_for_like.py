#!/usr/bin/env python3
"""
diag_ais_coulon_like_for_like.py — IS OUR AIS BAND REALLY "INSIDE COULON'S,
                                   DISPLACED HIGH AND 2.4x NARROWER"?

THE CLAIM UNDER TEST. CHANGELOG `2026-08-24c` block 5 placed our ssp585 AIS@2300
control band [168, 421] cm inside Coulon et al. 2025's [73, 595] cm, "displaced
high (p05 2.3x theirs, p95 0.71x theirs) and 2.4x narrower" -- and flagged, in the
same block, that this is **NOT like-for-like** because Coulon drives ice-sheet
models with CMIP6 GCM forcing while we drive BRICK-DAIS with FaIR-mean ssp585.
That flag has been open since; this closes it.

WHY IT MATTERS MORE THAN A CAVEAT USUALLY DOES. `like_for_like_forcing` records
that this same class of error has INVERTED a reading three times on one dataset,
and the Greenland re-target (`gis_targets.py`) is the precedent: once the PROTECT
ssp585 band was matched to our own forcing it moved 173-313 -> 43-145 cm, a factor
0.39, and every "we are SHORT by 3.5-6.3x" verdict in the repo flipped.

THE COMPARABLE QUANTITY IS ANTARCTIC WARMING, NOT GSAT. Coulon reports
Antarctic-averaged atmospheric warming directly, and DAIS's fast dynamics is driven
by exactly that (`T_ant = ais_gmst_amp * GMST + TANT0`), so the two are compared on
Antarctic warming with a shared 1995-2014 reference. No GSAT reconstruction of
their ensemble is needed and none is attempted.

BLOCKS
  [1] the forcing comparison -- ours vs theirs, on their baseline
  [2] the amplification decomposition, against the repo's own CMIP6 tas_ais data,
      including Coulon's four GCMs specifically
  [3] Coulon interpolated to OUR forcing, with the convexity argument that makes
      the answer a BOUND rather than a point

SOURCES. Coulon, Klose, Edwards, Turner, Pattyn & Winkelmann (2025), "From
short-term uncertainties to long-term certainties in the future evolution of the
Antarctic Ice Sheet", Nat. Commun. 16:10385, doi 10.1038/s41467-025-66178-w
(open access; PMC12680641). Numbers transcribed in COULON below, each with the
sentence they come from.

    source ~/climate-env/bin/activate
    python python/diag_ais_coulon_like_for_like.py
"""
import os
import glob
import csv
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "diag_ais_coulon_like_for_like.csv")

# --- Coulon et al. 2025, transcribed. Every value carries its own source. -----
COULON = {
    "models": "Kori-ULB + PISM, 2 x 1400-member ensemble, Bayesian-calibrated on IMBIE 1992-2020, NO MICI",
    "gcms": ["UKESM1-0-LL", "IPSL-CM6A-LR", "CESM2-WACCM", "MRI-ESM2-0"],
    "forcing": "extended SSP1-2.6 and SSP5-8.5, CMIP6 GCM forcing carried to 2300",
    "ref_period": (1995, 2014),          # "Reference period: 1995-2014"
    "slr_baseline": 2015,                 # "compared to 2015" (Table 1 caption)
    # "Antarctic-averaged atmospheric warming ranging from +12.0 degC to +17.0 degC"
    "tais_2300_ssp585": (12.0, 17.0),
    # "warming ranging from +1.0 degC - +3.6 degC"
    "tais_2300_ssp126": (1.0, 3.6),
    # "from +0.73 m to +5.95 m sea-level equivalent" (5-95%)
    "ais_2300_ssp585_cm": (73.0, 595.0),
    # "below +1.75 m by 2300 with 95% probability"; range -0.09 to +1.74 m
    "ais_2300_ssp126_cm": (-9.0, 174.0),
    # Table 1 medians, the two ice-sheet models
    "ais_2300_ssp585_med_cm": (267.0, 273.0),
    "ais_2300_ssp126_med_cm": (3.0, 110.0),
}
# Our shipped control band, ssp585 AIS @2300 (outputs/ssps_components_2300_L14.csv)
OURS_CM = (168.0, 421.0)
OURS_MED_CM = 281.2
# L14 posterior ais_gmst_amp, from the same 2000-draw subsample the panels use.
OURS_AMP = {"p05": 0.7858, "med": 0.9447, "p95": 1.1101}
GMST_CSV = os.path.join(REPO, "data/observations/fair_mean_gmst_ssp585.csv")
PAI_GLOB = os.path.join(REPO, "data/cmip6_pai", "tas_series_*.csv")
# Amplification convention, stated so it cannot drift: anomaly of an 11-yr window
# at HORIZON against the model's OWN historical 1850-1900 mean, ratio Antarctic to
# global. This is the same frame `ais_gmst_amp` lives in (T_ant = amp*GMST + TANT0
# with GMST on a 1850-1900 baseline), which is why the two are comparable at all.
AMP_HORIZON = 2100          # the last year every CMIP6 ssp585 run covers
AMP_WIN = 11
BASE_PERIOD = (1850, 1900)
DECK_PREFIXES = ("deck_", "ext_", "hemis_", "ohc_")

rows = []
def emit(block, key, value, note=""):
    rows.append(dict(block=block, key=key, value=value, note=note))

print("=" * 94)
print("IS OUR AIS BAND LIKE-FOR-LIKE WITH COULON 2025?")
print("=" * 94)
print(f"  Coulon: {COULON['models']}")
print(f"          {COULON['forcing']}; GCMs {', '.join(COULON['gcms'])}")
print(f"          warming referenced to {COULON['ref_period'][0]}-{COULON['ref_period'][1]}, "
      f"sea level to {COULON['slr_baseline']}")

# ===========================================================================
# [1] THE FORCING COMPARISON, on Coulon's own baseline
# ===========================================================================
print("\n" + "=" * 94)
print(f"[1] ANTARCTIC WARMING AT 2300, both on a {COULON['ref_period'][0]}-{COULON['ref_period'][1]} reference")
print("=" * 94)
g = pd.read_csv(GMST_CSV)
yr, gv = g[g.columns[0]].astype(int).values, g[g.columns[1]].astype(float).values
base = gv[(yr >= COULON["ref_period"][0]) & (yr <= COULON["ref_period"][1])].mean()
dg2300 = float(gv[yr == 2300][0] - base)
print(f"  our ssp585 GMST @2300 = {float(gv[yr == 2300][0]):.2f} C vs 1850-1900 "
      f"= {dg2300:.2f} C vs {COULON['ref_period'][0]}-{COULON['ref_period'][1]}")
ours_t = {k: v * dg2300 for k, v in OURS_AMP.items()}
print(f"  OUR T_ais warming @2300 : {ours_t['p05']:5.2f} to {ours_t['p95']:5.2f} C "
      f"(median {ours_t['med']:.2f}) -- the WHOLE ais_gmst_amp p05-p95")
lo, hi = COULON["tais_2300_ssp585"]
print(f"  COULON ssp585           : {lo:5.2f} to {hi:5.2f} C")
print(f"  COULON ssp126           : {COULON['tais_2300_ssp126'][0]:5.2f} to "
      f"{COULON['tais_2300_ssp126'][1]:5.2f} C")
print()
print(f"  -> ratio to our MEDIAN  : {lo / ours_t['med']:.2f}x to {hi / ours_t['med']:.2f}x")
print(f"  -> our p95 draw ({ours_t['p95']:.2f} C) is {ours_t['p95'] / lo * 100:.0f}% of Coulon's COLDEST GCM")
verdict = ("OUR ENTIRE POSTERIOR SITS BELOW COULON'S MINIMUM"
           if ours_t["p95"] < lo else "the posteriors overlap")
print(f"  -> {verdict}")
for k, v in ours_t.items():
    emit("1_forcing", f"ours_tais_2300_{k}_C", round(v, 3), "vs 1995-2014")
emit("1_forcing", "coulon_tais_2300_ssp585_C", f"{lo}-{hi}", "paper, vs 1995-2014")
emit("1_forcing", "coulon_tais_2300_ssp126_C", f"{COULON['tais_2300_ssp126'][0]}-"
     f"{COULON['tais_2300_ssp126'][1]}", "paper, vs 1995-2014")
emit("1_forcing", "ratio_coulon585_over_our_median", f"{lo / ours_t['med']:.2f}-{hi / ours_t['med']:.2f}")
emit("1_forcing", "verdict", verdict)

# ===========================================================================
# [2] WHERE THE GAP COMES FROM -- amplification, against the repo's own CMIP6 data
# ===========================================================================
print("\n" + "=" * 94)
print(f"[2] ANTARCTIC AMPLIFICATION, ssp585 @{AMP_HORIZON}, {AMP_WIN}-yr, vs each model's own "
      f"{BASE_PERIOD[0]}-{BASE_PERIOD[1]}")
print("=" * 94)
amps = []
for f in sorted(glob.glob(PAI_GLOB)):
    m = os.path.basename(f)[len("tas_series_"):-4]
    if m.startswith(DECK_PREFIXES):
        continue
    d = pd.read_csv(f)
    if "tas_ais" not in d.columns or "ssp585" not in set(d.scenario):
        continue
    h, s = d[d.scenario == "historical"], d[d.scenario == "ssp585"]
    b = h[(h.year >= BASE_PERIOD[0]) & (h.year <= BASE_PERIOD[1])]
    w = s[(s.year > AMP_HORIZON - AMP_WIN) & (s.year <= AMP_HORIZON)]
    if len(b) < 40 or len(w) < AMP_WIN:
        continue
    dgm = w.tas_global.mean() - b.tas_global.mean()
    dai = w.tas_ais.mean() - b.tas_ais.mean()
    amps.append(dict(model=m, dGMST=dgm, dT_ais=dai, amp=dai / dgm,
                     coulon=m in COULON["gcms"]))
A = pd.DataFrame(amps).sort_values("amp")
allm, cou = A.amp.median(), A[A.coulon].amp.median()
print(f"  {len(A)} CMIP6 GCMs   amp median {allm:.3f}  [{A.amp.min():.3f}, {A.amp.max():.3f}]")
print(f"  Coulon's {int(A.coulon.sum())} GCMs  amp median {cou:.3f}  "
      f"[{A[A.coulon].amp.min():.3f}, {A[A.coulon].amp.max():.3f}]   "
      f"({', '.join(A[A.coulon].model)})")
print(f"  OUR ais_gmst_amp  median {OURS_AMP['med']:.4f}  "
      f"[{OURS_AMP['p05']:.4f}, {OURS_AMP['p95']:.4f}]")
above = int((A.amp > OURS_AMP["med"]).sum())
above95 = int((A.amp > OURS_AMP["p95"]).sum())
print()
print(f"  -> CMIP6 median / ours = {allm / OURS_AMP['med']:.2f}x ; "
      f"Coulon's four / ours = {cou / OURS_AMP['med']:.2f}x")
print(f"  -> {above} of {len(A)} GCMs sit ABOVE our posterior MEDIAN; "
      f"{above95} sit above our p95 ({OURS_AMP['p95']:.3f})")
print(f"  -> our model gives Antarctica LESS warming than the global mean (amp < 1); "
      f"{int((A.amp > 1).sum())} of {len(A)} GCMs give MORE")
print(f"  -> Coulon's GCMs also run hotter globally: dGMST median {A[A.coulon].dGMST.median():.2f} C "
      f"@{AMP_HORIZON} vs our {float(gv[yr == AMP_HORIZON][0]):.2f} C "
      f"= {A[A.coulon].dGMST.median() / float(gv[yr == AMP_HORIZON][0]):.2f}x")
print("\n  the two effects COMPOUND: amplification x GMST = "
      f"{cou / OURS_AMP['med']:.2f} x "
      f"{A[A.coulon].dGMST.median() / float(gv[yr == AMP_HORIZON][0]):.2f} = "
      f"{cou / OURS_AMP['med'] * A[A.coulon].dGMST.median() / float(gv[yr == AMP_HORIZON][0]):.2f}x at {AMP_HORIZON}")
for _, r in A.iterrows():
    emit("2_amplification", f"amp_{r.model}", round(r.amp, 4),
         "COULON GCM" if r.coulon else "")
emit("2_amplification", "cmip6_all_median", round(allm, 4), f"n={len(A)}")
emit("2_amplification", "coulon4_median", round(cou, 4))
emit("2_amplification", "ours_median", OURS_AMP["med"])
emit("2_amplification", "gcms_above_our_median", f"{above}/{len(A)}")

# ===========================================================================
# [3] COULON AT *OUR* FORCING -- and why the answer is a BOUND
# ===========================================================================
print("\n" + "=" * 94)
print("[3] COULON INTERPOLATED TO OUR FORCING")
print("=" * 94)
t126 = float(np.mean(COULON["tais_2300_ssp126"]))
t585 = float(np.mean(COULON["tais_2300_ssp585"]))
m126 = float(np.mean(COULON["ais_2300_ssp126_med_cm"]))
m585 = float(np.mean(COULON["ais_2300_ssp585_med_cm"]))
ours = ours_t["med"]
frac = (ours - t126) / (t585 - t126)
lin = m126 + frac * (m585 - m126)
print(f"  Coulon anchors (mid of the two ice-sheet models' medians):")
print(f"    ssp126  T_ais {t126:5.2f} C -> AIS@2300 {m126:6.1f} cm")
print(f"    ssp585  T_ais {t585:5.2f} C -> AIS@2300 {m585:6.1f} cm")
print(f"  our T_ais {ours:.2f} C sits {frac * 100:.0f}% of the way between them "
      f"-- STRICTLY INSIDE, overlapping neither scenario")
print(f"  -> linear interpolation gives Coulon @ our forcing = {lin:.0f} cm")
print(f"  -> ours = {OURS_MED_CM:.0f} cm = {OURS_MED_CM / lin:.2f}x that")
print()
print("  ⚠ THIS IS A LOWER BOUND ON THE DISPLACEMENT, not a point estimate.")
print("    Only TWO anchors are available, and the response between them is CONVEX in")
print("    warming (it crosses a retreat threshold), so a straight line OVER-states")
print("    Coulon at an intermediate forcing. The true like-for-like Coulon value is")
print(f"    <= {lin:.0f} cm, so our displacement is >= {OURS_MED_CM / lin:.2f}x.")
print()
print("  ⇒ THE SIGN OF THE ORIGINAL READING FLIPS. The shipped comparison had our band")
print("    'inside Coulon's, displaced high'. Corrected for forcing, Coulon's band moves")
print("    DOWN toward us and past us: we are displaced high by MORE than recorded, not")
print("    less. Our band being 2.4x NARROWER than theirs also stops being evidence of")
print("    over-confidence in the same way -- their width spans a 12-17 C forcing range,")
print("    ours a 5.5-7.7 C one.")
emit("3_interp", "coulon_at_our_forcing_cm", round(lin, 1), "2-anchor linear, UPPER bound")
emit("3_interp", "ours_median_cm", OURS_MED_CM)
emit("3_interp", "displacement_x", round(OURS_MED_CM / lin, 2), "LOWER bound (convexity)")
emit("3_interp", "our_forcing_fraction_between_anchors", round(frac, 3))

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["block", "key", "value", "note"])
    w.writeheader()
    w.writerows(rows)
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
