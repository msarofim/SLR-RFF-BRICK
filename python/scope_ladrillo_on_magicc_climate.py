#!/usr/bin/env python3
"""scope_ladrillo_on_magicc_climate.py -- is the Ladrillo-vs-MAGICC gap MODULE or CLIMATE?

  python3 python/scope_ladrillo_on_magicc_climate.py [--forcing=spliced|raw|both]

Writes outputs/scope_ladrillo_on_magicc_climate.csv and .../log_...csv.txt.
SCOPING ONLY; reads the arms, runs nothing.

THE QUESTION (handoff 2026-08-31f section 6.2). Every Ladrillo-vs-MAGICC module claim at
2150/2300 has been a TWO-variable comparison: MAGICC-SLR computes its own climate from
emissions -- the property that makes its agreement with the three FaIR-driven arms
non-circular -- and that climate is 0.38-0.93 K COLDER than ours at 2300 on the four
declining markers. So a difference in TE, Greenland, Antarctica or the total could be a
module difference or the same climate difference the glaciers already turned out to have.

THE DESIGN. Ladrillo's modules, posterior, tap and draws are IDENTICAL across the two
arms; only the climate driving them changes. Three quantities per cell:

  MODULE+CLIMATE  MAGICC-SLR's own reported value minus Ladrillo on OUR climate.
                  The gap as it has been quoted all along -- both axes at once.
  CLIMATE         Ladrillo on MAGICC's climate minus Ladrillo on ours.
                  One axis. This is what the new arm buys.
  MODULE          the remainder. What is left for the modules to explain once the
                  climate difference is taken out.

⚠ THIS DECOMPOSES, IT DOES NOT ADJUDICATE. Nothing here says whose climate is right; that
is a separate and still-open question (handoff 31f open item 3). A cell where CLIMATE
accounts for the whole gap means the two models' MODULES agree once driven alike -- not
that either model is correct.

⚠ THE REVERSE ARM IS IMPOSSIBLE, not unbuilt (`runnable_is_not_undrivable`): MAGICC-SLR
lives inside MAGICC and consumes MAGICC's own climate module. There is no supported way
to drive it with FaIR's GMST, so this comparison exists in one direction only.

⚠ LWS IS A PRESCRIBED TERM IN BOTH MODELS, and that makes it a CHECK rather than a
result: neither model's land-water storage responds to temperature, so its CLIMATE column
must come out at zero. A non-zero one would mean the swap reached something it should not
have. It is kept in the decomposition (and not quietly dropped) for exactly that reason,
and because the five components sum to the total -- dropping one would leave the total's
gap unaccounted for.
"""
import argparse
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(REPO, "outputs")
OUT = os.path.join(OUTD, "scope_ladrillo_on_magicc_climate.csv")
LOG = os.path.join(OUTD, "log_scope_ladrillo_on_magicc_climate.txt")
MAGICC_MED = os.path.join(REPO, "data/comparison/magicc_nauels_components_vv.csv")

VV = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
CONTROL = ["ssp126", "ssp245", "ssp585"]
SCENARIOS = VV + CONTROL
HORIZONS = [2100, 2150, 2300]

## THE ARM. Both files must be this arm or the comparison is not like-for-like: the tap
## fires per config on that config's OWN gmst, so a tapped and an untapped file differ by
## a Greenland mechanism as well as by the climate.
ARM_TAG = "L21_tap4p69K_V5p64m_tau800"
## ⚠ THE DRAW COUNT IS NOT A CONSTANT ACROSS SCENARIOS, and hardcoding one is how this
## check would have passed on a mismatch. The shipped FaIR-climate arm runs 8000 draws for
## the seven markers and ssp585 but 2000 for ssp126 and ssp245. [ARM-MATCH] therefore takes
## the expectation from the COMPARATOR's own file, per scenario, and requires the MAGICC
## arm to meet it -- deriving the bound from the thing it tests rather than from a number
## typed once and outgrown.

