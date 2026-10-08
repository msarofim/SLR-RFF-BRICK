#!/usr/bin/env python3
"""
diag_tap_paired_contribution.py -- the Greenland tap's contribution, PAIRED per draw (tapped - untapped).

    python python/diag_tap_paired_contribution.py
Writes outputs/diag_tap_paired_contribution_L27.csv (+ provenance column) and prints a markdown table.

RULED (Marcus 2026-10-08, decision 4 of handoff 2026-10-08): Sect. 2.2.2 quotes the tap as the SHARE OF DRAWS IN WHICH
IT FIRES and its PAIRED MEAN contribution, not as a difference of two medians of the total. The difference of medians
is not a contribution: it went 0.3 -> 0.0 cm at SSP2-4.5 between v1.0 and v1.1 while the tap itself did not change
(Greenland is bit-identical between the two versions).

Pairing: the tapped and untapped joint arms share draws (rows 1:5:10000 of the 10k subsample) and the seeded
draw -> FaIR-config permutation, so row i of one file is row i of the other. That is ASSERTED (draw and config per row),
not assumed.

FIRES: the tap opens on GLOBAL mean temperature through a clamped linear ramp (julia/greenland_3basin_component.jl:357, clamp(
(GMT - onset) / ramp_w, 0, 1)), so a draw whose GMST never passes the onset receives EXACTLY zero from it. A draw
"fires" when its paired Greenland difference is nonzero (an exact test, not a tolerance). The total can move through
the Antarctic sea-level feedback only in draws where Greenland moved; that is asserted too.

Bootstrap: draws resampled with replacement, N_BOOT replicates, numpy default_rng(BOOT_SEED). The seed and the
replicate count are stamped into every row's provenance. The se says how far each statistic moves under resampling of
the same 2,000 draws -- the property that separates the paired mean from the difference of medians.
"""
import os, subprocess, datetime
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUAR = os.path.join(REPO, "outputs/quarantine/20261008_ladrillo_v10_superseded/outputs")
OUT = os.path.join(REPO, "outputs/diag_tap_paired_contribution_L27.csv")
TAP = "_tap4p69K_V5p64m_tau800"
SCENARIOS = ("ssp126", "ssp245", "ssp585")
LAB = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
HORIZONS = (2100, 2150, 2300)
COMPONENTS = ("gis", "total")
ARM = "joint"                                 # the arm the draft quotes (v11_paper_number_diff.py rows 2.2.2)
N_BOOT = 2000
BOOT_SEED = 20261008
VERSIONS = {"v1.1": os.path.join(REPO, "outputs"), "v1.0": QUAR}
DRAWS = lambda d, s, tap: os.path.join(d, f"scope_slr_fairunc_draws_{s}_spliced_L27{TAP if tap else ''}.csv")


def load(d, s, tap):
    x = pd.read_csv(DRAWS(d, s, tap), float_precision="round_trip")
    return x[x.arm == ARM]


def paired(d, s, comp, H):
    """(tapped - untapped) per draw, with the pairing asserted; also the two levels for the median difference."""
    a, b = load(d, s, True), load(d, s, False)
    a, b = a[(a.component == comp) & (a.horizon == H)], b[(b.component == comp) & (b.horizon == H)]
    a, b = a.sort_values("draw").reset_index(drop=True), b.sort_values("draw").reset_index(drop=True)
    assert len(a) == len(b) > 0, (s, comp, H, len(a), len(b))
    assert (a.draw.values == b.draw.values).all() and (a.config.values == b.config.values).all(), \
        f"{s} {comp} {H}: tapped and untapped arms are not paired row by row"
    return a.value_cm.values - b.value_cm.values, a.value_cm.values, b.value_cm.values


def stats(diff, lev_t, lev_u, fires):
    n = len(diff)
    return dict(n_draws=n, fires_share=fires.mean(), paired_mean_cm=diff.mean(), paired_median_cm=np.median(diff),
                mean_if_fires_cm=(diff[fires].mean() if fires.any() else 0.0),
                diff_of_medians_cm=np.median(lev_t) - np.median(lev_u))


def boot_se(diff, lev_t, lev_u, fires, rng):
    n = len(diff)
    idx = rng.integers(0, n, size=(N_BOOT, n))
    pm = diff[idx].mean(axis=1)
    dm = np.median(lev_t[idx], axis=1) - np.median(lev_u[idx], axis=1)
    fs = fires[idx].mean(axis=1)
    return dict(paired_mean_se=pm.std(ddof=1), diff_of_medians_se=dm.std(ddof=1), fires_share_se=fs.std(ddof=1))


rows = []
rng = np.random.default_rng(BOOT_SEED)
for ver, d in VERSIONS.items():
    for s in SCENARIOS:
        for H in HORIZONS:
            dg, _, _ = paired(d, s, "gis", H)
            fires = dg != 0.0
            for comp in COMPONENTS:
                diff, lt, lu = paired(d, s, comp, H)
                assert (diff[~fires] == 0.0).all(), \
                    f"{ver} {s} {comp} {H}: {int((diff[~fires] != 0).sum())} draws move with Greenland unmoved"
                r = dict(version=ver, scenario=s, scenario_label=LAB[s], horizon=H, component=comp, arm=ARM)
                r.update(stats(diff, lt, lu, fires))
                r.update(boot_se(diff, lt, lu, fires, rng))
                rows.append(r)

df = pd.DataFrame(rows)
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
df["provenance"] = (
    f"diag_tap_paired_contribution.py | SLR-RFF-BRICK {commit} | Ladrillo L27 (v1.1 = outputs/, v1.0 = "
    f"{os.path.relpath(QUAR, REPO)}) | {ARM} arm, rows 1:5:10000 of the 10k subsample paired with FaIR 2.2.4 "
    f"(calib 1.6.0) CMIP7-basis configs | tap cell {TAP.lstrip('_')} vs untapped | paired = tapped - untapped per "
    f"draw; fires = Greenland paired difference != 0 | bootstrap {N_BOOT} replicates over draws, "
    f"numpy default_rng({BOOT_SEED}), one stream in row order | cm rel 1995-2014 | {datetime.date.today()}")
df.to_csv(OUT, index=False)

print(f"wrote {os.path.relpath(OUT, REPO)}\n")
print("| version | scenario | horizon | component | fires in | paired mean (se) | paired median | mean if fires |"
      " difference of medians (se) |")
print("|---|---|---|---|---|---|---|---|---|")
for _, r in df.iterrows():
    print(f"| {r.version} | {r.scenario_label} | {r.horizon} | {r.component} | {100 * r.fires_share:.1f}% |"
          f" {r.paired_mean_cm:.2f} ({r.paired_mean_se:.2f}) | {r.paired_median_cm:.2f} | {r.mean_if_fires_cm:.2f} |"
          f" {r.diff_of_medians_cm:.2f} ({r.diff_of_medians_se:.2f}) |")
