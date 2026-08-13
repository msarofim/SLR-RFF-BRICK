#!/usr/bin/env python
"""Two confound tests on the CMIP6 Greenland amp(dT) curve, before it is used.

diag_gis_amp_cmip6.py reports a DECLINING amplification (secant slope -0.050/K,
95% [-0.079, -0.012]) whose median sits at 1.478 at present-day warming, well
below the observed south/full 1.922 that Ladrillo 1.0 actually uses. Neither
number is safe to act on until two confounds are ruled out.

TEST A -- COMPOSITION (is the shape physics or a changing model population?)
    The binned curve is NOT monotone: it falls 1.498 -> 1.284 to 2.75 K, then
    RISES to 1.341 at 3.25 K before falling again. The model count falls with the
    bin (40 -> 39 -> 34 -> 25 -> 21 -> 14 -> 7), so high-warming bins are populated
    only by high-ECS models. A curve built from a changing population measures the
    population as much as the warming level. Fix: a BALANCED PANEL -- restrict to
    models present in every bin up to a cap, recompute, and see whether the
    non-monotonicity survives.

TEST B -- ESTIMATOR/WINDOW (is the observed 1.922 comparable to CMIP6's 1.478?)
    The observed prior is a through-origin fit over 1901-2024 with NO warming-level
    filter; the CMIP6 curve drops windows below DT_MIN = 0.5 K. So the two are not
    like-for-like and the gap may be entirely window choice. Fix: compute the CMIP6
    amplification over the observed prior's OWN three windows (early 1901-1960,
    full 1901-2024, modern 1961-2024) with build_t_gis.amp_through_origin itself.

    This doubles as a test of the small-denominator artifact. build_t_gis's comment
    says the observed early window (3.604) is inflated because the global anomaly was
    near zero while Greenland swung +/- 1 C. If CMIP6 reproduces early >> full >
    modern while its own amp(dT) curve is nearly flat at low warming, then the
    observed "decline" across windows is largely ESTIMATOR ARTIFACT, and the early
    value must not be read as physical amplification.

Outputs:
  outputs/diag_gis_amp_cmip6_checks.md
  outputs/diag_gis_amp_cmip6_balanced.csv
  outputs/diag_gis_amp_cmip6_windows.csv
"""
import glob
import os
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_t_gis as BTG
import diag_gis_amp_cmip6 as D

REPO = BTG.REPO
OUT_MD = os.path.join(REPO, "outputs/diag_gis_amp_cmip6_checks.md")
OUT_BAL = os.path.join(REPO, "outputs/diag_gis_amp_cmip6_balanced.csv")
OUT_WIN = os.path.join(REPO, "outputs/diag_gis_amp_cmip6_windows.csv")

# Observed values these are tested against (outputs/gis_amp_prior.csv, zone=south).
OBS = {"early": 3.6036724362848376, "full": 1.9221976385152952,
       "modern": 1.7918384323792236}
OBS_SD = {"early": 0.6891845554118375, "full": 0.31812433437295146,
          "modern": 0.30253763239928405}
WINDOW_SCENARIO = "ssp245"      # 2015-2024 tail for the observed windows
PANEL_CAPS = [2.75, 3.25, 3.75, 4.25]   # balanced-panel bin caps, K

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


def test_a_balanced():
    """Median curve restricted to models present in EVERY bin up to a cap."""
    allw = pd.read_csv(os.path.join(REPO, "outputs/diag_gis_amp_cmip6.csv"))
    allw["bin"] = pd.cut(allw["dt_glob"], D.BIN_EDGES,
                         labels=(D.BIN_EDGES[:-1] + D.BIN_EDGES[1:]) / 2)
    per = (allw.groupby(["model", "bin"], observed=True)["secant"]
                .median().reset_index())
    per["dt_bin"] = per["bin"].astype(float)

    rows = []
    for cap in PANEL_CAPS:
        bins = sorted(b for b in per["dt_bin"].unique() if b <= cap)
        wide = per[per["dt_bin"].isin(bins)].pivot(index="model",
                                                   columns="dt_bin",
                                                   values="secant")
        panel = wide.dropna()
        if panel.empty or len(panel) < 5:
            continue
        med = panel.median()
        mono = bool(np.all(np.diff(med.values) <= 0))
        for dt, v in med.items():
            rows.append({"cap": cap, "n_models": len(panel), "dt_bin": dt,
                         "median": float(v), "monotone_decreasing": mono})
    return pd.DataFrame(rows)


