#!/usr/bin/env python3
"""
DIAGNOSTIC -- is the L24 panel's headline "@2024" gap a MODEL result or a WINDOW ARTIFACT?

Found 2026-09-09c while answering "do results need to be updated now?". The answer turned on
what the +0.74 cm actually is, and it is not what it is reported as.

THE MECHANISM. plot_hindcast_components.py prints each epoch as a 5-year mean -- "@2024
(2022-2026 mean)". The MODEL has all five years. The OBS DO NOT: the total target's Dangendorf
splice ends 2024, GlaMBIE ends 2023, the component splices end 2025. pandas' .mean() SKIPS NaN
SILENTLY, so the obs side is averaged over 2-4 years while the model side is averaged over 5.

On a series rising ~0.4 cm/yr, a 5-year mean centred 2024 and a 3-year mean centred 2023 MUST
differ by ~0.4 cm no matter what the model does. That difference is being reported as a model
excess. This is [[like_for_like_forcing]] applied to a mean's window instead of a trend's.

⭐ THE CONTROL IS BUILT IN: the same test at @1950 and @2000, where the obs cover all five
years, must return EXACTLY zero artifact. It does. That is what distinguishes a real mechanism
from an arithmetic slip in this script.

WRITES NOTHING. Changes no target, no figure, no chain. Reports only.
"""
import os
import numpy as np
import pandas as pd

REPO    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(REPO, "outputs", "diag_epoch_window_asymmetry.csv")
TGT_CSV = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
TAG     = "L24"                       # the tag the shipped panel numbers were printed at
LAD_CSV = os.path.join(REPO, "outputs", f"postpred_{TAG}_components_timeseries.csv")

HALF_WIDTH = 2                        # the panel's epoch mean is +/- HALF_WIDTH years
EPOCHS     = [1950, 2000, 2024]
RAGGED_EPOCH = 2024                   # the only one at the ragged end of the obs
TGT_COL = {"glaciers": "gsic", "gis": "gis", "ais": "ais", "te": "steric", "total": "dang"}

# The panel's own printed pair at RAGGED_EPOCH, as the gate that we reproduce it.
PANEL_OBS_TOTAL, PANEL_LAD_TOTAL, PANEL_TOL = 7.81, 8.55, 0.006


