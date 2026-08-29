#!/usr/bin/env bash
# Fetch CMIP6 tas for the FOUR GCMs that force Coulon et al. 2025 (Nat. Commun.
# 16:10385), ssp585 AND ssp126, through 2300 — the series needed to compute
# COULON'S OWN 2015-2300 temperature integral and make the Ladrillo AIS arm
# comparison like-for-like rather than endpoint-matched.
#
# WHY IT IS HERE: the arm selection was respecified on the INTEGRAL (Marcus,
# 2026-08-28) after AIS@2300 was measured ~linear in the integral at ~18.5 cm per
# degC-century on two vintages with disjoint config sets. Coulon's forcing is not
# novel data — it is CMIP6 GCM output, and python/diag_ais_coulon_like_for_like.py
# already names the four models and records "CMIP6 GCM forcing carried to 2300".
#
# WHY NOT PANGEO: the Google/Pangeo CMIP6 zarr mirror TRUNCATES AT 2100 for every
# member and every experiment — the experiment_id looks right and the data is not
# there, so check time[-1], not the name. Post-2100 lives only on ESGF.
#
# WHY NOT ORNL, WHICH THE 2026-08-21 PRECEDENT USED: esgf-node.ornl.gov no longer
# serves /esg-search — it returns a React SPA with HTTP 200, so a naive probe
# reads as "up". esgf.ceda.ac.uk and esgf-data.dkrz.de still serve the Solr API.
#
# ⚠ MEMBER IS NOT UNIFORM ACROSS THE FOUR. UKESM1-0-LL extended ONLY r4i1p1f2 —
# r1/r2/r3/r8 all stop at 2100, and the repo's existing 2015-2100 series is r1.
# Appending r4 to r1 would put a member change at 2100, inside the window being
# integrated. So UKESM is refetched END TO END on r4, historical included: the
# 1995-2014 reference period Coulon uses lives in the HISTORICAL leg, so a
# consistent anomaly needs r4's historical too, not just its future.
# The other three extended the r1i1p1f1 already in the files and splice cleanly.
#
# ~1.9 GB, gitignored per the repo's large-external-data convention. The derived
# annual tables are what gets tracked.
#
# NO PINNED CHECKSUMS: the 2026-08-21 precedent verified against md5s computed
# from an earlier fetch. This IS that earlier fetch, so it WRITES the manifest
# (.fetch_manifest.md5, tracked) instead of verifying against one. A later
# re-fetch can verify against it. ESGF publishes no per-file md5 in the search
# index, so this pins OUR copy, not the archive's.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=data/cmip6_coulon_ext
mkdir -p "$DEST"
CEDA=https://esgf.ceda.ac.uk/thredds/fileServer/esg_cmip6/CMIP6
SCEN=$CEDA/ScenarioMIP
HIST=$CEDA/CMIP

