#!/usr/bin/env python3
"""
diag_gis_committed_loss.py — Greenland's COMMITTED (multi-millennial equilibrium)
loss on each SSP path, both ladder arms, reported strictly SEPARATELY from the
realised sea-level rise the shipped posterior projects.

WHY THIS EXISTS
  Option C — replacing Ladrillo Greenland's linear committed loss L_eq = c1*T + c0
  with the Bochow-2023 equilibrium ladder as a DRIVER of realised SLR — was
  abandoned 2026-08-16. Across five structures no configuration both fitted the
  hindcast and moved 2300: the better the fit, the deader the ladder, because a
  throughput cap makes L_eq algebraically irrelevant wherever it binds. Three
  independent routes agree that 2300 Greenland is THROUGHPUT-limited, not
  COMMITMENT-limited.

  The surviving use, recommended when C was abandoned, is this: evaluate the
  equilibrium on each scenario's GMST as POST-PROCESSING, report both model
  families, label it as a multi-millennial equilibrium, and keep it out of the
  realised-SLR accounting. This script is that diagnostic. It needs no refit and
  no new vintage — it reads the shipped projection and the published ladder.

WHAT IT REPORTS, AND WHAT IT DELIBERATELY DOES NOT
  For each SSP and each of three warming levels — the PEAK of the path, the 2100
  level and the 2300 level — the committed loss is reported as the BRACKET
  formed by the two ladder rungs either side. It is NOT interpolated. Neither
  family resolves its own transition (both largest jumps are exactly one grid
  interval wide, diag_ladder_transition_resolution.py), so interpolating across
  one would invent a shape neither model measured. Where a bracket straddles a
  family's own transition interval the bracket is WIDE, and that width is the
  honest statement of what the ladder knows.

  Both arms are carried throughout. Nothing tips the choice: standing favours
  PISM (twice in ISMIP6-Greenland), physics on the disputed mechanism favours
  Yelmo (REMBO's retreat-precipitation feedback), Bochow's own authors decline
  to adjudicate, and the Last Interglacial is confounded (~45% of Eemian SMB
  change is insolation, not ambient temperature — van de Berg, ngeo1245).

  The equilibrium is a MULTI-MILLENNIAL object. Placing it beside realised 2300
  SLR measures how little of the commitment is discharged on our horizon; it is
  NOT a projection, and the ratio must never be read as one.

  THE RATIO IS ALWAYS AGAINST REALISED SLR AT THE END OF THE HORIZON (2300), for
  every warming level including the path peak. Dividing a peak-year commitment by
  the SLR realised in that same year would compare a commitment incurred in 2071
  against only the rise banked by 2071, which understates the discharge for no
  reason. Realised SLR at the evaluation year is carried alongside as context.

CAVEATS THAT SHIP WITH THE NUMBERS
  1. The ladder is an EQUILIBRIUM under SUSTAINED warming. It cannot represent
     overshoot reversibility, so for a peaking path (SSP1-2.6) the peak-level and
     2300-level commitments are two different questions and both are reported.
  2. Committed loss is measured from each model's own control ice sheet, whose
     zero-forcing reference is about +0.5 K GMT; realised SLR is relative to
     1995-2014. The offset between those two zero points is sub-0.1 m, well
     inside the bracket widths, and is NOT corrected for.
  3. Bochow's GMT is converted from their summer-forcing coordinate by
     GMT = dT_summer/1.19 + 0.5 (build_greenland_equilibrium_ladder.py).

READS   data/observations/greenland_equilibrium_bochow2023.csv   (the ladder)
        outputs/ssps_components_2300_<LADRILLO_TAG>.csv          (GMST + realised GIS)
WRITES  outputs/diag_gis_committed_loss.csv

  python3 python/diag_gis_committed_loss.py [--tag L12]
"""
import argparse
import os
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
# the bracket rule and the transition-interval locator are defined once, in the
# script that established that neither transition is resolved.
from diag_ladder_transition_resolution import (  # noqa: E402
    GMT_COL, LOSS_COL, committed_bracket, transition_report,
)

