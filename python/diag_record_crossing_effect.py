#!/usr/bin/env python3
"""
diag_record_crossing_effect.py -- what conditioning on "no Antarctic fast dynamics before the record ends" would do to
the paper's reported JOINT-arm numbers. Diagnostic only: no product changes.

    python python/diag_record_crossing_effect.py
Writes outputs/diag_record_crossing_effect_L27.csv (+ provenance) and prints the largest moves.

WHY: decision 2 (handoff 2026-10-08) was argued on "none of the 4 crossing draws is among the 2,000 projection rows".
That was measured on the MEAN climate. In the joint arm each draw runs on its own FaIR config, and there 3 of the 2,000
SSP draws (2 of the van Vuuren) fire by 2025 (Ladrillo.jl CHANGELOG 2026-10-08c). Conditioning by rejection DELETES
draws and leaves every other draw's value unchanged, so its effect on a cell is exact from the shipped draws file:
recompute the statistic without the crossing draws.

INPUTS:
- outputs/record_crossings_projection_draws.csv: Ladrillo.jl scripts/record_crossings.jl (the package's
  fastdyn_onset_year, checked against model runs draw for draw). Its `config` column is asserted equal to the research
  draws file's, draw by draw, so the two codebases' pairings agree before anything is used.
- outputs/scope_slr_fairunc_draws_<scen>_spliced_L27<TAP>.csv: the paper's Ladrillo joint arm (v1.1, canonical).

[REPRO] the median / p05 / p95 recomputed from ALL draws must equal the shipped cells file exactly, or the deltas below
would be measured against the wrong base. Julia's quantile and median are reimplemented arithmetic for arithmetic
(numpy's "linear" quantile is the same definition but lands 1 ulp away on some cells).
Effects are reported against the bootstrap se of the same statistic (draws resampled, N_BOOT, BOOT_SEED, both stamped
in the provenance): a move inside that se is resampling-size.
"""
import os, math, subprocess, datetime
from fractions import Fraction
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/diag_record_crossing_effect_L27.csv")
CROSS = os.path.join(REPO, "outputs/record_crossings_projection_draws.csv")
TAP = "_tap4p69K_V5p64m_tau800"
DRAWS = lambda s: os.path.join(REPO, f"outputs/scope_slr_fairunc_draws_{s}_spliced_L27{TAP}.csv")
CELLS = lambda s: os.path.join(REPO, f"outputs/scope_slr_fairunc_cells_{s}_spliced_L27{TAP}.csv")
SCENARIOS = ("ssp126", "ssp245", "ssp585", "vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH")
COMPONENTS = ("ais", "total")
HORIZONS = (2100, 2150, 2300)
ARM = "joint"
RECORD_END = 2025                # the Antarctic target's last year (Ladrillo record_end()); asserted against the input
LAST_YEARS = (RECORD_END, RECORD_END + 1)   # the record end, and one year past it (sensitivity)


def jl_quantile(x, p):
    """Julia Statistics.quantile (default alpha = beta = 1), arithmetic for arithmetic: numpy's "linear" quantile is the
    same definition but interpolates differently and lands 1 ulp away on some cells (found by [REPRO])."""
    v = np.sort(x); n = len(v)
    m = 1.0 + p * (1.0 - 1.0 - 1.0)
    aleph = float(Fraction(n) * Fraction(p) + Fraction(m))           # fma(n, p, m): one rounding
    j = min(max(int(aleph), 1), n - 1)
    g = min(max(aleph - j, 0.0), 1.0)
    a, b = float(v[j - 1]), float(v[j])
    if abs(a - b) <= math.sqrt(np.finfo(float).eps) * max(abs(a), abs(b)):    # a ≈ b (isapprox defaults)
        return a + g * (b - a)
    return (1 - g) * a + g * b


