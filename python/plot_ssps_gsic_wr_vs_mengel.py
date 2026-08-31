#!/usr/bin/env python3
"""Glacier (GSIC) melt to 2300 under all SSPs: Wigley-Raper (BRICK 2.0) vs Mengel — commitment + spread.

Same FaIR 2.2.4 SSP GMST drives all -- ENFORCED by the vintage gate below, which refuses to draw if the inputs disagree on the calibration. (b) WR keeps melting even where T plateaus/declines
(no finite equilibrium). (c) Mengel posterior stabilizes but its SCENARIO SPREAD is anomalously
compressed — the calibrated gic_b→0.89 (railed at its 1.0 bound) saturates S_eq by ~1.3 deg C; the
dashed b=0.52 counterfactual (Mengel-published b, a rescaled to keep each draw's historical a*b) restores
the physically-expected spread. Reads outputs/ssps_gsic_2300{,_mengel,_mengel_b052}.csv.
"""
import os
import subprocess
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

_SRC = {"WR (ssps_gsic_2300)":           "outputs/ssps_gsic_2300.csv",
        "Mengel (ssps_gsic_2300_mengel)": "outputs/ssps_gsic_2300_mengel.csv",
        "Mengel b052":                    "outputs/ssps_gsic_2300_mengel_b052.csv"}

## VINTAGE GATE, added 2026-08-30. THIS FIGURE'S WHOLE CLAIM IS "same GMST drives all",
## and on 2026-08-30 that stopped being true WITHOUT ANY EDIT TO THIS FILE:
## ssps_gsic_2300.csv was regenerated on calib 1.6.0 while the two Mengel arms stayed on
## 1.4.5 -- a 0.4266 K difference in the driver. A re-run would have silently produced a
## MIXED-VINTAGE comparison under a caption asserting a common driver.
## The gate reads the CAUSE: every input carries its own `gmst` column, so the forcing it
## was actually built on is checkable against the current fair_mean files -- no invented
## tolerance, no mtime guessing. It prints the row count it compared, so a gate that
## matches nothing cannot report a pass.
_LAB = {"SSP1-1.9": "ssp119", "SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245",
        "SSP4-6.0": "ssp460", "SSP3-7.0": "ssp370", "SSP5-8.5": "ssp585"}


def _forcing_delta(df):
    """max |file's own gmst - the CURRENT fair_mean gmst|, and how many rows matched."""
    d = df.drop_duplicates(["ssp", "year"])
    worst, n = 0.0, 0
    for ssp, g in d.groupby("ssp"):
        key = _LAB.get(ssp)
        if key is None:
            continue
        f = "data/observations/fair_mean_gmst_%s.csv" % key
        if not os.path.exists(f):
            continue
        m = pd.read_csv(f).set_index("year")["gmst_C"].reindex(g.year.values).values
        ok = ~np.isnan(m)
        if not ok.any():
            continue
        worst = max(worst, float(np.nanmax(np.abs(g.gmst.values[ok] - m[ok]))))
        n += int(ok.sum())
    return worst, n


_loaded = {k: pd.read_csv(v) for k, v in _SRC.items()}
_delta = {k: _forcing_delta(v) for k, v in _loaded.items()}
if any(n == 0 for _, n in _delta.values()):
    raise SystemExit("[VINTAGE] compared ZERO rows for an input -- vacuous, not passing: "
                     + str({k: n for k, (_, n) in _delta.items()}))
_w = [w for w, _ in _delta.values()]
if max(_w) - min(_w) > 1e-6:
    _lines = ["    %-34s delta vs current fair_mean = %.4f K  (%d rows)"
              % (k, w, n) for k, (w, n) in _delta.items()]
    raise SystemExit(
        "[VINTAGE] THE INPUTS ARE ON DIFFERENT FORCING VINTAGES, so 'same GMST drives all' "
        "is FALSE and this figure must not be drawn:" + "\n"
        + "\n".join(_lines) + "\n"
        + "  Regenerate the lagging arm(s) (julia/project_ssps_gsic_2300_mengel.jl) or point "
          "this figure at a matched set. Do NOT relax this gate.")
