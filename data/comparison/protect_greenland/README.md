# PROTECT-Greenland scalar ensemble (Goelzer 2025)

**Source** doi [10.11582/2025.lf9m2wd0](https://doi.org/10.11582/2025.lf9m2wd0),
NIRD / Sigma2 archive, CC-BY, 74.3 MB. Paper: Goelzer et al. 2025, "Extending the
range and reach of physically-based Greenland ice sheet sea-level projections",
doi 10.5194/egusphere-2025-3098.

**Fetch** `bash scripts/fetch_protect_greenland.sh` — downloads and verifies all
six published md5s, then unpacks. The `.tgz` files and the 3136 unpacked NetCDFs
are gitignored (large external data, per the convention in the repo `.gitignore`);
the derived summary `outputs/protect_greenland_gis_summary.csv` IS tracked.

**Why it is here.** The only physics-based Greenland source in this repo carrying
ANNUAL series past 2100. At 2150 the alternatives are FACTS-FittedISMIP (an ISMIP6
emulator) and bamber19 (structured expert judgment); MAGICC-SLR and emuGrIS stop
at 2100.

## READ BEFORE USING AS A CONSTRAINT

1. **The 4-model ensemble is 2100-ONLY.** 1297 of 1568 scalar files stop at 2100.
   All 209 runs reaching 2150+ are **NORCE-CISM**. Past 2100 the spread is
   climate-forcing spread from one ice sheet model, not structural spread.
2. **Control drift must be removed** (ISMIP6 convention). It moves the ssp585 2300
   median by ~70%. `python/extract_protect_greenland.py` does this and drops the
   303 runs with no matching `ctrl-proj`.
3. **`sle`/`slc` DECREASE with mass loss.** Contribution is `-(x - x[0])`.
4. **Experiment families are not interchangeable.** `x2300` (forcing continued)
   and `r2300` differ by 3.5x at 2300. `x2300` is the apples-to-apples arm for
   Ladrillo's warming GMST paths; it is also the family behind the repo's existing
   `LIT_2300_M` "warming" band.
5. **Basis is rel 2015**, not this repo's 1995-2014. The offset is deliberately
   NOT invented here — the dataset has no pre-2015 data.

`scalars_rm_GIS` carries IMBIE2-Rignot basins `[no, ne, se, sw, cw, nw]`, so
**NO+NE is exactly the Ladrillo high basin** — unused so far, and the obvious
direct check on `s_high`.

See `notes/handoff_2026-08-21_protect_greenland.md` for what it says about the tap.
