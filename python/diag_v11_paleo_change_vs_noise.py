#!/usr/bin/env python3
"""diag_v11_paleo_change_vs_noise.py -- is the v1.0 -> v1.1 movement of the Ladrillo joint-arm medians sampling noise?

Fix A replaces the v1.0 paleo assignment (one chain's 500 (lambda, T_crit) rows reused by all four chains) with one
assignment over all 10,000 draws. Both are unbiased draws of the same joint paleo prior, so the medians should move by
about one standard error, in MIXED directions (~/.claude/CLAUDE.md: all-same-sign across many cells is a bug signal).
For each scenario x horizon x {ais, total}: d = median(v1.1) - median(v1.0), scaled by the bootstrap se of the v1.1
median (NBOOT resamples of the 2,000 draws, seed SEED). Reads the joint-arm draws files (v1.0 from the quarantine).
  python python/diag_v11_paleo_change_vs_noise.py   -> outputs/diag_v11_paleo_change_vs_noise.csv
"""
import os, numpy as np, pandas as pd, datetime, subprocess
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "outputs/quarantine/20261008_ladrillo_v10_superseded/outputs")
TAP = "_tap4p69K_V5p64m_tau800"
SCEN = ["ssp126", "ssp245", "ssp585", "vvVL", "vvL", "vvLN", "vvML", "vvM", "vvHL", "vvH"]
NBOOT, SEED = 500, 20261008
rng = np.random.default_rng(SEED)
rows = []
for s in SCEN:
    f = f"scope_slr_fairunc_draws_{s}_spliced_L27{TAP}.csv"
    a = pd.read_csv(os.path.join(Q, f), float_precision="round_trip")
    b = pd.read_csv(os.path.join(REPO, "outputs", f), float_precision="round_trip")
    for comp in ("ais", "total"):
        for H in (2100, 2150, 2300):
            sel = lambda d: d[(d.arm == "joint") & (d.component == comp) & (d.horizon == H)].value_cm.to_numpy()
            x0, x1 = sel(a), sel(b)
            se = np.std([np.median(rng.choice(x1, x1.size)) for _ in range(NBOOT)], ddof=1)
            d = np.median(x1) - np.median(x0)
            rows.append(dict(scenario=s, component=comp, horizon=H, med_v10=np.median(x0), med_v11=np.median(x1),
                             d_cm=d, boot_se_cm=se, z=d / se if se > 0 else np.nan,
                             d_width_cm=(np.quantile(x1, .95) - np.quantile(x1, .05)) - (np.quantile(x0, .95) - np.quantile(x0, .05))))
df = pd.DataFrame(rows)
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
df["provenance"] = (f"diag_v11_paleo_change_vs_noise.py | SLR-RFF-BRICK {commit} | Ladrillo L27 joint arm, FaIR CMIP7, tapped | "
                    f"v1.0 = quarantine 20261008, v1.1 = canonical | bootstrap {NBOOT} x numpy default_rng({SEED}) | cm | {datetime.date.today()}")
df.to_csv(os.path.join(REPO, "outputs/diag_v11_paleo_change_vs_noise.csv"), index=False)
for comp in ("ais", "total"):
    z = df[df.component == comp].z
    print(f"{comp:5s}: n={len(z)}  positive {int((z > 0).sum())}, negative {int((z < 0).sum())}, zero {int((z == 0).sum())}; "
          f"|z| median {z.abs().median():.2f}, max {z.abs().max():.2f}; |z|>2: {int((z.abs() > 2).sum())}")
print(df.sort_values("z", key=abs, ascending=False).head(6)[["scenario", "component", "horizon", "d_cm", "boot_se_cm", "z"]].to_string(index=False))
