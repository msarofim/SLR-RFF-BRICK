#!/usr/bin/env bash
# One-shot regeneration of the Greenland offline cell + g/beta_f variants on the
# calib-1.6.0 drivers with the corrected splice anchor (CHANGELOG 2026-09-16).
# Launched with nohup because tool-driven background shells die at 10 min.
set -uo pipefail
cd "$(dirname "$0")/../python"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY=$HOME/climate-env/bin/python3
echo "START $(date)"
$PY gis_offline_cell.py > ../logs/gis_offline_cell_20260916.log 2>&1
echo "gis_offline_cell exit $? $(date)"
$PY diag_gis_g_betaf.py > ../logs/diag_gis_g_betaf_20260916.log 2>&1
echo "diag_gis_g_betaf exit $? $(date)"
echo "DONE $(date)"