## ⚠ THE SPREAD TEST ALONE IS BLIND TO ARMS THAT ARE ALL STALE TOGETHER (found 2026-08-31
## by mutation-testing: pointing one marker at an SSP driver produced a 1.4074 K delta on
## EVERY arm and this gate still printed "all arms share a forcing vintage"). It compares
## the arms against EACH OTHER; if the driver is regenerated after all three were built,
## they go stale in lockstep and the spread stays zero. That is the same failure in its
## all-together form, so the ABSOLUTE delta is now checked as well
## (`two_statistics_can_be_blind`). Both figures measure 0.0000 K today, so this is inert
## now and can only fire on a real regeneration.
_ABS_TOL_K = 1e-6
if max(_w) > _ABS_TOL_K:
    raise SystemExit(
        "[VINTAGE] every arm AGREES WITH THE OTHERS but ALL are stale against the current "
        "fair_mean drivers by up to %.4f K, so 'same GMST drives all' is true of the arms "
        "and FALSE of the figure:\n" % max(_w)
        + "\n".join("    %-34s delta = %.4f K  (%d rows)" % (k, w, n)
                     for k, (w, n) in _delta.items())
        + "\n  Regenerate the arms against the current drivers. Do NOT relax this gate.")
print("[VINTAGE] all %d ARMS share a forcing vintage (delta vs current fair_mean = %.4f K)"
      % (len(_SRC), _w[0]))

## CROSS-SSP PROVENANCE GATE, added 2026-08-30. THE GATE ABOVE CANNOT SEE THIS.
## It compares each ARM against the CURRENT fair_mean file, so it proves the three arms
## agree with each other -- not that the six SSPs agree with each other. They do not.
## Only ssp126/245/585 have a calib 1.6.0 + CMIP7 cube (839a176, 2026-08-28); ssp119/370/460
## have no 1.6.0 emissions file and remain calib 1.4.5, RCMIP-native. So panel (c)'s headline
## "spread @2300" -- SSP5-8.5 minus SSP1-1.9 -- STRADDLES TWO CALIBRATIONS, and the caption
## used to assert a "single vintage" it had never checked. Measured cost of the split on that
## statistic: 0.11 cm of the posterior arm's 3.72 cm and 0.07 cm of the b=0.52 arm's 12.87 cm
## (1.4.5 -> 1.6.0 on ssp585 alone), i.e. ~3% and ~0.5%. Disclosed, not fatal.
## Declared as a NAMED CONSTANT so a future regeneration cannot change the mix silently:
## if someone builds ssp119 on 1.6.0 and does not update this table, the gate fires.
_DRIVER_PROVENANCE = {                       # ssp -> (commit that wrote fair_mean_gmst_<ssp>.csv, calib)
    "ssp119": ("f2b0a8d", "calib 1.4.5 / RCMIP-native"),
    "ssp126": ("839a176", "calib 1.6.0 / CMIP7-harmonized"),
    "ssp245": ("839a176", "calib 1.6.0 / CMIP7-harmonized"),
    "ssp370": ("f2b0a8d", "calib 1.4.5 / RCMIP-native"),
    "ssp460": ("f2b0a8d", "calib 1.4.5 / RCMIP-native"),
    "ssp585": ("839a176", "calib 1.6.0 / CMIP7-harmonized"),
}


def _driver_commit(ssp):
    """Short hash of the commit that last wrote this SSP's mean-GMST driver."""
    out = subprocess.run(["git", "log", "-1", "--format=%h", "--",
                          "data/observations/fair_mean_gmst_%s.csv" % ssp],
                         capture_output=True, text=True)
    return out.stdout.strip()


_actual = {s: _driver_commit(s) for s in _DRIVER_PROVENANCE}
_drift = {s: (_actual[s], c) for s, (c, _) in _DRIVER_PROVENANCE.items()
          if _actual[s] and not (_actual[s].startswith(c) or c.startswith(_actual[s]))}