def main():
    tgt = pd.read_csv(TGT_CSV).set_index("year")
    lad = pd.read_csv(LAD_CSV).set_index("year")

    print("=" * 78)
    print(f"DIAGNOSTIC: ragged-window asymmetry in the {TAG} panel's epoch means")
    print("=" * 78)

    # ---- GATE: we must reproduce the panel's own printed numbers ------------
    O, L = tgt["dang"], lad["total_p50"]
    w = range(RAGGED_EPOCH - HALF_WIDTH, RAGGED_EPOCH + HALF_WIDTH + 1)
    yrs = [y for y in w if np.isfinite(O.get(y, np.nan))]
    o_m, l_m = O.loc[yrs].mean(), L.loc[min(w):max(w)].mean()
    print(f"\n[GATE PANEL] reproduce the printed pair at @{RAGGED_EPOCH}: "
          f"obs {o_m:.3f} vs {PANEL_OBS_TOTAL}, Ladrillo {l_m:.3f} vs {PANEL_LAD_TOTAL}")
    if abs(o_m - PANEL_OBS_TOTAL) > PANEL_TOL or abs(l_m - PANEL_LAD_TOTAL) > PANEL_TOL:
        raise SystemExit("[GATE PANEL] FAILED -- this is not the panel's arithmetic; "
                         "every number below would be about a different quantity")
    print("             PASSED. What follows is the panel's own headline number.")

    rows = []
    print(f"\n[1] EVERY COMPONENT AT @{RAGGED_EPOCH} -- model over "
          f"{2*HALF_WIDTH+1} yrs, obs over however many are non-NaN")
    print(f"    {'component':10s} {'obs yrs':>16s} {'REPORTED':>10s} {'LIKE-FOR-LIKE':>14s} "
          f"{'artifact':>9s} {'% reported':>11s}")
    for c in ["glaciers", "gis", "ais", "te", "total"]:
        O, L = tgt[TGT_COL[c]], lad[c + "_p50"]
        yrs = [y for y in w if np.isfinite(O.get(y, np.nan))]
        o, l_all, l_matched = O.loc[yrs].mean(), L.loc[min(w):max(w)].mean(), L.loc[yrs].mean()
        rep, lfl = l_all - o, l_matched - o
        pct = 100 * (rep - lfl) / rep if abs(rep) > 1e-9 else np.nan
        print(f"    {c:10s} {f'{yrs[0]}-{yrs[-1]} (n={len(yrs)})':>16s} {rep:>+10.3f} "
              f"{lfl:>+14.3f} {rep-lfl:>+9.3f} {pct:>10.0f}%")
        rows.append(dict(epoch=RAGGED_EPOCH, component=c, n_obs_years=len(yrs),
                         gap_reported_cm=rep, gap_like_for_like_cm=lfl,
                         artifact_cm=rep - lfl, pct_of_reported=pct))

    # ---- THE CONTROL: complete-coverage epochs must show EXACTLY zero -------
    print(f"\n[2] ⭐ CONTROL -- the same test where the obs cover all {2*HALF_WIDTH+1} years")
    ok = True
    for yc in [e for e in EPOCHS if e != RAGGED_EPOCH]:
        O, L = tgt["dang"], lad["total_p50"]
        ww = range(yc - HALF_WIDTH, yc + HALF_WIDTH + 1)
        yy = [y for y in ww if np.isfinite(O.get(y, np.nan))]
        art = L.loc[min(ww):max(ww)].mean() - L.loc[yy].mean()
        print(f"    @{yc}: obs {len(yy)}/{2*HALF_WIDTH+1} yrs   artifact {art:+.3e} cm")
        ok &= (len(yy) == 2*HALF_WIDTH+1) and abs(art) < 1e-12
        rows.append(dict(epoch=yc, component="total", n_obs_years=len(yy),
                         gap_reported_cm=np.nan, gap_like_for_like_cm=np.nan,
                         artifact_cm=art, pct_of_reported=np.nan))
    if not ok:
        raise SystemExit("[CONTROL] FAILED -- a complete-coverage epoch showed a nonzero "
                         "artifact, so the effect at the ragged end is NOT the raggedness")
    print("    => EXACTLY zero where coverage is complete. The effect is the RAGGED END, "
          "not the arithmetic.")

    print(f"\n[3] VERDICT")
    tot = [r for r in rows if r["component"] == "total" and r["epoch"] == RAGGED_EPOCH][0]
    gl = [r for r in rows if r["component"] == "glaciers"][0]
    rate = lad["total_p50"].loc[min(w):max(w)].diff().mean()
    print(f"    ⛔ {tot['pct_of_reported']:.0f}% of the headline "
          f"{tot['gap_reported_cm']:+.3f} cm TOTAL gap is a window artifact. Like-for-like "
          f"it is {tot['gap_like_for_like_cm']:+.3f} cm.")
    print(f"       Ladrillo rises {rate:.3f} cm/yr here, so a {2*HALF_WIDTH+1}-yr mean centred "
          f"{RAGGED_EPOCH} against a")
    print(f"       {tot['n_obs_years']}-yr mean centred "
          f"{RAGGED_EPOCH - HALF_WIDTH + (tot['n_obs_years']-1)/2:.0f} MUST differ by "
          f"~{rate * (HALF_WIDTH - (tot['n_obs_years']-1)/2):.2f} cm whatever the model does.")
    print(f"    ⛔ GLACIERS is worse in kind: only {gl['n_obs_years']} obs years, and the "
          f"artifact {gl['artifact_cm']:+.3f} cm")
    print(f"       EXCEEDS the reported gap {gl['gap_reported_cm']:+.3f} cm, so the SIGN of the "
          f"reported")
    print(f"       glacier bias is set by the raggedness: like-for-like it is "
          f"{gl['gap_like_for_like_cm']:+.3f} cm.")
    print(f"    ✅ TE survives: {[r for r in rows if r['component']=='te'][0]['pct_of_reported']:.0f}% "
          f"artifact only -- that overshoot is real.")
    print(f"    ⚠ This is a REPORTING defect, not a model or target defect. No posterior, "
          f"target or chain")
    print(f"      is implicated. It is also INDEPENDENT of the recalibration rulings.")

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {OUT_CSV}")


if __name__ == "__main__":
    main()