def test_b_windows():
    """CMIP6 amplification on the observed prior's own three windows."""
    rows = []
    for f in sorted(glob.glob(os.path.join(D.IN_DIR, "tas_series_gis_*.csv"))):
        model = os.path.basename(f)[len("tas_series_gis_"):-len(".csv")]
        per_sc = D.load_model(f)
        if not per_sc or WINDOW_SCENARIO not in per_sc:
            continue
        ts = per_sc[WINDOW_SCENARIO].set_index("year")
        glob_s, zone_s = ts["dt_glob"], ts["dt_zone"]
        rec = {"model": model}
        for name, win in BTG.AMP_WINDOWS.items():
            rec[name] = BTG.amp_through_origin(zone_s, glob_s, win)
        # the model's own mean warming over the modern window, for context
        rec["dt_modern"] = float(glob_s.loc[
            BTG.AMP_WINDOWS["modern"][0]:BTG.AMP_WINDOWS["modern"][1]].mean())
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    bal = test_a_balanced()
    bal.to_csv(OUT_BAL, index=False)
    win = test_b_windows()
    win.to_csv(OUT_WIN, index=False)

    L = [f"# Confound tests on the CMIP6 Greenland amp(dT) curve",
         "", f"commit `{COMMIT}`; zone = {D.ZONE}; "
         f"{win['model'].nunique()} models", ""]

    # ---- Test A -------------------------------------------------------------
    L += ["## Test A -- balanced panel (composition)", "",
          "Median secant amplification using ONLY models present in every bin up "
          "to the cap.", "",
          "| cap (K) | n models | curve (dT: amp) | monotone decreasing? |",
          "|---|---|---|---|"]
    for cap, g in bal.groupby("cap"):
        curve = "  ".join(f"{r.dt_bin:.2f}: {r['median']:.3f}"
                          for _, r in g.iterrows())
        L.append(f"| {cap} | {int(g.n_models.iloc[0])} | {curve} | "
                 f"**{'YES' if bool(g.monotone_decreasing.iloc[0]) else 'NO'}** |")
    L.append("")

    # ---- Test B -------------------------------------------------------------
    L += ["## Test B -- the observed prior's own windows, computed on CMIP6", "",
          f"`build_t_gis.amp_through_origin` on historical + {WINDOW_SCENARIO}, "
          f"anomalies rel {BTG.BASE[0]}-{BTG.BASE[1]}.", "",
          "| window | years | CMIP6 median [p05, p95] | observed | observed sd |",
          "|---|---|---|---|---|"]
    for name in ("early", "full", "modern"):
        v = win[name].dropna().values
        L.append(f"| {name} | {BTG.AMP_WINDOWS[name][0]}-{BTG.AMP_WINDOWS[name][1]} "
                 f"| **{np.median(v):.3f}** [{np.percentile(v,5):.3f}, "
                 f"{np.percentile(v,95):.3f}] | {OBS[name]:.3f} | "
                 f"{OBS_SD[name]:.3f} |")
    L.append("")

    # z-scores of the observation against the CMIP6 ensemble
    L += ["Observed vs the CMIP6 ensemble, in ensemble-sd units:", ""]
    for name in ("early", "full", "modern"):
        v = win[name].dropna().values
        z = (OBS[name] - np.mean(v)) / np.std(v, ddof=1)
        frac = float((v >= OBS[name]).mean())
        L.append(f"- **{name}**: observed {OBS[name]:.3f} vs CMIP6 mean "
                 f"{np.mean(v):.3f} (sd {np.std(v, ddof=1):.3f}) -> "
                 f"**{z:+.2f} sd**; {frac*100:.0f}% of models exceed the observation")
    L.append("")

    # does CMIP6 reproduce the observed early >> full > modern ordering?
    med = {n: float(np.nanmedian(win[n])) for n in ("early", "full", "modern")}
    ordering = med["early"] > med["full"] > med["modern"]
    obs_ord = OBS["early"] > OBS["full"] > OBS["modern"]
    L += ["### Does CMIP6 reproduce the observed early >> full > modern ordering?", "",
          f"- CMIP6 medians: early {med['early']:.3f}, full {med['full']:.3f}, "
          f"modern {med['modern']:.3f} -> ordering holds: **{ordering}**",
          f"- observed: early {OBS['early']:.3f}, full {OBS['full']:.3f}, "
          f"modern {OBS['modern']:.3f} -> ordering holds: **{obs_ord}**",
          f"- CMIP6 early/modern ratio {med['early']/med['modern']:.2f} vs observed "
          f"{OBS['early']/OBS['modern']:.2f}", ""]

    with open(OUT_MD, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {OUT_MD}\nwrote {OUT_BAL}\nwrote {OUT_WIN}")


if __name__ == "__main__":
    main()
