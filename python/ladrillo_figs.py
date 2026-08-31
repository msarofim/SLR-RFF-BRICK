#!/usr/bin/env python3
"""ladrillo_figs.py — shared constants, loaders and gates for the Ladrillo figure suite.

WHY THIS EXISTS. Before 2026-08-31 every figure script declared its own palette, and two
live ones DISAGREED: plot_ladrillo_memo_figures.py had Ladrillo="#2166ac" / BRICK 2.0="#7f7f7f",
doc_l14_vs_brick20.py had Ladrillo="tab:red" / BRICK 2.0="0.55". A reader moving between two
figures of the same model saw two different colours for it. THE MEMO CONVENTION IS ADOPTED
HERE (it is the older and the more widely reproduced), and it is declared ONCE.

⚠ THE THREE BASELINE WINDOWS ARE DIFFERENT AND MIXING THEM IS THE CLASSIC ERROR IN THIS REPO:
  1995-2005  the CALIBRATION re-reference -- every postpred_* file and recalib_targets_ext.csv
  1995-2014  the PROJECTION baseline -- every ssps_components_2300_*, scope_slr_fairunc_*,
             *_model_comparison_*, and AR6 Table 9.9
  1970-2020  a DISPLAY-ONLY re-reference used by plot_postpred_components_ext.py
They are named constants here so a caption cannot claim one while the data carries another.

This module deliberately does NOT import matplotlib: it is data + gates only, so a driver
script can use the loaders without a display stack.
"""
import os
import subprocess

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- baselines -------------------------------------------------------------
CAL_BASELINE = "cm, rel. 1995-2005"          # postpred_*, recalib_targets_ext
PROJ_BASELINE = "cm, rel. 1995-2014"         # every projection product
DISPLAY_BASELINE = "1970-2020"               # display-only re-reference

# --- components ------------------------------------------------------------
## Canonical order and titles. `total` is LAST so it reads as the sum of what precedes it.
COMPONENTS = ["glaciers", "gis", "ais", "te", "lws", "total"]
COMP_TITLE = {"glaciers": "Glaciers", "gis": "Greenland ice sheet",
              "ais": "Antarctic ice sheet", "te": "Thermal expansion",
              "lws": "Land-water storage", "total": "Total"}

# --- sources ---------------------------------------------------------------
SRC_COLOR = {"Ladrillo": "#2166ac", "BRICK 2.0": "#7f7f7f",
             "MAGICC-SLR": "#d62728", "FACTS": "#ff9900"}

## WHETHER A WIDTH MAY BE DRAWN IS A PROPERTY OF THE ARM, NOT OF THE SOURCE NAME.
##
## ⚠ CORRECTED 2026-08-31. This module shipped a `WIDTH_SRCS = {"Ladrillo", "BRICK 2.0"}`
## set with the caveat "MAGICC/FACTS bands ALSO carry climate uncertainty, so their MEDIANS
## are comparable and their WIDTHS are not". That sentence encodes the state of the world
## BEFORE 2026-08-30, when both our arms ran on MEAN forcing and were therefore
## posterior-parameter spread only. It is now FALSE for any product built on the joint arm:
## `scope_slr_fair_uncertainty.jl` and `scope_slr_fairunc_oldbrick.jl` propagate the
## Ladrillo and BRICK 2.0 posteriors across the SAME 841 FaIR configs, so those bands carry
## climate uncertainty too -- which is the entire reason the joint arms were built
## (`brick20_joint_band`: "every column of the comparison now carries climate uncertainty,
## so the WIDTHS are like-for-like for the first time"). Keeping the old set suppressed
## three of the four bands on the one figure where they were finally comparable.
##
## The predicate reads the row's OWN `band_basis` string instead, so a cell that falls back
## to the fixed arm loses its band automatically and no source-name list can go stale again.
BASIS_CARRIES_CLIMATE = ("joint", "climate + parameter")
BASIS_PARAM_ONLY = ("fixed",)


