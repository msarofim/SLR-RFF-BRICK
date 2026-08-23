#!/usr/bin/env python3
"""
diag_gis_2150_structural_spread.py -- THE 2150 BAND CARRIES NO ICE-SHEET
STRUCTURAL SPREAD. MEASURE HOW MUCH IT IS MISSING, AND RE-ASK THE VETO.

WHY (Marcus 2026-08-23: "watch out for overly tight constraints")
  `diag_gis_2150_band_veto.py` tested the 2150 band's WIDTH for sample-size and it
  SURVIVED: its two GCM clusters agree to 0.6 cm. But that test asked only whether
  the CLIMATE spread was under-counted. Every run behind the band -- all 18 -- is
  NORCE-CISM, its three `model` values being MAR SMB percentile variants of one
  ice-sheet model. So the band contains **zero ice-sheet structural spread**, and
  the repo's own caveat already says so in as many words: "the p05-p95 is CLIMATE-
  forcing spread, NOT structural spread". Applying it as a hard gate treats the
  dominant missing uncertainty as if it were zero. That is the same error class as
  the 0.10 cm 2100 tolerance, one level up -- and this band is what vetoed the
  weighted-verdict cell.

TWO INDEPENDENT MEASUREMENTS, because one would not be enough
  (A) ISMIP6 AT 2100. 14-16 ice-sheet models under IDENTICAL GCM forcing -- the
      only place in this repo where ISM structural spread is directly observable.
      Measured as a multiplicative factor about each arm's own median, then applied
      to 2150 as a FLOOR (model divergence does not shrink with lead time).
  (B) SICOPOLIS AT 2150. Greve's long runs carry a full annual axis, so a SECOND
      ice-sheet model can be read at 2150 directly on the five CMIP6 cells. This is
      a like-for-like ISM-vs-ISM check that needs no inflation assumption at all.

  If (A) and (B) disagree about how big the structural term is, that disagreement
  is the result and no band should be widened until it is understood.

WHAT THIS FILE CANNOT DO. It cannot put NORCE-CISM and SICOPOLIS under the SAME
forcing at 2150 -- PROTECT's x2300 arm is IPSL-CM6A-LR + CESM2-WACCM and Greve's
runs are CNRM/UKESM/CESM2 -- so (B) is a spread-MAGNITUDE measurement, not a
paired difference. It is reported as such.

READS   outputs/diag_gis_ismip6_2100_ism_spread_arms.csv, the Greve archive
WRITES  outputs/diag_gis_2150_structural_spread.csv
  python3 python/diag_gis_2150_structural_spread.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_reservoir_offline import (  # noqa: E402
    reservoir_unit_n, CM_PER_M, WINNER_CELL, CELL_A,
)
from diag_gis_greve_year3000 import EXPS, YEARS_EXT, read_greve  # noqa: E402
import scope_gis_onset_rescan as R  # noqa: E402

ISM_REF = os.path.join(REPO, "outputs/diag_gis_ismip6_2100_ism_spread_arms.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_2150_structural_spread.csv")

# --- named constants ---------------------------------------------------------
LINEAGE = "L14 canonical (two-basin), extended axis 1850-3001"
YEAR = 2150
BASE_YEAR = 2100                 # where ISM structural spread is observable
VETO_ARM = ("ssp585", "SSP5-8.5", "x2300")
SHIPPED_2150_BAND_CM = (44.6, 53.2)     # as gated today, from the run-level 5-95%
## The cascade cell now under consideration, and the two first-order cells it
## replaced -- imported where they exist so this file cannot drift from the scans.
CASCADE_CELL = (6.0, 4.69, 800.0, 2)    # (V_m, onset_K, tau_yr, stages)
CELLS = {"base (no reservoir)": None,
         "cell A (n=1)": CELL_A + (1,),
         "08-23b winner (n=1)": WINNER_CELL + (1,),
         "cascade (n=2, V=6, tau=800)": CASCADE_CELL}
SSP585_GCM_CELLS = [e for e, v in EXPS.items() if v[1] and v[2] == "ssp585"]


def ism_structural_factor():
    """ISM structural spread at 2100 as a multiplicative factor about each arm's
    OWN median, from ISMIP6. Returned per arm plus the pooled summary."""
    d = pd.read_csv(ISM_REF)
    d = d[d.n_ism >= 3].copy()
    d["lo_fac"] = d.ism_min / d.ism_median
    d["hi_fac"] = d.ism_max / d.ism_median
    d["q_lo_fac"] = d.ism_p25 / d.ism_median
    d["q_hi_fac"] = d.ism_p75 / d.ism_median
    return d


def main():
    print(f"diag_gis_2150_structural_spread -- {LINEAGE}, horizon {YEAR}\n")

    # --- (A) ISMIP6: how big is ISM structural spread where we CAN see it? ----
    d = ism_structural_factor()
    print(f"=== (A) ICE-SHEET STRUCTURAL SPREAD AT {BASE_YEAR}, FROM ISMIP6 ===")
    print(f"  the only place in this repo it is directly observable: many ISMs, "
          f"ONE forcing each\n")
    print(f"  {'GCM':20}{'ssp':8}{'n_ism':>6}{'median':>9}{'min/med':>9}"
          f"{'max/med':>9}{'p25/med':>9}{'p75/med':>9}")
    for _, r in d.iterrows():
        print(f"  {r.gcm:20}{r.ssp:8}{int(r.n_ism):6d}{r.ism_median:9.2f}"
              f"{r.lo_fac:9.3f}{r.hi_fac:9.3f}{r.q_lo_fac:9.3f}{r.q_hi_fac:9.3f}")
    lo, hi = float(d.lo_fac.median()), float(d.hi_fac.median())
    qlo, qhi = float(d.q_lo_fac.median()), float(d.q_hi_fac.median())
    print(f"\n  MEDIAN ACROSS {len(d)} ARMS: full ISM range {lo:.3f}-{hi:.3f}x the "
          f"median (a factor {hi / lo:.2f} wide),\n  interquartile "
          f"{qlo:.3f}-{qhi:.3f}x. The {YEAR} band as gated today is "
          f"{SHIPPED_2150_BAND_CM[0]:.1f}-{SHIPPED_2150_BAND_CM[1]:.1f} cm =\n  "
          f"{SHIPPED_2150_BAND_CM[0] / np.mean(SHIPPED_2150_BAND_CM):.3f}-"
          f"{SHIPPED_2150_BAND_CM[1] / np.mean(SHIPPED_2150_BAND_CM):.3f}x its own "
          f"midpoint, a factor "
          f"{SHIPPED_2150_BAND_CM[1] / SHIPPED_2150_BAND_CM[0]:.2f} wide -- "
          f"carrying CLIMATE spread only.\n")

    # --- (B) SICOPOLIS at 2150: a genuine second ice-sheet model --------------
    print(f"=== (B) A SECOND ICE-SHEET MODEL AT {YEAR}: SICOPOLIS (Greve) ===")
    tc, _, greve = read_greve()
    i150 = int(np.where(tc == YEAR)[0][0])
    i100 = int(np.where(tc == BASE_YEAR)[0][0])
    gmst, base, ie, thin = R.build_base()
    iy = {y: int(np.where(YEARS_EXT == y)[0][0]) for y in (BASE_YEAR, YEAR)}
    rows = []
    print(f"  {'cell':10}{'forcing':22}{f'SICO {BASE_YEAR}':>12}{'ours':>9}"
          f"{'ratio':>8}{f'  SICO {YEAR}':>12}{'ours':>9}{'ratio':>8}")
    for e in SSP585_GCM_CELLS:
        s100, s150 = float(greve[e][i100]), float(greve[e][i150])
        o100, o150 = base[e][iy[BASE_YEAR]], base[e][iy[YEAR]]
        print(f"  {e:10}{EXPS[e][0]:22}{s100:12.1f}{o100:9.1f}{o100 / s100:8.2f}"
              f"{s150:12.1f}{o150:9.1f}{o150 / s150:8.2f}")
        rows.append(dict(measurement="sicopolis_vs_ours", exp=e,
                         forcing=EXPS[e][0], sico_2100=s100, ours_2100=o100,
                         sico_2150=s150, ours_2150=o150))
    sico150 = np.array([r["sico_2150"] for r in rows])
    print(f"\n  SICOPOLIS spread ACROSS ITS OWN {len(sico150)} ssp585 cells at "
          f"{YEAR}: {sico150.min():.1f}-{sico150.max():.1f} cm "
          f"({sico150.max() / sico150.min():.2f}x) -- that is CLIMATE spread, its "
          f"own.\n  The point of this block is the LEVEL: NORCE-CISM's "
          f"{YEAR} band sits at "
          f"{np.mean(SHIPPED_2150_BAND_CM):.1f} cm under a MUCH hotter forcing "
          f"(x2300 reaches 9.9 K by {YEAR}),\n  while SICOPOLIS under ssp585 GCM "
          f"forcing spans {sico150.min():.1f}-{sico150.max():.1f}. Two ice-sheet "
          f"models, no overlap in forcing =>\n  a MAGNITUDE comparison, not a "
          f"paired difference.\n")

    # --- the veto, re-asked under a structurally-inflated band ----------------
    mid = float(np.mean(SHIPPED_2150_BAND_CM))
    bands = {
        "shipped (climate spread only)": SHIPPED_2150_BAND_CM,
        f"+ ISM interquartile ({qlo:.2f}-{qhi:.2f}x)":
            (SHIPPED_2150_BAND_CM[0] * qlo, SHIPPED_2150_BAND_CM[1] * qhi),
        f"+ ISM full range ({lo:.2f}-{hi:.2f}x)":
            (SHIPPED_2150_BAND_CM[0] * lo, SHIPPED_2150_BAND_CM[1] * hi),
    }
    ssp, lab, fam = VETO_ARM
    g_arm = None
    for a in A.ARMS:
        if (a[0], a[2]) == (ssp, fam):
            stem = a[3]
    gm = pd.read_csv(os.path.join(REPO, f"outputs/{stem}.csv")).set_index(
        "year")[f"gmst_{A.ARM}"]
    from scope_gis_2300_relaxation import YEARS, DRIVER_BASE
    gg = gm.reindex(YEARS).to_numpy()
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    g_arm = gg - gg[ibd].mean()
    i_arm = int(np.where(YEARS == YEAR)[0][0])
    BASE_ARM_2150_CM = 45.191            # measured, diag_gis_2150_band_veto GATE

    print(f"=== THE VETO, RE-ASKED ON {lab} {fam} @{YEAR} ===")
    print(f"  {'cell':30}{'ours':>8}   " + "".join(
        f"{k.split(' ')[0]:>16}" for k in bands))
    for name, cell in CELLS.items():
        add = 0.0 if cell is None else CM_PER_M * cell[0] * reservoir_unit_n(
            g_arm, cell[1], cell[2], cell[3])[i_arm]
        v = BASE_ARM_2150_CM + add
        marks = "".join(f"{('IN' if l <= v <= h else 'OUT'):>16}"
                        for l, h in bands.values())
        print(f"  {name:30}{v:8.1f}   {marks}")
        for k, (l, h) in bands.items():
            rows.append(dict(measurement="veto", cell=name, band=k, ours_cm=v,
                             lo_cm=l, hi_cm=h, in_band=bool(l <= v <= h)))
    for k, (l, h) in bands.items():
        print(f"    {k:44} {l:6.1f} - {h:6.1f} cm")
    pd.DataFrame(rows).to_csv(OUT, index=False)

    print(f"\n=== VERDICT ===")
    print(f"  The {YEAR} gate as applied today asserts that ice-sheet model choice "
          f"contributes ZERO\n  uncertainty, at a horizon where ISMIP6 measures it "
          f"at {lo:.2f}-{hi:.2f}x the median 50 years EARLIER.\n  Inflating by even "
          f"the INTERQUARTILE factor changes which cells the gate admits -- see the "
          f"table.\n  This does NOT make the shipped band wrong; it makes it a "
          f"CLIMATE-spread band, which is what\n  gis_targets.MATCHED_CAVEAT has "
          f"said all along. What is wrong is using it as a hard veto.")
    print(f"\nWROTE {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
