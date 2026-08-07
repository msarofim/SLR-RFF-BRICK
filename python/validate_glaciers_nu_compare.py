#!/usr/bin/env python3
"""
validate_glaciers_nu_compare.py — Python side of the extB3 port validation.

Reads outputs/validate_glaciers_nu.csv (Julia trajectories + the exact driver
the Julia model used), re-integrates each (kappa, nu) combo with an independent
Python implementation of the same algebra, and compares:
  V1: max |Julia - Python| per combo, tol 1e-9 m (identical algebra, Float64).
  V2: nu=0 combo == analytic single-tau Mengel relaxation (kappa = 1/tau).
"""
import os
import re

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
CSV = os.path.join(REPO, "outputs/validate_glaciers_nu.csv")
TOL = 1e-9
SC = dict(a=0.383, b=0.286, T_off=-0.957)

df = pd.read_csv(CSV)
T = df["tglac"].to_numpy()

def integrate_nu(a, b, T_off, kappa, nu, Tarr):
    S = np.empty(len(Tarr))
    S[0] = 0.0
    for k in range(1, len(Tarr)):
        Tprev = Tarr[k - 1]
        seq = a * (1 - np.exp(-b * (Tprev - T_off)))
        frac_left = max(1 - S[k - 1] / a, 1e-12)
        T_eq = T_off - np.log(frac_left) / b
        exc = max(Tprev - T_eq, 0.0)
        mult = min(kappa * exc ** nu, 1.0)
        S[k] = S[k - 1] + mult * (seq - S[k - 1])
    return S

def integrate_single_tau(a, b, T_off, tau, Tarr):
    S = np.empty(len(Tarr))
    S[0] = 0.0
    for k in range(1, len(Tarr)):
        seq = a * (1 - np.exp(-b * (Tarr[k - 1] - T_off)))
        S[k] = S[k - 1] + (seq - S[k - 1]) / tau
    return S

npass = 0
combos = [c for c in df.columns if c.startswith("gsic_k")]
for col in combos:
    kap, nu = map(float, re.match(r"gsic_k([0-9.]+)_nu([0-9.]+)", col).groups())
    py = integrate_nu(SC["a"], SC["b"], SC["T_off"], kap, nu, T)
    d = np.abs(df[col].to_numpy() - py).max()
    ok = d < TOL
    npass += ok
    print(f"V1 {col}: max|Julia-Python| = {d:.3e}  {'PASS' if ok else 'FAIL'}")
    if nu == 0.0:
        py_tau = integrate_single_tau(SC["a"], SC["b"], SC["T_off"], 1.0 / kap, T)
        d2 = np.abs(df[col].to_numpy() - py_tau).max()
        ok2 = d2 < TOL
        npass += ok2
        print(f"V2 nu=0 vs analytic single-tau (tau={1/kap:.1f}): max diff = {d2:.3e}  "
              f"{'PASS' if ok2 else 'FAIL'}")

total = len(combos) + 1
print(f"\n{npass}/{total} checks passed" + ("" if npass == total else "  <-- INVESTIGATE"))