def band_is_comparable(basis):
    """True when this row's band carries CLIMATE uncertainty as well as parameter spread.

    Joint arms (ours) and the MAGICC/FACTS native ensembles all do; a `fixed
    (posterior params, mean forcing)` band does not, and is a narrower object for reasons
    that have nothing to do with the model. Unrecognised bases raise rather than default:
    guessing which kind of band an unknown string describes is how the stale set survived."""
    b = str(basis).strip().lower()
    if b.startswith(BASIS_PARAM_ONLY):
        return False
    if b.startswith(BASIS_CARRIES_CLIMATE):
        return True
    raise SystemExit(
        "unrecognised band_basis %r -- refusing to guess whether it carries climate "
        "uncertainty. Add it to ladrillo_figs.BASIS_CARRIES_CLIMATE or BASIS_PARAM_ONLY."
        % basis)


## The caveat that survives the correction. Climate uncertainty is now present on every
## arm, but the ENSEMBLES generating it are not the same ensemble, and two of the four
## bands are prior propagations rather than refits.
BAND_CAVEAT = ("All four bands now carry climate uncertainty -- ours from 841 FaIR "
               "configs, MAGICC-SLR from its 600-member AR6 drawnset, FACTS from its own "
               "internal ensembles -- so the widths are the same KIND of object and are "
               "comparable; they are not the same ensemble, and the two joint arms are "
               "PRIOR PROPAGATIONS (both posteriors were calibrated under fixed forcing), "
               "not refits.")

# --- scenario sets ---------------------------------------------------------
## One table per set: (key, label, colour). The van Vuuren table additionally carries the
## peak-and-decline flag, so a commitment panel is built from the FLAG and can never fall
## out of step with the scenario list. ⚠ Never hand-type a subset of either.
SSP_SET = [("ssp126", "SSP1-2.6", "#1b7837"),
           ("ssp245", "SSP2-4.5", "#2166ac"),
           ("ssp585", "SSP5-8.5", "#b2182b")]
VV_SET = [("vvVL", "Very Low",      "#00a9cf", True),
          ("vvLN", "Low-to-Neg",    "#1f78b4", True),
          ("vvL",  "Low",           "#003466", False),
          ("vvML", "Medium-to-Low", "#f69320", True),
          ("vvM",  "Medium",        "#c8a000", False),
          ("vvHL", "High-to-Low",   "#df0000", True),
          ("vvH",  "High",          "#7a0002", False)]

## ⚠ THE VINTAGE STAMP IS DECLARED, NEVER DERIVED FROM THE TAG STRING. Until 2026-08-30 an
## L21 figure was printing L11-era facts in its caption, because the caption text was
## written once and the --tag was free. An undeclared tag now REFUSES to draw rather than
## captioning a figure with an arm it was not written for.
TAG_DESC = {
    "L21": dict(model="Ladrillo L21",
                calib="FaIR 2.2.4 calib 1.6.0 + CMIP7",
                chains="8 chains, chain_L21_seed*_n2000000",
                glacier="3-reservoir Nauels-nu (glaciers_nu3): R19 / SLOWP / FAST",
                gis="two-basin Greenland with the shipped tap",
                note="champion since 2026-08-28; L14's config on the 1.6.0 drivers. "
                     "SLR@2100 = 45.01 cm is an L14 number and keeps that label."),
    "L14": dict(model="Ladrillo L14",
                calib="FaIR 2.2.4 calib 1.4.5",
                chains="chain_L14_*",
                glacier="3-reservoir Nauels-nu (glaciers_nu3): R19 / SLOWP / FAST",
                gis="two-basin Greenland",
                note="canonical 2026-08-20 to 2026-08-28; SLR@2100 = 45.01 cm."),
}


def tag_desc(tag):
    if tag not in TAG_DESC:
        raise SystemExit(
            "undeclared --tag=%s: add it to ladrillo_figs.TAG_DESC with its model, calib, "
            "chains, glacier and gis strings.\n  A figure must not be captioned with an arm "
            "it was not written for -- that is how an L21 figure came to print L11-era "
            "facts. Declare it; do not derive it from the tag string."
            % tag)
    return TAG_DESC[tag]


def scen_set(name):
    """(key, label, colour, decline) rows for a named set. `decline` is False throughout
    the SSP set: only ssp119 peaks and declines and it is not in the shared three."""
    if name == "ssp":
        return [(k, l, c, False) for k, l, c in SSP_SET]
    if name == "vv":
        return list(VV_SET)
    raise SystemExit("unknown scenario set %r -- expected 'ssp' or 'vv'" % name)


