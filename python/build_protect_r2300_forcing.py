#!/usr/bin/env python3
"""
build_protect_r2300_forcing.py — the GMST path that FORCED the PROTECT-Greenland
`r2300` arm, on this repo's convention, as a Ladrillo driver.

WHY (2026-08-21, notes/handoff_2026-08-21b_protect_matched_forcing.md §5)
  The x2300 matched-forcing arm runs at 9.8-13.6 K against our 4.7-7.8 K, so it
  tests the model far outside our own scenario's range. `r2300` is the closer
  analogue AND the broader sample:

      family   post-2100 forcing        n (ssp585-like)   forcing GCMs   CISM configs
      x2300    natural CMIP6 extension        18                2            several
      r2300    HELD at the 2100 level         40                6            one

  Goelzer et al. 2025 (doi 10.5194/egusphere-2025-3098, open discussion): r2300 =
  "the climate forcing from 2100 is held constant and repeated through 2300";
  x2300 = the natural CMIP6 extension; and on the two, "Neither scenario is fully
  realistic, but the two approaches are complementary". A reviewer calls the repeat
  scenario "arguably more plausible than the latter".

  BECAUSE THE FORCING IS HELD AT 2100, THIS NEEDS NO POST-2100 CMIP6 DATA. Every
  GCM's ssp585 through 2100 is enough — which is exactly what the Pangeo mirror
  has (see [[pangeo_cmip6_no_ext]]: it stops at 2100 and that was fatal for x2300).

WHAT THIS ARM ACTUALLY TESTS — and it is NOT the tap
  The n-weighted plateau is 5.58 K and the spliced driver peaks at 6.32 K, both
  below the 6.5 K onset, so THE TAP NEVER FIRES on the arm that is actually run.
  ONE individual GCM does clear it -- UKESM1-0-LL holds at 6.52 K -- so a per-GCM
  r2300 arm would NOT be tap-free. Stated because the n-weighted result must not be
  generalised to "r2300 cannot fire the tap".
  That makes this a clean test of the BASE model's behaviour under CONSTANT
  forcing — i.e. of its committed-loss response, which is the other half of the
  x2300 finding (our base is 0.37x the physics at 2300 there). Asserted below so
  the arm cannot be silently misread as a tap test.

ACCESS1.3 IS DROPPED, FROM BOTH SIDES
  It is CMIP5 (rcp85) and not in the CMIP6 panel. Rather than fill it with a proxy,
  its 5 runs are dropped from the forcing AND from the comparison band, so the two
  sides are the same 35 runs. Reported, never silently kept.

MODEL-NAME ALIASES, stated because they are assumptions, not lookups
  "CESM2-Leo" -> CESM2 and "UKESM1-0-LL-Robin" -> UKESM1-0-LL. The PROTECT labels
  carry a contributor suffix; the underlying GCM is the CMIP6 source_id.

WRITES outputs/protect_r2300_forcing_gmst.csv
       outputs/cmip6_gsat_r2300_gcms.csv   (per-GCM GMST, incl. any Pangeo pulls)
  python3 python/build_protect_r2300_forcing.py
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_targets  # noqa: E402

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIS_DIR = os.path.join(REPO, "data/cmip6_gis")
ANN = os.path.join(REPO, "outputs/protect_greenland_gis_annual.csv")
OUT = os.path.join(REPO, "outputs/protect_r2300_forcing_gmst.csv")
OUT_GCM = os.path.join(REPO, "outputs/cmip6_gsat_r2300_gcms.csv")
CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"

Y0, Y1 = 1850, 2300
BASE_LO, BASE_HI = 1850, 1900        # 51-yr baseline, same as the x2300 reducer
HOLD_LO, HOLD_HI = 2081, 2100        # the 20-yr level r2300 repeats after 2100
SPLICE_YEAR = 2014                   # last year from our own path in the spliced arm
REF0, REF1 = 1995, 2014
SMOOTH = 11
## THE ONSET IS READ FROM THE JULIA CONSTANT, NEVER RETYPED. It was retyped here
## as 6.5, and when the shipped cell moved to 4.69 K the assertion below went on
## passing against a threshold nothing was being tested at. See gis_targets.tap_cell.
ONSET_K = gis_targets.tap_cell()["onset_K"]
## WHAT THIS ARM IS, DECLARED SO EITHER DIRECTION OF DRIFT IS CAUGHT. At the shipped
## onset the r2300 driver DOES clear the onset, so this forcing is NOT tap-free and
## a run on it is not a base-model test unless the tap is explicitly switched off
## (julia/diag_protect_forcing_matched.jl --untapped). It was tap-free at the
## original 6.5 K cell. The expectation is asserted rather than the bound, so a
## future onset that puts the arm back below it fails here and sends whoever
## changed it to the consumers that describe this arm.
EXPECT_TAP_FREE = False
ALIAS = {"CESM2-Leo": "CESM2", "UKESM1-0-LL-Robin": "UKESM1-0-LL"}
DROP = {"ACCESS1.3"}                 # CMIP5, dropped from BOTH sides


def from_pangeo(model):
    """cos(lat) + month-length annual global mean, matching reduce_cmip6_tas_gis.py.
    Only ever called for a GCM absent from data/cmip6_gis; r2300 needs <=2100 only."""
    import gcsfs
    cat = pd.read_csv(CATALOG_URL)
    fs = gcsfs.GCSFileSystem(token="anon")
    sub = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
              & (cat.source_id == model) & (cat.grid_label.isin(("gn", "gr", "gr1")))]
    common = set(sub[sub.experiment_id == "historical"].member_id) & \
             set(sub[sub.experiment_id == "ssp585"].member_id)
    if not common:
        sys.exit(f"{model}: no member with both historical and ssp585 on Pangeo")
    member = sorted(common)[0]
    frames = []
    for exp in ("historical", "ssp585"):
        row = sub[(sub.experiment_id == exp) & (sub.member_id == member)].iloc[0]
        ds = xr.open_zarr(fs.get_mapper(row.zstore), consolidated=True)
        w = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
        series = ds["tas"].weighted(w).mean(("lat", "lon"))
        dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                           coords={"time": ds.time})
        yr = ds.time.dt.year
        s = ((series * dim).groupby(yr).sum() / dim.groupby(yr).sum()).to_series()
        frames.append(pd.DataFrame({"year": s.index, "tas_global": s.values,
                                    "scenario": exp, "member": member}))
    print(f"  {model}: pulled from Pangeo, member {member}")
    return pd.concat(frames, ignore_index=True)


ann = pd.read_csv(ANN)
r = ann[ann.exp.str.contains("r2300") & ann.exp.str.contains("ssp585|rcp85")]
r = r.assign(gcm=r.exp.str.split("_").str[0])
runs = r.groupby(["group", "model", "exp"]).first().reset_index()
w_all = runs.gcm.value_counts()
w = w_all.drop(labels=[g for g in DROP if g in w_all.index])
print(f"r2300 ssp585-like runs: {int(w_all.sum())} total, "
      f"{int(w_all[list(DROP & set(w_all.index))].sum())} DROPPED ({', '.join(sorted(DROP))}, CMIP5), "
      f"{int(w.sum())} used")
print("  weights: " + ", ".join(f"{k} {v}" for k, v in w.items()))

paths, gcm_rows = {}, []
for gcm in w.index:
    model = ALIAS.get(gcm, gcm)
    f = os.path.join(GIS_DIR, f"tas_series_gis_{model}.csv")
    if os.path.exists(f):
        d = pd.read_csv(f)
        d = d[d.member == d.member.iloc[0]][["year", "tas_global", "scenario", "member"]]
    else:
        d = from_pangeo(model)
    hist = d[d.scenario == "historical"].set_index("year").tas_global
    scen = d[d.scenario == "ssp585"].set_index("year").tas_global
    base = hist.loc[BASE_LO:BASE_HI]
    if len(base) < (BASE_HI - BASE_LO + 1):
        sys.exit(f"{model}: baseline window incomplete ({len(base)} yr)")
    hold = (scen.loc[HOLD_LO:HOLD_HI].mean() - base.mean())
    anom = pd.concat([hist, scen]).sort_index() - base.mean()
    ## THE r2300 CONSTRUCTION: everything <=2100 is the GCM's own ssp585; everything
    ## after is the 2081-2100 mean, held. That is the dataset's own definition, not
    ## an approximation of it.
    full = anom.reindex(range(Y0, Y1 + 1))
    full.loc[2101:] = hold
    if full.isna().any():
        sys.exit(f"{model}: gaps in {Y0}-2100 — refusing to fill")
    paths[gcm] = full
    gcm_rows.append(pd.DataFrame({"year": full.index, "gcm": gcm, "model": model,
                                  "member": d.member.iloc[0], "gsat_anom_C": full.values,
                                  "hold_level_C": hold, "n_runs": int(w[gcm])}))
    print(f"    {gcm:20} ({model:14}) 2100 {anom.loc[2100]:5.2f} K | "
          f"HELD at {hold:5.2f} K from 2101")

pd.concat(gcm_rows, ignore_index=True).to_csv(OUT_GCM, index=False)

gcm = sum(paths[g] * w[g] for g in w.index) / w.sum()
ours = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_gmst_ssp585.csv")
                   ).set_index("year").gmst_C.loc[Y0:Y1]
off = ours.loc[REF0:REF1].mean() - gcm.loc[REF0:REF1].mean()
spliced = pd.concat([ours.loc[:SPLICE_YEAR], gcm.loc[SPLICE_YEAR + 1:] + off])

## DOES THE TAP FIRE ON THE DRIVER THAT IS RUN? Measured on the DRIVERS FED TO THE
## MODEL (n-weighted raw and spliced), not on the per-GCM paths, and checked against
## EXPECT_TAP_FREE rather than against a one-sided bound — the bound version passed
## for a month after the onset it was written for had been superseded.
peak = max(float(spliced.max()), float(gcm.max()))
tap_free = peak < ONSET_K
assert tap_free == EXPECT_TAP_FREE, (
    f"the n-weighted r2300 driver peaks at {peak:.2f} K against a {ONSET_K} K onset, "
    f"so this arm is {'' if tap_free else 'NOT '}tap-free — but EXPECT_TAP_FREE is "
    f"{EXPECT_TAP_FREE}. The shipped cell has moved across this arm's peak: update "
    f"EXPECT_TAP_FREE **and** every consumer that describes the arm "
    f"(julia/diag_protect_forcing_matched.jl names it in its --family block).")
hot = {g: float(p.loc[2200]) for g, p in paths.items() if float(p.loc[2200]) >= ONSET_K}
print(f"\nn-weighted plateau {gcm.loc[2200]:.2f} K, spliced peak {spliced.max():.2f} K, "
      f"onset {ONSET_K} K ({gis_targets.tap_cell_label()})")
if tap_free:
    print("  => the tap never fires on the driver that is run; this is a BASE-MODEL test.")
else:
    print("  => the driver CLEARS the onset: the tap FIRES on this arm. A run on this "
          "forcing is NOT a base-model test unless the tap is switched off explicitly "
          "(diag_protect_forcing_matched.jl --untapped).")
print("  per-GCM plateaus AT OR ABOVE the onset: "
      + (", ".join(f"{g} {v:.2f} K" for g, v in hot.items()) if hot else "none"))
print(f"splice offset over {REF0}-{REF1}: {off:+.3f} C")

out = pd.DataFrame({"year": range(Y0, Y1 + 1)}).set_index("year")
out["gmst_ours"] = ours
out["gmst_raw"] = gcm
out["gmst_spliced"] = spliced
for c in ("gmst_ours", "gmst_raw", "gmst_spliced"):
    out[f"{c}_{SMOOTH}yr"] = out[c].rolling(SMOOTH, center=True, min_periods=1).mean()
out["n_runs"] = int(w.sum())
out["weights"] = "|".join(f"{k}:{v}" for k, v in w.items())
out["dropped"] = "|".join(f"{g}:{int(w_all[g])}" for g in sorted(DROP) if g in w_all.index)
out["basis"] = (f"C vs 1850-1900; forcing HELD at each GCM's {HOLD_LO}-{HOLD_HI} mean "
                f"from 2101 (Goelzer 2025 r2300); spliced = ours <=2014 re-ref on 1995-2014")
out.reset_index().to_csv(OUT, index=False)
print(f"\n{'year':>5} {'ours':>7} {'r2300':>8}   (11-yr)")
for y in (2050, 2100, 2150, 2200, 2300):
    print(f"{y:>5} {out.loc[y,'gmst_ours_11yr']:7.2f} {out.loc[y,'gmst_spliced_11yr']:8.2f}")
print(f"\nwrote {os.path.relpath(OUT, REPO)}, {os.path.relpath(OUT_GCM, REPO)}")