if any(not v for v in _actual.values()):
    ## FATAL, not a warning. An "unverified" that still draws is the vacuous pass this gate
    ## exists to prevent -- caught by mutation-testing it against an untracked path.
    raise SystemExit(
        "[PROVENANCE] git returned nothing for %d of %d driver(s), so the calibration mix is "
        "UNVERIFIED and this figure must not be drawn: %s\n"
        "  Run from inside the SLR-RFF-BRICK checkout, with the drivers committed."
        % (sum(1 for v in _actual.values() if not v), len(_actual),
           sorted(s for s, v in _actual.items() if not v)))
elif _drift:
    raise SystemExit(
        "[PROVENANCE] a driver moved off its declared commit, so the calibration mix in this "
        "figure is not what _DRIVER_PROVENANCE says:\n"
        + "\n".join("    %-8s now %s, declared %s" % (s, a, d) for s, (a, d) in sorted(_drift.items()))
        + "\n  Update _DRIVER_PROVENANCE *and* the caption together. Do NOT drop this gate.")
else:
    _by_calib = {}
    for s, (_, cal) in _DRIVER_PROVENANCE.items():
        _by_calib.setdefault(cal, []).append(s)
    print("[PROVENANCE] %d drivers verified against declared commits; %d calibration(s) in this figure:"
          % (len(_actual), len(_by_calib)))
    for cal, ss in sorted(_by_calib.items()):
        print("    %-32s %s" % (cal, " ".join(sorted(ss))))
_MIXED = len({cal for _, cal in _DRIVER_PROVENANCE.values()}) > 1
_CALIB_NOTE = ("ssp126/245/585 calib 1.6.0 + CMIP7, ssp119/370/460 calib 1.4.5 (no 1.6.0 cube exists), "
               "so the 2300 spreads marked † straddle two calibrations"
               if _MIXED else "one calibration throughout")

WR, MEN, MENCF = (_loaded["WR (ssps_gsic_2300)"],
                  _loaded["Mengel (ssps_gsic_2300_mengel)"],
                  _loaded["Mengel b052"])
SSPS = ["SSP1-1.9","SSP1-2.6","SSP2-4.5","SSP4-6.0","SSP3-7.0","SSP5-8.5"]
COL = {"SSP1-1.9":"#00a9cf","SSP1-2.6":"#003466","SSP2-4.5":"#f69320",
       "SSP4-6.0":"#c8a000","SSP3-7.0":"#df0000","SSP5-8.5":"#7a0002"}
X0, X1 = 2000, 2300
# the spread is SSP5-8.5 minus SSP1-1.9 = a 1.6.0 endpoint minus a 1.4.5 one -- flag it on the label
_SPREAD_FLAG = " †" if _MIXED else ""

def series(df, ssp):
    d = df[df.ssp == ssp].sort_values("year"); m = (d.year >= X0)
    return d.year[m].values, d[m]

fig, ax = plt.subplots(4, 1, figsize=(8.6, 12.2), sharex=True,
                       gridspec_kw=dict(height_ratios=[0.85, 1.2, 1.2, 0.95], hspace=0.13))

# ---- (a) GMST forcing ----
for s in SSPS:
    yr, d = series(WR, s)
    ax[0].plot(yr, d.gmst, color=COL[s], lw=1.8, label=s)
ax[0].set_ylabel("GMST (°C rel. PI)")
ax[0].set_title("Glacier (GSIC) melt to 2300 — Wigley–Raper (BRICK 2.0) vs Mengel, identical SSP temperatures",
                fontsize=11, fontweight="bold", loc="left")
ax[0].legend(ncol=3, fontsize=8, frameon=False, loc="upper left")
ax[0].annotate("SSP1-1.9 peaks ~2050,\nthen declines", xy=(2205, 1.05), fontsize=7.5,
               color=COL["SSP1-1.9"], ha="center")

ymax = max(WR.gsic_hi.max(), MENCF.gsic_hi.max()) * 1.02

# ---- (b) Wigley–Raper ----
for s in SSPS:
    yr, d = series(WR, s)
    ax[1].plot(yr, d.gsic_med, color=COL[s], lw=1.9)
    if s == "SSP1-1.9":
        ax[1].fill_between(yr, d.gsic_lo, d.gsic_hi, color=COL[s], alpha=0.15, lw=0)