# --- named constants; every label and filename below derives from these -------
LADRILLO_TAG = "L12"
LADDER_TAG = "Bochow et al. 2023 equilibrium ladder (Nature 622:528, Zenodo 8155423)"
EQUILIBRIUM_LABEL = "multi-millennial equilibrium commitment (NOT a projection)"
REALISED_LABEL = "realised SLR contribution"
LADDER = os.path.join(REPO, "data/observations/greenland_equilibrium_bochow2023.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_committed_loss.csv")
GIS_COMPONENT = "gis"
EVAL_YEARS = [2100, 2300]          # levels evaluated in addition to the path peak

# --- literature benchmark for the REALISED 2300 contribution, m SLE ----------
# Added 2026-08-18 after Marcus asked whether the discharged fraction is
# defensible. The distinction between the two arms is LOAD-BEARING:
#
#   "stabilised" = year-2100 forcing repeated to 2300. Comparing Ladrillo to this
#       arm FLATTERS it, because Ladrillo keeps warming (ssp585 reaches 7.81 K by
#       2300 against ~4.69 K at 2100). Carried only to make that trap explicit.
#   "warming"    = climate forcing continued to 2300. This is the apples-to-apples
#       arm for Ladrillo's own GMST paths.
#
# Sources:
#   TC19:6887 (2025) doi 10.5194/tc-19-6887-2025 — physically-based GrIS ensemble,
#       both arms; SSP5-8.5-ext from IPSL-CM6A-LR and CESM2-WACCM.
#   TC20:309  (2026) doi 10.5194/tc-20-309-2026 — MAR-GISM coupled, SSP5-8.5
#       IPSL-CM6A-LR, 0/1/2-way coupling; reaches 5.1-7.1 m by 3000.
# 2026-08-21g. This is the ONE place in the repo that legitimately keeps its own
# 2300 dict: it is a TWO-ARM structure (stabilised vs continued-warming), not the
# single band gis_targets serves, and it carries an ssp585 stabilised band that
# appears nowhere else. Left as-is, with the re-target's finding attached:
#
#   The "warming" ssp585 band (1.732-3.127 m) is the PROTECT x2300 family, forced
#   to 13.80 K at 2300 against our ssp585's 7.80 K -- so the "LOW by 3.8-6.9x"
#   this file prints against it is partly a comparison at two different forcings.
#   The forcing-matched band for our own ssp585 is gis_targets.MATCHED_2300_M
#   ["SSP5-8.5"] = 0.429-1.450 m, against which the untapped base (0.500 m) is IN.
#
#   The "stabilised" ssp585 band transcribed here (0.282-1.230 m) is INDEPENDENTLY
#   CORROBORATED by the 2026-08-21g extraction: the PROTECT r2300 ssp585 family
#   (35 runs, forcing held at each GCM's 2081-2100 mean) gives p05-p95
#   0.298-1.087 m. Same arm, same range, transcription and raw NetCDFs agreeing.
#   Note that arm is forced to 5.58 K, COOLER than our 7.80 K -- so it is not
#   apples-to-apples either, in the opposite direction. Neither raw arm brackets
#   our scenario; the matched band is the interpolation between them.
LIT_2300_M = {
    "SSP1-2.6": {"stabilised": (0.058, 0.163), "warming": (0.092, 0.092)},
    "SSP2-4.5": {"stabilised": (0.098, 0.218), "warming": None},
    "SSP5-8.5": {"stabilised": (0.282, 1.230), "warming": (1.732, 3.127)},
}
LIT_CITE = ("TC 19:6887 (2025) doi 10.5194/tc-19-6887-2025; "
            "TC 20:309 (2026) doi 10.5194/tc-20-309-2026")
