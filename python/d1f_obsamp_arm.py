#!/usr/bin/env python3
"""D1f — obs-amp sensitivity arm (Marcus green-light 2026-08-09, alongside extC).

The flagged, never-run orthogonal test: the per-reservoir amplification
ratios amp_b are regchar (ISIMIP3) values known to sit LOW vs both the
calibrator convention (area-wt aggregate 1.34 vs amp_g = 1.8) and the obs
through-origin fit (aggregate 1.59). This arm rebuilds C_both with amp_b
from the OBS through-origin fits (block driver on HadCRUT5 global, both
rel 1850-1900, window AMP_FIT_WIN = 1901-2024 — the AMP_FIT convention,
d1_multireservoir_cell.py:816) and re-runs the D1e ledger cell.

amp_b enters three places, all rebuilt here: (1) the 4-rung S_eq fit
(glacier-frame conversion amp_b*L), (2) the tau50 anchored kappa/nu solve,
(3) the FaIR extension of the obs driver (hindcast tail + projections).
The aggregate amp_g = 1.8 convention (pathological comparator + d0 gates)
is UNCHANGED, so the D1e pathological references remain valid and are
reused (read from the d1e CSV: patho_fw = flow_win + flow_win_deficit).

SANITY (evaluation-based): regchar structures rebuilt here reproduce the
d1e headline row by evaluating the stored d1e ANCH theta under loglik_d.

PRE-REGISTERED: this is a SENSITIVITY arm with a neutral prior - report
Delta(deficit, gates, ladder z, spread, ds245, modern rate) vs D1e.
It INFORMS the extC amp choice; any config change is Marcus's call and
only warranted if the verdict pattern moves materially (a gate flips or
the deficit moves by more than ~1 logL).

Configs: C_both(obs-amp) x {unc_t5d: ANCH/MID/FREE; unc_sx2: ANCH/MID}.
Outputs: outputs/d1f_obsamp_arm.csv, figures/d1f_obsamp_arm.png.
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO_D1F = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
D1E_SRC = os.path.join(REPO_D1F, "python/d1e_dside_ledger.py")

_src_e = open(D1E_SRC).read()
_MARKER_E = "# ---------------------------------------------------------------- run\n"
assert _src_e.count(_MARKER_E) == 1, "d1e run marker not unique - refusing to exec"
exec(_src_e.split(_MARKER_E)[0])

# paths AFTER the exec (rebind trap)
OUT_CSV = os.path.join(REPO, "outputs/d1f_obsamp_arm.csv")
OUT_FIG = os.path.join(REPO, "figures/d1f_obsamp_arm.png")
D1E_CSV = os.path.join(REPO, "outputs/d1e_dside_ledger.csv")

DEFICIT_MATERIAL_LOGL = 1.0      # materiality threshold for the extC flag


def obs_amp_of(blk):
    """Through-origin fit of the block driver on HadCRUT5 global (both rel
    1850-1900), window AMP_FIT_WIN — the d0/d1 AMP_FIT convention."""
    gx = gobs.loc[AMP_FIT_WIN[0]:AMP_FIT_WIN[1]].to_numpy()
    by = blk["driver_obs"].loc[AMP_FIT_WIN[0]:AMP_FIT_WIN[1]].to_numpy()
    assert len(gx) == len(by), "driver/global window mismatch"
    return float((gx * by).sum() / (gx ** 2).sum())


# ---------------------------------------------------------------- run
print(f"D1f obs-amp arm | commit={COMMIT} | amp source: through-origin obs fit "
      f"{AMP_FIT_WIN} (AMP_FIT convention; aggregate obs-fit = {AMP_FIT:.3f}) | "
      f"regchar comparators from d1e | amp_g (patho/gates) unchanged at {AMP_G}")
print(f"  materiality threshold for the extC flag: gate flip OR |Delta deficit| > "
      f"{DEFICIT_MATERIAL_LOGL} logL")

# regchar reference structures (same build order as d1d/d1e for determinism)
res3_raw = {n: build_reservoir(n, m, farinotti_basis=True)
            for n, m in SPEC_3RES.items()}
blk2_raw = {n: build_reservoir(n, m, farinotti_basis=False)
            for n, m in SPEC_2BLK.items()}
_ = {n: four_rung_fit(b) for n, b in blk2_raw.items()}          # rng-stream parity
_ = {n: two_rung_anchor(b) for n, b in res3_raw.items()}
cboth_reg = {n: four_rung_fit(b) for n, b in res3_raw.items()}
anch_reg = {n: solve_anchored(b) for n, b in cboth_reg.items()}

# obs-amp structures: override amp_b, then refit rungs + re-solve anchors
print("\n== amp_b: regchar vs obs through-origin fit ==")
res3_obs = {}
for n, m in SPEC_3RES.items():
    blk = build_reservoir(n, m, farinotti_basis=True)
    oa = obs_amp_of(blk)
    print(f"  [{n:5s}] regchar {blk['amp_b']:.3f} -> obs-fit {oa:.3f} "
          f"(ratio {oa / blk['amp_b']:.2f})")
    blk["amp_b"] = oa
    res3_obs[n] = blk
cboth_obs = {n: four_rung_fit(b) for n, b in res3_obs.items()}
anch_obs = {n: solve_anchored(b) for n, b in cboth_obs.items()}
print("\n== obs-amp anchors (C_both) ==")
for n, blk in cboth_obs.items():
    a = anch_obs[n]
    zs = "/".join(f"{blk['rung_z'][L]:+.1f}" for L in GMIP3_LEVELS)
    print(f"  [{n:5s}] a={blk['a']:.3f} b={blk['b']:.3f} T_off={blk['T_off']:+.3f} "
          f"amp={blk['amp_b']:.2f} | rung z {zs} | kappa={a['kappa']:.5f} "
          f"nu={a['nu']:.2f} ({'exact' if a['exact'] else 'FALLBACK'})")

# sanity: regchar rebuild reproduces the d1e headline by theta evaluation
d1e_rows = pd.read_csv(D1E_CSV)
print("\n== sanity (D1f, evaluation-based) ==")
ok = []
ref = d1e_rows[d1e_rows.label == "C_both/ANCH/unc_t5d"].iloc[0]
th_ref = dict(sigma=ref["sigma"], rho=ref["rho"], delta=ref["delta"],
              u_mm=ref["u_mm"], u_pre_mm=ref["u_pre_mm"], s_r5_mm=ref["s_r5_mm"])
for n in RES_NAMES_3:
    th_ref[f"kappa_{n}"] = ref[f"kappa_{n}"]
    th_ref[f"nu_{n}"] = ref[f"nu_{n}"]
t_ref = loglik_d(cboth_reg, th_ref, "unc_t5d", "ANCH", HIND_D1E, OBS_ADJ)
fw_ref = flow_logl_window(t_ref["m_cm"], t_ref["obs_vec"],
                          VARIANTS["unc_t5d"]["eps_vec"], th_ref["sigma"],
                          th_ref["rho"], FLOW_WIN[0], FLOW_WIN[1])
d_fw = abs(fw_ref - ref["flow_win"])
d_lj = abs(t_ref["logJ"] - ref["logJ"])
ok.append(d_fw < 0.1 and d_lj < 0.5)
print(f"  [1] regchar rebuild reproduces d1e headline theta evaluation "
      f"(|d fw| = {d_fw:.2e}, |d logJ| = {d_lj:.2e}): {'PASS' if ok[-1] else 'FAIL'}")
ok.append(all(anch_obs[n]["match_ok"] for n in cboth_obs))
print(f"  [2] obs-amp tau50 anchored solves match_ok in every reservoir: "
      f"{'PASS' if ok[-1] else 'FAIL'}")
if not all(ok):
    raise SystemExit("SANITY FAILED - do not trust results")

# pathological references reused from d1e (amp_g frame is untouched)
patho_fw = {}
for variant in ("unc_t5d", "unc_sx2"):
    r = d1e_rows[d1e_rows.label == f"C_both/ANCH/{variant}"].iloc[0]
    patho_fw[variant] = float(r["flow_win"] + r["flow_win_deficit"])
    print(f"  patho ref [{variant}] = {patho_fw[variant]:.2f} (from d1e CSV)")

CONFIGS_D1F = [("unc_t5d", ["ANCH", "MID", "FREE"]), ("unc_sx2", ["ANCH", "MID"])]
rows = []
for variant, arms in CONFIGS_D1F:
    print(f"\n== runs [C_both-obsamp/{variant}] ==")
    for arm in arms:
        th = optimize_arm_d(cboth_obs, variant, arm, anch_obs, HIND_D1E, OBS_ADJ)
        m = metrics_d(cboth_obs, th, variant, arm, patho_fw[variant],
                      patho_fw[variant], HIND_D1E, OBS_ADJ,
                      label=f"OBSAMP/{arm}/{variant}")
        if m is None:
            print(f"  [OBSAMP/{arm}/{variant}] DEGENERATE")
            continue
        row, per, t = m
        rows.append(row)
        print(f"  [{row['label']:22s}] npass={row['npass']}/4 "
              f"[inv{'+' if row['g_inv'] else '-'} lec{'+' if row['g_lec'] else '-'} "
              f"lad{'+' if row['g_lad'] else '-'} spr{'+' if row['g_spread'] else '-'}] "
              f"deficit={row['flow_win_deficit']:6.2f} spread={row['spread']:5.2f} "
              f"ds245={row['ds245']:5.2f} ledger={row['s1900_inv_mm']:.1f}"
              f"+{row['s_r5_mm']:.1f}+{row['u_pre_mm']:.1f} z={row['lec_z']:+.2f} "
              f"rate={row['rate_modern_hind']:.3f} U={row['u_mm']:.1f} "
              f"delta={row['delta']:+.2f}({row['delta_sigmas']:.1f}s)")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict vs d1e
print("\n=== D1f verdict: obs-amp vs regchar (d1e) ===")
material = False
for variant, arms in CONFIGS_D1F:
    for arm in arms:
        new = res[res.label == f"OBSAMP/{arm}/{variant}"]
        old = d1e_rows[d1e_rows.label == f"C_both/{arm}/{variant}"]
        if not len(new) or not len(old):
            continue
        new, old = new.iloc[0], old.iloc[0]
        dd = new["flow_win_deficit"] - old["flow_win_deficit"]
        gate_flip = int(new["npass"]) != int(old["npass"])
        material |= gate_flip or abs(dd) > DEFICIT_MATERIAL_LOGL
        print(f"  [{arm:4s}/{variant}] deficit {old['flow_win_deficit']:6.2f} -> "
              f"{new['flow_win_deficit']:6.2f} ({dd:+.2f}) | npass "
              f"{int(old['npass'])} -> {int(new['npass'])}"
              f"{' GATE-FLIP' if gate_flip else ''} | spread "
              f"{old['spread']:5.2f} -> {new['spread']:5.2f} | ds245 "
              f"{old['ds245']:5.2f} -> {new['ds245']:5.2f} | rate "
              f"{old['rate_modern_hind']:.3f} -> {new['rate_modern_hind']:.3f}")
print(f"  MATERIAL for extC config (gate flip or |Ddeficit| > "
      f"{DEFICIT_MATERIAL_LOGL}): {'YES - Marcus call needed' if material else 'NO'}")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
axA, axB = axes
names = list(SPEC_3RES)
x = np.arange(len(names))
axA.bar(x - 0.15, [cboth_reg[n]["amp_b"] for n in names], 0.3, color="0.6",
        label="regchar (ISIMIP3)")
axA.bar(x + 0.15, [cboth_obs[n]["amp_b"] for n in names], 0.3, color="tab:red",
        label=f"obs through-origin fit {AMP_FIT_WIN}")
axA.axhline(AMP_G, color="k", ls=":", lw=1, label=f"amp_g convention {AMP_G}")
axA.axhline(AMP_FIT, color="tab:red", ls="--", lw=1,
            label=f"aggregate obs-fit {AMP_FIT:.2f}")
axA.set_xticks(x)
axA.set_xticklabels(names)
axA.set(ylabel="glacier-frame amplification", title="amp_b: regchar vs obs fit")
axA.legend(fontsize=8)

mets = ["flow_win_deficit", "spread", "ds245", "rate_modern_hind"]
lbls = ["deficit (logL)", "spread (cm)", "ds245 (cm)", "modern rate (mm/yr)"]
old = d1e_rows[d1e_rows.label == "C_both/ANCH/unc_t5d"].iloc[0]
new = res[res.label == "OBSAMP/ANCH/unc_t5d"].iloc[0]
xx = np.arange(len(mets))
axB.bar(xx - 0.15, [old[m] for m in mets], 0.3, color="0.6", label="regchar (d1e)")
axB.bar(xx + 0.15, [new[m] for m in mets], 0.3, color="tab:red", label="obs-amp (d1f)")
axB.set_xticks(xx)
axB.set_xticklabels(lbls, fontsize=8)
axB.set(title="headline ANCH/unc_t5d: regchar vs obs-amp")
axB.legend(fontsize=8)
fig.suptitle(f"D1f obs-amp sensitivity arm | amp_g (patho/gates) fixed {AMP_G} | "
             f"commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_FIG, REPO)}")
