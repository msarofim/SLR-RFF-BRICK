#!/usr/bin/env bash
#
# download_data.sh
# =================
# Fetch the large intermediate-data tarball for the SLR-RFF-BRICK pipeline
# from its Zenodo deposit and extract into outputs/ and data/.
#
# This is Tier 2 setup: brings down the FaIR cubes + LHS-10k weighted
# ensemble CSVs + ANOVA factorial CSVs needed to re-run BRICK and to
# regenerate any of the project's figures from raw ensembles.
#
# Tier 1 (figure regeneration from small CSVs already in the repo) does
# NOT need this script.
#
# Usage:
#   bash scripts/download_data.sh
#
# Requirements: curl, tar, gzip. Disk: ~6 GB free.

set -euo pipefail

# -----------------------------------------------------------------------------
# Zenodo deposit: SLR-RFF-BRICK intermediate data v1.0
# DOI: 10.5281/zenodo.20312325
# -----------------------------------------------------------------------------
ZENODO_DOI="${ZENODO_DOI:-10.5281/zenodo.20312325}"
ZENODO_RECORD_ID="${ZENODO_RECORD_ID:-20312325}"
# The DOI resolves to https://zenodo.org/records/20312325; the files endpoint
# is https://zenodo.org/api/records/20312325/files-archive (returns a .zip of
# the whole record).
# -----------------------------------------------------------------------------

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
mkdir -p outputs

if [[ "$ZENODO_RECORD_ID" == "XXXXXXX" ]]; then
  cat <<EOF >&2
ERROR: Zenodo record ID not configured.

The deposit hasn't been created yet (or the script hasn't been updated
with the DOI). To configure:

  1. Create the Zenodo deposit (see SETUP_ZENODO.md for the manifest
     and metadata template).
  2. Note the DOI (format: 10.5281/zenodo.XXXXXXX) and record ID
     (the trailing integer).
  3. Either:
       a. Edit this script's ZENODO_DOI and ZENODO_RECORD_ID variables, or
       b. Run with env vars set:
            ZENODO_RECORD_ID=12345678 bash scripts/download_data.sh

EOF
  exit 1
fi

URL="https://zenodo.org/api/records/${ZENODO_RECORD_ID}/files-archive"

echo "Downloading SLR-RFF-BRICK intermediate data from"
echo "  ${URL}"
echo "to outputs/ (expect ~6 GB) ..."
echo

TARBALL=outputs/_zenodo_download.zip
curl -L --fail --progress-bar -o "${TARBALL}" "${URL}"

echo
echo "Extracting ..."
unzip -o -q "${TARBALL}" -d outputs/
rm -f "${TARBALL}"

echo
echo "Done. Verifying expected files exist:"
for f in \
  outputs/lhs_pilot_gmst_full_N200_to2300.npz \
  outputs/lhs_pilot_gmst_full_stoch_test_ohc4.npz \
  outputs/rff_baseline_stoch_to2300.npz \
  outputs/rff_pulse_stoch_to2300.npz \
  outputs/rff_pulse0p01gtc_stoch_to2300.npz \
  outputs/brick_lhs10k_baseline_to2300_weighted.csv \
  outputs/brick_lhs10k_pulse_to2300_weighted.csv \
  outputs/brick_lhs10k_pulse0p01gtc_to2300_weighted.csv \
  outputs/brick_anova_long_2300_weighted.csv \
  outputs/brick_anova_pulse_long_2300.csv \
  outputs/brick_lB_per_post_dangendorf.csv ; do
  if [[ -f "$f" ]]; then
    sz=$(du -h "$f" | cut -f1)
    echo "  OK  ${f}  (${sz})"
  else
    echo "  !!  ${f}  MISSING"
  fi
done

echo
echo "Tier 2 reproducibility is now possible. To regenerate the LHS-10k"
echo "weighted ensembles from the FaIR cubes (instead of using the"
echo "CSVs we just downloaded), submit:"
echo
echo "  sbatch slurm/submit_lhs10k_brick_pipeline.sh   # baseline + 1 GtC pulse"
echo "  sbatch slurm/submit_lhs10k_brick_smallpulse.sh # 0.01 GtC small-pulse"
echo
echo "To re-derive a figure end-to-end from the cubes, see README.md Tier 2."
