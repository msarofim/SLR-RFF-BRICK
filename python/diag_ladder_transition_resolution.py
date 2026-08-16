#!/usr/bin/env python3
"""
diag_ladder_transition_resolution.py — is PISM-dEBM's Greenland threshold
actually GRADED, or is it just sampled more coarsely than Yelmo-REMBO's?

WHY THIS EXISTS (2026-08-16, thread 5, decision 2)
  Marcus's standing question was whether to carry the PISM-vs-Yelmo ladder arm
  through to the reported results, or whether outside information tips it to a
  single family. The practical argument that had favoured PISM was that PISM is
  "graded" while Yelmo is a "step", so PISM avoids embedding a razor-edge
  discontinuity in a Monte Carlo emulator (scoping section 18).

  scoping section 19.4 already withdrew that on the strength of Bochow et al.
  2026's text ("both show a clear two-fold shape"), but section 18 item 4 and
  section 20 BOTH left "confirm the PISM ladder shape from pism_debm.zip" as an
  outstanding validation against the raw model output. The PISM ladder has since
  been extracted (build_greenland_equilibrium_ladder.py, 2026-08-10), so the
  validation is now cheap. This script is it.

WHAT IT MEASURES
  For each ladder family: the GMT grid spacing, the largest single-rung jump in
  committed loss, and — the point of the exercise — the WIDTH OF THAT JUMP
  EXPRESSED IN UNITS OF THE MODEL'S OWN FINEST GRID SPACING.

  A transition that spans exactly ONE grid interval is UNRESOLVED. Its apparent
  width is an upper bound set by the sampling, not a measured property of the
  model. Comparing an unresolved width against a differently-sampled model's
  unresolved width measures the two sampling designs, not the two ice sheets.

  Also reports the equilibrium drift over the averaging window at the jump
  rungs, since a poorly-converged rung would be a separate reason to distrust
  the shape, and the SSP-peak committed-loss brackets that decide whether the
  arm is decisive at policy-relevant warming.

READS   data/observations/greenland_equilibrium_bochow2023.csv  (the ladder)
        outputs/ssps_components_2300_L11.csv                    (SSP GMST paths)
WRITES  outputs/diag_ladder_transition_resolution.csv

  python3 python/diag_ladder_transition_resolution.py
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(REPO, "data/observations/greenland_equilibrium_bochow2023.csv")
SSPS = os.path.join(REPO, "outputs/ssps_components_2300_L11.csv")
OUT = os.path.join(REPO, "outputs/diag_ladder_transition_resolution.csv")

# --- named constants that the labels below derive from -----------------------
LADDER_TAG = "Bochow et al. 2023 equilibrium ladder (Nature 622:528, Zenodo 8155423)"
SSP_TAG = "L11 posterior projections"
GMT_COL, LOSS_COL = "gmt_K", "loss_m_sle"
DRIFT_COL = "drift_over_window_m"
# a transition spanning <= this many of the model's own finest grid intervals is
# reported as UNRESOLVED: its width is set by the sampling, not by the model.
RESOLVED_MIN_INTERVALS = 2.0


def transition_report(name, g):
    """Grid spacing, largest jump, and whether that jump is resolved."""
    g = g.sort_values(GMT_COL).reset_index(drop=True)
    step = np.diff(g[GMT_COL].to_numpy())
    jump = np.diff(g[LOSS_COL].to_numpy())
    i = int(np.argmax(jump))
    finest = float(step.min())
    width = float(step[i])
    intervals = width / finest
    return {
        "model": name,
        "n_rungs": len(g),
        "grid_min_K": finest,
        "grid_max_K": float(step.max()),
        "jump_m_sle": float(jump[i]),
        "jump_lo_K": float(g[GMT_COL][i]),
        "jump_hi_K": float(g[GMT_COL][i + 1]),
        "jump_width_K": width,
        "width_in_own_finest_intervals": intervals,
        "resolved": intervals >= RESOLVED_MIN_INTERVALS,
        "drift_at_jump_lo_m": float(g[DRIFT_COL][i]),
        "drift_at_jump_hi_m": float(g[DRIFT_COL][i + 1]),
    }


def committed_bracket(g, T):
    """Bracketing rungs at GMT T. Deliberately NOT interpolated: interpolating
    across a transition the model never resolved would invent a shape."""
    g = g.sort_values(GMT_COL)
    below = g[g[GMT_COL] <= T]
    above = g[g[GMT_COL] > T]
    lo = below.iloc[-1] if len(below) else None
    hi = above.iloc[0] if len(above) else None
    return lo, hi


def main():
    d = pd.read_csv(LADDER)
    fams = {m: g for m, g in d.groupby("model")}

    print(f"LADDER: {LADDER_TAG}\n")
    print("=== 1. Is the transition resolved? ===\n")
    rows = [transition_report(m, g) for m, g in fams.items()]
    for r in rows:
        verdict = "RESOLVED" if r["resolved"] else "UNRESOLVED"
        print(f"  {r['model']}")
        print(f"    {r['n_rungs']} rungs; GMT grid spacing "
              f"{r['grid_min_K']:.3f}-{r['grid_max_K']:.3f} K")
        print(f"    largest jump {r['jump_m_sle']:.2f} m over "
              f"[{r['jump_lo_K']:.3f} -> {r['jump_hi_K']:.3f}] K "
              f"(width {r['jump_width_K']:.3f} K)")
        print(f"    = {r['width_in_own_finest_intervals']:.1f}x the model's own "
              f"finest spacing  -> {verdict}")
        print(f"    equilibrium drift at the jump rungs: "
              f"{r['drift_at_jump_lo_m']:.3f} / {r['drift_at_jump_hi_m']:.3f} m\n")

    if not any(r["resolved"] for r in rows):
        print("  VERDICT: NEITHER family resolves its own transition. The apparent")
        print("  'PISM graded vs Yelmo step' contrast is a SAMPLING artefact --")
        print("  each width is one grid interval of a differently-refined ladder.")
        print("  It cannot be used as an argument for preferring either family.\n")

    print("=== 2. Where the arm is actually decisive ===\n")
    ssp = (pd.read_csv(SSPS).groupby("ssp")["gmst"]
           .agg(peak="max", at2300=lambda s: s.iloc[-1]))
    print(f"  SSP GMST from {SSP_TAG}:")
    print("   ", ssp.round(3).to_string().replace("\n", "\n    "), "\n")

    brackets = []
    for s, row in ssp.iterrows():
        T = float(row["peak"])
        print(f"  {s}  peak GMT {T:.2f} K")
        vals = {}
        for m, g in fams.items():
            lo, hi = committed_bracket(g, T)
            if hi is None:
                txt = (f"ABOVE the ladder's top rung "
                       f"{lo[GMT_COL]:.3f}K={lo[LOSS_COL]:.2f}m (saturated)")
                vals[m] = float(lo[LOSS_COL])
            else:
                txt = (f"{lo[GMT_COL]:.3f}K={lo[LOSS_COL]:.2f}m .. "
                       f"{hi[GMT_COL]:.3f}K={hi[LOSS_COL]:.2f}m")
                vals[m] = 0.5 * (float(lo[LOSS_COL]) + float(hi[LOSS_COL]))
            print(f"     {m:12s} {txt}")
            brackets.append({"ssp": s, "peak_gmt_K": T, "model": m,
                             "committed_m_sle_midrange": vals[m]})
        ratio = max(vals.values()) / min(vals.values())
        print(f"     -> families differ by {ratio:.2f}x in committed loss\n")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    pd.DataFrame(brackets).to_csv(OUT.replace(".csv", "_ssp.csv"), index=False)
    print(f"wrote {os.path.relpath(OUT, REPO)}")
    print(f"wrote {os.path.relpath(OUT.replace('.csv', '_ssp.csv'), REPO)}")


if __name__ == "__main__":
    main()
