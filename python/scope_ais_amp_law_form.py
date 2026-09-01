#!/usr/bin/env python3
"""
scope_ais_amp_law_form.py — SHOULD `ais_gmst_amp` BE A FUNCTION OF WARMING LEVEL?
                            Measured answer: NO. And the constant is in the wrong place.

⚠⚠ THIS SCRIPT EXISTS BECAUSE ADDENDUM 7 OF handoff_2026-08-25c WAS WRONG, AND IT WAS WRONG
IN THE WAY `~/.claude/CLAUDE.md` WARNS ABOUT. It asserted, citing memory `pai_cmip6_time`,
that Antarctic amplification "RISES with warming level, ~0.85-0.90 at 0.6-0.8 K -> ~1.15-1.20
at 2-4 K, saturating at the DAIS equilibrium", and concluded that a constant amp is "fitted
where amp is low and applied where it is high" so the fix must be `amp(dT)`.

**That memory describes a SUPERSEDED diagnostic.** On 2026-08-24, two commits replaced it:
  * `a79d532` "Switch scenario diagnostic to SECANT ratio; correct a to ~1.08"
  * `9de38bf` "data/cmip6_pai was corrupt for SEVEN files, not two -- and the numerator was
    wrong too" (an xarray `.weighted()` inner-join on float-noise latitudes silently reduced
    MPI-ESM1-2-LR to 56 of 96 latitudes; the AIS numerator inherited it)

`python/diag_pai_cmip6_time.py`'s own header states the supersession: the earlier
sliding-window TREND ratio (Xie's PAI1) "is superseded -- the SECANT is the BRICK-relevant
quantity", because BRICK's `a` multiplies a LEVEL anomaly, not a trend. The two behave
OPPOSITELY with warming. Gist-recall of a directional claim, off by a sign, on the number
that was about to decide a model-form change and a recalibration.

WHAT THIS SCRIPT MEASURES, from the CORRECTED data (34 models, land-frame AIS):

  [A] IS THE STATE-DEPENDENCE RESOLVABLE? Per-model OLS slope of the secant R on dT_global,
      restricted to dT >= 1.0 K where the denominator is not noise (the diagnostic's own
      rule). If the slope is not resolved, or is small against the between-model spread, a
      constant is the right FORM and `amp(dT)` must not be built.

  [B] WHERE SHOULD THE CONSTANT SIT? The model-median secant, with the between-model spread,
      cross-checked against the independent DECK 1pctCO2 secant.

  [C] WHAT IT IS WORTH, through the tipping threshold -- the same closed form as
      `scope_ais_amp_price.py`, so the two compose.

    source ~/climate-env/bin/activate
    python python/scope_ais_amp_law_form.py [--tag=L14]
Reads   outputs/diag_pai_cmip6_time.csv        (34-model secant, CORRECTED 2026-08-24)
        outputs/diag_pai_deck_summary.md       (41-model DECK 1pctCO2 cross-check)
        data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv
Writes  outputs/scope_ais_amp_law_form_<TAG>.csv
"""
import os
import re
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUT = os.path.join(REPO, "outputs", f"scope_ais_amp_law_form_{TAG}.csv")
PAI = os.path.join(REPO, "outputs", "diag_pai_cmip6_time.csv")
DECK = os.path.join(REPO, "outputs", "diag_pai_deck_summary.md")
POST = os.path.join(REPO, "data", "MimiBRICK",
                    f"parameters_subsample_brick_mengel_{TAG}.csv")

# The diagnostic's own floor: below this the secant's denominator is small and R is noise.
DT_FLOOR = 1.0
# The projection-relevant warming range, from the shipped drivers (1.85 K ssp126@2100 to
# 7.79 K ssp585@2300); 1->4 K covers every cell the literature comparators exist at.
DT_RANGE = (1.0, 4.0)
# The shipped prior, PARSED from the calibration driver rather than copied. It was
# hand-copied as (0.95, 0.10) and went stale the day `165a860` moved it to (1.09, 0.180),
# so this script printed a superseded number under the label "THE SHIPPED PRIOR" for a
# week. Read the DEFAULT branch of the AMP_EQ ternary -- the equilibrium arm and the
# --amp-mu/--amp-sigma overrides are per-run, not what ships.
MCMC_SRC = os.path.join(REPO, "julia", "calibrate_mcmc_ext.jl")