## Ladrillo component -> the MAGICC component name in magicc_nauels_components_vv.csv.
## Verified against that file's own `component` column rather than assumed -- a first
## version of this map guessed `gsic` for the glaciers and would have silently produced
## NaN for every glacier row.
PAIRED = {"glaciers": "glaciers", "gis": "gis", "ais": "ais", "te": "te",
          "lws": "lws", "total": "total"}
## [LWS-ZERO] the prescribed-component check described in the docstring.
LWS_CLIMATE_TOL_CM = 1e-6

## THE VERDICT IS FIVE-VALUED, BECAUSE A SHARE ALONE MISLEADS. `climate / gap` is a clean
## fraction only when the climate term lies between zero and the gap. It does not always:
## at vvVL/gis/2300 the gap is +5.13 cm while the climate term is -2.83, so swapping the
## climate makes the two models disagree MORE and the module term (7.96) is LARGER than
## the raw gap. Reporting that as "-55 %" reads like a small climate contribution when it
## is the opposite. So the share is classified, and the classes that are not
## "climate explains it" get their own names rather than being folded into a number.
##
## ⚠ THE "NO GAP TO EXPLAIN" FLOOR IS SCALED TO THE ARM'S OWN SPREAD, not set as an
## absolute cm (`tolerance_scaled_to_spread`): a fixed 0.5 cm would be a third of the band
## at vvVL/2100 and a fortieth of it at vvH/2300, so it would be choosing the physics at
## one end of the table and rubber-stamping at the other.
GAP_FLOOR_FRAC_OF_SPREAD = 0.05
SHARE_MOSTLY, SHARE_SOME, SHARE_OVER = 0.75, 0.25, 1.25


def verdict(gap, clim, spread):
    """Which axis carries this cell's Ladrillo-vs-MAGICC difference."""
    if abs(gap) < GAP_FLOOR_FRAC_OF_SPREAD * spread:
        return "AGREE", np.nan          # no gap worth decomposing
    share = clim / gap
    if share > SHARE_OVER:
        return "OVERSHOOT", share       # the swap crosses past agreement
    if share >= SHARE_MOSTLY:
        return "CLIMATE", share
    if share >= SHARE_SOME:
        return "BOTH", share
    if share > -SHARE_SOME:
        return "MODULE", share
    return "OPPOSED", share             # the swap WIDENS the gap


