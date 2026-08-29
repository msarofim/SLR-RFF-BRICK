#!/usr/bin/env python3
"""
reduce_cmip6_tas_coulon.py — annual global-mean and AIS-mean tas, 1850-2300, for
the FOUR GCMs that force Coulon et al. 2025 (Nat. Commun. 16:10385), ssp585 AND
ssp126.

WHY: the Ladrillo AIS arms were respecified on the 2015-2300 temperature INTEGRAL
(Marcus, 2026-08-28) after AIS@2300 was measured ~linear in it. Coulon's forcing
is CMIP6 GCM output, so their own integral is computable rather than assumable --
which is what makes the arm comparison like-for-like instead of endpoint-matched.

WRITES data/cmip6_coulon/tas_series_<model>.csv
  columns: year, member, tas_global, tas_ais, scenario   (Kelvin)

COVERAGE IS EMITTED AS EACH MODEL ACTUALLY HAS IT -- 2300 for three, 2299 for
CESM2-WACCM -- and is NOT truncated here. The consumer integrates 2015-2299 for
all four so the window is identical across models and cancels in every
cross-model comparison (Ladrillo, 2026-08-28); that window is its named constant.
Baking the truncation into the data would hide the real coverage from a later
reader.

⚠ A SEPARATE DIRECTORY, ON PURPOSE. The schema is identical to data/cmip6_pai/,
but pai_series.SIBLING_PREFIXES is ("ohc_deck","hemis","deck","ext") and anything
else matching tas_series_*.csv IS TREATED AS A MODEL. A file named
tas_series_coulon_<model>.csv dropped in there would silently enter the 36-model
PAI ensemble as a model called "coulon_<model>" and move every median and spread
in those diagnostics. Same schema, separate namespace.

⚠ MEMBER IS NOT UNIFORM. UKESM1-0-LL extended ONLY r4i1p1f2 (r1/r2/r3/r8 stop at
2100) while data/cmip6_pai/ carries r1i1p1f2, so UKESM is rebuilt END TO END on
r4 -- historical included, because Coulon's 1995-2014 reference lives in the
historical leg and a mixed-member baseline is a mixed-member anomaly. The other
three extended the r1i1p1f1 already on disk and are spliced.

REDUCTION IS THE cmip6_pai CONVENTION, IMPORTED NOT RETYPED: cos(lat) global
weights; AIS = land (sftlf >= 50%) south of -60 deg, cos(lat)-weighted;
month-length-weighted annual means; weights rebuilt PER DATASET on its own coords
via pai_series.align_sftlf_to, and every series checked by
pai_series.assert_global_plausible. Both guards exist because reusing one
dataset's weights silently reduced a global mean by 7.4 K on the MPI family.

GATES
  [EXT-GATE]  post-2100 tas_global for IPSL-CM6A-LR and CESM2-WACCM must
              reproduce outputs/cmip6_ssp585ext_gsat.csv, which the 2026-08-21
              PROTECT-Greenland work derived from the SAME ESGF files through an
              independent implementation. That is an independent check of this
              reduction, not a self-consistency one.
  [JOIN]      |value(2101) - value(2100)| must be within JOIN_TOL_K, so a
              spliced series is continuous across the source change.
  plausibility on every emitted series.

    python3 python/reduce_cmip6_tas_coulon.py
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import xarray as xr
from pai_series import align_sftlf_to, assert_global_plausible

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NC_DIR = os.path.join(REPO, "data", "cmip6_coulon_ext")
PAI_DIR = os.path.join(REPO, "data", "cmip6_pai")
OUT_DIR = os.path.join(REPO, "data", "cmip6_coulon")
EXT_GATE_CSV = os.path.join(REPO, "outputs", "cmip6_ssp585ext_gsat.csv")
CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"

# ── the cmip6_pai convention, same values ───────────────────────────────────
SFTLF_MIN = 50.0
AIS_LAT_MAX = -60.0
# ssp585 ONLY, by the consumer's decision (Ladrillo, 2026-08-28). ssp126 was in
# the original request because Coulon reports both, but the arm comparison does
# not read it: julia/scope_ais_coulon_forcing.jl:65 pins `const SSP = "ssp585"`
# and every number in play -- the 12.0/14.5/17.0 targets, COULON_BAND (73,595),
# the 522 cm width behind the 0.96x/1.01x ratio -- is ssp585. ssp126 has no
# 2015-2100 half on disk either (reduce_cmip6_tas_pai.py:32 never fetched it), so
# emitting it would mean a series that silently starts at 2101. A HALF-BUILT
# ssp126 SERIES IS WORSE THAN NONE: it invites someone to complete it later for a
# comparison nobody asked for. The ssp126 post-2100 NetCDFs were already fetched
# and are kept in data/cmip6_coulon_ext/ -- sunk, harmless, and NOT reduced here.
# A low-scenario Coulon comparison is a real request with its own scoping.
SCENARIOS = ("ssp585",)
SPLICE_YEAR = 2100          # last year taken from the pre-existing/Pangeo half
# Members: UKESM is the exception and the reason this script has a member table.
MEMBERS = {"UKESM1-0-LL": "r4i1p1f2", "IPSL-CM6A-LR": "r1i1p1f1",
           "CESM2-WACCM": "r1i1p1f1", "MRI-ESM2-0": "r1i1p1f1"}
REBUILD_FROM_NC = ("UKESM1-0-LL",)   # member differs from cmip6_pai; no splice possible

# [EXT-GATE] tolerance. Both sides reduce the SAME NetCDF with the same cos(lat)
# weighting and the same month-length annual weighting, so the only difference is
# float accumulation order over ~1e5 grid cells x 12 months in float32/float64.
# Derived, not picked: float32 tas has ~1e-7 relative precision, and a ~290 K
# value accumulated over that many terms lands at ~1e-4 K worst case. A real
# convention difference (a different mask, a different annual weighting) shows at
# 1e-2 K or more, so this still discriminates by two orders of magnitude.
EXT_GATE_TOL_K = 1e-3
# [JOIN] tolerance: a year-to-year step in annual-mean GSAT under a strong
# forcing. Sized from the data rather than guessed -- see join_tol_from_series().
JOIN_SIGMA = 5.0


def annual_means(ds, wg, wa):
    """Month-length-weighted annual means of area-weighted global/AIS tas.
    reduce_cmip6_tas_pai.py:52-64, unchanged."""
    tas = ds["tas"]
    glob = tas.weighted(wg).mean(("lat", "lon"))
    ais = tas.weighted(wa).mean(("lat", "lon"))
    dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                       coords={"time": ds.time})
    yr = ds.time.dt.year
    out = {}
    for name, series in (("tas_global", glob), ("tas_ais", ais)):
        num = (series * dim).groupby(yr).sum()
        den = dim.groupby(yr).sum()
        out[name] = (num / den).to_series()
    return pd.DataFrame(out)


def join_tol_from_series(s):
    """A join step is acceptable if it is within JOIN_SIGMA of the series' OWN
    year-to-year variability -- derived from the quantity it tests, not picked."""
    d = np.abs(np.diff(np.asarray(s, dtype=float)))
    return JOIN_SIGMA * float(np.nanstd(d)) if d.size else np.inf


def load_sftlf(model, grid_label):
    """sftlf from the same Pangeo catalog that built data/cmip6_pai/."""
    import gcsfs
    cat = pd.read_csv(CATALOG_URL)
    lf = cat[(cat.variable_id == "sftlf") & (cat.source_id == model)
             & (cat.grid_label == grid_label)]
    if lf.empty:
        lf = cat[(cat.variable_id == "sftlf") & (cat.source_id == model)]
    if lf.empty:
        sys.exit(f"ERROR: no sftlf for {model}")
    fs = gcsfs.GCSFileSystem(token="anon")
    ds = xr.open_zarr(fs.get_mapper(lf.zstore.iloc[0]), consolidated=True)
    return ds["sftlf"].squeeze(drop=True)


def reduce_files(paths, sftlf, label):
    # open_dataset per file + concat, NOT open_mfdataset: the latter always routes
    # through a chunk manager and dask is not in this env. These load fine eagerly
    # (largest is MRI-ESM2-0 at 2400 months x 160 x 320 float32 ~ 0.5 GB).
    parts = [xr.open_dataset(p, use_cftime=True)[["tas"]] for p in sorted(paths)]
    ds = xr.concat(parts, dim="time") if len(parts) > 1 else parts[0]
    if ds.lat.ndim != 1:
        sys.exit(f"ERROR: {label}: non-regular grid")
    lf = align_sftlf_to(sftlf, ds, label)
    wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
    wa = wg.where((lf >= SFTLF_MIN) & (lf.lat <= AIS_LAT_MAX), 0.0)
    if float(wa.sum()) == 0.0:
        sys.exit(f"ERROR: {label}: empty AIS mask")
    df = annual_means(ds, wg, wa)
    assert_global_plausible(df.tas_global, label)
    # a concat of N files must cover N files' worth of months, contiguously
    yy = np.asarray(df.index, dtype=int)
    if np.any(np.diff(yy) != 1):
        sys.exit(f"ERROR: {label}: year axis has a gap -- files do not join")
    for d in parts:
        d.close()
    return df


def nc_for(model, exp, member, post_2100_only):
    pat = os.path.join(NC_DIR, f"tas_Amon_{model}_{exp}_{member}_*.nc")
    out = []
    for p in sorted(glob.glob(pat)):
        rng = os.path.basename(p).rsplit("_", 1)[-1][:-3]
        end = int(rng.split("-")[1][:4])
        if post_2100_only and end <= SPLICE_YEAR:
            continue
        out.append(p)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MEMBERS),
                    help="subset to reduce; default all four")
    args = ap.parse_args()
    want = [m.strip() for m in args.models.split(",")]
    os.makedirs(OUT_DIR, exist_ok=True)
    gate = pd.read_csv(EXT_GATE_CSV) if os.path.exists(EXT_GATE_CSV) else None
    gated = 0

    for model, member in MEMBERS.items():
        if model not in want:
            continue
        rebuild = model in REBUILD_FROM_NC
        print(f"\n── {model} ({member}){'  [rebuilt end to end]' if rebuild else ''}")
        grid = "gr" if model == "IPSL-CM6A-LR" else "gn"
        sftlf = load_sftlf(model, grid)
        frames = []

        # HISTORICAL IS EMITTED FOR EVERY MODEL, not just the rebuilt one: Coulon's
        # 1995-2014 reference period lives in the historical leg, so a series that
        # starts at 2015 cannot be turned into an anomaly at all. For the spliced
        # models it comes from data/cmip6_pai (same member, same convention); for
        # UKESM it is reduced from r4's own ESGF historical files.
        for exp in ("historical",) + SCENARIOS:
            paths = nc_for(model, exp, member, post_2100_only=not rebuild)
            new = reduce_files(paths, sftlf, f"{model}/{exp}") if paths else None
            if new is not None:
                print(f"   {exp:<11} ESGF {len(paths)} file(s) -> "
                      f"{int(new.index.min())}-{int(new.index.max())}")

            old = None
            if not rebuild:
                pai = os.path.join(PAI_DIR, f"tas_series_{model}.csv")
                d = pd.read_csv(pai)
                d = d[(d.scenario == exp) & (d.member == member)]
                if not d.empty:
                    old = d.set_index("year")[["tas_global", "tas_ais"]]
                    old = old[old.index <= SPLICE_YEAR]
                    print(f"   {exp:<11} cmip6_pai   -> "
                          f"{int(old.index.min())}-{int(old.index.max())}")
                elif exp == "ssp126":
                    print(f"   {exp:<11} ⚠ NO 2015-{SPLICE_YEAR} half on disk "
                          f"(reduce_cmip6_tas_pai.py never fetched ssp126); "
                          f"post-2100 only")

            if old is not None and new is not None:
                tol = join_tol_from_series(old.tas_global)
                step = abs(float(new.tas_global.iloc[0]) - float(old.tas_global.iloc[-1]))
                ok = step <= tol
                print(f"   {exp:<11} [JOIN] |{SPLICE_YEAR+1} - {SPLICE_YEAR}| = "
                      f"{step:.3f} K (tol {tol:.3f} = {JOIN_SIGMA}x own sd)  "
                      f"{'PASS' if ok else 'FAIL'}")
                if not ok:
                    sys.exit(f"ERROR: {model}/{exp} discontinuous at the splice")

            if gate is not None and new is not None and exp == "ssp585":
                g = gate[(gate.model == model) & (gate.scenario == "ssp585")
                         & (gate.year > SPLICE_YEAR)].set_index("year")["tas_global_K"]
                if not g.empty:
                    yy = g.index.intersection(new.index)
                    w = float(np.abs(new.loc[yy, "tas_global"].to_numpy()
                                     - g.loc[yy].to_numpy()).max())
                    ok = w <= EXT_GATE_TOL_K
                    print(f"   {exp:<11} [EXT-GATE] vs cmip6_ssp585ext_gsat.csv "
                          f"({len(yy)} yr): max |diff| = {w:.3e} K "
                          f"(tol {EXT_GATE_TOL_K:.0e})  {'PASS' if ok else 'FAIL'}")
                    if not ok:
                        sys.exit(f"ERROR: {model} post-2100 tas_global does not "
                                 f"reproduce the independent 2026-08-21 reduction")
                    gated += 1

            for part in (old, new):
                if part is not None:
                    f = part.reset_index()
                    f.columns = ["year"] + list(part.columns)
                    f["scenario"] = exp
                    frames.append(f)

        if not frames:
            print(f"   nothing to write for {model}")
            continue
        allf = pd.concat(frames, ignore_index=True)
        allf.insert(1, "member", member)
        allf = allf[["year", "member", "tas_global", "tas_ais", "scenario"]]
        allf["year"] = allf["year"].astype(int)
        dest = os.path.join(OUT_DIR, f"tas_series_{model}.csv")
        allf.to_csv(dest, index=False)
        span = ", ".join(f"{s} {allf[allf.scenario==s].year.min()}-"
                         f"{allf[allf.scenario==s].year.max()}"
                         for s in allf.scenario.unique())
        print(f"   wrote {os.path.basename(dest)}  {len(allf)} rows  [{span}]")

    print(f"\n[EXT-GATE] ran on {gated} model-scenario cell(s); the 2026-08-21 "
          f"table covers ssp585 for IPSL-CM6A-LR and CESM2-WACCM only.")
    print(f"PROVENANCE: CMIP6 Amon tas; post-2100 from ESGF (CEDA), "
          f"<= {SPLICE_YEAR} from data/cmip6_pai (Pangeo) except UKESM1-0-LL "
          f"which is ESGF end to end on {MEMBERS['UKESM1-0-LL']}. AIS = land "
          f"(sftlf >= {SFTLF_MIN}%) south of {AIS_LAT_MAX} deg, cos(lat) weighted.")


if __name__ == "__main__":
    main()