def jl_median(x):
    """Julia Statistics.median: for even n, middle(a, b) = a/2 + b/2."""
    v = np.sort(x); n = len(v)
    return float(v[n // 2]) if n % 2 else float(v[n // 2 - 1]) / 2 + float(v[n // 2]) / 2


STATS = {"med": jl_median, "p05": lambda x: jl_quantile(x, 0.05), "p95": lambda x: jl_quantile(x, 0.95)}
CELL_COL = {"med": "med_cm", "p05": "p05_cm", "p95": "p95_cm"}
N_BOOT = 2000
BOOT_SEED = 20261008

cross = pd.read_csv(CROSS)
assert f"Antarctic record ends {RECORD_END}" in cross.provenance.iloc[0], "record end disagrees with the producer"
rng = np.random.default_rng(BOOT_SEED)
rows = []
for s in SCENARIOS:
    d = pd.read_csv(DRAWS(s), float_precision="round_trip"); d = d[d.arm == ARM]
    cl = pd.read_csv(CELLS(s), float_precision="round_trip"); cl = cl[cl.arm == ARM]
    c = cross[cross.scenario == s].set_index("draw")
    for comp in COMPONENTS:
        for H in HORIZONS:
            x = d[(d.component == comp) & (d.horizon == H)].sort_values("draw")
            assert len(x) == len(c) == 2000, (s, comp, H, len(x), len(c))
            assert (x.config.values == c.loc[x.draw.values, "config"].values).all(), f"{s}: pairing disagrees"
            v = x.value_cm.values
            onset = c.loc[x.draw.values, "onset_joint"].values
            cell = cl[(cl.component == comp) & (cl.horizon == H)]
            assert len(cell) == 1
            idx = rng.integers(0, len(v), size=(N_BOOT, len(v)))
            for st, f in STATS.items():
                base = f(v)
                assert base == float(cell[CELL_COL[st]].iloc[0]), f"[REPRO] {s} {comp} {H} {st}: {base} vs cell"
                se = np.std([f(v[i]) for i in idx], ddof=1)
                for ly in LAST_YEARS:
                    keep = ~((onset > 0) & (onset <= ly))
                    cond = f(v[keep])
                    rows.append(dict(scenario=s, component=comp, horizon=H, stat=st, last_year=ly,
                                     n_dropped=int((~keep).sum()), dropped_draws=" ".join(map(str, x.draw.values[~keep])),
                                     reported_cm=base, conditioned_cm=cond, delta_cm=cond - base, boot_se_cm=se,
                                     delta_over_se=(cond - base) / se if se > 0 else np.nan))

df = pd.DataFrame(rows)
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
df["provenance"] = (
    f"diag_record_crossing_effect.py | SLR-RFF-BRICK {commit} | Ladrillo L27 v1.1 joint arm, draws files "
    f"scope_slr_fairunc_draws_<scen>_spliced_L27{TAP}.csv | crossings: {cross.provenance.iloc[0].split(' | ')[0]} "
    f"scripts/record_crossings.jl (onset_joint) | conditioned = drop draws with onset <= last_year | statistics "
    f"Julia Statistics quantile/median reimplemented, [REPRO] exact vs the shipped cells | bootstrap {N_BOOT} replicates, "
    f"default_rng({BOOT_SEED}), one stream in row order | cm rel 1995-2014 | {datetime.date.today()}")
df.to_csv(OUT, index=False)

print(f"wrote {os.path.relpath(OUT, REPO)}  ([REPRO] passed on {len(df) // len(LAST_YEARS)} cells)\n")
for ly in LAST_YEARS:
    g = df[df.last_year == ly]
    print(f"last_year {ly}: dropped per scenario {dict(g.groupby('scenario').n_dropped.first())}")
    print(f"  max |delta| {g.delta_cm.abs().max():.3f} cm, max |delta|/se {g.delta_over_se.abs().max():.2f}")
    top = g.reindex(g.delta_cm.abs().sort_values(ascending=False).index).head(8)
    for _, r in top.iterrows():
        print(f"  {r.scenario:7s} {r.component:5s} {r.horizon} {r.stat}: {r.reported_cm:9.3f} -> {r.conditioned_cm:9.3f}"
              f"  ({r.delta_cm:+.3f} cm, {r.delta_over_se:+.2f} se)")
