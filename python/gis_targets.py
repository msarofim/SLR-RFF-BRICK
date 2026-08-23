#!/usr/bin/env python3
"""
gis_targets.py — THE ONE PLACE Greenland 2300 target bands live.

WHY THIS EXISTS (2026-08-21g)
  Six scripts scored 2300 against `LIT_2300_M`; four imported it from
  `scope_gis_leq_ridge_vs_literature` and two carried their OWN copied literals
  (`plot_gis_basin_mock.py`, `plot_gis_rate_power_scan.py`). When 2026-08-21f
  established that the ssp585 band is the PROTECT `x2300` family -- forced to
  13.8 K at 2300 against our ssp585's 7.8 K -- there was no single edit that could
  correct all six. There is now.

TWO SETS, DELIBERATELY BOTH KEPT, AND NAMED SO THEY CANNOT BE CONFUSED

  LIT_2300_M      the raw literature bands, EXACTLY as transcribed. Each band was
                  produced at ITS OWN forcing, recorded in LIT_2300_FORCING.
                  Retained for provenance and for reproducing every pre-2026-08-21g
                  scorecard. NOT a like-for-like target for our scenarios.

  MATCHED_2300_M  what the PROTECT-Greenland physics ensemble implies AT OUR OWN
                  FORCING. Derived in build_gis_matched_targets.py, checked against
                  its CSV at import. THIS is the like-for-like target.

  DEFAULT_SET is "matched". Any script that scores 2300 must print banner() so the
  reader always knows which set produced the verdict.

WHAT ACTUALLY CHANGED, so this is not oversold
  ssp126 and ssp245 barely move -- their bands were already forcing-matched
  (integral ratios 1.10x and 1.00x against ours). ONLY ssp585 moves, and it moves a
  lot: 173-313 cm -> 43-145 cm, a factor 0.39. Every "ssp585 SHORT by 3.5-6.3x"
  in this repo before 2026-08-21g inherits the mismatch; no cool-scenario verdict
  does, so the k <= 1.25 kill from the pre-flight survives re-targeting.

THE COVERAGE CAVEAT TRAVELS WITH THE MATCHED SET
  Every anchor past 2100 is NORCE-CISM: ONE ice sheet model under many climate
  forcings. The p05-p95 is CLIMATE-forcing spread, NOT ice-sheet structural spread.
  A target, never a hard cut.
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCHED_CSV = os.path.join(REPO, "outputs/gis_matched_targets_2300.csv")

# --- SET 1: the raw literature bands, m SLE. UNCHANGED, kept for provenance. ---
# TC 19:6887 (2025) doi 10.5194/tc-19-6887-2025; TC 20:309 (2026) doi 10.5194/tc-20-309-2026
LIT_2300_M = {"SSP1-2.6": (0.058, 0.163), "SSP2-4.5": (0.098, 0.218),
              "SSP5-8.5": (1.732, 3.127)}
LIT_2300_NOTE = {"SSP1-2.6": "stabilised+ext (ext = 0.092)",
                 "SSP2-4.5": "stabilised (no continued-warming run reported)",
                 "SSP5-8.5": "CONTINUED-WARMING (the apples-to-apples arm)"}
# The forcing each band was produced at, MEASURED 2026-08-21g by
# scope_gis_cool_band_forcing.py. GSAT at 2300, 11-yr, C vs 1850-1900, n-weighted
# over the family's own GCMs; integral is 2015-2300 in K.yr. "ours" is
# data/observations/fair_mean_gmst_<ssp>.csv on the same convention.
LIT_2300_FORCING = {
    "SSP1-2.6": "r2300 1.96 K (int 544) + x2300 2.48 K (int 651) vs OURS 1.73 K "
                "(int 495) -- integral ratio 1.10x, MATCHED",
    "SSP2-4.5": "r2300 2.99 K (int 790) vs OURS 3.14 K (int 790) -- integral ratio "
                "1.00x, MATCHED",
    "SSP5-8.5": "x2300 13.80 K (int 2614) vs OURS 7.80 K (int 1626) -- integral "
                "ratio 1.61x, MISMATCHED; this band scores a hotter world than ours",
}

# --- SET 2: forcing-matched at OUR forcing, m SLE. -----------------------------
# Derived: build_gis_matched_targets.py -> outputs/gis_matched_targets_2300.csv.
# PCHIP through log(SLR@2300) vs the 2015-2300 GSAT INTEGRAL, over 5 anchors
# (ssp126 r/x2300, ssp245 r2300, ssp585 r/x2300) spanning 1.96-13.80 K, evaluated
# at our own scenario's integral. Outside the anchor hull the band is the UNION of
# the bracketing anchors instead -- see MATCHED_2300_RULE.
MATCHED_2300_M = {"SSP1-2.6": (0.062, 0.159), "SSP2-4.5": (0.106, 0.215),
                  "SSP5-8.5": (0.429, 1.450)}
MATCHED_2300_RULE = {
    "SSP1-2.6": "UNION of the bracketing anchors -- our integral is 10% BELOW the "
                "anchor hull, so this band is if anything GENEROUS",
    "SSP2-4.5": "PCHIP interpolation at our forcing (inside the anchor hull)",
    "SSP5-8.5": "PCHIP interpolation at our forcing (inside the anchor hull)",
}
MATCHED_2300_P50_M = {"SSP1-2.6": 0.111, "SSP2-4.5": 0.154, "SSP5-8.5": 0.985}
MATCHED_SOURCE = ("PROTECT-Greenland (Goelzer 2025) doi 10.11582/2025.lf9m2wd0, "
                  "NORCE-CISM long runs, control-drift-corrected, rel 2015")
MATCHED_CAVEAT = ("every anchor past 2100 is NORCE-CISM -- ONE ice sheet model, so "
                  "the p05-p95 is CLIMATE-forcing spread, NOT structural spread")

TARGET_SETS = {"lit": LIT_2300_M, "matched": MATCHED_2300_M}
DEFAULT_SET = "matched"
# Every printed label and every output filename derives from this, so a scorecard
# cannot print "literature band" while scoring the matched set, and a matched-set
# run cannot overwrite the artefact a lit-set verdict rests on.
SET_WORD = {"lit": "literature", "matched": "forcing-matched"}
SET_SUFFIX = {"lit": "_lit", "matched": "_matched"}
# Tolerance on the import-time check of the literals against the derivation CSV.
VERIFY_TOL_M = 5e-4


def get(name=None):
    """Return (bands, set_name). `name` defaults to DEFAULT_SET."""
    name = (name or DEFAULT_SET).lower()
    if name not in TARGET_SETS:
        raise SystemExit(f"unknown target set {name!r}; have {sorted(TARGET_SETS)}")
    return TARGET_SETS[name], name


def from_argv(argv, default=None):
    """Parse `--targets=lit|matched` out of argv. Returns (bands, set_name)."""
    pick = default
    for a in argv[1:]:
        if a.startswith("--targets="):
            pick = a.split("=", 1)[1]
    return get(pick)


def out_path(path, name=None):
    """Suffix an output path with the target set. A matched-set scan must never
    overwrite the artefact a lit-set verdict rests on, and vice versa."""
    _, name = get(name)
    root, ext = os.path.splitext(path)
    return root + SET_SUFFIX[name] + ext


def note(lab, name=None):
    """The per-band annotation appropriate to the set in use."""
    _, name = get(name)
    return LIT_2300_NOTE[lab] if name == "lit" else MATCHED_2300_RULE[lab]


def banner(name=None):
    """The line EVERY 2300 scorecard must print, so a verdict can never be read
    without knowing which target set produced it."""
    bands, name = get(name)
    head = (f"TARGET SET = {name.upper()} "
            + ("(raw literature, each band at ITS OWN forcing -- NOT like-for-like)"
               if name == "lit" else
               "(forcing-matched to OUR scenarios; " + MATCHED_SOURCE + ")"))
    lines = [head]
    for lab in ("SSP1-2.6", "SSP2-4.5", "SSP5-8.5"):
        lo, hi = bands[lab]
        note = LIT_2300_NOTE[lab] if name == "lit" else MATCHED_2300_RULE[lab]
        lines.append(f"  {lab:9} {lo * 100:6.1f}-{hi * 100:<6.1f} cm   [{note}]")
    if name == "lit":
        lines.append("  FORCING OF EACH BAND (measured 2026-08-21g):")
        lines += [f"    {k:9} {v}" for k, v in LIT_2300_FORCING.items()]
    else:
        lines.append(f"  CAVEAT: {MATCHED_CAVEAT}")
    return "\n".join(lines)


def ratio_band(bands=None):
    """The ssp585/ssp245 2300 separation implied by a target set, (lo, hi)."""
    bands = bands or MATCHED_2300_M
    return (bands["SSP5-8.5"][0] / bands["SSP2-4.5"][1],
            bands["SSP5-8.5"][1] / bands["SSP2-4.5"][0])


# --- THE SHIPPED TAP CELL, READ FROM THE JULIA COMPONENT --------------------
# WHY THIS IS PARSED AND NOT RETYPED (2026-08-23). The cell has moved three times
# -- (6.5 K, 2.0 m, 50 yr) first-order -> (4.69 K, 6.0 m, 800 yr) cascade ->
# (4.69 K, 5.64 m, 800 yr) cascade -- and each move left a copied literal behind on
# the python side. One of them was not a stale comment but a DEAD GUARD:
# build_protect_r2300_forcing.py asserted its arm was "tap-free" against ONSET_K =
# 6.5 long after the shipped onset had dropped to 4.69, so the assertion certified a
# threshold nothing was being tested at. The Julia const is the authority; this
# reads it, so a fourth move needs no python edit at all.
GIS3_COMPONENT_JL = os.path.join(REPO, "julia/greenland_3basin_component.jl")
_TAP_CELL_RE = re.compile(r"^const\s+GIS_TAP_CELL\s*=\s*\((.*?)\)\s*$",
                          re.MULTILINE | re.DOTALL)
_TAP_FIELD_RE = re.compile(r"(\w+)\s*=\s*([-\d.eE+]+|true|false)")


def tap_cell(path=GIS3_COMPONENT_JL):
    """The SHIPPED tap cell as a dict, parsed from `const GIS_TAP_CELL` in
    julia/greenland_3basin_component.jl -- the single source of truth. Keys are the
    Julia field names (onset_K, V_m, tau_yr, ramp_w_K, stages, wholesheet); numbers
    come back as float, `true`/`false` as bool. Raises if the constant is absent or
    has lost a field, because a partial parse would silently hand back a default."""
    with open(path) as fh:
        m = _TAP_CELL_RE.search(fh.read())
    if m is None:
        raise SystemExit(f"gis_targets.tap_cell: no `const GIS_TAP_CELL = (...)` in "
                         f"{os.path.relpath(path, REPO)} -- has the component moved?")
    cell = {k: (v == "true") if v in ("true", "false") else float(v)
            for k, v in _TAP_FIELD_RE.findall(m.group(1))}
    missing = {"onset_K", "V_m", "tau_yr", "ramp_w_K", "stages", "wholesheet"} - set(cell)
    if missing:
        raise SystemExit(f"gis_targets.tap_cell: GIS_TAP_CELL is missing "
                         f"{', '.join(sorted(missing))} -- refusing a partial cell")
    return cell


def tap_cell_label(cell=None):
    """One-line human label for the shipped cell, for console banners and captions."""
    c = cell or tap_cell()
    return (f"onset {c['onset_K']:.2f} K / V {c['V_m']:.2f} m / tau {c['tau_yr']:.0f} yr "
            f"/ n={int(c['stages'])} / {'whole-sheet' if c['wholesheet'] else 'high-basin'}")


def _verify():
    """Re-derive the MATCHED literals from the derivation CSV and refuse to import
    if they have drifted. The literals are here so a scorecard cannot silently
    depend on a regenerated file; the check is here so they cannot silently rot."""
    if not os.path.exists(MATCHED_CSV):
        return "matched-target CSV absent -- literals UNVERIFIED this import"
    import csv
    with open(MATCHED_CSV) as fh:
        for row in csv.DictReader(fh):
            lab = row["label"]
            lo, hi = float(row["band_lo_cm"]) / 100, float(row["band_hi_cm"]) / 100
            have = MATCHED_2300_M[lab]
            if abs(lo - have[0]) > VERIFY_TOL_M or abs(hi - have[1]) > VERIFY_TOL_M:
                raise SystemExit(
                    f"gis_targets: MATCHED_2300_M[{lab!r}] = {have} disagrees with "
                    f"{os.path.basename(MATCHED_CSV)} ({lo:.4f}, {hi:.4f}). Re-run "
                    f"build_gis_matched_targets.py and update the literal.")
    return "matched-target literals VERIFIED against the derivation CSV"


VERIFY_STATUS = _verify()

if __name__ == "__main__":
    import sys
    print(_verify() + "\n")
    for s in TARGET_SETS:
        print(banner(s))
        r = ratio_band(TARGET_SETS[s])
        print(f"  implied ssp585/ssp245 ratio band: {r[0]:.2f}-{r[1]:.2f}x\n")
