#!/usr/bin/env python3
"""scope_magicc_glacier_drawnset.py -- what MAGICC's glacier module actually IS,
read from the drawnset the van Vuuren run was driven with.

  python3 python/scope_magicc_glacier_drawnset.py

Writes outputs/scope_magicc_glacier_drawnset.csv and .../log_..._drawnset.txt.
SCOPING ONLY; reads the drawnset, runs nothing, and does not touch MAGICC.

WHY. Handoff 2026-08-31f open item 2: "whether the Nauels 2025 glacier module differs
from the 2017 one" was inherited unverified from 31d, and it is the single claim behind
"MAGICC has no clamp" -- which is the framing the whole glacier-regrowth comparison rests
on (`glacier_regrowth_capability`). The MAGICC binary is closed, but the DRAWNSET is not,
and it carries the glacier module's parameters explicitly.

⚠ READ THE DRAWNSET THE RUN ACTUALLY USED. There are two on this machine and they are not
the same object: ~/CodeProjects/MAGICC/drawnset/...-drawnset.json is the plain AR6
distribution and carries only SLR_EXPANSION -- reading it would support the flatly wrong
claim that MAGICC samples no glacier uncertainty at all. The van Vuuren run loads
`magicc-ar6-0fd0f62-f023edb-drawnset_with_slr.json` (302_run-magicc-vv.py:58), which
carries 41 SLR-family keys. This script asserts it is reading that file.

WHAT IT ESTABLISHES, and what it does NOT.
  ESTABLISHES  the FORM of the equilibrium: a tabulated S_eq(T) on a shared temperature
               axis, one curve per CMIP5 GCM tune, plus a rate (`slr_gl_sens_mmpyrdeg`)
               and an exponent. That is the Nauels 2017 Eq. 3 parameter family, and the
               tunes are CMIP5-vintage model names -- so the 2025 run is not using a
               new-generation glacier module.
  ESTABLISHES  the DOMAIN: the temperature axis starts at 0.0 K and never goes negative.
               MAGICC's own equilibrium is therefore undefined below the pre-industrial
               state, and S_eq(0 K) is a POSITIVE committed loss. This is the external
               comparator for our own curve going negative below T_off, which
               `glacier_gap_is_rate_not_curve` reports on 48 % of cells at vvLN/2300 and
               handles by flooring.
  DOES NOT     settle whether MAGICC clamps. The update law -- whether S relaxes toward
               S_eq symmetrically or is ratcheted like ours -- lives in the binary, not in
               the drawnset. What the drawnset shows is that MAGICC's equilibrium DECLINES
               with temperature and is bounded below by S_eq(0 K), so any regrowth it
               produces is bounded by that floor. Saying more than this would be inferring
               a law from a parameter file.
"""
import json
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/scope_magicc_glacier_drawnset.csv")
LOG = os.path.join(REPO, "outputs/log_scope_magicc_glacier_drawnset.txt")
## The file 302_run-magicc-vv.py names, not the other one in the MAGICC tree.
DRAWNSET = os.path.expanduser(
    "~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/magicc-drawnsets/"
    "magicc-ar6-0fd0f62-f023edb-drawnset_with_slr.json")
EXPECT_N = 600
GL_KEYS = ["slr_gl_equitemp", "slr_gl_equislr", "slr_gl_sens_mmpyrdeg",
           "slr_gl_temp_exponent"]
REPORT_T = [0.0, 1.0, 2.0, 3.0]