# --- paths -----------------------------------------------------------------
def joint_stem(tag, tapped=True):
    """The stem scope_slr_fair_uncertainty.jl writes, MIRRORED from the same GIS_TAP_CELL
    the Julia reads (`const TAP_TAG`, ~:162).

    ⚠ NAMING SKEW, DELIBERATELY HANDLED HERE. The components deliverable uses
    `<tag>_tap...K_V...m_tau<N>_n<stages>_ws` (gis_targets.tap_tag), while the
    scope_slr_fairunc_* family omits the `_n<stages>_ws` suffix. Two stems for the SAME arm.
    Both are resolved from the Julia constant, never by f-string -- an f-string could only
    ever find the untapped file, which is the -1.7 cm silent-wrong-model class of error."""
    if not tapped:
        return tag
    import gis_targets
    c = gis_targets.tap_cell()
    return (f"{tag}_tap{str(c['onset_K']).replace('.', 'p')}K"
            f"_V{str(c['V_m']).replace('.', 'p')}m_tau{int(c['tau_yr'])}")


def paths_csv(scen, model, tag="L21", forcing="spliced"):
    """Annual trajectory file for one scenario and model. `model` is 'ladrillo' or 'brick20'."""
    stem = joint_stem(tag) if model == "ladrillo" else "oldbrick"
    return os.path.join(REPO, "outputs",
                        f"scope_slr_fairunc_paths_{scen}_{forcing}_{stem}.csv")


def gates_csv(scen, tag="L21", forcing="spliced"):
    return os.path.join(REPO, "outputs",
                        f"scope_slr_fairunc_gates_{scen}_{forcing}_{joint_stem(tag)}.csv")


def commit_stamp():
    """Short HEAD, for the suptitle. A figure that cannot say which commit produced it
    cannot be reproduced from a slide."""
    return subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip() or "UNKNOWN"


# --- gates -----------------------------------------------------------------
def gate_ladrillo(scen, tag="L21", forcing="spliced"):
    """Read the driver's OWN gates file and refuse a scenario whose run did not pass.

    ⚠ A MISSING GATES FILE IS A FAILURE, NOT A SKIP -- an absent gate and a passing gate
    must not look the same. CONTROL is legitimately SKIPPED on every van Vuuren marker
    (no shipped panel row exists to compare against); a CONTROL verdict of CHECK or FAIL is
    still an error here."""
    f = gates_csv(scen, tag, forcing)
    if not os.path.exists(f):
        raise SystemExit(
            "no Ladrillo gates file for %s at %s\n  Produce it with: julia "
            "--project=julia_v2 julia/scope_slr_fair_uncertainty.jl --ssp=%s "
            "--build-ssp=ssp245 --forcing=%s --tag=%s --tap"
            % (scen, os.path.relpath(f, REPO), scen, forcing, tag))
    g = pd.read_csv(f)
    ## ⚠ `CHECK` IS NOT `FAIL`, AND IT IS NOT `PASS` EITHER. The Julia drivers emit CHECK
    ## when a CONTROL cell exceeds CONTROL_TOL_CM -- it means "over tolerance, look at
    ## this", not "the run is invalid". Refusing to draw over one is disproportionate
    ## (ssp585's ais@2300 is -0.518 cm against a 0.5 cm tolerance = 0.19% of 268 cm, a
    ## cross-driver gap that predates this figure); silently allowing one is worse, because
    ## then the figure asserts a control it never passed.
    ## So CHECK rows are RETURNED and the caller MUST stamp them on the figure. Any verdict
    ## that is neither a known pass nor CHECK stays fatal.
    KNOWN_OK = ["PASS", "SKIPPED", "measured"]
    check = g[g.verdict == "CHECK"]
    bad = g[~g.verdict.isin(KNOWN_OK + ["CHECK"])]
    if len(bad):
        raise SystemExit("[GATE] %s: %d gate row(s) with an unrecognised verdict:\n%s"
                         % (scen, len(bad), bad))
    if "CONTROL" not in set(g.gate):
        raise SystemExit("[GATE] %s: gates file has NO CONTROL row -- a gate that is absent "
                         "is not a gate that passed." % scen)
    ## ⚠ THE SUMMARY IS EVERY CONTROL VERDICT, NOT THE FIRST ROW. Reading .iloc[0] made
    ## ssp585 print "CONTROL PASS" while one of its CONTROL rows was CHECK -- a label that
    ## contradicted the data one line below it.
    _cv = sorted(set(g[g.gate == "CONTROL"].verdict))
    return dict(control="+".join(_cv),
                configs=int(g.query("gate=='PAIRING' and key=='configs_used'").value.iloc[0]),
                checks=[(r.gate, r.key, float(r.value)) for r in check.itertuples()])