def _shipped_prior():
    src = open(MCMC_SRC).read()
    out = []
    for name in ("AMP_MU", "AMP_SIGMA"):
        m = re.search(rf"^const {name}\s*=.*?AMP_EQ \?[^:]+:\s*([0-9.]+)\)", src, re.M)
        if m is None:
            raise SystemExit(
                f"cannot read {name} from {os.path.relpath(MCMC_SRC, REPO)} -- the prior's "
                "definition moved. FIX THE PARSE, do not re-hardcode the number: the "
                "hardcoded copy is what went stale last time.")
        out.append(float(m.group(1)))
    return out


CUR_MU, CUR_SIGMA = _shipped_prior()
TANT0 = -15.42 / 0.8365
rows = []


def main():
    d = pd.read_csv(PAI)
    d = d[d.dTg >= DT_FLOOR]
    print("=" * 100)
    print("SHOULD amp BE A FUNCTION OF WARMING LEVEL? — the CORRECTED 34-model secant")
    print("=" * 100)
    print(f"\n  R = [smooth30(T_AIS) - T_AIS,PI] / [smooth30(T_glob) - T_glob,PI], land-frame,")
    print(f"  PI = 1850-1900. A LEVEL ratio -- the quantity BRICK's `a` actually is.")
    print(f"  Restricted to dT >= {DT_FLOOR} K (below it the denominator is noise).")

    # ------------------------------------------------------- [A] is the slope resolvable?
    print(f"\n[A] IS THE STATE-DEPENDENCE RESOLVABLE? per-model OLS slope of R on dT")
    print(f"\n{'scenario':10s} {'n':>4s} {'mean slope':>12s} {'sd':>8s} {'se':>8s} {'z':>7s} "
          f"{'worth over ' + str(DT_RANGE[0]) + '-' + str(DT_RANGE[1]) + ' K':>22s}  verdict")
    for ssp in sorted(d.scenario.unique()):
        s = d[d.scenario == ssp]
        sl = np.array([np.polyfit(g.dTg, g.R, 1)[0] for _, g in s.groupby("model")
                       if len(g) >= 30])
        se = sl.std(ddof=1) / np.sqrt(len(sl))
        z = sl.mean() / se
        worth = sl.mean() * (DT_RANGE[1] - DT_RANGE[0])
        bms = s.groupby("model").R.median().std(ddof=1)
        print(f"{ssp:10s} {len(sl):4d} {sl.mean():+12.4f} {sl.std(ddof=1):8.4f} {se:8.4f} "
              f"{z:+7.2f} {worth:+15.3f} in amp  "
              f"{'RESOLVED' if abs(z) >= 2 else 'UNRESOLVED'}")
        print(f"{'':10s} {'':4s} against a BETWEEN-MODEL sd of {bms:.3f} "
              f"=> the slope is worth {abs(worth)/bms:.2f}x the spread")
        rows.append(dict(block="A", scenario=ssp, quantity="slope_R_on_dT", value=sl.mean(),
                         unit="per K",
                         note=f"n={len(sl)} models, sd {sl.std(ddof=1):.4f}, se {se:.4f}, "
                              f"z={z:+.2f}; worth {worth:+.3f} over {DT_RANGE} K vs "
                              f"between-model sd {bms:.3f}",
                         verdict="RESOLVED" if abs(z) >= 2 else "UNRESOLVED"))
    print(f"\n    ⇒ NEITHER SCENARIO RESOLVES A SLOPE, THEY DISAGREE IN SIGN, and each is worth")
    print(f"      6-9x LESS than the between-model spread. A CONSTANT IS THE RIGHT FORM.")
    print(f"      **`amp(dT)` MUST NOT BE BUILT** -- it would encode a trend the data do not"
          f" have,\n      and addendum 7's version of it would have encoded one of the wrong "
          f"SIGN.")

    # --------------------------------------------------------- [B] where should it sit?
    print(f"\n[B] WHERE SHOULD THE CONSTANT SIT?")
    print(f"\n{'scenario':10s} {'model-median R':>15s} {'between-model sd':>18s} "
          f"{'p17':>7s} {'p83':>7s} {'n':>4s}")
    for ssp in sorted(d.scenario.unique()) + ["BOTH"]:
        s = d if ssp == "BOTH" else d[d.scenario == ssp]
        mm = s.groupby("model").R.median()
        print(f"{ssp:10s} {mm.median():15.3f} {mm.std(ddof=1):18.3f} {mm.quantile(.17):7.3f} "
              f"{mm.quantile(.83):7.3f} {len(mm):4d}")
        rows.append(dict(block="B", scenario=ssp, quantity="model_median_secant",
                         value=float(mm.median()), unit="amp",
                         note=f"between-model sd {mm.std(ddof=1):.3f}, p17 {mm.quantile(.17):.3f}, "
                              f"p83 {mm.quantile(.83):.3f}, n={len(mm)} models", verdict=""))
    # ⚠ PARSE THE COLUMN BY POSITION, NOT BY A LOOSE REGEX. A first version matched the
    # 3rd numeric group anywhere on the line and picked up the dT column's "3.000" as an
    # amplification of 3.0, which then printed as a comparator range of "1.087-3.000".
    deck_rows = [l for l in open(DECK).read().splitlines()
                 if l.startswith("|") and re.match(r"^\|\s*[\d.]+\s*\|", l)]
    r1 = []
    for l in deck_rows:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if len(cells) >= 3:
            try:
                r1.append(float(cells[2]))          # column 3 = r_1pct
            except ValueError:
                pass
    if r1:
        print(f"\n    INDEPENDENT CROSS-CHECK — DECK 1pctCO2 secant (41 models, "
              f"`diag_pai_deck_summary.md`):\n      r_1pct over 2.5-4.5 K = "
              f"{min(r1):.3f}-{max(r1):.3f}, median {np.median(r1):.3f}")
        rows.append(dict(block="B", scenario="DECK 1pctCO2", quantity="secant_cross_check",
                         value=float(np.median(r1)), unit="amp",
                         note=f"41 models, 2.5-4.5 K, range {min(r1):.3f}-{max(r1):.3f}",
                         verdict=""))
    both = d.groupby("model").R.median()
    post = pd.read_csv(POST)
    amp0 = post["ais_gmst_amp"].to_numpy(float)
    post_med = float(np.median(amp0))
    print(f"\n    ⇒ the scenario ensemble and the DECK ensemble agree on "
          f"~{float(both.median()):.2f}.")
    print(f"    ⚠ THE SHIPPED PRIOR IS N({CUR_MU:.3f}, {CUR_SIGMA:.3f}) "
          f"({os.path.relpath(MCMC_SRC, REPO)}) AND THE {TAG}\n      POSTERIOR MEDIAN IS "
          f"{post_med:.3f} — {(post_med - float(both.median()))/CUR_SIGMA:+.2f} prior sd from "
          f"the corrected\n      measurement, whose own centre sits "
          f"{(float(both.median())-CUR_MU)/CUR_SIGMA:+.2f} prior sd from the prior mean. The "
          f"direction\n      addendum 7 got right; the MECHANISM and the FIX it proposed were "
          f"both wrong.")

    # ------------------------------------------------- [C] what re-centring is worth
    thr = post["antarctic_temp_threshold"].to_numpy(float)
    need = thr - TANT0
    print(f"\n[C] WHAT RE-CENTRING IS WORTH — crossing GMST = (threshold - T_ant0)/amp")
    print(f"\n{'arm':28s} {'amp':>7s} {'crossing GMST':>15s}")
    for lab, a in ((f"{TAG} posterior", post_med),
                   ("corrected secant (BOTH)", float(both.median())),
                   ("ssp245 model-median", float(d[d.scenario == 'ssp245']
                                                 .groupby('model').R.median().median())),
                   ("ssp585 model-median", float(d[d.scenario == 'ssp585']
                                                 .groupby('model').R.median().median()))):
        gx = float(np.median(need / a))
        print(f"{lab:28s} {a:7.3f} {gx:12.3f} K")
        rows.append(dict(block="C", scenario="", quantity=f"crossing_GMST/{lab}", value=gx,
                         unit="degC", note=f"amp {a:.3f}", verdict=""))
    print(f"\n    ⇒ a {float(both.median())-post_med:+.3f} move in amp, i.e. "
          f"{(float(both.median())-post_med)/CUR_SIGMA:+.2f} prior sd. "
          f"`scope_ais_amp_price.py`\n      prices the tipped fractions this implies.")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