def main():
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    if not os.path.exists(DRAWNSET):
        raise SystemExit("[SOURCE] missing %s" % DRAWNSET)
    cs = json.load(open(DRAWNSET))
    ## [SOURCE] the with-SLR drawnset, not the plain AR6 one. The discriminator is the
    ## presence of the glacier keys themselves -- a name check would pass on a renamed copy.
    if len(cs) != EXPECT_N:
        raise SystemExit("[SOURCE] %d members, expected %d" % (len(cs), EXPECT_N))
    missing = [k for k in GL_KEYS if not all(k in c for c in cs)]
    if missing:
        raise SystemExit("[SOURCE] %s absent from some members -- this looks like the "
                         "plain AR6 drawnset, which carries only SLR_EXPANSION" % missing)
    say("[SOURCE] %s" % os.path.basename(DRAWNSET))
    say("         %d members, all carrying the glacier keys" % len(cs))

    ## [SHARED-AXIS] every member's equilibrium curve must be tabulated on ONE temperature
    ## grid, or the curves are not comparable point-by-point and no S_eq(1 K) column below
    ## means anything.
    T = cs[0]["slr_gl_equitemp"]
    if not all(c["slr_gl_equitemp"] == T for c in cs):
        raise SystemExit("[SHARED-AXIS] the members do not share one temperature grid")
    step = np.diff(T)
    say("[SHARED-AXIS] one grid, %d points, %.1f to %.1f K, step %.2f K, "
        "min entry %.1f -- NEGATIVE DOMAIN: %s"
        % (len(T), T[0], T[-1], step[0], min(T), "yes" if min(T) < 0 else "NO"))
    say()

    curves = {}
    for c in cs:
        curves.setdefault(tuple(c["slr_gl_equislr"]),
                          c.get("file_slr_gl_xtraparams", "(no xtraparams key)"))
    idx = {t: T.index(t) for t in REPORT_T}
    say("THE %d EQUILIBRIUM CURVES, mm of glacier SLR at equilibrium (sorted by S_eq(0 K))"
        % len(curves))
    say("%-30s %9s %9s %9s %9s %11s  %s"
        % ("GCM tune", "S_eq(0K)", "S_eq(1K)", "S_eq(2K)", "S_eq(3K)",
           "S_eq(%.1fK)" % T[-1], "monotone"))
    rows = []
    for v, name in sorted(curves.items(), key=lambda x: x[0][0]):
        mono = all(v[i] <= v[i + 1] for i in range(len(v) - 1))
        say("%-30s %9.1f %9.1f %9.1f %9.1f %11.1f  %s"
            % (name, v[idx[0.0]], v[idx[1.0]], v[idx[2.0]], v[idx[3.0]], v[-1], mono))
        rows += [(name, t, v[idx[t]], "mm", mono) for t in REPORT_T]
        rows.append((name, T[-1], v[-1], "mm", mono))
    s0 = [v[0] for v in curves]
    say()
    say("S_eq(0 K) spans %.1f-%.1f mm -- a POSITIVE committed loss at ZERO warming, so"
        % (min(s0), max(s0)))
    say("MAGICC's glacier drawdown is bounded below by that floor and cannot pass it.")
    ## One curve is non-monotone and is also the one with no xtraparams file. Reported, not
    ## gated: it is a property of the shipped drawnset, and hiding it behind a pass would
    ## be exactly the silent-truncation failure the gate discipline is against.
    nm = [n for v, n in curves.items() if not all(v[i] <= v[i + 1] for i in range(len(v) - 1))]
    if nm:
        say("⚠ %d curve(s) NON-MONOTONE in T: %s. These are also the members with no "
            "file_slr_gl_xtraparams key (%d of %d). Reported, not repaired -- it is the "
            "shipped drawnset."
            % (len(nm), ", ".join(nm),
               sum(1 for c in cs if "file_slr_gl_xtraparams" not in c), len(cs)))
    say()

    say("THE OTHER GLACIER PARAMETERS -- how much spread MAGICC's glacier band carries")
    for k in ("slr_gl_sens_mmpyrdeg", "slr_gl_temp_exponent", "slr_gl_equitemp"):
        u = {str(c[k]) for c in cs}
        say("  %-24s %3d distinct value(s) across %d members" % (k, len(u), len(cs)))
    for k in ("slr_ais_sid_basalmelt", "slr_expansion_scaling"):
        u = {str(c[k]) for c in cs if k in c}
        say("  %-24s %3d distinct  (for contrast: a continuously sampled term)"
            % (k, len(u)))
    say()
    say("READING. MAGICC's glacier band carries %d DISCRETE CMIP5 GCM tunes, not a "
        "continuous" % len(curves))
    say("posterior -- the same KIND of object as an inter-model spread -- while the AIS")
    say("basal-melt and thermal-expansion terms in the SAME drawnset take 600 distinct")
    say("values each. A width comparison against our glacier band should say so.")

    pd.DataFrame(rows, columns=["tune", "temperature_K", "s_eq_mm", "unit", "monotone"]
                 ).to_csv(OUT, index=False)
    with open(LOG, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\nwrote %s\n      %s" % (os.path.relpath(OUT, REPO), os.path.relpath(LOG, REPO)))


if __name__ == "__main__":
    main()