HORIZON_YEAR = 2300                # realised SLR is discharged against THIS year
PLOT_LEVEL_KEY = "y2300"           # the evaluation level the literature check uses
SSP_ORDER = ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]
# within this factor of the literature arm counts as agreement rather than a
# discrepancy: a single-model extension is not precise enough to call a 10% gap
AGREEMENT_TOL = 1.25
CM_PER_M = 100.0


def ssps_path(tag):
    return os.path.join(REPO, f"outputs/ssps_components_2300_{tag}.csv")


def eval_points(x):
    """The warming levels at which the commitment is evaluated, per SSP path."""
    pk = x.loc[x.gmst.idxmax()]
    pts = [("peak", int(pk.year), float(pk.gmst))]
    for y in EVAL_YEARS:
        r = x[x.year == y]
        if len(r):
            pts.append((f"y{y}", y, float(r.gmst.iloc[0])))
    return pts


def bracket_row(g, T, jump_lo, jump_hi):
    """Committed-loss bracket at GMT T, with the flags that qualify it."""
    lo, hi = committed_bracket(g, T)
    if lo is None:                       # below the ladder's lowest rung
        return dict(committed_lo_m=float("nan"), committed_hi_m=float(hi[LOSS_COL]),
                    rung_lo_K=float("nan"), rung_hi_K=float(hi[GMT_COL]),
                    below_ladder=True, saturated=False, straddles_transition=False)
    if hi is None:                       # above the top rung: equilibrium saturated
        return dict(committed_lo_m=float(lo[LOSS_COL]), committed_hi_m=float(lo[LOSS_COL]),
                    rung_lo_K=float(lo[GMT_COL]), rung_hi_K=float("nan"),
                    below_ladder=False, saturated=True, straddles_transition=False)
    straddles = (abs(float(lo[GMT_COL]) - jump_lo) < 1e-9
                 and abs(float(hi[GMT_COL]) - jump_hi) < 1e-9)
    return dict(committed_lo_m=float(lo[LOSS_COL]), committed_hi_m=float(hi[LOSS_COL]),
                rung_lo_K=float(lo[GMT_COL]), rung_hi_K=float(hi[GMT_COL]),
                below_ladder=False, saturated=False, straddles_transition=straddles)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=LADRILLO_TAG,
                    help=f"Ladrillo posterior vintage (default {LADRILLO_TAG})")
    args = ap.parse_args()
    tag = args.tag

    ladder = pd.read_csv(LADDER)
    fams = {m: g.sort_values(GMT_COL).reset_index(drop=True)
            for m, g in ladder.groupby("model")}
    jumps = {m: transition_report(m, g) for m, g in fams.items()}

    comp = pd.read_csv(ssps_path(tag))
    gis = comp[comp.component == GIS_COMPONENT]

    print(f"GREENLAND COMMITTED LOSS — {EQUILIBRIUM_LABEL}")
    print(f"  ladder     : {LADDER_TAG}")
    print(f"  warming    : {tag} SSP GMST paths, rel. 1850-1900")
    print(f"  realised   : {tag} {REALISED_LABEL}, GIS component, rel. 1995-2014\n")
    print("  Brackets are the two rungs either side. NOT interpolated: neither")
    print("  family resolves its own transition, so a bracket that straddles it")
    print("  is wide because the ladder genuinely does not know.\n")
    for m, j in jumps.items():
        print(f"  {m:12s} transition (unresolved) between "
              f"{j['jump_lo_K']:.3f} and {j['jump_hi_K']:.3f} K, "
              f"jump {j['jump_m_sle']:.2f} m")
    print()

    rows = []
    for s, x in gis.groupby("ssp"):
        x = x.sort_values("year")
        print(f"--- {s} " + "-" * (58 - len(s)))
        h = x[x.year == HORIZON_YEAR].iloc[0]
        realised_h = float(h.med) / CM_PER_M
        h05, h95 = float(h.p05) / CM_PER_M, float(h.p95) / CM_PER_M
        print(f"  {REALISED_LABEL} at {HORIZON_YEAR}: {realised_h:5.3f} m "
              f"[{h05:.3f}, {h95:.3f}]  <- every ratio below is against this\n")
        for level, year, T in eval_points(x):
            at_year = float(x[x.year == year].med.iloc[0]) / CM_PER_M
            print(f"  {level:6s} {year}  GMT {T:5.2f} K   "
                  f"(realised by {year}: {at_year:5.3f} m)")
            mids = {}
            for m, g in fams.items():
                b = bracket_row(g, T, jumps[m]["jump_lo_K"], jumps[m]["jump_hi_K"])
                mid = 0.5 * (b["committed_lo_m"] + b["committed_hi_m"])
                mids[m] = mid
                flag = ("SATURATED (above top rung)" if b["saturated"]
                        else "STRADDLES THE UNRESOLVED TRANSITION"
                        if b["straddles_transition"] else "")
                span = (f"{b['committed_lo_m']:5.2f} m"
                        if b["saturated"] else
                        f"{b['committed_lo_m']:5.2f} .. {b['committed_hi_m']:5.2f} m")
                print(f"         committed {m:12s} {span}   "
                      f"{100 * realised_h / mid:5.1f}% discharged by "
                      f"{HORIZON_YEAR}   {flag}")
                rows.append(dict(ssp=s, level=level, year=year, gmt_K=T, model=m,
                                 realised_at_year_m=at_year,
                                 realised_horizon_m=realised_h,
                                 realised_horizon_p05_m=h05,
                                 realised_horizon_p95_m=h95,
                                 horizon_year=HORIZON_YEAR,
                                 committed_mid_m=mid,
                                 frac_discharged_by_horizon=realised_h / mid,
                                 ladrillo_tag=tag, **b))
            ratio = max(mids.values()) / min(mids.values())
            print(f"         -> arms differ by {ratio:.2f}x\n")

    print("=" * 66)
    print("LITERATURE CHECK on the REALISED 2300 contribution (the numerator)")
    print(f"  {LIT_CITE}\n")
    print("  The discharged fraction is only as defensible as the realised SLR")
    print("  feeding it. Compare against the CONTINUED-WARMING arm: Ladrillo keeps")
    print("  warming, so the stabilised arm is not apples-to-apples and comparing")
    print("  to it flatters the model.\n")
    for s_ in SSP_ORDER:
        sub = pd.DataFrame(rows)
        sub = sub[(sub.ssp == s_) & (sub.level == PLOT_LEVEL_KEY)]
        if not len(sub):
            continue
        real = float(sub.realised_horizon_m.iloc[0])
        lit = LIT_2300_M[s_]
        st, wm = lit["stabilised"], lit["warming"]
        print(f"  {s_}  Ladrillo {real:.3f} m")
        print(f"      stabilised-forcing lit {st[0]:.3f}-{st[1]:.3f} m"
              f"   {'INSIDE' if st[0] <= real <= st[1] else 'OUTSIDE'}"
              f"  (not apples-to-apples)")
        if wm is None:
            print("      continued-warming lit  not reported for this scenario")
        else:
            lo_f = wm[0] / real
            hi_f = wm[1] / real
            if wm[0] <= real <= wm[1] or max(lo_f, 1 / hi_f) <= AGREEMENT_TOL:
                verdict = "CONSISTENT"
            elif real < wm[0]:
                verdict = f"LADRILLO LOW by {lo_f:.1f}-{hi_f:.1f}x"
            else:
                verdict = "LADRILLO HIGH"
            print(f"      continued-warming lit  {wm[0]:.3f}-{wm[1]:.3f} m   {verdict}")
            cmid = float(sub.committed_mid_m.mean())
            print(f"      => discharged: Ladrillo {100 * real / cmid:.1f}% vs "
                  f"literature {100 * wm[0] / cmid:.1f}-{100 * wm[1] / cmid:.1f}%")
        print()

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"wrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