ax[1].text(0.012, 0.93, "(b)  Wigley–Raper (BRICK 2.0) — keeps melting toward a common ceiling",
           transform=ax[1].transAxes, fontsize=9.5, fontweight="bold", va="top")

# ---- (c) Mengel: posterior (solid) + b=0.52 counterfactual (dashed) ----
for s in SSPS:
    yr, d  = series(MEN, s)
    _,  dc = series(MENCF, s)
    ax[2].plot(yr, d.gsic_med,  color=COL[s], lw=1.9, ls="-")
    ax[2].plot(yr, dc.gsic_med, color=COL[s], lw=1.6, ls="--")
ax[2].text(0.012, 0.93, "(c)  Mengel — posterior spread is too small; b=0.52 restores it",
           transform=ax[2].transAxes, fontsize=9.5, fontweight="bold", va="top")
sp_post = MEN[(MEN.year==2300)&(MEN.ssp=="SSP5-8.5")].gsic_med.values[0] - MEN[(MEN.year==2300)&(MEN.ssp=="SSP1-1.9")].gsic_med.values[0]
sp_cf   = MENCF[(MENCF.year==2300)&(MENCF.ssp=="SSP5-8.5")].gsic_med.values[0] - MENCF[(MENCF.year==2300)&(MENCF.ssp=="SSP1-1.9")].gsic_med.values[0]
ax[2].legend(handles=[Line2D([],[],color="0.3",ls="-", label=f"extA108 (b→0.89): {sp_post:.1f} cm spread @2300{_SPREAD_FLAG}"),
                      Line2D([],[],color="0.3",ls="--",label=f"b=0.52 (Mengel-pub): {sp_cf:.1f} cm spread @2300{_SPREAD_FLAG}")],
             fontsize=8, frameon=False, loc="lower right")

for a in (ax[1], ax[2]):
    a.set_ylim(0, ymax); a.axvline(2100, color="0.6", lw=0.8, ls=":")
    a.set_ylabel("cumulative glacier\nmelt (cm SLE, rel 1995–2014)")

# ---- (d) melt rate, low SSPs: WR vs Mengel (the commitment/stabilization signal) ----
for s in ["SSP1-1.9", "SSP1-2.6"]:
    for df, ls in [(WR, "-"), (MEN, "--")]:
        yr, d = series(df, s)
        ax[3].plot(yr, np.gradient(d.gsic_med.values, yr)*100, color=COL[s], lw=1.8, ls=ls)
ax[3].axhline(0, color="0.6", lw=0.8); ax[3].axvline(2100, color="0.6", lw=0.8, ls=":")
ax[3].set_ylabel("melt rate\n(cm / century)"); ax[3].set_xlabel("year"); ax[3].set_xlim(X0, X1)
ax[3].text(0.012, 0.93, "(d)  melt rate, low SSPs — WR solid stays high, Mengel dashed falls toward zero",
           transform=ax[3].transAxes, fontsize=9.5, fontweight="bold", va="top")
ax[3].legend(handles=[Line2D([],[],color=COL["SSP1-1.9"],label="SSP1-1.9"),
                      Line2D([],[],color=COL["SSP1-2.6"],label="SSP1-2.6")],
             fontsize=8, frameon=False, loc="center right")

fig.text(0.5, 0.004,
         "BRICK 2.0 WR posterior (parameters_subsample_brick.csv) vs Mengel gic_* (BRICK-AM extA108); 1000 draws each, "
         "FaIR 2.2.4 SSP GMST — all three ARMS on one vintage (gate-enforced), but the SSPs are NOT: "
         + _CALIB_NOTE + ".\nHistory constrains a·b, not b alone → the extA108 b saturates S_eq and "
         "compresses the scenario spread. Absolute magnitudes differ by calibration — the SHAPE is the point.",
         fontsize=6.6, ha="center", color="0.35")
fig.savefig("figures/ssps_gsic_wr_vs_mengel_2300.png", dpi=150, bbox_inches="tight")
print("wrote figures/ssps_gsic_wr_vs_mengel_2300.png")