while read -r u; do
  [[ -z "$u" || "$u" == \#* ]] && continue
  f=$(basename "$u")
  if [[ -s "$DEST/$f" ]]; then echo "  have $f"; continue; fi
  echo "  fetching $f"
  curl -fL --retry 5 --retry-delay 5 -C - "$u" -o "$DEST/$f"
done <<URLS
# --- UKESM1-0-LL, r4i1p1f2 END TO END (the only extended member) ---
$HIST/MOHC/UKESM1-0-LL/historical/r4i1p1f2/Amon/tas/gn/v20190502/tas_Amon_UKESM1-0-LL_historical_r4i1p1f2_gn_185001-194912.nc
$HIST/MOHC/UKESM1-0-LL/historical/r4i1p1f2/Amon/tas/gn/v20190502/tas_Amon_UKESM1-0-LL_historical_r4i1p1f2_gn_195001-201412.nc
$SCEN/MOHC/UKESM1-0-LL/ssp585/r4i1p1f2/Amon/tas/gn/v20190507/tas_Amon_UKESM1-0-LL_ssp585_r4i1p1f2_gn_201501-204912.nc
$SCEN/MOHC/UKESM1-0-LL/ssp585/r4i1p1f2/Amon/tas/gn/v20190507/tas_Amon_UKESM1-0-LL_ssp585_r4i1p1f2_gn_205001-210012.nc
$SCEN/MOHC/UKESM1-0-LL/ssp585/r4i1p1f2/Amon/tas/gn/v20210205/tas_Amon_UKESM1-0-LL_ssp585_r4i1p1f2_gn_210101-214912.nc
$SCEN/MOHC/UKESM1-0-LL/ssp585/r4i1p1f2/Amon/tas/gn/v20210205/tas_Amon_UKESM1-0-LL_ssp585_r4i1p1f2_gn_215001-224912.nc
$SCEN/MOHC/UKESM1-0-LL/ssp585/r4i1p1f2/Amon/tas/gn/v20210205/tas_Amon_UKESM1-0-LL_ssp585_r4i1p1f2_gn_225001-230012.nc
$SCEN/MOHC/UKESM1-0-LL/ssp126/r4i1p1f2/Amon/tas/gn/v20190507/tas_Amon_UKESM1-0-LL_ssp126_r4i1p1f2_gn_201501-204912.nc
$SCEN/MOHC/UKESM1-0-LL/ssp126/r4i1p1f2/Amon/tas/gn/v20190507/tas_Amon_UKESM1-0-LL_ssp126_r4i1p1f2_gn_205001-210012.nc
$SCEN/MOHC/UKESM1-0-LL/ssp126/r4i1p1f2/Amon/tas/gn/v20210205/tas_Amon_UKESM1-0-LL_ssp126_r4i1p1f2_gn_210101-214912.nc
$SCEN/MOHC/UKESM1-0-LL/ssp126/r4i1p1f2/Amon/tas/gn/v20210205/tas_Amon_UKESM1-0-LL_ssp126_r4i1p1f2_gn_215001-224912.nc
$SCEN/MOHC/UKESM1-0-LL/ssp126/r4i1p1f2/Amon/tas/gn/v20210205/tas_Amon_UKESM1-0-LL_ssp126_r4i1p1f2_gn_225001-230012.nc
# --- IPSL-CM6A-LR r1i1p1f1, post-2100 only (2015-2100 already in the repo) ---
$SCEN/IPSL/IPSL-CM6A-LR/ssp585/r1i1p1f1/Amon/tas/gr/v20190903/tas_Amon_IPSL-CM6A-LR_ssp585_r1i1p1f1_gr_210101-230012.nc
$SCEN/IPSL/IPSL-CM6A-LR/ssp126/r1i1p1f1/Amon/tas/gr/v20190903/tas_Amon_IPSL-CM6A-LR_ssp126_r1i1p1f1_gr_210101-230012.nc
# --- CESM2-WACCM r1i1p1f1, post-2100 only (ends 2299, not 2300) ---
$SCEN/NCAR/CESM2-WACCM/ssp585/r1i1p1f1/Amon/tas/gn/v20200702/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_210101-215012.nc
$SCEN/NCAR/CESM2-WACCM/ssp585/r1i1p1f1/Amon/tas/gn/v20200702/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_215101-220012.nc
$SCEN/NCAR/CESM2-WACCM/ssp585/r1i1p1f1/Amon/tas/gn/v20200702/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_220101-225012.nc
$SCEN/NCAR/CESM2-WACCM/ssp585/r1i1p1f1/Amon/tas/gn/v20200702/tas_Amon_CESM2-WACCM_ssp585_r1i1p1f1_gn_225101-229912.nc
$SCEN/NCAR/CESM2-WACCM/ssp126/r1i1p1f1/Amon/tas/gn/v20210211/tas_Amon_CESM2-WACCM_ssp126_r1i1p1f1_gn_210101-215012.nc
$SCEN/NCAR/CESM2-WACCM/ssp126/r1i1p1f1/Amon/tas/gn/v20210211/tas_Amon_CESM2-WACCM_ssp126_r1i1p1f1_gn_215101-220012.nc
$SCEN/NCAR/CESM2-WACCM/ssp126/r1i1p1f1/Amon/tas/gn/v20210211/tas_Amon_CESM2-WACCM_ssp126_r1i1p1f1_gn_220101-225012.nc
$SCEN/NCAR/CESM2-WACCM/ssp126/r1i1p1f1/Amon/tas/gn/v20210211/tas_Amon_CESM2-WACCM_ssp126_r1i1p1f1_gn_225101-229912.nc
# --- MRI-ESM2-0 r1i1p1f1, post-2100 only ---
$SCEN/MRI/MRI-ESM2-0/ssp585/r1i1p1f1/Amon/tas/gn/v20191108/tas_Amon_MRI-ESM2-0_ssp585_r1i1p1f1_gn_210101-230012.nc
$SCEN/MRI/MRI-ESM2-0/ssp126/r1i1p1f1/Amon/tas/gn/v20191108/tas_Amon_MRI-ESM2-0_ssp126_r1i1p1f1_gn_210101-230012.nc
URLS

echo "writing manifest (pins OUR copy; ESGF publishes no per-file md5)"
cd "$DEST"
for f in *.nc; do echo "$(md5 -q "$f")  $f"; done > .fetch_manifest.md5
echo "  $(wc -l < .fetch_manifest.md5) files, $(du -sh . | cut -f1) total"
echo "next: python3 python/reduce_cmip6_tas_coulon.py"
