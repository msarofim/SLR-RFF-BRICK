#!/usr/bin/env python3
"""diag_table_a2_subsample_move.py -- Table A2: chains (stride 200, 4 x 5000) vs the 10k subsample (stride 400, 4 x 2500), unrounded.
Error bar: the post/prior ratio along each FIXED subsample PC, computed per chain; se = sd over the 4 chains / sqrt(4).
  python3 python/diag_table_a2_subsample_move.py [--rerun=<path to a chain-mode re-run of diag_ais_block_pca_L27.csv>]
Needs outputs/diag_ais_block_pca_L27{,_sub10k}.csv. With --rerun, also checks that re-run against the committed CSV.
"""
import sys, os, numpy as np, pandas as pd
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
shipped = pd.read_csv(os.path.join(S, "outputs/diag_ais_block_pca_L27.csv"))
sub = pd.read_csv(os.path.join(S, "outputs/diag_ais_block_pca_L27_sub10k.csv"))
rerun_p = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--rerun=")), "")
num = [c for c in shipped.columns if c not in ("loadings", "provenance")]
if rerun_p:
    rerun = pd.read_csv(rerun_p, float_precision="round_trip")
    sh = pd.read_csv(os.path.join(S, "outputs/diag_ais_block_pca_L27.csv"), float_precision="round_trip")
    d = (rerun[num] - sh[num]).abs().to_numpy().max()
    print(f"REGRESSION chains re-run vs committed CSV: max|diff| over {len(num)} numeric cols = {d:.3e}; "
          f"loadings strings equal: {(rerun.loadings == sh.loadings).all()}")
vcols = [c for c in num if c.startswith("v_")]
print(f"\n{'PC':>3} {'ratio ch':>9} {'ratio sub':>9} {'d ratio':>9} {'rhat ch':>8} {'rhat sub':>8} {'|cos|':>7}")
for k in range(len(shipped)):
    a, b = shipped.iloc[k], sub.iloc[k]
    cos = abs(np.dot(a[vcols].astype(float), b[vcols].astype(float)))
    print(f"{k+1:>3} {a.ratio:9.4f} {b.ratio:9.4f} {b.ratio-a.ratio:+9.4f} {a.rhat:8.4f} {b.rhat:8.4f} {cos:7.4f}")
print("\nsub-chain error bar on the IDENTIFIED rows (ratio along the fixed subsample PC, per chain):")
sys.argv = ["x", "--tag=L27", "--source=subsample"]
ns = {"__file__": os.path.join(S, "python/diag_ais_block_pca.py")}
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    src = open(ns["__file__"]).read().split("df = pd.DataFrame(out)")[0]   # stop before it writes anything
    exec(compile(src, ns["__file__"], "exec"), ns)
Z, V, Cpri, order_w = ns["Z"], ns["V"], ns["Cpri"], ns["w"]
for k in (11, 12, 13):
    v = V[:, k]; pv = v @ Cpri @ v
    per = np.array([np.var(z @ v, ddof=1) / pv for z in Z])
    print(f"  PC{k+1}: pooled-within {per.mean():.4f}; per chain {np.round(per, 4)}; se(mean) {per.std(ddof=1)/2:.4f} "
          f"= {100*per.std(ddof=1)/2:.2f} pp of prior; chains-minus-sub move {100*(shipped.ratio[k]-sub.ratio[k]):+.2f} pp")
