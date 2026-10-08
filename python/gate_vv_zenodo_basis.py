#!/usr/bin/env python3
"""
gate_vv_zenodo_basis.py -- the van Vuuren FaIR cubes rebuilt on the published Zenodo v1.1.1 scenario (2026-10-08,
"variant b") must be the cubes the a-vs-b test measured, and must differ from their predecessors only where the
emissions changed.

    python python/gate_vv_zenodo_basis.py <quarantined_cube_dir> [<arm_b_cube_dir>]

[PRE2024-IDENTITY]  variant b keeps the CMIP7 1.6.0 history verbatim through 2023.5 and FaIR integrates forward, so
                    every live vv cube (GMST and OHC, 841 configs) must equal its quarantined `harmonized` predecessor
                    EXACTLY for every year <= HIST_LAST_YEAR...
[POST2023-MOVES]    ...and must differ from it in some year after HIST_LAST_YEAR (the 2024-2100 block moved from the
                    IIASA prerelease to the published file for every marker). A cube identical after 2023 means the
                    rebuild read the old emissions.
[ARM-B-IDENTITY]    with <arm_b_cube_dir>: the live vvML GMST and OHC cubes must be BYTE-identical to the cubes written
                    from SLR-RFF-BRICK python/diag_vv_zenodo_ab arm `b` (the measurement the switch was decided on).

⚠ The existing gate_vv_cmip7_basis.py is BLIND to this change: it tests only the pre-2014 history, which variant b
does not move. This gate is its complement.

Power: before judging, the comparison is run once on the quarantined copy against ITSELF; [POST2023-MOVES] must then
FAIL on every marker, or the gate is refused as blind.
"""
import sys, os
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(REPO, "data", "observations")
MARKERS = ("vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH")
FIELDS = ("gmst", "ohc")
HIST_LAST_YEAR = 2023                  # CMIP7 history ends here (build_emissions_v160_cmip7harm_vv.py)
ARM_B_MARKER = "vvML"


def cube(d, field, m):
    return pd.read_csv(os.path.join(d, f"fair_cube_{field}_{m}_raw.csv"), float_precision="round_trip")


def judge(new_dir, old_dir):
    """-> {(marker, field): (pre_identical, post_differs)}"""
    out = {}
    for m in MARKERS:
        for f in FIELDS:
            a, b = cube(new_dir, f, m), cube(old_dir, f, m)
            if list(a.columns) != list(b.columns) or not np.array_equal(a.year.values, b.year.values):
                sys.exit(f"ERROR: {f} {m}: column or year layout differs between {new_dir} and {old_dir}")
            pre, post = a.year.values <= HIST_LAST_YEAR, a.year.values > HIST_LAST_YEAR
            va, vb = a.drop(columns="year").values, b.drop(columns="year").values
            out[(m, f)] = (np.array_equal(va[pre], vb[pre]), not np.array_equal(va[post], vb[post]))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    old = sys.argv[1]
    fails = 0
    # power: the quarantined copy against itself must FAIL [POST2023-MOVES] everywhere
    blind = [k for k, (_, moved) in judge(old, old).items() if moved]
    if blind:
        sys.exit(f"ERROR: [POWER] self-comparison reported a post-2023 move for {blind}; the gate is blind")
    print(f"[POWER] self-comparison: [POST2023-MOVES] fails on all {len(MARKERS) * len(FIELDS)} cubes, as it must")
    for (m, f), (pre_ok, moved) in judge(LIVE, old).items():
        v1, v2 = ("PASS" if pre_ok else "FAIL"), ("PASS" if moved else "FAIL")
        fails += (not pre_ok) + (not moved)
        print(f"  {m:5s} {f:4s} [PRE2024-IDENTITY] {v1}   [POST2023-MOVES] {v2}")
    if len(sys.argv) > 2:
        for f in FIELDS:
            name = f"fair_cube_{f}_{ARM_B_MARKER}_raw.csv"
            same = open(os.path.join(LIVE, name), "rb").read() == open(os.path.join(sys.argv[2], name), "rb").read()
            fails += not same
            print(f"  [ARM-B-IDENTITY] {name}: {'BYTE-IDENTICAL: PASS' if same else 'DIFFERS: FAIL'}")
    print(f"[VV-ZENODO-BASIS] {'PASS' if fails == 0 else f'FAIL ({fails})'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
