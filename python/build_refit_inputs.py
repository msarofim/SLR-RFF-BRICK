#!/usr/bin/env python3
"""build_refit_inputs.py -- the two files a same-objective REFIT needs, built from a finished run's
own chains rather than by hand (2026-09-20; the L27r arm that measures between-refit precision).

  1. outputs/mcmc/overdispersed_starts_<OUT>.csv -- four over-dispersed start rows = the 2nd-half
     draws of chain <TAG> seed <SEED> at the ais_iceflow0 quantiles 0.02 / 0.35 / 0.65 / 0.98 (the
     convention every production run since L14 has used; NOT random jitter, which leaves the
     feasible region -- calibrate_mcmc_ext.jl header). Every sampled column of the chain is kept,
     so the file covers the current parameter set by NAME.
  2. outputs/mcmc/adapted_cov_<TAG>_named.csv -- postprocess_mcmc_ext.jl writes the pooled
     posterior covariance with a placeholder x1..xN header; the calibrator REFUSES that file and
     wants parameter names (positional reading was the L23 trap). The names are the chain's own
     first N columns, in order -- the sampler's parameter order, which is what the covariance rows
     are. N is asserted equal on both sides.

  python3 python/build_refit_inputs.py --tag=L27 --seed=2026 --out=L27r
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import stamp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCMC = os.path.join(REPO, "outputs/mcmc")
NITER = 2_000_000
QUANTILES = [0.02, 0.35, 0.65, 0.98]        # the seed-bank convention: row i <-> seed 2026+i / 3026+i
PIVOT = "ais_iceflow0"                      # the slowest-mixing direction, hence the spread axis
NON_PARAM = {"log_post", "accept_rate"}

def arg(name, default=None):
    v = next((a[len(name):] for a in sys.argv[1:] if a.startswith(name)), None)
    if v is None and default is None:
        raise SystemExit(f"missing {name}")
    return v if v is not None else default

TAG = arg("--tag=")
SEED = int(arg("--seed=", "2026"))
OUT = arg("--out=", TAG + "r")

chain = os.path.join(MCMC, f"chain_{TAG}_seed{SEED}_n{NITER}.csv")
header = list(pd.read_csv(chain, nrows=0).columns)
params = [c for c in header if c not in NON_PARAM]
print(f"chain {os.path.basename(chain)}: {len(params)} sampled parameters")

## 1. starts: find the rows first (one column), then read only those rows (all columns)
piv = pd.read_csv(chain, usecols=[PIVOT])[PIVOT].to_numpy()
n = len(piv); half = np.arange(n // 2, n)
vals = piv[half]
rows = []
for q in QUANTILES:
    target = np.quantile(vals, q)
    rows.append(int(half[np.argmin(np.abs(vals - target))]))
print("start rows (0-based, 2nd half):", rows, "at", PIVOT, "=", [round(float(piv[r]), 4) for r in rows])
keep = set(r + 1 for r in rows)                                   # +1 for the header line
st = pd.read_csv(chain, skiprows=lambda i: i != 0 and i not in keep)
# skiprows returns file order (ascending row index); put the rows in QUANTILE order, row i <-> seed i
st.index = sorted(rows)
st = st.loc[rows, params].reset_index(drop=True)
starts_out = os.path.join(MCMC, f"overdispersed_starts_{OUT}.csv")
st.to_csv(starts_out, index=False)
print(f"wrote {os.path.relpath(starts_out, REPO)}  ({len(st)} rows x {st.shape[1]} params)")

## 2. the named covariance
cov_in = os.path.join(MCMC, f"adapted_cov_{TAG}.csv")
cov = pd.read_csv(cov_in)
assert cov.shape[0] == cov.shape[1] == len(params), \
    f"{os.path.basename(cov_in)} is {cov.shape}, chain has {len(params)} parameters"
assert all(c.startswith("x") for c in cov.columns), "expected a placeholder x1..xN header"
cov.columns = params
cov_out = os.path.join(MCMC, f"adapted_cov_{TAG}_named.csv")
cov.to_csv(cov_out, index=False)
print(f"wrote {os.path.relpath(cov_out, REPO)}  (header = the chain's {len(params)} parameter names, in order)")

## provenance sidecar (the starts/cov files are consumed by name, so the record travels beside them)
prov = stamp(pd.DataFrame(dict(file=[os.path.basename(starts_out), os.path.basename(cov_out)],
                               source_chain=[os.path.basename(chain)] * 2,
                               rows=[str(rows), "-"], pivot=[PIVOT, "-"], quantiles=[str(QUANTILES), "-"])),
             __file__, tag=TAG, inputs={"chain": chain, "cov": cov_in},
             extra=f"2nd-half draws at {PIVOT} quantiles; cov header by chain column order")
prov.to_csv(os.path.join(MCMC, f"refit_inputs_{OUT}_provenance.csv"), index=False)
