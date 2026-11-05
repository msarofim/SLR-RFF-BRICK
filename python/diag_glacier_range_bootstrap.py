#!/usr/bin/env python3
"""Bootstrap interval on how much larger Ladrillo's glacier scenario range is than BRICK 2.0's.

  python3 python/diag_glacier_range_bootstrap.py

The statistic (abstract candidate, Marcus 2026-11-05: "Use 2300, High minus Very Low; bootstrap the 47%"):
    R = [med_L(HI) - med_L(LO)] / [med_B(HI) - med_B(LO)] - 1
with med the median of the joint-arm draws, L Ladrillo, B BRICK 2.0, of COMPONENT at HORIZON. The point estimate
reproduces `outputs/vv_model_comparison_L27.csv` (the table every paper figure reads) exactly; [IDENTITY] checks it.
Also reported: the median of per-draw ranges (each draw is paired across the two scenarios), as a check that the
result does not depend on taking the difference of medians.

THE RESAMPLING UNIT IS THE DRAW INDEX k, because of how the joint arms are built:
  - within each model, draw k runs the same posterior row on the same FaIR configuration in every scenario, so the
    HI and LO values of draw k are paired ([PAIR-SCEN] checks the configuration);
  - across models, draw k <= N_SHARED uses the same FaIR configuration in Ladrillo and BRICK 2.0 (one pairing seed,
    scripts/project_joint.jl and brick20_joint.jl), so the two models' ranges share climate draws ([PAIR-MODEL]).
PAIRED scheme (the headline): draws 1..N_SHARED are resampled once and used by both models; Ladrillo's draws
N_SHARED+1..2000 are resampled separately for Ladrillo alone. Sample sizes stay fixed. A resampled Ladrillo draw
that the record conditioning rejected is absent, as it is from the arm itself.
INDEPENDENT scheme (sensitivity): each model's draws resampled on their own, which ignores the shared climate.

Writes outputs/diag_glacier_range_bootstrap_L27.csv (summary rows, provenance column with the seed).
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draws_io import read_draws  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

TAG = "L27"
STEM = "L27_tap4p69K_V5p64m_tau800"
COMPONENT, HORIZON = "glaciers", 2300
SCEN_HI, SCEN_LO = "vvH", "vvVL"
LABEL = {"vvH": "High", "vvVL": "Very Low"}
LAD_DRAWS = "outputs/scope_slr_fairunc_draws_{m}_spliced_%s.csv" % STEM
BRK_DRAWS = "outputs/scope_slr_fairunc_draws_{m}_spliced_oldbrick.csv"
TABLE = "outputs/vv_model_comparison_%s.csv" % TAG
OUT = "outputs/diag_glacier_range_bootstrap_%s.csv" % TAG
N_BOOT = 10_000
SEED = 20261105                       # applied immediately before each scheme's resampling loop
N_SHARED = 1000                       # BRICK 2.0's joint arm: draws 1..1000, paired with Ladrillo's 1..1000
QS = [0.025, 0.05, 0.5, 0.95, 0.975]  # the paper quotes 5-95 %; 2.5-97.5 % reported beside it


def load(path, arm="joint"):
    d = read_draws(path)
    d = d[(d.arm == arm) & (d.component == COMPONENT) & (d.horizon == HORIZON)]
    if d.empty:
        raise SystemExit("no %s/%s/%d rows in %s" % (arm, COMPONENT, HORIZON, path))
    return d.set_index("draw").sort_index()


def med(v):
    return float(np.percentile(v, 50))        # = vv_model_comparison.py's np.percentile


L = {m: load(LAD_DRAWS.format(m=m)) for m in (SCEN_HI, SCEN_LO)}
B = {m: load(BRK_DRAWS.format(m=m)) for m in (SCEN_HI, SCEN_LO)}

## [PAIR-SCEN] same draws and configurations in both scenarios, per model
for name, D in (("Ladrillo", L), ("BRICK 2.0", B)):
    hi, lo = D[SCEN_HI], D[SCEN_LO]
    if list(hi.index) != list(lo.index) or not (hi.config.values == lo.config.values).all():
        raise SystemExit("[PAIR-SCEN] %s: %s and %s draws/configurations differ" % (name, SCEN_HI, SCEN_LO))
## [PAIR-MODEL] BRICK 2.0 draw k uses Ladrillo draw k's configuration, wherever Ladrillo kept draw k
_common = B[SCEN_HI].index.intersection(L[SCEN_HI].index)
if not (B[SCEN_HI].loc[_common].config.values == L[SCEN_HI].loc[_common].config.values).all():
    raise SystemExit("[PAIR-MODEL] BRICK 2.0 and Ladrillo configurations differ on shared draws")
if list(B[SCEN_HI].index) != list(range(1, N_SHARED + 1)):
    raise SystemExit("[PAIR-MODEL] BRICK 2.0 draws are not 1..%d" % N_SHARED)
N_LAD_ALL = int(L[SCEN_HI].index.max())
REJECTED = sorted(set(range(1, N_LAD_ALL + 1)) - set(L[SCEN_HI].index))
print("[PAIR] scenarios paired in both models; %d of %d BRICK 2.0 draws share a Ladrillo configuration; "
      "Ladrillo rejected draws %s" % (len(_common), N_SHARED, REJECTED))


def stat(lhi, llo, bhi, blo):
    """Difference of medians (the table's statistic), then the median of per-draw ranges (each draw is paired across
    the two scenarios, so it has its own HI - LO range): a check that the result is not a property of the first form."""
    rl, rb = med(lhi) - med(llo), med(bhi) - med(blo)
    dl, db = med(lhi - llo), med(bhi - blo)
    return rl, rb, 100.0 * (rl / rb - 1.0), dl, db, 100.0 * (dl / db - 1.0)


POINT = stat(L[SCEN_HI].value_cm.values, L[SCEN_LO].value_cm.values,
             B[SCEN_HI].value_cm.values, B[SCEN_LO].value_cm.values)
STATS = ("range_ladrillo_cm", "range_brick20_cm", "ladrillo_range_larger_pct",
         "median_perdraw_range_ladrillo_cm", "median_perdraw_range_brick20_cm", "perdraw_ladrillo_range_larger_pct")

## [IDENTITY] the point estimate is the table's: every one of the four medians equals vv_model_comparison's
T = pd.read_csv(TABLE)
T = T[(T.component == COMPONENT) & (T.year == HORIZON)].set_index(["source", "marker"]).med
_pairs = [(("Ladrillo", m), med(L[m].value_cm.values)) for m in (SCEN_HI, SCEN_LO)] + \
         [(("BRICK 2.0", m), med(B[m].value_cm.values)) for m in (SCEN_HI, SCEN_LO)]
_worst = max(abs(T.loc[k] - v) for k, v in _pairs)
if _worst > 1e-9:
    raise SystemExit("[IDENTITY] medians differ from %s by %.3e cm" % (TABLE, _worst))
## mutation: the fixed arm must NOT reproduce the table (the gate can fail)
_mut = abs(T.loc[("Ladrillo", SCEN_HI)] - med(load(LAD_DRAWS.format(m=SCEN_HI), arm="fixed").value_cm.values))
if _mut <= 1e-9:
    raise SystemExit("[IDENTITY-MUTATION] the fixed arm reproduces the joint table: the gate is blind")
print("[IDENTITY] four medians equal %s (max |d| %.1e cm); mutation (fixed arm) differs by %.2f cm"
      % (TABLE, _worst, _mut))

# arrays indexed by draw number (NaN where Ladrillo rejected the draw)
def by_draw(D, m, n):
    a = np.full(n + 1, np.nan)
    a[D[m].index.values] = D[m].value_cm.values
    return a


LH, LL = by_draw(L, SCEN_HI, N_LAD_ALL), by_draw(L, SCEN_LO, N_LAD_ALL)
BH, BL = by_draw(B, SCEN_HI, N_SHARED), by_draw(B, SCEN_LO, N_SHARED)
K_SHARED = np.arange(1, N_SHARED + 1)
K_LADONLY = np.arange(N_SHARED + 1, N_LAD_ALL + 1)


def nn(a):
    return a[~np.isnan(a)]


def boot(scheme):
    rng = np.random.default_rng(SEED)                 # seeded immediately before the stream is consumed
    out = np.empty((N_BOOT, len(STATS)))
    for i in range(N_BOOT):
        if scheme == "paired":
            ks = rng.choice(K_SHARED, size=K_SHARED.size, replace=True)
            kl = np.concatenate([ks, rng.choice(K_LADONLY, size=K_LADONLY.size, replace=True)])
            kb = ks
        else:
            kl = rng.choice(np.arange(1, N_LAD_ALL + 1), size=N_LAD_ALL, replace=True)
            kb = rng.choice(K_SHARED, size=K_SHARED.size, replace=True)
        out[i] = stat(nn(LH[kl]), nn(LL[kl]), BH[kb], BL[kb])   # LH and LL are NaN on the same rejected draws
    return out


rows = []
_prov = ("diag_glacier_range_bootstrap.py | SLR-RFF-BRICK %s | Ladrillo %s joint arm (%s, %d kept draws) and BRICK 2.0 "
         "joint arm (Zenodo 10.5281/zenodo.20592337 joint file, %d draws) | %s, %d, %s minus %s | statistic "
         "[med_L(HI)-med_L(LO)]/[med_B(HI)-med_B(LO)]-1 | %d resamples, numpy default_rng seed %d applied at the start "
         "of each scheme | cm rel 1995-2014"
         % (subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
            TAG, STEM, len(L[SCEN_HI]), N_SHARED, COMPONENT, HORIZON, LABEL[SCEN_HI], LABEL[SCEN_LO], N_BOOT, SEED))
for scheme in ("paired", "independent"):
    bs = boot(scheme)
    for j, name in enumerate(STATS):
        q = np.quantile(bs[:, j], QS)
        rows.append(dict(scheme=scheme, statistic=name, point=POINT[j], p025=q[0], p05=q[1], p50=q[2],
                         p95=q[3], p975=q[4], share_above_zero=float(np.mean(bs[:, j] > 0)), n_boot=N_BOOT,
                         seed=SEED, provenance=_prov))
res = pd.DataFrame(rows)
res.to_csv(OUT, index=False)
pd.set_option("display.width", 200)
print(res.drop(columns="provenance").round(3).to_string(index=False))
print("wrote " + OUT)