def cells(scen, forcing, climate):
    tag = "" if climate == "fair" else "_magiccclim"
    p = os.path.join(OUTD, "scope_slr_fairunc_cells_%s_%s%s_%s.csv"
                     % (scen, forcing, tag, ARM_TAG))
    if not os.path.exists(p):
        return None, None
    d = pd.read_csv(p)
    d = d[d.arm == "joint"]
    n = sorted(set(d.n_draws))
    if len(n) != 1:
        raise SystemExit("[ARM-MATCH] %s mixes draw counts %s" % (os.path.basename(p), n))
    return d.set_index(["component", "horizon"]), n[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcing", default="both", choices=["spliced", "raw", "both"])
    a = ap.parse_args()
    forcings = ["spliced", "raw"] if a.forcing == "both" else [a.forcing]

    mag = pd.read_csv(MAGICC_MED)
    rows, lines = [], []

    def say(s=""):
        print(s)
        lines.append(s)

    say("LADRILLO L21 ON MAGICC'S CLIMATE -- separating the module axis from the climate axis")
    say("arm %s, %d draws, joint band, cm rel 1995-2014" % (ARM_TAG, ARM_N_DRAWS))
    say()

    for forcing in forcings:
        say("=" * 104)
        say("FORCING CONVENTION: %s   %s" % (
            forcing.upper(),
            "our history, MAGICC's future anomaly -- the PRIMARY arm (Marcus 2026-08-31)"
            if forcing == "spliced" else
            "MAGICC's whole path -- the CHECK arm; Ladrillo's hindcast is NOT preserved"))
        say("=" * 104)
        say("%-7s %-9s %-6s %9s %9s %9s | %10s %10s %10s %7s  %-9s"
            % ("scen", "component", "horiz", "L/ours", "L/MAGICC", "MAGICC",
               "mod+clim", "climate", "module", "share", "verdict"))
        for scen in SCENARIOS:
            (f, nf), (m, nm) = cells(scen, forcing, "fair"), cells(scen, forcing, "magicc")
            if f is None or m is None:
                say("%-7s  -- not run yet (%s%s)" % (
                    scen, "" if f is not None else "fair ",
                    "" if m is not None else "magicc"))
                continue
            ## [ARM-MATCH] a difference between two files run at different sample sizes is
            ## partly a difference in sample size. The comparator sets the expectation.
            if nf != nm:
                raise SystemExit("[ARM-MATCH] %s/%s: the MAGICC arm has %d draws but its "
                                 "FaIR comparator has %d -- re-run the MAGICC arm at "
                                 "%d/4 = %d draws per chain"
                                 % (scen, forcing, nm, nf, nf, nf // 4))
            for comp, magcomp in PAIRED.items():
                for H in HORIZONS:
                    lo = f.loc[(comp, H), "med_cm"]
                    lm = m.loc[(comp, H), "med_cm"]
                    r = mag[(mag.scenario == scen) & (mag.year == H)
                            & (mag.component == magcomp)]
                    mv = float(r["med"].iloc[0]) if len(r) == 1 else np.nan
                    both, clim = mv - lo, lm - lo
                    mod = both - clim
                    spread = m.loc[(comp, H), "spread_cm"]
                    v, share = verdict(both, clim, spread)
                    say("%-7s %-9s %-6d %9.2f %9.2f %9.2f | %10.2f %10.2f %10.2f %7s  %-9s"
                        % (scen, comp, H, lo, lm, mv, both, clim, mod,
                           "--" if np.isnan(share) else "%6.0f%%" % (100 * share), v))
                    rows.append((forcing, scen, comp, H, lo, lm, mv, both, clim, mod,
                                 spread, share, v))
                    ## [LWS-ZERO] a prescribed component cannot respond to a climate
                    ## swap. If it does, the swap reached something it should not have.
                    if comp == "lws" and abs(clim) > LWS_CLIMATE_TOL_CM:
                        raise SystemExit("[LWS-ZERO] %s/%s/%d: the climate swap moved a "
                                         "PRESCRIBED component by %.3e cm"
                                         % (forcing, scen, H, clim))
            say()

    df = pd.DataFrame(rows, columns=[
        "forcing", "scenario", "component", "horizon", "ladrillo_our_climate_cm",
        "ladrillo_magicc_climate_cm", "magicc_slr_cm", "module_plus_climate_cm",
        "climate_cm", "module_cm", "joint_spread_cm", "climate_share_of_gap", "verdict"])
    df.to_csv(OUT, index=False)

    say("=" * 104)
    say("ROLL-UP -- how each component's Ladrillo-vs-MAGICC gap is carried, by verdict")
    say("=" * 104)
    for forcing in forcings:
        sub_ = df[(df.forcing == forcing) & (df.component != "lws")]
        if sub_.empty:
            continue
        say("  %s" % forcing.upper())
        say("    %-9s %s" % ("component", "  ".join("%-9s" % v for v in
            ("CLIMATE", "BOTH", "MODULE", "OPPOSED", "OVERSHOOT", "AGREE"))))
        for comp in [c for c in PAIRED if c != "lws"]:
            cc = sub_[sub_.component == comp]
            say("    %-9s %s  (n=%d)" % (comp, "  ".join(
                "%-9d" % int((cc.verdict == v).sum()) for v in
                ("CLIMATE", "BOTH", "MODULE", "OPPOSED", "OVERSHOOT", "AGREE")), len(cc)))
        say()
    with open(LOG, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\nwrote %s\n      %s" % (os.path.relpath(OUT, REPO), os.path.relpath(LOG, REPO)))


if __name__ == "__main__":
    main()
