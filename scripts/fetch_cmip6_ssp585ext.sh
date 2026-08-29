#!/usr/bin/env bash
# Fetch the CMIP6 ssp585 EXTENSION (2101-2300) global tas for the two GCMs that
# force the PROTECT-Greenland x2300 arm, and verify checksums.
#
# WHY IT IS HERE: notes/handoff_2026-08-21_protect_greenland.md section 5 item 1 —
# the PROTECT x2300 ensemble agrees with our tapped Greenland cell at 2300 to 1.4%
# and undershoots it by 38% at 2150, and that pattern can only be read once the
# x2300 FORCING PATH has been checked against ours year by year. The x2300 arm is
# forced by exactly two GCMs (info_p11/exps_pxx_uniqc.txt):
#     IPSL-CM6A-LR ssp585-x2300  (MARv3.13-e05, MARv3.13-e55)
#     CESM2-WACCM  ssp585-x2300  (SDBN1)
# Neither the PROTECT scalar NetCDFs nor info_p11 carry any climate variable, so
# GSAT has to come from the source CMIP6 runs.
#
# WHY NOT PANGEO: the Google/Pangeo CMIP6 zarr mirror carries ssp585 for both
# models but TRUNCATES AT 2100 (checked 2026-08-21: 1032 monthly steps, 2015-01
# to 2100-12, every member). The post-2100 extension exists only as ESGF files.
#
# The 2015-2100 half is already in the repo (data/cmip6_gis/tas_series_gis_*.csv,
# same r1i1p1f1 member, same cos(lat) weighting) — only 2101+ is fetched here.
#
# ~400 MB, gitignored per the repo's large-external-data convention. The DERIVED
# annual GSAT table (outputs/cmip6_ssp585ext_gsat.csv) is tracked.
# ⚠ BROKEN NODE AS OF 2026-08-28: the ORNL and UCAR hosts below no longer serve
# these paths. esgf-node.ornl.gov now returns a React SPA with HTTP 200 for any
# /esg-search or /thredds request, so a status-code check reads as "up" and the
# fetch silently writes HTML into a .nc file -- a check that cannot fail, the same
# shape as a gate reading its own output. esgf-data.ucar.edu returns 404.
# Working mirrors: esgf.ceda.ac.uk and esgf-data.dkrz.de. See
# scripts/fetch_cmip6_coulon_ext.sh for the CEDA URL pattern. The checksum block
# below WOULD catch the HTML, but only after a full download.

set -euo pipefail
cd "$(dirname "$0")/.."
DEST=data/cmip6_gsat_ext
mkdir -p "$DEST"
ORNL=http://esgf-node.ornl.gov/thredds/fileServer/css03_data/CMIP6/ScenarioMIP
UCAR=http://esgf-data.ucar.edu/thredds/fileServer/esg_dataroot/CMIP6/ScenarioMIP
IPSL=$ORNL/IPSL/IPSL-CM6A-LR/ssp585/r1i1p1f1/Amon/tas/gr/v20190903
CESM=$UCAR/NCAR/CESM2-WACCM/ssp585/r1i1p1f1/Amon/tas/gn/v20200702
for u in \
  "$IPSL/tas_Amon_IPSL-CM6A-LR_ssp585_r1i1p1f1_gr_210101-230012.nc" \
  "$CESM/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_210101-215012.nc" \
  "$CESM/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_215101-220012.nc" \
  "$CESM/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_220101-225012.nc" \
  "$CESM/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_225101-229912.nc" ; do
  f=$(basename "$u"); echo "  fetching $f"
  curl -fL --retry 3 -C - "$u" -o "$DEST/$f"
done
echo "verifying checksums (computed from the 2026-08-21 fetch; ESGF publishes no"
echo "per-file md5 in the search index, so these pin OUR copy, not the archive's)"
cd "$DEST"
cat > .expected.md5 <<'MD5'
fd71f67bca80122216e34abd40c47d08  tas_Amon_IPSL-CM6A-LR_ssp585_r1i1p1f1_gr_210101-230012.nc
73a42493195689f3b5e5414ef1415792  tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_210101-215012.nc
5da6e8ef590610170daf8daf68ef5873  tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_215101-220012.nc
ba3d26668c1175e58fe32d7fd727ff65  tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_220101-225012.nc
48662bf8685d0aefe82b506ef31bdf8d  tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_225101-229912.nc
MD5
fail=0
while read -r want f; do
  got=$(md5 -q "$f" 2>/dev/null || md5sum "$f" | awk '{print $1}')
  if [[ "$got" == "$want" ]]; then echo "  OK   $f"; else echo "  FAIL $f"; fail=1; fi
done < .expected.md5
rm -f .expected.md5
[[ $fail -eq 0 ]] || { echo "CHECKSUM MISMATCH — do not use"; exit 1; }
echo "next: python3 python/reduce_cmip6_gsat_ssp585ext.py"