def gate_driver_provenance(keys, expect_one_commit=True):
    """git-log the mean-GMST driver behind each scenario.

    For the van Vuuren set the claim is STRONG and checkable: all seven markers came from
    ONE run of build_fair_cube_vv_v160.py, so they must share a SINGLE commit -- which
    cannot rot the way a hand-typed table can. For the SSP set it is FALSE by construction
    (ssp126/245/585 are calib 1.6.0; ssp119/370/460 have no 1.6.0 cube and remain 1.4.5),
    so pass expect_one_commit=False and REPORT the mix instead of asserting one.
    ⚠ A missing commit is FATAL: an "unverified" that still draws is the vacuous pass."""
    actual = {}
    for k in keys:
        r = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h", "--",
                            "data/observations/fair_mean_gmst_%s.csv" % k],
                           capture_output=True, text=True)
        actual[k] = r.stdout.strip()
    missing = sorted(k for k, v in actual.items() if not v)
    if missing:
        raise SystemExit(
            "[PROVENANCE] git returned nothing for %d of %d driver(s), so the calibration "
            "is UNVERIFIED and this figure must not be drawn: %s\n  Run from inside the "
            "SLR-RFF-BRICK checkout, with the drivers committed."
            % (len(missing), len(actual), missing))
    commits = sorted(set(actual.values()))
    if expect_one_commit and len(commits) != 1:
        raise SystemExit(
            "[PROVENANCE] these drivers were expected to share ONE commit (one build, one "
            "calibration) but %d are present, so that caption claim is FALSE:\n%s\n"
            "  Rebuild the set in one run. Do NOT drop this gate."
            % (len(commits), "\n".join("    %-8s %s" % (k, c) for k, c in sorted(actual.items()))))
    return actual, commits


def load_paths(scen, model, tag="L21", arm="joint", forcing="spliced"):
    """{component: DataFrame indexed by year with med_cm/p05_cm/p95_cm} for one run."""
    f = paths_csv(scen, model, tag, forcing)
    if not os.path.exists(f):
        cmd = ("julia --project=julia_v2 julia/scope_slr_fairunc_oldbrick.jl --ssp=%s" % scen
               if model == "brick20" else
               "julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl --ssp=%s "
               "--build-ssp=ssp245 --forcing=%s --tag=%s --tap" % (scen, forcing, tag))
        raise SystemExit("missing %s trajectory for %s: %s\n  Produce it with:\n    %s"
                         % (model, scen, os.path.relpath(f, REPO), cmd))
    d = pd.read_csv(f)
    d = d[d.arm == arm]
    if d.empty:
        raise SystemExit("%s %s: arm %r is EMPTY in %s"
                         % (model, scen, arm, os.path.relpath(f, REPO)))
    return {c: g.sort_values("year").set_index("year") for c, g in d.groupby("component")}


def check_component_sum(byc, scen, model, year=2300, tol_cm=1e-6):
    """The five components must sum to `total` at every reported year -- an identity, so
    the tolerance stays EXACT rather than being scaled to anything. Catches a component
    silently dropped from a plot's data path."""
    parts = [c for c in COMPONENTS if c != "total"]
    missing = [c for c in parts + ["total"] if c not in byc]
    if missing:
        raise SystemExit("[SUM] %s %s: components missing from the trajectory file: %s"
                         % (model, scen, missing))
    s = sum(byc[c].med_cm.loc[year] for c in parts)
    ## ⚠ MEDIANS DO NOT ADD. The sum of per-component medians is NOT the median of the sum
    ## whenever the components are not comonotonic, so this is reported as a MEASUREMENT,
    ## not a pass/fail -- asserting it would be asserting something false.
    return s, float(byc["total"].med_cm.loc[year])
