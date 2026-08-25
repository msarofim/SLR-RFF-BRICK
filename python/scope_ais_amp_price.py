#!/usr/bin/env python3
"""
scope_ais_amp_price.py — PRICE `ais_gmst_amp` BEFORE REFITTING IT.

`npv_retires_tau`: price a knob against the deliverable BEFORE identifying it, and report
the RANKING of knobs rather than one knob's sensitivity. `ais_gmst_amp` came out of the
2026-08-25 AIS review as the only AIS parameter worth a refit -- rank 2 at BOTH scenarios
(+0.67 ssp245, +0.30 ssp585), the only one high-ranked in both, and unlike `antarctic_lambda`
it is not unconditionally prior-inert. This prices it.

WHAT amp IS. DAIS computes `T_ant = amp * GMST + T_ant0` with the paleo anchor
T_ant0 = -18.435 degC preserved (`ladrillo_projection.jl:815`). amp is the GMST -> Antarctic
polar amplification. Stock DAIS hard-codes 1.196 -- the inverted paleo EQUILIBRIUM
regression. The A6 prior replaced it with a TRANSIENT value, N(0.95, 0.10) on [0.70, 1.25],
from Xie et al. 2022 (Sci Rep 12:16548).

⚠ TWO OPEN PROBLEMS WITH THAT PRIOR, both measured 2026-07-22 (`pai_cmip6_time`) and both
still unresolved, which is why a refit was proposed:

  [FRAME] Xie's 0.95 is numerically a POLAR-CAP metric. A 6-model mask test reproduces it
          only with ALL points south of 60S including the Southern Ocean (cap60: 0.92/0.98).
          DAIS's temperature lineage is ice-core / CONTINENTAL, and the land-only PAI1 over
          34 CMIP6 models is 1.13 (ssp245) / 1.16 (ssp585). So the prior may be ~0.15 LOW
          -- 1.5 prior sd -- in DAIS's own reference frame.
  [STATE] Amplification is WARMING-LEVEL controlled, not constant: ~0.85-0.9 at 0.6-0.8 K,
          ~1.1 at 1.5-2 K, saturating at ~1.15-1.2 for 2-4 K -- i.e. at the DAIS
          equilibrium. A constant amp is wrong in SHAPE, not just in level.

WHY THE PRICING IS DONE THIS WAY. amp enters the projection through two channels:

  * THE THRESHOLD CHANNEL. Fast dynamics fires when T_ant clears
    `antarctic_temp_threshold`, so the GMST required is (threshold - T_ant0)/amp -- a CLOSED
    FORM in two sampled columns. No model run, and it is exact.
  * THE SMOOTH CHANNEL (runoff line, ocean forcing). This one is NOT free: amp correlates
    **r = 0.608** with `ais_runoff_Ton` in the posterior, a likelihood-induced compensation
    (more Antarctic warming needs more runoff-line offset to keep the historical mass
    balance). ⚠ SO amp IS NOT PRIOR-INERT THE WAY `antarctic_lambda` IS: its MARGINAL is a
    prior sample (posterior sd is **0.992x** the truncated prior sd) but its JOINT is not,
    and shifting it without a refit leaves `ais_runoff_Ton` tuned for the old amp.

⇒ THIS SCRIPT PRICES THE THRESHOLD CHANNEL EXACTLY AND SAYS SO. It is a LOWER BOUND on what
a refit would move, and it is the channel that dominates where the deficit is (ssp245, where
`antarctic_temp_threshold` is rank 1). Do not quote it as the refit's answer.

    source ~/climate-env/bin/activate
    python python/scope_ais_amp_price.py [--tag=L14]
Reads   data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv
        data/observations/fair_cube_gmst_<ssp>_raw.csv
Writes  outputs/scope_ais_amp_price_<TAG>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUT = os.path.join(REPO, "outputs", f"scope_ais_amp_price_{TAG}.csv")
POST = os.path.join(REPO, "data", "MimiBRICK",
                    f"parameters_subsample_brick_mengel_{TAG}.csv")
CUBE = os.path.join(REPO, "data", "observations", "fair_cube_gmst_{ssp}_raw.csv")

# The preserved DAIS paleo anchor, = -15.42/0.8365 (ladrillo_projection.jl:259).
TANT0 = -15.42 / 0.8365
SSPS = ["ssp126", "ssp245", "ssp585"]
HORIZONS = (2100, 2150, 2300)
# THE FORCING CONVENTION MUST MATCH THE REPORTED BAND. `diag_ais_tipping_under_forcing.jl`
# builds the SPLICED driver in line -- mean GMST through SPLICE_YEAR, then the config's own
# anomaly about its reference-window mean -- and evaluates the threshold INSTANTANEOUSLY at
# the horizon, because DAIS re-tests `T_ant > threshold` every year and does NOT latch.
# ⚠ A FIRST VERSION OF THIS SCRIPT USED THE RAW CUBE AND A RUNNING MAX ("ever tipped") AND
# GOT 6.5% WHERE THE COMMITTED DIAGNOSTIC SAYS 3.95%. Both were wrong: raw is not the
# reported convention (`ohc_splice_prov` / 2026-08-25c), and a latch is not the model.
SPLICE_YEAR = 2014
REF = (1995, 2014)               # LADRILLO_REF, the re-reference window
# ⚠ NO PAIRING SEED. The committed diagnostic assigns each draw ONE FaIR config under seed
# 2026; a FRACTION marginalised over the full draws x configs product has the SAME
# expectation with ZERO pairing noise, so the exact marginal is used and the paired value is
# reported beside it as the reproduction check.
# THE ARMS. Each is a value for amp, with the provenance that makes it a candidate.
ARMS = [
    ("posterior (shipped)", None,
     "the L14 posterior column as sampled; prior N(0.95, 0.10)"),
    ("Xie cap60 = the prior", 0.95,
     "Xie et al. 2022 as published -- reproduced only by a POLAR-CAP mask (cap60 0.92/0.98)"),
    ("land60 ssp245", 1.13,
     "34-model CMIP6 land-only PAI1, the mask matching DAIS's continental lineage"),
    ("land60 ssp585", 1.16, "same metric at ssp585"),
    ("DAIS equilibrium", 1.196,
     "the hard-coded stock map, = where the CMIP6 warming-level curve SATURATES at 2-4 K"),
]
rows = []


def main():
    p = pd.read_csv(POST)
    amp0 = p["ais_gmst_amp"].to_numpy(float)
    thr = p["antarctic_temp_threshold"].to_numpy(float)
    n = len(amp0)
    need = thr - TANT0                       # Antarctic warming required, per draw
    print("=" * 100)
    print(f"PRICING ais_gmst_amp — THRESHOLD CHANNEL, EXACT (tag {TAG}, {n} draws)")
    print("=" * 100)
    print(f"\n  posterior amp: median {np.median(amp0):.4f}  sd {amp0.std():.4f}  "
          f"[p05 {np.percentile(amp0,5):.4f}, p95 {np.percentile(amp0,95):.4f}]")
    print(f"  required Antarctic warming to tip: median {np.median(need):.3f} degC "
          f"[p05 {np.percentile(need,5):.3f}, p95 {np.percentile(need,95):.3f}]")

    # --------------------------------------------- [A] the crossing GMST, per arm
    print(f"\n[A] THE GMST REQUIRED TO TIP = (threshold - T_ant0) / amp")
    print(f"\n{'arm':24s} {'amp':>7s} {'crossing GMST (degC)':>28s}   provenance")
    base_med = None
    for lab, val, prov in ARMS:
        a = amp0 if val is None else np.full(n, val)
        gx = need / a
        med = float(np.median(gx))
        base_med = med if base_med is None else base_med
        print(f"{lab:24s} {np.median(a):7.3f} {med:9.3f} "
              f"[{np.percentile(gx,5):5.3f}, {np.percentile(gx,95):5.3f}]"
              f"  {med-base_med:+6.3f}   {prov[:44]}")
        rows.append(dict(block="A", arm=lab, ssp="", horizon="",
                         quantity="crossing_GMST_degC", value=med,
                         note=f"amp {np.median(a):.3f}; p05 {np.percentile(gx,5):.3f} "
                              f"p95 {np.percentile(gx,95):.3f}; delta vs shipped "
                              f"{med-base_med:+.3f} degC; {prov}"))
    print(f"\n    ⇒ moving amp from the shipped {np.median(amp0):.3f} to the continent-"
          f"referenced 1.13 lowers the\n      tipping threshold by "
          f"{np.median(need)/np.median(amp0) - np.median(need)/1.13:.3f} degC of GMST. "
          f"That is the whole price, and it is a\n      THRESHOLD move -- it changes WHICH "
          f"draws tip, not how fast a tipped draw goes.")

    # ------------------------------------------- [B] the tipped fraction, per arm and cell
    print(f"\n[B] TIPPED FRACTION under each arm — SPLICED driver, instantaneous at the "
          f"horizon,\n    marginalised over the full draws x configs product")
    for ssp in SSPS:
        g = pd.read_csv(CUBE.format(ssp=ssp))
        ycol = "year" if "year" in g.columns else g.columns[0]
        cfg_cols = [c for c in g.columns if c != ycol]
        gm = g.set_index(ycol)[cfg_cols]
        mean_g = pd.read_csv(os.path.join(REPO, "data", "observations",
                                          f"fair_mean_gmst_{ssp}.csv")).set_index("year")
        mcol = [c for c in mean_g.columns if "gmst" in c.lower()][0]
        mean_g = mean_g[mcol]
        iref = (gm.index >= REF[0]) & (gm.index <= REF[1])
        mref = float(mean_g[(mean_g.index >= REF[0]) & (mean_g.index <= REF[1])].mean())
        cref = gm[iref].mean(axis=0)                       # per-config reference mean
        print(f"\n  --- {ssp}  ({len(cfg_cols)} configs)")
        print(f"{'arm':24s} " + "  ".join(f"{h:>10d}" for h in HORIZONS))
        for lab, val, _ in ARMS:
            a = amp0 if val is None else np.full(n, val)
            cells = []
            for H in HORIZONS:
                if H not in gm.index:
                    cells.append(np.nan)
                    continue
                gH = (float(mean_g[H]) if H <= SPLICE_YEAR
                      else (mref + (gm.loc[H] - cref)).to_numpy(float))
                gH = np.atleast_1d(gH)
                # exact marginal over the draws x configs product, no pairing noise
                frac = float(np.mean(np.add.outer(a, np.zeros(len(gH))) *
                                     gH[None, :] + TANT0 > thr[:, None]))
                cells.append(frac)
                rows.append(dict(block="B", arm=lab, ssp=ssp, horizon=H,
                                 quantity="tipped_fraction", value=frac,
                                 note=f"amp {np.median(a):.3f}; spliced driver, "
                                      f"instantaneous; exact marginal over {n} draws x "
                                      f"{len(gH)} configs"))
            print(f"{lab:24s} " + "  ".join(f"{100*c:9.1f}%" for c in cells))
    print(f"\n  ⚠ THRESHOLD CHANNEL ONLY. The smooth channel (runoff line, ocean forcing) is "
          f"NOT priced\n    here and cannot be: amp correlates r = 0.608 with "
          f"`ais_runoff_Ton`, so a refit would move\n    both. These numbers are a LOWER "
          f"BOUND on what a refit would do.")
    # ------------------------------------------------ reproduction check + what it targets
    COMMITTED = {("ssp126", 2100): 0.0395, ("ssp126", 2150): 0.0375, ("ssp126", 2300): 0.0630,
                 ("ssp245", 2100): 0.3335, ("ssp245", 2150): 0.4465, ("ssp245", 2300): 0.4830,
                 ("ssp585", 2100): 0.9565,
                 ("ssp585", 2150): 0.9940, ("ssp585", 2300): 0.9915}
    print(f"\n[REPRO] the shipped arm against the committed "
          f"`diag_ais_tipping_under_forcing_{TAG}.csv` (per-draw config)")
    print(f"\n{'cell':16s} {'here':>8s} {'committed':>10s} {'diff':>8s}")
    worst = 0.0
    for (ssp, H), ref in COMMITTED.items():
        got = [r["value"] for r in rows if r["block"] == "B" and r["ssp"] == ssp and
               r["horizon"] == H and r["arm"] == "posterior (shipped)"]
        if not got:
            continue
        d = got[0] - ref
        worst = max(worst, abs(d))
        print(f"{ssp + '@' + str(H):16s} {100*got[0]:7.1f}% {100*ref:9.1f}% {100*d:+7.2f}pp")
    print(f"\n    max |diff| {100*worst:.2f}pp. ⚠ NOT expected to be zero: the committed file "
          f"assigns each\n    draw ONE config under seed 2026 and reads the chains; this is "
          f"the EXACT marginal over the\n    full product on the 10k subsample. Same "
          f"expectation, no pairing noise.")

    print(f"\n[C] WHAT A REFIT WOULD TARGET, and why this is not a marginal knob")
    print(f"""
    The AIS median deficit is concentrated at ssp245 -- 0.531x the literature at 2100 and
    0.406x at 2150, the two largest AIS median WARNs in the benchmark -- and
    `antarctic_temp_threshold` is RANK 1 there (`ais_spread_is_lambda_prior`), i.e. the
    binding question at ssp245 is WHICH DRAWS TIP. That is exactly the quantity amp moves:
    the continent-referenced frame takes the ssp245 tipped fraction from 33.1% to 59.7% at
    2100 and 44.5% to 69.2% at 2150, and ssp126 from 4.2% to 11.7%.

    ⚠ DO NOT READ A CORRECTED MEDIAN OFF THIS. The map from tipped fraction to median cm is
      not linear and the smooth channel moves too. What this establishes is the RANKING
      (`npv_retires_tau`): amp is the largest available lever on the one place the AIS is
      measurably weakest, and it is a lever with a MEASURED reason to move -- not a fit.

    ⚠ AND IT CUTS AGAINST A DECISION ALREADY TAKEN. The ssp126 tipped fraction was accepted
      at ~4% on 2026-08-25 as "not a dealbreaker unless the literature says otherwise". The
      literature that says otherwise is OUR OWN: 34 CMIP6 models under the mask matching
      DAIS's continental lineage put amp at 1.13-1.16, which triples that fraction. The
      acceptance stands on the CURRENT prior; it does not survive the frame correction.""")
    # ------------------------------------- [D] the warming level, which changes the diagnosis
    print(f"\n[D] ⚠ THE PROBLEM IS NOT THE PRIOR'S CENTRE. IT IS THAT amp IS CONSTANT.")
    print(f"\n    CMIP6 land-only amp is WARMING-LEVEL controlled (`pai_cmip6_time`, 34 models):")
    print(f"      ~0.85-0.90 at dT 0.6-0.8 K  ->  ~1.10 at 1.5-2 K  ->  ~1.15-1.20 at 2-4 K")
    print(f"      (i.e. it saturates AT the DAIS equilibrium 1.196 the A6 prior replaced)")
    print(f"\n{'':10s} {'calib 1900-2024':>16s} {'SMB anchor 1979-2008':>21s} "
          f"{'2100':>8s} {'2300':>8s}")
    for ssp in SSPS:
        g = pd.read_csv(os.path.join(REPO, "data", "observations",
                                     f"fair_mean_gmst_{ssp}.csv")).set_index("year")
        c = [x for x in g.columns if "gmst" in x.lower()][0]
        ser = g[c]
        ref = float(ser[(ser.index >= 1850) & (ser.index <= 1900)].mean())
        w = lambda a, b: float(ser[(ser.index >= a) & (ser.index <= b)].mean()) - ref
        print(f"{ssp:10s} {w(1900,2024):15.2f}K {w(1979,2008):20.2f}K "
              f"{w(2095,2105):7.2f}K {w(2290,2300):7.2f}K")
        rows.append(dict(block="D", arm="", ssp=ssp, horizon="",
                         quantity="warming_level_degC",
                         value=w(2095, 2105),
                         note=f"calib 1900-2024 {w(1900,2024):.2f} K; SMB anchor 1979-2008 "
                              f"{w(1979,2008):.2f} K; 2100 {w(2095,2105):.2f} K; "
                              f"2300 {w(2290,2300):.2f} K"))
    print(f"""
    ⇒ THE CALIBRATION LIVES AT 0.41-0.65 K AND THE PROJECTIONS AT 1.85-7.79 K -- a factor of
      3 to 12 in warming level, across a relationship the CMIP6 ensemble says RISES by ~0.3
      over exactly that range. A CONSTANT amp is being fitted where amp is low and applied
      where it is high.

    ⇒ SO RE-CENTRING THE CONSTANT PRIOR IS THE WRONG FIX, even though it would improve the
      projections. 1.13 is the FULL-PERIOD land-only value; it is NOT the historical value,
      and amp is jointly constrained with `ais_runoff_Ton` (r = 0.608) over exactly the
      historical window. Re-centring buys the ssp245 projection by mis-fitting the history
      that the same parameter is pinned by. A constant cannot be right at both ends.

    ⇒ THE FIX IS amp(dT) -- state-dependent, interpolating transient to equilibrium. That is
      a MODEL-FORM change, not a prior change, which puts it in the same category as the
      magnitude-dependent fast-dynamics fork: price it, build it as an arm, do not adopt it
      silently. ⚠ AND UNLIKE THAT FORK IT IS **NOT** LIKELIHOOD-INERT -- amp is active in the
      historical window through the smooth channel, so it CANNOT be prior-propagated onto
      the existing posterior. It needs a refit, and that is the honest cost.""")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
