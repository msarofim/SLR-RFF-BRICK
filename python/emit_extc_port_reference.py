#!/usr/bin/env python3
"""Emit the extC port-validation reference (python ground truth).

For BOTH amp bases (regchar / obsfit), at the anchored theta (kappa/nu from
solve_anchored, structure from the 4-rung fits — exactly the build in
build_extc_inputs.py), emit per year:
  - the spliced per-block drivers (extend_obs, K glacier frame), and
  - the integrated per-block melt series (integrate_N, m SLE).
julia/validate_glaciers_nu3.jl must reproduce the drivers from the artifact
CSVs and the series through the Mimi component to <= 1e-9.

Output: outputs/extc_port_reference.csv
  year, then per basis in {reg, obs} x block in {R19, SLOWP, FAST}:
  drv_<basis>_<block>, s_<basis>_<block>
"""
import os

import numpy as np
import pandas as pd

REPO_PR = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
D1F_SRC = os.path.join(REPO_PR, "python/d1f_obsamp_arm.py")

_src_f = open(D1F_SRC).read()
_MARKER_F = "# ---------------------------------------------------------------- run\n"
assert _src_f.count(_MARKER_F) == 1
exec(_src_f.split(_MARKER_F)[0])

OUT_REF = os.path.join(REPO, "outputs/extc_port_reference.csv")

res3_raw = {n: build_reservoir(n, m, farinotti_basis=True)
            for n, m in SPEC_3RES.items()}
blk2_raw = {n: build_reservoir(n, m, farinotti_basis=False)
            for n, m in SPEC_2BLK.items()}
_ = {n: four_rung_fit(b) for n, b in blk2_raw.items()}
_ = {n: two_rung_anchor(b) for n, b in res3_raw.items()}
structures = {"reg": {n: four_rung_fit(b) for n, b in res3_raw.items()}}
res3_obs = {}
for n, m in SPEC_3RES.items():
    blk = build_reservoir(n, m, farinotti_basis=True)
    blk["amp_b"] = obs_amp_of(blk)
    res3_obs[n] = blk
structures["obs"] = {n: four_rung_fit(b) for n, b in res3_obs.items()}

out = pd.DataFrame({"year": years})
th_rows = []
for basis, resv in structures.items():
    anch = {n: solve_anchored(b) for n, b in resv.items()}
    assert all(a["match_ok"] for a in anch.values())
    for n, blk in resv.items():
        drv_full = extend_obs(blk["driver_obs"], fair_rb, blk["amp_b"]).to_numpy()
        s = integrate_N(drv_full[:-1], blk["a"], blk["b"], blk["T_off"],
                        anch[n]["kappa"], anch[n]["nu"])
        out[f"drv_{basis}_{n}"] = drv_full
        out[f"s_{basis}_{n}"] = s
        th_rows.append(dict(basis=basis, block=n, a=blk["a"], b=blk["b"],
                            T_off=blk["T_off"], kappa=anch[n]["kappa"],
                            nu=anch[n]["nu"], amp=blk["amp_b"]))
out.to_csv(OUT_REF, index=False, float_format="%.12f")
OUT_TH = os.path.join(REPO, "outputs/extc_port_reference_theta.csv")
pd.DataFrame(th_rows).to_csv(OUT_TH, index=False, float_format="%.17g")
print(f"commit={COMMIT}  wrote {os.path.relpath(OUT_REF, REPO)} "
      f"({len(out)} years, {len(out.columns) - 1} series) + "
      f"{os.path.relpath(OUT_TH, REPO)}")
