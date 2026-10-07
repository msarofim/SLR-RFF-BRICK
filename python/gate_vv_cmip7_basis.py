"""[VV-BASIS] gate: the van Vuuren FaIR drivers must be on the CMIP7 history basis before any vv arm runs.

WHY (2026-10-07). Until 2026-10-02 every vv cube paired fair-calibrate 1.6.0 parameters with SMITH 2024
history (memory `vv_arm_was_smith_history`; quarantine `outputs/quarantine/20261002_vv_smith_history_basis/`).
The symptom a projection arm can see is its PRE-SPLICE half: before 2014 every arm runs on the marker's own
ensemble-mean GMST, and on the Smith basis that history sits up to 0.074 K from `fair_mean_gmst_ssp245harm`,
the driver Ladrillo was CALIBRATED on (1995-2014 mean 0.750 vs 0.803 degC). On the CMIP7 basis it is 0.015 K.

THE TEST IS AN ORDERING, not a picked tolerance (`threshold_from_obs_or_law`): for every marker, the live
file's max |vv mean - calibration driver| over 1850-2014 must be SMALLER than the same statistic on the
quarantined Smith-basis copy. No number is invented; the Smith copy is the reference it must beat.

MUTATION TEST: `--obs-dir=outputs/quarantine/20261002_vv_smith_history_basis` points the LIVE side at the
Smith files, which must FAIL (live == reference, so "smaller" is false on every marker).

Usage: python python/gate_vv_cmip7_basis.py [--obs-dir=<dir>]
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKERS = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
CALIB_KEY = "ssp245harm"                  # the calibration driver (run_mcmc_L27.sh)
WINDOW = (1850, 2014)                     # the pre-splice half every spliced arm runs on (SPLICE_YEAR = 2014)
REF = (1995, 2014)                        # LADRILLO_REF
SMITH_DIR = os.path.join(REPO, "outputs/quarantine/20261002_vv_smith_history_basis")


def _arg(flag, default):
    return next((a[len(flag):] for a in sys.argv[1:] if a.startswith(flag)), default)


LIVE_DIR = os.path.join(REPO, _arg("--obs-dir=", "data/observations"))


def mean_gmst(d, key):
    f = os.path.join(d, "fair_mean_gmst_%s.csv" % key)
    x = pd.read_csv(f)
    return x.set_index(x.year.astype(int)).gmst_C.astype(float)


calib = mean_gmst(os.path.join(REPO, "data/observations"), CALIB_KEY)
w = slice(*WINDOW)
print("[VV-BASIS] live dir: %s" % os.path.relpath(LIVE_DIR, REPO))
print("[VV-BASIS] max |vv mean - %s| over %d-%d, live vs Smith-basis reference; ref-window means in degC"
      % (CALIB_KEY, *WINDOW))
print("  %-5s %10s %10s %10s %10s  %s" % ("key", "live", "smith", "live REF", "smith REF", "verdict"))
fails = 0
for m in MARKERS:
    live, smith = mean_gmst(LIVE_DIR, m), mean_gmst(SMITH_DIR, m)
    dl = float(np.abs(live.loc[w] - calib.loc[w]).max())
    ds = float(np.abs(smith.loc[w] - calib.loc[w]).max())
    ok = dl < ds
    fails += not ok
    print("  %-5s %10.4f %10.4f %10.4f %10.4f  %s" % (m, dl, ds, live.loc[slice(*REF)].mean(),
                                                     smith.loc[slice(*REF)].mean(), "PASS" if ok else "FAIL"))
print("[VV-BASIS] calibration driver %s REF mean %.4f degC" % (CALIB_KEY, calib.loc[slice(*REF)].mean()))
if fails:
    sys.exit("[VV-BASIS] FAIL on %d of %d markers -- the vv drivers are NOT closer to the calibration history "
             "than the Smith-basis copy. Refusing." % (fails, len(MARKERS)))
print("[VV-BASIS] PASS on all %d markers" % len(MARKERS))
