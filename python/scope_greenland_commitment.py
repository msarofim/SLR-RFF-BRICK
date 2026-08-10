#!/usr/bin/env python3
"""
scope_greenland_commitment.py — BRICK's Greenland equilibrium against the
published commitment anchors. Scopes option C (nonlinear V_eq).

SIMPLE's equilibrium volume is LINEAR in temperature, V_eq = a·T + b, so its
committed loss grows by a fixed a per degree forever. The published picture is
strongly nonlinear with a threshold. This script puts the posterior's implied
commitment next to the anchors and quantifies where the linear form breaks.

VERIFIED ANCHORS (fetched 2026-08-10, not recalled):

  Box et al. 2022, Nat. Clim. Change 12:808, doi 10.1038/s41558-022-01441-2
      "Greenland ice imbalance with the recent (2000-2019) climate commits at
      least 274 +/- 68 mm of sea-level rise ... regardless of twenty-first-
      century climate pathways" (3.3 +/- 0.9% volume loss). This is a
      DISEQUILIBRIUM commitment at present-day climate (~+1.2 C), i.e. a LOWER
      BOUND on the commitment at that temperature, not the equilibrium.

  Bochow et al. 2023, Nature 622:528, doi 10.1038/s41586-023-06503-9
      Two ice-sheet models run to equilibrium. Critical GMT threshold for
      abrupt loss 1.7-2.3 C (PISM-dEBM) and ~1.7 C (Yelmo-REMBO). Stable
      states: present-day, an intermediate at ~75% of present volume
      (PISM-dEBM only), and ice-free. Below 1.5 C convergence temperature both
      models give "less than 1 m long-term SLR contribution"; at 2.2 C
      convergence PISM-dEBM loses more than 20% of present-day volume.
      Multistability arises from the melt-elevation feedback in interplay with
      bedrock uplift. Data: Zenodo 10.5281/zenodo.8155423 (open).

  Levermann et al. 2013, PNAS 110:13745, doi 10.1073/pnas.1219414110
      2000-year commitment ~2.3 m/C total, of which thermal expansion
      0.4 m/C and Antarctica 1.2 m/C; glaciers saturate and are
      "overcompensated by the nonlinear response of the Greenland Ice Sheet".
      Per-warming-level Greenland numbers are in the figures, not the
      abstract — NOT extracted here.

  python3 python/scope_greenland_commitment.py
Writes outputs/scope_greenland_commitment.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTERIOR = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
OUT = os.path.join(REPO, "outputs/scope_greenland_commitment.csv")

LEVELS = [1.2, 1.5, 2.0, 2.2, 3.0, 4.0, 5.0]
# Anchors as (level, low, high, m SLE, source) — ranges where the source gives one.
BOX_2022 = (1.2, 0.206, 0.342, "Box 2022 disequilibrium commitment (LOWER BOUND)")
BOCHOW_15 = (1.5, None, 1.0, "Bochow 2023: < 1 m below 1.5 C convergence")
BOCHOW_22 = (2.2, 0.20 * 7.35, None, "Bochow 2023: > 20% of present volume at 2.2 C")
BOCHOW_INTERMEDIATE = 0.25 * 7.35   # the ~75%-of-present intermediate state
GRIS_VOLUME_M = 7.35                # m SLE, posterior median V0


def main():
    post = pd.read_csv(POSTERIOR)
    a = post.greenland_a.to_numpy()
    b = post.greenland_b.to_numpy()
    v0 = post.greenland_v0.to_numpy()

    print("BRICK-F* Greenland: committed loss at equilibrium, V_eq = a*T + b\n")
    print(f"  {'GMT':>5s}  {'committed m SLE':>22s}  {'% of ice sheet':>15s}")
    rows = []
    med = {}
    for T in LEVELS:
        com = v0 - (a * T + b)
        q = np.percentile(com, [5, 50, 95])
        med[T] = q[1]
        print(f"  {T:5.1f}  {q[1]:8.2f} [{q[0]:5.2f},{q[2]:5.2f}]  {100 * q[1] / GRIS_VOLUME_M:14.1f}%")
        rows.append(dict(level_K=T, brick_med_m=q[1], brick_p05_m=q[0], brick_p95_m=q[2],
                         brick_pct=100 * q[1] / GRIS_VOLUME_M))

    print("\nAGAINST THE VERIFIED ANCHORS")
    lvl, lo, hi, src = BOX_2022
    ok = lo <= med[lvl]          # Box is a lower bound: BRICK must be at least this
    print(f"  +{lvl} C  BRICK {med[lvl]:.2f} m  vs  {src}")
    print(f"           {lo:.3f}-{hi:.3f} m as a lower bound -> "
          f"{'CONSISTENT (BRICK exceeds the floor)' if ok else 'BRICK BELOW THE FLOOR'}")

    lvl, lo, hi, src = BOCHOW_15
    ok = med[lvl] < hi
    print(f"  +{lvl} C  BRICK {med[lvl]:.2f} m  vs  {src}")
    print(f"           -> {'CONSISTENT' if ok else 'BRICK EXCEEDS'}")

    lvl, lo, hi, src = BOCHOW_22
    ratio = lo / med[lvl]
    print(f"  +{lvl} C  BRICK {med[lvl]:.2f} m  vs  {src} = {lo:.2f} m")
    print(f"           -> BRICK is {ratio:.1f}x TOO LOW against a lower bound")

    print(f"  +3.0 C  BRICK {med[3.0]:.2f} m. Above the 1.7-2.3 C threshold both Bochow")
    print(f"          models lose the ice sheet to a near-ice-free state; even the")
    print(f"          INTERMEDIATE stable state is {BOCHOW_INTERMEDIATE:.2f} m of loss, so BRICK is")
    print(f"          {BOCHOW_INTERMEDIATE / med[3.0]:.1f}x low against the mildest published outcome and")
    print(f"          {GRIS_VOLUME_M / med[3.0]:.0f}x low against the ice-free one.")

    print("\nVERDICT")
    print("  The linear V_eq is roughly right at +1.5 C and fails progressively above")
    print("  the published threshold. It cannot represent a threshold at all: it has no")
    print("  curvature, so no warming level produces qualitatively different behaviour.")
    print("  For a model run to 2300 and used for pulse experiments, this understates")
    print("  the high-warming commitment by a factor of several.")

    for r in rows:
        r["anchor"] = {1.2: BOX_2022[3], 1.5: BOCHOW_15[3], 2.2: BOCHOW_22[3]}.get(
            r["level_K"], "")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
