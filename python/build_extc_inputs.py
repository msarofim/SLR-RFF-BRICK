#!/usr/bin/env python3
"""Build the extC calibrator input artifacts (one-time, machine-generated).

SUPERSEDED 2026-08-10 by python/brickf_data.py, which does the same job as a
readable module with no exec-prefix chain. python/test_brickf_data.py asserts
the two produce byte-identical artifacts, so this file is kept only as
provenance for how they were originally generated — build from brickf_data.py.

The extC surgery moves the 3-reservoir glacier structure into
julia/calibrate_mcmc_ext.jl. Julia must not hand-copy offline numbers, so
this script (exec-inheriting the d1f prefix -> d1e -> d1d -> d0 chain)
emits everything the calibrator needs, with provenance:

  1. data/observations/t_glac_blocks.csv
       year, R19, SLOWP, FAST — GlaMBIE-area-weighted HadCRUT5 block drivers,
       K rel 1850-1900 (identical to the offline blk["driver_obs"]).
  2. outputs/extc_block_constants.csv
       one row per reservoir: Farinotti a-priors, S2000/S2020 data basis,
       tau50 pair, GlaMBIE modern rate +/- sd (err x1.5), amp_b for BOTH
       bases (regchar ISIMIP3 / obs through-origin fit), the 4 committed
       rungs + band sigmas (data side of the rung likelihood), and the
       offline-fitted (b, T_off) + anchored (kappa, nu) under each basis
       (kappa-prior centers / theta0; nu is FIXED at the anchored value
       per basis — the MID design the offline arms validated).
  3. outputs/recalib_targets_ext_gsicadj.csv
       year, gsic_adj — the r19-seam-adjusted gsic target (obs_adj):
       identical to the targets gsic column pre-2019, GlaMBIE r19
       cumulative removed 2019+ (net 0.38 mm at series end).

Run AFTER any change to the offline structure; commit the outputs.
"""
import os

import numpy as np
import pandas as pd

REPO_BX = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
D1F_SRC = os.path.join(REPO_BX, "python/d1f_obsamp_arm.py")

_src_f = open(D1F_SRC).read()
_MARKER_F = "# ---------------------------------------------------------------- run\n"
assert _src_f.count(_MARKER_F) == 1, "d1f run marker not unique - refusing to exec"
exec(_src_f.split(_MARKER_F)[0])

OUT_DRV = os.path.join(REPO, "data/observations/t_glac_blocks.csv")
OUT_CONST = os.path.join(REPO, "outputs/extc_block_constants.csv")
OUT_GSICADJ = os.path.join(REPO, "outputs/recalib_targets_ext_gsicadj.csv")
TARGETS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

print(f"build_extc_inputs | commit={COMMIT}")

# structures under both amp bases (d1d build order for rng parity)
res3_raw = {n: build_reservoir(n, m, farinotti_basis=True)
            for n, m in SPEC_3RES.items()}
blk2_raw = {n: build_reservoir(n, m, farinotti_basis=False)
            for n, m in SPEC_2BLK.items()}
_ = {n: four_rung_fit(b) for n, b in blk2_raw.items()}
_ = {n: two_rung_anchor(b) for n, b in res3_raw.items()}
cboth_reg = {n: four_rung_fit(b) for n, b in res3_raw.items()}
anch_reg = {n: solve_anchored(b) for n, b in cboth_reg.items()}

res3_obs = {}
for n, m in SPEC_3RES.items():
    blk = build_reservoir(n, m, farinotti_basis=True)
    blk["amp_b"] = obs_amp_of(blk)
    res3_obs[n] = blk
cboth_obs = {n: four_rung_fit(b) for n, b in res3_obs.items()}
anch_obs = {n: solve_anchored(b) for n, b in cboth_obs.items()}
assert all(anch_reg[n]["match_ok"] and anch_obs[n]["match_ok"] for n in SPEC_3RES)

# 1. block drivers
drv = pd.DataFrame({"year": cboth_reg["R19"]["driver_obs"].index})
for n in SPEC_3RES:
    s = cboth_reg[n]["driver_obs"]
    drv[n] = s.reindex(drv["year"]).to_numpy()
assert not drv.isna().any().any(), "block driver has gaps"
# full precision: the Julia port validation compares these at 1e-9, and the
# multi-region area-weighted averages are not 6-decimal-exact
drv.to_csv(OUT_DRV, index=False, float_format="%.12f")

# 2. block constants
rows = []
for n in SPEC_3RES:
    br, bo = cboth_reg[n], cboth_obs[n]
    row = dict(block=n, members="|".join(SPEC_3RES[n]),
               a0=br["a0"], a0_sig=br["a0_sig"],
               S2000_data=br["S2000_data"], S2020_data=br["S2020_data"],
               tau15=br["tau15"], tau30=br["tau30"],
               glambie_rate=br["glambie_rate"], glambie_rate_sd=br["glambie_rate_sd"],
               amp_regchar=br["amp_b"], amp_obsfit=bo["amp_b"],
               b_fit_regchar=br["b"], T_off_fit_regchar=br["T_off"],
               b_fit_obsfit=bo["b"], T_off_fit_obsfit=bo["T_off"],
               kappa_anch_regchar=anch_reg[n]["kappa"], nu_anch_regchar=anch_reg[n]["nu"],
               kappa_anch_obsfit=anch_obs[n]["kappa"], nu_anch_obsfit=anch_obs[n]["nu"])
    for L in GMIP3_LEVELS:
        key = str(L).replace(".", "p")
        row[f"com{key}"] = br["com"][L]
        row[f"sig{key}"] = br["rung_sig"][L]
    rows.append(row)
const_df = pd.DataFrame(rows)
const_df.to_csv(OUT_CONST, index=False, float_format="%.12g")

# 3. r19-adjusted gsic target (obs_adj), asserted against the targets CSV frame
tgt = pd.read_csv(TARGETS_CSV).set_index("year")
gsic_col = tgt["gsic"].dropna()
assert np.allclose(gsic_col.loc[fit_years].to_numpy(), obs, atol=1e-9), \
    "d0 obs vector != targets gsic column — frame drift, do not emit"
pre = fit_years < 2019
assert np.array_equal(OBS_ADJ[pre], obs[pre])
pd.DataFrame({"year": fit_years, "gsic_adj": OBS_ADJ}).to_csv(
    OUT_GSICADJ, index=False, float_format="%.12g")

print(f"  amp_b regchar/obsfit: "
      + "  ".join(f"{n} {cboth_reg[n]['amp_b']:.3f}/{cboth_obs[n]['amp_b']:.3f}"
                  for n in SPEC_3RES))
print(f"  kappa anchors regchar/obsfit: "
      + "  ".join(f"{n} {anch_reg[n]['kappa']:.5f}/{anch_obs[n]['kappa']:.5f}"
                  for n in SPEC_3RES))
print(f"  net r19 target removal at end: {10 * (obs[-1] - OBS_ADJ[-1]):.3f} mm")
print(f"Wrote {os.path.relpath(OUT_DRV, REPO)}, {os.path.relpath(OUT_CONST, REPO)}, "
      f"{os.path.relpath(OUT_GSICADJ, REPO)}")
